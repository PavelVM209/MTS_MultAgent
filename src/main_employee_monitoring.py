"""
Main Employee Monitoring System Entry Point

Launches the complete Employee Monitoring System with scheduler,
orchestrator, and all agents for automated employee performance monitoring.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scheduler.employee_monitoring_scheduler import EmployeeMonitoringScheduler
from orchestrator.employee_monitoring_orchestrator import EmployeeMonitoringOrchestrator, WorkflowType
from core.config import get_employee_monitoring_config, load_config
from core.json_memory_store import JSONMemoryStore
from core.llm_client import LLMClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('employee_monitoring.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class EmployeeMonitoringSystem:
    """
    Main Employee Monitoring System class.
    
    Manages the complete system lifecycle including:
    - Scheduler for automated execution
    - Orchestrator for workflow coordination
    - Health monitoring and status reporting
    - Graceful shutdown handling
    """
    
    def __init__(self):
        """Initialize the Employee Monitoring System."""
        self.scheduler: Optional[EmployeeMonitoringScheduler] = None
        self.orchestrator: Optional[EmployeeMonitoringOrchestrator] = None
        self.memory_store: Optional[JSONMemoryStore] = None
        self.llm_client: Optional[LLMClient] = None
        self.is_running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Employee Monitoring System initialized")
    
    async def start(self) -> None:
        """Start the Employee Monitoring System."""
        if self.is_running:
            logger.warning("Employee Monitoring System is already running")
            return
        
        try:
            logger.info("Starting Employee Monitoring System...")
            
            # Load configuration
            config = get_employee_monitoring_config()
            if not config:
                logger.error("Failed to load employee monitoring configuration")
                return
            
            # Initialize components
            self.memory_store = JSONMemoryStore()
            self.llm_client = LLMClient()
            self.orchestrator = EmployeeMonitoringOrchestrator()
            self.scheduler = EmployeeMonitoringScheduler()
            
            # Verify system health
            await self._verify_system_health()
            
            # Start the scheduler
            await self.scheduler.start()
            
            self.is_running = True
            logger.info("Employee Monitoring System started successfully")
            
            # Print startup information
            await self._print_startup_info()
            
            # Keep the system running
            await self._run_main_loop()
            
        except Exception as e:
            logger.error(f"Failed to start Employee Monitoring System: {e}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop the Employee Monitoring System."""
        if not self.is_running:
            return
        
        logger.info("Stopping Employee Monitoring System...")
        
        self.is_running = False
        
        # Stop scheduler
        if self.scheduler:
            await self.scheduler.stop()
        
        logger.info("Employee Monitoring System stopped")
    
    async def _verify_system_health(self) -> None:
        """Verify system health before starting."""
        logger.info("Verifying system health...")
        
        # Check configuration
        if not get_employee_monitoring_config():
            raise RuntimeError("Employee monitoring configuration not found")
        
        # Check memory store
        if not self.memory_store.is_healthy():
            raise RuntimeError("Memory store is not healthy")
        
        # Check LLM client
        if not await self.llm_client.is_available():
            logger.warning("LLM client is not available - some features may be limited")
        
        # Check orchestrator
        orchestrator_status = await self.orchestrator.get_orchestrator_status()
        if orchestrator_status.get('orchestrator_status') != 'healthy':
            raise RuntimeError(f"Orchestrator is not healthy: {orchestrator_status}")
        
        logger.info("System health verification passed")
    
    async def _print_startup_info(self) -> None:
        """Print startup information."""
        config = get_employee_monitoring_config()
        
        print("\n" + "="*60)
        print("🚀 MTS MULTAGENT EMPLOYEE MONITORING SYSTEM")
        print("="*60)
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⚙️  Scheduler: {'Enabled' if config.get('scheduler', {}).get('enabled') else 'Disabled'}")
        print(f"🔍 Quality Threshold: {config.get('quality', {}).get('threshold', 0.9)}")
        print(f"📊 Reports Directory: {config.get('reports', {}).get('base_dir', './reports')}")
        print(f"🔗 Jira Projects: {len(config.get('jira', {}).get('projects', []))}")
        print(f"📝 Confluence Space: {config.get('confluence', {}).get('space', 'N/A')}")
        print(f"👥 Employees Monitored: {len(config.get('employees', {}).get('list', []))}")
        print("="*60)
        
        # Show scheduled tasks
        if self.scheduler:
            tasks = await self.scheduler.get_scheduled_tasks()
            if tasks:
                print(f"📋 Scheduled Tasks: {len(tasks)}")
                for task in tasks[:5]:  # Show first 5 tasks
                    status_icon = "✅" if task.enabled else "❌"
                    print(f"   {status_icon} {task.name} ({task.schedule_expression})")
                if len(tasks) > 5:
                    print(f"   ... and {len(tasks) - 5} more tasks")
            else:
                print("📋 No scheduled tasks configured")
        
        print("="*60)
        print("🎯 System is ready for automated employee monitoring!")
        print("📝 Logs are being written to: employee_monitoring.log")
        print("⏹️  Press Ctrl+C to stop the system gracefully")
        print("="*60 + "\n")
    
    async def _run_main_loop(self) -> None:
        """Main execution loop."""
        try:
            while self.is_running:
                # Periodic health check every 5 minutes
                await asyncio.sleep(300)
                
                if self.is_running:
                    await self._periodic_health_check()
                    
        except asyncio.CancelledError:
            logger.info("Main loop cancelled")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
    
    async def _periodic_health_check(self) -> None:
        """Perform periodic health check."""
        try:
            # Check scheduler status
            if self.scheduler:
                scheduler_status = await self.scheduler.get_scheduler_status()
                if scheduler_status.get('scheduler_status') != 'running':
                    logger.warning(f"Scheduler not running: {scheduler_status}")
            
            # Check orchestrator status
            if self.orchestrator:
                orchestrator_status = await self.orchestrator.get_orchestrator_status()
                total_workflows = orchestrator_status.get('total_workflows', 0)
                success_rate = orchestrator_status.get('success_rate', 0)
                
                if total_workflows > 0 and success_rate < 0.8:
                    logger.warning(f"Low workflow success rate: {success_rate:.2%}")
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(self.stop())
    
    async def get_system_status(self) -> dict:
        """Get comprehensive system status."""
        status = {
            'system_running': self.is_running,
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }
        
        # Scheduler status
        if self.scheduler:
            status['components']['scheduler'] = await self.scheduler.get_scheduler_status()
        
        # Orchestrator status
        if self.orchestrator:
            status['components']['orchestrator'] = await self.orchestrator.get_orchestrator_status()
        
        # Memory store status
        if self.memory_store:
            status['components']['memory_store'] = {
                'healthy': self.memory_store.is_healthy(),
                'records_count': len(self.memory_store.records) if hasattr(self.memory_store, 'records') else 'unknown'
            }
        
        # LLM client status
        if self.llm_client:
            status['components']['llm_client'] = {
                'available': await self.llm_client.is_available()
            }
        
        return status


