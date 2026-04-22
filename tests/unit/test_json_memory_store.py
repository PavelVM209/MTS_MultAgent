"""
Unit Tests for JSON Memory Store - Phase 1 Foundation Components

Tests schema validation, atomic operations, and data persistence.
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from datetime import datetime, date
from unittest.mock import patch, AsyncMock

# Import components under test
from src.core.json_memory_store import (
    JSONMemoryStore, StorageConfig, ValidationError, StorageError,
    create_memory_store, JSONQuery, FilterSpec, DateRange
)
from src.core.schemas import JiraAnalysisSchema, MeetingAnalysisSchema


class TestJSONMemoryStore:
    """Test suite for JSON Memory Store"""
    
    @pytest.fixture
    async def temp_store(self):
        """Create temporary store for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = StorageConfig(
                base_path=Path(temp_dir) / "memory" / "json",
                backup_path=Path(temp_dir) / "memory" / "backups",
                retention_days=30  # Short retention for testing
            )
            store = JSONMemoryStore(config)
            yield store
    
    @pytest.fixture
    def sample_jira_data(self):
        """Sample Jira analysis data for testing"""
        return {
            "date": "2026-03-25",
            "timestamp": "2026-03-25T19:00:00",
            "projects": {
                "CSI": {
                    "total_tasks": 45,
                    "completed_tasks": 12,
                    "in_progress_tasks": 25,
                    "blocked_tasks": 8,
                    "employees": {
                        "john.doe": {
                            "username": "john.doe",
                            "tasks": {
                                "total": 10,
                                "completed": 3,
                                "in_progress": 5,
                                "blocked": 2
                            },
                            "metrics": {
                                "performance_score": 7.5,
                                "completion_rate": 30.0,
                                "avg_task_duration": 2.5
                            }
                        }
                    }
                }
            },
            "system_metrics": {
                "jira_api_calls": 25,
                "processing_time_seconds": 45,
                "quality_score": 92
            }
        }
    
    @pytest.fixture
    def sample_meeting_data(self):
        """Sample meeting analysis data for testing"""
        return {
            "date": "2026-03-25",
            "processed_files": ["/data/protocols/daily_standup_2026-03-25.txt"],
            "meetings": [
                {
                    "meeting_type": "daily_standup",
                    "date": "2026-03-25",
                    "participants": [
                        {"name": "John Doe", "role": "Developer"},
                        {"name": "Jane Smith", "role": "Team Lead"}
                    ],
                    "employee_actions": [
                        {
                            "employee": "John Doe",
                            "action": "Fix authentication bug in login module",
                            "deadline": "2026-03-26",
                            "priority": "high"
                        }
                    ]
                }
            ],
            "daily_employee_summary": {
                "John Doe": {
                    "meetings_attended": 1,
                    "action_items_assigned": 2,
                    "action_items_completed": 1,
                    "participation_score": 8.0
                }
            },
            "system_metrics": {
                "files_processed": 1,
                "processing_time_seconds": 15,
                "quality_score": 88
            }
        }
    
    @pytest.mark.asyncio
    async def test_store_initialization(self, temp_store):
        """Test store initialization creates directories"""
        assert temp_store.base_path.exists()
        assert temp_store.backup_path.exists()
        assert (temp_store.base_path / "history").exists()
        assert (temp_store.base_path / "temp").exists()
    
    @pytest.mark.asyncio
    async def test_persist_jira_data_success(self, temp_store, sample_jira_data):
        """Test successful Jira data persistence"""
        file_path = await temp_store.persist_json_data(
            "daily_jira_data", 
            sample_jira_data,
            date.fromisoformat("2026-03-25")
        )
        
        assert file_path is not None
        assert Path(file_path).exists()
        
        # Verify file content
        with open(file_path, 'r') as f:
            saved_data = json.load(f)
        
        # Check metadata was added
        assert "_metadata" in saved_data
        assert saved_data["_metadata"]["data_type"] == "daily_jira_data"
        assert saved_data["_metadata"]["persisted_by"] == "MTS_MultAgent_v3"
        
        # Check original data is intact
        assert saved_data["date"] == sample_jira_data["date"]
        assert saved_data["projects"]["CSI"]["total_tasks"] == 45
    
    @pytest.mark.asyncio
    async def test_persist_meeting_data_success(self, temp_store, sample_meeting_data):
        """Test successful meeting data persistence"""
        file_path = await temp_store.persist_json_data(
            "daily_meeting_data", 
            sample_meeting_data,
            date.fromisoformat("2026-03-25")
        )
        
        assert file_path is not None
        assert Path(file_path).exists()
        
        # Verify file content
        with open(file_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["_metadata"]["data_type"] == "daily_meeting_data"
        assert saved_data["meetings"][0]["meeting_type"] == "daily_standup"
    
    @pytest.mark.asyncio
    async def test_schema_validation_failure(self, temp_store):
        """Test schema validation rejects invalid data"""
        invalid_data = {
            "date": "2026-03-25",
            # Missing required fields
            "invalid_field": "value"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            await temp_store.persist_json_data("daily_jira_data", invalid_data)
        
        assert "Required field" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_load_json_data_success(self, temp_store, sample_jira_data):
        """Test successful JSON data loading"""
        # First save data
        await temp_store.persist_json_data("daily_jira_data", sample_jira_data)
        
        # Then load it
        loaded_data = await temp_store.load_json_data("daily_jira_data")
        
        assert loaded_data["date"] == sample_jira_data["date"]
        assert loaded_data["projects"]["CSI"]["total_tasks"] == 45
        assert "_metadata" in loaded_data
    
    @pytest.mark.asyncio
    async def test_load_json_data_not_found(self, temp_store):
        """Test loading non-existent data raises FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            await temp_store.load_json_data("daily_jira_data", "2026-01-01")
    
    @pytest.mark.asyncio
    async def test_load_json_data_finds_most_recent(self, temp_store, sample_jira_data):
        """Test loading finds most recent file when specific date not found"""
        # Save data for specific date
        await temp_store.persist_json_data(
            "daily_jira_data", 
            sample_jira_data,
            date.fromisoformat("2026-03-25")
        )
        
        # Try to load different date - should find most recent
        loaded_data = await temp_store.load_json_data("daily_jira_data", "2026-01-01")
        
        assert loaded_data is not None
        assert loaded_data["date"] == "2026-03-25"
    
    @pytest.mark.asyncio
    async def test_query_json_data_basic(self, temp_store, sample_jira_data):
        """Test basic JSON query functionality"""
        # Save test data
        await temp_store.persist_json_data("daily_jira_data", sample_jira_data)
        
        # Query by data type
        query = JSONQuery(data_type="daily_jira_data")
        results = await temp_store.query_json_data(query)
        
        assert len(results) == 1
        assert results[0]["data"]["date"] == sample_jira_data["date"]
    
    @pytest.mark.asyncio
    async def test_query_json_data_with_filters(self, temp_store, sample_jira_data):
        """Test JSON query with filters"""
        # Save test data
        await temp_store.persist_json_data("daily_jira_data", sample_jira_data)
        
        # Query with project filter
        query = JSONQuery(
            data_type="daily_jira_data",
            filters=[
                FilterSpec(field="projects.CSI.total_tasks", operator="equals", value=45)
            ]
        )
        results = await temp_store.query_json_data(query)
        
        assert len(results) == 1
        assert results[0]["data"]["projects"]["CSI"]["total_tasks"] == 45
    
    @pytest.mark.asyncio
    async def test_query_json_data_date_range(self, temp_store, sample_jira_data, sample_meeting_data):
        """Test JSON query with date range"""
        # Save test data for different dates
        jira_data_mar25 = sample_jira_data.copy()
        jira_data_mar25["date"] = "2026-03-25"
        await temp_store.persist_json_data("daily_jira_data", jira_data_mar25, date(2026, 3, 25))
        
        jira_data_mar26 = sample_jira_data.copy()
        jira_data_mar26["date"] = "2026-03-26"
        await temp_store.persist_json_data("daily_jira_data", jira_data_mar26, date(2026, 3, 26))
        
        # Query for specific date range
        query = JSONQuery(
            data_type="daily_jira_data",
            date_range=DateRange(start=date(2026, 3, 25), end=date(2026, 3, 25))
        )
        results = await temp_store.query_json_data(query)
        
        assert len(results) == 1
        assert results[0]["data"]["date"] == "2026-03-25"
    
    @pytest.mark.asyncio
    async def test_query_json_data_sorting(self, temp_store, sample_jira_data):
        """Test JSON query sorting functionality"""
        # Save multiple entries
        for i in range(3):
            data = sample_jira_data.copy()
            data["date"] = f"2026-03-{25+i:02d}"
            data["system_metrics"]["quality_score"] = 90 + i
            await temp_store.persist_json_data("daily_jira_data", data)
        
        # Query sorted by quality score
        query = JSONQuery(
            data_type="daily_jira_data",
            sort_by="_metadata.quality_score",
            sort_order="asc"
        )
        results = await temp_store.query_json_data(query)
        
        assert len(results) == 3
        assert results[0]["data"]["system_metrics"]["quality_score"] == 90
        assert results[2]["data"]["system_metrics"]["quality_score"] == 92
    
    @pytest.mark.asyncio
    async def test_atomic_write_error_handling(self, temp_store, sample_jira_data):
        """Test atomic write handles errors correctly"""
        # Mock file operations to raise exception
        with patch('aiofiles.open', side_effect=IOError("Disk full")):
            with pytest.raises(StorageError):
                await temp_store.persist_json_data("daily_jira_data", sample_jira_data)
        
        # Ensure no partial file exists
        files = list(temp_store.base_path.glob("daily_jira_data_*.json"))
        assert len(files) == 0
    
    @pytest.mark.asyncio
    async def test_data_retention_cleanup(self, temp_store, sample_jira_data):
        """Test old data cleanup based on retention policy"""
        # Create old file (outside retention window)
        old_date = date(2026, 2, 20)  # More than 30 days ago
        await temp_store.persist_json_data("daily_jira_data", sample_jira_data, old_date)
        
        # Create recent file (within retention window)
        recent_date = date(2026, 3, 25)
        await temp_store.persist_json_data("daily_jira_data", sample_jira_data, recent_date)
        
        # Manually trigger cleanup by persisting new data
        await temp_store.persist_json_data("daily_jira_data", sample_jira_data, date.today())
        
        # Check that old file was moved to history
        main_files = list(temp_store.base_path.glob("daily_jira_data_*.json"))
        history_files = list((temp_store.base_path / "history").glob("daily_jira_data_*.json"))
        
        # Should have recent files in main, old file in history
        assert len(main_files) >= 2  # Recent files
        assert len(history_files) >= 1  # Old file moved to history
    
    @pytest.mark.asyncio
    async def test_health_check(self, temp_store):
        """Test store health check functionality"""
        health = await temp_store.health_check()
        
        assert health["status"] == "healthy"
        assert "permissions_ok" in health
        assert "free_space_gb" in health
        assert "storage_stats" in health
        assert "last_check" in health
    
    @pytest.mark.asyncio
    async def test_get_storage_stats(self, temp_store, sample_jira_data, sample_meeting_data):
        """Test storage statistics functionality"""
        # Save some test data
        await temp_store.persist_json_data("daily_jira_data", sample_jira_data)
        await temp_store.persist_json_data("daily_meeting_data", sample_meeting_data)
        
        stats = await temp_store.get_storage_stats()
        
        assert stats["total_files"] == 2
        assert stats["total_size_mb"] > 0
        assert "daily_jira_data" in stats["files_by_type"]
        assert "daily_meeting_data" in stats["files_by_type"]
        assert stats["retention_days"] == 30
    
    @pytest.mark.asyncio
    async def test_create_memory_store_function(self, sample_jira_data):
        """Test convenience function for creating store"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = StorageConfig(base_path=Path(temp_dir) / "store")
            
            store = await create_memory_store(config)
            
            # Should be healthy
            health = await store.health_check()
            assert health["status"] == "healthy"
            
            # Should be functional
            await store.persist_json_data("daily_jira_data", sample_jira_data)
            loaded = await store.load_json_data("daily_jira_data")
            assert loaded is not None
    
    @pytest.mark.asyncio
    async def test_create_memory_store_health_check_failure(self):
        """Test store creation fails on health check"""
        # Create config with invalid path
        config = StorageConfig(base_path=Path("/invalid/path/that/does/not/exist"))
        
        with pytest.raises(StorageError):
            await create_memory_store(config)
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, temp_store, sample_jira_data):
        """Test concurrent read/write operations"""
        # Create multiple concurrent operations
        async def persist_data(i):
            data = sample_jira_data.copy()
            data["date"] = f"2026-03-{25+i:02d}"
            return await temp_store.persist_json_data("daily_jira_data", data)
        
        async def load_data(i):
            return await temp_store.load_json_data("daily_jira_data", f"2026-03-{25+i:02d}")
        
        # Run concurrent operations
        persist_tasks = [persist_data(i) for i in range(5)]
        persist_results = await asyncio.gather(*persist_tasks)
        
        # Verify all writes succeeded
        assert len(persist_results) == 5
        for result in persist_results:
            assert result is not None
            assert Path(result).exists()
        
        # Verify reads work
        load_tasks = [load_data(i) for i in range(5)]
        load_results = await asyncio.gather(*load_tasks)
        
        assert len(load_results) == 5
        for result in load_results:
            assert result is not None
            assert "date" in result


class TestJSONQuery:
    """Test suite for JSON query functionality"""
    
    def test_query_builder_basic(self):
        """Test basic query building"""
        from src.core.index_manager import QueryBuilder
        
        query = (QueryBuilder()
                .data_type("daily_jira_data")
                .filter("project", "equals", "CSI")
                .sort_by("date", "desc")
                .limit(10)
                .build())
        
        assert query.data_type == "daily_jira_data"
        assert len(query.filters) == 1
        assert query.filters[0].field == "project"
        assert query.filters[0].operator == "equals"
        assert query.filters[0].value == "CSI"
        assert query.sort_by == "date"
        assert query.sort_order == "desc"
        assert query.limit == 10
    
    def test_filter_spec_creation(self):
        """Test FilterSpec creation"""
        filter_spec = FilterSpec(field="status", operator="equals", value="done")
        
        assert filter_spec.field == "status"
        assert filter_spec.operator == "equals"
        assert filter_spec.value == "done"
    
    def test_date_range_creation(self):
        """Test DateRange creation"""
        start = date(2026, 3, 25)
        end = date(2026, 3, 31)
        date_range = DateRange(start=start, end=end)
        
        assert date_range.start == start
        assert date_range.end == end


if __name__ == "__main__":
    pytest.main([__file__])
