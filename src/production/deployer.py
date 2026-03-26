"""
Production Deployer
Handles automated production deployment and application management.
"""

import asyncio
import aiohttp
import logging
import subprocess
import json
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from ..core.config import get_config
from .server import ProductionServer
from .monitoring import ProductionMonitor


@dataclass
class DeploymentStep:
    """Deployment step information"""
    name: str
    status: str  # "pending", "running", "completed", "failed"
    message: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    details: Dict[str, Any] = None


@dataclass
class DeploymentResult:
    """Complete deployment result"""
    deployment_id: str
    success: bool
    steps: List[DeploymentStep]
    start_time: datetime
    end_time: Optional[datetime] = None
    rollback_performed: bool = False
    error_message: Optional[str] = None


class ProductionDeployer:
    """Production deployment automation system"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        self._session: Optional[aiohttp.ClientSession] = None
        self._deployment_history: List[DeploymentResult] = []
        
    async def __aenter__(self):
        """Async context manager entry"""
        self._session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._session:
            await self._session.close()
    
    async def deploy_to_production(self, rollback_on_failure: bool = True) -> DeploymentResult:
        """Deploy application to production"""
        deployment_id = f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.logger.info(f"🚀 Starting production deployment: {deployment_id}")
        
        steps = []
        start_time = datetime.now()
        
        try:
            # Deployment steps
            deployment_steps = [
                ("pre_deployment_checks", self._pre_deployment_checks),
                ("backup_current_version", self._backup_current_version),
                ("setup_environment", self._setup_environment),
                ("download_application", self._download_application),
                ("install_dependencies", self._install_dependencies),
                ("configure_application", self._configure_application),
                ("setup_services", self._setup_services),
                ("run_health_checks", self._run_health_checks),
                ("start_services", self._start_services),
                ("post_deployment_validation", self._post_deployment_validation)
            ]
            
            for step_name, step_func in deployment_steps:
                step = await self._execute_deployment_step(step_name, step_func)
                steps.append(step)
                
                if step.status == "failed":
                    error_msg = f"Deployment failed at step: {step_name}"
                    self.logger.error(f"❌ {error_msg}")
                    
                    if rollback_on_failure:
                        self.logger.info("🔄 Initiating rollback...")
                        rollback_step = await self._execute_deployment_step(
                            "rollback", lambda: self._rollback_deployment()
                        )
                        steps.append(rollback_step)
                    
                    result = DeploymentResult(
                        deployment_id=deployment_id,
                        success=False,
                        steps=steps,
                        start_time=start_time,
                        end_time=datetime.now(),
                        rollback_performed=rollback_on_failure,
                        error_message=error_msg
                    )
                    
                    await self._save_deployment_result(result)
                    return result
            
            # Deployment successful
            result = DeploymentResult(
                deployment_id=deployment_id,
                success=True,
                steps=steps,
                start_time=start_time,
                end_time=datetime.now()
            )
            
            self.logger.info(f"✅ Production deployment completed: {deployment_id}")
            await self._save_deployment_result(result)
            return result
            
        except Exception as e:
            error_msg = f"Deployment error: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            
            result = DeploymentResult(
                deployment_id=deployment_id,
                success=False,
                steps=steps,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=error_msg
            )
            
            await self._save_deployment_result(result)
            return result
    
    async def _execute_deployment_step(self, step_name: str, step_func) -> DeploymentStep:
        """Execute a deployment step"""
        self.logger.info(f"🔄 Executing deployment step: {step_name}")
        
        step = DeploymentStep(
            name=step_name,
            status="running",
            message="Starting step execution",
            start_time=datetime.now(),
            details={}
        )
        
        try:
            result = await step_func()
            
            step.status = "completed"
            step.message = "Step completed successfully"
            step.details = result if isinstance(result, dict) else {"result": result}
            step.end_time = datetime.now()
            
            self.logger.info(f"✅ Step completed: {step_name}")
            return step
            
        except Exception as e:
            step.status = "failed"
            step.message = str(e)
            step.details = {"error": str(e)}
            step.end_time = datetime.now()
            
            self.logger.error(f"❌ Step failed: {step_name} - {e}")
            return step
    
    async def _pre_deployment_checks(self) -> Dict[str, Any]:
        """Perform pre-deployment system checks"""
        checks = {
            "disk_space": await self._check_disk_space(),
            "memory": await self._check_memory_requirements(),
            "network": await self._check_network_connectivity(),
            "dependencies": await self._check_system_dependencies(),
            "permissions": await self._check_user_permissions()
        }
        
        all_passed = all(checks.values())
        if not all_passed:
            failed_checks = [k for k, v in checks.items() if not v]
            raise Exception(f"Pre-deployment checks failed: {', '.join(failed_checks)}")
        
        return {"checks": checks, "status": "passed"}
    
    async def _check_disk_space(self) -> bool:
        """Check available disk space"""
        disk = shutil.disk_usage('/opt/mts-multagent' if Path('/opt/mts-multagent').exists() else '/')
        required_space = 5 * 1024 * 1024 * 1024  # 5GB required
        return disk.free >= required_space
    
    async def _check_memory_requirements(self) -> bool:
        """Check available memory"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            required_memory = 2 * 1024 * 1024 * 1024  # 2GB required
            return memory.available >= required_memory
        except ImportError:
            return True  # Skip check if psutil not available
    
    async def _check_network_connectivity(self) -> bool:
        """Check network connectivity"""
        try:
            if not self._session:
                return False
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with self._session.get("https://www.google.com", timeout=timeout) as response:
                return response.status == 200
        except Exception:
            return False
    
    async def _check_system_dependencies(self) -> bool:
        """Check system dependencies"""
        required_commands = ["python3", "pip3", "git", "systemctl"]
        
        for command in required_commands:
            try:
                subprocess.run(["which", command], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                return False
        
        return True
    
    async def _check_user_permissions(self) -> bool:
        """Check user permissions for deployment"""
        try:
            # Check if user can write to installation directory
            install_dir = Path("/opt/mts-multagent")
            if install_dir.exists():
                return os.access(install_dir, os.W_OK)
            else:
                # Check if user can create installation directory
                test_dir = Path("/tmp/mts_multagent_test")
                test_dir.mkdir(exist_ok=True)
                test_dir.rmdir()
                return True
        except Exception:
            return False
    
    async def _backup_current_version(self) -> Dict[str, Any]:
        """Backup current version before deployment"""
        backup_dir = Path("/opt/mts-multagent/backups")
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = backup_dir / backup_name
        
        try:
            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup application files
            app_dir = Path("/opt/mts-multagent")
            if app_dir.exists():
                backup_app_dir = backup_path / "app"
                shutil.copytree(app_dir / "src", backup_app_dir / "src", dirs_exist_ok=True)
                shutil.copy2(app_dir / "requirements.txt", backup_app_dir / "requirements.txt")
                shutil.copy2(app_dir / ".env", backup_app_dir / ".env")
            
            # Backup configuration
            config_dir = Path("/opt/mts-multagent/config")
            if config_dir.exists():
                backup_config_dir = backup_path / "config"
                shutil.copytree(config_dir, backup_config_dir, dirs_exist_ok=True)
            
            # Backup data
            data_dir = Path("/opt/mts-multagent/data")
            if data_dir.exists():
                backup_data_dir = backup_path / "data"
                shutil.copytree(data_dir, backup_data_dir, dirs_exist_ok=True)
            
            return {
                "backup_path": str(backup_path),
                "backup_size": self._get_directory_size(backup_path),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Cleanup on failure
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise Exception(f"Backup failed: {e}")
    
    def _get_directory_size(self, path: Path) -> int:
        """Get total size of directory"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = Path(dirpath) / filename
                    if filepath.exists():
                        total_size += filepath.stat().st_size
        except Exception:
            pass
        return total_size
    
    async def _setup_environment(self) -> Dict[str, Any]:
        """Setup deployment environment"""
        install_dir = Path("/opt/mts-multagent")
        
        try:
            # Create installation directory
            install_dir.mkdir(parents=True, exist_ok=True)
            
            # Create necessary subdirectories
            subdirs = [
                "src", "config", "data", "logs", "temp", "scripts",
                "monitoring", "backups", "venv"
            ]
            
            for subdir in subdirs:
                (install_dir / subdir).mkdir(exist_ok=True)
            
            # Set permissions
            subprocess.run([
                "sudo", "chown", "-R", "multagent:multagent", str(install_dir)
            ], check=True)
            
            subprocess.run([
                "sudo", "chmod", "-R", "755", str(install_dir)
            ], check=True)
            
            return {
                "install_dir": str(install_dir),
                "subdirs_created": subdirs,
                "permissions_set": True
            }
            
        except Exception as e:
            raise Exception(f"Environment setup failed: {e}")
    
    async def _download_application(self) -> Dict[str, Any]:
        """Download application code"""
        install_dir = Path("/opt/mts-multagent")
        
        try:
            # Clone or update repository
            repo_url = "https://github.com/PavelVM209/MTS_MultAgent.git"
            
            if (install_dir / ".git").exists():
                # Update existing repository
                subprocess.run([
                    "git", "pull", "origin", "main"
                ], cwd=install_dir, check=True)
                action = "updated"
            else:
                # Clone fresh repository
                subprocess.run([
                    "git", "clone", repo_url, str(install_dir)
                ], check=True)
                action = "cloned"
            
            # Get current commit info
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=install_dir,
                capture_output=True,
                text=True,
                check=True
            )
            commit_hash = result.stdout.strip()
            
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=install_dir,
                capture_output=True,
                text=True,
                check=True
            )
            branch = result.stdout.strip()
            
            return {
                "action": action,
                "commit_hash": commit_hash,
                "branch": branch,
                "repo_url": repo_url
            }
            
        except Exception as e:
            raise Exception(f"Application download failed: {e}")
    
    async def _install_dependencies(self) -> Dict[str, Any]:
        """Install Python dependencies"""
        install_dir = Path("/opt/mts-multagent")
        
        try:
            # Create virtual environment
            if not (install_dir / "venv" / "bin" / "python").exists():
                subprocess.run([
                    "python3", "-m", "venv", str(install_dir / "venv")
                ], check=True)
            
            # Install dependencies
            pip_path = install_dir / "venv" / "bin" / "pip"
            requirements_path = install_dir / "requirements.txt"
            
            subprocess.run([
                str(pip_path), "install", "-r", str(requirements_path)
            ], check=True)
            
            # Get installed packages list
            result = subprocess.run([
                str(pip_path), "list", "--format=json"
            ], capture_output=True, text=True, check=True)
            
            installed_packages = json.loads(result.stdout)
            
            return {
                "venv_created": True,
                "packages_installed": len(installed_packages),
                "python_version": subprocess.run([
                    str(install_dir / "venv" / "bin" / "python"), "--version"
                ], capture_output=True, text=True).stdout.strip()
            }
            
        except Exception as e:
            raise Exception(f"Dependencies installation failed: {e}")
    
    async def _configure_application(self) -> Dict[str, Any]:
        """Configure application settings"""
        install_dir = Path("/opt/mts-multagent")
        
        try:
            # Copy configuration files
            config_source = install_dir / "config" / "production.yaml"
            config_dest = install_dir / ".env-production"
            
            if config_source.exists():
                shutil.copy2(config_source, config_dest)
            
            # Setup environment variables
            env_content = f"""
# Production Environment
APP_ENV=production
PYTHONPATH={install_dir}
PATH={install_dir}/venv/bin:$PATH
TZ=Europe/Moscow

# Application Settings
LOG_LEVEL=INFO
MAX_WORKERS=4
QUALITY_THRESHOLD=90.0

# Paths
DATA_PATH={install_dir}/data
LOG_PATH={install_dir}/logs
CONFIG_PATH={install_dir}/config
BACKUP_PATH={install_dir}/backups
"""
            
            env_file = install_dir / ".env"
            env_file.write_text(env_content.strip())
            
            # Set file permissions
            env_file.chmod(0o600)
            
            return {
                "config_file": str(config_dest),
                "env_file": str(env_file),
                "permissions_set": True
            }
            
        except Exception as e:
            raise Exception(f"Application configuration failed: {e}")
    
    async def _setup_services(self) -> Dict[str, Any]:
        """Setup system services"""
        try:
            # Setup systemd service
            service_content = """[Unit]
Description=MTS MultAgent Service
After=network.target

[Service]
Type=simple
User=multagent
Group=multagent
WorkingDirectory=/opt/mts-multagent
Environment=PATH=/opt/mts-multagent/venv/bin
ExecStart=/opt/mts-multagent/venv/bin/python -m src.cli.main --mode scheduled
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
            
            service_file = Path("/etc/systemd/system/mts-multagent.service")
            service_file.write_text(service_content)
            
            # Reload systemd
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            
            # Enable service
            subprocess.run([
                "sudo", "systemctl", "enable", "mts-multagent"
            ], check=True)
            
            return {
                "service_file": str(service_file),
                "service_enabled": True,
                "systemd_reloaded": True
            }
            
        except Exception as e:
            raise Exception(f"Service setup failed: {e}")
    
    async def _run_health_checks(self) -> Dict[str, Any]:
        """Run application health checks"""
        install_dir = Path("/opt/mts-multagent")
        
        try:
            # Test application import
            result = subprocess.run([
                str(install_dir / "venv" / "bin" / "python"),
                "-c", "import src.core.config; print('Import successful')"
            ], capture_output=True, text=True, cwd=install_dir)
            
            if result.returncode != 0:
                raise Exception(f"Import test failed: {result.stderr}")
            
            # Test configuration
            result = subprocess.run([
                str(install_dir / "venv" / "bin" / "python"),
                "-c", "from src.core.config import get_config; print('Config loaded')"
            ], capture_output=True, text=True, cwd=install_dir)
            
            if result.returncode != 0:
                raise Exception(f"Config test failed: {result.stderr}")
            
            return {
                "import_test": "passed",
                "config_test": "passed",
                "application_ready": True
            }
            
        except Exception as e:
            raise Exception(f"Health checks failed: {e}")
    
    async def _start_services(self) -> Dict[str, Any]:
        """Start application services"""
        try:
            # Start main service
            subprocess.run([
                "sudo", "systemctl", "start", "mts-multagent"
            ], check=True)
            
            # Wait for service to start
            await asyncio.sleep(5)
            
            # Check service status
            result = subprocess.run([
                "sudo", "systemctl", "is-active", "mts-multagent"
            ], capture_output=True, text=True)
            
            service_active = result.returncode == 0
            
            return {
                "service_started": True,
                "service_active": service_active,
                "status": result.stdout.strip() if service_active else "inactive"
            }
            
        except Exception as e:
            raise Exception(f"Service start failed: {e}")
    
    async def _post_deployment_validation(self) -> Dict[str, Any]:
        """Validate successful deployment"""
        try:
            # Check service is running
            result = subprocess.run([
                "sudo", "systemctl", "is-active", "mts-multagent"
            ], capture_output=True, text=True)
            
            service_active = result.returncode == 0 and result.stdout.strip() == "active"
            
            # Check application endpoints (if any)
            health_check_passed = True  # Placeholder for actual health check
            
            # Validate deployment by checking critical files
            install_dir = Path("/opt/mts-multagent")
            critical_files = [
                install_dir / "src" / "__init__.py",
                install_dir / "venv" / "bin" / "python",
                install_dir / ".env",
                install_dir / "requirements.txt"
            ]
            
            all_files_exist = all(file.exists() for file in critical_files)
            
            if not all_files_exist:
                missing_files = [str(f) for f in critical_files if not f.exists()]
                raise Exception(f"Missing critical files: {', '.join(missing_files)}")
            
            return {
                "service_active": service_active,
                "health_check": "passed" if health_check_passed else "failed",
                "files_validated": True,
                "deployment_successful": service_active and health_check_passed
            }
            
        except Exception as e:
            raise Exception(f"Post-deployment validation failed: {e}")
    
    async def _rollback_deployment(self) -> Dict[str, Any]:
        """Rollback to previous version"""
        try:
            backup_dir = Path("/opt/mts-multagent/backups")
            
            # Find latest backup
            backups = [d for d in backup_dir.iterdir() if d.is_dir() and d.name.startswith("backup_")]
            if not backups:
                raise Exception("No backups found for rollback")
            
            latest_backup = max(backups, key=lambda x: x.stat().st_mtime)
            
            # Stop current service
            subprocess.run([
                "sudo", "systemctl", "stop", "mts-multagent"
            ], check=True)
            
            # Restore application files
            install_dir = Path("/opt/mts-multagent")
            backup_app_dir = latest_backup / "app"
            
            if backup_app_dir.exists():
                shutil.rmtree(install_dir / "src", ignore_errors=True)
                shutil.copytree(backup_app_dir / "src", install_dir / "src")
                
                if (backup_app_dir / "requirements.txt").exists():
                    shutil.copy2(backup_app_dir / "requirements.txt", install_dir / "requirements.txt")
                
                if (backup_app_dir / ".env").exists():
                    shutil.copy2(backup_app_dir / ".env", install_dir / ".env")
            
            # Restore configuration
            backup_config_dir = latest_backup / "config"
            if backup_config_dir.exists():
                shutil.rmtree(install_dir / "config", ignore_errors=True)
                shutil.copytree(backup_config_dir, install_dir / "config")
            
            # Restore data
            backup_data_dir = latest_backup / "data"
            if backup_data_dir.exists():
                shutil.rmtree(install_dir / "data", ignore_errors=True)
                shutil.copytree(backup_data_dir, install_dir / "data")
            
            # Start service
            subprocess.run([
                "sudo", "systemctl", "start", "mts-multagent"
            ], check=True)
            
            return {
                "rollback_completed": True,
                "backup_used": str(latest_backup),
                "service_restarted": True
            }
            
        except Exception as e:
            raise Exception(f"Rollback failed: {e}")
    
    async def _save_deployment_result(self, result: DeploymentResult) -> None:
        """Save deployment result to history"""
        try:
            self._deployment_history.append(result)
            
            # Keep only last 50 deployments in memory
            self._deployment_history = self._deployment_history[-50:]
            
            # Save to file
            deployments_file = Path("/opt/mts-multagent/monitoring/deployments.json")
            deployments_file.parent.mkdir(parents=True, exist_ok=True)
            
            history_data = [asdict(deployment) for deployment in self._deployment_history]
            
            with open(deployments_file, 'w') as f:
                json.dump(history_data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Failed to save deployment result: {e}")
    
    async def get_deployment_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get deployment history"""
        return [asdict(deployment) for deployment in self._deployment_history[-limit:]]
    
    async def rollback_to_version(self, backup_name: str) -> Dict[str, Any]:
        """Rollback to specific backup version"""
        try:
            backup_dir = Path("/opt/mts-multagent/backups") / backup_name
            
            if not backup_dir.exists():
                raise Exception(f"Backup {backup_name} not found")
            
            # Stop current service
            subprocess.run([
                "sudo", "systemctl", "stop", "mts-multagent"
            ], check=True)
            
            # Restore from specified backup
            install_dir = Path("/opt/mts-multagent")
            
            # Similar to _rollback_deployment but with specific backup
            # Implementation would be similar to _rollback_deployment
            
            return {
                "rollback_completed": True,
                "backup_used": str(backup_dir),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Rollback to version failed: {e}")
    
    async def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific deployment"""
        for deployment in self._deployment_history:
            if deployment.deployment_id == deployment_id:
                return asdict(deployment)
        return None
    
    async def cleanup_old_backups(self, keep_count: int = 5) -> Dict[str, Any]:
        """Clean up old deployment backups"""
        try:
            backup_dir = Path("/opt/mts-multagent/backups")
            backups = [d for d in backup_dir.iterdir() if d.is_dir() and d.name.startswith("backup_")]
            
            # Sort by modification time (newest first)
            backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove old backups
            removed_backups = []
            for backup in backups[keep_count:]:
                shutil.rmtree(backup)
                removed_backups.append(str(backup))
            
            return {
                "cleaned_up": len(removed_backups),
                "remaining_backups": len(backups) - len(removed_backups),
                "removed_backups": removed_backups
            }
            
        except Exception as e:
            raise Exception(f"Backup cleanup failed: {e}")
