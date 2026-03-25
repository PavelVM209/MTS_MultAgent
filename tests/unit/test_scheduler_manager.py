"""
Unit Tests for Scheduler Manager - Phase 3 Foundation Component

Tests APScheduler integration with timezone handling,
job persistence, recovery, and health monitoring.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.core.scheduler_manager import (
    SchedulerManager,
    JobConfig,
    JobStatus,
    SchedulerStatus,
    JobExecutionResult,
    SchedulerHealth
)


class TestJobConfig:
    """Test job configuration dataclass"""
    
    def test_job_config_creation(self):
        """Test job configuration creation"""
        def sample_func():
            pass
        
        job_config = JobConfig(
            id="test_job",
            name="Test Job",
            func=sample_func,
            trigger_type="cron",
            trigger_config={"minute": "0", "hour": "9"}
        )
        
        assert job_config.id == "test_job"
        assert job_config.name == "Test Job"
        assert job_config.func == sample_func
        assert job_config.trigger_type == "cron"
        assert job_config.trigger_config == {"minute": "0", "hour": "9"}
        assert job_config.enabled is True
        assert job_config.max_instances == 1
        assert job_config.misfire_grace_time == 300
        assert job_config.coalesce is True
    
    def test_job_config_to_dict(self):
        """Test job configuration serialization"""
        def sample_func():
            pass
        
        job_config = JobConfig(
            id="test_job",
            name="Test Job",
            func=sample_func,
            trigger_type="cron",
            trigger_config={"minute": "0", "hour": "9"},
            args=[1, 2, 3],
            kwargs={"key": "value"},
            description="Test job description"
        )
        
        job_dict = job_config.to_dict()
        
        assert job_dict["id"] == "test_job"
        assert job_dict["name"] == "Test Job"
        assert job_dict["trigger_type"] == "cron"
        assert job_dict["trigger_config"] == {"minute": "0", "hour": "9"}
        assert job_dict["args"] == [1, 2, 3]
        assert job_dict["kwargs"] == {"key": "value"}
        assert job_dict["description"] == "Test job description"
        assert job_dict["enabled"] is True
        assert job_dict["max_instances"] == 1
        assert job_dict["misfire_grace_time"] == 300
        assert job_dict["coalesce"] is True


class TestJobExecutionResult:
    """Test job execution result dataclass"""
    
    def test_job_execution_result_creation(self):
        """Test job execution result creation"""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=5)
        
        result = JobExecutionResult(
            job_id="test_job",
            status=JobStatus.COMPLETED,
            start_time=start_time,
            end_time=end_time,
            result={"success": True}
        )
        
        assert result.job_id == "test_job"
        assert result.status == JobStatus.COMPLETED
        assert result.start_time == start_time
        assert result.end_time == end_time
        assert result.result == {"success": True}
        assert result.error is None
        assert result.traceback is None
    
    def test_job_execution_result_to_dict(self):
        """Test job execution result serialization"""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=5)
        
        result = JobExecutionResult(
            job_id="test_job",
            status=JobStatus.ERROR,
            start_time=start_time,
            end_time=end_time,
            error="Test error",
            traceback="Test traceback"
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["job_id"] == "test_job"
        assert result_dict["status"] == "error"
        assert result_dict["start_time"] == start_time.isoformat()
        assert result_dict["end_time"] == end_time.isoformat()
        assert result_dict["error"] == "Test error"
        assert result_dict["traceback"] == "Test traceback"


class TestSchedulerManager:
    """Test scheduler manager functionality"""
    
    @pytest.fixture
    def scheduler_manager(self):
        """Create scheduler manager instance for testing"""
        return SchedulerManager(timezone_str="Europe/Moscow")
    
    @pytest.fixture
    def sample_job_func(self):
        """Sample job function for testing"""
        async def sample_job():
            await asyncio.sleep(0.1)
            return {"result": "success"}
        return sample_job
    
    def test_scheduler_manager_initialization(self, scheduler_manager):
        """Test scheduler manager initialization"""
        assert scheduler_manager.timezone.zone == "Europe/Moscow"
        assert scheduler_manager.scheduler is None
        assert scheduler_manager.job_configs == {}
        assert scheduler_manager.job_executions == []
        assert scheduler_manager.health.status == SchedulerStatus.STOPPED
        assert scheduler_manager.startup_time is None
    
    @pytest.mark.asyncio
    async def test_scheduler_initialize(self, scheduler_manager):
        """Test scheduler initialization"""
        await scheduler_manager.initialize()
        
        assert scheduler_manager.scheduler is not None
        assert scheduler_manager.health.status == SchedulerStatus.STARTING
    
    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self, scheduler_manager):
        """Test scheduler start and stop"""
        await scheduler_manager.initialize()
        await scheduler_manager.start()
        
        assert scheduler_manager.scheduler.running
        assert scheduler_manager.health.status == SchedulerStatus.RUNNING
        assert scheduler_manager.startup_time is not None
        
        await scheduler_manager.stop()
        
        assert not scheduler_manager.scheduler.running
        assert scheduler_manager.health.status == SchedulerStatus.STOPPED
    
    @pytest.mark.asyncio
    async def test_add_job(self, scheduler_manager, sample_job_func):
        """Test adding a job to scheduler"""
        await scheduler_manager.initialize()
        await scheduler_manager.start()
        
        job_config = JobConfig(
            id="test_job",
            name="Test Job",
            func=sample_job_func,
            trigger_type="interval",
            trigger_config={"seconds": 10}
        )
        
        job_id = await scheduler_manager.add_job(job_config)
        
        assert job_id == "test_job"
        assert "test_job" in scheduler_manager.job_configs
        assert scheduler_manager.scheduler.get_job("test_job") is not None
    
    @pytest.mark.asyncio
    async def test_remove_job(self, scheduler_manager, sample_job_func):
        """Test removing a job from scheduler"""
        await scheduler_manager.initialize()
        await scheduler_manager.start()
        
        job_config = JobConfig(
            id="test_job",
            name="Test Job",
            func=sample_job_func,
            trigger_type="interval",
            trigger_config={"seconds": 10}
        )
        
        await scheduler_manager.add_job(job_config)
        
        # Remove job
        removed = await scheduler_manager.remove_job("test_job")
        
        assert removed is True
        assert "test_job" not in scheduler_manager.job_configs
        assert scheduler_manager.scheduler.get_job("test_job") is None
        
        # Try to remove non-existent job
        removed_again = await scheduler_manager.remove_job("non_existent")
        assert removed_again is False
    
    @pytest.mark.asyncio
    async def test_pause_resume_job(self, scheduler_manager, sample_job_func):
        """Test pausing and resuming a job"""
        await scheduler_manager.initialize()
        await scheduler_manager.start()
        
        job_config = JobConfig(
            id="test_job",
            name="Test Job",
            func=sample_job_func,
            trigger_type="interval",
            trigger_config={"seconds": 10}
        )
        
        await scheduler_manager.add_job(job_config)
        
        # Pause job
        paused = await scheduler_manager.pause_job("test_job")
        assert paused is True
        
        job = scheduler_manager.scheduler.get_job("test_job")
        assert job.pending
        
        # Resume job
        resumed = await scheduler_manager.resume_job("test_job")
        assert resumed is True
        
        job = scheduler_manager.scheduler.get_job("test_job")
        assert not job.pending
    
    @pytest.mark.asyncio
    async def test_get_job_info(self, scheduler_manager, sample_job_func):
        """Test getting job information"""
        await scheduler_manager.initialize()
        await scheduler_manager.start()
        
        job_config = JobConfig(
            id="test_job",
            name="Test Job",
            func=sample_job_func,
            trigger_type="interval",
            trigger_config={"seconds": 10},
            description="Test job description"
        )
        
        await scheduler_manager.add_job(job_config)
        
        job_info = await scheduler_manager.get_job_info("test_job")
        
        assert job_info is not None
        assert job_info["id"] == "test_job"
        assert job_info["name"] == "Test Job"
        assert job_info["enabled"] is True
        assert job_info["config"]["description"] == "Test job description"
        
        # Test non-existent job
        non_existent = await scheduler_manager.get_job_info("non_existent")
        assert non_existent is None
    
    @pytest.mark.asyncio
    async def test_list_jobs(self, scheduler_manager, sample_job_func):
        """Test listing all jobs"""
        await scheduler_manager.initialize()
        await scheduler_manager.start()
        
        # Add multiple jobs
        jobs = [
            JobConfig(
                id="job_1",
                name="Job 1",
                func=sample_job_func,
                trigger_type="interval",
                trigger_config={"seconds": 10}
            ),
            JobConfig(
                id="job_2",
                name="Job 2",
                func=sample_job_func,
                trigger_type="interval",
                trigger_config={"seconds": 20}
            )
        ]
        
        for job in jobs:
            await scheduler_manager.add_job(job)
        
        jobs_list = await scheduler_manager.list_jobs()
        
        assert len(jobs_list) == 2
        job_ids = [job["id"] for job in jobs_list]
        assert "job_1" in job_ids
        assert "job_2" in job_ids
    
    @pytest.mark.asyncio
    async def test_get_health(self, scheduler_manager, sample_job_func):
        """Test scheduler health monitoring"""
        await scheduler_manager.initialize()
        await scheduler_manager.start()
        
        # Add a job
        job_config = JobConfig(
            id="test_job",
            name="Test Job",
            func=sample_job_func,
            trigger_type="interval",
            trigger_config={"seconds": 10}
        )
        await scheduler_manager.add_job(job_config)
        
        health = await scheduler_manager.get_health()
        
        assert health.status == SchedulerStatus.RUNNING
        assert health.total_jobs == 1
        assert health.active_jobs == 1
        assert health.paused_jobs == 0
        assert health.uptime is not None
        assert health.last_check is not None
    
    def test_create_trigger_cron(self, scheduler_manager):
        """Test creating cron trigger"""
        job_config = JobConfig(
            id="test_job",
            name="Test Job",
            func=lambda: None,
            trigger_type="cron",
            trigger_config={
                "minute": "0",
                "hour": "9",
                "day_of_week": "1-5"
            }
        )
        
        trigger = scheduler_manager._create_trigger(job_config)
        
        # Check that trigger has correct fields
        assert trigger.fields[0].name == "minute"
        assert trigger.fields[1].name == "hour"
        assert trigger.fields[5].name == "day_of_week"
    
    def test_create_trigger_interval(self, scheduler_manager):
        """Test creating interval trigger"""
        job_config = JobConfig(
            id="test_job",
            name="Test Job",
            func=lambda: None,
            trigger_type="interval",
            trigger_config={
                "seconds": 30,
                "minutes": 5,
                "hours": 1
            }
        )
        
        trigger = scheduler_manager._create_trigger(job_config)
        
        assert trigger.interval.total_seconds() == 3630  # 1*3600 + 5*60 + 30
    
    def test_create_trigger_unsupported(self, scheduler_manager):
        """Test creating unsupported trigger type"""
        job_config = JobConfig(
            id="test_job",
            name="Test Job",
            func=lambda: None,
            trigger_type="unsupported",
            trigger_config={}
        )
        
        with pytest.raises(ValueError, match="Unsupported trigger type"):
            scheduler_manager._create_trigger(job_config)
    
    def test_job_callbacks(self, scheduler_manager):
        """Test job event callbacks"""
        callback_called = False
        callback_result = None
        
        def test_callback(execution_result):
            nonlocal callback_called, callback_result
            callback_called = True
            callback_result = execution_result
        
        scheduler_manager.add_callback('job_completed', test_callback)
        
        # Simulate job execution
        start_time = datetime.now()
        execution_result = JobExecutionResult(
            job_id="test_job",
            status=JobStatus.COMPLETED,
            start_time=start_time,
            result={"success": True}
        )
        
        scheduler_manager._trigger_callbacks('job_completed', execution_result)
        
        assert callback_called
        assert callback_result == execution_result
        
        # Remove callback
        scheduler_manager.remove_callback('job_completed', test_callback)
        callback_called = False
        
        scheduler_manager._trigger_callbacks('job_completed', execution_result)
        assert not callback_called
    
    def test_cleanup_executions_history(self, scheduler_manager):
        """Test cleanup of execution history"""
        # Add many executions
        for i in range(1500):  # More than max_execution_history
            execution = JobExecutionResult(
                job_id=f"job_{i}",
                status=JobStatus.COMPLETED,
                start_time=datetime.now()
            )
            scheduler_manager.job_executions.append(execution)
        
        scheduler_manager._cleanup_executions_history()
        
        # Should be limited to max_execution_history
        assert len(scheduler_manager.job_executions) <= scheduler_manager.max_execution_history
    
    @pytest.mark.asyncio
    async def test_scheduler_without_initialization(self, scheduler_manager, sample_job_func):
        """Test operations without scheduler initialization"""
        job_config = JobConfig(
            id="test_job",
            name="Test Job",
            func=sample_job_func,
            trigger_type="interval",
            trigger_config={"seconds": 10}
        )
        
        # Should work - initialize() is called automatically
        job_id = await scheduler_manager.add_job(job_config)
        assert job_id == "test_job"


class TestGlobalSchedulerManager:
    """Test global scheduler manager functions"""
    
    @pytest.mark.asyncio
    async def test_get_scheduler_manager(self):
        """Test global scheduler manager getter"""
        from src.core.scheduler_manager import get_scheduler_manager, _scheduler_manager
        
        # Clear global instance
        _scheduler_manager = None
        
        manager1 = await get_scheduler_manager()
        manager2 = await get_scheduler_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, SchedulerManager)
    
    def test_get_scheduler(self):
        """Test getting underlying APScheduler instance"""
        from src.core.scheduler_manager import get_scheduler, _scheduler_manager
        
        # Clear global instance
        _scheduler_manager = None
        
        # Should return None when not initialized
        scheduler = get_scheduler()
        assert scheduler is None


class TestSchedulerManagerErrorHandling:
    """Test scheduler manager error handling"""
    
    @pytest.mark.asyncio
    async def test_job_error_listener(self, scheduler_manager):
        """Test job error event listener"""
        # Mock event
        mock_event = Mock()
        mock_event.job_id = "test_job"
        mock_event.scheduled_run_time = datetime.now()
        mock_event.exception = Exception("Test error")
        mock_event.traceback = "Test traceback"
        
        # Call error listener
        scheduler_manager._job_error_listener(mock_event)
        
        # Check that error was recorded
        assert len(scheduler_manager.job_executions) == 1
        execution = scheduler_manager.job_executions[0]
        assert execution.job_id == "test_job"
        assert execution.status == JobStatus.ERROR
        assert execution.error == "Test error"
        assert execution.traceback == "Test traceback"
        
        # Check health error count
        assert scheduler_manager.health.errors_count == 1
    
    @pytest.mark.asyncio
    async def test_job_missed_listener(self, scheduler_manager):
        """Test job missed event listener"""
        # Mock event
        mock_event = Mock()
        mock_event.job_id = "test_job"
        mock_event.scheduled_run_time = datetime.now()
        
        # Call missed listener
        scheduler_manager._job_missed_listener(mock_event)
        
        # Check that missed execution was recorded
        assert len(scheduler_manager.job_executions) == 1
        execution = scheduler_manager.job_executions[0]
        assert execution.job_id == "test_job"
        assert execution.status == JobStatus.MISSED
    
    @pytest.mark.asyncio
    async def test_job_executed_listener(self, scheduler_manager):
        """Test job executed event listener"""
        # Mock event
        mock_event = Mock()
        mock_event.job_id = "test_job"
        mock_event.scheduled_run_time = datetime.now()
        mock_event.retval = {"result": "success"}
        
        # Call executed listener
        scheduler_manager._job_executed_listener(mock_event)
        
        # Check that execution was recorded
        assert len(scheduler_manager.job_executions) == 1
        execution = scheduler_manager.job_executions[0]
        assert execution.job_id == "test_job"
        assert execution.status == JobStatus.COMPLETED
        assert execution.result == {"result": "success"}
    
    @pytest.mark.asyncio
    async def test_callback_error_handling(self, scheduler_manager):
        """Test error handling in callbacks"""
        def failing_callback(execution_result):
            raise Exception("Callback error")
        
        scheduler_manager.add_callback('job_completed', failing_callback)
        
        # Mock execution result
        execution_result = JobExecutionResult(
            job_id="test_job",
            status=JobStatus.COMPLETED,
            start_time=datetime.now()
        )
        
        # Should not raise exception
        scheduler_manager._trigger_callbacks('job_completed', execution_result)


class TestSchedulerManagerIntegration:
    """Integration tests for scheduler manager"""
    
    @pytest.mark.asyncio
    async def test_job_execution_flow(self, scheduler_manager):
        """Test complete job execution flow"""
        execution_results = []
        
        async def test_job():
            execution_results.append("executed")
            return {"status": "success"}
        
        # Set up callback
        def callback(execution_result):
            execution_results.append(execution_result.status.value)
        
        scheduler_manager.add_callback('job_completed', callback)
        
        # Initialize and start scheduler
        await scheduler_manager.initialize()
        await scheduler_manager.start()
        
        # Add job with short interval
        job_config = JobConfig(
            id="integration_test",
            name="Integration Test Job",
            func=test_job,
            trigger_type="interval",
            trigger_config={"seconds": 1}
        )
        
        await scheduler_manager.add_job(job_config)
        
        # Wait for job execution
        await asyncio.sleep(2)
        
        # Check that job was executed
        assert "executed" in execution_results
        assert "completed" in execution_results
    
    @pytest.mark.asyncio
    async def test_scheduler_performance(self, scheduler_manager):
        """Test scheduler performance with multiple jobs"""
        execution_count = 0
        
        async def performance_job():
            nonlocal execution_count
            execution_count += 1
        
        await scheduler_manager.initialize()
        await scheduler_manager.start()
        
        # Add multiple jobs
        for i in range(5):
            job_config = JobConfig(
                id=f"perf_job_{i}",
                name=f"Performance Job {i}",
                func=performance_job,
                trigger_type="interval",
                trigger_config={"seconds": 1}
            )
            await scheduler_manager.add_job(job_config)
        
        # Run for 3 seconds
        await asyncio.sleep(3)
        
        # Should have executed multiple times
        assert execution_count >= 5  # At least some executions
        
        await scheduler_manager.stop()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
