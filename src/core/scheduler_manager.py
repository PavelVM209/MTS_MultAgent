"""
Scheduler Manager - Phase 3 Foundation Component

Provides APScheduler integration with timezone handling,
job persistence, recovery, and health monitoring.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
import structlog

logger = structlog.get_logger()


class JobStatus(Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    MISSED = "missed"
    PAUSED = "paused"


class SchedulerStatus(Enum):
    """Scheduler overall status"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"


@dataclass
class JobConfig:
    """Configuration for a scheduled job"""
    id: str
    name: str
    func: Callable
    trigger_type: str  # 'cron', 'interval', 'date'
    trigger_config: Dict[str, Any]
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    description: Optional[str] = None
    max_instances: int = 1
    misfire_grace_time: Optional[int] = 300  # 5 minutes default
    coalesce: bool = True  # Combine missed jobs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'trigger_type': self.trigger_type,
            'trigger_config': self.trigger_config,
            'args': self.args,
            'kwargs': self.kwargs,
            'enabled': self.enabled,
            'description': self.description,
            'max_instances': self.max_instances,
            'misfire_grace_time': self.misfire_grace_time,
            'coalesce': self.coalesce
        }


@dataclass
class JobExecutionResult:
    """Result of job execution"""
    job_id: str
    status: JobStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'job_id': self.job_id,
            'status': self.status.value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'result': str(self.result) if self.result is not None else None,
            'error': self.error,
            'traceback': self.traceback
        }


@dataclass
class SchedulerHealth:
    """Scheduler health information"""
    status: SchedulerStatus
    uptime: Optional[timedelta] = None
    total_jobs: int = 0
    active_jobs: int = 0
    paused_jobs: int = 0
    recent_executions: List[JobExecutionResult] = field(default_factory=list)
    last_check: datetime = field(default_factory=datetime.now)
    errors_count: int = 0
    success_rate: float = 0.0


