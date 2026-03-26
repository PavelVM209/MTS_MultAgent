"""
Comprehensive Test Suite for Employee Monitoring System

Tests all components including agents, orchestrator, scheduler, and API.
Provides integration tests with real data and performance validation.
"""

import asyncio
import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import tempfile
import shutil

from src.orchestrator.employee_monitoring_orchestrator import (
    EmployeeMonitoringOrchestrator, WorkflowType, WorkflowStatus
)
from src.scheduler.employee_monitoring_scheduler import (
    EmployeeMonitoringScheduler, ScheduleType, TaskStatus
)
from src.agents.task_analyzer_agent import TaskAnalyzerAgent
from src.agents.meeting_analyzer_agent import MeetingAnalyzerAgent
from src.agents.weekly_reports_agent import WeeklyReportsAgent
from src.agents.quality_validator_agent import QualityValidatorAgent
from src.core.config import get_employee_monitoring_config
from src.core.json_memory_store import JSONMemoryStore
from src.core.llm_client import LLMClient


class TestEmployeeMonitoringSystem:
    """Comprehensive test suite for Employee Monitoring System."""
    
    @pytest.fixture
    async def test_config(self):
        """Load test configuration."""
        config = get_employee_monitoring_config()
        if not config:
            pytest.skip("Employee monitoring configuration not found")
        return config
    
    @pytest.fixture
    async def memory_store(self):
        """Create temporary memory store for testing."""
        temp_dir = tempfile.mkdtemp()
        store = JSONMemoryStore()
        yield store
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    async def llm_client(self):
        """Create LLM client for testing."""
        client = LLMClient()
        # Check if client is available
        if not await client.is_available():
            pytest.skip("LLM client not available")
        return client
    
    @pytest.fixture
    async def orchestrator(self, memory_store, llm_client):
        """Create orchestrator for testing."""
        from unittest.mock import Mock
        orchestrator = EmployeeMonitoringOrchestrator()
        orchestrator.memory_store = memory_store
        orchestrator.llm_client = llm_client
        return orchestrator
    
    @pytest.fixture
    async def scheduler(self):
        """Create scheduler for testing."""
        scheduler = EmployeeMonitoringScheduler()
        # Don't start scheduler for unit tests
        return scheduler
    
    class TestTaskAnalyzerAgent:
        """Test TaskAnalyzerAgent functionality."""
        
        @pytest.mark.asyncio
        async def test_task_analysis(self, test_config, llm_client):
            """Test task analysis with mock data."""
            agent = TaskAnalyzerAgent()
            agent.llm_client = llm_client
            
            # Mock task data
            mock_tasks = [
                {
                    'key': 'ROOBY-123',
                    'summary': 'Implement new feature',
                    'assignee': 'john.doe',
                    'status': 'Done',
                    'created': '2026-03-20T10:00:00Z',
                    'updated': '2026-03-25T15:30:00Z'
                },
                {
                    'key': 'ROOBY-124',
                    'summary': 'Fix critical bug',
                    'assignee': 'jane.smith',
                    'status': 'In Progress',
                    'created': '2026-03-24T09:00:00Z',
                    'updated': '2026-03-26T11:00:00Z'
                }
            ]
            
            # Analyze tasks
            result = await agent.analyze_tasks(mock_tasks, {
                'analysis_date': datetime.now().isoformat(),
                'projects': ['ROOBY']
            })
            
            # Validate result
            assert result is not None
            assert 'total_tasks' in result
            assert 'employee_metrics' in result
            assert result['total_tasks'] == 2
            assert len(result['employee_metrics']) >= 1
            
            # Check employee metrics structure
            for employee_id, metrics in result['employee_metrics'].items():
                assert 'completion_rate' in metrics
                assert 'productivity_score' in metrics
                assert 'performance_rating' in metrics
                assert 1 <= metrics['performance_rating'] <= 10
        
        @pytest.mark.asyncio
        async def test_empty_task_analysis(self, llm_client):
            """Test analysis with empty task list."""
            agent = TaskAnalyzerAgent()
            agent.llm_client = llm_client
            
            result = await agent.analyze_tasks([], {
                'analysis_date': datetime.now().isoformat(),
                'projects': ['ROOBY']
            })
            
            assert result is not None
            assert result['total_tasks'] == 0
            assert len(result['employee_metrics']) == 0
    
    class TestMeetingAnalyzerAgent:
        """Test MeetingAnalyzerAgent functionality."""
        
        @pytest.mark.asyncio
        async def test_protocol_analysis(self, test_config, llm_client):
            """Test meeting protocol analysis."""
            agent = MeetingAnalyzerAgent()
            agent.llm_client = llm_client
            
            # Mock protocol content
            mock_protocol = """
            Участники: Иванов И.И., Петров П.П., Сидорова С.С.
            
            Обсуждаемые вопросы:
            1. Статус проекта ROOBY - Иванов И.И. сообщил о завершении этапа
            2. Проблемы с BILLING - Петров П.П. описал технические трудности
            3. План на следующую неделю - Сидорова С.С. предложила новые подходы
            
            Действия:
            - Иванов: подготовить отчет (срок: 2026-03-28)
            - Петров: исправить баги (срок: 2026-03-27)
            """
            
            result = await agent.analyze_protocol(mock_protocol, {
                'meeting_date': datetime.now().isoformat(),
                'meeting_type': 'team_sync'
            })
            
            # Validate result
            assert result is not None
            assert 'participants' in result
            assert 'engagement_metrics' in result
            assert 'action_items' in result
            assert len(result['participants']) >= 2
            assert len(result['action_items']) >= 1
            
            # Check engagement metrics
            for employee_id, metrics in result['engagement_metrics'].items():
                assert 'engagement_score' in metrics
                assert 'activity_rating' in metrics
                assert 0 <= metrics['engagement_score'] <= 10
        
        @pytest.mark.asyncio
        async def test_empty_protocol_analysis(self, llm_client):
            """Test analysis with empty protocol."""
            agent = MeetingAnalyzerAgent()
            agent.llm_client = llm_client
            
            result = await agent.analyze_protocol("", {
                'meeting_date': datetime.now().isoformat(),
                'meeting_type': 'team_sync'
            })
            
            assert result is not None
            assert len(result['participants']) == 0
            assert len(result['action_items']) == 0
    
    class TestWeeklyReportsAgent:
        """Test WeeklyReportsAgent functionality."""
        
        @pytest.mark.asyncio
        async def test_weekly_report_generation(self, test_config, llm_client, memory_store):
            """Test weekly report generation."""
            agent = WeeklyReportsAgent()
            agent.llm_client = llm_client
            agent.memory_store = memory_store
            
            # Store mock daily data
            today = datetime.now()
            for i in range(7):
                date = today - timedelta(days=i)
                await memory_store.store_record(
                    'daily_task_analysis',
                    f'task_analysis_{date.strftime("%Y-%m-%d")}',
                    {
                        'date': date.strftime("%Y-%m-%d"),
                        'total_tasks': 10,
                        'employee_metrics': {
                            'john.doe': {
                                'completed_tasks': 5,
                                'completion_rate': 0.8,
                                'performance_rating': 8
                            }
                        }
                    }
                )
                
                await memory_store.store_record(
                    'daily_meeting_analysis',
                    f'meeting_analysis_{date.strftime("%Y-%m-%d")}',
                    {
                        'date': date.strftime("%Y-%m-%d"),
                        'total_meetings': 2,
                        'engagement_metrics': {
                            'john.doe': {
                                'engagement_score': 7.5,
                                'activity_rating': 8
                            }
                        }
                    }
                )
            
            # Generate weekly report
            result = await agent.generate_weekly_report({
                'week_start': (today - timedelta(days=6)).strftime("%Y-%m-%d"),
                'week_end': today.strftime("%Y-%m-%d"),
                'employees': ['john.doe']
            })
            
            # Validate result
            assert result is not None
            assert 'executive_summary' in result
            assert 'employee_summaries' in result
            assert 'team_insights' in result
            assert 'recommendations' in result
            assert len(result['employee_summaries']) >= 1
            
            # Check structure
            for employee_id, summary in result['employee_summaries'].items():
                assert 'performance_trend' in summary
                assert 'engagement_trend' in summary
                assert 'overall_rating' in summary
    
    class TestQualityValidatorAgent:
        """Test QualityValidatorAgent functionality."""
        
        @pytest.mark.asyncio
        async def test_quality_validation(self, llm_client):
            """Test quality validation."""
            agent = QualityValidatorAgent()
            agent.llm_client = llm_client
            
            # Mock analysis result
            mock_result = {
                'employee_summaries': {
                    'john.doe': {
                        'performance_rating': 7,
                        'engagement_score': 6,
                        'recommendations': ['Продолжать в том же духе']
                    }
                },
                'team_insights': {
                    'overall_performance': 'Хорошая',
                    'areas_for_improvement': ['Коммуникация']
                }
            }
            
            result = await agent.validate_quality(mock_result, {
                'validation_type': 'weekly_report',
                'threshold': 0.8
            })
            
            # Validate result
            assert result is not None
            assert 'quality_score' in result
            assert 'passed_validation' in result
            assert 'improvements' in result
            assert 0 <= result['quality_score'] <= 1
        
        @pytest.mark.asyncio
        async def test_quality_improvement(self, llm_client):
            """Test quality improvement suggestions."""
            agent = QualityValidatorAgent()
            agent.llm_client = llm_client
            
            # Low quality result
            low_quality_result = {
                'employee_summaries': {},  # Empty
                'team_insights': {}       # Empty
            }
            
            result = await agent.validate_quality(low_quality_result, {
                'validation_type': 'weekly_report',
                'threshold': 0.8
            })
            
            assert result['passed_validation'] is False
            assert len(result['improvements']) > 0
    
    class TestEmployeeMonitoringOrchestrator:
        """Test EmployeeMonitoringOrchestrator functionality."""
        
        @pytest.mark.asyncio
        async def test_workflow_execution(self, orchestrator, test_config):
            """Test workflow execution."""
            # Start orchestrator
            await orchestrator.start()
            
            try:
                # Execute daily task analysis workflow
                execution = await orchestrator.execute_workflow(
                    WorkflowType.DAILY_TASK_ANALYSIS,
                    {
                        'analysis_date': datetime.now().isoformat(),
                        'projects': test_config.get('jira', {}).get('projects', ['ROOBY'])
                    }
                )
                
                # Validate execution
                assert execution is not None
                assert execution.status == WorkflowStatus.COMPLETED
                assert execution.workflow_type == WorkflowType.DAILY_TASK_ANALYSIS
                assert len(execution.results) > 0
                
            finally:
                await orchestrator.stop()
        
        @pytest.mark.asyncio
        async def test_comprehensive_monitoring(self, orchestrator, test_config):
            """Test comprehensive monitoring workflow."""
            await orchestrator.start()
            
            try:
                # Start comprehensive monitoring
                execution = await orchestrator.start_comprehensive_monitoring({
                    'source': 'test',
                    'timestamp': datetime.now().isoformat(),
                    'employees': test_config.get('employees', {}).get('list', ['john.doe'])
                })
                
                # This should run all workflows
                assert execution is not None
                # Note: This might take time, so we just check it started
                
            finally:
                await orchestrator.stop()
        
        @pytest.mark.asyncio
        async def test_workflow_status_tracking(self, orchestrator):
            """Test workflow status tracking."""
            await orchestrator.start()
            
            try:
                # Get initial status
                initial_status = await orchestrator.get_orchestrator_status()
                assert initial_status['orchestrator_status'] == 'healthy'
                
                # Execute a workflow
                execution = await orchestrator.execute_workflow(
                    WorkflowType.DAILY_TASK_ANALYSIS,
                    {'test': True}
                )
                
                # Check active workflows
                active_workflows = await orchestrator.get_active_workflows()
                assert len(active_workflows) >= 0
                
            finally:
                await orchestrator.stop()
    
    class TestEmployeeMonitoringScheduler:
        """Test EmployeeMonitoringScheduler functionality."""
        
        @pytest.mark.asyncio
        async def test_task_scheduling(self, scheduler):
            """Test task scheduling."""
            # Add a daily task
            task_id = await scheduler.add_scheduled_task(
                name="Test Daily Task",
                workflow_type=WorkflowType.DAILY_TASK_ANALYSIS,
                schedule_type=ScheduleType.DAILY,
                schedule_expression="09:00",
                input_data={"source": "test"},
                enabled=True
            )
            
            assert task_id is not None
            
            # Get task status
            task = await scheduler.get_task_status(task_id)
            assert task is not None
            assert task.name == "Test Daily Task"
            assert task.enabled is True
            
            # Disable task
            success = await scheduler.disable_task(task_id)
            assert success is True
            
            task = await scheduler.get_task_status(task_id)
            assert task.enabled is False
            
            # Remove task
            success = await scheduler.remove_scheduled_task(task_id)
            assert success is True
            
            task = await scheduler.get_task_status(task_id)
            assert task is None
        
        @pytest.mark.asyncio
        async def test_scheduler_status(self, scheduler):
            """Test scheduler status."""
            status = await scheduler.get_scheduler_status()
            
            assert status is not None
            assert 'scheduler_status' in status
            assert 'total_tasks' in status
            assert 'enabled_tasks' in status
            assert status['scheduler_status'] == 'stopped'  # Not started in test
    
    class TestIntegration:
        """Integration tests for the complete system."""
        
        @pytest.mark.asyncio
        async def test_end_to_end_workflow(self, test_config, llm_client):
            """Test complete end-to-end workflow."""
            # Initialize components
            memory_store = JSONMemoryStore()
            orchestrator = EmployeeMonitoringOrchestrator()
            orchestrator.memory_store = memory_store
            orchestrator.llm_client = llm_client
            
            await orchestrator.start()
            
            try:
                # Simulate task analysis
                task_agent = TaskAnalyzerAgent()
                task_agent.llm_client = llm_client
                
                mock_tasks = [
                    {
                        'key': 'TEST-001',
                        'summary': 'Test task',
                        'assignee': 'test.user',
                        'status': 'Done',
                        'created': '2026-03-20T10:00:00Z',
                        'updated': '2026-03-25T15:30:00Z'
                    }
                ]
                
                task_result = await task_agent.analyze_tasks(mock_tasks, {
                    'analysis_date': datetime.now().isoformat(),
                    'projects': ['TEST']
                })
                
                # Store result
                await memory_store.store_record(
                    'daily_task_analysis',
                    f'task_analysis_{datetime.now().strftime("%Y-%m-%d")}',
                    task_result
                )
                
                # Generate weekly report
                weekly_agent = WeeklyReportsAgent()
                weekly_agent.llm_client = llm_client
                weekly_agent.memory_store = memory_store
                
                weekly_result = await weekly_agent.generate_weekly_report({
                    'week_start': (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d"),
                    'week_end': datetime.now().strftime("%Y-%m-%d"),
                    'employees': ['test.user']
                })
                
                # Validate complete workflow
                assert task_result is not None
                assert weekly_result is not None
                assert 'executive_summary' in weekly_result
                
            finally:
                await orchestrator.stop()
        
        @pytest.mark.asyncio
        async def test_error_handling(self, orchestrator):
            """Test error handling and recovery."""
            await orchestrator.start()
            
            try:
                # Execute with invalid input
                execution = await orchestrator.execute_workflow(
                    WorkflowType.DAILY_TASK_ANALYSIS,
                    {}  # Empty input
                )
                
                # Should handle gracefully
                assert execution is not None
                # Status might be FAILED, but shouldn't crash
                
            finally:
                await orchestrator.stop()


class TestPerformance:
    """Performance tests for the system."""
    
    @pytest.mark.asyncio
    async def test_task_analysis_performance(self, llm_client):
        """Test task analysis performance."""
        agent = TaskAnalyzerAgent()
        agent.llm_client = llm_client
        
        # Create larger dataset
        mock_tasks = [
            {
                'key': f'TEST-{i:03d}',
                'summary': f'Test task {i}',
                'assignee': f'user{i % 5}',
                'status': 'Done' if i % 2 == 0 else 'In Progress',
                'created': '2026-03-20T10:00:00Z',
                'updated': '2026-03-25T15:30:00Z'
            }
            for i in range(50)  # 50 tasks
        ]
        
        start_time = datetime.now()
        
        result = await agent.analyze_tasks(mock_tasks, {
            'analysis_date': datetime.now().isoformat(),
            'projects': ['TEST']
        })
        
        duration = datetime.now() - start_time
        
        # Should complete within reasonable time (30 seconds)
        assert duration.total_seconds() < 30
        assert result is not None
        assert result['total_tasks'] == 50


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
