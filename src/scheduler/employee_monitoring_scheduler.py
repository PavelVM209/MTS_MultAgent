"""
Employee Monitoring Scheduler

Manages scheduled execution of employee monitoring workflows,
handles cron-like scheduling and periodic tasks.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta, time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import schedule

from ..orchestrator.employee_monitoring_orchestrator import EmployeeMonitoringOrchestrator, WorkflowType
from ..core.config import get_employee_monitoring_config

logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """Types of scheduling."""
    DAILY = "daily"
    WEEKLY = "weekly"
    HOURLY = "hourly"
    CUSTOM = "custom"


class TaskStatus(Enum):
    """Scheduled task status."""
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    """Represents a scheduled task."""
    task_id: str
    name: str
    workflow_type: WorkflowType
    schedule_type: ScheduleType
    schedule_expression: str  # cron-like expression
    input_data: Dict[str, Any]
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    status: TaskStatus = TaskStatus.SCHEDULED
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    max_retries: int = 3
    timeout_minutes: int = 60
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class EmployeeMonitoringScheduler:
    """
    Scheduler for Employee Monitoring System.
    
    Manages scheduled execution by:
    - Supporting cron-like scheduling
    - Handling periodic and one-time tasks
    - Managing task dependencies
    - Providing execution monitoring
    - Implementing retry logic and error handling
    """
    
    def __init__(self):
        """Initialize the scheduler."""
        # Load configuration
        self.emp_config = get_employee_monitoring_config()
        self.scheduler_config = self.emp_config.get('scheduler', {})
        
        # Initialize orchestrator
        self.orchestrator = EmployeeMonitoringOrchestrator()
        
        # Scheduling parameters
        self.enabled = self.scheduler_config.get('enabled', True)
        self.timezone = self.scheduler_config.get('timezone', 'UTC')
        self.max_concurrent_tasks = self.scheduler_config.get('max_concurrent_tasks', 5)
        self.default_retry_count = self.scheduler_config.get('default_retry_count', 3)
        self.default_timeout = self.scheduler_config.get('default_timeout', 60)
        
        # Task management
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        
        # Storage
        self.tasks_file = Path(self.emp_config.get('reports', {}).get('scheduler_dir', './reports/scheduler')) / "scheduled_tasks.json"
        self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Background tasks
        self.scheduler_task: Optional[asyncio.Task] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        logger.info("EmployeeMonitoringScheduler initialized")
    
    async def start(self) -> None:
        """Start the scheduler."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        if not self.enabled:
            logger.info("Scheduler is disabled in configuration")
            return
        
        self.is_running = True
        
        # Load saved tasks
        await self._load_scheduled_tasks()
        
        # Create default schedules if none exist
        if not self.scheduled_tasks:
            await self._create_default_schedules()
        
        # Start background tasks
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Employee Monitoring Scheduler started")
    
    async def stop(self) -> None:
        """Stop the scheduler."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel background tasks
        if self.scheduler_task:
            self.scheduler_task.cancel()
        if self.monitoring_task:
            self.monitoring_task.cancel()
        
        # Wait for tasks to complete
        try:
            await asyncio.gather(self.scheduler_task, self.monitoring_task, return_exceptions=True)
        except Exception:
            pass
        
        # Cancel running tasks
        for task_id, task in self.running_tasks.items():
            if not task.done():
                task.cancel()
                logger.info(f"Cancelled running task: {task_id}")
        
        # Save current state
        await self._save_scheduled_tasks()
        
        logger.info("Employee Monitoring Scheduler stopped")
    
    async def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        while self.is_running:
            try:
                # Check for due tasks
                await self._check_and_execute_due_tasks()
                
                # Calculate next run times
                await self._update_next_run_times()
                
                # Sleep for a minute before next check
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)
    
    async def _monitoring_loop(self) -> None:
        """Monitor running tasks and handle timeouts."""
        while self.is_running:
            try:
                # Check for task timeouts
                await self._check_task_timeouts()
                
                # Clean up completed tasks
                await self._cleanup_completed_tasks()
                
                # Sleep for 30 seconds
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)
    
    async def _check_and_execute_due_tasks(self) -> None:
        """Check for tasks that are due to run and execute them."""
        now = datetime.now()
        
        for task_id, task in self.scheduled_tasks.items():
            if (task.enabled and 
                task.status == TaskStatus.SCHEDULED and 
                task.next_run and 
                task.next_run <= now):
                
                # Check concurrent task limit
                if len(self.running_tasks) >= self.max_concurrent_tasks:
                    logger.warning(f"Concurrent task limit reached, skipping {task_id}")
                    continue
                
                # Execute the task
                await self._execute_scheduled_task(task)
    
    async def _execute_scheduled_task(self, task: ScheduledTask) -> None:
        """Execute a scheduled task."""
        if task.task_id in self.running_tasks:
            logger.warning(f"Task {task.task_id} is already running")
            return
        
        logger.info(f"Executing scheduled task: {task.task_id} ({task.name})")
        
        task.status = TaskStatus.RUNNING
        task.last_run = datetime.now()
        task.run_count += 1
        
        # Create async task for execution
        async_task = asyncio.create_task(self._run_task_with_handling(task))
        self.running_tasks[task.task_id] = async_task
    
    async def _run_task_with_handling(self, task: ScheduledTask) -> None:
        """Run a task with error handling and retries."""
        retry_count = 0
        
        while retry_count <= task.max_retries:
            try:
                # Execute the workflow
                execution = await asyncio.wait_for(
                    self.orchestrator.execute_workflow(
                        task.workflow_type,
                        task.input_data,
                        f"{task.task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    ),
                    timeout=task.timeout_minutes * 60
                )
                
                # Check if execution was successful
                if execution.status.value in ['completed']:
                    task.status = TaskStatus.COMPLETED
                    task.success_count += 1
                    logger.info(f"Task completed successfully: {task.task_id}")
                    break
                else:
                    raise RuntimeError(f"Workflow failed with status: {execution.status.value}")
                
            except asyncio.TimeoutError:
                logger.warning(f"Task timeout: {task.task_id} (attempt {retry_count + 1})")
            except Exception as e:
                logger.warning(f"Task failed: {task.task_id} - {str(e)} (attempt {retry_count + 1})")
            
            retry_count += 1
            
            if retry_count <= task.max_retries:
                # Wait before retry
                await asyncio.sleep(60 * retry_count)  # Exponential backoff
        
        if retry_count > task.max_retries:
            task.status = TaskStatus.FAILED
            task.failure_count += 1
            logger.error(f"Task failed after all retries: {task.task_id}")
        
        # Clean up from running tasks
        if task.task_id in self.running_tasks:
            del self.running_tasks[task.task_id]
        
        # Reset status to scheduled if enabled
        if task.enabled and task.status != TaskStatus.FAILED:
            task.status = TaskStatus.SCHEDULED
    
    async def _update_next_run_times(self) -> None:
        """Update next run times for all scheduled tasks."""
        for task in self.scheduled_tasks.values():
            if task.enabled and task.status == TaskStatus.SCHEDULED:
                task.next_run = self._calculate_next_run(task)
    
    def _calculate_next_run(self, task: ScheduledTask) -> Optional[datetime]:
        """Calculate the next run time for a task."""
        now = datetime.now()
        
        if task.schedule_type == ScheduleType.DAILY:
            # Parse schedule expression like "09:00" or "09:00,17:00"
            times = task.schedule_expression.split(',')
            
            for time_str in sorted(times):
                try:
                    hour, minute = map(int, time_str.strip().split(':'))
                    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    if next_run <= now:
                        next_run += timedelta(days=1)
                    
                    return next_run
                except ValueError:
                    continue
            
            # Default to next day at 9 AM if parsing fails
            return now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        elif task.schedule_type == ScheduleType.WEEKLY:
            # Parse schedule expression like "MON:09:00" or "FRI:17:00"
            try:
                parts = task.schedule_expression.split(':')
                if len(parts) >= 3:
                    day_str = parts[0].upper()
                    hour = int(parts[1])
                    minute = int(parts[2])
                    
                    # Map day string to weekday number (0=Monday)
                    day_map = {'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4, 'SAT': 5, 'SUN': 6}
                    target_weekday = day_map.get(day_str[:3], 0)
                    
                    # Find next occurrence of the target weekday
                    current_weekday = now.weekday()
                    days_ahead = (target_weekday - current_weekday) % 7
                    if days_ahead == 0 and now.time() >= time(hour, minute):
                        days_ahead = 7
                    
                    next_run = now + timedelta(days=days_ahead)
                    next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    return next_run
            except (ValueError, IndexError):
                pass
            
            # Default to next Monday at 9 AM if parsing fails
            next_monday = now + timedelta(days=(7 - now.weekday()))
            return next_monday.replace(hour=9, minute=0, second=0, microsecond=0)
        
        elif task.schedule_type == ScheduleType.HOURLY:
            # Run at the start of each hour
            next_run = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            return next_run
        
        return None
    
    async def _check_task_timeouts(self) -> None:
        """Check for tasks that have exceeded their timeout."""
        now = datetime.now()
        
        for task_id, task in self.scheduled_tasks.items():
            if (task.status == TaskStatus.RUNNING and 
                task.last_run and 
                (now - task.last_run).total_seconds() > task.timeout_minutes * 60):
                
                logger.warning(f"Task timeout detected: {task_id}")
                
                # Cancel the running task if it exists
                if task_id in self.running_tasks:
                    self.running_tasks[task_id].cancel()
                    del self.running_tasks[task_id]
                
                # Mark task as failed
                task.status = TaskStatus.FAILED
                task.failure_count += 1
    
    async def _cleanup_completed_tasks(self) -> None:
        """Clean up completed running tasks."""
        completed_tasks = []
        
        for task_id, async_task in self.running_tasks.items():
            if async_task.done():
                completed_tasks.append(task_id)
                
                # Handle task result
                try:
                    result = async_task.result()
                    logger.debug(f"Task {task_id} completed with result: {result}")
                except Exception as e:
                    logger.error(f"Task {task_id} completed with error: {e}")
        
        # Remove completed tasks
        for task_id in completed_tasks:
            del self.running_tasks[task_id]
    
    async def _create_default_schedules(self) -> None:
        """Create default scheduled tasks if none exist."""
        logger.info("Creating default scheduled tasks")
        
        # Daily task analysis at 9 AM and 6 PM
        await self.add_scheduled_task(
            name="Daily Task Analysis - Morning",
            workflow_type=WorkflowType.DAILY_TASK_ANALYSIS,
            schedule_type=ScheduleType.DAILY,
            schedule_expression="09:00",
            input_data={"source": "scheduler", "analysis_type": "daily"}
        )
        
        await self.add_scheduled_task(
            name="Daily Task Analysis - Evening",
            workflow_type=WorkflowType.DAILY_TASK_ANALYSIS,
            schedule_type=ScheduleType.DAILY,
            schedule_expression="18:00",
            input_data={"source": "scheduler", "analysis_type": "daily"}
        )
        
        # Daily meeting analysis at 10 AM
        await self.add_scheduled_task(
            name="Daily Meeting Analysis",
            workflow_type=WorkflowType.DAILY_MEETING_ANALYSIS,
            schedule_type=ScheduleType.DAILY,
            schedule_expression="10:00",
            input_data={"source": "scheduler", "analysis_type": "daily"}
        )
        
        # Weekly report every Friday at 5 PM
        await self.add_scheduled_task(
            name="Weekly Report Generation",
            workflow_type=WorkflowType.WEEKLY_REPORT_GENERATION,
            schedule_type=ScheduleType.WEEKLY,
            schedule_expression="FRI:17:00",
            input_data={"source": "scheduler", "analysis_type": "weekly"}
        )
    
    async def add_scheduled_task(
        self,
        name: str,
        workflow_type: WorkflowType,
        schedule_type: ScheduleType,
        schedule_expression: str,
        input_data: Dict[str, Any],
        enabled: bool = True,
        max_retries: Optional[int] = None,
        timeout_minutes: Optional[int] = None
    ) -> str:
        """
        Add a new scheduled task.
        
        Args:
            name: Human-readable name for the task
            workflow_type: Type of workflow to execute
            schedule_type: Type of scheduling
            schedule_expression: Schedule expression
            input_data: Input data for the workflow
            enabled: Whether the task is enabled
            max_retries: Maximum number of retries
            timeout_minutes: Timeout in minutes
            
        Returns:
            Task ID
        """
        task_id = f"{workflow_type.value}_{name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            workflow_type=workflow_type,
            schedule_type=schedule_type,
            schedule_expression=schedule_expression,
            input_data=input_data,
            enabled=enabled,
            max_retries=max_retries or self.default_retry_count,
            timeout_minutes=timeout_minutes or self.default_timeout
        )
        
        # Calculate next run time
        task.next_run = self._calculate_next_run(task)
        
        # Add to scheduled tasks
        self.scheduled_tasks[task_id] = task
        
        # Save to file
        await self._save_scheduled_tasks()
        
        logger.info(f"Added scheduled task: {task_id} ({name}) - Next run: {task.next_run}")
        
        return task_id
    
    async def remove_scheduled_task(self, task_id: str) -> bool:
        """Remove a scheduled task."""
        if task_id not in self.scheduled_tasks:
            return False
        
        # Cancel if running
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            del self.running_tasks[task_id]
        
        # Remove from scheduled tasks
        del self.scheduled_tasks[task_id]
        
        # Save to file
        await self._save_scheduled_tasks()
        
        logger.info(f"Removed scheduled task: {task_id}")
        
        return True
    
    async def enable_task(self, task_id: str) -> bool:
        """Enable a scheduled task."""
        if task_id not in self.scheduled_tasks:
            return False
        
        task = self.scheduled_tasks[task_id]
        task.enabled = True
        task.next_run = self._calculate_next_run(task)
        
        await self._save_scheduled_tasks()
        
        logger.info(f"Enabled scheduled task: {task_id}")
        
        return True
    
    async def disable_task(self, task_id: str) -> bool:
        """Disable a scheduled task."""
        if task_id not in self.scheduled_tasks:
            return False
        
        task = self.scheduled_tasks[task_id]
        task.enabled = False
        
        # Cancel if running
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            del self.running_tasks[task_id]
        
        await self._save_scheduled_tasks()
        
        logger.info(f"Disabled scheduled task: {task_id}")
        
        return True
    
    async def get_scheduled_tasks(self) -> List[ScheduledTask]:
        """Get all scheduled tasks."""
        return list(self.scheduled_tasks.values())
    
    async def get_task_status(self, task_id: str) -> Optional[ScheduledTask]:
        """Get the status of a specific task."""
        return self.scheduled_tasks.get(task_id)
    
    async def get_scheduler_status(self) -> Dict[str, Any]:
        """Get overall scheduler status."""
        total_tasks = len(self.scheduled_tasks)
        enabled_tasks = len([t for t in self.scheduled_tasks.values() if t.enabled])
        running_tasks = len(self.running_tasks)
        
        success_rate = 0.0
        if self.scheduled_tasks:
            total_runs = sum(t.run_count for t in self.scheduled_tasks.values())
            total_successes = sum(t.success_count for t in self.scheduled_tasks.values())
            success_rate = total_successes / max(total_runs, 1)
        
        return {
            'scheduler_status': 'running' if self.is_running else 'stopped',
            'enabled': self.enabled,
            'total_tasks': total_tasks,
            'enabled_tasks': enabled_tasks,
            'running_tasks': running_tasks,
            'success_rate': success_rate,
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'timezone': self.timezone,
            'last_check': datetime.now().isoformat()
        }
    
    async def _load_scheduled_tasks(self) -> None:
        """Load scheduled tasks from file."""
        try:
            if self.tasks_file.exists():
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    tasks_data = json.load(f)
                
                for task_data in tasks_data:
                    # Convert dict back to ScheduledTask
                    task = ScheduledTask(
                        task_id=task_data['task_id'],
                        name=task_data['name'],
                        workflow_type=WorkflowType(task_data['workflow_type']),
                        schedule_type=ScheduleType(task_data['schedule_type']),
                        schedule_expression=task_data['schedule_expression'],
                        input_data=task_data['input_data'],
                        enabled=task_data.get('enabled', True),
                        last_run=datetime.fromisoformat(task_data['last_run']) if task_data.get('last_run') else None,
                        next_run=datetime.fromisoformat(task_data['next_run']) if task_data.get('next_run') else None,
                        status=TaskStatus(task_data.get('status', 'scheduled')),
                        run_count=task_data.get('run_count', 0),
                        success_count=task_data.get('success_count', 0),
                        failure_count=task_data.get('failure_count', 0),
                        max_retries=task_data.get('max_retries', 3),
                        timeout_minutes=task_data.get('timeout_minutes', 60),
                        created_at=datetime.fromisoformat(task_data['created_at']) if task_data.get('created_at') else datetime.now(),
                        metadata=task_data.get('metadata', {})
                    )
                    
                    self.scheduled_tasks[task.task_id] = task
                
                logger.info(f"Loaded {len(self.scheduled_tasks)} scheduled tasks from file")
            
        except Exception as e:
            logger.error(f"Failed to load scheduled tasks: {e}")
    
    async def _save_scheduled_tasks(self) -> None:
        """Save scheduled tasks to file."""
        try:
            tasks_data = []
            
            for task in self.scheduled_tasks.values():
                task_dict = {
                    'task_id': task.task_id,
                    'name': task.name,
                    'workflow_type': task.workflow_type.value,
                    'schedule_type': task.schedule_type.value,
                    'schedule_expression': task.schedule_expression,
                    'input_data': task.input_data,
                    'enabled': task.enabled,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'next_run': task.next_run.isoformat() if task.next_run else None,
                    'status': task.status.value,
                    'run_count': task.run_count,
                    'success_count': task.success_count,
                    'failure_count': task.failure_count,
                    'max_retries': task.max_retries,
                    'timeout_minutes': task.timeout_minutes,
                    'created_at': task.created_at.isoformat() if task.created_at else datetime.now().isoformat(),
                    'metadata': task.metadata
                }
                tasks_data.append(task_dict)
            
            # Save to JSON file
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved {len(tasks_data)} scheduled tasks to file")
            
        except Exception as e:
            logger.error(f"Failed to save scheduled tasks: {e}")
    
    async def run_task_now(self, task_id: str) -> bool:
        """Run a scheduled task immediately."""
        if task_id not in self.scheduled_tasks:
            return False
        
        task = self.scheduled_tasks[task_id]
        
        # Create a copy of the task for immediate execution
        immediate_task = ScheduledTask(
            task_id=f"{task.task_id}_immediate_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=f"Immediate: {task.name}",
            workflow_type=task.workflow_type,
            schedule_type=task.schedule_type,
            schedule_expression=task.schedule_expression,
            input_data=task.input_data,
            enabled=True,
            max_retries=task.max_retries,
            timeout_minutes=task.timeout_minutes,
            metadata=task.metadata
        )
        
        # Execute immediately
        await self._execute_scheduled_task(immediate_task)
        
        logger.info(f"Executed task immediately: {task_id}")
        
        return True
    
    async def get_task_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get task execution history."""
        # This would typically load from a more comprehensive logging system
        # For now, return current task information
        history = []
        
        for task in self.scheduled_tasks.values():
            history.append({
                'task_id': task.task_id,
                'name': task.name,
                'last_run': task.last_run.isoformat() if task.last_run else None,
                'status': task.status.value,
                'run_count': task.run_count,
                'success_count': task.success_count,
                'failure_count': task.failure_count
            })
        
        # Sort by last run time
        history.sort(key=lambda x: x['last_run'] or '', reverse=True)
        
        return history[:limit]
