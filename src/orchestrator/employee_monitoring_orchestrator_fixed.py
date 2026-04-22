# -*- coding: utf-8 -*-
"""
Employee Monitoring Orchestrator - Fixed Version

Главный оркестратор системы Employee Monitoring с новым QualityOrchestrator.
Реализует правильную архитектуру согласно первоначальным требованиям.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..agents.quality_orchestrator import QualityOrchestrator
from ..core.scheduler_manager import SchedulerManager, JobConfig
from ..core.config import get_employee_monitoring_config

logger = logging.getLogger(__name__)


class EmployeeMonitoringOrchestratorFixed:
    """
    Главный оркестратор Employee Monitoring System.
    
    Новая архитектура:
    1. QualityOrchestrator - главный компонент с контролем качества
    2. Координирует все workflow с валидацией на каждом шаге
    3. Управляет планированием через SchedulerManager
    """
    
    def __init__(self):
        """Инициализация оркестратора."""
        self.emp_config = get_employee_monitoring_config()
        self.quality_orchestrator = QualityOrchestrator()
        self.scheduler_manager = SchedulerManager()
        
        # Параметры планирования
        self.daily_task_time = self.emp_config.get('scheduling', {}).get('daily_task_time', '22:55')
        self.daily_meeting_time = self.emp_config.get('scheduling', {}).get('daily_meeting_time', '22:57')
        self.weekly_report_time = self.emp_config.get('scheduling', {}).get('weekly_report_time', '22:58')
        self.weekly_report_day = self.emp_config.get('scheduling', {}).get('weekly_report_day', 'sunday')
        
        logger.info("EmployeeMonitoringOrchestrator initialized with QualityOrchestrator")
    
    async def start(self) -> Dict[str, Any]:
        """Запуск системы и расписание задач."""
        try:
            logger.info("Starting Employee Monitoring System")
            
            # Проверяем состояние системы
            system_status = await self.quality_orchestrator.get_system_status()
            logger.info(f"System status: {system_status}")
            
            # Инициализируем и запускаем планировщик
            await self.scheduler_manager.initialize()
            scheduler_result = await self.scheduler_manager.start()
            
            # Настраиваем расписание
            await self._setup_schedules()
            
            logger.info("Employee Monitoring System started successfully")
            
            return {
                'status': 'started',
                'system_status': system_status,
                'scheduler_status': scheduler_result,
                'schedules_configured': True,
                'started_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to start Employee Monitoring System: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'started_at': datetime.now().isoformat()
            }
    
    async def _setup_schedules(self):
        """Настройка расписания выполнения задач."""
        try:
            # Ежедневный анализ задач
            daily_task_job = JobConfig(
                id='daily_task_analysis',
                name='Daily Task Analysis (Jira)',
                func=self._run_daily_task_workflow,
                trigger_type='cron',
                trigger_config={
                    'hour': int(self.daily_task_time.split(':')[0]),
                    'minute': int(self.daily_task_time.split(':')[1])
                },
                max_instances=1
            )
            await self.scheduler_manager.add_job(daily_task_job)
            
            # Ежедневный анализ протоколов
            daily_meeting_job = JobConfig(
                id='daily_meeting_analysis',
                name='Daily Meeting Analysis',
                func=self._run_daily_meeting_workflow,
                trigger_type='cron',
                trigger_config={
                    'hour': int(self.daily_meeting_time.split(':')[0]),
                    'minute': int(self.daily_meeting_time.split(':')[1])
                },
                max_instances=1
            )
            await self.scheduler_manager.add_job(daily_meeting_job)
            
            # Еженедельный отчет (в пятницу вечером)
            weekday_map = {
                'monday': 0,
                'tuesday': 1,
                'wednesday': 2,
                'thursday': 3,
                'friday': 4,
                'saturday': 5,
                'sunday': 6
            }
            
            weekday = weekday_map.get(self.weekly_report_day.lower(), 4)  # по умолчанию пятница
            
            weekly_job = JobConfig(
                id='weekly_report',
                name='Weekly Report Generation and Confluence Publishing',
                func=self._run_weekly_workflow,
                trigger_type='cron',
                trigger_config={
                    'day_of_week': weekday,
                    'hour': int(self.weekly_report_time.split(':')[0]),
                    'minute': int(self.weekly_report_time.split(':')[1])
                },
                max_instances=1
            )
            await self.scheduler_manager.add_job(weekly_job)
            
            logger.info("Schedules configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup schedules: {e}")
            raise
    
    async def _run_daily_task_workflow(self):
        """Запуск ежедневного анализа задач через QualityOrchestrator."""
        try:
            logger.info("Starting scheduled daily task analysis workflow")
            
            result = await self.quality_orchestrator.execute_daily_task_workflow()
            
            if result['success']:
                logger.info(f"Daily task analysis completed successfully. Quality score: {result.get('quality_score', 0):.2f}")
            else:
                logger.error(f"Daily task analysis failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Daily task workflow error: {e}")
            return {
                'success': False,
                'error': str(e),
                'workflow_type': 'daily_tasks'
            }
    
    async def _run_daily_meeting_workflow(self):
        """Запуск ежедневного анализа протоколов через QualityOrchestrator."""
        try:
            logger.info("Starting scheduled daily meeting analysis workflow")
            
            result = await self.quality_orchestrator.execute_daily_meeting_workflow()
            
            if result['success']:
                logger.info(f"Daily meeting analysis completed successfully. Quality score: {result.get('quality_score', 0):.2f}")
            else:
                logger.error(f"Daily meeting analysis failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Daily meeting workflow error: {e}")
            return {
                'success': False,
                'error': str(e),
                'workflow_type': 'daily_meetings'
            }
    
    async def _run_weekly_workflow(self):
        """Запуск еженедельного отчета через QualityOrchestrator."""
        try:
            logger.info("Starting scheduled weekly report workflow")
            
            result = await self.quality_orchestrator.execute_weekly_workflow()
            
            if result['success']:
                logger.info(f"Weekly report completed successfully. Quality score: {result.get('quality_score', 0):.2f}")
                
                if result.get('published_to_confluence'):
                    logger.info(f"Weekly report published to Confluence: {result.get('confluence_url', 'Unknown URL')}")
                else:
                    logger.warning("Weekly report was not published to Confluence")
            else:
                logger.error(f"Weekly report failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Weekly workflow error: {e}")
            return {
                'success': False,
                'error': str(e),
                'workflow_type': 'weekly_report'
            }
    
    async def run_manual_daily_task_analysis(self) -> Dict[str, Any]:
        """Ручной запуск ежедневного анализа задач."""
        return await self._run_daily_task_workflow()
    
    async def run_manual_daily_meeting_analysis(self) -> Dict[str, Any]:
        """Ручной запуск ежедневного анализа протоколов."""
        return await self._run_daily_meeting_workflow()
    
    async def run_manual_weekly_report(self) -> Dict[str, Any]:
        """Ручной запуск еженедельного отчета."""
        return await self._run_weekly_workflow()
    
    async def run_all_workflows(self) -> Dict[str, Any]:
        """Запуск всех workflow вручную."""
        try:
            logger.info("Running all workflows manually")
            start_time = datetime.now()
            
            # Запускаем все workflow
            task_result = await self._run_daily_task_workflow()
            meeting_result = await self._run_daily_meeting_workflow()
            weekly_result = await self._run_weekly_workflow()
            
            execution_time = datetime.now() - start_time
            
            results = {
                'execution_time_seconds': execution_time.total_seconds(),
                'workflows': {
                    'daily_tasks': task_result,
                    'daily_meetings': meeting_result,
                    'weekly_report': weekly_result
                },
                'summary': {
                    'total_workflows': 3,
                    'successful_workflows': sum(1 for result in [task_result, meeting_result, weekly_result] 
                                              if result.get('success', False)),
                    'failed_workflows': sum(1 for result in [task_result, meeting_result, weekly_result] 
                                          if not result.get('success', False))
                }
            }
            
            logger.info(f"All workflows completed in {execution_time.total_seconds():.2f}s")
            return results
            
        except Exception as e:
            logger.error(f"Failed to run all workflows: {e}")
            return {
                'error': str(e),
                'execution_time_seconds': (datetime.now() - start_time).total_seconds()
            }
    
    async def stop(self) -> Dict[str, Any]:
        """Остановка системы."""
        try:
            logger.info("Stopping Employee Monitoring System")
            
            # Останавливаем планировщик
            scheduler_result = await self.scheduler_manager.stop()
            
            logger.info("Employee Monitoring System stopped successfully")
            
            return {
                'status': 'stopped',
                'scheduler_status': scheduler_result,
                'stopped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to stop Employee Monitoring System: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'stopped_at': datetime.now().isoformat()
            }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса всей системы."""
        try:
            # Статус системы через QualityOrchestrator
            system_status = await self.quality_orchestrator.get_system_status()
            
            # Статус планировщика
            scheduler_health = await self.scheduler_manager.get_health()
            scheduler_status = {
                'status': 'running' if scheduler_health.status.value == 'running' else 'stopped',
                'total_jobs': scheduler_health.total_jobs,
                'active_jobs': scheduler_health.active_jobs,
                'uptime': scheduler_health.uptime.total_seconds() if scheduler_health.uptime else 0
            }
            
            # Статус оркестратора
            orchestrator_status = {
                'status': 'running',
                'scheduling': {
                    'daily_task_time': self.daily_task_time,
                    'daily_meeting_time': self.daily_meeting_time,
                    'weekly_report_time': self.weekly_report_time,
                    'weekly_report_day': self.weekly_report_day
                },
                'last_check': datetime.now().isoformat()
            }
            
            return {
                'orchestrator': orchestrator_status,
                'quality_orchestrator': system_status,
                'scheduler': scheduler_status,
                'overall_status': 'healthy' if (
                    system_status.get('orchestrator', {}).get('status') == 'active' and
                    scheduler_status.get('status') == 'running'
                ) else 'degraded',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """Получение списка запланированных задач."""
        try:
            return await self.scheduler_manager.list_jobs()
        except Exception as e:
            logger.error(f"Failed to get scheduled jobs: {e}")
            return []
    
    async def add_custom_job(self, func: callable, trigger_type: str, trigger_config: Dict[str, Any]) -> bool:
        """Добавление кастомной задачи в расписание."""
        try:
            await self.scheduler_manager.add_job(func, trigger_type, trigger_config)
            logger.info(f"Custom job added with trigger: {trigger_type}")
            return True
        except Exception as e:
            logger.error(f"Failed to add custom job: {e}")
            return False
    
    async def remove_job(self, job_id: str) -> bool:
        """Удаление задачи из расписания."""
        try:
            await self.scheduler_manager.remove_job(job_id)
            logger.info(f"Job {job_id} removed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {e}")
            return False
    
    async def pause_job(self, job_id: str) -> bool:
        """Пауза задачи."""
        try:
            await self.scheduler_manager.pause_job(job_id)
            logger.info(f"Job {job_id} paused successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to pause job {job_id}: {e}")
            return False
    
    async def resume_job(self, job_id: str) -> bool:
        """Возобновление задачи."""
        try:
            await self.scheduler_manager.resume_job(job_id)
            logger.info(f"Job {job_id} resumed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to resume job {job_id}: {e}")
            return False
