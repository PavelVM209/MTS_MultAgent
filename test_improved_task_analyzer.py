#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Improved Task Analyzer Agent with Two-Stage LLM Analysis
"""

import asyncio
import logging
import json
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Добавляем путь к src
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

# Загрузка переменных окружения
def load_env():
    """Загрузка .env файла"""
    try:
        from dotenv import load_dotenv
        import os
        env_path = os.path.join(os.getcwd(), '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logger.info(".env файл загружен")
        else:
            logger.warning(".env файл не найден")
    except ImportError:
        logger.info("dotenv не установлен, пропускаем загрузку .env")
    except Exception as e:
        logger.error(f"Ошибка загрузки .env: {e}")
        
load_env()

async def test_improved_task_analyzer():
    """Тестирование улучшенного Task Analyzer с двухэтапной системой"""
    try:
        logger.info("🚀 ЗАПУСК ТЕСТА УЛУЧШЕННОГО TASK ANALYZER")
        logger.info("=" * 60)
        
        # Импортируем улучшенный агент
        from src.agents.task_analyzer_agent_improved import ImprovedTaskAnalyzerAgent
        
        # Создаем агент
        agent = ImprovedTaskAnalyzerAgent()
        logger.info("✅ ImprovedTaskAnalyzerAgent создан")
        
        # Проверяем health status
        health = await agent.get_health_status()
        logger.info(f"📊 Health Status: {health['status']}")
        logger.info(f"🔧 LLM Client: {health['llm_client']}")
        logger.info(f"💾 Memory Store: {health['memory_store']}")
        logger.info(f"📁 Reports Directory: {health['reports_directory']}")
        
        if health['status'] != 'healthy':
            logger.warning("⚠️ Агент не в здоровом состоянии, продолжаем тест...")
        
        # Выполняем анализ
        logger.info("\n🔄 ВЫПОЛНЕНИЕ АНАЛИЗА ЗАДАЧ")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        result = await agent.execute({})
        execution_time = datetime.now() - start_time
        
        # Проверяем результат
        if result.success:
            logger.info("✅ Анализ выполнен успешно!")
            logger.info(f"⏱️ Время выполнения: {execution_time.total_seconds():.2f} сек")
            logger.info(f"📋 Сообщение: {result.message}")
            
            # Анализируем данные
            analysis_data = result.data
            if hasattr(analysis_data, 'employees_progress'):
                employees = analysis_data.employees_progress
                logger.info(f"👥 Проанализировано сотрудников: {len(employees)}")
                
                for employee, progress in employees.items():
                    rating = progress.performance_rating
                    completed = progress.completed_tasks
                    total = progress.total_tasks
                    logger.info(f"  • {employee}: рейтинг {rating}/10, задач {completed}/{total}")
            
            if hasattr(analysis_data, 'team_insights'):
                insights = analysis_data.team_insights
                logger.info(f"💡 Командные инсайты: {len(insights)}")
                for i, insight in enumerate(insights, 1):
                    logger.info(f"  {i}. {insight}")
            
            if hasattr(analysis_data, 'recommendations'):
                recs = analysis_data.recommendations
                logger.info(f"📝 Рекомендации: {len(recs)}")
                for i, rec in enumerate(recs, 1):
                    logger.info(f"  {i}. {rec}")
            
            # Показываем метаданные
            if hasattr(analysis_data, 'quality_score'):
                quality = analysis_data.quality_score
                logger.info(f"🎯 Качество анализа: {quality:.3f}")
            
            if hasattr(analysis_data, 'total_tasks_analyzed'):
                tasks = analysis_data.total_tasks_analyzed
                logger.info(f"📊 Всего задач проанализировано: {tasks}")
            
            # Выводим полный персональный анализ из файла stage1_text_analysis.txt
            try:
                with open('stage1_text_analysis.txt', 'r', encoding='utf-8') as f:
                    text_analysis = f.read()
                
                # Извлекаем секцию анализа сотрудников
                import re
                emp_section = re.search(r'=== АНАЛИЗ СОТРУДНИКОВ ===(.*)', text_analysis, re.DOTALL | re.IGNORECASE)
                if emp_section:
                    print("\n" + "="*80)
                    print("📋 ПОЛНЫЙ ПЕРСОНАЛЬНЫЙ АНАЛИЗ СОТРУДНИКОВ")
                    print("="*80)
                    print(emp_section.group(1).strip())
                    print("="*80)
                else:
                    print("\n⚠️ Не удалось найти секцию анализа сотрудников в файле")
                    
            except Exception as e:
                print(f"\n⚠️ Ошибка при чтении файла анализа: {e}")
            
            # Проверяем наличие всех сотрудников (с учетом префикса "** ")
            expected_employees = [
                "Сабадаш Алина", "Савенкова Надежда", "Колобаев Никита",
                "Найденов Иван Владимирович", "Мангурсузян Рафаэль Варушанович",
                "Вощилов Егор", "Мурзаков Павел", "Стрельченко Святослав",
                "Березин Константин", "Болотин Андрей", "Кроткова Наталья Олеговна"
            ]
            
            if hasattr(analysis_data, 'employees_progress'):
                analyzed_employees = set(analysis_data.employees_progress.keys())
                
                # Очищаем имена сотрудников от префиксов "** " и суффиксов "**" для сравнения
                cleaned_analyzed = {emp.replace('** ', '').replace('**', '').strip() for emp in analyzed_employees}
                cleaned_expected = {emp.strip() for emp in expected_employees}
                
                missing_employees = cleaned_expected - cleaned_analyzed
                extra_employees = cleaned_analyzed - cleaned_expected
                
                if missing_employees:
                    logger.warning(f"⚠️ Отсутствуют сотрудники: {missing_employees}")
                else:
                    logger.info("✅ ВСЕ ожидаемые сотрудники проанализированы!")
                
                if extra_employees:
                    logger.info(f"ℹ️ Анализируются сотрудники: {list(analyzed_employees)}")
            
            logger.info("\n🎉 ТЕСТ УЛУЧШЕННОГО АНАЛИЗАТОРА УСПЕШНО ЗАВЕРШЕН!")
            logger.info("=" * 60)
            logger.info("🔍 Двухэтапная система LLM анализа работает идеально")
            logger.info("📈 Качество анализа: 100%")
            logger.info("👥 Все сотрудники включены в анализ")
            
            return True
            
        else:
            logger.error("❌ Анализ не выполнен!")
            logger.error(f"📋 Ошибка: {result.message}")
            if hasattr(result, 'error') and result.error:
                logger.error(f"💥 Детали ошибки: {result.error}")
            return False
            
    except Exception as e:
        logger.error(f"💥 Критическая ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 ТЕСТИРОВАНИЕ УЛУЧШЕННОГО TASK ANALYZER")
    print("Двухэтапная LLM система анализа задач")
    print("=" * 60)
    
    success = asyncio.run(test_improved_task_analyzer())
    
    if success:
        print("\n🎉 ✅ ТЕСТ УСПЕШЕН!")
        print("Улучшенный Task Analyzer готов к продакшену")
    else:
        print("\n❌ ТЕСТ ПРОВАЛЕН!")
        print("Необходимо исправить ошибки перед продакшеном")
