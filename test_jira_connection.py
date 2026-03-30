#!/usr/bin/env python3
"""
Простой тест подключения к Jira API с новым токеном
"""

import asyncio
import sys
import os
sys.path.append('src')

from core.jira_client import JiraClient

async def test_jira_connection():
    """Тест подключения к Jira API"""
    print("🔧 Тест подключения к Jira API...")
    print(f"URL: https://jira.mts.ru")
    print(f"Username: sa0000openbdrnd")
    print(f"Token: NDg0NDQ2ODIwNzA0O... (скрыт)")
    
    # Явно передаем конфигурацию
    config = {
        'base_url': 'https://jira.mts.ru',
        'username': 'sa0000openbdrnd',
        'api_token': 'REDACTED',
        'project_key': 'TEST'
    }
    
    print(f"\n📋 Конфигурация:")
    print(f"  Base URL: {config['base_url']}")
    print(f"  Username: {config['username']}")
    print(f"  Token configured: {'Yes' if config['api_token'] else 'No'}")
    
    # Создаем клиент с конфигурацией
    jira_client = JiraClient(config)
    
    # Тестируем подключение
    print("\n� Тестирование базового подключения...")
    connection_result = await jira_client.test_connection()
    
    if connection_result:
        print("✅ Подключение к Jira API успешно!")
        
        # Тестируем поиск задач
        print("\n🔄 Тестирование поиска задач...")
        tasks = await jira_client.search_issues(
            jql="project = TEST ORDER BY updated DESC",
            fields=['key', 'summary', 'status', 'assignee'],
            max_results=5
        )
        
        if tasks:
            print(f"✅ Найдено {len(tasks)} задач:")
            for task in tasks:
                fields = task.get('fields', {})
                key = task.get('key', 'N/A')
                summary = fields.get('summary', 'N/A')
                status = fields.get('status', {}).get('name', 'N/A')
                assignee = fields.get('assignee', {}).get('displayName', 'Unassigned')
                
                print(f"  📋 {key}: {summary}")
                print(f"     👤 {assignee} | 📊 {status}")
        else:
            print("⚠️ Задачи не найдены, но подключение работает")
        
        return True
    else:
        print("❌ Ошибка подключения к Jira API")
        return False

async def main():
    """Главная функция"""
    print("🧪 Тест Jira API с новым токеном")
    print("=" * 50)
    
    try:
        success = await test_jira_connection()
        
        if success:
            print("\n🎉 Jira API работает корректно!")
            print("Система готова к анализу задач!")
        else:
            print("\n💥 Jira API недоступен")
            print("Проверьте токен и права доступа")
            
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
