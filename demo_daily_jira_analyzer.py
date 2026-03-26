#!/usr/bin/env python3
"""
Daily JIRA Analyzer Demonstration

Shows comprehensive JIRA analysis capabilities including:
- Task parsing and validation
- Employee workload analysis
- Project progress tracking
- LLM-powered insights
- Quality metrics
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.agents.daily_jira_analyzer import DailyJiraAnalyzer
from src.core.base_agent import AgentConfig
from src.core.llm_client import LLMClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_jira_data():
    """Create realistic sample JIRA data for demonstration."""
    return [
        {
            "id": "1",
            "key": "MTS-101",
            "summary": "Разработка модуля аутентификации пользователей",
            "status": "in_progress",
            "priority": "high",
            "assignee": "ivan.ivanov",
            "reporter": "petr.petrov",
            "project": "MTS",
            "created": "2024-03-20T10:00:00Z",
            "updated": "2024-03-25T15:30:00Z",
            "due_date": "2024-03-28T17:00:00Z",
            "story_points": "8",
            "labels": ["backend", "auth", "security"],
            "components": ["authentication"],
            "description": "Реализовать OAuth2 аутентификацию с поддержкой JWT токенов",
            "comments_count": 12
        },
        {
            "id": "2",
            "key": "MTS-102",
            "summary": "Проектирование архитектуры базы данных",
            "status": "done",
            "priority": "medium",
            "assignee": "maria.sidorova",
            "reporter": "ivan.ivanov",
            "project": "MTS",
            "created": "2024-03-18T09:00:00Z",
            "updated": "2024-03-22T14:00:00Z",
            "due_date": "2024-03-20T17:00:00Z",
            "story_points": 5,
            "labels": ["database", "architecture"],
            "components": ["backend"],
            "description": "Спроектировать схему БД для пользователей и ролей",
            "comments_count": 8
        },
        {
            "id": "3",
            "key": "MTS-103",
            "summary": "Исправление критического бага в системе логирования",
            "status": "blocked",
            "priority": "highest",
            "assignee": "ivan.ivanov",
            "reporter": "alexey.smirnov",
            "project": "MTS",
            "created": "2024-03-24T11:00:00Z",
            "updated": "2024-03-25T16:00:00Z",
            "due_date": "2024-03-25T17:00:00Z",
            "story_points": 3,
            "labels": ["bug", "critical", "logging"],
            "components": ["backend"],
            "description": "Критическая ошибка приводит к потере логов системы",
            "comments_count": 15
        },
        {
            "id": "4",
            "key": "MTS-104",
            "summary": "Разработка REST API для управления пользователями",
            "status": "in_progress",
            "priority": "high",
            "assignee": "petr.petrov",
            "reporter": "maria.sidorova",
            "project": "MTS",
            "created": "2024-03-21T13:00:00Z",
            "updated": "2024-03-25T12:00:00Z",
            "due_date": "2024-03-30T17:00:00Z",
            "story_points": 13,
            "labels": ["api", "backend", "users"],
            "components": ["api"],
            "description": "Создать CRUD операции для управления пользователями",
            "comments_count": 6
        }
    ]


def print_section(title: str):
    """Print formatted section title."""
    print(f"\n{'='*60}")
    print(f"🎯 {title}")
    print(f"{'='*60}")


def print_subsection(title: str):
    """Print formatted subsection title."""
    print(f"\n📋 {title}")
    print("-" * 40)


async def demo_basic_analysis():
    """Demonstrate basic JIRA analysis without LLM."""
    print_section("Daily JIRA Analyzer - Basic Analysis Demo")
    
    # Create analyzer
    config = AgentConfig(
        name="DailyJiraAnalyzer",
        description="Demo JIRA analysis without LLM",
        version="1.0.0"
    )
    
    analyzer = DailyJiraAnalyzer(config)
    
    # Check health status
    print("🏥 Checking analyzer health...")
    health = await analyzer.get_health_status()
    print(f"   Status: {health['status']}")
    print(f"   LLM Client: {health['llm_client']}")
    print(f"   Memory Store: {health['memory_store']}")
    
    # Create sample data
    sample_data = create_sample_jira_data()
    print(f"\n📊 Analyzing {len(sample_data)} JIRA tasks...")
    
    # Execute analysis without LLM
    start_time = datetime.now()
    
    result = await analyzer.execute({
        'jira_tasks': sample_data,
        'include_llm_analysis': False,
        'filters': {
            'projects': ['MTS'],
            'status_exclude': ['to_do']
        }
    })
    
    execution_time = (datetime.now() - start_time).total_seconds()
    
    if result.success:
        print_subsection("Analysis Results Summary")
        print(f"✅ Status: {result.success}")
        print(f"📝 Message: {result.message}")
        print(f"⏱️  Execution Time: {execution_time:.2f}s")
        print(f"📊 Tasks Analyzed: {result.metadata.get('tasks_analyzed', 0)}")
        print(f"🎯 Quality Score: {result.metadata.get('quality_score', 0):.2f}")
        
        # Display employee workload
        if 'employees_workload' in result.data:
            print_subsection("Employee Workload Analysis")
            for employee, workload in result.data['employees_workload'].items():
                print(f"\n👤 {employee}")
                print(f"   Total Tasks: {workload['total_tasks']}")
                print(f"   Completed: {workload['completed_tasks']}")
                print(f"   In Progress: {workload['in_progress_tasks']}")
                print(f"   Blocked: {workload['blocked_tasks']}")
                print(f"   Overdue: {workload['overdue_tasks']}")
                print(f"   Completion Rate: {workload['completion_rate']:.1%}")
                print(f"   Story Points: {workload['total_story_points']}")
        
        # Display project progress
        if 'projects_progress' in result.data:
            print_subsection("Project Progress Analysis")
            for project, progress in result.data['projects_progress'].items():
                print(f"\n🚀 {project}")
                print(f"   Total Tasks: {progress['total_tasks']}")
                print(f"   Completed: {progress['completed_tasks']}")
                print(f"   In Progress: {progress['in_progress_tasks']}")
                print(f"   Completion: {progress['completion_percentage']:.1f}%")
                print(f"   Active Employees: {len(progress['active_employees'])}")
                if progress['blockers']:
                    print(f"   Blockers: {len(progress['blockers'])}")
        
        # Display insights
        if 'insights' in result.data:
            print_subsection("Generated Insights")
            for i, insight in enumerate(result.data['insights'], 1):
                print(f"💡 {i}. {insight}")
        
        # Display recommendations
        if 'recommendations' in result.data:
            print_subsection("Recommendations")
            for i, rec in enumerate(result.data['recommendations'], 1):
                print(f"🎯 {i}. {rec}")
    
    else:
        print(f"❌ Analysis failed: {result.message}")
        if result.error:
            print(f"Error: {result.error}")


async def demo_task_parsing():
    """Demonstrate JIRA task parsing capabilities."""
    print_section("JIRA Task Parsing Demo")
    
    analyzer = DailyJiraAnalyzer()
    
    # Test various task formats
    test_tasks = [
        {
            "id": "1",
            "key": "PROJ-001",
            "summary": "Test task with different formats",
            "status": "In Progress",
            "priority": "High",
            "story_points": "5 SP",
            "created": "2024-03-25T10:00:00Z",
            "assignee": "test.user"
        },
        {
            "id": "2",
            "key": "PROJ-002",
            "summary": "Task with numeric story points",
            "status": "done",
            "priority": "medium",
            "story_points": 3.5,
            "created": "2024-03-24T15:30:00Z",
            "assignee": "another.user"
        }
    ]
    
    print_subsection("Task Parsing Results")
    
    for i, task_data in enumerate(test_tasks, 1):
        print(f"\n📝 Task {i}: {task_data['key']}")
        print(f"   Original Status: '{task_data['status']}'")
        print(f"   Original Priority: '{task_data['priority']}'")
        print(f"   Original Story Points: '{task_data['story_points']}'")
        
        # Parse using analyzer methods
        parsed_status = analyzer._parse_status(task_data['status'])
        parsed_priority = analyzer._parse_priority(task_data['priority'])
        parsed_story_points = analyzer._parse_story_points(task_data['story_points'])
        parsed_datetime = analyzer._parse_datetime(task_data['created'])
        
        print(f"   Parsed Status: {parsed_status.value}")
        print(f"   Parsed Priority: {parsed_priority.value}")
        print(f"   Parsed Story Points: {parsed_story_points}")
        print(f"   Parsed DateTime: {parsed_datetime}")
    
    # Parse all tasks together
    print_subsection("Batch Task Parsing")
    parsed_tasks = await analyzer._parse_jira_tasks(test_tasks)
    
    print(f"✅ Successfully parsed {len(parsed_tasks)} tasks")
    for task in parsed_tasks:
        print(f"   {task.key}: {task.summary} ({task.status.value}, {task.story_points} SP)")


async def main():
    """Main demonstration function."""
    print("🚀 Daily JIRA Analyzer Demonstration")
    print("=" * 60)
    
    try:
        # Run basic analysis demo
        await demo_basic_analysis()
        
        # Run task parsing demo
        await demo_task_parsing()
        
        print_section("Demo Complete")
        print("✅ All demonstrations completed successfully!")
        print("\nNext steps:")
        print("1. Configure OpenAI API key for LLM features")
        print("2. Set up JIRA integration")
        print("3. Configure scheduler for daily analysis")
        print("4. Add Confluence integration for reporting")
        
    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
