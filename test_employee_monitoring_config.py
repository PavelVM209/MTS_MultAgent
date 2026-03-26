#!/usr/bin/env python3
"""
Тестовый скрипт для проверки загрузки конфигурации мониторинга сотрудников
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Добавляем src в Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.config_manager import get_config_manager
from src.core.config import get_employee_monitoring_config
import structlog

logger = structlog.get_logger()


async def test_employee_monitoring_config():
    """Тест загрузки конфигурации мониторинга сотрудников"""
    
    print("🔧 Тест загрузки конфигурации мониторинга сотрудников...")
    print("=" * 60)
    
    try:
        # Инициализация менеджера конфигурации
        config_manager = await get_config_manager()
        await config_manager.load_config()
        
        print("✅ Базовая конфигурация загружена успешно")
        
        # Тест загрузки employee_monitoring.yaml
        emp_config = config_manager.get_section('employee_monitoring', {})
        
        if emp_config:
            print("✅ Конфигурация employee_monitoring.yaml загружена")
            print(f"📊 Количество секций: {len(emp_config)}")
            
            # Проверка основных секций
            required_sections = [
                'jira', 'protocols', 'reports', 'confluence', 
                'scheduler', 'quality', 'employees'
            ]
            
            for section in required_sections:
                if section in emp_config:
                    print(f"  ✅ Секция '{section}': присутствует")
                else:
                    print(f"  ❌ Секция '{section}': отсутствует")
            
            # Вывод важных параметров
            print("\n📋 Ключевые параметры:")
            
            # Jira configuration
            jira_config = emp_config.get('jira', {})
            print(f"  🎯 Jira проекты: {jira_config.get('project_keys', 'не настроено')}")
            print(f"  🔍 Jira фильтр: {jira_config.get('query_filter', 'не настроено')[:50]}...")
            
            # Scheduler configuration
            scheduler_config = emp_config.get('scheduler', {})
            print(f"  ⏰ Ежедневный анализ: {scheduler_config.get('daily_analysis_time', 'не настроено')}")
            print(f"  📅 Еженедельный отчет: {scheduler_config.get('weekly_report_time', 'не настроено')}")
            
            # Quality configuration
            quality_config = emp_config.get('quality', {})
            print(f"  📊 Порог качества: {quality_config.get('threshold', 'не настроено')}")
            
            # Reports configuration
            reports_config = emp_config.get('reports', {})
            print(f"  📁 Папка ежедневных отчетов: {reports_config.get('daily_reports_dir', 'не настроено')}")
            print(f"  📁 Папка еженедельных отчетов: {reports_config.get('weekly_reports_dir', 'не настроено')}")
            
        else:
            print("❌ Конфигурация employee_monitoring.yaml не загружена")
        
        # Тест через функцию get_employee_monitoring_config
        print("\n🔧 Тест через get_employee_monitoring_config():")
        try:
            emp_config_func = get_employee_monitoring_config()
            if emp_config_func:
                print("✅ Функция get_employee_monitoring_config() работает")
                print(f"📊 Получено секций: {len(emp_config_func)}")
            else:
                print("❌ Функция get_employee_monitoring_config() вернула пустой результат")
        except Exception as e:
            print(f"❌ Ошибка в функции get_employee_monitoring_config(): {e}")
        
        # Тест переменных окружения
        print("\n🌍 Тест переменных окружения:")
        env_vars = [
            'JIRA_PROJECT_KEYS',
            'DAILY_ANALYSIS_TIME', 
            'WEEKLY_REPORT_TIME',
            'QUALITY_THRESHOLD',
            'EMPLOYEE_MONITORING_ENABLED'
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                print(f"  ✅ {var}: {value}")
            else:
                print(f"  ⚠️  {var}: не установлена")
        
        # Проверка директорий
        print("\n📁 Проверка директорий:")
        directories = [
            'reports/daily',
            'reports/weekly', 
            'reports/quality',
            'dev-reports/daily',
            'dev-reports/weekly'
        ]
        
        for dir_path in directories:
            if Path(dir_path).exists():
                print(f"  ✅ {dir_path}: существует")
            else:
                print(f"  ❌ {dir_path}: не существует")
        
        print("\n" + "=" * 60)
        print("🎉 Тест конфигурации мониторинга сотрудников завершен!")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании конфигурации: {e}")
        logger.error("Config test failed", error=str(e))
        return False


async def test_config_integration():
    """Тест интеграции конфигурации с существующими компонентами"""
    
    print("\n🔗 Тест интеграции конфигурации...")
    print("=" * 40)
    
    try:
        # Тест загрузки полной конфигурации
        config_manager = await get_config_manager()
        full_config = config_manager.get_config()
        
        print("✅ Полная конфигурация загружена")
        print(f"📊 Всего секций: {len(full_config)}")
        
        # Проверка что employee_monitoring интегрирован
        if 'employee_monitoring' in full_config:
            print("✅ employee_monitoring интегрирован в основную конфигурацию")
        else:
            print("❌ employee_monitoring не найден в основной конфигурации")
        
        # Тест health check
        health = await config_manager.health_check()
        print(f"🏥 Статус конфигурации: {health.get('status', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка интеграции: {e}")
        return False


async def main():
    """Основная функция тестирования"""
    
    print("🚀 Запуск тестов конфигурации мониторинга сотрудников MTS MultAgent")
    print("=" * 80)
    
    # Тест 1: Базовая конфигурация
    test1_result = await test_employee_monitoring_config()
    
    # Тест 2: Интеграция
    test2_result = await test_config_integration()
    
    # Итоги
    print("\n" + "=" * 80)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
    print(f"  🔧 Базовая конфигурация: {'✅ УСПЕХ' if test1_result else '❌ ОШИБКА'}")
    print(f"  🔗 Интеграция: {'✅ УСПЕХ' if test2_result else '❌ ОШИБКА'}")
    
    if test1_result and test2_result:
        print("\n🎉 Все тесты пройдены! Система готова к разработке агентов.")
        return 0
    else:
        print("\n❌ Некоторые тесты не пройдены. Проверьте конфигурацию.")
        return 1


if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Запуск тестов
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
