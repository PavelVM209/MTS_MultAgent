#!/usr/bin/env python3
"""
Demo Script for MTS_MultAgent

This script demonstrates the basic functionality of the system
without requiring real Jira/Confluence credentials.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.config import initialize_config, ConfigManager
from src.core.models import JiraTask, JiraResult, JiraIssue, WorkflowTask
from src.agents.jira_agent import JiraAgent

import structlog

logger = structlog.get_logger()


def print_banner():
    """Print demo banner."""
    print("=" * 60)
    print("🚀 MTS_MultAgent Demo")
    print("=" * 60)
    print("This demo shows the core functionality without API calls")
    print("=" * 60)


def demo_configuration():
    """Demonstrate configuration management."""
    print("\n📋 Configuration Demo")
    print("-" * 30)
    
    try:
        # Create demo environment file
        demo_env = """# Demo Configuration
PROJECT_NAME="DemoProject"
DEBUG=true
TEST_MODE=true

JIRA_BASE_URL="https://demo.atlassian.net"
JIRA_ACCESS_TOKEN="demo_token"
JIRA_USERNAME="demo@example.com"

CONFLUENCE_BASE_URL="https://demo.atlassian.net/wiki"
CONFLUENCE_ACCESS_TOKEN="demo_token"
CONFLUENCE_SPACE="DEMO"
ROOT_PAGE_ID_TO_ADD_NEW_PAGES=12345

