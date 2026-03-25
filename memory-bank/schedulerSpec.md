# Scheduler Specification - MTS MultAgent Scheduled System

## 🕒 **Scheduler Architecture Overview**

**Component:** APScheduler Integration  
**Purpose:** Automated execution of multi-agent workflows  
**Timezone:** Europe/Moscow (UTC+3)  
**Execution Model:** Scheduled + Event-driven  

---

## 🔄 **SCHEDULER COMPONENT ARCHITECTURE**

### **Core Components:**
```python
# src/core/scheduler.py
class TaskScheduler:
    """
    Центральный планировщик для всех scheduled операций
    """
    scheduler: AsyncIOScheduler
    orchestrator: OrchestratorAgent
    config: SchedulerConfig
    
    async def start_scheduler(self) -> None:
        """Запуск планировщика с all scheduled jobs"""
        
    async def add_daily_jobs(self) -> None:
        """Добавление ежедневных задач"""
        
    async def add_weekly_jobs(self) -> None:
        """Добавление недельных задач"""
        
    async def add_health_checks(self) -> None:
        """Добавление health monitoring"""
```

### **Configuration Management:**
```python
# src/core/scheduler_config.py
class SchedulerConfig:
    """
    Конфигурация всех scheduled параметров
    """
    
    daily_workflow_time: str = "19:00"
    weekly_workflow_day: str = "friday"
    weekly_workflow_time: str = "19:00"
    scheduler_timezone: str = "Europe/Moscow"
    
    # Quality and retry parameters
    max_retry_attempts: int = 3
    retry_delay_seconds: int = 300
    quality_threshold: float = 90.0
    
    # Health monitoring
    health_check_interval: int = 3600
    notification_email: str = "admin@company.com"
```

---

## 📅 **SCHEDULE DEFINITIONS**

### **1. Daily Jira Analysis Job**
```python
async def daily_jira_analysis_job():
    """
    Ежедневный анализ Jira проектов
    Запуск: 19:00 UTC+3 каждый день
    """
    try:
        result = await orchestrator.daily_jira_analyzer.execute({
            "execution_type": "scheduled",
            "target_projects": config.project_keys,
            "analysis_depth": "employee_metrics"
        })
        
        # Quality validation
        quality = await quality_controller.validate_agent_result(result)
        
        if quality.overall_quality < 90.0:
            await handle_quality_issue("daily_jira_analysis", quality)
        else:
            await log_success("Daily Jira analysis completed", quality)
            
    except Exception as e:
        await handle_job_error("daily_jira_analysis", e)
        await schedule_retry_if_needed("daily_jira_analysis", e)
```

**Job Configuration:**
```yaml
daily_jira_job:
  trigger: "cron"
  hour: 19
  minute: 0
  timezone: "Europe/Moscow"
  max_instances: 1
  coalesce: true
  misfire_grace_time: 300  # 5 minutes
  retry_delay: 300
  max_retries: 3
```

### **2. Daily Meeting Analysis Job**
```python
async def daily_meeting_analysis_job():
    """
    Ежедневный анализ протоколов совещаний
    Запуск: 19:00 UTC+3 каждый день (параллельно с Jira)
    """
    try:
        result = await orchestrator.daily_meeting_analyzer.execute({
            "execution_type": "scheduled",
            "scan_directory": config.protocols_path,
            "file_formats": config.supported_formats,
            "extraction_depth": "employee_actions"
        })
        
        # Quality validation
        quality = await quality_controller.validate_agent_result(result)
        
        if quality.overall_quality < 90.0:
            await handle_quality_issue("daily_meeting_analysis", quality)
        else:
            await log_success("Daily meeting analysis completed", quality)
            
    except Exception as e:
        await handle_job_error("daily_meeting_analysis", e)
        await schedule_retry_if_needed("daily_meeting_analysis", e)
```

**Job Configuration:**
```yaml
daily_meeting_job:
  trigger: "cron"
  hour: 19
  minute: 0
  timezone: "Europe/Moscow"
  max_instances: 1
  coalesce: true
  misfire_grace_time: 300
  retry_delay: 300
  max_retries: 3
```

