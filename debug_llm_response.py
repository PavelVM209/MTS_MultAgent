#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug LLM Response
Проверяем что именно возвращает LLM
"""

import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
def load_env():
    """Загрузка .env файла"""
    try:
        from dotenv import load_dotenv
        env_path = Path('.env')
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(".env файл загружен")
        else:
            logger.warning(".env файл не найден")
    except ImportError:
        logger.info("dotenv не установлен, пропускаем загрузку .env")
    except Exception as e:
        logger.error(f"Ошибка загрузки .env: {e}")
        
load_env()

async def main():
    """Основная функция"""
    try:
        logger.info("=== ОТЛАДКА LLM RESPONSE ===")
        
        # Импортируем необходимые модули
        import sys
        sys.path.append('./src')
        
        from agents.task_analyzer_agent import TaskAnalyzerAgent
        from core.jira_client import JiraClient
        
        # 1. Создаем Task Analyzer
        agent = TaskAnalyzerAgent()
        
        # 2. Получаем задачи из Jira
        logger.info("Получаем задачи из Jira...")
        jira_client = JiraClient()
        tasks = await agent.fetch_jira_tasks()
        
        if not tasks:
            logger.error("Задачи не получены")
            return
            
        # 3. Группируем по сотрудникам
        employee_tasks = await agent._group_tasks_by_employee(tasks)
        
        # 4. Отправляем в LLM и получаем RAW ответ
        logger.info("Отправляем в LLM...")
        llm_analysis = await agent._analyze_tasks_with_llm(tasks, employee_tasks)
        
        if llm_analysis:
            logger.info("=== LLM RESPONSE RECEIVED ===")
            logger.info(f"Type: {type(llm_analysis)}")
            logger.info(f"Keys: {list(llm_analysis.keys()) if isinstance(llm_analysis, dict) else 'Not a dict'}")
            
            # Сохраняем полный LLM response
            with open('debug_llm_raw_response.json', 'w', encoding='utf-8') as f:
                json.dump(llm_analysis, f, indent=2, ensure_ascii=False)
            logger.info("Полный LLM ответ сохранен в debug_llm_raw_response.json")
            
            # Анализируем структуру
            if isinstance(llm_analysis, dict):
                logger.info("\n=== АНАЛИЗ СТРУКТУРЫ LLM RESPONSE ===")
                
                # Проверяем employee_analysis
                if 'employee_analysis' in llm_analysis:
                    logger.info(f"✅ employee_analysis найден: {len(llm_analysis['employee_analysis'])} сотрудников")
                    for emp_name, emp_data in llm_analysis['employee_analysis'].items():
                        logger.info(f"  - {emp_name}: {list(emp_data.keys())}")
                else:
                    logger.error("❌ employee_analysis НЕ найден в LLM ответе")
                
                # Проверяем team_insights
                if 'team_insights' in llm_analysis:
                    insights = llm_analysis['team_insights']
                    logger.info(f"✅ team_insights найден: {len(insights)} инсайтов")
                    for i, insight in enumerate(insights, 1):
                        logger.info(f"  Инсайт {i}: {insight}")
                else:
                    logger.error("❌ team_insights НЕ найден в LLM ответе")
                
                # Проверяем recommendations
                if 'recommendations' in llm_analysis:
                    recs = llm_analysis['recommendations']
                    logger.info(f"✅ recommendations найден: {len(recs)} рекомендаций")
                    for i, rec in enumerate(recs, 1):
                        logger.info(f"  Рекомендация {i}: {rec}")
                else:
                    logger.error("❌ recommendations НЕ найден в LLM ответе")
                
                # Показываем первую часть ответа
                logger.info("\n=== ПЕРВЫЕ 500 СИМВОЛОВ LLM RESPONSE ===")
                response_str = json.dumps(llm_analysis, ensure_ascii=False, indent=2)
                logger.info(response_str[:500])
                
            else:
                logger.error(f"LLM вернул не dict: {type(llm_analysis)}")
                logger.info(f"Content: {str(llm_analysis)[:500]}")
                
        else:
            logger.error("LLM вернул None")
            
        logger.info("=== ОТЛАДКА ЗАВЕРШЕНА ===")
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 ЗАПУСК ОТЛАДКИ LLM RESPONSE")
    print("=" * 60)
    asyncio.run(main())
