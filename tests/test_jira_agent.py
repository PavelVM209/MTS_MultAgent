"""
Tests for JiraAgent

This module contains unit tests for the JiraAgent class,
including validation, execution, and error handling.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.agents.jira_agent import JiraAgent
from src.core.models import JiraTask, JiraResult, JiraIssue
from src.core.base_agent import AgentResult


@pytest.fixture
def mock_config():
    """Mock configuration for JiraAgent."""
    return {
        "jira": {
            "base_url": "https://test.atlassian.net",
            "access_token": "test_token",
            "username": "test@example.com",
            "timeout": 30
        },
        "debug": True,
        "test_mode": True
    }


@pytest.fixture
def jira_agent(mock_config):
    """Create JiraAgent instance with mock configuration."""
    return JiraAgent(mock_config)


@pytest.fixture
def sample_jira_task():
    """Sample JiraTask for testing."""
    return {
        "project_key": "TEST",
        "task_description": "Test task",
        "search_keywords": ["test", "bug"],
        "max_results": 10
    }


@pytest.fixture
def sample_jira_response():
    """Sample Jira API response."""
    return {
        "issues": [
            {
                "id": "10001",
                "key": "TEST-1",
                "fields": {
                    "summary": "Test bug report",
                    "description": "This is a test bug",
                    "status": {"name": "Open"},
                    "assignee": {"displayName": "John Doe"},
                    "reporter": {"displayName": "Jane Smith"},
                    "created": "2024-01-01T10:00:00.000Z",
                    "updated": "2024-01-02T10:00:00.000Z",
                    "issuetype": {"name": "Bug"},
                    "priority": {"name": "High"},
                    "labels": ["test", "urgent"],
                    "components": [{"name": "Backend"}]
                }
            }
        ]
    }


class TestJiraAgent:
    """Test class for JiraAgent functionality."""
    
    def test_initialization(self, mock_config):
        """Test JiraAgent initialization."""
        agent = JiraAgent(mock_config)
        
        assert agent.name == "JiraAgent"
        assert agent.base_url == "https://test.atlassian.net"
        assert agent.access_token == "test_token"
        assert agent.username == "test@example.com"
        assert agent.timeout == 30
        assert "Authorization" in agent.auth_headers
    
    def test_initialization_missing_config(self):
        """Test JiraAgent initialization with missing configuration."""
        with pytest.raises(ValueError, match="Missing required Jira configuration"):
            JiraAgent({"invalid": "config"})
    
    @pytest.mark.asyncio
    async def test_validate_valid_task(self, jira_agent, sample_jira_task):
        """Test task validation with valid data."""
        result = await jira_agent.validate(sample_jira_task)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_invalid_task(self, jira_agent):
        """Test task validation with invalid data."""
        # Missing project_key
        invalid_task = {
            "task_description": "Test task",
            "search_keywords": ["test"]
        }
        result = await jira_agent.validate(invalid_task)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_max_results_limit(self, jira_agent, sample_jira_task):
        """Test task validation with max_results above limit."""
        sample_jira_task["max_results"] = 150  # Above limit of 100
        
        result = await jira_agent.validate(sample_jira_task)
        assert result is True  # Should be True but with warning logged
    
    @pytest.mark.asyncio
    @patch('src.agents.jira_agent.aiohttp.ClientSession')
    async def test_execute_success(self, mock_session_class, jira_agent, sample_jira_task, sample_jira_response):
        """Test successful execution."""
        # Setup mock session
        mock_session = AsyncMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        # Setup mock response
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json = AsyncMock(return_value=sample_jira_response)
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        # Mock extract_comments to return empty list
        with patch.object(jira_agent, 'extract_comments', return_value=[]):
            result = await jira_agent.execute(sample_jira_task)
        
        assert isinstance(result, AgentResult)
        assert result.success is True
        assert "data" in result.dict()
        assert result.agent_name == "JiraAgent"
    
    @pytest.mark.asyncio
    @patch('src.agents.jira_agent.aiohttp.ClientSession')
    async def test_execute_api_error(self, mock_session_class, jira_agent, sample_jira_task):
        """Test execution with API error."""
        # Setup mock session that raises exception
        mock_session = AsyncMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        # Mock response that raises error
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock(side_effect=Exception("API Error"))
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        result = await jira_agent.execute(sample_jira_task)
        
        assert isinstance(result, AgentResult)
        assert result.success is False
        assert "Jira execution failed" in result.error
    
    @pytest.mark.asyncio
    @patch('src.agents.jira_agent.aiohttp.ClientSession')
    async def test_search_issues(self, mock_session_class, jira_agent, sample_jira_response):
        """Test search_issues method."""
        # Setup mock session
        mock_session = AsyncMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        # Setup mock response
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json = AsyncMock(return_value=sample_jira_response)
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        issues = await jira_agent.search_issues("TEST", ["test", "bug"])
        
        assert len(issues) == 1
        assert isinstance(issues[0], JiraIssue)
        assert issues[0].key == "TEST-1"
        assert issues[0].summary == "Test bug report"
        assert issues[0].status == "Open"
    
    def test_build_jql_query_basic(self, jira_agent):
        """Test JQL query building with basic parameters."""
        jql = jira_agent._build_jql_query("TEST", ["test", "bug"])
        
        assert 'project = "TEST"' in jql
        assert 'text ~ "test"' in jql
        assert 'text ~ "bug"' in jql
        assert 'ORDER BY created DESC' in jql
    
    def test_build_jql_query_with_date_range(self, jira_agent):
        """Test JQL query building with date range."""
        date_range = {"from": "2024-01-01", "to": "2024-01-31"}
        jql = jira_agent._build_jql_query("TEST", ["test"], date_range)
        
        assert 'project = "TEST"' in jql
        assert 'created >= "2024-01-01"' in jql
        assert 'created <= "2024-01-31"' in jql
    
    def test_build_jql_query_empty_keywords(self, jira_agent):
        """Test JQL query building with empty keywords."""
        jql = jira_agent._build_jql_query("TEST", [])
        
        assert 'project = "TEST"' in jql
        assert 'ORDER BY created DESC' in jql
        assert 'text ~' not in jql
    
    def test_parse_issue_success(self, jira_agent, sample_jira_response):
        """Test successful issue parsing."""
        issue_data = sample_jira_response["issues"][0]
        issue = jira_agent._parse_issue(issue_data)
        
        assert isinstance(issue, JiraIssue)
        assert issue.id == "10001"
        assert issue.key == "TEST-1"
        assert issue.summary == "Test bug report"
        assert issue.status == "Open"
        assert issue.assignee == "John Doe"
        assert issue.reporter == "Jane Smith"
        assert issue.issue_type == "Bug"
        assert issue.priority == "High"
        assert "test" in issue.labels
        assert "urgent" in issue.labels
        assert "Backend" in issue.components
    
    def test_parse_issue_invalid_data(self, jira_agent):
        """Test issue parsing with invalid data."""
        invalid_issue = {"invalid": "data"}
        issue = jira_agent._parse_issue(invalid_issue)
        
        assert issue is None
    
    def test_parse_comment_success(self, jira_agent):
        """Test successful comment parsing."""
        comment_data = {
            "id": "10001",
            "body": "Test comment",
            "created": "2024-01-01T10:00:00.000Z",
            "author": {"displayName": "John Doe"}
        }
        
        comment = jira_agent._parse_comment(comment_data)
        
        assert comment.id == "10001"
        assert comment.body == "Test comment"
        assert comment.author == "John Doe"
    
    def test_extract_attendees(self, jira_agent):
        """Test attendee extraction from text."""
        text = "Присутствовали: Иванов, Петров, Сидоров"
        attendees = jira_agent._extract_attendees(text)
        
        assert "Иванов" in attendees
        assert "Петров" in attendees
        assert "Сидоров" in attendees
    
    def test_extract_action_items(self, jira_agent):
        """Test action items extraction from text."""
        text = "- Fix the bug\n- Update documentation\n- Review code"
        actions = jira_agent._extract_action_items(text)
        
        assert len(actions) >= 1
        assert any("Fix the bug" in action for action in actions)
    
    def test_extract_text_context(self, jira_agent):
        """Test text context extraction."""
        issues = [
            JiraIssue(
                id="1", key="TEST-1", summary="Bug 1", status="Open",
                created=datetime.now(), updated=datetime.now(), issue_type="Bug"
            ),
            JiraIssue(
                id="2", key="TEST-2", summary="Bug 2", status="Closed",
                created=datetime.now(), updated=datetime.now(), issue_type="Bug"
            )
        ]
        
        context = jira_agent._extract_text_context(issues, [])
        
        assert "Issue: Bug 1" in context
        assert "Issue: Bug 2" in context
    
    @pytest.mark.asyncio
    @patch('src.agents.jira_agent.aiohttp.ClientSession')
    async def test_extract_meeting_protocol(self, mock_session_class, jira_agent):
        """Test meeting protocol extraction."""
        # Create issue that looks like meeting protocol
        issue = JiraIssue(
            id="1", key="MEET-1", summary="Протокол совещания", status="Done",
            created=datetime.now(), updated=datetime.now(), issue_type="Meeting"
        )
        
        # Create sample comment
        from src.core.models import JiraComment
        comments = [
            JiraComment(
                id="1", author="John Doe", body="Test comment",
                created=datetime.now()
            )
        ]
        
        protocol = await jira_agent._extract_meeting_protocol(issue, comments)
        
        assert protocol is not None
        assert protocol.title == "Протокол совещания"
        assert protocol.issue_id == "1"
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, jira_agent):
        """Test successful health check."""
        # Mock session creation and API call
        with patch('src.agents.jira_agent.aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            health = await jira_agent.health_check()
            
            assert health["status"] == "healthy"
            assert health["jira_configured"] is True
            assert health["jira_health"]["api_connected"] is True
    
    @pytest.mark.asyncio
    async def test_context_manager(self, mock_config):
        """Test async context manager functionality."""
        async with JiraAgent(mock_config) as agent:
            assert agent is not None
            assert agent.name == "JiraAgent"
        
        # Session should be closed after context exit
        assert agent.session is None


@pytest.mark.integration
class TestJiraAgentIntegration:
    """Integration tests for JiraAgent (requires real Jira instance)."""
    
    @pytest.mark.skip(reason="Requires real Jira instance")
    @pytest.mark.asyncio
    async def test_real_jira_connection(self):
        """Test connection to real Jira instance."""
        # This test would be skipped by default but can be run manually
        # with a real Jira instance for integration testing
        pass


if __name__ == "__main__":
    pytest.main([__file__])
