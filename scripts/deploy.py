#!/usr/bin/env python3
"""
Скрипт развертывания production-версии MTS MultAgent системы

Автоматизирует процесс развертывания, настройки конфигурации,
проверки зависимостей и запуска системы в production-режиме.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.config import get_config
from src.core.agent_orchestrator import AgentOrchestrator
from src.agents.daily_jira_analyzer import DailyJiraAnalyzer
from src.agents.daily_meeting_analyzer import DailyMeetingAnalyzer

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ProductionDeployer:
    """
    Класс для развертывания production-версии системы
    
    Отвечает за:
    - Проверку окружения и зависимостей
    - Настройку production-конфигурации
    - Инициализацию базы данных
    - Запуск сервисов
    - Проверку работоспособности
    """
    
    def __init__(self):
        """Инициализация развертывания"""
        self.config = get_config()
        self.project_root = Path(__file__).parent.parent
        self.deployment_start = datetime.now()
        
        # Директории для развертывания
        self.directories = {
            'logs': self.project_root / 'logs',
            'data': self.project_root / 'data',
            'temp': self.project_root / 'temp',
            'backups': self.project_root / 'backups'
        }
        
        logger.info("Инициализируем систему развертывания")
    
    def check_environment(self) -> bool:
        """
        Проверка системных требований и окружения
        
        Returns:
            bool: True если все проверки пройдены
        """
        logger.info("🔍 Проверка системного окружения...")
        
        checks_passed = 0
        total_checks = 0
        
        # Проверка Python версии
        total_checks += 1
        python_version = sys.version_info
        if python_version >= (3, 8):
            logger.info(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
            checks_passed += 1
        else:
            logger.error(f"❌ Требуется Python 3.8+, обнаружено {python_version.major}.{python_version.minor}")
        
        # Проверка необходимых директорий
        total_checks += 1
        dirs_created = self._create_directories()
        if dirs_created:
            logger.info("✅ Системные директории созданы/проверены")
            checks_passed += 1
        else:
            logger.error("❌ Не удалось создать системные директории")
        
        # Проверка переменных окружения
        total_checks += 1
        env_ok = self._check_environment_variables()
        if env_ok:
            logger.info("✅ Переменные окружения настроены")
            checks_passed += 1
        else:
            logger.error("❌ Отсутствуют необходимые переменные окружения")
        
        # Проверка зависимостей
        total_checks += 1
        deps_ok = self._check_dependencies()
        if deps_ok:
            logger.info("✅ Все зависимости установлены")
            checks_passed += 1
        else:
            logger.error("❌ Проблемы с зависимостями")
        
        # Проверка конфигурации
        total_checks += 1
        config_ok = self._validate_configuration()
        if config_ok:
            logger.info("✅ Конфигурация прошла валидацию")
            checks_passed += 1
        else:
            logger.error("❌ Ошибки в конфигурации")
        
        logger.info(f"📊 Проверка окружения завершена: {checks_passed}/{total_checks} пройдено")
        
        return checks_passed == total_checks
    
    def _create_directories(self) -> bool:
        """Создание необходимых директорий"""
        try:
            for dir_name, dir_path in self.directories.items():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Создана директория: {dir_path}")
            
            # Установка прав доступа
            for dir_path in self.directories.values():
                os.chmod(dir_path, 0o755)
            
            return True
        except Exception as e:
            logger.error(f"Ошибка при создании директорий: {e}")
            return False
    
    def _check_environment_variables(self) -> bool:
        """Проверка необходимых переменных окружения"""
        required_vars = [
            'OPENAI_API_KEY',
            'JIRA_URL',
            'JIRA_USERNAME',
            'JIRA_API_TOKEN',
            'CONFLUENCE_URL',
            'CONFLUENCE_USERNAME',
            'CONFLUENCE_API_TOKEN'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Отсутствуют переменные окружения: {missing_vars}")
            logger.info("Создайте .env файл на основе .env.example")
            return False
        
        return True
    
    def _check_dependencies(self) -> bool:
        """Проверка установленных зависимостей"""
        try:
            # Проверка установленных пакетов
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error("Не удалось получить список установленных пакетов")
                return False
            
            # Ключевые зависимости для проверки
            required_packages = [
                'openai', 'pandas', 'numpy', 'pyyaml', 
                'aiohttp', 'asyncio', 'pytest', 'python-dotenv'
            ]
            
            installed = result.stdout.lower()
            missing_packages = []
            
            for package in required_packages:
                if package.lower() not in installed:
                    missing_packages.append(package)
            
            if missing_packages:
                logger.error(f"Отсутствуют пакеты: {missing_packages}")
                logger.info("Установите зависимости: pip install -r requirements.txt")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при проверке зависимостей: {e}")
            return False
    
    def _validate_configuration(self) -> bool:
        """Валидация конфигурации"""
        try:
            # Проверка основных секций конфигурации
            required_sections = ['llm', 'jira', 'confluence', 'database']
            
            for section in required_sections:
                if section not in self.config:
                    logger.error(f"Отсутствует секция конфигурации: {section}")
                    return False
            
            # Проверка LLM конфигурации
            llm_config = self.config.get('llm', {})
            if not llm_config.get('api_key'):
                logger.error("Отсутствует API ключ для LLM")
                return False
            
            # Проверка JIRA конфигурации
            jira_config = self.config.get('jira', {})
            required_jira_fields = ['url', 'username', 'api_token']
            for field in required_jira_fields:
                if not jira_config.get(field):
                    logger.error(f"Отсутствует поле JIRA конфигурации: {field}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка валидации конфигурации: {e}")
            return False
    
    def deploy_services(self) -> bool:
        """
        Развертывание и запуск сервисов
        
        Returns:
            bool: True если развертывание успешно
        """
        logger.info("🚀 Начинаем развертывание сервисов...")
        
        try:
            # Инициализация базы данных
            if not self._initialize_database():
                logger.error("Ошибка инициализации базы данных")
                return False
            
            # Настройка логирования
            if not self._setup_logging():
                logger.error("Ошибка настройки логирования")
                return False
            
            # Инициализация агентов
            if not self._initialize_agents():
                logger.error("Ошибка инициализации агентов")
                return False
            
            # Запуск мониторинга
            if not self._setup_monitoring():
                logger.error("Ошибка настройки мониторинга")
                return False
            
            logger.info("✅ Все сервисы успешно развернуты")
            return True
            
        except Exception as e:
            logger.error(f"Критическая ошибка развертывания: {e}")
            return False
    
    def _initialize_database(self) -> bool:
        """Инициализация базы данных"""
        logger.info("🗄️ Инициализация базы данных...")
        
        try:
            from src.core.json_memory_store import JSONMemoryStore
            
            # Создание экземпляра хранилища
            memory_store = JSONMemoryStore()
            
            # Проверка соединения
            if memory_store.is_healthy():
                logger.info("✅ База данных готова к работе")
                return True
            else:
                logger.error("❌ База данных не отвечает")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            return False
    
    def _setup_logging(self) -> bool:
        """Настройка production-логирования"""
        logger.info("📝 Настройка системы логирования...")
        
        try:
            # Создание лог-файлов
            log_files = [
                'app.log',
                'error.log',
                'performance.log',
                'security.log'
            ]
            
            logs_dir = self.directories['logs']
            for log_file in log_files:
                log_path = logs_dir / log_file
                log_path.touch(exist_ok=True)
                os.chmod(log_path, 0o644)
            
            logger.info("✅ Система логирования настроена")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка настройки логирования: {e}")
            return False
    
    async def _initialize_agents(self) -> bool:
        """Инициализация и проверка агентов"""
        logger.info("🤖 Инициализация агентов...")
        
        try:
            # Создание orchstrator
            orchestrator = AgentOrchestrator()
            
            # Создание агентов
            jira_analyzer = DailyJiraAnalyzer()
            meeting_analyzer = DailyMeetingAnalyzer()
            
            # Регистрация агентов
            orchestrator.register_agent("daily_jira_analyzer", jira_analyzer, priority=2)
            orchestrator.register_agent("daily_meeting_analyzer", meeting_analyzer, priority=1)
            
            # Проверка здоровья агентов
            health = await orchestrator.get_health_status()
            
            if health['orchestrator_status'] == 'healthy':
                logger.info("✅ Агенты успешно инициализированы")
                return True
            else:
                logger.error(f"❌ Проблемы со здоровьем системы: {health}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка инициализации агентов: {e}")
            return False
    
    def _setup_monitoring(self) -> bool:
        """Настройка мониторинга"""
        logger.info("📊 Настройка системы мониторинга...")
        
        try:
            # Создание директорий для мониторинга
            monitoring_dirs = [
                self.directories['logs'] / 'metrics',
                self.directories['logs'] / 'alerts',
                self.directories['logs'] / 'health'
            ]
            
            for monitor_dir in monitoring_dirs:
                monitor_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info("✅ Система мониторинга настроена")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка настройки мониторинга: {e}")
            return False
    
    def run_health_check(self) -> bool:
        """
        Комплексная проверка работоспособности системы
        
        Returns:
            bool: True если система работоспособна
        """
        logger.info("🏥 Запуск комплексной проверки работоспособности...")
        
        health_results = {}
        
        # Проверка базы данных
        try:
            from src.core.json_memory_store import JSONMemoryStore
            memory_store = JSONMemoryStore()
            health_results['database'] = memory_store.is_healthy()
        except Exception as e:
            logger.error(f"Ошибка проверки базы данных: {e}")
            health_results['database'] = False
        
        # Проверка LLM клиента
        try:
            from src.core.llm_client import LLMClient
            llm_client = LLMClient()
            health_results['llm'] = await llm_client.is_available()
        except Exception as e:
            logger.error(f"Ошибка проверки LLM клиента: {e}")
            health_results['llm'] = False
        
        # Проверка агентов
        try:
            orchestrator = AgentOrchestrator()
            jira_analyzer = DailyJiraAnalyzer()
            meeting_analyzer = DailyMeetingAnalyzer()
            
            orchestrator.register_agent("daily_jira_analyzer", jira_analyzer, priority=2)
            orchestrator.register_agent("daily_meeting_analyzer", meeting_analyzer, priority=1)
            
            health_status = await orchestrator.get_health_status()
            health_results['agents'] = health_status['orchestrator_status'] == 'healthy'
        except Exception as e:
            logger.error(f"Ошибка проверки агентов: {e}")
            health_results['agents'] = False
        
        # Проверка файловой системы
        try:
            health_results['filesystem'] = all(
                dir_path.exists() and os.access(dir_path, os.W_OK)
                for dir_path in self.directories.values()
            )
        except Exception as e:
            logger.error(f"Ошибка проверки файловой системы: {e}")
            health_results['filesystem'] = False
        
        # Подсчет результатов
        healthy_components = sum(health_results.values())
        total_components = len(health_results)
        
        logger.info(f"📊 Результаты проверки работоспособности:")
        for component, status in health_results.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"   {status_icon} {component}: {'здоров' if status else 'проблема'}")
        
        logger.info(f"🏥 Система работоспособна: {healthy_components}/{total_components} компонентов")
        
        return healthy_components == total_components
    
    def create_backup(self) -> bool:
        """
        Создание резервной копии конфигурации и данных
        
        Returns:
            bool: True если бэкап создан успешно
        """
        logger.info("💾 Создание резервной копии...")
        
        try:
            backup_dir = self.directories['backups'] / f"backup_{self.deployment_start.strftime('%Y%m%d_%H%M%S')}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Бэкап конфигурации
            import shutil
            config_files = list(self.project_root.glob("config/*.yaml"))
            for config_file in config_files:
                shutil.copy2(config_file, backup_dir / config_file.name)
            
            # Бэкап.environment файла
            env_file = self.project_root / ".env"
            if env_file.exists():
                shutil.copy2(env_file, backup_dir / ".env")
            
            logger.info(f"✅ Резервная копия создана: {backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            return False
    
    def generate_deployment_report(self) -> str:
        """
        Генерация отчета о развертывании
        
        Returns:
            str: Путь к файлу отчета
        """
        logger.info("📋 Генерация отчета о развертывании...")
        
        try:
            deployment_time = datetime.now() - self.deployment_start
            
            report = f"""
