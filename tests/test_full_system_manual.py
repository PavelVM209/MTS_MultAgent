#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ручной тест полной системы Employee Monitoring на реальных данных и API

Запускает все компоненты системы последовательно для проверки работы с реальными данными.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

from orchestrator.employee_monitoring_orchestrator_fixed import EmployeeMonitoringOrchestratorFixed
from core.config import get_employee_monitoring_config
from agents.quality_orchestrator import QualityOrchestrator

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('manual_test_results.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ManualSystemTester:
    """Класс для ручного тестирования всей системы"""
    
    def __init__(self):
        """Инициализация тестера"""
        self.orchestrator = None
        self.quality_orchestrator = None
        self.test_results = {
            'start_time': datetime.now().isoformat(),
            'tests': {},
            'errors': [],
            'summary': {}
        }
    
    async def setup(self):
        """Настройка системы"""
        try:
            logger.info("🔧 Настройка системы...")
            
            # Проверяем конфигурацию
            config = get_employee_monitoring_config()
            logger.info(f"📋 Конфигурация загружена: {config.get('scheduling', {})}")
            
            # Инициализируем Quality Orchestrator
            self.quality_orchestrator = QualityOrchestrator()
            system_status = await self.quality_orchestrator.get_system_status()
            logger.info(f"🎯 Quality Orchestrator статус: {system_status}")
            
            # Инициализируем основной оркестратор
            self.orchestrator = EmployeeMonitoringOrchestratorFixed()
            logger.info("🎛️ Основной оркестратор инициализирован")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка настройки: {e}")
            self.test_results['errors'].append(f"Setup error: {e}")
            return False
    
    async def test_jira_analysis(self):
        """Тест анализа Jira задач"""
        logger.info("🔄 Тестирование анализа Jira задач...")
        
        try:
            start_time = datetime.now()
            
            # Запускаем анализ Jira через Quality Orchestrator
            result = await self.quality_orchestrator.execute_daily_task_workflow()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.test_results['tests']['jira_analysis'] = {
                'success': result.get('success', False),
                'execution_time_seconds': execution_time,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
            if result.get('success'):
                logger.info(f"✅ Анализ Jira выполнен успешно за {execution_time:.2f} сек")
                logger.info(f"📊 Качество анализа: {result.get('quality_score', 0):.2f}")
            else:
                logger.error(f"❌ Анализ Jira завершился с ошибкой: {result.get('error', 'Unknown')}")
            
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка при анализе Jira: {e}")
            self.test_results['tests']['jira_analysis'] = {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.test_results['errors'].append(f"Jira analysis error: {e}")
            return False
    
    async def test_meeting_analysis(self):
        """Тест анализа протоколов встреч"""
        logger.info("🔄 Тестирование анализа протоколов встреч...")
        
        try:
            start_time = datetime.now()
            
            # Проверяем наличие протоколов
            protocols_dir = Path("protocols")
            if not protocols_dir.exists():
                logger.warning("⚠️ Директория protocols не найдена, создаем тестовый протокол")
                protocols_dir.mkdir(exist_ok=True)
                self._create_test_protocol()
            
            # Запускаем анализ протоколов через Quality Orchestrator
            result = await self.quality_orchestrator.execute_daily_meeting_workflow()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.test_results['tests']['meeting_analysis'] = {
                'success': result.get('success', False),
                'execution_time_seconds': execution_time,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
            if result.get('success'):
                logger.info(f"✅ Анализ протоколов выполнен успешно за {execution_time:.2f} сек")
                logger.info(f"📊 Качество анализа: {result.get('quality_score', 0):.2f}")
                if 'report_path' in result:
                    logger.info(f"📄 Отчет сохранен: {result['report_path']}")
            else:
                logger.error(f"❌ Анализ протоколов завершился с ошибкой: {result.get('error', 'Unknown')}")
            
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка при анализе протоколов: {e}")
            self.test_results['tests']['meeting_analysis'] = {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.test_results['errors'].append(f"Meeting analysis error: {e}")
            return False
    
    async def test_weekly_report(self):
        """Тест еженедельного отчета"""
        logger.info("🔄 Тестирование еженедельного отчета...")
        
        try:
            start_time = datetime.now()
            
            # Запускаем генерацию еженедельного отчета через Quality Orchestrator
            result = await self.quality_orchestrator.execute_weekly_workflow()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.test_results['tests']['weekly_report'] = {
                'success': result.get('success', False),
                'execution_time_seconds': execution_time,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
            if result.get('success'):
                logger.info(f"✅ Еженедельный отчет выполнен успешно за {execution_time:.2f} сек")
                logger.info(f"📊 Качество отчета: {result.get('quality_score', 0):.2f}")
                if result.get('published_to_confluence'):
                    logger.info(f"🌐 Отчет опубликован в Confluence: {result.get('confluence_url', 'Unknown URL')}")
                if 'report_path' in result:
                    logger.info(f"📄 Отчет сохранен: {result['report_path']}")
            else:
                logger.error(f"❌ Еженедельный отчет завершился с ошибкой: {result.get('error', 'Unknown')}")
            
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка при генерации еженедельного отчета: {e}")
            self.test_results['tests']['weekly_report'] = {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.test_results['errors'].append(f"Weekly report error: {e}")
            return False
    
    async def test_system_status(self):
        """Тест статуса системы"""
        logger.info("🔄 Тестирование статуса системы...")
        
        try:
            # Получаем статус через оркестратор
            status = await self.orchestrator.get_system_status()
            
            self.test_results['tests']['system_status'] = {
                'success': True,
                'status': status,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info("✅ Статус системы получен")
            logger.info(f"🎯 Общий статус: {status.get('overall_status', 'Unknown')}")
            
            # Получаем запланированные задачи
            jobs = await self.orchestrator.get_scheduled_jobs()
            logger.info(f"📋 Запланированных задач: {len(jobs)}")
            for job in jobs:
                logger.info(f"   - {job.get('name', 'Unknown')}: {job.get('next_run_time', 'Unknown')}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса системы: {e}")
            self.test_results['tests']['system_status'] = {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.test_results['errors'].append(f"System status error: {e}")
            return False
    
    async def test_api_connectivity(self):
        """Тест подключения к API"""
        logger.info("🔄 Тестирование подключения к API...")
        
        try:
            from core.jira_client import JiraClient
            from core.llm_client import LLMClient
            
            # Тест Jira API
            jira_client = JiraClient()
            jira_config = jira_client.get_config()
            
            jira_result = {
                'configured': bool(jira_config.get('base_url') and jira_config.get('access_token')),
                'config_valid': jira_client.validate_config(),
                'base_url': jira_config.get('base_url', 'Not configured'),
                'username': jira_config.get('username', 'Not configured')
            }
            
            if jira_result['configured'] and jira_result['config_valid']:
                logger.info("✅ Jira API настроен корректно")
            else:
                logger.warning("⚠️ Jira API требует настройки")
            
            # Тест LLM API
            llm_client = LLMClient()
            
            try:
                # Простая проверка подключения
                test_response = await llm_client.generate_response({
                    "messages": [{"role": "user", "content": "Test connection"}],
                    "max_tokens": 10
                })
                
                llm_result = {
                    'connected': True,
                    'model': llm_client.model,
                    'base_url': llm_client.base_url
                }
                logger.info("✅ LLM API подключен и работает")
                
            except Exception as e:
                llm_result = {
                    'connected': False,
                    'error': str(e),
                    'model': llm_client.model,
                    'base_url': llm_client.base_url
                }
                logger.warning(f"⚠️ Проблема с LLM API: {e}")
            
            self.test_results['tests']['api_connectivity'] = {
                'success': True,
                'jira': jira_result,
                'llm': llm_result,
                'timestamp': datetime.now().isoformat()
            }
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования API: {e}")
            self.test_results['tests']['api_connectivity'] = {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.test_results['errors'].append(f"API connectivity error: {e}")
            return False
    
    def _create_test_protocol(self):
        """Создает тестовый протокол встречи"""
        test_protocol = """Протокол совещания команды разработки
Дата: 30 марта 2026 г.
Время: 14:00-15:30
Участники: Мария Иванова, Иван Петров, Алексей Сидоров, Елена Кузнецова

ПОВЕСТКА ДНЯ:
1. Обсуждение прогресса по проекту X
2. Планирование спринта
3. Решение проблем с производством

ХОД СОВЕЩАНИЯ:

1. Обсуждение прогресса по проекту X (14:00-14:45)
   - Мария Иванова представила отчет о выполнении задач:
     * Завершено: 5 из 8 запланированных задач
     * В работе: 2 задачи
     * Задержка: 1 задача (проблема с интеграцией)
   
   - Иван Петров сообщил о проблемах с тестированием:
     * Найден критический баг в модуле авторизации
     * Требуется дополнительное время для исправлений
   
   - Алексей Сидоров предложил решение:
     * Использовать альтернативный подход к интеграции
     * Провести дополнительное код-ревью

РЕШЕНИЯ:
1. Перенести дедлайн по проекту X на 3 дня
2. Алексей Сидоров подготовить план миграции до 5 апреля
3. Иван Петров исправить критический баг до 31 марта
4. Мария Иванова координировать работу с интеграцией
5. Елена Кузнецова обновить план проекта с новыми сроками
"""
        
        protocol_file = Path("protocols/meeting_2026-03-30.txt")
        with open(protocol_file, 'w', encoding='utf-8') as f:
            f.write(test_protocol)
        
        logger.info(f"📄 Создан тестовый протокол: {protocol_file}")
    
    async def run_all_tests(self):
        """Запускает все тесты"""
        logger.info("🚀 Запуск полного тестирования системы...")
        
        # Настройка
        if not await self.setup():
            logger.error("❌ Не удалось настроить систему")
            return False
        
        # Список тестов
        tests = [
            ("Статус системы", self.test_system_status),
            ("Подключение к API", self.test_api_connectivity),
            ("Анализ Jira задач", self.test_jira_analysis),
            ("Анализ протоколов встреч", self.test_meeting_analysis),
            ("Еженедельный отчет", self.test_weekly_report),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            logger.info(f"\n{'='*60}")
            logger.info(f"🧪 Выполняем тест: {test_name}")
            logger.info(f"{'='*60}")
            
            try:
                success = await test_func()
                results[test_name] = success
                
                if success:
                    logger.info(f"✅ Тест '{test_name}' пройден")
                else:
                    logger.warning(f"⚠️ Тест '{test_name}' не пройден")
                
            except Exception as e:
                logger.error(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
                results[test_name] = False
                self.test_results['errors'].append(f"Test '{test_name}' critical error: {e}")
        
        # Формирование сводки
        self.test_results['summary'] = {
            'total_tests': len(tests),
            'passed_tests': sum(1 for result in results.values() if result),
            'failed_tests': sum(1 for result in results.values() if not result),
            'success_rate': f"{(sum(1 for result in results.values() if result) / len(tests) * 100):.1f}%",
            'end_time': datetime.now().isoformat()
        }
        
        return results
    
    def save_results(self):
        """Сохраняет результаты тестирования"""
        import json
        
        results_file = f"manual_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📊 Результаты сохранены в: {results_file}")
        return results_file
    
    def print_summary(self):
        """Выводит сводку результатов"""
        summary = self.test_results['summary']
        
        print(f"\n{'='*60}")
        print("📊 СВОДКА РЕЗУЛЬТАТОВ ТЕСТИРОВАНИЯ")
        print(f"{'='*60}")
        print(f"📈 Всего тестов: {summary['total_tests']}")
        print(f"✅ Успешных: {summary['passed_tests']}")
        print(f"❌ Неудачных: {summary['failed_tests']}")
        print(f"📊 Успешность: {summary['success_rate']}")
        
        if self.test_results['errors']:
            print(f"\n⚠️ Ошибки ({len(self.test_results['errors'])}):")
            for error in self.test_results['errors']:
                print(f"   - {error}")
        
        print(f"\nВремя начала: {self.test_results['start_time']}")
        print(f"Время окончания: {summary['end_time']}")
        print(f"{'='*60}")


async def main():
    """Главная функция"""
    print("🧪 Ручное тестирование Employee Monitoring System")
    print("🔄 Запуск всех компонент на реальных данных и API\n")
    
    tester = ManualSystemTester()
    
    try:
        # Запуск всех тестов
        results = await tester.run_all_tests()
        
        # Сохранение результатов
        results_file = tester.save_results()
        
        # Вывод сводки
        tester.print_summary()
        
        # Возврат кода завершения
        success_rate = float(tester.test_results['summary']['success_rate'].rstrip('%'))
        return 0 if success_rate >= 50 else 1
        
    except KeyboardInterrupt:
        logger.info("🛑 Тестирование прервано пользователем")
        return 130
    except Exception as e:
        logger.error(f"❌ Критическая ошибка тестирования: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
