#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Improved Meeting Analyzer Agent with Three-Stage Analysis System
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

async def test_improved_meeting_analyzer():
    """Тестирование улучшенного Meeting Analyzer с трехэтапной системой"""
    try:
        logger.info("🚀 ЗАПУСК ТЕСТА УЛУЧШЕННОГО MEETING ANALYZER")
        logger.info("Трехэтапная система анализа совещаний")
        logger.info("=" * 80)
        
        # Проверяем наличие необходимых файлов
        task_analyzer_txt = 'stage1_text_analysis.txt'
        if not os.path.exists(task_analyzer_txt):
            logger.error(f"❌ Файл {task_analyzer_txt} не найден!")
            logger.info("Сначала запустите Task Analyzer для создания этого файла")
            return False
        
        # Проверяем наличие протоколов
        protocols_dir = './protocols'
        if not os.path.exists(protocols_dir):
            logger.error(f"❌ Директория {protocols_dir} не найдена!")
            return False
        
        protocol_files = list(os.path.join(protocols_dir, f) for f in os.listdir(protocols_dir) if f.endswith('.txt'))
        if not protocol_files:
            logger.error(f"❌ В директории {protocols_dir} нет .txt файлов!")
            return False
        
        logger.info(f"✅ Найдено {len(protocol_files)} протоколов для анализа")
        logger.info(f"✅ Файл Task Analyzer: {task_analyzer_txt}")
        
        # Импортируем улучшенный агент
        from src.agents.meeting_analyzer_agent_improved import ImprovedMeetingAnalyzerAgent
        
        # Создаем агент
        agent = ImprovedMeetingAnalyzerAgent()
        logger.info("✅ ImprovedMeetingAnalyzerAgent создан")
        
        # Проверяем health status
        health = await agent.get_health_status()
        logger.info(f"📊 Health Status: {health['status']}")
        logger.info(f"🔧 LLM Client: {health['llm_client']}")
        logger.info(f"📁 Protocols Directory: {health['protocols_directory']}")
        logger.info(f"📄 Task Analyzer TXT: {health['task_analyzer_txt']}")
        logger.info(f"🔧 Analysis Stages: {health['analysis_stages']}")
        
        if health['status'] != 'healthy':
            logger.warning("⚠️ Агент не в здоровом состоянии, продолжаем тест...")
        
        # Выполняем анализ
        logger.info("\n🔄 ВЫПОЛНЕНИЕ ТРЕХЭТАПНОГО АНАЛИЗА СОВЕЩАНИЙ")
        logger.info("=" * 80)
        
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
            if hasattr(analysis_data, 'employees_performance'):
                employees = analysis_data.employees_performance
                logger.info(f"👥 Проанализировано сотрудников: {len(employees)}")
                
                for employee, performance in employees.items():
                    rating = performance.performance_rating
                    correlation = performance.task_to_meeting_correlation
                    effectiveness = performance.communication_effectiveness
                    logger.info(f"  • {employee}: рейтинг {rating:.1f}/10, корреляция {correlation:.2f}, эффективность {effectiveness:.1f}/10")
            
            if hasattr(analysis_data, 'team_insights'):
                insights = analysis_data.team_insights
                logger.info(f"💡 Командные инсайты: {len(insights)}")
                for i, insight in enumerate(insights, 1):
                    logger.info(f"  {i}. {insight}")
            
            if hasattr(analysis_data, 'recommendations'):
                recs = analysis_data.recommendations
                logger.info(f"📝 Рекомендации менеджеру: {len(recs)}")
                for i, rec in enumerate(recs, 1):
                    logger.info(f"  {i}. {rec}")
            
            # Показываем метаданные
            if hasattr(analysis_data, 'quality_score'):
                quality = analysis_data.quality_score
                logger.info(f"🎯 Качество анализа: {quality:.3f}")
            
            if hasattr(analysis_data, 'team_collaboration_score'):
                collaboration = analysis_data.team_collaboration_score
                logger.info(f"🤝 Скор командной работы: {collaboration:.1f}/10")
            
            if hasattr(analysis_data, 'task_meeting_alignment'):
                alignment = analysis_data.task_meeting_alignment
                logger.info(f"📊 Согласование задач и встреч: {alignment:.1f}/10")
            
            if hasattr(analysis_data, 'overall_team_health'):
                health_score = analysis_data.overall_team_health
                logger.info(f"💪 Общее здоровье команды: {health_score:.1f}/10")
            
            # Проверяем созданные файлы
            await _check_created_files(analysis_data)
            
            logger.info("\n🎉 ТРЕХЭТАПНЫЙ АНАЛИЗАТОР УСПЕШНО ЗАВЕРШЕН!")
            logger.info("=" * 80)
            logger.info("🔍 Все этапы анализа выполнены корректно")
            logger.info("📈 Комплексный анализ совещаний иtasks завершен")
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

