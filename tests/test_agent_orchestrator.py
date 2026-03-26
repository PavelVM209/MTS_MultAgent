"""
Tests for Agent Orchestrator

Comprehensive testing of agent coordination, workflow execution,
data sharing, and error handling capabilities.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.agent_orchestrator import (
    AgentOrchestrator,
    WorkflowStatus,
    AgentExecutionResult,
    WorkflowResult
)
from src.core.base_agent import AgentResult


@pytest.fixture
def mock_jira_agent():
    """Create mock JIRA analyzer agent."""
    agent = AsyncMock()
    agent.execute.return_value = AgentResult(
        success=True,
        message="JIRA analysis completed",
        data={
            'projects': [{'key': 'PROJ', 'name': 'Test Project'}],
            'employees': [{'name': 'John Doe', 'role': 'Developer'}],
            'analysis_summary': {'total_tasks': 10, 'completed': 5}
        },
        metadata={'execution_time': 1.5}
    )
    return agent


@pytest.fixture
def mock_meeting_agent():
    """Create mock meeting analyzer agent."""
    agent = AsyncMock()
    agent.execute.return_value = AgentResult(
        success=True,
        message="Meeting analysis completed",
        data={
            'meeting_info': {'title': 'Test Meeting', 'attendees': 5},
            'action_items': [{'description': 'Test action', 'responsible': 'John'}],
            'decisions': ['Decision 1', 'Decision 2']
        },
        metadata={'execution_time': 2.0}
    )
    return agent


@pytest.fixture
def mock_failing_agent():
    """Create mock failing agent."""
    agent = AsyncMock()
    agent.execute.return_value = AgentResult(
        success=False,
        message="Agent execution failed",
        data={},
        error="Simulated failure"
    )
    return agent


@pytest.fixture
def orchestrator():
    """Create agent orchestrator for testing."""
    with patch('src.core.agent_orchestrator.LLMClient'), \
         patch('src.core.agent_orchestrator.JSONMemoryStore'), \
         patch('src.core.agent_orchestrator.QualityMetrics'), \
         patch('src.core.agent_orchestrator.get_config', return_value={}):
        
        orchestrator = AgentOrchestrator()
        orchestrator.agent_timeout = 30  # Shorter timeout for tests
        return orchestrator


class TestAgentOrchestrator:
    """Test cases for AgentOrchestrator."""
    
    def test_register_agent(self, orchestrator, mock_jira_agent):
        """Test agent registration."""
        orchestrator.register_agent("test_agent", mock_jira_agent, priority=5)
        
        assert "test_agent" in orchestrator.agents
        assert orchestrator.agents["test_agent"]["agent"] == mock_jira_agent
        assert orchestrator.agents["test_agent"]["priority"] == 5
        assert orchestrator.agents["test_agent"]["success_count"] == 0
        assert orchestrator.agents["test_agent"]["failure_count"] == 0
    
    @pytest.mark.asyncio
    async def test_execute_workflow_sequential(
        self, orchestrator, mock_jira_agent, mock_meeting_agent
    ):
        """Test sequential workflow execution."""
        # Register agents
        orchestrator.register_agent("jira_analyzer", mock_jira_agent, priority=2)
        orchestrator.register_agent("meeting_analyzer", mock_meeting_agent, priority=1)
        
        # Prepare workflow configuration
        workflow_config = {
            'agents': ['meeting_analyzer', 'jira_analyzer'],
            'execution_constraints': {'sequenced': True, 'fail_fast': False}
        }
        
        # Prepare data sources
        data_sources = {
            'jira_analyzer': {'test_jira_data': 'data'},
            'meeting_analyzer': {'test_meeting_data': 'data'}
        }
        
        # Execute workflow
        result = await orchestrator.execute_workflow(workflow_config, data_sources)
        
        # Verify results
        assert result.status == WorkflowStatus.COMPLETED
        assert len(result.agent_results) == 2
        assert result.total_execution_time > 0
        
        # Check agent execution order (meeting_analyzer should run first due to higher priority)
        assert result.metadata['execution_order'] == ['jira_analyzer', 'meeting_analyzer']
        
        # Verify all agents succeeded
        for agent_result in result.agent_results:
            assert agent_result.success is True
            assert agent_result.quality_score > 0
    
    @pytest.mark.asyncio
    async def test_execute_workflow_parallel(
        self, orchestrator, mock_jira_agent, mock_meeting_agent
    ):
        """Test parallel workflow execution."""
        # Register agents
        orchestrator.register_agent("jira_analyzer", mock_jira_agent, priority=1)
        orchestrator.register_agent("meeting_analyzer", mock_meeting_agent, priority=1)
        
        # Prepare workflow configuration
        workflow_config = {
            'agents': ['jira_analyzer', 'meeting_analyzer'],
            'execution_constraints': {'sequenced': False}
        }
        
        # Prepare data sources
        data_sources = {
            'jira_analyzer': {'test_jira_data': 'data'},
            'meeting_analyzer': {'test_meeting_data': 'data'}
        }
        
        # Execute parallel workflow
        result = await orchestrator.execute_parallel_workflow(workflow_config, data_sources)
        
        # Verify results
        assert result.status == WorkflowStatus.COMPLETED
        assert len(result.agent_results) == 2
        assert result.metadata['parallel_groups'] == 1
        
        # Check data sharing
        assert 'shared_data' in result.aggregated_data
        assert result.aggregated_data['summary']['successful_agents'] == 2
    
    @pytest.mark.asyncio
    async def test_execute_workflow_with_fail_fast(
        self, orchestrator, mock_jira_agent, mock_failing_agent
    ):
        """Test workflow execution with fail_fast enabled."""
        # Register agents
        orchestrator.register_agent("failing_agent", mock_failing_agent, priority=2)
        orchestrator.register_agent("jira_analyzer", mock_jira_agent, priority=1)
        
        # Prepare workflow configuration with fail_fast
        workflow_config = {
            'agents': ['failing_agent', 'jira_analyzer'],
            'execution_constraints': {'sequenced': True, 'fail_fast': True}
        }
        
        # Prepare data sources
        data_sources = {
            'failing_agent': {'test_data': 'data'},
            'jira_analyzer': {'test_data': 'data'}
        }
        
        # Execute workflow
        result = await orchestrator.execute_workflow(workflow_config, data_sources)
        
        # Verify workflow stopped after first failure
        assert result.status == WorkflowStatus.FAILED
        
        # Only failing agent should have executed (due to fail_fast)
        assert len(result.agent_results) == 1
        assert result.agent_results[0].agent_name == "failing_agent"
        assert result.agent_results[0].success is False
    
    @pytest.mark.asyncio
    async def test_execute_workflow_partial_success(
        self, orchestrator, mock_jira_agent, mock_failing_agent
    ):
        """Test workflow execution with partial success."""
        # Register agents
        orchestrator.register_agent("failing_agent", mock_failing_agent, priority=2)
        orchestrator.register_agent("jira_analyzer", mock_jira_agent, priority=1)
        
        # Prepare workflow configuration without fail_fast
        workflow_config = {
            'agents': ['failing_agent', 'jira_analyzer'],
            'execution_constraints': {'sequenced': True, 'fail_fast': False}
        }
        
        # Prepare data sources
        data_sources = {
            'failing_agent': {'test_data': 'data'},
            'jira_analyzer': {'test_data': 'data'}
        }
        
        # Execute workflow
        result = await orchestrator.execute_workflow(workflow_config, data_sources)
        
        # Verify partial success
        assert result.status == WorkflowStatus.PARTIAL
        assert len(result.agent_results) == 2
        
        # Check summary
        summary = result.aggregated_data['summary']
        assert summary['successful_agents'] == 1
        assert summary['failed_agents'] == 1
    
    @pytest.mark.asyncio
    async def test_agent_timeout(self, orchestrator):
        """Test agent timeout handling."""
        # Create slow agent
        slow_agent = AsyncMock()
        slow_agent.execute.side_effect = asyncio.sleep(60)  # Very slow
        
        # Register agent
        orchestrator.register_agent("slow_agent", slow_agent)
        orchestrator.agent_timeout = 1  # 1 second timeout
        
        # Prepare workflow configuration
        workflow_config = {
            'agents': ['slow_agent'],
            'execution_constraints': {'sequenced': True}
        }
        
        # Prepare data sources
        data_sources = {'slow_agent': {'test_data': 'data'}}
        
        # Execute workflow
        result = await orchestrator.execute_workflow(workflow_config, data_sources)
        
        # Verify timeout handling
        assert result.status == WorkflowStatus.FAILED
        assert len(result.agent_results) == 1
        assert result.agent_results[0].success is False
        assert "timeout" in result.agent_results[0].error_message.lower()
    
    @pytest.mark.asyncio
    async def test_data_sharing_between_agents(
        self, orchestrator, mock_jira_agent, mock_meeting_agent
    ):
        """Test data sharing between agents."""
        # Register agents
        orchestrator.register_agent("jira_analyzer", mock_jira_agent)
        orchestrator.register_agent("meeting_analyzer", mock_meeting_agent)
        
        # Enable data sharing
        orchestrator.enable_data_sharing = True
        
        # Prepare workflow configuration
        workflow_config = {
            'agents': ['jira_analyzer', 'meeting_analyzer'],
            'data_sharing': True
        }
        
        # Prepare data sources
        data_sources = {
            'jira_analyzer': {'test_jira_data': 'data'},
            'meeting_analyzer': {'test_meeting_data': 'data'}
        }
        
        # Execute workflow
        result = await orchestrator.execute_workflow(workflow_config, data_sources)
        
        # Verify data sharing
        shared_data = result.aggregated_data['shared_data']
        
        # Check that agent data is shared
        assert 'jira_analyzer_data' in shared_data
        assert 'meeting_analyzer_data' in shared_data
        assert 'jira_analyzer_timestamp' in shared_data
        assert 'meeting_analyzer_timestamp' in shared_data
        
        # Check common entities extraction
        correlations = result.aggregated_data.get('correlations', {})
        if 'common_entities' in correlations:
            entities = correlations['common_entities']
            # Should extract common projects and employees
            assert 'projects' in entities or 'employees' in entities
    
    @pytest.mark.asyncio
    async def test_cross_agent_correlation(
        self, orchestrator, mock_jira_agent, mock_meeting_agent
    ):
        """Test cross-agent data correlation."""
        # Modify mock data to have common entities
        mock_jira_agent.execute.return_value.data.update({
            'projects': [{'key': 'PROJ', 'name': 'Test Project'}],
            'employees': [{'name': 'John Doe', 'role': 'Developer'}]
        })
        
        mock_meeting_agent.execute.return_value.data.update({
            'participants': [{'name': 'John Doe', 'role': 'Team Lead'}],
            'project_context': {'key': 'PROJ', 'name': 'Test Project'}
        })
        
        # Register agents
        orchestrator.register_agent("jira_analyzer", mock_jira_agent)
        orchestrator.register_agent("meeting_analyzer", mock_meeting_agent)
        
        # Execute workflow
        workflow_config = {
            'agents': ['jira_analyzer', 'meeting_analyzer'],
            'execution_constraints': {'sequenced': True}
        }
        
        data_sources = {
            'jira_analyzer': {'test_data': 'data'},
            'meeting_analyzer': {'test_data': 'data'}
        }
        
        result = await orchestrator.execute_workflow(workflow_config, data_sources)
        
        # Verify correlations
        correlations = result.aggregated_data.get('correlations')
        assert correlations is not None
        
        # Check common entities
        common_entities = correlations.get('common_entities', {})
        assert 'projects' in common_entities
        assert 'employees' in common_entities
        
        # Check quality analysis
        quality_analysis = correlations.get('quality_analysis', {})
        assert 'average_quality' in quality_analysis
        assert 'highest_quality_agent' in quality_analysis
        assert 'lowest_quality_agent' in quality_analysis
    
    @pytest.mark.asyncio
    async def test_agent_statistics_tracking(
        self, orchestrator, mock_jira_agent, mock_meeting_agent
    ):
        """Test agent statistics tracking."""
        # Register agents
        orchestrator.register_agent("jira_analyzer", mock_jira_agent)
        orchestrator.register_agent("meeting_analyzer", mock_meeting_agent)
        
        # Execute multiple workflows
        workflow_config = {
            'agents': ['jira_analyzer', 'meeting_analyzer'],
            'execution_constraints': {'sequenced': True}
        }
        
        data_sources = {
            'jira_analyzer': {'test_data': 'data'},
            'meeting_analyzer': {'test_data': 'data'}
        }
        
        # Execute workflow multiple times
        for i in range(3):
            await orchestrator.execute_workflow(workflow_config, data_sources)
        
        # Check statistics
        stats = await orchestrator.get_agent_statistics()
        
        assert "jira_analyzer" in stats
        assert "meeting_analyzer" in stats
        
        for agent_name, agent_stats in stats.items():
            assert agent_stats['total_executions'] == 3
            assert agent_stats['success_count'] == 3
            assert agent_stats['failure_count'] == 0
            assert agent_stats['success_rate'] == 1.0
            assert agent_stats['last_execution'] is not None
    
    @pytest.mark.asyncio
    async def test_workflow_history(self, orchestrator, mock_jira_agent):
        """Test workflow execution history."""
        # Register agent
        orchestrator.register_agent("jira_analyzer", mock_jira_agent)
        
        # Execute multiple workflows
        workflow_config = {
            'agents': ['jira_analyzer'],
            'execution_constraints': {'sequenced': True}
        }
        
        data_sources = {'jira_analyzer': {'test_data': 'data'}}
        
        # Execute workflows
        for i in range(3):
            await orchestrator.execute_workflow(workflow_config, data_sources)
        
        # Get history
        history = await orchestrator.get_workflow_history(limit=5)
        
        assert len(history) == 3
        
        for workflow in history:
            assert 'workflow_id' in workflow
            assert 'status' in workflow
            assert 'start_time' in workflow
            assert 'total_execution_time' in workflow
    
    @pytest.mark.asyncio
    async def test_health_status(self, orchestrator, mock_jira_agent):
        """Test health status monitoring."""
        # Register agent
        orchestrator.register_agent("jira_analyzer", mock_jira_agent)
        
        # Mock health check
        mock_jira_agent.get_health_status = AsyncMock(return_value={
            'status': 'healthy',
            'last_check': datetime.now().isoformat()
        })
        
        # Get health status
        health = await orchestrator.get_health_status()
        
        assert 'orchestrator_status' in health
        assert 'llm_client' in health
        assert 'memory_store' in health
        assert 'agent_health' in health
        assert 'total_agents' in health
        assert 'last_check' in health
        
        assert health['total_agents'] == 1
        assert health['agent_health'] == '1/1'
    
    def test_determine_execution_order(self, orchestrator):
        """Test execution order determination."""
        # Register agents with different priorities
        orchestrator.register_agent("low_priority", None, priority=1)
        orchestrator.register_agent("high_priority", None, priority=5)
        orchestrator.register_agent("medium_priority", None, priority=3)
        
        # Test order determination
        workflow_config = {'agents': ['low_priority', 'high_priority', 'medium_priority']}
        order = orchestrator._determine_execution_order(workflow_config)
        
        # Should be sorted by priority (descending)
        expected_order = ['high_priority', 'medium_priority', 'low_priority']
        assert order == expected_order
    
    def test_determine_parallel_groups(self, orchestrator):
        """Test parallel group determination."""
        # Set small parallel limit for testing
        orchestrator.max_parallel_agents = 2
        
        # Test group determination
        workflow_config = {'agents': ['agent1', 'agent2', 'agent3', 'agent4', 'agent5']}
        groups = orchestrator._determine_parallel_groups(workflow_config)
        
        # Should create groups based on max_parallel_agents
        assert len(groups) == 3  # 5 agents / 2 per group = 3 groups
        assert len(groups[0]) == 2  # First group has 2 agents
        assert len(groups[1]) == 2  # Second group has 2 agents
        assert len(groups[2]) == 1  # Third group has 1 agent
    
    def test_extract_shared_data(self, orchestrator):
        """Test shared data extraction."""
        # Create mock agent result
        mock_agent_result = AgentExecutionResult(
            agent_name="test_agent",
            execution_time=1.0,
            success=True,
            result=AgentResult(
                success=True,
                message="Success",
                data={
                    'projects': [{'key': 'PROJ', 'name': 'Test'}],
                    'employees': [{'name': 'John', 'role': 'Developer'}],
                    'action_items': [{'description': 'Test action'}],
                    'participants': [{'name': 'John'}]
                }
            ),
            quality_score=0.8
        )
        
        # Extract shared data
        shared_data = orchestrator._extract_shared_data(mock_agent_result)
        
        # Verify shared data
        assert 'projects' in shared_data
        assert 'employees' in shared_data
        assert 'action_items' in shared_data
        assert 'participants' in shared_data
        assert 'test_agent_data' in shared_data
        assert 'test_agent_timestamp' in shared_data
    
    def test_determine_workflow_status(self, orchestrator):
        """Test workflow status determination."""
        # Test all successful
        successful_results = [
            AgentExecutionResult("agent1", 1.0, True, None, 0.8),
            AgentExecutionResult("agent2", 1.0, True, None, 0.9)
        ]
        status = orchestrator._determine_workflow_status(successful_results)
        assert status == WorkflowStatus.COMPLETED
        
        # Test all failed
        failed_results = [
            AgentExecutionResult("agent1", 1.0, False, None, 0.0),
            AgentExecutionResult("agent2", 1.0, False, None, 0.0)
        ]
        status = orchestrator._determine_workflow_status(failed_results)
        assert status == WorkflowStatus.FAILED
        
        # Test mixed success
        mixed_results = [
            AgentExecutionResult("agent1", 1.0, True, None, 0.8),
            AgentExecutionResult("agent2", 1.0, False, None, 0.0)
        ]
        status = orchestrator._determine_workflow_status(mixed_results)
        assert status == WorkflowStatus.PARTIAL
        
        # Test empty results
        status = orchestrator._determine_workflow_status([])
        assert status == WorkflowStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_calculate_agent_quality(self, orchestrator):
        """Test agent quality calculation."""
        # Test successful agent with good data
        good_result = AgentResult(
            success=True,
            message="Success",
            data={'field1': 'value1', 'field2': 'value2', 'field3': 'value3'},
            metadata={'execution_time': 5.0}
        )
        
        quality = await orchestrator._calculate_agent_quality("test_agent", good_result)
        assert quality > 0.5  # Should be good quality
        
        # Test failed agent
        bad_result = AgentResult(
            success=False,
            message="Failed",
            data={},
            metadata={}
        )
        
        quality = await orchestrator._calculate_agent_quality("test_agent", bad_result)
        assert quality == 0.0  # Should be zero quality for failed agents
    
    @pytest.mark.asyncio
    async def test_reset_agent_statistics(self, orchestrator, mock_jira_agent):
        """Test agent statistics reset."""
        # Register agent
        orchestrator.register_agent("jira_analyzer", mock_jira_agent)
        
        # Execute some workflows to generate statistics
        workflow_config = {
            'agents': ['jira_analyzer'],
            'execution_constraints': {'sequenced': True}
        }
        data_sources = {'jira_analyzer': {'test_data': 'data'}}
        
        await orchestrator.execute_workflow(workflow_config, data_sources)
        
        # Verify statistics exist
        stats = await orchestrator.get_agent_statistics()
        assert stats["jira_analyzer"]["total_executions"] > 0
        
        # Reset statistics for specific agent
        orchestrator.reset_agent_statistics("jira_analyzer")
        
        # Verify statistics are reset
        stats = await orchestrator.get_agent_statistics()
        assert stats["jira_analyzer"]["total_executions"] == 0
        assert stats["jira_analyzer"]["success_count"] == 0
        assert stats["jira_analyzer"]["failure_count"] == 0
        assert stats["jira_analyzer"]["last_execution"] is None
        
        # Execute another workflow
        await orchestrator.execute_workflow(workflow_config, data_sources)
        
        # Reset all statistics
        orchestrator.reset_agent_statistics()
        
        # Verify all statistics are reset
        stats = await orchestrator.get_agent_statistics()
        for agent_stats in stats.values():
            assert agent_stats["total_executions"] == 0
            assert agent_stats["success_count"] == 0
            assert agent_stats["failure_count"] == 0
            assert agent_stats["last_execution"] is None


if __name__ == "__main__":
    pytest.main([__file__])