LOG_LEVEL="INFO"
"""
        
        with open(".env.demo", "w") as f:
            f.write(demo_env)
        
        # Initialize configuration
        config_manager = ConfigManager(".env.demo")
        config = config_manager.config
        
        print(f"✅ Project: {config.project_name}")
        print(f"🔧 Debug: {config.debug}")
        print(f"🧪 Test Mode: {config.test_mode}")
        print(f"🌐 Jira URL: {config.jira.base_url}")
        print(f"📝 Confluence Space: {config.confluence.space}")
        print(f"📊 Excel Path: {config.excel.file_path}")
        
        return config_manager
        
    except Exception as e:
        print(f"❌ Configuration demo failed: {e}")
        return None


def demo_models():
    """Demonstrate Pydantic models."""
    print("\n🏗️  Models Demo")
    print("-" * 30)
    
    try:
        # Create demo Jira task
        task = JiraTask(
            project_key="DEMO",
            task_description="Analyze project metrics",
            search_keywords=["metrics", "performance", "deadline"],
            max_results=10
        )
        
        print(f"📝 Task: {task.task_description}")
        print(f"🔑 Project: {task.project_key}")
        print(f"🔍 Keywords: {', '.join(task.search_keywords)}")
        
        # Create demo Jira issue
        from datetime import datetime
        issue = JiraIssue(
            id="10001",
            key="DEMO-1",
            summary="Performance optimization needed",
            description="The system is running slow",
            status="Open",
            assignee="John Doe",
            reporter="Jane Smith",
            created=datetime.now(),
            updated=datetime.now(),
            issue_type="Task",
            priority="High"
        )
        
        print(f"🐛 Issue: {issue.key} - {issue.summary}")
        print(f"📊 Status: {issue.status}, Priority: {issue.priority}")
        
        # Create demo result
        result = JiraResult(
            issues=[issue],
            total_count=1,
            extracted_context="Performance issues detected in the system",
            search_summary={
                "project_key": "DEMO",
                "keywords": task.search_keywords,
                "issues_found": 1
            }
        )
        
        print(f"📈 Found {len(result.issues)} issues")
        print(f"🔍 Context: {result.extracted_context[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Models demo failed: {e}")
        return False


async def demo_jira_agent():
    """Demonstrate JiraAgent functionality (without API calls)."""
    print("\n🤖 JiraAgent Demo")
    print("-" * 30)
    
    try:
        # Create demo config
        demo_config = {
            "jira": {
                "base_url": "https://demo.atlassian.net",
                "access_token": "demo_token",
                "username": "demo@example.com",
                "timeout": 30
            },
            "debug": True,
            "test_mode": True,
            "logging": {
                "level": "INFO",
                "file_path": "logs/demo.log"
            },
            "performance": {
                "max_concurrent_requests": 10,
                "cache_ttl_seconds": 3600
            }
        }
        
        # Create agent
        agent = JiraAgent(demo_config)
        
        print(f"🤖 Agent: {agent.name}")
        print(f"🌐 Base URL: {agent.base_url}")
        print(f"⏱️  Timeout: {agent.timeout}s")
        
        # Test validation
        task_data = {
            "project_key": "DEMO",
            "task_description": "Test task",
            "search_keywords": ["test"],
            "max_results": 5
        }
        
        is_valid = await agent.validate(task_data)
        print(f"✅ Task validation: {'Passed' if is_valid else 'Failed'}")
        
        # Test JQL query building
        jql = agent._build_jql_query(
            "DEMO", 
            ["performance", "bug"],
            {"from": "2024-01-01", "to": "2024-01-31"}
        )
        print(f"🔍 JQL Query: {jql}")
        
        # Test issue parsing
        demo_issue_data = {
            "id": "10001",
            "key": "DEMO-1",
            "fields": {
                "summary": "Demo issue",
                "description": "This is a demo issue",
                "status": {"name": "Open"},
                "assignee": {"displayName": "John Doe"},
                "reporter": {"displayName": "Jane Smith"},
                "created": "2024-01-01T10:00:00.000Z",
                "updated": "2024-01-02T10:00:00.000Z",
                "issuetype": {"name": "Task"},
                "priority": {"name": "High"},
                "labels": ["demo"],
                "components": [{"name": "Backend"}]
            }
        }
        
        parsed_issue = agent._parse_issue(demo_issue_data)
        if parsed_issue:
            print(f"📊 Parsed Issue: {parsed_issue.key} - {parsed_issue.summary}")
        
        # Test text extraction
        text = "Присутствовали: Иванов, Петров. Действия: - Исправить bug - Обновить docs"
        attendees = agent._extract_attendees(text)
        actions = agent._extract_action_items(text)
        
        print(f"👥 Attendees: {', '.join(attendees)}")
        print(f"⚡ Actions: {len(actions)} items found")
        
        # Test health check
        health = await agent.health_check()
        print(f"🏥 Health: {health['status']}")
        print(f"🔧 Configured: {health['jira_configured']}")
        
        # Clean up session
        if agent.session:
            await agent.session.close()
        
        return True
        
    except Exception as e:
        print(f"❌ JiraAgent demo failed: {e}")
        return False


def demo_workflow():
    """Demonstrate workflow creation."""
    print("\n🔄 Workflow Demo")
    print("-" * 30)
    
    try:
        # Create demo workflow task
        workflow = WorkflowTask(
            description="Analyze project performance metrics",
            project_key="DEMO",
            keywords=["performance", "metrics", "optimization"],
            date_range={"from": "2024-01-01", "to": "2024-01-31"},
            excel_files=["data/excel/sample_data.xlsx"]
        )
        
        print(f"📝 Task: {workflow.description}")
        print(f"🔑 Project: {workflow.project_key}")
        print(f"🔍 Keywords: {', '.join(workflow.keywords)}")
        print(f"📅 Date Range: {workflow.date_range['from']} to {workflow.date_range['to']}")
        print(f"📊 Excel Files: {', '.join(workflow.excel_files)}")
        
        # Check if Excel files exist
        for file_path in workflow.excel_files:
            if os.path.exists(file_path):
                print(f"✅ File exists: {file_path}")
                size = os.path.getsize(file_path)
                print(f"📏 File size: {size} bytes")
            else:
                print(f"❌ File missing: {file_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow demo failed: {e}")
        return False


def demo_project_structure():
    """Show project structure."""
    print("\n📁 Project Structure Demo")
    print("-" * 30)
    
    structure = {
        "src/": [
            "agents/__init__.py",
            "agents/jira_agent.py",
            "core/__init__.py", 
            "core/base_agent.py",
            "core/config.py",
            "core/models.py",
            "cli/__init__.py",
            "cli/main.py"
        ],
        "tests/": [
            "__init__.py",
            "test_jira_agent.py"
        ],
        "memory-bank/": [
            "projectbrief.md",
            "productContext.md", 
            "systemPatterns.md",
            "techContext.md",
            "agentsSpec.md",
            "activeContext.md",
            "progress.md"
        ],
        "config/": [],
        "data/excel/": [
            "sample_data.xlsx"
        ]
    }
    
    for directory, files in structure.items():
        print(f"📂 {directory}")
        for file in files:
            path = Path(directory) / file if files else Path(directory)
            if path.exists():
                print(f"  ✅ {file}")
            else:
                print(f"  ❌ {file}")
    
    # Count total files
    total_files = 0
    for files in structure.values():
        total_files += len(files)
    
    print(f"\n📊 Total files in project: {total_files}")


async def main():
    """Main demo function."""
    print_banner()
    
    # Check virtual environment
    print("\n🔍 Checking environment...")
    import sys
    if sys.prefix == sys.base_prefix:
        print("⚠️  WARNING: No virtual environment detected!")
        print("💡 Please activate virtual environment first:")
        print("   source venv/bin/activate  # Linux/Mac")
        print("   venv\\Scripts\\activate     # Windows")
        print()
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return
    else:
        print("✅ Virtual environment is active")
    
    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Please run this script from the project root directory")
        return
    
    try:
        # Run demos
        print("\n🎯 Running Demos...")
        
        # Configuration demo
        config_manager = demo_configuration()
        if not config_manager:
            print("❌ Configuration demo failed, stopping")
            return
        
        # Models demo
        if not demo_models():
            print("❌ Models demo failed, stopping")
            return
        
        # JiraAgent demo
        if not await demo_jira_agent():
            print("❌ JiraAgent demo failed, stopping")
            return
        
        # Workflow demo
        if not demo_workflow():
            print("❌ Workflow demo failed, stopping")
            return
        
        # Project structure demo
        demo_project_structure()
        
        # Cleanup demo file
        demo_env_path = Path(".env.demo")
        if demo_env_path.exists():
            demo_env_path.unlink()
            print("\n🧹 Cleaned up demo files")
        
        print("\n" + "=" * 60)
        print("🎉 All demos completed successfully!")
        print("=" * 60)
        print("\n💡 Next steps:")
        print("1. Copy .env.example to .env and add your real credentials")
        print("2. Run: python -m src.cli.main --help")
        print("3. Try: python -m src.cli.main config")
        print("4. Try: python -m src.cli.main health --agent jira")
        print("5. Run tests: pytest tests/")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo cancelled by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
