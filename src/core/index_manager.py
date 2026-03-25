"""
Index Manager for JSON Memory Store - Phase 1 Foundation Component

Provides fast query capabilities for scheduled architecture data.
Uses file-based indexing with intelligent caching.
"""

import json
import asyncio
import aiofiles
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import bisect
import pickle
from concurrent.futures import ThreadPoolExecutor

from .json_memory_store import JSONQuery, FilterSpec, DateRange
from .schemas import JiraAnalysisSchema, MeetingAnalysisSchema


@dataclass
class IndexEntry:
    """Single index entry"""
    file_path: str
    data_type: str
    date: str
    timestamp: str
    file_size: int
    metadata: Dict[str, Any]
    
    # Extracted searchable fields
    projects: List[str]
    employees: List[str]
    keywords: Set[str]
    
    # Performance metrics for quick filtering
    min_performance_score: Optional[float] = None
    max_performance_score: Optional[float] = None
    
    # Quality metrics
    quality_score: Optional[float] = None


@dataclass
class IndexConfig:
    """Configuration for index manager"""
    index_path: Path = Path("/data/memory/index")
    cache_size_mb: int = 50
    rebuild_interval_hours: int = 24
    enable_full_text_search: bool = True
    
    # Performance tuning
    max_results_cache: int = 1000
    index_compression: bool = True
    parallel_indexing: bool = True


