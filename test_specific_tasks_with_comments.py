#!/usr/bin/env python3
"""
Тестирование конкретных Jira задач с комментариями и разными статусами
OPENBD-1375 (комментарий, "Готово к проверке") и OPENBD-1224 ("Выполнено")
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

async def test_specific_tasks():
    """Проверка конкретных задач с комментариями"""
    print("🔍 Тестирование конкретных Jira задач с комментариями")
    print("=" * 60)
    
    try:
        # Создаем Jira клиент
        jira_client = JiraClient()
        
        # Тестируем подключение
        if not await jira_client.test_connection():
            print("❌ Не удалось подключиться к Jira API")
            return
        
        print("✅ Подключение к Jira успешно")
        
        # Список конкретных задач для проверки
        task_keys = ['OPENBD-1375', 'OPENBD-1224']
        
        for task_key in task_keys:
            print(f"\n🔍 Анализ задачи: {task_key}")
            print("-" * 40)
            
            # Получаем задачу по ключу
            jql = f'key = "{task_key}"'
            tasks = await jira_client.search_issues(
                jql=jql,
                fields=['summary', 'comment', 'assignee', 'status', 'updated', 'created', 'description', 'priority'],
                max_results=1
            )
            
            if not tasks:
                print(f"❌ Задача {task_key} не найдена")
                continue
            
            task = tasks[0]
            await analyze_task_detailed(task, task_key)
        
        # Дополнительно ищем другие задачи с комментариями
        print(f"\n🔍 Поиск других задач с комментариями...")
        jql_with_comments = 'project = "OPENBD" AND comment is not EMPTY ORDER BY updated DESC'
        tasks_with_comments = await jira_client.search_issues(
            jql=jql_with_comments,
            fields=['summary', 'comment', 'assignee', 'status', 'updated'],
            max_results=5
        )
        
        if tasks_with_comments:
            print(f"✅ Найдено {len(tasks_with_comments)} задач с комментариями")
            for i, task in enumerate(tasks_with_comments[:3], 1):
                print(f"\n📋 Задача #{i}: {task.get('key')}")
                fields = task.get('fields', {})
                print(f"   Статус: {fields.get('status', {}).get('name', 'N/A')}")
                print(f"   Назначена: {fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned'}")
                
                # Проверяем комментарии
                comment_field = fields.get('comment', {})
                if isinstance(comment_field, dict):
                    comments = comment_field.get('comments', [])
                    print(f"   Комментарии: {len(comments)}")
                    if comments:
                        for j, comment in enumerate(comments[:2], 1):
                            author = comment.get('author', {}).get('displayName', 'Unknown') if comment.get('author') else 'Unknown'
                            body = comment.get('body', '')[:100].replace('\n', ' ') + '...' if len(comment.get('body', '')) > 100 else comment.get('body', '')
                            print(f"     {j}. {author}: {body}")
        else:
            print("❌ Других задач с комментариями не найдено")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

async def analyze_task_detailed(task, task_key):
    """Детальный анализ конкретной задачи"""
    fields = task.get('fields', {})
    
    # Базовая информация
    print(f"📝 Название: {fields.get('summary', 'N/A')}")
    print(f"👤 Исполнитель: {fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned'}")
    print(f"📊 Статус: {fields.get('status', {}).get('name', 'N/A')}")
    print(f"🔥 Приоритет: {fields.get('priority', {}).get('name', 'N/A')}")
    print(f"📅 Создана: {fields.get('created', 'N/A')}")
    print(f"📅 Обновлена: {fields.get('updated', 'N/A')}")
    
    # Описание
    description = fields.get('description', '')
    if description:
        desc_preview = description[:200].replace('\n', ' ') + '...' if len(description) > 200 else description
        print(f"📄 Описание: {desc_preview}")
    else:
        print(f"📄 Описание: отсутствует")
    
    # Анализ комментариев
    print(f"\n💬 Анализ комментариев:")
    comment_field = fields.get('comment', {})
    
    if isinstance(comment_field, dict):
        comments = comment_field.get('comments', [])
        print(f"   Всего комментариев: {len(comments)}")
        
        if comments:
            print(f"   💬 Комментарии детально:")
            for i, comment in enumerate(comments, 1):
                author_info = comment.get('author', {})
                author = author_info.get('displayName', 'Unknown') if author_info else 'Unknown'
                body = comment.get('body', '')
                created = comment.get('created', 'N/A')
                updated = comment.get('updated', 'N/A')
                
                print(f"   --- Комментарий #{i} ---")
                print(f"   Автор: {author}")
                print(f"   Создан: {created}")
                print(f"   Обновлен: {updated}")
                
                if body:
                    # Очищаем и форматируем текст комментария
                    clean_body = body.replace('\r\n', '\n').replace('\n', ' | ')
                    body_preview = clean_body[:300] + '...' if len(clean_body) > 300 else clean_body
                    print(f"   Текст: {body_preview}")
                else:
                    print(f"   Текст: [пустой]")
                print()
        else:
            print("   ❌ Комментарии отсутствуют")
    else:
        print(f"   ❌ Поле комментариев имеет unexpected формат: {type(comment_field)}")
        print(f"   Значение: {str(comment_field)[:200]}...")
    
    # Проверяем структуру всех полей
    print(f"\n🔍 Структура полей задачи:")
    for key, value in fields.items():
        if 'comment' in key.lower():
            print(f"   {key}: {type(value)}")

async def main():
    await test_specific_tasks()

if __name__ == "__main__":
    asyncio.run(main())
