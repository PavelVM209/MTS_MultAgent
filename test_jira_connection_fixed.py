#!/usr/bin/env python3
"""
Исправленный тест подключения к Jira API с реальными токенами из .env
"""

import asyncio
import sys
import os
import logging
from dotenv import load_dotenv
sys.path.append('src')

from core.jira_client import JiraClient

# Загружаем environment variables из .env файла
load_dotenv()

# Настройка детального логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Debug: проверяем что переменные окружения загружены
print(f"🔍 Debug environment variables:")
print(f"  JIRA_BASE_URL: {os.getenv('JIRA_BASE_URL', 'NOT FOUND')}")
print(f"  JIRA_USERNAME: {os.getenv('JIRA_USERNAME', 'NOT FOUND')}")
print(f"  JIRA_ACCESS_TOKEN: {'CONFIGURED' if os.getenv('JIRA_ACCESS_TOKEN') else 'NOT FOUND'}")
print(f"  JIRA_PROJECT_KEYS: {os.getenv('JIRA_PROJECT_KEYS', 'NOT FOUND')}")

async def test_jira_connection():
    """Тест подключения к Jira API с реальными данными"""
    print("🔧 Тест подключения к Jira API с реальными токенами...")
    
    # Клиент автоматически загрузит конфигурацию из .env
    jira_client = JiraClient()
    
    # Проверяем конфигурацию
    config = jira_client.get_config()
    print(f"\n📋 Загруженная конфигурация:")
    print(f"  Base URL: {config['base_url']}")
    print(f"  Username: {config['username']}")
    print(f"  Token configured: {config['configured']}")
    print(f"  Project key: {config['project_key']}")
    
    # Валидация конфигурации
    validation = jira_client.validate_config()
    print(f"\n✅ Валидация конфигурации:")
    print(f"  Status: {validation['status']}")
    if validation['errors']:
        print(f"  Errors: {validation['errors']}")
    if validation['warnings']:
        print(f"  Warnings: {validation['warnings']}")
    print(f"  Configured fields: {validation['configured_fields']}")
    
    if not validation['valid']:
        print("❌ Конфигурация невалидна!")
        return False
    
    # Тестируем подключение
    print("\n🔄 Тестирование базового подключения...")
    try:
        connection_result = await jira_client.test_connection()
        
        if connection_result:
            print("✅ Подключение к Jira API успешно!")
            
            # Тестируем поиск задач в проекте OPENBD
            print("\n🔍 Тестирование поиска задач в проекте OPENBD...")
            tasks = await jira_client.search_issues(
                jql='project = "OPENBD" ORDER BY updated DESC',
                fields=['key', 'summary', 'status', 'assignee', 'priority', 'created', 'updated'],
                max_results=10
            )
            
            if tasks:
                print(f"✅ Найдено {len(tasks)} задач:")
                for i, task in enumerate(tasks[:5], 1):  # Показываем первые 5
                    fields = task.get('fields', {})
                    key = task.get('key', 'N/A')
                    summary = fields.get('summary', 'N/A')
                    status = fields.get('status', {}).get('name', 'N/A')
                    assignee = fields.get('assignee', {}).get('displayName', 'Unassigned')
                    priority = fields.get('priority', {}).get('name', 'N/A')
                    
                    print(f"  📋 {i}. {key}: {summary[:60]}...")
                    print(f"     👤 {assignee} | 📊 {status} | 🎯 {priority}")
                
                # Анализируем сотрудников
                employees = set()
                for task in tasks:
                    fields = task.get('fields')
                    if not fields:
                        continue
                    assignee_data = fields.get('assignee')
                    if not assignee_data:
                        continue
                    assignee = assignee_data.get('displayName')
                    if assignee and assignee != 'Unassigned':
                        employees.add(assignee)
                
                print(f"\n👥 Найдено сотрудников: {len(employees)}")
                for emp in sorted(list(employees))[:10]:  # Показываем первых 10
                    print(f"  👤 {emp}")
                
                return True
            else:
                print("⚠️ Задачи не найдены, но подключение работает")
                return True
        else:
            print("❌ Ошибка подключения к Jira API")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при тестировании подключения: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await jira_client.close()

async def main():
    """Главная функция"""
    print("🧪 Исправленный тест Jira API с реальными токенами")
    print("=" * 60)
    
    try:
        success = await test_jira_connection()
        
        if success:
            print("\n🎉 Jira API работает корректно!")
            print("✅ Система готова к анализу задач!")
        else:
            print("\n💥 Jira API недоступен")
            print("❌ Проверьте токен и права доступа")
            
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
