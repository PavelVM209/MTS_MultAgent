#!/usr/bin/env python3
"""
Отладка проблемы с фильтром задач OPENBD-1375 и OPENBD-1224
"""

import asyncio
import sys
import logging
from dotenv import load_dotenv
sys.path.append('src')

from core.jira_client import JiraClient

# Загружаем environment variables
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_task_filter():
    """Отладка проблемы с фильтром задач"""
    print("🔍 Отладка фильтра задач OPENBD-1375 и OPENBD-1224")
    print("=" * 60)
    
    try:
        # Создаем Jira клиент
        jira_client = JiraClient()
        
        # Тестируем подключение
        if not await jira_client.test_connection():
            print("❌ Не удалось подключиться к Jira API")
            return
        
        print("✅ Подключение к Jira успешно")
        
        # 1. Проверяем конкретные задачи
        task_keys = ['OPENBD-1375', 'OPENBD-1224']
        
        print(f"\n🔍 Шаг 1: Проверка конкретных задач")
        for task_key in task_keys:
            jql = f'key = "{task_key}"'
            tasks = await jira_client.search_issues(
                jql=jql,
                fields=['summary', 'status', 'updated', 'comment', 'assignee'],
                max_results=1
            )
            
            if tasks:
                task = tasks[0]
                fields = task.get('fields', {})
                print(f"✅ {task_key}:")
                print(f"   Статус: {fields.get('status', {}).get('name', 'N/A')}")
                print(f"   Обновлена: {fields.get('updated', 'N/A')}")
                print(f"   Комментариев: {len(fields.get('comment', {}).get('comments', []))}")
            else:
                print(f"❌ {task_key}: не найдена")
        
        # 2. Проверяем текущий JQL запрос
        current_jql = 'project = "OPENBD" AND status IN ("In Progress", "Done", "To Do", "Готово к тестированию", "Закрыт", "Выполнено", "Готово к проверке") AND updated >= -90d'
        print(f"\n🔍 Шаг 2: Текущий JQL запрос")
        print(f"JQL: {current_jql}")
        
        current_tasks = await jira_client.search_issues(
            jql=current_jql,
            fields=['key', 'status', 'updated', 'summary'],
            max_results=50
        )
        
        print(f"Найдено задач: {len(current_tasks)}")
        
        # Ищем наши задачи в результатах
        found_keys = [task.get('key') for task in current_tasks]
        for task_key in task_keys:
            if task_key in found_keys:
                print(f"✅ {task_key} найдена в текущем фильтре")
            else:
                print(f"❌ {task_key} НЕ найдена в текущем фильтре")
        
        # 3. Проверяем разные варианты JQL
        print(f"\n🔍 Шаг 3: Тестирование разных JQL вариантов")
        
        jql_variants = [
            'project = "OPENBD" AND updated >= -90d',  # Без фильтра статусов
            'project = "OPENBD" AND key IN ("OPENBD-1375", "OPENBD-1224")',  # Только наши задачи
            'project = "OPENBD" AND status = "Готово к тестированию"',  # Только статус OPENBD-1375
            'project = "OPENBD" AND status = "Закрыт"',  # Только статус OPENBD-1224
        ]
        
        for i, jql in enumerate(jql_variants, 1):
            print(f"\n   Вариант {i}: {jql}")
            try:
                tasks = await jira_client.search_issues(
                    jql=jql,
                    fields=['key', 'status', 'updated', 'summary'],
                    max_results=10
                )
                print(f"      Найдено: {len(tasks)} задач")
                for task in tasks:
                    fields = task.get('fields', {})
                    print(f"      - {task.get('key')}: {fields.get('status', {}).get('name', 'N/A')} ({fields.get('updated', 'N/A')})")
            except Exception as e:
                print(f"      Ошибка: {e}")
        
        # 4. Проверяем все возможные статусы в проекте
        print(f"\n🔍 Шаг 4: Все статусы в проекте OPENBD")
        
        try:
            # Ищем задачи с разными статусами
            all_tasks_jql = 'project = "OPENBD" ORDER BY updated DESC'
            all_tasks = await jira_client.search_issues(
                jql=all_tasks_jql,
                fields=['key', 'status', 'updated'],
                max_results=20
            )
            
            statuses = set()
            for task in all_tasks:
                status_name = task.get('fields', {}).get('status', {}).get('name', 'Unknown')
                statuses.add(status_name)
            
            print(f"Все найденные статусы: {sorted(statuses)}")
            
            # Проверяем наши задачи
            print(f"\nПоследние 20 задач:")
            for task in all_tasks:
                fields = task.get('fields', {})
                key = task.get('key')
                status = fields.get('status', {}).get('name', 'Unknown')
                updated = fields.get('updated', 'N/A')
                
                if key in task_keys:
                    print(f"   🎯 {key}: {status} ({updated})")
                else:
                    print(f"   - {key}: {status} ({updated})")
                    
        except Exception as e:
            print(f"Ошибка при получении всех статусов: {e}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

async def main():
    await debug_task_filter()

if __name__ == "__main__":
    asyncio.run(main())
