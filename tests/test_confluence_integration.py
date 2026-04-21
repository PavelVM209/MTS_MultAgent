#!/usr/bin/env python3
"""
Тестирование Confluence интеграции с Bearer токеном
"""

import asyncio
import logging
import os
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_confluence_integration():
    """Тестирование Confluence API с Bearer токеном."""
    try:
        logger.info("🔧 Тестирование Confluence API с Bearer токеном")
        
        # Загрузка конфигурации
        from dotenv import load_dotenv
        load_dotenv()
        
        confluence_url = os.getenv('CONFLUENCE_BASE_URL')
        confluence_token = os.getenv('CONFLUENCE_ACCESS_TOKEN')
        
        if not confluence_url or not confluence_token:
            logger.error("❌ Отсутствуют переменные окружения Confluence")
            return False
        
        logger.info(f"🌐 Confluence URL: {confluence_url}")
        logger.info(f"🔑 Token: {confluence_token[:10]}...")
        
        # Тест с curl
        import subprocess
        try:
            cmd = [
                'curl', '-H', f'Authorization: Bearer {confluence_token}',
                '-L', f'{confluence_url}/rest/api/content',
                '-s', '-w', '%{http_code}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                response_code = result.stdout[-3:]  # Последние 3 символа - HTTP код
                response_body = result.stdout[:-3]   # Все кроме HTTP кода
                
                if response_code == '200':
                    logger.info("✅ Confluence API доступен через curl")
                    logger.info(f"📄 Ответ: {response_body[:200]}...")
                    return True
                else:
                    logger.error(f"❌ HTTP код: {response_code}")
                    return False
            else:
                logger.error(f"❌ Ошибка curl: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения curl: {e}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования Confluence: {e}")
        return False

async def test_weekly_reports_confluence():
    """Тестирование WeeklyReportsAgent с Confluence."""
    try:
        logger.info("📊 Тестирование WeeklyReportsAgent с Confluence")
        
        from agents.weekly_reports_agent_complete import WeeklyReportsAgentComplete
        
        # Инициализация агента
        agent = WeeklyReportsAgentComplete()
        
        # Проверка конфигурации
        if not agent.confluence_url:
            logger.error("❌ Confluence URL не настроен")
            return False
        
        if not agent.confluence_api_token:
            logger.error("❌ Confluence API токен не настроен")
            return False
        
        logger.info(f"🌐 Confluence URL: {agent.confluence_url}")
        logger.info(f"🔑 Token настроен: {bool(agent.confluence_api_token)}")
        logger.info(f"📁 Space: {agent.confluence_space_key}")
        logger.info(f"📄 Parent Page: {agent.confluence_parent_page_id}")
        
        # Тест публикации тестового отчета
        test_report = {
            'week_number': 1,
            'period': {
                'start': '2026-03-23T00:00:00',
                'end': '2026-03-30T00:00:00'
            },
            'total_employees': 10,
            'total_tasks_completed': 50,
            'total_story_points': 100,
            'avg_performance_score': 8.5,
            'top_performers': ['Иван Петров', 'Мария Иванова'],
            'employees_needing_attention': ['Петр Сидоров'],
            'team_achievements': ['Завершили все задачи в срок'],
            'team_challenges': ['Нужно улучшить коммуникацию'],
            'team_recommendations': ['Регулярные встречи команды'],
            'employees_summaries': {}
        }
        
        logger.info("📤 Публикация тестового отчета в Confluence...")
        result = await agent.publish_to_confluence(test_report)
        
        if result.get('success'):
            logger.info("✅ Отчет успешно опубликован в Confluence")
            logger.info(f"🔗 URL: {result.get('url')}")
            logger.info(f"📄 Заголовок: {result.get('title')}")
            return True
        else:
            logger.error(f"❌ Ошибка публикации: {result.get('error')}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования WeeklyReportsAgent: {e}")
        return False

async def main():
    """Основная функция тестирования."""
    logger.info("🚀 Начало тестирования Confluence интеграции")
    
    # Тест 1: Базовое подключение к Confluence API
    logger.info("\n" + "="*60)
    logger.info("🧪 Тест 1: Confluence API подключение")
    logger.info("="*60)
    
    api_test = await test_confluence_integration()
    if api_test:
        logger.info("✅ Тест Confluence API пройден")
    else:
        logger.error("❌ Тест Confluence API не пройден")
    
    # Тест 2: WeeklyReportsAgent с Confluence
    logger.info("\n" + "="*60)
    logger.info("🧪 Тест 2: WeeklyReportsAgent с Confluence")
    logger.info("="*60)
    
    agent_test = await test_weekly_reports_confluence()
    if agent_test:
        logger.info("✅ Тест WeeklyReportsAgent с Confluence пройден")
    else:
        logger.error("❌ Тест WeeklyReportsAgent с Confluence не пройден")
    
    # Итоги
    logger.info("\n" + "="*60)
    logger.info("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ CONFLUENCE")
    logger.info("="*60)
    
    tests = [
        ("Confluence API", api_test),
        ("WeeklyReportsAgent", agent_test)
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ УСПЕХ" if result else "❌ НЕУДАЧА"
        logger.info(f"{test_name}: {status}")
    
    success_rate = (passed / total) * 100
    logger.info(f"\n📈 Всего тестов: {total}")
    logger.info(f"✅ Успешных: {passed}")
    logger.info(f"❌ Неудачных: {total - passed}")
    logger.info(f"📊 Успешность: {success_rate:.1f}%")
    
    if success_rate >= 50:
        logger.info("🎉 Confluence интеграция готова к использованию!")
    else:
        logger.warning("⚠️ Confluence интеграция требует доработки")
    
    return success_rate >= 50

if __name__ == "__main__":
    asyncio.run(main())
