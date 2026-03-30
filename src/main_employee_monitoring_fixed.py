# -*- coding: utf-8 -*-
"""
Employee Monitoring System - Fixed Main Entry Point

Главный файл запуска системы с исправленной архитектурой.
Использует новый QualityOrchestrator и правильную структуру.
"""

import asyncio
import logging
import sys
import signal
from pathlib import Path

# Добавляем src в Python path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from orchestrator.employee_monitoring_orchestrator_fixed import EmployeeMonitoringOrchestratorFixed

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('employee_monitoring.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class EmployeeMonitoringSystemFixed:
    """
    Главная система Employee Monitoring с исправленной архитектурой.
    
    Новая архитектура:
    1. QualityOrchestrator контролирует качество на каждом этапе
    2. TaskAnalyzer работает напрямую с Jira API
    3. MeetingAnalyzer auto-сканирует директорию с протоколами
    4. WeeklyReports публикует в Confluence (без Git интеграции)
    """
    
    def __init__(self):
        """Инициализация системы."""
        self.orchestrator = EmployeeMonitoringOrchestratorFixed()
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Employee Monitoring System Fixed initialized")
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для корректной остановки."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False
    
    async def start(self):
        """Запуск системы."""
        try:
            logger.info("=== Starting Employee Monitoring System (Fixed) ===")
            
            # Запускаем оркестратор
            start_result = await self.orchestrator.start()
            
            if start_result.get('status') == 'started':
                logger.info("✅ System started successfully!")
                logger.info(f"📊 System status: {start_result.get('system_status', {}).get('orchestrator', {}).get('status', 'unknown')}")
                logger.info(f"⏰ Scheduler status: {start_result.get('scheduler_status', {}).get('status', 'unknown')}")
                
                # Показываем расписание
                jobs = await self.orchestrator.get_scheduled_jobs()
                if jobs:
                    logger.info("📅 Scheduled jobs:")
                    for job in jobs:
                        logger.info(f"  • {job.get('name', 'Unknown')} - {job.get('next_run_time', 'Not scheduled')}")
                else:
                    logger.warning("⚠️  No scheduled jobs found")
                
                self.running = True
                
                # Главный цикл системы
                await self._main_loop()
            else:
                logger.error(f"❌ Failed to start system: {start_result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"💥 System startup failed: {e}")
            return False
        
        return True
    
    async def _main_loop(self):
        """Главный цикл работы системы."""
        logger.info("🔄 System is running. Press Ctrl+C to stop.")
        
        try:
            while self.running:
                # Проверяем статус системы каждые 60 секунд
                await asyncio.sleep(60)
                
                if self.running:  # Double check after sleep
                    status = await self.orchestrator.get_system_status()
                    
                    # Логируем статус только если есть проблемы
                    overall_status = status.get('overall_status', 'unknown')
                    if overall_status != 'healthy':
                        logger.warning(f"⚠️  System status: {overall_status}")
                        
                        # Показываем детальную информацию о проблемах
                        quality_status = status.get('quality_orchestrator', {}).get('orchestrator', {})
                        if quality_status.get('status') != 'active':
                            logger.warning(f"  🔧 Quality Orchestrator: {quality_status.get('status')}")
                        
                        scheduler_status = status.get('scheduler', {}).get('status', 'unknown')
                        if scheduler_status != 'running':
                            logger.warning(f"  ⏰ Scheduler: {scheduler_status}")
        
        except KeyboardInterrupt:
            logger.info("🛑 Received keyboard interrupt")
        except Exception as e:
            logger.error(f"💥 Error in main loop: {e}")
        finally:
            self.running = False
    
    async def stop(self):
        """Остановка системы."""
        try:
            logger.info("🛑 Stopping Employee Monitoring System...")
            
            # Останавливаем оркестратор
            stop_result = await self.orchestrator.stop()
            
            if stop_result.get('status') == 'stopped':
                logger.info("✅ System stopped successfully!")
            else:
                logger.error(f"❌ Failed to stop system: {stop_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"💥 System shutdown failed: {e}")
    
    async def run_manual_task_analysis(self):
        """Ручной запуск анализа задач."""
        logger.info("🔍 Running manual task analysis...")
        result = await self.orchestrator.run_manual_daily_task_analysis()
        
        if result['success']:
            logger.info(f"✅ Task analysis completed. Quality: {result.get('quality_score', 0):.2f}")
        else:
            logger.error(f"❌ Task analysis failed: {result.get('error')}")
        
        return result
    
    async def run_manual_meeting_analysis(self):
        """Ручной запуск анализа протоколов."""
        logger.info("📝 Running manual meeting analysis...")
        result = await self.orchestrator.run_manual_daily_meeting_analysis()
        
        if result['success']:
            logger.info(f"✅ Meeting analysis completed. Quality: {result.get('quality_score', 0):.2f}")
        else:
            logger.error(f"❌ Meeting analysis failed: {result.get('error')}")
        
        return result
    
    async def run_manual_weekly_report(self):
        """Ручной запуск еженедельного отчета."""
        logger.info("📊 Running manual weekly report...")
        result = await self.orchestrator.run_manual_weekly_report()
        
        if result['success']:
            logger.info(f"✅ Weekly report completed. Quality: {result.get('quality_score', 0):.2f}")
            if result.get('published_to_confluence'):
                logger.info(f"🌐 Published to Confluence: {result.get('confluence_url')}")
        else:
            logger.error(f"❌ Weekly report failed: {result.get('error')}")
        
        return result
    
    async def run_all_workflows(self):
        """Запуск всех workflow вручную."""
        logger.info("🚀 Running all workflows manually...")
        result = await self.orchestrator.run_all_workflows()
        
        successful = result.get('summary', {}).get('successful_workflows', 0)
        total = result.get('summary', {}).get('total_workflows', 0)
        
        logger.info(f"📊 Workflows completed: {successful}/{total}")
        
        if successful == total:
            logger.info("✅ All workflows completed successfully!")
        else:
            logger.warning(f"⚠️  {total - successful} workflows failed")
        
        return result
    
    async def get_system_status(self):
        """Получение статуса системы."""
        return await self.orchestrator.get_system_status()
    
    async def get_scheduled_jobs(self):
        """Получение списка запланированных задач."""
        return await self.orchestrator.get_scheduled_jobs()


async def main():
    """Главная функция."""
    try:
        system = EmployeeMonitoringSystemFixed()
        
        # Проверяем аргументы командной строки
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == "task-analysis":
                # Ручной запуск анализа задач
                await system.run_manual_task_analysis()
                return
            
            elif command == "meeting-analysis":
                # Ручной запуск анализа протоколов
                await system.run_manual_meeting_analysis()
                return
            
            elif command == "weekly-report":
                # Ручной запуск еженедельного отчета
                await system.run_manual_weekly_report()
                return
            
            elif command == "run-all":
                # Запуск всех workflow
                await system.run_all_workflows()
                return
            
            elif command == "status":
                # Показать статус системы
                status = await system.get_system_status()
                print("\n=== Employee Monitoring System Status ===")
                print(f"Overall Status: {status.get('overall_status', 'unknown')}")
                print(f"Quality Orchestrator: {status.get('quality_orchestrator', {}).get('orchestrator', {}).get('status', 'unknown')}")
                print(f"Scheduler: {status.get('scheduler', {}).get('status', 'unknown')}")
                
                jobs = await system.get_scheduled_jobs()
                print(f"\nScheduled Jobs ({len(jobs)}):")
                for job in jobs:
                    print(f"  • {job.get('name', 'Unknown')} - {job.get('next_run_time', 'Not scheduled')}")
                return
            
            elif command == "help":
                print("""
Employee Monitoring System (Fixed) - Usage:

  python main_employee_monitoring_fixed.py [COMMAND]

Commands:
  (no args)          Start the system with scheduler
  task-analysis      Run manual task analysis
  meeting-analysis   Run manual meeting analysis  
  weekly-report      Run manual weekly report
  run-all           Run all workflows manually
  status            Show system status
  help              Show this help

Examples:
  python main_employee_monitoring_fixed.py
  python main_employee_monitoring_fixed.py task-analysis
  python main_employee_monitoring_fixed.py status
                """)
                return
            else:
                logger.error(f"Unknown command: {command}")
                logger.info("Use 'help' to see available commands")
                return
        
        # Запуск системы в нормальном режиме
        success = await system.start()
        
        if success:
            # Система будет работать в цикле до получения сигнала остановки
            pass
        
        # Корректная остановка
        await system.stop()
        
    except KeyboardInterrupt:
        logger.info("🛑 Received keyboard interrupt")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
