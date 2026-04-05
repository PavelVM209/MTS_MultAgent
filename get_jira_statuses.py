#!/usr/bin/env python3
"""
Скрипт для получения всех статусов проекта OPENBD
"""
import asyncio
import json
import sys
import os
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.jira_client import JiraClient

async def get_status_ids():
    """Получаем все уникальные статусы проекта OPENBD"""
    print("🔍 Получение статусов проекта OPENBD...")
    
    jira = JiraClient()
    await jira.test_connection()
    
    # Получаем все статусы проекта OPENBD
    tasks = await jira.search_issues('project = "OPENBD" ORDER BY updated DESC', ['status'], 100)
    
    print(f"📊 Получено {len(tasks)} задач")
    
    # Уникальные статусы
    unique_statuses = {}
    for task in tasks:
        status = task.get('fields', {}).get('status', {})
        status_name = status.get('name', '')
        status_id = status.get('id', '') if isinstance(status, dict) else ''
        
        if status_name and status_name not in unique_statuses:
            unique_statuses[status_name] = {
                'name': status_name,
                'id': status_id,
                'count': 1
            }
        elif status_name in unique_statuses:
            unique_statuses[status_name]['count'] += 1
    
    print("\n🎯 Все статусы в проекте OPENBD:")
    for name, info in unique_statuses.items():
        print(f"  {name} (ID: {info['id']}) - {info['count']} задач")
    
    # Создаем JQL с ID статусов
    status_ids = [info['id'] for info in unique_statuses.values() if info['id']]
    if status_ids:
        jql_with_ids = f'project = "OPENBD" AND status IN ({", ".join(status_ids)}) AND updated >= -90d'
        print(f"\n📝 JQL с ID статусов:\n{jql_with_ids}")
    
    # Сохраняем в файл
    with open('jira_statuses.json', 'w', encoding='utf-8') as f:
        json.dump(unique_statuses, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Статусы сохранены в jira_statuses.json")
    return unique_statuses

if __name__ == "__main__":
    asyncio.run(get_status_ids())
