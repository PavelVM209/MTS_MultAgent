"""
Tests for Daily JIRA Analyzer Agent
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.daily_jira_analyzer import (
    DailyJiraAnalyzer, 
    JiraTask, 
    TaskStatus, 
    Priority,
    EmployeeWorkload,
    ProjectProgress,
    JiraAnalysisResult
)
from src.core.base_agent import AgentResult


@pytest.fixture
def sample_jira_tasks():
    """Sample JIRA tasks for testing."""
    return [
        {
            "id": "1",
            "key": "PROJ-101",
            "summary": "Implement user authentication",
            "status": "in_progress",
            "priority": "high",
            "assignee": "john.doe",
            "reporter": "jane.smith",
            "project": "PROJ",
            "created": "2024-03-20T10:00:00Z",
            "updated": "2024-03-25T15:30:00Z",
            "due_date": "2024-03-28T17:00:00Z",
            "story_points": "5",
            "labels": ["backend", "auth"],
            "components": ["authentication"],
            "description": "Implement OAuth2 authentication",
            "comments_count": 3
        },
        {
            "id": "2",
            "key": "PROJ-102",
            "summary": "Design database schema",
            "status": "done",
            "priority": "medium",
            "assignee": "jane.smith",
            "reporter": "john.doe",
            "project": "PROJ",
            "created": "2024-03-18T09:00:00Z",
            "updated": "2024-03-22T14:00:00Z",
            "due_date": "2024-03-20T17:00:00Z",
            "story_points": 3,
            "labels": ["database"],
            "components": ["backend"],
            "description": "Design user and authentication tables",
            "comments_count": 5
        },
        {
            "id": "3",
            "key": "PROJ-103",
            "summary": "Fix authentication bug",
            "status": "blocked",
            "priority": "highest",
            "assignee": "john.doe",
            "reporter": "manager",
            "project": "PROJ",
            "created": "2024-03-24T11:00:00Z",
            "updated": "2024-03-25T16:00:00Z",
            "due_date": "2024-03-25T17:00:00Z",
            "story_points": 2,
            "labels": ["bug", "auth"],
            "components": ["authentication"],
            "description": "Critical bug in login flow",
            "comments_count": 8
        }
    ]


@pytest.fixture
def mock_analyzer():
    """Create a mock DailyJiraAnalyzer for testing."""
    with patch('src.agents.daily_jira_analyzer.LLMClient'), \
         patch('src.agents.daily_jira_analyzer.JSONMemoryStore'), \
         patch('src.agents.daily_jira_analyzer.QualityMetrics'), \
         patch('src.agents.daily_jira_analyzer.get_config', return_value={}):
        
        analyzer = DailyJiraAnalyzer()
        return analyzer


class TestDailyJiraAnalyzer:
    """Test cases for DailyJiraAnalyzer."""
    
    @pytest.mark.asyncio
    async def test_execute_successful_analysis(self, mock_analyzer, sample_jira_tasks):
        """Test successful JIRA analysis execution."""
        # Mock LLM client
        mock_analyzer.llm_client.is_available = AsyncMock(return_value=True)
        
        # Mock memory store
        mock_analyzer.memory_store.save_record = AsyncMock()
        
        # Mock schema validation
        mock_schema = AsyncMock()
        mock_schema.validate = AsyncMock(return_value={"validated": True})
        
        with patch('src.agents.daily_jira_analyzer.JiraAnalysisSchema', return_value=mock_schema):
            # Execute analysis
            result = await mock_analyzer.execute({
                'jira_tasks': sample_jira_tasks,
                'include_llm_analysis': False  # Disable LLM for simpler test
            })
            
            # Verify results
            assert result.success is True
            assert 'Successfully analyzed' in result.message
            assert 'execution_time' in result.metadata
            assert 'tasks_analyzed' in result.metadata
            assert result.metadata['tasks_analyzed'] == 3
    
    @pytest.mark.asyncio
    async def test_execute_no_tasks(self, mock_analyzer):
        """Test execution with no tasks."""
        result = await mock_analyzer.execute({'jira_tasks': []})
        
        assert result.success is False
        assert 'No JIRA tasks found' in result.message
        assert result.data == {}
    
    @pytest.mark.asyncio
    async def test_parse_jira_tasks(self, mock_analyzer, sample_jira_tasks):
        """Test JIRA task parsing."""
        tasks = await mock_analyzer._parse_jira_tasks(sample_jira_tasks)
        
        assert len(tasks) == 3
        
        # Check first task
        task = tasks[0]
        assert task.key == "PROJ-101"
        assert task.summary == "Implement user authentication"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == Priority.HIGH
        assert task.assignee == "john.doe"
        assert task.project == "PROJ"
        assert task.story_points == 5.0
    
    def test_parse_status(self, mock_analyzer):
        """Test status parsing."""
        assert mock_analyzer._parse_status("In Progress") == TaskStatus.IN_PROGRESS
        assert mock_analyzer._parse_status("Done") == TaskStatus.DONE
        assert mock_analyzer._parse_status("Blocked Issue") == TaskStatus.BLOCKED
        assert mock_analyzer._parse_status("Unknown") == TaskStatus.TODO
    
    def test_parse_priority(self, mock_analyzer):
        """Test priority parsing."""
        assert mock_analyzer._parse_priority("Highest") == Priority.HIGHEST
        assert mock_analyzer._parse_priority("Medium") == Priority.MEDIUM
        assert mock_analyzer._parse_priority("Low") == Priority.LOW
        assert mock_analyzer._parse_priority("Unknown") == Priority.MEDIUM
    
    def test_parse_datetime(self, mock_analyzer):
        """Test datetime parsing."""
        # Test valid datetime
        dt = mock_analyzer._parse_datetime("2024-03-25T15:30:00Z")
        assert dt is not None
        assert dt.year == 2024
        assert dt.month == 3
        assert dt.day == 25
        
        # Test invalid datetime
        dt = mock_analyzer._parse_datetime("invalid")
        assert dt is None
        
        # Test empty string
        dt = mock_analyzer._parse_datetime("")
        assert dt is None
    
    def test_parse_story_points(self, mock_analyzer):
        """Test story points parsing."""
        # Test numeric
        assert mock_analyzer._parse_story_points(5) == 5.0
        assert mock_analyzer._parse_story_points(3.5) == 3.5
        
        # Test string with SP
        assert mock_analyzer._parse_story_points("5 SP") == 5.0
        assert mock_analyzer._parse_story_points("3 story points") == 3.0
        
        # Test direct string conversion
        assert mock_analyzer._parse_story_points("8") == 8.0
        
        # Test invalid
        assert mock_analyzer._parse_story_points("invalid") is None
        assert mock_analyzer._parse_story_points(None) is None
    
    @pytest.mark.asyncio
    async def test_analyze_employee_workload(self, mock_analyzer):
        """Test employee workload analysis."""
        # Create sample tasks
        tasks = [
            JiraTask(
                id="1", key="TASK-1", summary="Task 1", status=TaskStatus.DONE,
                priority=Priority.MEDIUM, assignee="john", project="PROJ",
                created=datetime.now() - timedelta(days=5),
                updated=datetime.now() - timedelta(days=3),
                story_points=5.0
            ),
            JiraTask(
                id="2", key="TASK-2", summary="Task 2", status=TaskStatus.IN_PROGRESS,
                priority=Priority.HIGH, assignee="john", project="PROJ",
                created=datetime.now() - timedelta(days=2),
                updated=datetime.now() - timedelta(days=1),
                due_date=datetime.now() + timedelta(days=2),
                story_points=3.0
            )
        ]
        
        workload = await mock_analyzer._analyze_employee_workload("john", tasks)
        
        assert workload.employee == "john"
        assert workload.total_tasks == 2
        assert workload.completed_tasks == 1
        assert workload.in_progress_tasks == 1
        assert workload.blocked_tasks == 0
        assert workload.total_story_points == 8.0
        assert workload.completed_story_points == 5.0
        assert workload.completion_rate == 0.5
    
    @pytest.mark.asyncio
    async def test_analyze_project_progress(self, mock_analyzer):
        """Test project progress analysis."""
        # Create sample tasks
        tasks = [
            JiraTask(
                id="1", key="TASK-1", summary="Task 1", status=TaskStatus.DONE,
                priority=Priority.MEDIUM, assignee="john", project="PROJ",
                created=datetime.now() - timedelta(days=5),
                updated=datetime.now() - timedelta(days=3),
                story_points=5.0
            ),
            JiraTask(
                id="2", key="TASK-2", summary="Task 2", status=TaskStatus.IN_PROGRESS,
                priority=Priority.HIGH, assignee="jane", project="PROJ",
                created=datetime.now() - timedelta(days=2),
                updated=datetime.now() - timedelta(days=1),
                story_points=3.0
            )
        ]
        
        progress = await mock_analyzer._analyze_project_progress("PROJ", tasks)
        
        assert progress.project == "PROJ"
        assert progress.total_tasks == 2
        assert progress.completed_tasks == 1
        assert progress.in_progress_tasks == 1
        assert progress.total_story_points == 8.0
        assert progress.completed_story_points == 5.0
        assert progress.completion_percentage == 62.5  # (5/8) * 100
        assert "john" in progress.active_employees
        assert "jane" in progress.active_employees
    
    @pytest.mark.asyncio
    async def test_generate_insights(self, mock_analyzer):
        """Test insights generation."""
        # Create sample workloads
        employees_workload = {
            "john": EmployeeWorkload(
                employee="john", total_tasks=10, completed_tasks=5,
                in_progress_tasks=6, blocked_tasks=1, overdue_tasks=2,
                total_story_points=20.0, completed_story_points=10.0,
                completion_rate=0.5
            ),
            "jane": EmployeeWorkload(
                employee="jane", total_tasks=5, completed_tasks=4,
                in_progress_tasks=1, blocked_tasks=0, overdue_tasks=0,
                total_story_points=10.0, completed_story_points=8.0,
                completion_rate=0.8
            )
        }
        
        # Create sample project progress
        projects_progress = {
            "PROJ": ProjectProgress(
                project="PROJ", total_tasks=15, completed_tasks=5,
                in_progress_tasks=5, total_story_points=30.0,
                completed_story_points=15.0, completion_percentage=50.0
            )
        }
        
        insights = await mock_analyzer._generate_insights(
            employees_workload, projects_progress, []
        )
        
        assert len(insights) > 0
        assert any("High workload" in insight for insight in insights)
        assert any("blocked" in insight.lower() for insight in insights)
        assert any("overdue" in insight.lower() for insight in insights)
    
    @pytest.mark.asyncio
    async def test_generate_recommendations(self, mock_analyzer):
        """Test recommendations generation."""
        # Create sample workloads with issues
        employees_workload = {
            "john": EmployeeWorkload(
                employee="john", total_tasks=10, completed_tasks=5,
                in_progress_tasks=6, blocked_tasks=1, overdue_tasks=2,
                total_story_points=20.0, completed_story_points=10.0,
                completion_rate=0.5
            )
        }
        
        # Create sample project progress
        projects_progress = {
            "PROJ": ProjectProgress(
                project="PROJ", total_tasks=15, completed_tasks=5,
                in_progress_tasks=5, total_story_points=30.0,
                completed_story_points=15.0, completion_percentage=30.0
            )
        }
        
        recommendations = await mock_analyzer._generate_recommendations(
            employees_workload, projects_progress, []
        )
        
        assert len(recommendations) > 0
        assert any("redistributing" in rec for rec in recommendations)
        assert any("blocked" in rec.lower() for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_calculate_analysis_quality(self, mock_analyzer):
        """Test analysis quality calculation."""
        # Create sample data
        employees_workload = {
            "john": EmployeeWorkload(
                employee="john", total_tasks=10, completed_tasks=5,
                in_progress_tasks=3, blocked_tasks=2, overdue_tasks=1,
                total_story_points=20.0, completed_story_points=10.0,
                completion_rate=0.5
            )
        }
        
        projects_progress = {
            "PROJ": ProjectProgress(
                project="PROJ", total_tasks=15, completed_tasks=5,
                in_progress_tasks=5, total_story_points=30.0,
                completed_story_points=15.0, completion_percentage=50.0
            )
        }
        
        quality_score = await mock_analyzer._calculate_analysis_quality(
            employees_workload, projects_progress
        )
        
        assert 0.0 <= quality_score <= 1.0
        assert quality_score > 0.0  # Should have some quality
    
    @pytest.mark.asyncio
    async def test_get_health_status(self, mock_analyzer):
        """Test health status check."""
        # Mock component availability
        mock_analyzer.llm_client.is_available = AsyncMock(return_value=True)
        mock_analyzer.memory_store.is_healthy = MagicMock(return_value=True)
        
        health = await mock_analyzer.get_health_status()
        
        assert health['agent_name'] == 'DailyJiraAnalyzer'
        assert health['status'] == 'healthy'
        assert health['llm_client'] == 'available'
        assert health['memory_store'] == 'healthy'
        assert 'last_check' in health
    
    @pytest.mark.asyncio
    async def test_get_health_status_degraded(self, mock_analyzer):
        """Test health status when components are unavailable."""
        # Mock component unavailability
        mock_analyzer.llm_client.is_available = AsyncMock(return_value=False)
        mock_analyzer.memory_store.is_healthy = MagicMock(return_value=False)
        
        health = await mock_analyzer.get_health_status()
        
        assert health['status'] == 'degraded'
        assert health['llm_client'] == 'unavailable'
        assert health['memory_store'] == 'unhealthy'
    
    @pytest.mark.asyncio
    async def test_add_llm_insights(self, mock_analyzer):
        """Test adding LLM insights."""
        # Create sample analysis result
        analysis_result = JiraAnalysisResult(
            analysis_date=datetime.now(),
            tasks_analyzed=3,
            employees_workload={},
            projects_progress={},
            insights=["Existing insight"],
            recommendations=["Existing recommendation"],
            quality_score=0.8
        )
        
        # Create sample tasks
        tasks = []
        
        # Mock LLM analysis
        mock_llm_analysis = {
            'insights': ['LLM insight 1', 'LLM insight 2'],
            'recommendations': ['LLM recommendation 1']
        }
        
        with patch('src.agents.daily_jira_analyzer.analyze_jira_analysis', 
                  return_value=mock_llm_analysis):
            await mock_analyzer._add_llm_insights(analysis_result, tasks)
        
        # Check that LLM insights were added
        assert len(analysis_result.insights) > 1
        assert len(analysis_result.recommendations) > 1
        assert 'LLM insight 1' in analysis_result.insights
        assert 'LLM recommendation 1' in analysis_result.recommendations
        assert 'llm_analysis' in analysis_result.metadata
    
    @pytest.mark.asyncio
    async def test_execute_with_llm_error(self, mock_analyzer, sample_jira_tasks):
        """Test execution when LLM analysis fails."""
        # Mock successful LLM availability but failed analysis
        mock_analyzer.llm_client.is_available = AsyncMock(return_value=True)
        mock_analyzer.memory_store.save_record = AsyncMock()
        
        # Mock schema validation
        mock_schema = AsyncMock()
        mock_schema.validate = AsyncMock(return_value={"validated": True})
        
        with patch('src.agents.daily_jira_analyzer.JiraAnalysisSchema', return_value=mock_schema), \
             patch('src.agents.daily_jira_analyzer.analyze_jira_analysis', 
                   side_effect=Exception("LLM Error")):
            
            # Execute with LLM enabled (should handle error gracefully)
            result = await mock_analyzer.execute({
                'jira_tasks': sample_jira_tasks,
                'include_llm_analysis': True
            })
            
            # Should still succeed even with LLM error
            assert result.success is True
            assert result.metadata['tasks_analyzed'] == 3
    
    @pytest.mark.asyncio
    async def test_validate_and_format_results(self, mock_analyzer):
        """Test result validation and formatting."""
        # Create sample analysis result
        analysis_result = JiraAnalysisResult(
            analysis_date=datetime.now(),
            tasks_analyzed=3,
            employees_workload={
                "john": EmployeeWorkload(
                    employee="john", total_tasks=10, completed_tasks=5,
                    in_progress_tasks=3, blocked_tasks=2, overdue_tasks=0,
                    total_story_points=20.0, completed_story_points=10.0,
                    completion_rate=0.5
                )
            },
            projects_progress={
                "PROJ": ProjectProgress(
                    project="PROJ", total_tasks=15, completed_tasks=5,
                    in_progress_tasks=5, total_story_points=30.0,
                    completed_story_points=15.0, completion_percentage=50.0
                )
            },
            insights=["Test insight"],
            recommendations=["Test recommendation"],
            quality_score=0.8
        )
        
        # Mock schema validation
        mock_schema = AsyncMock()
        mock_schema.validate = AsyncMock(return_value={"validated": True})
        
        # Test validation and formatting
        result = await mock_analyzer._validate_and_format_results(analysis_result, mock_schema)
        
        assert 'analysis_date' in result
        assert 'tasks_analyzed' in result
        assert result['tasks_analyzed'] == 3
        assert 'employees_workload' in result
        assert 'projects_progress' in result
        assert 'insights' in result
        assert 'recommendations' in result
        assert 'quality_score' in result


if __name__ == "__main__":
    pytest.main([__file__])
