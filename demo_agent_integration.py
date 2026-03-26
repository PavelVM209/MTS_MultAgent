#!/usr/bin/env python3
"""
Agent Integration Demonstration

Shows comprehensive integration of DailyJiraAnalyzer and DailyMeetingAnalyzer
through the AgentOrchestrator with unified workflow execution.
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.agent_orchestrator import AgentOrchestrator
from src.agents.daily_jira_analyzer import DailyJiraAnalyzer
from src.agents.daily_meeting_analyzer import DailyMeetingAnalyzer
from src.core.base_agent import AgentConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_jira_data():
    """Create sample JIRA data for demonstration."""
    return {
        'jira_tasks': [
            {
                'key': 'PROJ-001',
                'summary': 'Разработать модуль аутентификации',
                'status': 'In Progress',
                'assignee': 'Иван Иванов',
                'reporter': 'Мария Сидорова',
                'priority': 'High',
                'created': '2024-03-20T10:00:00Z',
                'updated': '2024-03-25T15:30:00Z',
                'description': 'Необходимо разработать систему аутентификации с поддержкой OAuth 2.0',
                'project': {
                    'key': 'PROJ',
                    'name': 'MultAgent Platform'
                },
                'subtasks': [
                    {'key': 'PROJ-002', 'summary': 'UI для входа', 'status': 'Done'},
                    {'key': 'PROJ-003', 'summary': 'API endpoints', 'status': 'In Progress'}
                ]
            },
            {
                'key': 'PROJ-004',
                'summary': 'Настроить CI/CD pipeline',
                'status': 'Done',
                'assignee': 'Петр Петров',
                'reporter': 'Иван Иванов',
                'priority': 'Medium',
                'created': '2024-03-18T09:00:00Z',
                'updated': '2024-03-24T17:45:00Z',
                'description': 'Автоматизация сборки и развертывания проекта',
                'project': {
                    'key': 'PROJ',
                    'name': 'MultAgent Platform'
                }
            },
            {
                'key': 'PROJ-005',
                'summary': 'Оптимизация производительности базы данных',
                'status': 'To Do',
                'assignee': 'Елена Козлова',
                'reporter': 'Алексей Смирнов',
                'priority': 'Critical',
                'created': '2024-03-25T11:00:00Z',
                'updated': '2024-03-25T11:00:00Z',
                'description': 'Оптимизировать запросы и добавить индексы',
                'project': {
                    'key': 'PROJ',
                    'name': 'MultAgent Platform'
                }
            }
        ],
        'projects': [
            {
                'key': 'PROJ',
                'name': 'MultAgent Platform',
                'type': 'Software',
                'lead': 'Иван Иванов'
            }
        ],
        'employees': [
            {
                'name': 'Иван Иванов',
                'email': 'ivan.ivanov@example.com',
                'role': 'Team Lead',
                'department': 'Development'
            },
            {
                'name': 'Мария Сидорова',
                'email': 'maria.sidorova@example.com',
                'role': 'Senior Developer',
                'department': 'Development'
            },
            {
                'name': 'Петр Петров',
                'email': 'petr.petrov@example.com',
                'role': 'DevOps Engineer',
                'department': 'Operations'
            },
            {
                'name': 'Елена Козлова',
                'email': 'elena.kozlova@example.com',
                'role': 'DBA',
                'department': 'Infrastructure'
            },
            {
                'name': 'Алексей Смирнов',
                'email': 'alexey.smirnov@example.com',
                'role': 'Project Manager',
                'department': 'Management'
            }
        ]
    }


def create_sample_meeting_data():
    """Create sample meeting protocol data for demonstration."""
    return {
        'meeting_protocols': [
            {
                "id": "daily_standup_2024_03_25",
                "title": "Ежедневный стендап - Команда разработки",
                "date": "2024-03-25T09:00:00Z",
                "content": """
Ежедневное стендап совещание - 25.03.2024
==============================================

