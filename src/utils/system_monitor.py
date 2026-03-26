"""
System Monitor Utility

Provides comprehensive monitoring capabilities for the Employee Monitoring System,
including health checks, performance metrics, and alerting.
"""

import asyncio
import logging
import json
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import aiofiles

from ..scheduler.employee_monitoring_scheduler import EmployeeMonitoringScheduler
from ..orchestrator.employee_monitoring_orchestrator import EmployeeMonitoringOrchestrator
from ..core.config import get_employee_monitoring_config

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System metrics data structure."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    disk_usage_percent: float
    active_connections: int
    uptime_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HealthCheck:
    """Health check result structure."""
    component: str
    status: str  # 'healthy', 'warning', 'critical'
    message: str
    response_time_ms: float
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SystemMonitor:
    """
    System Monitor for Employee Monitoring System.
    
    Provides:
    - Real-time system metrics collection
    - Component health checks
    - Performance monitoring
    - Alert threshold monitoring
    - Historical data tracking
    """
    
    def __init__(self, check_interval: int = 60):
        """Initialize system monitor.
        
        Args:
            check_interval: Interval in seconds between checks
        """
        self.check_interval = check_interval
        self.start_time = time.time()
        self.metrics_history: List[SystemMetrics] = []
        self.health_checks: Dict[str, HealthCheck] = {}
        self.alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_usage_percent': 90.0,
            'response_time_ms': 5000.0
        }
        
        # Storage paths
        self.reports_dir = Path('./reports/monitoring')
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Components to monitor
        self.scheduler: Optional[EmployeeMonitoringScheduler] = None
        self.orchestrator: Optional[EmployeeMonitoringOrchestrator] = None
        
        # Monitoring state
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        logger.info("SystemMonitor initialized")
    
    def set_components(self, scheduler: Optional[EmployeeMonitoringScheduler] = None,
                      orchestrator: Optional[EmployeeMonitoringOrchestrator] = None):
        """Set system components for monitoring."""
        self.scheduler = scheduler
        self.orchestrator = orchestrator
        logger.info(f"Components set for monitoring: scheduler={scheduler is not None}, orchestrator={orchestrator is not None}")
    
    async def start_monitoring(self):
        """Start continuous monitoring."""
        if self.is_monitoring:
            logger.warning("Monitoring is already running")
            return
        
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"System monitoring started (interval: {self.check_interval}s)")
    
    async def stop_monitoring(self):
        """Stop continuous monitoring."""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("System monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                # Collect system metrics
                metrics = await self._collect_system_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only last 1000 entries
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]
                
                # Perform health checks
                await self._perform_health_checks()
                
                # Check for alerts
                await self._check_alerts(metrics)
                
                # Save metrics periodically (every 10 minutes)
                if int(time.time()) % 600 == 0:
                    await self._save_metrics()
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            
            # Network connections
            try:
                connections = len(psutil.net_connections())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                connections = 0
            
            # Uptime
            uptime_seconds = time.time() - self.start_time
            
            metrics = SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_gb=memory_used_gb,
                disk_usage_percent=disk_usage_percent,
                active_connections=connections,
                uptime_seconds=uptime_seconds
            )
            
            logger.debug(f"Collected system metrics: CPU={cpu_percent}%, MEM={memory_percent}%, DISK={disk_usage_percent}%")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_gb=0.0,
                disk_usage_percent=0.0,
                active_connections=0,
                uptime_seconds=0.0
            )
    
    async def _perform_health_checks(self):
        """Perform health checks on all components."""
        current_time = datetime.now()
        
        # Check Scheduler
        if self.scheduler:
            start_time = time.time()
            try:
                status = await self.scheduler.get_scheduler_status()
                response_time = (time.time() - start_time) * 1000
                
                if status.get('scheduler_status') == 'running':
                    health_status = 'healthy'
                    message = 'Scheduler is running normally'
                else:
                    health_status = 'warning'
                    message = f"Scheduler status: {status.get('scheduler_status', 'unknown')}"
                
                self.health_checks['scheduler'] = HealthCheck(
                    component='scheduler',
                    status=health_status,
                    message=message,
                    response_time_ms=response_time,
                    timestamp=current_time.isoformat()
                )
                
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                self.health_checks['scheduler'] = HealthCheck(
                    component='scheduler',
                    status='critical',
                    message=f"Scheduler check failed: {str(e)}",
                    response_time_ms=response_time,
                    timestamp=current_time.isoformat()
                )
        
        # Check Orchestrator
        if self.orchestrator:
            start_time = time.time()
            try:
                status = await self.orchestrator.get_orchestrator_status()
                response_time = (time.time() - start_time) * 1000
                
                if status.get('orchestrator_status') == 'healthy':
                    health_status = 'healthy'
                    message = 'Orchestrator is healthy'
                else:
                    health_status = 'warning'
                    message = f"Orchestrator status: {status.get('orchestrator_status', 'unknown')}"
                
                self.health_checks['orchestrator'] = HealthCheck(
                    component='orchestrator',
                    status=health_status,
                    message=message,
                    response_time_ms=response_time,
                    timestamp=current_time.isoformat()
                )
                
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                self.health_checks['orchestrator'] = HealthCheck(
                    component='orchestrator',
                    status='critical',
                    message=f"Orchestrator check failed: {str(e)}",
                    response_time_ms=response_time,
                    timestamp=current_time.isoformat()
                )
        
        # Check Configuration
        start_time = time.time()
        try:
            config = get_employee_monitoring_config()
            response_time = (time.time() - start_time) * 1000
            
            if config:
                health_status = 'healthy'
                message = 'Configuration loaded successfully'
            else:
                health_status = 'critical'
                message = 'Configuration not found'
            
            self.health_checks['configuration'] = HealthCheck(
                component='configuration',
                status=health_status,
                message=message,
                response_time_ms=response_time,
                timestamp=current_time.isoformat()
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.health_checks['configuration'] = HealthCheck(
                component='configuration',
                status='critical',
                message=f"Configuration check failed: {str(e)}",
                response_time_ms=response_time,
                timestamp=current_time.isoformat()
            )
    
    async def _check_alerts(self, metrics: SystemMetrics):
        """Check for alert conditions."""
        alerts = []
        
        # CPU alert
        if metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
            alerts.append({
                'type': 'cpu_high',
                'message': f"High CPU usage: {metrics.cpu_percent:.1f}%",
                'value': metrics.cpu_percent,
                'threshold': self.alert_thresholds['cpu_percent'],
                'timestamp': metrics.timestamp
            })
        
        # Memory alert
        if metrics.memory_percent > self.alert_thresholds['memory_percent']:
            alerts.append({
                'type': 'memory_high',
                'message': f"High memory usage: {metrics.memory_percent:.1f}%",
                'value': metrics.memory_percent,
                'threshold': self.alert_thresholds['memory_percent'],
                'timestamp': metrics.timestamp
            })
        
        # Disk alert
        if metrics.disk_usage_percent > self.alert_thresholds['disk_usage_percent']:
            alerts.append({
                'type': 'disk_high',
                'message': f"High disk usage: {metrics.disk_usage_percent:.1f}%",
                'value': metrics.disk_usage_percent,
                'threshold': self.alert_thresholds['disk_usage_percent'],
                'timestamp': metrics.timestamp
            })
        
        # Response time alerts
        for component, health in self.health_checks.items():
            if health.response_time_ms > self.alert_thresholds['response_time_ms']:
                alerts.append({
                    'type': 'response_time_high',
                    'message': f"High response time for {component}: {health.response_time_ms:.1f}ms",
                    'component': component,
                    'value': health.response_time_ms,
                    'threshold': self.alert_thresholds['response_time_ms'],
                    'timestamp': health.timestamp
                })
        
        # Component status alerts
        for component, health in self.health_checks.items():
            if health.status == 'critical':
                alerts.append({
                    'type': 'component_critical',
                    'message': f"Component {component} is critical: {health.message}",
                    'component': component,
                    'status': health.status,
                    'timestamp': health.timestamp
                })
        
        # Log alerts
        for alert in alerts:
            logger.warning(f"ALERT: {alert['message']}")
        
        # Save alerts
        if alerts:
            await self._save_alerts(alerts)
    
    async def _save_metrics(self):
        """Save metrics history to file."""
        try:
            metrics_file = self.reports_dir / f"metrics_{datetime.now().strftime('%Y%m%d')}.json"
            
            metrics_data = {
                'timestamp': datetime.now().isoformat(),
                'history': [metrics.to_dict() for metrics in self.metrics_history[-100:]],  # Last 100
                'health_checks': {k: v.to_dict() for k, v in self.health_checks.items()}
            }
            
            async with aiofiles.open(metrics_file, 'w') as f:
                await f.write(json.dumps(metrics_data, indent=2, ensure_ascii=False))
                
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    async def _save_alerts(self, alerts: List[Dict[str, Any]]):
        """Save alerts to file."""
        try:
            alerts_file = self.reports_dir / f"alerts_{datetime.now().strftime('%Y%m%d')}.json"
            
            # Load existing alerts
            existing_alerts = []
            if alerts_file.exists():
                try:
                    async with aiofiles.open(alerts_file, 'r') as f:
                        content = await f.read()
                        existing_alerts = json.loads(content).get('alerts', [])
                except:
                    existing_alerts = []
            
            # Add new alerts
            existing_alerts.extend(alerts)
            
            # Keep only last 1000 alerts
            if len(existing_alerts) > 1000:
                existing_alerts = existing_alerts[-1000:]
            
            alerts_data = {
                'timestamp': datetime.now().isoformat(),
                'alerts': existing_alerts
            }
            
            async with aiofiles.open(alerts_file, 'w') as f:
                await f.write(json.dumps(alerts_data, indent=2, ensure_ascii=False))
                
        except Exception as e:
            logger.error(f"Failed to save alerts: {e}")
    
    async def get_current_status(self) -> Dict[str, Any]:
        """Get current system status."""
        if not self.metrics_history:
            current_metrics = await self._collect_system_metrics()
        else:
            current_metrics = self.metrics_history[-1]
        
        # Calculate averages over last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_metrics = [
            m for m in self.metrics_history 
            if datetime.fromisoformat(m.timestamp) > one_hour_ago
        ]
        
        averages = {}
        if recent_metrics:
            averages = {
                'avg_cpu_percent': sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
                'avg_memory_percent': sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
                'avg_response_time_ms': sum(
                    h.response_time_ms for h in self.health_checks.values()
                ) / max(len(self.health_checks), 1)
            }
        
        return {
            'current_metrics': current_metrics.to_dict(),
            'averages_last_hour': averages,
            'health_checks': {k: v.to_dict() for k, v in self.health_checks.items()},
            'monitoring_status': {
                'is_monitoring': self.is_monitoring,
                'check_interval': self.check_interval,
                'uptime_seconds': time.time() - self.start_time,
                'metrics_count': len(self.metrics_history)
            },
            'alert_thresholds': self.alert_thresholds
        }
    
    async def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate performance report for specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter metrics
        period_metrics = [
            m for m in self.metrics_history 
            if datetime.fromisoformat(m.timestamp) > cutoff_time
        ]
        
        if not period_metrics:
            return {
                'period_hours': hours,
                'message': 'No data available for the specified period'
            }
        
        # Calculate statistics
        cpu_values = [m.cpu_percent for m in period_metrics]
        memory_values = [m.memory_percent for m in period_metrics]
        disk_values = [m.disk_usage_percent for m in period_metrics]
        
        # Component availability
        component_uptime = {}
        for component in self.health_checks.keys():
            healthy_checks = [
                h for h in self.health_checks.values() 
                if h.component == component and h.status == 'healthy'
                and datetime.fromisoformat(h.timestamp) > cutoff_time
            ]
            total_checks = [
                h for h in self.health_checks.values() 
                if h.component == component
                and datetime.fromisoformat(h.timestamp) > cutoff_time
            ]
            
            if total_checks:
                component_uptime[component] = len(healthy_checks) / len(total_checks) * 100
        
        report = {
            'period_hours': hours,
            'data_points': len(period_metrics),
            'period_start': cutoff_time.isoformat(),
            'period_end': datetime.now().isoformat(),
            'system_statistics': {
                'cpu': {
                    'min': min(cpu_values),
                    'max': max(cpu_values),
                    'avg': sum(cpu_values) / len(cpu_values)
                },
                'memory': {
                    'min': min(memory_values),
                    'max': max(memory_values),
                    'avg': sum(memory_values) / len(memory_values)
                },
                'disk': {
                    'min': min(disk_values),
                    'max': max(disk_values),
                    'avg': sum(disk_values) / len(disk_values)
                }
            },
            'component_uptime_percent': component_uptime,
            'alerts_count': len([
                a for a in self.metrics_history 
                if any(metric > threshold for metric, threshold in [
                    (a.cpu_percent, self.alert_thresholds['cpu_percent']),
                    (a.memory_percent, self.alert_thresholds['memory_percent']),
                    (a.disk_usage_percent, self.alert_thresholds['disk_usage_percent'])
                ])
            ])
        }
        
        return report
    
    def update_alert_thresholds(self, **thresholds):
        """Update alert thresholds."""
        for key, value in thresholds.items():
            if key in self.alert_thresholds:
                old_value = self.alert_thresholds[key]
                self.alert_thresholds[key] = value
                logger.info(f"Updated alert threshold {key}: {old_value} -> {value}")
            else:
                logger.warning(f"Unknown alert threshold: {key}")
    
    async def cleanup_old_data(self, days: int = 30):
        """Clean up old monitoring data."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            # Clean old metrics files
            for file_path in self.reports_dir.glob("metrics_*.json"):
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    file_path.unlink()
                    logger.info(f"Deleted old metrics file: {file_path}")
            
            # Clean old alerts files
            for file_path in self.reports_dir.glob("alerts_*.json"):
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    file_path.unlink()
                    logger.info(f"Deleted old alerts file: {file_path}")
            
            # Clean in-memory history
            self.metrics_history = [
                m for m in self.metrics_history
                if datetime.fromisoformat(m.timestamp) > cutoff_date
            ]
            
            logger.info(f"Cleaned up monitoring data older than {days} days")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")


# Utility functions for standalone usage
async def run_monitoring_dashboard():
    """Run a simple monitoring dashboard."""
    monitor = SystemMonitor()
    await monitor.start_monitoring()
    
    try:
        while True:
            status = await monitor.get_current_status()
            
            print("\n" + "="*60)
            print("🖥️  SYSTEM MONITORING DASHBOARD")
            print("="*60)
            print(f"🕐 Timestamp: {status['current_metrics']['timestamp']}")
            print(f"⏱️  Uptime: {status['monitoring_status']['uptime_seconds']:.0f}s")
            
            # System metrics
            metrics = status['current_metrics']
            print(f"\n📊 System Metrics:")
            print(f"   CPU: {metrics['cpu_percent']:.1f}%")
            print(f"   Memory: {metrics['memory_percent']:.1f}% ({metrics['memory_used_gb']:.1f}GB)")
            print(f"   Disk: {metrics['disk_usage_percent']:.1f}%")
            print(f"   Connections: {metrics['active_connections']}")
            
            # Health checks
            print(f"\n🏥 Health Checks:")
            for component, health in status['health_checks'].items():
                status_icon = "✅" if health['status'] == 'healthy' else "⚠️" if health['status'] == 'warning' else "❌"
                print(f"   {status_icon} {component}: {health['status']} ({health['response_time_ms']:.1f}ms)")
            
            # Averages
            if status['averages_last_hour']:
                print(f"\n📈 Last Hour Averages:")
                avg = status['averages_last_hour']
                print(f"   CPU: {avg.get('avg_cpu_percent', 0):.1f}%")
                print(f"   Memory: {avg.get('avg_memory_percent', 0):.1f}%")
                print(f"   Response Time: {avg.get('avg_response_time_ms', 0):.1f}ms")
            
            print("="*60)
            
            await asyncio.sleep(30)  # Update every 30 seconds
            
    except KeyboardInterrupt:
        print("\n👋 Stopping monitoring dashboard...")
    finally:
        await monitor.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(run_monitoring_dashboard())
