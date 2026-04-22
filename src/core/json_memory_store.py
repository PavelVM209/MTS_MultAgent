"""
JSON Memory Store - Phase 1 Foundation Component

Provides JSON-based persistent storage with schema validation,
atomic operations, and indexing for scheduled architecture.
"""

import json
import asyncio
import aiofiles
import logging
import copy
import re
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
import uuid
import shutil
from contextlib import asynccontextmanager

from .models import JSONEvent, JSONState, JSONIndex
from .schemas import (
    JiraAnalysisSchema, MeetingAnalysisSchema, 
    DailySummarySchema, WeeklySummarySchema
)

logger = logging.getLogger(__name__)


@dataclass
class StorageConfig:
    """Configuration for JSON memory store"""
    base_path: Path = Path("./data/memory/json")
    backup_path: Path = Path("./data/memory/backups")
    max_file_size_mb: int = 100
    retention_days: int = 365
    enable_compression: bool = True
    atomic_writes: bool = True


class JSONMemoryStore:
    """
    JSON-based memory store with schema validation and atomic operations.
    
    Provides the foundation for scheduled architecture data persistence.
    """
    
    def __init__(self, config: StorageConfig = None):
        self.config = config or StorageConfig()
        self.base_path = self.config.base_path
        self.backup_path = self.config.backup_path
        self.schemas = self._load_schemas()
        
        # Ensure directories exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.backup_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize subdirectories
        (self.base_path / "history").mkdir(exist_ok=True)
        (self.base_path / "temp").mkdir(exist_ok=True)
    
    def _load_schemas(self) -> Dict[str, Any]:
        """Load JSON schemas for validation"""
        return {
            "daily_jira_data": JiraAnalysisSchema(),
            "daily_meeting_data": MeetingAnalysisSchema(),
            "daily_summary_data": DailySummarySchema(),
            "weekly_summary_data": WeeklySummarySchema()
        }
    
    async def persist_json_data(
        self, 
        data_type: str, 
        data: Dict[str, Any],
        target_date: Union[str, date] = None
    ) -> str:
        """
        Persist JSON data with schema validation and atomic write.
        
        Args:
            data_type: Type of data (e.g., "daily_jira_data")
            data: JSON data to persist
            target_date: Date for filename (defaults to today)
            
        Returns:
            File path of persisted data
            
        Raises:
            ValidationError: If data doesn't match schema
            StorageError: If write operation fails
        """
        try:
            if target_date is None:
                data_date = data.get("date")
                if isinstance(data_date, str):
                    try:
                        target_date = datetime.strptime(data_date, "%Y-%m-%d").date()
                    except ValueError:
                        target_date = None

            if target_date is None:
                target_date = date.today()
            elif isinstance(target_date, str):
                target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

            filename = f"{data_type}_{target_date.strftime('%Y-%m-%d')}.json"
            file_path = self.base_path / filename

            # Schema Validation
            schema = self.schemas.get(data_type)
            if schema:
                validation_result = await schema.validate(data)
                if not validation_result.valid:
                    raise ValidationError(f"Schema validation failed: {validation_result.errors}")

            # Data Enrichment
            enriched_data = await self._enrich_with_metadata(data, data_type)

            # Atomic Write
            await self._atomic_json_write(file_path, enriched_data)

            # Update Indexes
            await self._update_indexes(data_type, file_path, enriched_data)

            # Cleanup Old Files
            await self._cleanup_old_data(data_type)

            return str(file_path)

        except ValidationError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to persist {data_type}: {str(e)}")
    
    async def load_json_data(
        self, 
        data_type: str, 
        target_date: Union[str, date] = None
    ) -> Dict[str, Any]:
        """
        Load JSON data with schema validation.
        
        Args:
            data_type: Type of data to load
            target_date: Date for file (defaults to today)
            
        Returns:
            Loaded JSON data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValidationError: If loaded data doesn't match schema
        """
        try:
            # 🔹 File Path Resolution
            if target_date is None:
                target_date = date.today()
            elif isinstance(target_date, str):
                target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
            
            filename = f"{data_type}_{target_date.strftime('%Y-%m-%d')}.json"
            file_path = self.base_path / filename
            
            if not file_path.exists():
                # Try to find most recent file if specific date not found
                file_path = await self._find_most_recent_file(data_type)
                if not file_path or not file_path.exists():
                    raise FileNotFoundError(f"No {data_type} file found for {target_date}")
            
            # 🔹 Load JSON Data
            data = await self._load_json_file(file_path)
            
            # 🔹 Validate on Load
            schema = self.schemas.get(data_type)
            if schema:
                validation_result = await schema.validate(data)
                if not validation_result.valid:
                    raise ValidationError(f"Loaded data validation failed: {validation_result.errors}")
            
            return data
            
        except Exception as e:
            if isinstance(e, (FileNotFoundError, ValidationError)):
                raise
            raise StorageError(f"Failed to load {data_type}: {str(e)}")
    
    async def query_json_data(
        self, 
        query: "JSONQuery"
    ) -> List[Dict[str, Any]]:
        """
        Query JSON data using file-based indexes.
        
        Args:
            query: Query specification with filters
            
        Returns:
            List of matching JSON records
        """
        try:
            # 🔹 Find Candidate Files
            candidate_files = await self._find_candidate_files(query)
            
            results = []
            for file_path in candidate_files:
                try:
                    data = await self._load_json_file(file_path)
                    
                    # 🔹 Apply Query Filters
                    if await self._matches_query(data, query):
                        results.append({
                            "file_path": str(file_path),
                            "data": data,
                            "metadata": data.get("_metadata", {})
                        })
                        
                except Exception as e:
                    # Log error but continue with other files
                    print(f"Error querying file {file_path}: {str(e)}")
                    continue
            
            # 🔹 Sort and Limit Results
            if query.sort_by:
                results = await self._sort_results(results, query.sort_by, query.sort_order)
            
            if query.limit:
                results = results[:query.limit]
            
            return results
            
        except Exception as e:
            raise StorageError(f"Query failed: {str(e)}")
    
    async def _enrich_with_metadata(
        self, 
        data: Dict[str, Any], 
        data_type: str
    ) -> Dict[str, Any]:
        """Enrich data with metadata"""
        enriched_data = copy.deepcopy(data)

        quality_score = None
        system_metrics = enriched_data.get("system_metrics")
        if isinstance(system_metrics, dict):
            quality_score = system_metrics.get("quality_score")
        
        metadata = {
            "data_type": data_type,
            "persisted_at": datetime.now().isoformat(),
            "persisted_by": "MTS_MultAgent_v3",
            "version": "1.0.0",
            "file_id": str(uuid.uuid4()),
            "size_bytes": len(json.dumps(data, default=str)),
            "quality_score": quality_score,
        }
        
        enriched_data["_metadata"] = metadata
        return enriched_data
    
    async def _atomic_json_write(self, file_path: Path, data: Dict[str, Any]):
        """Atomically write JSON data to file"""
        temp_path = file_path.with_suffix(f".{uuid.uuid4().hex}.tmp")
        
        try:
            # Write to temp file first
            async with aiofiles.open(temp_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, default=str, ensure_ascii=False))
            
            # Atomic move
            temp_path.replace(file_path)
            
        except Exception as e:
            # Cleanup temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise e
    
    async def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON data from file"""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            return json.loads(content)
    
    async def _find_most_recent_file(self, data_type: str) -> Optional[Path]:
        """Find most recent file for data type"""
        pattern = f"{data_type}_*.json"
        files = list(self.base_path.glob(pattern))
        
        if not files:
            return None
        
        # Sort by modification time (most recent first)
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return files[0]
    
    async def _find_candidate_files(self, query: "JSONQuery") -> List[Path]:
        """Find candidate files based on query criteria"""
        if query.data_type:
            pattern = f"{query.data_type}_*.json"
        else:
            pattern = "*.json"
        
        files = list(self.base_path.glob(pattern))
        
        # Filter by date range if specified
        if query.date_range:
            filtered_files = []
            for file_path in files:
                # Extract date from filename
                try:
                    filename = file_path.stem
                    date_part = filename.split('_')[-1]
                    file_date = datetime.strptime(date_part, "%Y-%m-%d").date()
                    
                    if query.date_range.start <= file_date <= query.date_range.end:
                        filtered_files.append(file_path)
                except ValueError:
                    continue
            
            files = filtered_files
        
        return files
    
    async def _matches_query(self, data: Dict[str, Any], query: "JSONQuery") -> bool:
        """Check if data matches query filters"""
        if not query.filters:
            return True
        
        for filter_spec in query.filters:
            field_path = filter_spec.field.split('.')
            current_value = data
            
            # Navigate nested fields
            for path_part in field_path:
                if isinstance(current_value, dict) and path_part in current_value:
                    current_value = current_value[path_part]
                else:
                    current_value = None
                    break
            
            # Apply filter condition
            if not self._evaluate_filter_condition(current_value, filter_spec):
                return False
        
        return True
    
    def _evaluate_filter_condition(self, value: Any, filter_spec: "FilterSpec") -> bool:
        """Evaluate individual filter condition"""
        if filter_spec.operator == "equals":
            return value == filter_spec.value
        elif filter_spec.operator == "contains":
            return filter_spec.value in str(value)
        elif filter_spec.operator == "greater_than":
            return value > filter_spec.value
        elif filter_spec.operator == "less_than":
            return value < filter_spec.value
        elif filter_spec.operator == "exists":
            return value is not None
        
        return False
    
    async def _sort_results(
        self, 
        results: List[Dict], 
        sort_by: str, 
        sort_order: str = "desc"
    ) -> List[Dict]:
        """Sort results by specified field"""
        reverse = sort_order.lower() == "desc"
        
        def get_sort_key(item):
            # Navigate to sort field
            current_value = item.get("data", item)
            for path_part in sort_by.split('.'):
                if isinstance(current_value, (dict, list)) and path_part in current_value:
                    current_value = current_value[path_part]
                else:
                    current_value = None
                    break
            return (current_value is None, current_value)
        
        return sorted(results, key=get_sort_key, reverse=reverse)
    
    async def _update_indexes(
        self, 
        data_type: str, 
        file_path: Path, 
        data: Dict[str, Any]
    ):
        """Update file-based indexes"""
        # Simple indexing by date and type for now
        # Can be extended with more sophisticated indexing
        index_file = self.base_path / ".index.json"
        
        try:
            if index_file.exists():
                index_data = await self._load_json_file(index_file)
            else:
                index_data = {"files": [], "last_updated": None}
            
            # Add file to index
            file_info = {
                "path": str(file_path.relative_to(self.base_path)),
                "data_type": data_type,
                "created_at": datetime.now().isoformat(),
                "size": file_path.stat().st_size,
                "metadata": data.get("_metadata", {})
            }
            
            index_data["files"].append(file_info)
            index_data["last_updated"] = datetime.now().isoformat()
            
            # Keep index clean
            index_data["files"] = [
                f for f in index_data["files"] 
                if (self.base_path / f["path"]).exists()
            ]
            
            await self._atomic_json_write(index_file, index_data)
            
        except Exception as e:
            # Index failures shouldn't stop main operations
            print(f"Index update failed: {str(e)}")
    
    async def _cleanup_old_data(self, data_type: str):
        """Clean up old data based on retention policy"""
        try:
            cutoff_date = date.fromordinal(date.today().toordinal() - self.config.retention_days)
            pattern = f"{data_type}_*.json"
            files = list(self.base_path.glob(pattern))
            
            for file_path in files:
                try:
                    # Extract date from filename
                    filename = file_path.stem
                    date_part = filename.split('_')[-1]
                    file_date = datetime.strptime(date_part, "%Y-%m-%d").date()
                    
                    if file_date < cutoff_date:
                        # Move to history or archive
                        history_path = self.base_path / "history" / file_path.name
                        history_path.parent.mkdir(exist_ok=True)
                        
                        if history_path.exists():
                            history_path.unlink()
                        
                        shutil.move(str(file_path), str(history_path))
                        
                except ValueError:
                    # Skip files with invalid date format
                    continue
                    
        except Exception as e:
            print(f"Cleanup failed for {data_type}: {str(e)}")
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            files = [
                file_path
                for file_path in self.base_path.glob("*.json")
                if not file_path.name.startswith(".")
            ]
            total_size = sum(f.stat().st_size for f in files)
            
            # Count by data type
            type_counts = {}
            for file_path in files:
                data_type = re.sub(r"_\d{4}-\d{2}-\d{2}$", "", file_path.stem)
                type_counts[data_type] = type_counts.get(data_type, 0) + 1
            
            return {
                "total_files": len(files),
                "total_size_bytes": total_size,
                "total_size_mb": max(round(total_size / (1024 * 1024), 4), 0.0001) if total_size else 0.0,
                "files_by_type": type_counts,
                "storage_path": str(self.base_path),
                "retention_days": self.config.retention_days
            }
            
        except Exception as e:
            raise StorageError(f"Failed to get storage stats: {str(e)}")
    
    async def save_record(
        self,
        data: Dict[str, Any],
        record_type: str,
        record_id: str = None,
        source: str = "unknown"
    ) -> str:
        """
        Save a record with automatic type handling and ID generation.
        
        This method provides a simplified interface for saving records
        that can be used by agents without worrying about file paths.
        
        Args:
            data: Record data to save
            record_type: Type of record (e.g., 'quality_validation', 'employee_analysis')
            record_id: Optional record ID (auto-generated if not provided)
            source: Source of the record (agent name, system component)
            
        Returns:
            Record ID and file path
        """
        try:
            # Generate record ID if not provided
            if record_id is None:
                record_id = f"{record_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # Enrich data with record metadata
            enriched_data = {
                "record_id": record_id,
                "record_type": record_type,
                "source": source,
                "created_at": datetime.now().isoformat(),
                "data": data
            }
            
            # Determine data type for schema validation
            data_type_mapping = {
                "quality_validation": "daily_summary_data",
                "employee_analysis": "daily_jira_data", 
                "employee_analysis_record": "daily_jira_data",
                "meeting_analysis": "daily_meeting_data",
                "weekly_report": "weekly_summary_data"
            }
            
            mapped_data_type = data_type_mapping.get(record_type, "daily_summary_data")
            
            # Save using persist_json_data
            file_path = await self.persist_json_data(
                data_type=mapped_data_type,
                data=enriched_data,
                target_date=date.today()
            )
            
            logger.info(f"Record saved: {record_id} -> {file_path}")
            return record_id
            
        except Exception as e:
            logger.error(f"Failed to save record {record_id}: {e}")
            raise StorageError(f"Failed to save record: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on storage system"""
        try:
            stats = await self.get_storage_stats()
            
            # Check directory permissions
            try:
                test_file = self.base_path / ".health_check"
                test_file.touch()
                test_file.unlink()
                permissions_ok = True
            except Exception:
                permissions_ok = False
            
            # Check disk space (basic check)
            stat = shutil.disk_usage(str(self.base_path))
            free_space_gb = round(stat.free / (1024**3), 2)
            
            # Check if store is healthy for common operations
            try:
                # Test basic operations
                await self.get_storage_stats()
                is_healthy = True
            except Exception:
                is_healthy = False
            
            return {
                "status": "healthy" if permissions_ok and is_healthy else "unhealthy",
                "permissions_ok": permissions_ok,
                "free_space_gb": free_space_gb,
                "storage_stats": stats,
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }


# Exception classes
class ValidationError(Exception):
    """Schema validation error"""
    pass


class StorageError(Exception):
    """Storage operation error"""
    pass


# Query-related classes (simplified for now)
@dataclass
class FilterSpec:
    field: str
    operator: str  # equals, contains, greater_than, less_than, exists
    value: Any


@dataclass
class DateRange:
    start: date
    end: date


@dataclass
class JSONQuery:
    data_type: Optional[str] = None
    filters: Optional[List[FilterSpec]] = None
    date_range: Optional[DateRange] = None
    sort_by: Optional[str] = None
    sort_order: str = "desc"
    limit: Optional[int] = None


# Convenience functions for common operations
async def create_memory_store(config: StorageConfig = None) -> JSONMemoryStore:
    """Create and initialize JSON memory store"""
    try:
        store = JSONMemoryStore(config)

        # Perform health check
        health = await store.health_check()
        if health["status"] != "healthy":
            raise StorageError(f"Memory store health check failed: {health}")

        return store
    except StorageError:
        raise
    except Exception as e:
        raise StorageError(f"Failed to create memory store: {e}")