# Отчет о развертывании MTS MultAgent System

**Дата и время:** {self.deployment_start.strftime('%Y-%m-%d %H:%M:%S')}
**Длительность развертывания:** {deployment_time}

## Компоненты системы
- ✅ AgentOrchestrator - Система оркестрации агентов
- ✅ DailyJiraAnalyzer - Анализатор JIRA задач
- ✅ DailyMeetingAnalyzer - Анализатор протоколов совещаний
- ✅ JSONMemoryStore - Система хранения данных
- ✅ LLMClient - Клиент для работы с языковыми моделями

## Директории
- 📁 Логи: {self.directories['logs']}
- 📁 Данные: {self.directories['data']}
- 📁 Временные файлы: {self.directories['temp']}
- 📁 Резервные копии: {self.directories['backups']}

## Конфигурация
- 📄 Конфигурация LLM: Настроена
- 📄 Конфигурация JIRA: Настроена
- 📄 Конфигурация Confluence: Настроена

## Статус развертывания: ✅ УСПЕШНО

## Следующие шаги
1. Настройте автоматические задачи через cron
2. Проверьте веб-интерфейс мониторинга
3. Настройте оповещения и алерты
4. Проведите тестовый запуск workflow

---
Система готова к production использованию
"""
            
            report_file = self.directories['logs'] / f"deployment_report_{self.deployment_start.strftime('%Y%m%d_%H%M%S')}.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"✅ Отчет создан: {report_file}")
            return str(report_file)
            
        except Exception as e:
            logger.error(f"Ошибка генерации отчета: {e}")
            return ""


async def main():
    """Главная функция развертывания"""
    print("🚀 Развертывание MTS MultAgent System")
    print("=" * 50)
    
    deployer = ProductionDeployer()
    
    # Этап 1: Проверка окружения
    if not deployer.check_environment():
        logger.error("❌ Проверка окружения не пройдена. Исправьте ошибки и попробуйте снова.")
        return 1
    
    print("\n📋 Создание резервной копии...")
    if not deployer.create_backup():
        logger.warning("⚠️ Не удалось создать резервную копию, продолжаем развертывание")
    
    print("\n🚀 Развертывание сервисов...")
    if not await deployer._initialize_agents():
        logger.error("❌ Не удалось инициализировать агенты")
        return 1
    
    if not deployer._initialize_database():
        logger.error("❌ Не удалось инициализировать базу данных")
        return 1
    
    if not deployer._setup_logging():
        logger.error("❌ Не удалось настроить логирование")
        return 1
    
    if not deployer._setup_monitoring():
        logger.error("❌ Не удалось настроить мониторинг")
        return 1
    
    print("\n🏥 Проверка работоспособности системы...")
    if not deployer.run_health_check():
        logger.error("❌ Проверка работоспособности не пройдена")
        return 1
    
    print("\n📋 Генерация отчета о развертывании...")
    report_file = deployer.generate_deployment_report()
    if report_file:
        print(f"✅ Отчет создан: {report_file}")
    
    print("\n" + "=" * 50)
    print("🎉 Развертывание завершено успешно!")
    print("=" * 50)
    print("\n📋 Что делать дальше:")
    print("1. ✅ Проверьте логи в директории ./logs/")
    print("2. ✅ Настройте cron для автоматического запуска")
    print("3. ✅ Проверьте веб-интерфейс мониторинга")
    print("4. ✅ Проведите тестовый запуск workflow")
    print("5. ✅ Настройте оповещения и алерты")
    
    print(f"\n📁 Директории созданы:")
    for name, path in deployer.directories.items():
        print(f"   📁 {name}: {path}")
    
    print(f"\n📊 Время развертывания: {datetime.now() - deployer.deployment_start}")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