async def run_interactive_mode(system: EmployeeMonitoringSystem) -> None:
    """Run the system in interactive mode with command interface."""
    print("\n🎮 Interactive Mode - Available Commands:")
    print("  status    - Show system status")
    print("  tasks     - Show scheduled tasks")
    print("  workflows - Show active workflows")
    print("  run <task_id> - Run a task immediately")
    print("  health    - Detailed health check")
    print("  help      - Show this help")
    print("  quit      - Exit interactive mode")
    print("-" * 50)
    
    while system.is_running:
        try:
            command = input("\n🔧 Enter command: ").strip().lower()
            
            if command == 'quit' or command == 'exit':
                break
            elif command == 'status':
                await _show_system_status(system)
            elif command == 'tasks':
                await _show_scheduled_tasks(system)
            elif command == 'workflows':
                await _show_active_workflows(system)
            elif command.startswith('run '):
                task_id = command[4:].strip()
                await _run_task_immediately(system, task_id)
            elif command == 'health':
                await _show_detailed_health(system)
            elif command == 'help':
                print("\n🎮 Interactive Mode - Available Commands:")
                print("  status    - Show system status")
                print("  tasks     - Show scheduled tasks")
                print("  workflows - Show active workflows")
                print("  run <task_id> - Run a task immediately")
                print("  health    - Detailed health check")
                print("  help      - Show this help")
                print("  quit      - Exit interactive mode")
            else:
                print("❌ Unknown command. Type 'help' for available commands.")
                
        except (EOFError, KeyboardInterrupt):
            break
        except Exception as e:
            print(f"❌ Error executing command: {e}")
    
    print("\n👋 Exiting interactive mode...")


async def _show_system_status(system: EmployeeMonitoringSystem) -> None:
    """Show comprehensive system status."""
    status = await system.get_system_status()
    
    print(f"\n📊 System Status: {'🟢 RUNNING' if status['system_running'] else '🔴 STOPPED'}")
    print(f"🕐 Timestamp: {status['timestamp']}")
    
    for component, comp_status in status['components'].items():
        print(f"\n📦 {component.title()}:")
        for key, value in comp_status.items():
            if isinstance(value, float) and key.endswith('_rate'):
                print(f"   {key}: {value:.2%}")
            else:
                print(f"   {key}: {value}")


async def _show_scheduled_tasks(system: EmployeeMonitoringSystem) -> None:
    """Show scheduled tasks."""
    if not system.scheduler:
        print("❌ Scheduler not available")
        return
    
    tasks = await system.scheduler.get_scheduled_tasks()
    
    if not tasks:
        print("📋 No scheduled tasks")
        return
    
    print(f"\n📋 Scheduled Tasks ({len(tasks)}):")
    for task in tasks:
        status_icon = "✅" if task.enabled else "❌"
        next_run = task.next_run.strftime('%Y-%m-%d %H:%M') if task.next_run else "Not scheduled"
        
        print(f"   {status_icon} {task.name}")
        print(f"      ID: {task.task_id}")
        print(f"      Schedule: {task.schedule_expression}")
        print(f"      Next run: {next_run}")
        print(f"      Status: {task.status.value}")
        print(f"      Runs: {task.run_count} ({task.success_count} success, {task.failure_count} failed)")
        print()


