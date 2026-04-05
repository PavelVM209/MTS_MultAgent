#!/usr/bin/env python3
"""
Тестирование Task Analyzer Agent с реальными данными MTS Jira
"""

import asyncio
import sys
import os
import logging
from dotenv import load_dotenv
sys.path.append('src')

from agents.task_analyzer_agent import TaskAnalyzerAgent
from core.config_manager import ConfigurationManager
from core.base_agent import AgentConfig

# Загружаем environment variables из .env файла
load_dotenv()

# Настройка детального логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_task_analyzer():
    """Тестирование Task Analyzer с реальными данными"""
    print("🔧 Тестирование Task Analyzer Agent...")
    
    try:
        # Загружаем конфигурацию
        config_manager = ConfigurationManager()
        config = await config_manager.load_config()
        
        print(f"📋 Конфигурация загружена:")
        print(f"  Jira project keys: {config.get('employee_monitoring', {}).get('jira', {}).get('project_keys', 'N/A')}")
        print(f"  Query filter: {config.get('employee_monitoring', {}).get('jira', {}).get('query_filter', 'N/A')}")
        
        # Создаем правильный AgentConfig объект
        agent_config = AgentConfig(
            name="TaskAnalyzerAgent",
            description="Analyzes JIRA tasks for employee performance monitoring - TEST",
            version="1.0.0"
        )
        
        # Создаем агент
        agent = TaskAnalyzerAgent(agent_config)
        
        print("\n🔄 Тестирование выполнения Task Analyzer...")
        
        # Выполняем агент
        result = await agent.execute({"mode": "test"})
        
        print(f"\n📊 Результат выполнения:")
        print(f"  Success: {result.success}")
        print(f"  Message: {result.message}")
        
        if result.success:
            data = result.data
            print(f"\n📈 Анализ данных:")
            print(f"  Analysis date: {data.analysis_date}")
            print(f"  Total tasks: {data.total_tasks_analyzed}")
            print(f"  Employees analyzed: {data.total_employees}")
            
            # Показываем детали по сотрудникам
            employees = data.employees_progress
            if employees:
                print(f"\n👥 Детали по сотрудникам (первые 5):")
                for i, (employee_name, employee_data) in enumerate(list(employees.items())[:5], 1):
                    print(f"  {i}. {employee_name}:")
                    print(f"     Total tasks: {employee_data.total_tasks}")
                    print(f"     Completed: {employee_data.completed_tasks}")
                    print(f"     In progress: {employee_data.in_progress_tasks}")
                    print(f"     Productivity score: {employee_data.productivity_score:.2f}")
                    print(f"     Performance rating: {employee_data.performance_rating:.2f}")
            
            # Показываем team insights
            team_insights = data.team_insights
            if team_insights:
                print(f"\n💡 Team Insights ({len(team_insights)}):")
                for i, insight in enumerate(team_insights[:3], 1):
                    print(f"  {i}. {insight}")
            
            # Показываем team recommendations
            recommendations = data.recommendations
            if recommendations:
                print(f"\n📋 Team Recommendations ({len(recommendations)}):")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"  {i}. {rec}")
            
            # Проверяем качество анализа
            quality_score = data.quality_score
            print(f"\n📊 Качество анализа: {quality_score:.2f}")
            
            if quality_score >= 0.8:
                print("✅ Качество анализа отличное!")
            elif quality_score >= 0.6:
                print("⚠️ Качество анализа приемлемое")
            else:
                print("❌ Качество анализа низкое")
            
            return True
            
        else:
            print(f"❌ Task Analyzer завершился с ошибкой:")
            print(f"  Errors: {result.errors}")
            
            # Анализируем ошибки
            if result.errors:
                print(f"\n🔍 Анализ ошибок:")
                for i, error in enumerate(result.errors, 1):
                    print(f"  {i}. {error}")
            
            return False
            
    except Exception as e:
        print(f"❌ Исключение при выполнении Task Analyzer: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_individual_components():
    """Тестирование отдельных компонентов Task Analyzer"""
    print("\n🔍 Тестирование отдельных компонентов...")
    
    try:
        config_manager = ConfigurationManager()
        config = await config_manager.load_config()
        
        # Создаем правильный AgentConfig объект
        agent_config = AgentConfig(
            name="TaskAnalyzerAgent",
            description="Test instance for component testing",
            version="1.0.0"
        )
        agent = TaskAnalyzerAgent(agent_config)
        
        # Тестируем fetch_jira_tasks
        print("\n1. Тестирование fetch_jira_tasks...")
        tasks = await agent.fetch_jira_tasks()
        print(f"   Получено задач: {len(tasks)}")
        
        if tasks:
            # Показываем первую задачу для анализа структуры
            print(f"\n📋 Пример структуры задачи:")
            first_task = tasks[0]
            print(f"   Key: {first_task.get('key', 'N/A')}")
            fields = first_task.get('fields', {})
            print(f"   Summary: {fields.get('summary', 'N/A')[:50]}...")
            print(f"   Status: {fields.get('status', {}).get('name', 'N/A')}")
            print(f"   Assignee: {fields.get('assignee', {}).get('displayName', 'N/A')}")
            
        # Тестируем parse_jira_tasks
        print(f"\n2. Тестирование parse_jira_tasks...")
        parsed_tasks = await agent._parse_jira_tasks(tasks)
        print(f"   Распарсено задач: {len(parsed_tasks)}")
        
        if parsed_tasks:
            print(f"   Первая распарсенная задача:")
            first_parsed = parsed_tasks[0]
            print(f"     Key: {first_parsed.get('key', 'N/A')}")
            print(f"     Assignee: {first_parsed.get('assignee', 'N/A')}")
            print(f"     Status: {first_parsed.get('status', 'N/A')}")
        
        # Тестируем группировку по сотрудникам
        print(f"\n3. Тестирование группировки по сотрудникам...")
        employee_groups = await agent._group_tasks_by_employee(parsed_tasks)
        print(f"   Сотрудников найдено: {len(employee_groups)}")
        
        if employee_groups:
            print(f"   Топ-5 сотрудников по количеству задач:")
            sorted_employees = sorted(employee_groups.items(), key=lambda x: len(x[1]), reverse=True)
            for i, (employee, tasks) in enumerate(sorted_employees[:5], 1):
                print(f"     {i}. {employee}: {len(tasks)} задач")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестиров компонентов: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Главная функция"""
    print("🧪 Тестирование Task Analyzer Agent с реальными данными")
    print("=" * 60)
    
    try:
        # Сначала тестируем отдельные компоненты
        components_success = await test_individual_components()
        
        if components_success:
            print("\n" + "=" * 60)
            # Затем тестируем полный агент
            agent_success = await test_task_analyzer()
            
            if agent_success:
                print("\n🎉 Task Analyzer Agent работает корректно!")
                print("✅ Переходим к следующему агенту!")
            else:
                print("\n💥 Task Analyzer Agent требует исправлений!")
                print("❌ Необходимо исправить ошибки перед движением дальше")
        else:
            print("\n💥 Компоненты Task Analyzer требуют исправлений!")
            print("❌ Пропускаем полный тест до исправления компонентов")
            
    except Exception as e:
        print(f"\n💥 Критическая ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
