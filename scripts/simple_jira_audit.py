#!/usr/bin/env python3
"""
Simple Jira Audit Script
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
project_root = Path('.').absolute()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from dotenv import load_dotenv
load_dotenv()

from src.core.jira_client import JiraClient

async def simple_jira_audit():
    print('🚀 ЗАПУСК ПРОСТОГО АУДИТА JIRA')
    print('=' * 60)
    
    jira_client = JiraClient()
    
    # Тест подключения
    print('📡 Тестирование подключения к Jira...')
    connection_ok = await jira_client.test_connection()
    
    if not connection_ok:
        print('❌ Подключение к Jira не удалось!')
        return False
    
    print('✅ Подключение к Jira успешно')
    
    # Получение задач за последние 7 дней
    print('\n📊 Получение задач за последние 7 дней...')
    try:
        tasks_7d = await jira_client.search_issues(
            jql='project = "OPENBD" AND updated >= -7d ORDER BY updated DESC',
            fields=['summary', 'status', 'assignee', 'created', 'updated', 'priority', 'project'],
            max_results=100
        )
        print(f'✅ Получено {len(tasks_7d) if tasks_7d else 0} задач за 7 дней')
    except Exception as e:
        print(f'❌ Ошибка получения задач за 7 дней: {e}')
        tasks_7d = []
    
    # Получение задач за последние 30 дней
    print('\n📊 Получение задач за последние 30 дней...')
    try:
        tasks_30d = await jira_client.search_issues(
            jql='project = "OPENBD" AND updated >= -30d ORDER BY updated DESC',
            fields=['summary', 'status', 'assignee', 'created', 'updated', 'priority', 'project'],
            max_results=500
        )
        print(f'✅ Получено {len(tasks_30d) if tasks_30d else 0} задач за 30 дней')
    except Exception as e:
        print(f'❌ Ошибка получения задач за 30 дней: {e}')
        tasks_30d = []
    
    # Получение всех доступных задач
    print('\n📊 Получение всех доступных задач...')
    try:
        all_tasks = await jira_client.search_issues(
            jql='project = "OPENBD" ORDER BY updated DESC',
            fields=['summary', 'status', 'assignee', 'created', 'updated', 'priority', 'project'],
            max_results=1000
        )
        print(f'✅ Получено {len(all_tasks) if all_tasks else 0} задач всего')
    except Exception as e:
        print(f'❌ Ошибка получения всех задач: {e}')
        all_tasks = []
    
    # Анализ данных
    status_counts = {}
    assignee_counts = {}
    
    if all_tasks:
        print('\n📈 Анализ данных...')
        
        for task in all_tasks:
            fields = task.get('fields', {})
            
            # Статус
            status = fields.get('status', {}).get('name', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Исполнитель
            assignee = fields.get('assignee')
            if assignee and isinstance(assignee, dict):
                assignee_name = assignee.get('displayName') or assignee.get('name', 'Unknown')
            else:
                assignee_name = 'Unassigned'
            
            assignee_counts[assignee_name] = assignee_counts.get(assignee_name, 0) + 1
        
        print(f'\n👥 Уникальные сотрудники: {len(assignee_counts)}')
        print('\n📊 Топ 10 сотрудников по количеству задач:')
        for assignee, count in sorted(assignee_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f'  • {assignee}: {count} задач')
        
        print('\n📊 Распределение по статусам:')
        for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
            print(f'  • {status}: {count} задач')
    
    # Тест производительности API
    print('\n⚡ Тест производительности API...')
    try:
        start_time = datetime.now()
        test_tasks = await jira_client.search_issues(
            jql='project = "OPENBD" ORDER BY updated DESC',
            fields=['key', 'summary'],
            max_results=50
        )
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        print(f'✅ API отзывчивость: {response_time:.2f} секунд для 50 задач')
    except Exception as e:
        print(f'❌ Ошибка теста производительности: {e}')
        response_time = 0
    
    # Сохранение результатов
    results = {
        'audit_date': datetime.now().isoformat(),
        'connection_status': connection_ok,
        'tasks_7d': len(tasks_7d) if tasks_7d else 0,
        'tasks_30d': len(tasks_30d) if tasks_30d else 0,
        'total_tasks': len(all_tasks) if all_tasks else 0,
        'unique_employees': len(assignee_counts) if all_tasks else 0,
        'status_distribution': status_counts if all_tasks else {},
        'employee_task_counts': assignee_counts if all_tasks else {},
        'api_response_time': response_time
    }
    
    # Создание директории reports
    reports_dir = Path('reports')
    reports_dir.mkdir(exist_ok=True)
    
    # Сохранение результатов
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = reports_dir / f'jira_audit_{timestamp}.json'
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f'\n📄 Результаты сохранены в: {report_file}')
    
    # Итоговая оценка
    print('\n🎯 ИТОГОВАЯ ОЦЕНКА ИНТЕГРАЦИИ JIRA:')
    
    if connection_ok and results['total_tasks'] > 0:
        if results['unique_employees'] >= 10 and response_time < 10:
            print('✅ JIRA ИНТЕГРАЦИЯ ГОТОВА К ПРОИЗВОДСТВУ')
        elif results['unique_employees'] >= 5:
            print('⚠️ JIRA ИНТЕГРАЦИЯ ТРЕБУЕТ ВНИМАНИЯ')
        else:
            print('❌ JIRA ИНТЕГРАЦИЯ НЕ ГОТОВА (мало данных)')
    else:
        print('❌ JIRA ИНТЕГРАЦИЯ НЕ ГОТОВА')
    
    return True

if __name__ == '__main__':
    asyncio.run(simple_jira_audit())
