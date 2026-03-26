"""
MTS MultAgent System - Agents Module

This module contains all specialized agents for the multi-agent system:
- JiraAgent: Integration with Jira API
- ContextAnalyzer: Text analysis and context extraction
- ConfluenceAgent: Confluence API integration
- ComparisonAgent: Data comparison and analysis
"""

__version__ = "0.1.0"

from agents.jira_agent import JiraAgent
from agents.context_analyzer import ContextAnalyzer

__all__ = [
    "JiraAgent",
    "ContextAnalyzer"
]