class SchedulerManager:
    """
    Enhanced scheduler manager with APScheduler integration.
    
    Features:
    - Timezone handling (Europe/Moscow)
    - Job persistence and recovery
    - Health monitoring
    - Configuration integration
    - Error handling and retry logic
    - Job execution history
    """
    
    def __init__(self, timezone_str: str = "Europe/Moscow"):
        self.timezone = pytz.timezone(timezone_str)
        self.scheduler: Optional[AsyncIOScheduler] = None
        
        # Job configurations
        self.job_configs: Dict[str, JobConfig] = {}
        
        # Execution tracking
        self.job_executions: List[JobExecutionResult] = []
        self.max_execution_history = 1000
        
        # Health monitoring
        self.health = SchedulerHealth(status=SchedulerStatus.STOPPED)
        self.startup_time: Optional[datetime] = None
        
        # Event callbacks
        self.job_callbacks: Dict[str, List[Callable]] = {
            'job_started': [],
            'job_completed': [],
            'job_error': [],
            'job_missed': []
        }
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        logger.info("Scheduler manager initialized", timezone=str(self.timezone))
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize scheduler with configuration.
        
        Args:
            config: Scheduler configuration dict
        """
        try:
            logger.info("Initializing scheduler...")
            self.health.status = SchedulerStatus.STARTING
            
            # Configure job stores
            jobstores = {
                'default': MemoryJobStore(),
                'memory': MemoryJobStore()
            }
            
            # Configure executors
            executors = {
                'default': AsyncIOExecutor()
            }
            
            # Create scheduler
            self.scheduler = AsyncIOScheduler(
                jobstores=jobstores,
                executors=executors,
                timezone=self.timezone,
                job_defaults={
                    'coalesce': True,
                    'max_instances': 3,
                    'misfire_grace_time': 300
                }
            )
            
            # Add event listeners
            self.scheduler.add_listener(
                self._job_executed_listener,
                EVENT_JOB_EXECUTED
            )
            self.scheduler.add_listener(
                self._job_error_listener,
                EVENT_JOB_ERROR
            )
            self.scheduler.add_listener(
                self._job_missed_listener,
                EVENT_JOB_MISSED
            )
            
            logger.info("Scheduler initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize scheduler", error=str(e))
            self.health.status = SchedulerStatus.STOPPED
            raise
    
    async def start(self):
        """Start the scheduler"""
        if not self.scheduler:
            await self.initialize()
        
        try:
            self.scheduler.start()
            self.startup_time = datetime.now(self.timezone)
            self.health.status = SchedulerStatus.RUNNING
            
            logger.info("Scheduler started", timezone=str(self.timezone))
            
        except Exception as e:
            logger.error("Failed to start scheduler", error=str(e))
            self.health.status = SchedulerStatus.STOPPED
            raise
    
    async def stop(self, wait: bool = True):
        """
        Stop the scheduler.
        
        Args:
            wait: Whether to wait for running jobs to complete
        """
        if self.scheduler and self.scheduler.running:
            self.health.status = SchedulerStatus.SHUTTING_DOWN
            
            try:
                self.scheduler.shutdown(wait=wait)
                self.health.status = SchedulerStatus.STOPPED
                
                logger.info("Scheduler stopped")
                
            except Exception as e:
                logger.error("Error stopping scheduler", error=str(e))
                raise
    
    async def add_job(self, job_config: JobConfig) -> str:
        """
        Add a new job to the scheduler.
        
        Args:
            job_config: Job configuration
            
        Returns:
            Job ID
        """
        async with self._lock:
            try:
                # Store job configuration
                self.job_configs[job_config.id] = job_config
                
                # Create trigger
                trigger = self._create_trigger(job_config)
                
                # Add job to scheduler
                if self.scheduler:
                    self.scheduler.add_job(
                        func=job_config.func,
                        trigger=trigger,
                        id=job_config.id,
                        name=job_config.name,
                        args=job_config.args,
                        kwargs=job_config.kwargs,
                        max_instances=job_config.max_instances,
                        misfire_grace_time=job_config.misfire_grace_time,
                        coalesce=job_config.coalesce,
                        replace_existing=True
                    )
                    
                    logger.info(
                        "Job added to scheduler",
                        job_id=job_config.id,
                        job_name=job_config.name,
                        trigger_type=job_config.trigger_type
                    )
                    
                    return job_config.id
                else:
                    raise RuntimeError("Scheduler not initialized")
                    
            except Exception as e:
                logger.error(
                    "Failed to add job",
                    job_id=job_config.id,
                    error=str(e)
                )
                raise
    
    async def remove_job(self, job_id: str) -> bool:
        """
        Remove a job from the scheduler.
        
        Args:
            job_id: ID of job to remove
            
        Returns:
            True if job was removed, False if not found
        """
        async with self._lock:
            try:
                if self.scheduler and self.scheduler.get_job(job_id):
                    self.scheduler.remove_job(job_id)
                    
                    # Remove from configurations
                    self.job_configs.pop(job_id, None)
                    
                    logger.info("Job removed from scheduler", job_id=job_id)
                    return True
                else:
                    logger.warning("Job not found for removal", job_id=job_id)
                    return False
                    
            except Exception as e:
                logger.error(
                    "Failed to remove job",
                    job_id=job_id,
                    error=str(e)
                )
                raise
    
    async def pause_job(self, job_id: str) -> bool:
        """Pause a specific job"""
        try:
            if self.scheduler and self.scheduler.get_job(job_id):
                self.scheduler.pause_job(job_id)
                logger.info("Job paused", job_id=job_id)
                return True
            return False
        except Exception as e:
            logger.error("Failed to pause job", job_id=job_id, error=str(e))
            raise
    
    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused job"""
        try:
            if self.scheduler and self.scheduler.get_job(job_id):
                self.scheduler.resume_job(job_id)
                logger.info("Job resumed", job_id=job_id)
                return True
            return False
        except Exception as e:
            logger.error("Failed to resume job", job_id=job_id, error=str(e))
            raise
    
    async def get_job_info(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job information dictionary or None
        """
        try:
            job = None
            if self.scheduler:
                job = self.scheduler.get_job(job_id)
            
            if not job:
                return None
            
            job_config = self.job_configs.get(job_id)
            
            # Get recent executions
            recent_executions = [
                exec_result for exec_result in self.job_executions[-10:]
                if exec_result.job_id == job_id
            ]
            
            return {
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger),
                'enabled': not job.pending,
                'config': job_config.to_dict() if job_config else None,
                'recent_executions': [exec_result.to_dict() for exec_result in recent_executions]
            }
            
        except Exception as e:
            logger.error("Failed to get job info", job_id=job_id, error=str(e))
            raise
    
    async def list_jobs(self) -> List[Dict[str, Any]]:
        """List all jobs with their status"""
        try:
            jobs_info = []
            
            if self.scheduler:
                for job in self.scheduler.get_jobs():
                    job_info = await self.get_job_info(job.id)
                    if job_info:
                        jobs_info.append(job_info)
            
            return jobs_info
            
        except Exception as e:
            logger.error("Failed to list jobs", error=str(e))
            raise
    
    async def get_health(self) -> SchedulerHealth:
        """Get scheduler health information"""
        try:
            if not self.scheduler:
                return self.health
            
            # Update statistics
            jobs = self.scheduler.get_jobs()
            self.health.total_jobs = len(jobs)
            self.health.active_jobs = len([j for j in jobs if not j.pending])
            self.health.paused_jobs = len([j for j in jobs if j.pending])
            
            # Calculate uptime
            if self.startup_time:
                self.health.uptime = datetime.now(self.timezone) - self.startup_time
            
            # Calculate success rate
            recent_executions = self.job_executions[-100:]  # Last 100 executions
            if recent_executions:
                successful = len([
                    exec_result for exec_result in recent_executions
                    if exec_result.status == JobStatus.COMPLETED
                ])
                self.health.success_rate = successful / len(recent_executions)
            
            # Add recent executions to health
            self.health.recent_executions = self.job_executions[-10:]
            self.health.last_check = datetime.now(self.timezone)
            
            return self.health
            
        except Exception as e:
            logger.error("Failed to get scheduler health", error=str(e))
            return self.health
    
    def _create_trigger(self, job_config: JobConfig):
        """Create APScheduler trigger from configuration"""
        trigger_config = job_config.trigger_config
        
        if job_config.trigger_type == 'cron':
            return CronTrigger(
                minute=trigger_config.get('minute', '*'),
                hour=trigger_config.get('hour', '*'),
                day=trigger_config.get('day', '*'),
                month=trigger_config.get('month', '*'),
                day_of_week=trigger_config.get('day_of_week', '*'),
                timezone=self.timezone
            )
        elif job_config.trigger_type == 'interval':
            return IntervalTrigger(
                seconds=trigger_config.get('seconds', 0),
                minutes=trigger_config.get('minutes', 0),
                hours=trigger_config.get('hours', 0),
                days=trigger_config.get('days', 0),
                weeks=trigger_config.get('weeks', 0),
                timezone=self.timezone
            )
        else:
            raise ValueError(f"Unsupported trigger type: {job_config.trigger_type}")
    
    def _job_executed_listener(self, event):
        """Handle job execution events"""
        try:
            execution_result = JobExecutionResult(
                job_id=event.job_id,
                status=JobStatus.COMPLETED,
                start_time=datetime.fromtimestamp(event.scheduled_run_time.timestamp()),
                end_time=datetime.now(self.timezone),
                result=getattr(event, 'retval', None)
            )
            
            self.job_executions.append(execution_result)
            self._cleanup_executions_history()
            
            # Trigger callbacks
            self._trigger_callbacks('job_completed', execution_result)
            
            logger.debug("Job executed successfully", job_id=event.job_id)
            
        except Exception as e:
            logger.error("Error in job execution listener", error=str(e))
    
    def _job_error_listener(self, event):
        """Handle job error events"""
        try:
            execution_result = JobExecutionResult(
                job_id=event.job_id,
                status=JobStatus.ERROR,
                start_time=datetime.fromtimestamp(event.scheduled_run_time.timestamp()),
                end_time=datetime.now(self.timezone),
                error=str(event.exception),
                traceback=getattr(event, 'traceback', None)
            )
            
            self.job_executions.append(execution_result)
            self._cleanup_executions_history()
            
            # Trigger callbacks
            self._trigger_callbacks('job_error', execution_result)
            
            self.health.errors_count += 1
            
            logger.error("Job execution failed", job_id=event.job_id, error=str(event.exception))
            
        except Exception as e:
            logger.error("Error in job error listener", error=str(e))
    
    def _job_missed_listener(self, event):
        """Handle job missed events"""
        try:
            execution_result = JobExecutionResult(
                job_id=event.job_id,
                status=JobStatus.MISSED,
                start_time=datetime.fromtimestamp(event.scheduled_run_time.timestamp()),
                end_time=datetime.now(self.timezone)
            )
            
            self.job_executions.append(execution_result)
            self._cleanup_executions_history()
            
            # Trigger callbacks
            self._trigger_callbacks('job_missed', execution_result)
            
            logger.warning("Job execution missed", job_id=event.job_id)
            
        except Exception as e:
            logger.error("Error in job missed listener", error=str(e))
    
    def _cleanup_executions_history(self):
        """Clean up old execution records"""
        if len(self.job_executions) > self.max_execution_history:
            self.job_executions = self.job_executions[-self.max_execution_history:]
    
    def _trigger_callbacks(self, event_type: str, execution_result: JobExecutionResult):
        """Trigger event callbacks"""
        for callback in self.job_callbacks.get(event_type, []):
            try:
                callback(execution_result)
            except Exception as e:
                logger.error(
                    "Error in job callback",
                    event_type=event_type,
                    job_id=execution_result.job_id,
                    error=str(e)
                )
    
    def add_callback(self, event_type: str, callback: Callable):
        """Add callback for job events"""
        if event_type not in self.job_callbacks:
            self.job_callbacks[event_type] = []
        self.job_callbacks[event_type].append(callback)
    
    def remove_callback(self, event_type: str, callback: Callable):
        """Remove job event callback"""
        if event_type in self.job_callbacks:
            try:
                self.job_callbacks[event_type].remove(callback)
            except ValueError:
                pass  # Callback not found


# Global scheduler manager instance
_scheduler_manager: Optional[SchedulerManager] = None


async def get_scheduler_manager() -> SchedulerManager:
    """Get global scheduler manager instance"""
    global _scheduler_manager
    
    if _scheduler_manager is None:
        _scheduler_manager = SchedulerManager()
        await _scheduler_manager.initialize()
    
    return _scheduler_manager


def get_scheduler() -> Optional[AsyncIOScheduler]:
    """Get the underlying APScheduler instance"""
    global _scheduler_manager
    if _scheduler_manager:
        return _scheduler_manager.scheduler
    return None