Участники: Иван Иванов (Team Lead), Мария Сидорова (Backend), Петр Петров (DevOps), Елена Козлова (DBA)

1. ПРОГРЕСС ЗА ВЧЕРА
--------------------
Иван: Провел code review для модуля аутентификации, запланировал следующие задачи
Мария: Завершила разработку API endpoints для аутентификации, начала интеграцию
Петр: Настроил CI/CD pipeline, все тесты проходят успешно
Елена: Проанализировала производительность БД, нашла узкие места

2. ПЛАН НА СЕГОДНЯ
------------------
Иван: Провести встречу с заказчиком по требованиям, спланировать спринт
Мария: Интегрировать frontend с backend API endpoints
Петр: Развернуть на тестовом стенде, настроить мониторинг
Елена: Создать оптимизационные запросы для БД

3. БЛОКЕРЫ И ПРОБЛЕМЫ
---------------------
Мария: Нужна помощь с настройкой CORS для frontend-бэкенд взаимодействия
Елена: Требуется доступ к production БД для анализа реальной нагрузки

4. ДЕЙСТВИЯ (ACTION ITEMS)
--------------------------
- Настроить CORS: ответственный Мария, срок 26.03.2024, приоритет high
- Дать доступ к production БД: ответственный Иван, срок 25.03.2024, приоритет critical
- Провести встречу с заказчиком: ответственный Иван, срок 25.03.2024
- Развернуть на тестовом стенде: ответственный Петр, срок 25.03.2024

5. РЕШЕНИЯ
-----------
- Запланировать демо новой функциональности на пятницу
- Провести нагрузочное тестирование на следующей неделе
- Внедрить код ревью для всех критичных изменений

6. СЛЕДУЮЩИЕ ШАГИ
----------------
- Подготовить отчет о прогрессе проекта
- Провести техническое ревью архитектуры
- Запланировать ресурсы на следующий спринт
""",
                "format": "text",
                "metadata": {
                    "meeting_type": "daily_standup",
                    "team": "development",
                    "duration_minutes": 30
                }
            },
            {
                "id": "sprint_planning_2024_03_24",
                "title": "Планирование Спринт 9 - Проект MultAgent Platform",
                "date": "2024-03-24T14:00:00Z",
                "content": """
Совещание по планированию Спринта 9
==================================

Организатор: Алексей Смирнов (Project Manager)
Участники: Иван, Мария, Петр, Елена, Алексей

ПОВЕСТКА ДНЯ:
1. Обзор результатов Спринта 8
2. Демонстрация готового функционала
3. Планирование Спринта 9

РЕЗУЛЬТАТЫ СПРИНТА 8:
- ✅ Модуль аутентификации (PROJ-001) - В работе
- ✅ CI/CD pipeline (PROJ-004) - Завершен
- ❌ Оптимизация БД (PROJ-005) - Перенесен

ПЛАН СПРИНТА 9:
- Завершить модуль аутентификации (PROJ-001)
- Оптимизация производительности БД (PROJ-005)
- Разработка панели администратора
- Интеграция с frontend
- Нагрузочное тестирование