class IndexManager:
    """
    Manages file-based indexes for fast JSON data queries.
    
    Provides intelligent indexing with keyword extraction,
    date-based indexing, and performance metrics indexing.
    """
    
    def __init__(self, config: IndexConfig = None):
        self.config = config or IndexConfig()
        self.index_path = self.config.index_path
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Index storage
        self._datetime_index = []  # Sorted by date
        self._type_index = defaultdict(list)  # By data type
        self._project_index = defaultdict(list)  # By project
        self._employee_index = defaultdict(list)  # By employee
        self._keyword_index = defaultdict(list)  # By keyword
        self._performance_index = []  # Sorted by performance score
        
        # Cache for query results
        self._query_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Index metadata
        self._last_rebuild = None
        self._index_version = "1.0.0"
        
        # Thread pool for parallel operations
        self._executor = ThreadPoolExecutor(max_workers=4)
    
    async def build_index(self, data_directory: Path) -> bool:
        """
        Build comprehensive index from JSON data directory.
        
        Args:
            data_directory: Directory containing JSON data files
            
        Returns:
            True if index built successfully
        """
        try:
            print(f"🔍 Building index from {data_directory}")
            
            # Clear existing indexes
            await self._clear_indexes()
            
            # Find all JSON files
            json_files = list(data_directory.glob("*.json"))
            
            if not json_files:
                print("⚠️ No JSON files found for indexing")
                return False
            
            # Process files in parallel if enabled
            if self.config.parallel_indexing:
                await self._build_index_parallel(json_files)
            else:
                await self._build_index_sequential(json_files)
            
            # Sort indexes for binary search
            await self._sort_indexes()
            
            # Save index to disk
            await self._save_index()
            
            # Update metadata
            self._last_rebuild = datetime.now()
            
            print(f"✅ Index built: {len(json_files)} files processed")
            return True
            
        except Exception as e:
            print(f"❌ Index build failed: {str(e)}")
            return False
    
    async def _build_index_parallel(self, json_files: List[Path]):
        """Build index using parallel processing"""
        # Process files in batches
        batch_size = 10
        for i in range(0, len(json_files), batch_size):
            batch = json_files[i:i + batch_size]
            
            # Process batch in parallel
            loop = asyncio.get_event_loop()
            tasks = []
            
            for file_path in batch:
                task = loop.run_in_executor(
                    self._executor, 
                    self._process_single_file, 
                    file_path
                )
                tasks.append(task)
            
            # Wait for batch completion
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Add valid results to indexes
            for result in batch_results:
                if isinstance(result, IndexEntry):
                    await self._add_to_indexes(result)
    
    async def _build_index_sequential(self, json_files: List[Path]):
        """Build index using sequential processing"""
        for file_path in json_files:
            try:
                entry = self._process_single_file(file_path)
                if entry:
                    await self._add_to_indexes(entry)
            except Exception as e:
                print(f"⚠️ Failed to index {file_path}: {str(e)}")
    
    def _process_single_file(self, file_path: Path) -> Optional[IndexEntry]:
        """
        Process single JSON file and extract index information.
        
        This runs in thread pool for parallel processing.
        """
        try:
            # Load JSON data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract basic metadata
            metadata = data.get('_metadata', {})
            data_type = metadata.get('data_type', 'unknown')
            
            # Extract date from filename or data
            date_str = self._extract_date_from_file(file_path, data)
            timestamp = metadata.get('persisted_at', datetime.now().isoformat())
            
            # Extract searchable fields based on data type
            projects = self._extract_projects(data, data_type)
            employees = self._extract_employees(data, data_type)
            keywords = self._extract_keywords(data)
            
            # Extract performance metrics
            min_score, max_score = self._extract_performance_range(data)
            quality_score = data.get('system_metrics', {}).get('quality_score')
            
            # Create index entry
            entry = IndexEntry(
                file_path=str(file_path.relative_to(file_path.parent.parent)),
                data_type=data_type,
                date=date_str,
                timestamp=timestamp,
                file_size=file_path.stat().st_size,
                metadata=metadata,
                projects=projects,
                employees=employees,
                keywords=keywords,
                min_performance_score=min_score,
                max_performance_score=max_score,
                quality_score=quality_score
            )
            
            return entry
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            return None
    
    def _extract_date_from_file(self, file_path: Path, data: Dict[str, Any]) -> str:
        """Extract date from filename or data"""
        # Try filename first (format: data_type_YYYY-MM-DD.json)
        filename = file_path.stem
        if '_' in filename:
            date_part = filename.split('_')[-1]
            try:
                date.fromisoformat(date_part)
                return date_part
            except ValueError:
                pass
        
        # Try data fields
        for field in ['date', 'generated_at', 'created_at']:
            if field in data:
                value = data[field]
                if isinstance(value, str):
                    # Try to parse as date
                    try:
                        if 'T' in value:  # Datetime
                            return datetime.fromisoformat(value.replace('Z', '+00:00')).date().isoformat()
                        else:  # Date
                            date.fromisoformat(value)
                            return value
                    except ValueError:
                        continue
        
        # Fallback to file modification time
        return datetime.fromtimestamp(file_path.stat().st_mtime).date().isoformat()
    
    def _extract_projects(self, data: Dict[str, Any], data_type: str) -> List[str]:
        """Extract project list from data"""
        projects = []
        
        if data_type == "daily_jira_data":
            if 'projects' in data:
                projects.extend(data['projects'].keys())
        elif data_type == "daily_meeting_data":
            # Extract projects from meeting descriptions
            if 'meetings' in data:
                for meeting in data['meetings']:
                    if 'project' in meeting:
                        projects.append(meeting['project'])
        elif data_type in ["daily_summary_data", "weekly_summary_data"]:
            if 'project_health' in data:
                projects.extend(data['project_health'].keys())
        
        return list(set(projects))  # Remove duplicates
    
    def _extract_employees(self, data: Dict[str, Any], data_type: str) -> List[str]:
        """Extract employee list from data"""
        employees = []
        
        if data_type == "daily_jira_data":
            if 'projects' in data:
                for project_data in data['projects'].values():
                    if 'employees' in project_data:
                        employees.extend(project_data['employees'].keys())
        elif data_type == "daily_meeting_data":
            if 'meetings' in data:
                for meeting in data['meetings']:
                    for participant in meeting.get('participants', []):
                        if 'name' in participant:
                            employees.append(participant['name'])
                    for action in meeting.get('employee_actions', []):
                        if 'employee' in action:
                            employees.append(action['employee'])
        elif data_type == "daily_summary_data":
            if 'employee_performance' in data:
                employees.extend(data['employee_performance'].keys())
        
        return list(set(employees))  # Remove duplicates
    
    def _extract_keywords(self, data: Dict[str, Any]) -> Set[str]:
        """Extract searchable keywords from data"""
        keywords = set()
        
        # Common Jira/project terms
        project_keywords = {
            'blocked', 'in_progress', 'done', 'testing', 'review',
            'sprint', 'backlog', 'epic', 'story', 'task', 'bug',
            'critical', 'high', 'medium', 'low', 'urgent'
        }
        
        # Employee performance keywords
        performance_keywords = {
            'performance', 'score', 'trend', 'improving', 'declining',
            'productivity', 'collaboration', 'meeting', 'action',
            'deadline', 'commit', 'code', 'review', 'merge'
        }
        
        # Search through data for keywords
        def recursive_search(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    # Check key name
                    if key.lower() in project_keywords | performance_keywords:
                        keywords.add(key.lower())
                    
                    # Recursively search value
                    recursive_search(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for item in obj:
                    recursive_search(item, path)
            elif isinstance(obj, str):
                # Check string content for keywords
                words = obj.lower().split()
                for word in words:
                    if word in project_keywords | performance_keywords:
                        keywords.add(word)
        
        recursive_search(data)
        return keywords
    
    def _extract_performance_range(self, data: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
        """Extract min/max performance scores from data"""
        scores = []
        
        def extract_scores(obj):
            if isinstance(obj, dict):
                # Look for performance scores
                for key, value in obj.items():
                    if 'score' in key.lower() and isinstance(value, (int, float)):
                        if 0 <= value <= 10:  # Reasonable performance range
                            scores.append(float(value))
                    elif key in ['performance_score', 'overall_score', 'quality_score']:
                        if isinstance(value, (int, float)):
                            scores.append(float(value))
                    extract_scores(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_scores(item)
        
        extract_scores(data)
        
        if scores:
            return min(scores), max(scores)
        return None, None
    
    async def _add_to_indexes(self, entry: IndexEntry):
        """Add entry to all relevant indexes"""
        # Date-based index (sorted by date for binary search)
        bisect.insort(self._datetime_index, (entry.date, entry))
        
        # Type-based index
        self._type_index[entry.data_type].append(entry)
        
        # Project-based index
        for project in entry.projects:
            self._project_index[project.lower()].append(entry)
        
        # Employee-based index
        for employee in entry.employees:
            self._employee_index[employee.lower()].append(entry)
        
        # Keyword-based index
        for keyword in entry.keywords:
            self._keyword_index[keyword.lower()].append(entry)
        
        # Performance-based index (sorted by min score)
        if entry.min_performance_score is not None:
            bisect.insort(self._performance_index, (entry.min_performance_score, entry))
    
    async def _sort_indexes(self):
        """Sort all indexes for optimal query performance"""
        # Sort each list index by date (newest first)
        for entries in self._type_index.values():
            entries.sort(key=lambda e: e.date, reverse=True)
        
        for entries in self._project_index.values():
            entries.sort(key=lambda e: e.date, reverse=True)
        
        for entries in self._employee_index.values():
            entries.sort(key=lambda e: e.date, reverse=True)
        
        for entries in self._keyword_index.values():
            entries.sort(key=lambda e: e.date, reverse=True)
    
    async def _clear_indexes(self):
        """Clear all indexes"""
        self._datetime_index.clear()
        self._type_index.clear()
        self._project_index.clear()
        self._employee_index.clear()
        self._keyword_index.clear()
        self._performance_index.clear()
    
    async def _save_index(self):
        """Save index to disk for persistence"""
        index_data = {
            'version': self._index_version,
            'last_rebuild': self._last_rebuild.isoformat() if self._last_rebuild else None,
            'datetime_index': [(date, asdict(entry)) for date, entry in self._datetime_index],
            'type_index': {k: [asdict(entry) for entry in v] for k, v in self._type_index.items()},
            'project_index': {k: [asdict(entry) for entry in v] for k, v in self._project_index.items()},
            'employee_index': {k: [asdict(entry) for entry in v] for k, v in self._employee_index.items()},
            'keyword_index': {k: [asdict(entry) for entry in v] for k, v in self._keyword_index.items()},
            'performance_index': [(score, asdict(entry)) for score, entry in self._performance_index]
        }
        
        index_file = self.index_path / "main_index.pkl"
        
        try:
            with open(index_file, 'wb') as f:
                pickle.dump(index_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            print(f"Failed to save index: {str(e)}")
    
    async def load_index(self) -> bool:
        """Load index from disk"""
        index_file = self.index_path / "main_index.pkl"
        
        if not index_file.exists():
            print("⚠️ No saved index found")
            return False
        
        try:
            with open(index_file, 'rb') as f:
                index_data = pickle.load(f)
            
            # Validate index version
            if index_data.get('version') != self._index_version:
                print("⚠️ Index version mismatch, will rebuild")
                return False
            
            # Load indexes
            self._last_rebuild = datetime.fromisoformat(index_data['last_rebuild']) if index_data['last_rebuild'] else None
            
            self._datetime_index = [(date, IndexEntry(**entry)) for date, entry in index_data['datetime_index']]
            self._type_index = {k: [IndexEntry(**entry) for entry in v] for k, v in index_data['type_index'].items()}
            self._project_index = {k: [IndexEntry(**entry) for entry in v] for k, v in index_data['project_index'].items()}
            self._employee_index = {k: [IndexEntry(**entry) for entry in v] for k, v in index_data['employee_index'].items()}
            self._keyword_index = {k: [IndexEntry(**entry) for entry in v] for k, v in index_data['keyword_index'].items()}
            self._performance_index = [(score, IndexEntry(**entry)) for score, entry in index_data['performance_index']]
            
            print(f"✅ Index loaded: {len(self._datetime_index)} entries")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load index: {str(e)}")
            return False
    
    async def query(self, query: JSONQuery) -> List[Dict[str, Any]]:
        """
        Execute optimized query using indexes.
        
        Args:
            query: Query specification
            
        Returns:
            List of matching data entries
        """
        # Check cache first
        cache_key = self._generate_cache_key(query)
        if cache_key in self._query_cache:
            self._cache_hits += 1
            return self._query_cache[cache_key]
        
        self._cache_misses += 1
        
        try:
            # Find candidate entries using indexes
            candidates = await self._find_candidates(query)
            
            # Apply detailed filtering on candidates
            results = []
            for entry in candidates:
                try:
                    # Load full data if needed for complex filtering
                    if self._needs_full_data_load(query):
                        data = await self._load_entry_data(entry)
                        if self._matches_query_data(data, query):
                            results.append({
                                'entry': entry,
                                'data': data
                            })
                    else:
                        results.append({
                            'entry': entry,
                            'data': None  # Metadata only
                        })
                except Exception as e:
                    print(f"Error processing entry {entry.file_path}: {str(e)}")
                    continue
            
            # Sort and limit results
            if query.sort_by:
                results = self._sort_results(results, query.sort_by, query.sort_order)
            
            if query.limit:
                results = results[:query.limit]
            
            # Cache results
            if len(self._query_cache) < self.config.max_results_cache:
                self._query_cache[cache_key] = results
            
            return results
            
        except Exception as e:
            print(f"Query failed: {str(e)}")
            return []
    
    def _generate_cache_key(self, query: JSONQuery) -> str:
        """Generate cache key for query"""
        key_parts = [
            query.data_type or "all",
            str(query.date_range) if query.date_range else "all",
            str([f"{f.field}:{f.operator}:{f.value}" for f in query.filters]) if query.filters else "none",
            query.sort_by or "date",
            query.sort_order or "desc",
            str(query.limit) if query.limit else "all"
        ]
        return "|".join(key_parts)
    
    async def _find_candidates(self, query: JSONQuery) -> List[IndexEntry]:
        """Find candidate entries using optimal index selection"""
        candidates = set()
        
        # Use most selective index first
        if query.data_type:
            # Type filter is very selective
            if query.data_type in self._type_index:
                candidates.update(self._type_index[query.data_type])
        elif query.date_range:
            # Date range filter
            candidates.update(self._find_by_date_range(query.date_range))
        elif query.filters:
            # Use filters to find best index
            candidates.update(self._find_by_filters(query.filters))
        else:
            # No filters - use all entries
            candidates.update(entry for _, entry in self._datetime_index)
        
        return list(candidates)
    
    def _find_by_date_range(self, date_range: DateRange) -> List[IndexEntry]:
        """Find entries in date range using binary search"""
        start_date = date_range.start.isoformat()
        end_date = date_range.end.isoformat()
        
        # Binary search for start position
        start_idx = bisect.bisect_left(self._datetime_index, (start_date, None))
        end_idx = bisect.bisect_right(self._datetime_index, (end_date, None))
        
        return [entry for _, entry in self._datetime_index[start_idx:end_idx]]
    
    def _find_by_filters(self, filters: List[FilterSpec]) -> List[IndexEntry]:
        """Find entries using filter-based index selection"""
        candidates = None
        
        for filter_spec in filters:
            filter_candidates = set()
            
            # Choose best index for this filter
            if filter_spec.field in ['project', 'projects']:
                for project in self._project_index.keys():
                    if filter_spec.operator == "contains" and filter_spec.value.lower() in project:
                        filter_candidates.update(self._project_index[project])
                    elif filter_spec.operator == "equals" and filter_spec.value.lower() == project:
                        filter_candidates.update(self._project_index[project])
            
            elif filter_spec.field in ['employee', 'employees', 'name']:
                for employee in self._employee_index.keys():
                    if filter_spec.operator == "contains" and filter_spec.value.lower() in employee:
                        filter_candidates.update(self._employee_index[employee])
                    elif filter_spec.operator == "equals" and filter_spec.value.lower() == employee:
                        filter_candidates.update(self._employee_index[employee])
            
            elif filter_spec.operator == "contains":
                # Keyword search
                keyword = filter_spec.value.lower()
                if keyword in self._keyword_index:
                    filter_candidates.update(self._keyword_index[keyword])
            
            elif filter_spec.field in ['performance_score', 'score'] and filter_spec.operator in ['greater_than', 'less_than']:
                # Performance range search
                target_score = float(filter_spec.value)
                if filter_spec.operator == "greater_than":
                    start_idx = bisect.bisect_right(self._performance_index, (target_score, None))
                    for _, entry in self._performance_index[start_idx:]:
                        filter_candidates.add(entry)
                else:  # less_than
                    end_idx = bisect.bisect_left(self._performance_index, (target_score, None))
                    for _, entry in self._performance_index[:end_idx]:
                        filter_candidates.add(entry)
            
            # Intersect with previous candidates
            if candidates is None:
                candidates = filter_candidates
            else:
                candidates &= filter_candidates
                
                # Early exit if no candidates left
                if not candidates:
                    break
        
        return list(candidates) if candidates else []
    
    def _needs_full_data_load(self, query: JSONQuery) -> bool:
        """Check if query requires loading full JSON data"""
        if not query.filters:
            return False
        
        for filter_spec in query.filters:
            # These filters can be satisfied by index metadata
            if filter_spec.field in ['project', 'employee', 'date', 'data_type']:
                continue
            
            # These require full data inspection
            if filter_spec.field in ['status', 'summary', 'description', 'content']:
                return True
        
        return False
    
    async def _load_entry_data(self, entry: IndexEntry) -> Dict[str, Any]:
        """Load full JSON data for entry"""
        try:
            # Construct full file path
            base_path = Path("/data/memory/json")
            full_path = base_path / entry.file_path
            
            async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content)
        
        except Exception as e:
            print(f"Failed to load data for {entry.file_path}: {str(e)}")
            return {}
    
    def _matches_query_data(self, data: Dict[str, Any], query: JSONQuery) -> bool:
        """Check if full data matches query filters"""
        if not query.filters:
            return True
        
        for filter_spec in query.filters:
            value = self._get_nested_value(data, filter_spec.field)
            
            if not self._evaluate_filter_condition(value, filter_spec):
                return False
        
        return True
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value by field path"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _evaluate_filter_condition(self, value: Any, filter_spec: FilterSpec) -> bool:
        """Evaluate individual filter condition"""
        if filter_spec.operator == "equals":
            return value == filter_spec.value
        elif filter_spec.operator == "contains":
            return filter_spec.value in str(value)
        elif filter_spec.operator == "greater_than":
            try:
                return float(value) > float(filter_spec.value)
            except (ValueError, TypeError):
                return False
        elif filter_spec.operator == "less_than":
            try:
                return float(value) < float(filter_spec.value)
            except (ValueError, TypeError):
                return False
        elif filter_spec.operator == "exists":
            return value is not None
        
        return False
    
    def _sort_results(
        self, 
        results: List[Dict], 
        sort_by: str, 
        sort_order: str = "desc"
    ) -> List[Dict]:
        """Sort query results"""
        reverse = sort_order.lower() == "desc"
        
        def get_sort_key(item):
            entry = item['entry']
            
            # Handle different sort fields
            if sort_by == "date":
                return entry.date
            elif sort_by == "timestamp":
                return entry.timestamp
            elif sort_by == "file_size":
                return entry.file_size
            elif sort_by == "quality_score":
                return entry.quality_score or 0
            elif sort_by == "performance_score":
                return entry.min_performance_score or 0
            else:
                # Try to get from entry metadata
                return entry.metadata.get(sort_by, 0)
        
        return sorted(results, key=get_sort_key, reverse=reverse)
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics and performance metrics"""
        total_entries = len(self._datetime_index)
        
        stats = {
            "total_entries": total_entries,
            "data_types": {k: len(v) for k, v in self._type_index.items()},
            "projects": len(self._project_index),
            "employees": len(self._employee_index),
            "keywords": len(self._keyword_index),
            "performance_entries": len(self._performance_index),
            "index_version": self._index_version,
            "last_rebuild": self._last_rebuild.isoformat() if self._last_rebuild else None,
            
            "cache_stats": {
                "entries": len(self._query_cache),
                "hits": self._cache_hits,
                "misses": self._cache_misses,
                "hit_rate": self._cache_hits / (self._cache_hits + self._cache_misses) if (self._cache_hits + self._cache_misses) > 0 else 0
            },
            
            "config": {
                "cache_size_mb": self.config.cache_size_mb,
                "rebuild_interval_hours": self.config.rebuild_interval_hours,
                "enable_full_text_search": self.config.enable_full_text_search,
                "max_results_cache": self.config.max_results_cache,
                "parallel_indexing": self.config.parallel_indexing
            }
        }
        
        return stats
    
    async def cleanup_cache(self):
        """Clean up query cache to free memory"""
        self._query_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        print("🧹 Query cache cleared")
    
    async def rebuild_needed(self, data_directory: Path) -> bool:
        """Check if index rebuild is needed"""
        if not self._last_rebuild:
            return True
        
        # Check time since last rebuild
        hours_since_rebuild = (datetime.now() - self._last_rebuild).total_seconds() / 3600
        if hours_since_rebuild > self.config.rebuild_interval_hours:
            return True
        
        # Check if files have been modified since last rebuild
        json_files = list(data_directory.glob("*.json"))
        for file_path in json_files:
            if file_path.stat().st_mtime > self._last_rebuild.timestamp():
                return True
        
        return False
    
    async def close(self):
        """Close index manager and cleanup resources"""
        if self._executor:
            self._executor.shutdown(wait=True)
        
        # Save final index state
        if self._datetime_index:
            await self._save_index()
        
        print("🔚 Index manager closed")


# Convenience functions for index management
async def create_index_manager(
    data_directory: Path,
    config: IndexConfig = None,
    force_rebuild: bool = False
) -> IndexManager:
    """Create and initialize index manager"""
    manager = IndexManager(config)
    
    # Try to load existing index
    if not force_rebuild:
        loaded = await manager.load_index()
        if loaded:
            # Check if rebuild is needed
            if not await manager.rebuild_needed(data_directory):
                return manager
    
    # Build new index
    success = await manager.build_index(data_directory)
    if not success:
        raise RuntimeError("Failed to build index")
    
    return manager


# Query builder helper
class QueryBuilder:
    """Helper class for building complex queries"""
    
    def __init__(self):
        self.query = JSONQuery()
    
    def data_type(self, data_type: str) -> "QueryBuilder":
        self.query.data_type = data_type
        return self
    
    def date_range(self, start: date, end: date) -> "QueryBuilder":
        self.query.date_range = DateRange(start=start, end=end)
        return self
    
    def filter(self, field: str, operator: str, value: Any) -> "QueryBuilder":
        if not self.query.filters:
            self.query.filters = []
        self.query.filters.append(FilterSpec(field=field, operator=operator, value=value))
        return self
    
    def sort_by(self, field: str, order: str = "desc") -> "QueryBuilder":
        self.query.sort_by = field
        self.query.sort_order = order
        return self
    
    def limit(self, limit: int) -> "QueryBuilder":
        self.query.limit = limit
        return self
    
    def build(self) -> JSONQuery:
        return self.query
