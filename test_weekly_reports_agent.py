#!/usr/bin/env python3
"""
Тестирование WeeklyReports Agent для Employee Monitoring System

Задача: Трегий агент раз в неделю в пятницу вечером 
делает комплексный анализ с выводами и комментариями по каждому сотруднику.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Добавляем src в Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agents.weekly_reports_agent_complete import WeeklyReportsAgentComplete
from core.llm_client import LLMClient

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_weekly_reports_agent():
    """Тестирование WeeklyReports Agent."""
    
    print("=" * 80)
    print("TESTING WeeklyReportsAgent - WEEKLY COMPREHENSIVE ANALYSIS")
    print("=" * 80)
    
    try:
        # Инициализация агента
        agent = WeeklyReportsAgentComplete()
        print(f"✅ Agent initialized: {agent.__class__.__name__}")
        print(f"📝 Description: {agent.config.description}")
        print(f"🔢 Version: {agent.config.version}")
        
        # Проверка здоровья
        print("\n📊 Checking agent health...")
        health = await agent.get_health_status()
        print(f"Status: {health['status']}")
        print(f"LLM Client: {health['llm_client']}")
        print(f"Memory Store: {health['memory_store']}")
        print(f"Confluence Client: {health['confluence_client']}")
        print(f"Reports Directory: {health['reports_directory']}")
        
        # Проверка даты (только пятница)
        today = datetime.now()
        if today.weekday() != 4:  # 4 = Friday
            print(f"\n⚠️  Today is {today.strftime('%A')}. Weekly reports only run on Fridays.")
            print("🔧 Forcing the agent to run anyway for testing...")
        
        # Создаем тестовые данные
        print("\n📋 Creating test employee data...")
        
        # Тестовые данные за неделю
        test_data = {
            'analysis_week': {
                'week_start': (datetime.now() - timedelta(days=7)).date().isoformat(),
                'week_end': datetime.now().date().isoformat(),
                'employees': {
                    'Иванов Иван': {
                        ' tasks_completed': 5,
                        'tasks_in_progress': 2,
                        'total_commits': 15,
                        'meeting_participation': {
                            'total_meetings': 3,
                            'meetings_attended': 3,
                            'speaking_turns': 25,
                            'questions_asked': 8,
                            'suggestions_made': 5,
                            'engagement_score': 0.8
                        },
                        'quality_metrics': {
                            'code_review_score': 0.9,
                            'task_completion_rate': 0.83,
                            'collaboration_score': 0.85
                        },
                        'concerns': ['Риск выгорания', 'Недостаточная документация'],
                        'achievements': ['Решил сложную проблему с производительностью', 'Помог новичку']
                    },
                    'Петров Петр': {
                        'tasks_completed': 3,
                        'tasks_in_progress': 4,
                        'total_commits': 8,
                        'meeting_participation': {
                            'total_meetings': 3,
                            'meetings_attended': 2,
                            'speaking_turns': 12,
                            'questions_asked': 3,
                            'suggestions_made': 2,
                            'engagement_score': 0.5
                        },
                        'quality_metrics': {
                            'code_review_score': 0.7,
                            'task_completion_rate': 0.43,
                            'collaboration_score': 0.6
                        },
                        'concerns': ['Низкая активность в встречах', 'Пропустил дедлайн'],
                        'achievements': ['Успешно завершил сложную задачу']
                    },
                    'Сидорова Мария': {
                        'tasks_completed': 7,
                        'tasks_in_progress': 1,
                        'total_commits': 22,
                        'meeting_participation': {
                            'total_meetings': 3,
                            'meetings_attended': 3,
                            'speaking_turns': 35,
                            'questions_asked': 12,
                            'suggestions_made': 8,
                            'engagement_score': 0.95
                        },
                        'quality_metrics': {
                            'code_review_score': 0.95,
                            'task_completion_rate': 0.88,
                            'collaboration_score': 0.92
                        },
                        'concerns': [],
                        'achievements': ['Лидер спринта', 'Отличная коммуникация', 'Помогла команде решить блокер']
                    }
                },
                'team_metrics': {
                    'total_tasks_completed': 15,
                    'total_tasks_in_progress': 7,
                    'total_commits': 45,
                    'avg_task_completion_rate': 0.71,
                    'team_collaboration_score': 0.79
                }
            }
        }
        
        print(f"📊 Created test data for {len(test_data['analysis_week']['employees'])} employees")
        
        # Запуск анализа
        print("\n🚀 Starting weekly comprehensive analysis...")
        start_time = datetime.now()
        
        result = await agent.execute(test_data)
        
        execution_time = datetime.now() - start_time
        
        if result.success:
            print(f"⏱️  Analysis completed in {execution_time.total_seconds():.2f} seconds")
            print(f"✅ Analysis completed successfully!")
            print(f"📊 Message: {result.message}")
            
            # Метаданные
            metadata = result.metadata
            print(f"\n📈 Execution metadata:")
            print(f"  - Execution time: {metadata.get('execution_time', 0):.2f}s")
            print(f"  - Employees analyzed: {metadata.get('employees_analyzed', 0)}")
            print(f"  - Team score: {metadata.get('team_score', 0):.2f}")
            print(f"  - Confluence published: {metadata.get('confluence_published', False)}")
            print(f"  - Analysis date: {metadata.get('analysis_date', 'N/A')}")
            
            # Результаты анализа
            analysis_data = result.data
            if analysis_data:
                print(f"\n📊 Analysis Results:")
                print(f"  - Week period: {analysis_data.get('week_start', 'N/A')} to {analysis_data.get('week_end', 'N/A')}")
                print(f"  - Total employees: {analysis_data.get('total_employees', 0)}")
                print(f"  - Total tasks completed: {analysis_data.get('total_tasks_completed', 0)}")
                print(f"  - Team performance score: {analysis_data.get('team_performance_score', 0):.2f}")
                
                # Детализация по сотрудникам
                employee_analyses = analysis_data.get('employee_analyses', {})
                if employee_analyses:
                    print(f"\n👥 Employee Analysis Details:")
                    for employee_name, employee_data in employee_analyses.items():
                        print(f"  👤 {employee_name}:")
                        print(f"    - Performance score: {employee_data.get('performance_score', 0):.2f}")
                        print(f"    - Tasks completed: {employee_data.get('tasks_completed', 0)}")
                        print(f"    - Engagement level: {employee_data.get('engagement_level', 'N/A')}")
                        print(f"    - Leadership indicators: {len(employee_data.get('leadership_indicators', []))}")
                        print(f"    - Concerns: {len(employee_data.get('concerns', []))}")
                        if employee_data.get('llm commentary'):
                            commentary = employee_data['llm commentary']
                            print(f"    - Commentary: {commentary[:100]}...")
                
                # Team insights
                team_insights = analysis_data.get('team_insights', [])
                if team_insights:
                    print(f"\n💡 Team Insights:")
                    for insight in team_insights:
                        print(f"  • {insight}")
                
                # Recommendations
                recommendations = analysis_data.get('recommendations', [])
                if recommendations:
                    print(f"\n🎯 Recommendations:")
                    for rec in recommendations:
                        print(f"  • {rec}")
                
                print(f"\n🎉 WEEKLY REPORTS AGENT TEST COMPLETED SUCCESSFULLY!")
                print(f"✅ WeeklyReportsAgent is working correctly")
                
            else:
                print(f"⚠️  Analysis data is empty")
                
        else:
            print(f"❌ Analysis failed!")
            print(f"Error: {result.error}")
            if result.data:
                print(f"Data: {result.data}")
        
        # Проверка сохраненных отчетов
        print(f"\n📁 Checking saved reports...")
        reports_dir = Path("reports/weekly")
        if reports_dir.exists():
            weekly_reports = list(reports_dir.glob("**/*.json"))
            if weekly_reports:
                print(f"✅ Found {len(weekly_reports)} weekly reports")
                for report_file in weekly_reports[-3:]:  # Последние 3 отчета
                    try:
                        print(f"  📄 {report_file.relative_to(Path.cwd())}")
                    except ValueError:
                        print(f"  📄 {report_file}")
            else:
                print(f"⚠️  No weekly reports found")
        
        return result.success
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"❌ Test failed: {e}")
        return False

async def main():
    """Главная функция."""
    try:
        success = await test_weekly_reports_agent()
        if success:
            print(f"\n🎉 All tests passed!")
            return 0
        else:
            print(f"\n❌ Some tests failed!")
            return 1
    except KeyboardInterrupt:
        print(f"\n⚠️  Test interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
