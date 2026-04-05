#!/usr/bin/env python3
"""
Проверка проекта OPENBD (ID: 36300) и конкретной задачи OPENBD-1225
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_openbd_task():
    """Проверка конкретной задачи OPENBD-1225"""
    print("🔍 Проверка задачи OPENBD-1225...")
    
    headers = {
        'Authorization': f'Bearer {os.getenv("JIRA_ACCESS_TOKEN")}',
        'Content-Type': 'application/json'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # Пробуем найти конкретную задачу OPENBD-1225
        url = 'https://jira.mts.ru/rest/api/2/issue/OPENBD-1225'
        print(f"   📡 Запрос: {url}")
        
        async with session.get(url) as response:
            print(f"   📊 Статус: {response.status}")
            
            if response.status == 200:
                issue_data = await response.json()
                fields = issue_data.get('fields', {})
                
                print(f"   ✅ Задача найдена!")
                print(f"   🆔 Ключ: {issue_data.get('key')}")
                print(f"   📝 Название: {fields.get('summary', 'N/A')}")
                print(f"   📊 Статус: {fields.get('status', {}).get('name', 'Unknown')}")
                print(f"   🏗️  Проект: {fields.get('project', {}).get('name', 'Unknown')}")
                print(f"   👤 Исполнитель: {fields.get('assignee', {}).get('displayName', 'Unassigned')}")
                print(f"   📅 Создана: {fields.get('created', 'N/A')}")
                print(f"   🔄 Обновлена: {fields.get('updated', 'N/A')}")
                return True
            else:
                error_text = await response.text()
                print(f"   ❌ Ошибка: {error_text}")
                return False

async def test_openbd_tasks():
    """Поиск задач в проекте OPENBD"""
    print("\n📊 Поиск задач в проекте OPENBD...")
    
    headers = {
        'Authorization': f'Bearer {os.getenv("JIRA_ACCESS_TOKEN")}',
        'Content-Type': 'application/json'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # Ищем задачи в проекте OPENBD
        url = 'https://jira.mts.ru/rest/api/2/search'
        params = {
            'jql': 'project = OPENBD ORDER BY updated DESC',
            'maxResults': 10
        }
        print(f"   📡 Запрос: {url}")
        print(f"   🔧 JQL: {params['jql']}")
        
        async with session.get(url, params=params) as response:
            print(f"   📊 Статус: {response.status}")
            
            if response.status == 200:
                data = await response.json()
                issues = data.get('issues', [])
                total = data.get('total', 0)
                
                print(f"   ✅ Найдено задач: {total} (показано {len(issues)})")
                
                if issues:
                    print(f"   📋 Последние задачи:")
                    for i, issue in enumerate(issues):
                        fields = issue.get('fields', {})
                        key = issue.get('key')
                        summary = fields.get('summary', 'No summary')
                        status = fields.get('status', {}).get('name', 'Unknown')
                        assignee = fields.get('assignee', {}).get('displayName', 'Unassigned')
                        
                        print(f"      {i+1}. {key}: {summary[:60]}...")
                        print(f"         Статус: {status}, Исполнитель: {assignee}")
                
                return issues
            else:
                error_text = await response.text()
                print(f"   ❌ Ошибка поиска: {error_text}")
                return []

async def test_openbd_project_info():
    """Информация о проекте OPENBD"""
    print("\n🏗️  Информация о проекте OPENBD...")
    
    headers = {
        'Authorization': f'Bearer {os.getenv("JIRA_ACCESS_TOKEN")}',
        'Content-Type': 'application/json'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # Получаем информацию о проекте
        url = 'https://jira.mts.ru/rest/api/2/project/OPENBD'
        print(f"   📡 Запрос: {url}")
        
        async with session.get(url) as response:
            print(f"   📊 Статус: {response.status}")
            
            if response.status == 200:
                project_data = await response.json()
                
                print(f"   ✅ Проект найден!")
                print(f"   🆔 ID: {project_data.get('id')}")
                print(f"   🔑 Key: {project_data.get('key')}")
                print(f"   📝 Название: {project_data.get('name')}")
                print(f"   📋 Описание: {(project_data.get('description') or 'N/A')[:100]}...")
                print(f"   👤 Лид проекта: {project_data.get('lead', {}).get('displayName', 'N/A')}")
                print(f"   📊 Категория: {project_data.get('projectCategory', {}).get('name', 'N/A')}")
                print(f"   🔗 URL: {project_data.get('self', 'N/A')}")
                return True
            else:
                error_text = await response.text()
                print(f"   ❌ Ошибка: {error_text}")
                return False

async def test_multiple_openbd_tasks():
    """Проверка нескольких конкретных задач OPENBD"""
    print("\n🎯 Проверка конкретных задач OPENBD...")
    
    test_tasks = ['OPENBD-1225', 'OPENBD-1', 'OPENBD-100', 'OPENBD-500']
    
    headers = {
        'Authorization': f'Bearer {os.getenv("JIRA_ACCESS_TOKEN")}',
        'Content-Type': 'application/json'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        for task_key in test_tasks:
            url = f'https://jira.mts.ru/rest/api/2/issue/{task_key}'
            
            async with session.get(url) as response:
                if response.status == 200:
                    issue_data = await response.json()
                    fields = issue_data.get('fields', {})
                    summary = fields.get('summary', 'No summary')
                    status = fields.get('status', {}).get('name', 'Unknown')
                    
                    print(f"   ✅ {task_key}: {summary[:40]}... (Статус: {status})")
                else:
                    print(f"   ❌ {task_key}: Не найдена (Статус: {response.status})")

async def main():
    """Main execution"""
    print("🎯 ПРОВЕРКА ПРОЕКТА OPENBD (ID: 36300)")
    print("="*60)
    print("Проверка гипотезы о существовании проекта OPENBD с ID 36300")
    print("="*60)
    
    # Проверяем информацию о проекте
    project_ok = await test_openbd_project_info()
    
    # Проверяем конкретную задачу
    task_ok = await test_openbd_task()
    
    # Ищем все задачи проекта
    tasks = await test_openbd_tasks()
    
    # Проверяем несколько задач
    await test_multiple_openbd_tasks()
    
    print("\n" + "="*60)
    print("📊 ИТОГИ ПРОВЕРКИ OPENBD")
    print("="*60)
    
    print(f"• Проект OPENBD найден: {'✅ Да' if project_ok else '❌ Нет'}")
    print(f"• Задача OPENBD-1225 найдена: {'✅ Да' if task_ok else '❌ Нет'}")
    print(f"• Всего задач в проекте: {len(tasks) if tasks else 0}")
    
    if project_ok and (task_ok or tasks):
        print("\n🎉 ПРОЕКТ OPENBD РАБОТАЕТ!")
        print("💡 Можно использовать для Employee Monitoring System")
        print("🔧 Нужно обновить JIRA_PROJECT_KEYS в .env на OPENBD")
    else:
        print("\n❌ Проблемы с проектом OPENBD")
        print("💡 Возможно, проект не доступен или нет прав доступа")

if __name__ == "__main__":
    asyncio.run(main())
