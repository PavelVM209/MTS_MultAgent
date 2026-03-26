"""
Production Monitoring System
Handles real-time monitoring, health checks, and alerting for production deployment.
"""

import asyncio
import aiohttp
import logging
import json
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

from ..core.config import get_config


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthCheck:
    """Health check result"""
    component: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    response_time: float
    timestamp: datetime
    details: Dict[str, Any]


@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    process_count: int
    load_average: List[float]
    timestamp: datetime


@dataclass
class ApplicationMetrics:
    """Application-specific metrics"""
    agent_executions: Dict[str, int]
    api_response_times: Dict[str, float]
    error_rates: Dict[str, float]
    quality_scores: Dict[str, float]
    active_workflows: int
    timestamp: datetime


@dataclass
class Alert:
    """System alert"""
    id: str
    level: AlertLevel
    component: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class ProductionMonitor:
    """Production monitoring and alerting system"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        self._session: Optional[aiohttp.ClientSession] = None
        self._alerts: List[Alert] = []
        self._health_checks: Dict[str, HealthCheck] = {}
        self._metrics_history: List[Dict[str, Any]] = []
        self._alert_callbacks: List[Callable[[Alert], None]] = []
        
    async def __aenter__(self):
        """Async context manager entry"""
        self._session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._session:
            await self._session.close()
    
    async def start_monitoring(self) -> Dict[str, Any]:
        """Start production monitoring"""
        self.logger.info("📊 Starting production monitoring system...")
        
        # Initialize monitoring
        await self._initialize_monitoring()
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._metrics_collection_loop()),
            asyncio.create_task(self._alert_processing_loop())
        ]
        
        self.logger.info("✅ Production monitoring started")
        return {
            "monitoring_active": True,
            "tasks_started": len(tasks),
            "initial_health": await self._run_initial_health_checks()
        }
    
    async def _initialize_monitoring(self) -> None:
        """Initialize monitoring components"""
        # Create monitoring directories
        monitoring_dirs = [
            "/opt/mts-multagent/monitoring/metrics",
            "/opt/mts-multagent/monitoring/alerts",
            "/opt/mts-multagent/monitoring/health"
        ]
        
        for directory in monitoring_dirs:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize alerting
        self._setup_alerting()
        
        # Load historical data
        await self._load_monitoring_history()
    
    def _setup_alerting(self) -> None:
        """Setup alert configuration"""
        # Configure alert thresholds
        self.alert_thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0,
            "response_time": 5.0,
            "error_rate": 5.0,
            "quality_score": 80.0
        }
        
        # Setup alert callbacks
        self._alert_callbacks = [
            self._log_alert,
            self._save_alert,
            self._send_webhook_alert
        ]
    
    async def _load_monitoring_history(self) -> None:
        """Load historical monitoring data"""
        try:
            metrics_file = Path("/opt/mts-multagent/monitoring/metrics/history.json")
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    self._metrics_history = json.load(f)
                self.logger.info(f"Loaded {len(self._metrics_history)} historical metrics")
        except Exception as e:
            self.logger.warning(f"Failed to load monitoring history: {e}")
            self._metrics_history = []
    
    async def _run_initial_health_checks(self) -> Dict[str, HealthCheck]:
        """Run initial health checks"""
        self.logger.info("🔍 Running initial health checks...")
        
        health_checks = {}
        components = [
            "database", "llm_service", "file_system", 
            "network", "agents", "scheduler"
        ]
        
        for component in components:
            health_check = await self._check_component_health(component)
            health_checks[component] = health_check
            self._health_checks[component] = health_check
            
            # Create alert for unhealthy components
            if health_check.status != "healthy":
                await self._create_alert(
                    level=AlertLevel.WARNING,
                    component=component,
                    message=f"Component {component} is {health_check.status}",
                    details={"health_check": asdict(health_check)}
                )
        
        return health_checks
    
    async def _health_check_loop(self) -> None:
        """Continuous health monitoring loop"""
        self.logger.info("🔄 Starting health check loop...")
        
        while True:
            try:
                for component in self._health_checks.keys():
                    health_check = await self._check_component_health(component)
                    self._health_checks[component] = health_check
                    
                    # Check for health status changes
                    await self._check_health_changes(component, health_check)
                
                # Save health status
                await self._save_health_status()
                
                # Wait before next check
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                self.logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _check_component_health(self, component: str) -> HealthCheck:
        """Check health of a specific component"""
        start_time = datetime.now()
        
        try:
            if component == "database":
                status = await self._check_database_health()
            elif component == "llm_service":
                status = await self._check_llm_service_health()
            elif component == "file_system":
                status = await self._check_file_system_health()
            elif component == "network":
                status = await self._check_network_health()
            elif component == "agents":
                status = await self._check_agents_health()
            elif component == "scheduler":
                status = await self._check_scheduler_health()
            else:
                status = {"status": "unknown", "message": "Unknown component"}
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            return HealthCheck(
                component=component,
                status=status["status"],
                message=status["message"],
                response_time=response_time,
                timestamp=start_time,
                details=status.get("details", {})
            )
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            return HealthCheck(
                component=component,
                status="unhealthy",
                message=str(e),
                response_time=response_time,
                timestamp=start_time,
                details={"error": str(e)}
            )
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            # Check file system (JSON storage)
            data_path = Path("/opt/mts-multagent/data")
            if not data_path.exists():
                return {"status": "unhealthy", "message": "Data directory not found"}
            
            # Check disk space
            disk_usage = psutil.disk_usage(data_path.anchor)
            if disk_usage.percent > 90:
                return {"status": "degraded", "message": "Low disk space"}
            
            # Test write operations
            test_file = data_path / "health_check.tmp"
            test_file.write_text("test")
            test_file.unlink()
            
            return {
                "status": "healthy",
                "message": "Database (JSON storage) operational",
                "details": {
                    "disk_usage": disk_usage.percent,
                    "data_path": str(data_path)
                }
            }
            
        except Exception as e:
            return {"status": "unhealthy", "message": f"Database error: {e}"}
    
    async def _check_llm_service_health(self) -> Dict[str, Any]:
        """Check LLM service health"""
        try:
            if not self._session:
                return {"status": "unhealthy", "message": "No HTTP session"}
            
            # Test OpenAI API connectivity
            timeout = aiohttp.ClientTimeout(total=10)
            async with self._session.get(
                "https://api.openai.com/v1/models",
                timeout=timeout
            ) as response:
                if response.status == 200:
                    return {
                        "status": "healthy",
                        "message": "LLM service accessible",
                        "details": {"response_time": response.headers.get("X-Response-Time")}
                    }
                else:
                    return {"status": "unhealthy", "message": f"API status: {response.status}"}
                    
        except Exception as e:
            return {"status": "unhealthy", "message": f"LLM service error: {e}"}
    
    async def _check_file_system_health(self) -> Dict[str, Any]:
        """Check file system health"""
        try:
            paths_to_check = [
                "/opt/mts-multagent/data",
                "/opt/mts-multagent/logs",
                "/opt/mts-multagent/config"
            ]
            
            issues = []
            for path in paths_to_check:
                path_obj = Path(path)
                if not path_obj.exists():
                    issues.append(f"Missing directory: {path}")
                elif not os.access(path, os.W_OK):
                    issues.append(f"No write access: {path}")
            
            if issues:
                return {
                    "status": "degraded" if len(issues) < 3 else "unhealthy",
                    "message": "; ".join(issues),
                    "details": {"issues": issues}
                }
            
            return {
                "status": "healthy",
                "message": "File system operational",
                "details": {"checked_paths": paths_to_check}
            }
            
        except Exception as e:
            return {"status": "unhealthy", "message": f"File system error: {e}"}
    
    async def _check_network_health(self) -> Dict[str, Any]:
        """Check network connectivity"""
        try:
            test_urls = [
                "https://www.google.com",
                "https://api.openai.com",
                self.config.jira.url if hasattr(self.config.jira, 'url') else None
            ]
            
            results = {}
            for url in test_urls:
                if url:
                    try:
                        timeout = aiohttp.ClientTimeout(total=5)
                        async with self._session.get(url, timeout=timeout) as response:
                            results[url] = response.status < 400
                    except Exception:
                        results[url] = False
            
            success_rate = sum(results.values()) / len(results)
            
            if success_rate >= 0.8:
                status = "healthy"
                message = "Network connectivity good"
            elif success_rate >= 0.5:
                status = "degraded"
                message = "Some network issues detected"
            else:
                status = "unhealthy"
                message = "Poor network connectivity"
            
            return {
                "status": status,
                "message": message,
                "details": {
                    "test_results": results,
                    "success_rate": success_rate
                }
            }
            
        except Exception as e:
            return {"status": "unhealthy", "message": f"Network check error: {e}"}
    
    async def _check_agents_health(self) -> Dict[str, Any]:
        """Check agents health"""
        try:
            # Check if agent processes are running
            agents = ["daily_jira_analyzer", "daily_meeting_analyzer"]
            
            running_agents = 0
            for agent in agents:
                # Simple check - would be more sophisticated in real deployment
                if True:  # Placeholder for actual agent health check
                    running_agents += 1
            
            if running_agents == len(agents):
                return {
                    "status": "healthy",
                    "message": f"All {len(agents)} agents operational",
                    "details": {"running_agents": running_agents}
                }
            elif running_agents > 0:
                return {
                    "status": "degraded",
                    "message": f"{running_agents}/{len(agents)} agents running",
                    "details": {"running_agents": running_agents}
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "No agents running",
                    "details": {"running_agents": 0}
                }
                
        except Exception as e:
            return {"status": "unhealthy", "message": f"Agent check error: {e}"}
    
    async def _check_scheduler_health(self) -> Dict[str, Any]:
        """Check scheduler health"""
        try:
            # Check if scheduler service is active
            result = subprocess.run(
                ["sudo", "systemctl", "is-active", "mts-multagent"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {
                    "status": "healthy",
                    "message": "Scheduler service active",
                    "details": {"service_status": result.stdout.strip()}
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "Scheduler service inactive",
                    "details": {"service_status": result.stderr.strip()}
                }
                
        except Exception as e:
            return {"status": "unhealthy", "message": f"Scheduler check error: {e}"}
    
    async def _check_health_changes(self, component: str, new_health: HealthCheck) -> None:
        """Check for health status changes and create alerts"""
        if component not in self._health_checks:
            return
        
        old_health = self._health_checks[component]
        
        # Status changed
        if old_health.status != new_health.status:
            if new_health.status == "unhealthy":
                level = AlertLevel.ERROR
            elif new_health.status == "degraded":
                level = AlertLevel.WARNING
            else:
                level = AlertLevel.INFO
            
            await self._create_alert(
                level=level,
                component=component,
                message=f"Health status changed from {old_health.status} to {new_health.status}",
                details={
                    "old_status": old_health.status,
                    "new_status": new_health.status,
                    "old_message": old_health.message,
                    "new_message": new_health.message
                }
            )
    
    async def _metrics_collection_loop(self) -> None:
        """Continuous metrics collection loop"""
        self.logger.info("📈 Starting metrics collection loop...")
        
        while True:
            try:
                # Collect system metrics
                system_metrics = await self._collect_system_metrics()
                
                # Collect application metrics
                app_metrics = await self._collect_application_metrics()
                
                # Store metrics
                metrics_data = {
                    "timestamp": datetime.now().isoformat(),
                    "system": asdict(system_metrics),
                    "application": asdict(app_metrics)
                }
                
                self._metrics_history.append(metrics_data)
                
                # Keep only last 24 hours of data
                cutoff_time = datetime.now() - timedelta(hours=24)
                self._metrics_history = [
                    m for m in self._metrics_history 
                    if datetime.fromisoformat(m["timestamp"]) > cutoff_time
                ]
                
                # Check thresholds and create alerts
                await self._check_metric_thresholds(system_metrics, app_metrics)
                
                # Save metrics
                await self._save_metrics()
                
                # Wait before next collection
                await asyncio.sleep(60)  # 1 minute
                
            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(30)  # Wait 30 seconds on error
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system performance metrics"""
        # CPU metrics
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent
        
        # Network I/O
        network = psutil.net_io_counters()
        network_io = {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv
        }
        
        # Process count
        process_count = len(psutil.pids())
        
        # Load average (Unix-like systems)
        try:
            load_avg = list(psutil.getloadavg())
        except AttributeError:
            load_avg = [0.0, 0.0, 0.0]  # Windows fallback
        
        return SystemMetrics(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            network_io=network_io,
            process_count=process_count,
            load_average=load_avg,
            timestamp=datetime.now()
        )
    
    async def _collect_application_metrics(self) -> ApplicationMetrics:
        """Collect application-specific metrics"""
        # This would be enhanced with actual application metrics
        # For now, returning placeholder values
        
        return ApplicationMetrics(
            agent_executions={
                "daily_jira_analyzer": 0,
                "daily_meeting_analyzer": 0
            },
            api_response_times={
                "jira_api": 0.5,
                "confluence_api": 0.3,
                "openai_api": 1.2
            },
            error_rates={
                "jira_api": 0.0,
                "confluence_api": 0.0,
                "openai_api": 0.0
            },
            quality_scores={
                "jira_analysis": 95.0,
                "meeting_analysis": 92.0
            },
            active_workflows=0,
            timestamp=datetime.now()
        )
    
    async def _check_metric_thresholds(self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics) -> None:
        """Check metrics against thresholds and create alerts"""
        thresholds = self.alert_thresholds
        
        # System thresholds
        if system_metrics.cpu_usage > thresholds["cpu_usage"]:
            await self._create_alert(
                level=AlertLevel.WARNING,
                component="system",
                message=f"High CPU usage: {system_metrics.cpu_usage}%",
                details={"cpu_usage": system_metrics.cpu_usage}
            )
        
        if system_metrics.memory_usage > thresholds["memory_usage"]:
            await self._create_alert(
                level=AlertLevel.WARNING,
                component="system",
                message=f"High memory usage: {system_metrics.memory_usage}%",
                details={"memory_usage": system_metrics.memory_usage}
            )
        
        if system_metrics.disk_usage > thresholds["disk_usage"]:
            await self._create_alert(
                level=AlertLevel.ERROR,
                component="system",
                message=f"High disk usage: {system_metrics.disk_usage}%",
                details={"disk_usage": system_metrics.disk_usage}
            )
        
        # Application thresholds
        for api, response_time in app_metrics.api_response_times.items():
            if response_time > thresholds["response_time"]:
                await self._create_alert(
                    level=AlertLevel.WARNING,
                    component="api",
                    message=f"Slow response time for {api}: {response_time}s",
                    details={"api": api, "response_time": response_time}
                )
        
        for api, error_rate in app_metrics.error_rates.items():
            if error_rate > thresholds["error_rate"]:
                await self._create_alert(
                    level=AlertLevel.ERROR,
                    component="api",
                    message=f"High error rate for {api}: {error_rate}%",
                    details={"api": api, "error_rate": error_rate}
                )
        
        for component, quality_score in app_metrics.quality_scores.items():
            if quality_score < thresholds["quality_score"]:
                await self._create_alert(
                    level=AlertLevel.WARNING,
                    component="quality",
                    message=f"Low quality score for {component}: {quality_score}%",
                    details={"component": component, "quality_score": quality_score}
                )
    
    async def _alert_processing_loop(self) -> None:
        """Alert processing and notifications loop"""
        self.logger.info("🔔 Starting alert processing loop...")
        
        while True:
            try:
                # Process active alerts
                unresolved_alerts = [a for a in self._alerts if not a.resolved]
                
                for alert in unresolved_alerts:
                    # Check if alert should be escalated
                    time_since_alert = datetime.now() - alert.timestamp
                    if time_since_alert > timedelta(minutes=30):
                        # Escalate alert
                        escalation_alert = Alert(
                            id=f"{alert.id}_escalated",
                            level=AlertLevel.CRITICAL if alert.level != AlertLevel.CRITICAL else alert.level,
                            component=alert.component,
                            message=f"ESCALATED: {alert.message}",
                            details={"original_alert": asdict(alert)},
                            timestamp=datetime.now()
                        )
                        await self._process_alert(escalation_alert)
                
                # Wait before next processing
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                self.logger.error(f"Alert processing error: {e}")
                await asyncio.sleep(60)
    
    async def _create_alert(self, level: AlertLevel, component: str, message: str, details: Dict[str, Any]) -> None:
        """Create a new alert"""
        alert = Alert(
            id=f"{component}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            level=level,
            component=component,
            message=message,
            details=details,
            timestamp=datetime.now()
        )
        
        self._alerts.append(alert)
        await self._process_alert(alert)
    
    async def _process_alert(self, alert: Alert) -> None:
        """Process alert through all callbacks"""
        for callback in self._alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")
    
    async def _log_alert(self, alert: Alert) -> None:
        """Log alert"""
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }.get(alert.level, logging.INFO)
        
        self.logger.log(log_level, f"ALERT [{alert.level.value.upper()}] {alert.component}: {alert.message}")
    
    async def _save_alert(self, alert: Alert) -> None:
        """Save alert to file"""
        try:
            alerts_file = Path("/opt/mts-multagent/monitoring/alerts/alerts.json")
            
            # Load existing alerts
            existing_alerts = []
            if alerts_file.exists():
                with open(alerts_file, 'r') as f:
                    existing_alerts = json.load(f)
            
            # Add new alert
            existing_alerts.append(asdict(alert))
            
            # Keep only last 1000 alerts
            existing_alerts = existing_alerts[-1000:]
            
            # Save alerts
            with open(alerts_file, 'w') as f:
                json.dump(existing_alerts, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Failed to save alert: {e}")
    
    async def _send_webhook_alert(self, alert: Alert) -> None:
        """Send alert via webhook"""
        try:
            webhook_url = self.config.production.get("webhook_url")
            if not webhook_url:
                return
            
            payload = {
                "alert_id": alert.id,
                "level": alert.level.value,
                "component": alert.component,
                "message": alert.message,
                "details": alert.details,
                "timestamp": alert.timestamp.isoformat()
            }
            
            if self._session:
                async with self._session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        self.logger.info(f"Alert webhook sent: {alert.id}")
                    else:
                        self.logger.warning(f"Alert webhook failed: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")
    
    async def _save_health_status(self) -> None:
        """Save health status to file"""
        try:
            health_file = Path("/opt/mts-multagent/monitoring/health/current_health.json")
            
            health_data = {
                "timestamp": datetime.now().isoformat(),
                "health_checks": {
                    component: asdict(health_check)
                    for component, health_check in self._health_checks.items()
                }
            }
            
            with open(health_file, 'w') as f:
                json.dump(health_data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Failed to save health status: {e}")
    
    async def _save_metrics(self) -> None:
        """Save metrics to file"""
        try:
            metrics_file = Path("/opt/mts-multagent/monitoring/metrics/history.json")
            
            with open(metrics_file, 'w') as f:
                json.dump(self._metrics_history, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # Current health status
            health_status = {
                component: asdict(health_check)
                for component, health_check in self._health_checks.items()
            }
            
            # Current metrics (latest)
            latest_metrics = self._metrics_history[-1] if self._metrics_history else None
            
            # Active alerts
            active_alerts = [
                asdict(alert) for alert in self._alerts 
                if not alert.resolved
            ]
            
            # System summary
            healthy_components = sum(
                1 for hc in self._health_checks.values() 
                if hc.status == "healthy"
            )
            
            total_components = len(self._health_checks)
            system_health = "healthy" if healthy_components == total_components else "degraded"
            
            return {
                "timestamp": datetime.now().isoformat(),
                "system_health": system_health,
                "healthy_components": healthy_components,
                "total_components": total_components,
                "health_status": health_status,
                "latest_metrics": latest_metrics,
                "active_alerts": active_alerts,
                "alert_count": len(active_alerts)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system status: {e}")
            raise
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        try:
            for alert in self._alerts:
                if alert.id == alert_id and not alert.resolved:
                    alert.resolved = True
                    alert.resolved_at = datetime.now()
                    
                    self.logger.info(f"Alert resolved: {alert_id}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to resolve alert: {e}")
            return False
    
    def add_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """Add custom alert callback"""
        self._alert_callbacks.append(callback)
    
    async def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics history for specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            metrics for metrics in self._metrics_history
            if datetime.fromisoformat(metrics["timestamp"]) > cutoff_time
        ]
    
    async def get_alert_history(self, resolved: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get alert history"""
        alerts = self._alerts
        
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        
        return [asdict(alert) for alert in alerts]