### **3. Daily Summary Job**
```python
async def daily_summary_job():
    """
    Ежедневная консолидация и генерация отчетов
    Запуск: 19:30 UTC+3 каждый день
    """
    try:
        # Verify prerequisite jobs completed
        if not await check_prerequisites_completed(["daily_jira_analysis", "daily_meeting_analysis"]):
            await schedule_delayed_retry("daily_summary", "Prerequisites not completed")
            return
            
        result = await orchestrator.daily_summary_agent.execute({
            "execution_type": "scheduled",
            "consolidation_sources": ["jira_data", "meeting_data"],
            "output_formats": ["json", "txt"]
        })
        
        # Quality validation
        quality = await quality_controller.validate_agent_result(result)
        
        if quality.overall_quality < 90.0:
            await handle_quality_issue("daily_summary", quality)
        else:
            await log_success("Daily summary completed", quality)
            await notify_daily_completion(result)
            
    except Exception as e:
        await handle_job_error("daily_summary", e)
        await schedule_retry_if_needed("daily_summary", e)
```

**Job Configuration:**
```yaml
daily_summary_job:
  trigger: "cron"
  hour: 19
  minute: 30
  timezone: "Europe/Moscow"
  max_instances: 1
  coalesce: true
  misfire_grace_time: 600  # 10 minutes
  retry_delay: 600
  max_retries: 2
```

### **4. Weekly Reporting Job**
```python
async def weekly_reporting_job():
    """
    Недельный аналитический отчет с публикацией в Confluence
    Запуск: Пятница 19:00 UTC+3
    """
    try:
        # Verify week data completeness
        if not await verify_week_data_completeness():
            await schedule_delayed_retry("weekly_reporting", "Incomplete week data")
            return
            
        result = await orchestrator.weekly_reporter.execute({
            "execution_type": "scheduled",
            "analysis_period": "7_days",
            "include_predictions": False,
            "publication_targets": ["confluence", "local_backup"]
        })
        
        # Quality validation
        quality = await quality_controller.validate_agent_result(result)
        
        if quality.overall_quality < 90.0:
            await handle_quality_issue("weekly_reporting", quality)
        else:
            await log_success("Weekly report published", quality)
            await notify_weekly_completion(result)
            
    except Exception as e:
        await handle_job_error("weekly_reporting", e)
        await schedule_retry_if_needed("weekly_reporting", e)
```

**Job Configuration:**
```yaml
weekly_reporting_job:
  trigger: "cron"
  day_of_week: "fri"
  hour: 19
  minute: 0
  timezone: "Europe/Moscow"
  max_instances: 1
  coalesce: true
  misfire_grace_time: 900  # 15 minutes
  retry_delay: 900
  max_retries: 1
```

### **5. Health Check Job**
```python
async def health_check_job():
    """
    Мониторинг здоровья системы
    Запуск: Каждый час
    """
    try:
        health_status = await orchestrator.health_monitor.check_system_health()
        
        if not health_status.is_healthy:
            await handle_health_issues(health_status)
        
        # Log health metrics
        await log_health_metrics(health_status)
        
        # Clean up old JSON files if needed
        await cleanup_old_data()
        
    except Exception as e:
        await handle_critical_health_error(e)
```

**Job Configuration:**
```yaml
health_check_job:
  trigger: "interval"
  hours: 1
  max_instances: 1
  coalesce: true
  misfire_grace_time: 300
```

---

## 🔄 **JOB COORDINATION LOGIC**

### **Daily Workflow Orchestration:**
```python
async def orchestrate_daily_workflow():
    """
    Координация ежедневного workflow
    """
    workflow_id = generate_workflow_id("daily")
    
    try:
        # Phase 1: Parallel Data Collection (19:00)
        await log_workflow_start(workflow_id, "daily", "data_collection")
        
        # Start parallel jobs
        jira_future = asyncio.create_task(run_job_with_tracking("daily_jira_analysis"))
        meeting_future = asyncio.create_task(run_job_with_tracking("daily_meeting_analysis"))
        
        # Wait for both to complete
        jira_result, meeting_result = await asyncio.gather(
            jira_future, meeting_future, return_exceptions=True
        )
        
        # Validate results
        if isinstance(jira_result, Exception) or isinstance(meeting_result, Exception):
            await handle_parallel_job_failures([jira_result, meeting_result])
            return
            
        await log_workflow_phase(workflow_id, "data_collection", "completed")
        
        # Phase 2: Consolidation (19:30)
        await log_workflow_phase(workflow_id, "consolidation", "started")
        
        summary_result = await run_job_with_tracking("daily_summary")
        
        if isinstance(summary_result, Exception):
            await handle_job_failure("daily_summary", summary_result)
            return
            
        await log_workflow_complete(workflow_id, "daily", "success")
        
    except Exception as e:
        await log_workflow_complete(workflow_id, "daily", "failed", str(e))
        await handle_workflow_critical_error("daily", e)
```