async def _show_active_workflows(system: EmployeeMonitoringSystem) -> None:
    """Show active workflows."""
    if not system.orchestrator:
        print("❌ Orchestrator not available")
        return
    
    workflows = await system.orchestrator.get_active_workflows()
    
    if not workflows:
        print("🔄 No active workflows")
        return
    
    print(f"\n🔄 Active Workflows ({len(workflows)}):")
    for workflow in workflows:
        duration = datetime.now() - workflow.start_time
        print(f"   🔄 {workflow.workflow_id}")
        print(f"      Type: {workflow.workflow_type.value}")
        print(f"      Status: {workflow.status.value}")
        print(f"      Started: {workflow.start_time.strftime('%H:%M:%S')}")
        print(f"      Duration: {duration}")
        print()


async def _run_task_immediately(system: EmployeeMonitoringSystem, task_id: str) -> None:
    """Run a task immediately."""
    if not system.scheduler:
        print("❌ Scheduler not available")
        return
    
    success = await system.scheduler.run_task_now(task_id)
    if success:
        print(f"✅ Task {task_id} started immediately")
    else:
        print(f"❌ Failed to start task {task_id}")


async def _show_detailed_health(system: EmployeeMonitoringSystem) -> None:
    """Show detailed health information."""
    print("\n🏥 Detailed Health Check:")
    
    # System components
    status = await system.get_system_status()
    
    for component, comp_status in status['components'].items():
        health_icon = "🟢" if str(comp_status.get('status', comp_status.get('healthy', 'unknown'))).lower() in ['healthy', 'running', 'available'] else "🔴"
        print(f"   {health_icon} {component.title()}: {comp_status.get('status', comp_status.get('healthy', 'unknown'))}")
    
    # Recent activity
    if system.scheduler:
        tasks = await system.scheduler.get_scheduled_tasks()
        recent_runs = [t for t in tasks if t.last_run and (datetime.now() - t.last_run).hours < 24]
        
        print(f"\n📈 Recent Activity (last 24h):")
        print(f"   Tasks run: {len(recent_runs)}")
        if recent_runs:
            successful = sum(1 for t in recent_runs if t.status.value in ['completed'])
            print(f"   Success rate: {successful/len(recent_runs):.1%}")


async def main():
    """Main entry point."""
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description='MTS MultAgent Employee Monitoring System')
    parser.add_argument('--interactive', '-i', action='store_true', 
                       help='Run in interactive mode')
    parser.add_argument('--single-run', '-s', action='store_true',
                       help='Run a single comprehensive analysis and exit')
    parser.add_argument('--config-test', '-c', action='store_true',
                       help='Test configuration and exit')
    
    args = parser.parse_args()
    
    # Configuration test mode
    if args.config_test:
        try:
            config = get_employee_monitoring_config()
            if config:
                print("✅ Configuration loaded successfully")
                print(f"📁 Reports directory: {config.get('reports', {}).get('base_dir')}")
                print(f"👥 Employees configured: {len(config.get('employees', {}).get('list', []))}")
                print(f"🔗 Jira projects: {len(config.get('jira', {}).get('projects', []))}")
                return
            else:
                print("❌ Failed to load configuration")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Configuration test failed: {e}")
            sys.exit(1)
    
    # Initialize system
    system = EmployeeMonitoringSystem()
    
    try:
        if args.single_run:
            # Single run mode
            logger.info("Running single comprehensive analysis...")
            
            # Initialize components
            system.memory_store = JSONMemoryStore()
            system.llm_client = LLMClient()
            system.orchestrator = EmployeeMonitoringOrchestrator()
            
            # Run comprehensive analysis
            execution = await system.orchestrator.start_comprehensive_monitoring({
                'source': 'single_run',
                'timestamp': datetime.now().isoformat()
            })
            
            print(f"\n📊 Analysis completed: {execution.workflow_id}")
            print(f"   Status: {execution.status.value}")
            print(f"   Duration: {execution.end_time - execution.start_time}")
            print(f"   Steps completed: {len(execution.results)}")
            
        else:
            # Normal mode with optional interactive interface
            if args.interactive:
                # Start system in background
                system_task = asyncio.create_task(system.start())
                
                # Wait a bit for startup
                await asyncio.sleep(2)
                
                # Run interactive mode
                await run_interactive_mode(system)
                
                # Stop system
                await system.stop()
                
            else:
                # Normal daemon mode
                await system.start()
                
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"System error: {e}")
        sys.exit(1)
    finally:
        await system.stop()


if __name__ == "__main__":
    asyncio.run(main())