ДЕЙСТВИЯ:
- Создать задачи в Jira: @мария, до 25.03.2024
- Провести оценку ресурсов: @иван, до 26.03.2024
- Подготовить тестовое окружение: @петр, до 27.03.2024
""",
                "format": "text",
                "metadata": {
                    "meeting_type": "sprint_planning",
                    "duration_minutes": 120,
                    "sprint_number": 9
                }
            }
        ]
    }


def print_section(title: str):
    """Print formatted section title."""
    print(f"\n{'='*70}")
    print(f"🚀 {title}")
    print(f"{'='*70}")


def print_subsection(title: str):
    """Print formatted subsection title."""
    print(f"\n📋 {title}")
    print("-" * 50)


async def demo_sequential_workflow():
    """Demonstrate sequential workflow execution."""
    print_section("Sequential Workflow Execution Demo")
    
    # Create orchestrator
    orchestrator = AgentOrchestrator()
    
    # Create agents
    jira_analyzer = DailyJiraAnalyzer()
    meeting_analyzer = DailyMeetingAnalyzer()
    
    # Register agents with priorities
    orchestrator.register_agent("daily_jira_analyzer", jira_analyzer, priority=2)
    orchestrator.register_agent("daily_meeting_analyzer", meeting_analyzer, priority=1)
    
    # Check health status
    print("🏥 Checking orchestrator health...")
    health = await orchestrator.get_health_status()
    print(f"   Status: {health['orchestrator_status']}")
    print(f"   LLM Client: {health['llm_client']}")
    print(f"   Memory Store: {health['memory_store']}")
    print(f"   Agent Health: {health['agent_health']}")
    
    # Prepare workflow configuration
    workflow_config = {
        'agents': ['daily_jira_analyzer', 'daily_meeting_analyzer'],
        'execution_constraints': {
            'sequenced': True,
            'fail_fast': False
        },
        'data_sharing': True
    }
    
    # Prepare data sources
    data_sources = {
        'daily_jira_analyzer': create_sample_jira_data(),
        'daily_meeting_analyzer': create_sample_meeting_data()
    }
    
    print(f"\n🔄 Executing sequential workflow...")
    print(f"   Agents: {', '.join(workflow_config['agents'])}")
    print(f"   Data Sharing: {workflow_config['data_sharing']}")
    
    # Execute workflow
    start_time = datetime.now()
    result = await orchestrator.execute_workflow(workflow_config, data_sources)
    execution_time = (datetime.now() - start_time).total_seconds()
    
    # Display results
    print_subsection("Workflow Execution Results")
    print(f"✅ Workflow ID: {result.workflow_id}")
    print(f"📊 Status: {result.status.value}")
    print(f"⏱️  Total Execution Time: {result.total_execution_time:.2f}s")
    print(f"🔄 Actual Execution Time: {execution_time:.2f}s")
    print(f"📈 Summary: {result.aggregated_data['summary']}")
    
    # Display individual agent results
    print_subsection("Individual Agent Results")
    for agent_result in result.agent_results:
        print(f"\n🤖 Agent: {agent_result.agent_name}")
        print(f"   ✅ Success: {agent_result.success}")
        print(f"   ⏱️  Execution Time: {agent_result.execution_time:.2f}s")
        print(f"   🎯 Quality Score: {agent_result.quality_score:.2f}")
        
        if agent_result.success:
            # Show key data points
            data = agent_result.result.data
            if 'projects' in data:
                print(f"   📁 Projects: {len(data['projects'])}")
            if 'employees' in data:
                print(f"   👥 Employees: {len(data['employees'])}")
            if 'action_items' in data:
                print(f"   📝 Action Items: {len(data['action_items'])}")
            if 'meeting_info' in data:
                print(f"   🏢 Meeting: {data['meeting_info']['title']}")
        else:
            print(f"   ❌ Error: {agent_result.error_message}")
    
    # Display correlations
    if result.aggregated_data.get('correlations'):
        print_subsection("Cross-Agent Correlations")
        correlations = result.aggregated_data['correlations']
        
        if 'common_entities' in correlations:
            entities = correlations['common_entities']
            if entities.get('projects'):
                print(f"📁 Common Projects: {', '.join(entities['projects'])}")
            if entities.get('employees'):
                print(f"👥 Common Employees: {', '.join(entities['employees'][:3])}...")
        
        if 'quality_analysis' in correlations:
            qa = correlations['quality_analysis']
            print(f"📊 Average Quality: {qa['average_quality']:.2f}")
            print(f"🏆 Highest Quality Agent: {qa['highest_quality_agent']}")
            print(f"📉 Lowest Quality Agent: {qa['lowest_quality_agent']}")
    
    return result


async def demo_parallel_workflow():
    """Demonstrate parallel workflow execution."""
    print_section("Parallel Workflow Execution Demo")
    
    # Create orchestrator
    orchestrator = AgentOrchestrator()
    
    # Create agents
    jira_analyzer = DailyJiraAnalyzer()
    meeting_analyzer = DailyMeetingAnalyzer()
    
    # Register agents
    orchestrator.register_agent("daily_jira_analyzer", jira_analyzer, priority=1)
    orchestrator.register_agent("daily_meeting_analyzer", meeting_analyzer, priority=1)
    
    # Prepare workflow configuration
    workflow_config = {
        'agents': ['daily_jira_analyzer', 'daily_meeting_analyzer'],
        'execution_constraints': {
            'sequenced': False,
            'fail_fast': False
        },
        'data_sharing': True
    }
    
    # Prepare data sources
    data_sources = {
        'daily_jira_analyzer': create_sample_jira_data(),
        'daily_meeting_analyzer': create_sample_meeting_data()
    }
    
    print(f"🔄 Executing parallel workflow...")
    print(f"   Agents: {', '.join(workflow_config['agents'])}")
    print(f"   Max Parallel Agents: {orchestrator.max_parallel_agents}")
    
    # Execute parallel workflow
    start_time = datetime.now()
    result = await orchestrator.execute_parallel_workflow(workflow_config, data_sources)
    execution_time = (datetime.now() - start_time).total_seconds()
    
    # Display results
    print_subsection("Parallel Workflow Results")
    print(f"✅ Workflow ID: {result.workflow_id}")
    print(f"📊 Status: {result.status.value}")
    print(f"⏱️  Total Execution Time: {result.total_execution_time:.2f}s")
    print(f"🔄 Actual Execution Time: {execution_time:.2f}s")
    print(f"🔀 Parallel Groups: {result.metadata['parallel_groups']}")
    print(f"📈 Summary: {result.aggregated_data['summary']}")
    
    # Performance comparison
    fastest_agent = min(result.agent_results, key=lambda x: x.execution_time)
    slowest_agent = max(result.agent_results, key=lambda x: x.execution_time)
    
    print_subsection("Performance Analysis")
    print(f"🚀 Fastest Agent: {fastest_agent.agent_name} ({fastest_agent.execution_time:.2f}s)")
    print(f"🐢 Slowest Agent: {slowest_agent.agent_name} ({slowest_agent.execution_time:.2f}s)")
    print(f"⚡ Parallel Gain: {max(0, slowest_agent.execution_time - result.total_execution_time):.2f}s")
    
    return result


async def demo_agent_statistics():
    """Demonstrate agent statistics and monitoring."""
    print_section("Agent Statistics & Monitoring Demo")
    
    # Create orchestrator
    orchestrator = AgentOrchestrator()
    
    # Create and register agents
    jira_analyzer = DailyJiraAnalyzer()
    meeting_analyzer = DailyMeetingAnalyzer()
    
    orchestrator.register_agent("daily_jira_analyzer", jira_analyzer, priority=2)
    orchestrator.register_agent("daily_meeting_analyzer", meeting_analyzer, priority=1)
    
    # Execute a few workflows to generate statistics
    print("🔄 Generating workflow statistics...")
    
    workflow_config = {
        'agents': ['daily_jira_analyzer', 'daily_meeting_analyzer'],
        'execution_constraints': {'sequenced': True, 'fail_fast': False},
        'data_sharing': True
    }
    
    data_sources = {
        'daily_jira_analyzer': create_sample_jira_data(),
        'daily_meeting_analyzer': create_sample_meeting_data()
    }
    
    # Execute multiple workflows
    for i in range(3):
        print(f"   Executing workflow {i+1}/3...")
        await orchestrator.execute_workflow(workflow_config, data_sources)
    
    # Get statistics
    print_subsection("Agent Execution Statistics")
    stats = await orchestrator.get_agent_statistics()
    
    for agent_name, agent_stats in stats.items():
        print(f"\n🤖 {agent_name}:")
        print(f"   Total Executions: {agent_stats['total_executions']}")
        print(f"   Success Count: {agent_stats['success_count']}")
        print(f"   Failure Count: {agent_stats['failure_count']}")
        print(f"   Success Rate: {agent_stats['success_rate']:.1%}")
        print(f"   Priority: {agent_stats['priority']}")
        if agent_stats['last_execution']:
            print(f"   Last Execution: {agent_stats['last_execution'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get workflow history
    print_subsection("Recent Workflow History")
    history = await orchestrator.get_workflow_history(limit=5)
    
    for i, workflow in enumerate(history, 1):
        print(f"\n🔄 Workflow {i}: {workflow['workflow_id']}")
        print(f"   Status: {workflow['status']}")
        print(f"   Start Time: {workflow['start_time']}")
        print(f"   Execution Time: {workflow['total_execution_time']:.2f}s")
    
    return orchestrator


async def demo_error_handling():
    """Demonstrate error handling and recovery."""
    print_section("Error Handling & Recovery Demo")
    
    # Create orchestrator
    orchestrator = AgentOrchestrator()
    
    # Create agents
    jira_analyzer = DailyJiraAnalyzer()
    meeting_analyzer = DailyMeetingAnalyzer()
    
    # Register agents
    orchestrator.register_agent("daily_jira_analyzer", jira_analyzer, priority=2)
    orchestrator.register_agent("daily_meeting_analyzer", meeting_analyzer, priority=1)
    
    # Test with invalid data
    print("🧪 Testing error handling with invalid data...")
    
    workflow_config = {
        'agents': ['daily_jira_analyzer', 'daily_meeting_analyzer'],
        'execution_constraints': {'sequenced': True, 'fail_fast': False},  # Continue on errors
        'data_sharing': True
    }
    
    # Prepare invalid data sources
    invalid_data_sources = {
        'daily_jira_analyzer': {'invalid': 'data'},  # Invalid JIRA data
        'daily_meeting_analyzer': create_sample_meeting_data()  # Valid meeting data
    }
    
    # Execute workflow with error handling
    result = await orchestrator.execute_workflow(workflow_config, invalid_data_sources)
    
    print_subsection("Error Handling Results")
    print(f"✅ Workflow ID: {result.workflow_id}")
    print(f"📊 Status: {result.status.value}")  # Should be PARTIAL
    print(f"📈 Summary: {result.aggregated_data['summary']}")
    
    # Show which agents failed
    print_subsection("Agent Status Analysis")
    for agent_result in result.agent_results:
        status_icon = "✅" if agent_result.success else "❌"
        print(f"{status_icon} {agent_result.agent_name}: {agent_result.success}")
        if not agent_result.success:
            print(f"   Error: {agent_result.error_message}")
    
    return result


async def demo_performance_comparison():
    """Compare performance between sequential and parallel execution."""
    print_section("Performance Comparison Demo")
    
    # Create orchestrator
    orchestrator = AgentOrchestrator()
    
    # Create agents
    jira_analyzer = DailyJiraAnalyzer()
    meeting_analyzer = DailyMeetingAnalyzer()
    
    orchestrator.register_agent("daily_jira_analyzer", jira_analyzer, priority=1)
    orchestrator.register_agent("daily_meeting_analyzer", meeting_analyzer, priority=1)
    
    # Prepare data
    workflow_config = {
        'agents': ['daily_jira_analyzer', 'daily_meeting_analyzer'],
        'data_sharing': True
    }
    
    data_sources = {
        'daily_jira_analyzer': create_sample_jira_data(),
        'daily_meeting_analyzer': create_sample_meeting_data()
    }
    
    # Sequential execution
    print("🔄 Running sequential execution...")
    sequential_config = {
        **workflow_config,
        'execution_constraints': {'sequenced': True, 'fail_fast': False}
    }
    
    sequential_start = datetime.now()
    sequential_result = await orchestrator.execute_workflow(sequential_config, data_sources)
    sequential_time = (datetime.now() - sequential_start).total_seconds()
    
    # Parallel execution
    print("🔄 Running parallel execution...")
    parallel_config = {
        **workflow_config,
        'execution_constraints': {'sequenced': False, 'fail_fast': False}
    }
    
    parallel_start = datetime.now()
    parallel_result = await orchestrator.execute_parallel_workflow(parallel_config, data_sources)
    parallel_time = (datetime.now() - parallel_start).total_seconds()
    
    # Performance comparison
    print_subsection("Performance Comparison Results")
    print(f"🕐 Sequential Execution: {sequential_time:.2f}s")
    print(f"⚡ Parallel Execution: {parallel_time:.2f}s")
    print(f"📈 Performance Gain: {max(0, sequential_time - parallel_time):.2f}s ({max(0, (sequential_time - parallel_time) / sequential_time * 100):.1f}%)")
    
    # Quality comparison
    sequential_avg_quality = sum(r.quality_score for r in sequential_result.agent_results) / len(sequential_result.agent_results)
    parallel_avg_quality = sum(r.quality_score for r in parallel_result.agent_results) / len(parallel_result.agent_results)
    
    print(f"\n🎯 Quality Comparison:")
    print(f"   Sequential Avg Quality: {sequential_avg_quality:.3f}")
    print(f"   Parallel Avg Quality: {parallel_avg_quality:.3f}")
    print(f"   Quality Difference: {abs(sequential_avg_quality - parallel_avg_quality):.3f}")
    
    return {
        'sequential': {'time': sequential_time, 'result': sequential_result},
        'parallel': {'time': parallel_time, 'result': parallel_result}
    }


async def main():
    """Main demonstration function."""
    print("🚀 Agent Integration Demonstration")
    print("=" * 70)
    print("Showing comprehensive integration of DailyJiraAnalyzer and DailyMeetingAnalyzer")
    print("through AgentOrchestrator with unified workflow execution")
    
    try:
        # Run sequential workflow demo
        await demo_sequential_workflow()
        
        # Run parallel workflow demo
        await demo_parallel_workflow()
        
        # Run agent statistics demo
        await demo_agent_statistics()
        
        # Run error handling demo
        await demo_error_handling()
        
        # Run performance comparison demo
        await demo_performance_comparison()
        
        print_section("Demo Complete")
        print("✅ All integration demonstrations completed successfully!")
        
        print("\n🎯 Key Capabilities Demonstrated:")
        print("1. ✅ Sequential workflow execution with data sharing")
        print("2. ✅ Parallel workflow execution for performance optimization")
        print("3. ✅ Agent coordination and result aggregation")
        print("4. ✅ Cross-agent data correlation and analysis")
        print("5. ✅ Error handling and graceful degradation")
        print("6. ✅ Performance monitoring and statistics")
        print("7. ✅ Health monitoring and status tracking")
        
        print("\n🚀 Integration Highlights:")
        print("- 🔄 Unified workflow orchestration")
        print("- 📊 Intelligent result aggregation")
        print("- ⚡ Performance optimization with parallel execution")
        print("- 🛡️ Robust error handling and recovery")
        print("- 📈 Comprehensive monitoring and statistics")
        print("- 🔗 Cross-agent data correlation")
        print("- 🏥 Health monitoring and diagnostics")
        
        print("\n📋 Next Steps:")
        print("1. Configure real JIRA and Confluence connections")
        print("2. Set up automated scheduling with cron jobs")
        print("3. Configure production deployment settings")
        print("4. Set up monitoring and alerting")
        print("5. Implement dashboard for real-time monitoring")
        
    except Exception as e:
        logger.error(f"Integration demonstration failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