### **Job Dependency Management:**
```python
class JobDependencyManager:
    """
    Управление зависимостями между задачами
    """
    
    async def check_job_prerequisites(self, job_id: str) -> bool:
        """
        Проверка выполнения prerequisite задач
        """
        prerequisites = self.get_job_prerequisites(job_id)
        
        for prereq_id in prerequisites:
            if not await self.is_job_completed_today(prereq_id):
                return False
                
        return True
    
    async def schedule_delayed_retry(self, job_id: str, reason: str):
        """
        Планирование отложенного retry для задачи
        """
        delay = self.calculate_retry_delay(job_id)
        
        self.scheduler.add_job(
            func=run_job_with_tracking,
            trigger="date",
            run_date=datetime.now() + timedelta(seconds=delay),
            args=[job_id],
            id=f"{job_id}_delayed_retry",
            replace_existing=True
        )
```

---

## 🔧 **ERROR HANDLING & RECOVERY**

### **Job Failure Handling:**
```python
async def handle_job_error(job_id: str, error: Exception):
    """
    Обработка ошибок выполнения задачи
    """
    error_context = {
        "job_id": job_id,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.now().isoformat(),
        "retry_count": get_job_retry_count(job_id)
    }
    
    # Log error
    await log_job_error(error_context)
    
    # Check if retry is needed
    if should_retry_job(job_id, error_context):
        await schedule_retry_job(job_id, error_context)
    else:
        await escalate_job_failure(job_id, error_context)

async def schedule_retry_job(job_id: str, error_context: Dict):
    """
    Планирование retry задачи
    """
    retry_count = error_context["retry_count"]
    
    if retry_count >= config.max_retry_attempts:
        await escalate_job_failure(job_id, error_context)
        return
    
    delay = calculate_exponential_backoff(retry_count)
    
    scheduler.add_job(
        func=run_job_with_tracking,
        trigger="date",
        run_date=datetime.now() + timedelta(seconds=delay),
        args=[job_id],
        id=f"{job_id}_retry_{retry_count + 1}",
        replace_existing=True
    )
    
    await log_retry_scheduled(job_id, retry_count + 1, delay)
```

### **Circuit Breaker Pattern:**
```python
class CircuitBreaker:
    """
    Circuit Breaker для предотвращения cascade failures
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def execute_job(self, job_func, *args, **kwargs):
        """
        Выполнение задачи через circuit breaker
        """
        if self.state == "OPEN":
            if self.should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenException("Circuit breaker is OPEN")
        
        try:
            result = await job_func(*args, **kwargs)
            self.on_success()
            return result
            
        except Exception as e:
            self.on_failure()
            raise e
    
    def on_success(self):
        """Обработка успешного выполнения"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def on_failure(self):
        """Обработка ошибки выполнения"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
```

---

## 📊 **MONITORING & OBSERVABILITY**