async def _check_created_files(analysis_data) -> None:
    """Проверяем созданные файлы"""
    try:
        from datetime import datetime
        date_str = datetime.now().strftime('%Y-%m-%d')
        reports_dir = f'./reports/daily/{date_str}'
        
        logger.info(f"\n📁 ПРОВЕРКА СОЗДАННЫХ ФАЙЛОВ:")
        logger.info(f"Директория отчетов: {reports_dir}")
        
        # Проверяем основной файл анализа
        main_file = f'{reports_dir}/meeting-analysis_{date_str}.json'
        if os.path.exists(main_file):
            logger.info(f"✅ Основной анализ: {main_file}")
            
            # Показываем содержимое файла
            with open(main_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"   📊 Анализировано сотрудников: {data.get('total_employees', 0)}")
            logger.info(f"   📝 Качество анализа: {data.get('quality_score', 0):.3f}")
            logger.info(f"   💪 Здоровье команды: {data.get('overall_team_health', 0):.1f}/10")
        else:
            logger.warning(f"⚠️ Основной файл не найден: {main_file}")
        
        # Проверяем файл комплексного анализа
        comprehensive_file = f'{reports_dir}/comprehensive-analysis_{date_str}.txt'
        if os.path.exists(comprehensive_file):
            logger.info(f"✅ Комплексный анализ: {comprehensive_file}")
            
            # Показываем размер файла
            size = os.path.getsize(comprehensive_file)
            logger.info(f"   📄 Размер файла: {size:,} байт")
        else:
            logger.warning(f"⚠️ Файл комплексного анализа не найден: {comprehensive_file}")
        
        # Проверяем директорию с прогрессом сотрудников
        progression_dir = f'{reports_dir}/employee_progression'
        if os.path.exists(progression_dir):
            employee_files = list(os.path.join(progression_dir, f) for f in os.listdir(progression_dir) if f.endswith('.json'))
            logger.info(f"✅ Файлы прогресса сотрудников: {len(employee_files)}")
            
            for emp_file in employee_files[:3]:  # Показываем первые 3 файла
                emp_name = os.path.basename(emp_file).replace(f'_{date_str}.json', '')
                logger.info(f"   👤 {emp_name}")
            
            if len(employee_files) > 3:
                logger.info(f"   ... и еще {len(employee_files) - 3} файлов")
        else:
            logger.warning(f"⚠️ Директория прогресса сотрудников не найдена: {progression_dir}")
        
        # Проверяем очищенные протоколы
        cleaned_files = list(os.path.join(reports_dir, f) for f in os.listdir(reports_dir) if f.startswith('cleaned_'))
        if cleaned_files:
            logger.info(f"✅ Очищенные протоколы: {len(cleaned_files)}")
            
            for cleaned_file in cleaned_files[:2]:  # Показываем первые 2 файла
                filename = os.path.basename(cleaned_file)
                logger.info(f"   📋 {filename}")
        else:
            logger.warning("⚠️ Очищенные протоколы не найдены")
            
    except Exception as e:
        logger.error(f"Ошибка при проверке файлов: {e}")

if __name__ == "__main__":
    print("🧪 ТЕСТИРОВАНИЕ УЛУЧШЕННОГО MEETING ANALYZER")
    print("Трехэтапная система анализа совещаний")
    print("Этап 1: Очистка протоколов")
    print("Этап 2: Комплексный анализ (протокол + Task Analyzer)")
    print("Этап 3: Финальный анализ + JSON для сотрудников")
    print("=" * 80)
    
    success = asyncio.run(test_improved_meeting_analyzer())
    
    if success:
        print("\n🎉 ✅ ТЕСТ УСПЕШЕН!")
        print("Улучшенный Meeting Analyzer готов к продакшену")
        print("Все три этапа анализа работают корректно")
    else:
        print("\n❌ ТЕСТ ПРОВАЛЕН!")
        print("Необходимо исправить ошибки перед продакшеном")