### **Job Metrics Collection:**
```python
class JobMetricsCollector:
    """
    Сбор метрик выполнения задач
    """
    
    async def record_job_start(self, job_id: str):
        """Запуск сбор метрик для задачи"""
        self.job_metrics[job_id] = {
            "start_time": datetime.now(),
            "status": "running",
            "retry_count": 0
        }
    
    async def record_job_completion(self, job_id: str, success: bool, duration: float):
        """Фиксация завершения задачи"""
        metrics = self.job_metrics.get(job_id, {})
        metrics.update({
            "end_time": datetime.now(),
            "duration_seconds": duration,
            "status": "completed" if success else "failed",
            "success": success
        })
        
        # Update aggregate metrics
        await self.update_aggregate_metrics(job_id, metrics)
    
    async def get_daily_metrics(self) -> Dict:
        """Получение суточных метрик"""
        today = datetime.now().date()
        today_metrics = [
            m for m in self.job_metrics.values()
            if m["start_time"].date() == today
        ]
        
        return {
            "total_jobs": len(today_metrics),
            "successful_jobs": sum(1 for m in today_metrics if m["success"]),
            "failed_jobs": sum(1 for m in today_metrics if not m["success"]),
            "avg_duration": sum(m["duration_seconds"] for m in today_metrics) / len(today_metrics),
            "retries_performed": sum(m["retry_count"] for m in today_metrics)
        }
```

### **Health Monitoring:**
```python
class SystemHealthMonitor:
    """
    Мониторинг здоровья системы
    """
    
    async def check_system_health(self) -> HealthStatus:
        """
        Комплексная проверка здоровья системы
        """
        checks = {
            "scheduler_status": await self.check_scheduler_health(),
            "agent_health": await self.check_all_agents_health(),
            "memory_store_health": await self.check_memory_store_health(),
            "external_services": await self.check_external_services_health(),
            "disk_space": await self.check_disk_space_health()
        }
        
        overall_status = self.calculate_overall_health(checks)
        
        return HealthStatus(
            is_healthy=overall_status.is_healthy,
            checks=checks,
            timestamp=datetime.now(),
            alerts=overall_status.alerts
        )
    
    async def check_scheduler_health(self) -> Dict:
        """Проверка здоровья планировщика"""
        return {
            "is_running": scheduler.running,
            "pending_jobs": len(scheduler.get_jobs()),
            "next_run_times": self.get_next_run_times(),
            "missed_executions": self.get_missed_executions()
        }
```

---

## 🔄 **CONFIGURATION MANAGEMENT**

### **YAML Configuration Structure:**
```yaml
# config/scheduler.yaml
scheduler:
  # Core settings
  timezone: "Europe/Moscow"
  max_workers: 10
  job_defaults:
    coalesce: true
    max_instances: 1
    misfire_grace_time: 300
  
  # Daily workflows
  daily_workflow:
    start_time: "19:00"
    summary_time: "19:30"
    timeout_minutes: 60
    
  # Weekly workflows  
  weekly_workflow:
    day: "friday"
    time: "19:00"
    timeout_minutes: 120
    
  # Quality control
  quality_control:
    threshold: 90.0
    max_retries: 3
    retry_delay_seconds: 300
    
  # Health monitoring
  health_monitoring:
    check_interval_seconds: 3600
    disk_space_threshold_gb: 10
    
  # Notifications
  notifications:
    admin_email: "admin@company.com"
    webhook_url: "https://hooks.company.com/scheduler"
    
  # Agent configuration
  agents:
    daily_jira_analyzer:
      project_keys: ["CSI", "PROJ", "DEV"]
      employee_identification: ["jira_username", "email", "full_name"]
      
    daily_meeting_analyzer:
      protocols_path: "/data/meetings"
      supported_formats: ["txt", "docx", "pdf"]
      
    weekly_reporter:
      confluence_space_key: "PROJECTS"
      parent_page_id: "897438835"
```

---

## 🚨 **ALERTING & NOTIFICATIONS**

### **Alert Types:**
```python
class AlertType(Enum):
    JOB_FAILURE = "job_failure"
    QUALITY_THRESHOLD_BREACH = "quality_threshold_breach"
    SYSTEM_HEALTH_DEGRADATION = "system_health_degradation"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"
    RETRY_EXHAUSTED = "retry_exhausted"
    EXTERNAL_SERVICE_UNAVAILABLE = "external_service_unavailable"

class AlertManager:
    """
    Управление оповещениями системы
    """
    
    async def send_alert(self, alert_type: AlertType, context: Dict):
        """
        Отправка оповещения
        """
        alert_message = self.format_alert_message(alert_type, context)
        
        # Send email notification
        await self.send_email_alert(alert_message, context)
        
        # Send webhook notification
        await self.send
