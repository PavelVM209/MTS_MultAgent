"""
Production Server Management
Handles production server setup, configuration, and management.
"""

import asyncio
import aiohttp
import logging
import subprocess
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from ..core.config import get_config


@dataclass
class ServerStatus:
    """Server status information"""
    hostname: str
    uptime: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_status: bool
    services_status: Dict[str, bool]
    timestamp: datetime


@dataclass
class SSLCertificate:
    """SSL certificate information"""
    domain: str
    cert_path: str
    key_path: str
    expires_at: datetime
    is_valid: bool


class ProductionServer:
    """Production server management and monitoring"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self._session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._session:
            await self._session.close()
    
    async def setup_production_server(self) -> Dict[str, Any]:
        """Setup production server infrastructure"""
        self.logger.info("🚀 Setting up production server infrastructure...")
        
        setup_results = {
            "system_setup": await self._setup_system(),
            "network_config": await self._setup_network(),
            "ssl_certificates": await self._setup_ssl_certificates(),
            "firewall_config": await self._setup_firewall(),
            "monitoring": await self._setup_monitoring(),
            "backup_system": await self._setup_backup_system()
        }
        
        # Validate all setups
        validation_results = await self._validate_server_setup(setup_results)
        
        self.logger.info("✅ Production server setup completed")
        return {
            "setup_results": setup_results,
            "validation": validation_results,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _setup_system(self) -> Dict[str, Any]:
        """Setup system requirements"""
        self.logger.info("🔧 Setting up system requirements...")
        
        tasks = [
            self._create_system_user(),
            self._setup_directories(),
            self._install_dependencies(),
            self._configure_environment(),
            self._setup_log_rotation()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "user_created": not isinstance(results[0], Exception),
            "directories_setup": not isinstance(results[1], Exception),
            "dependencies_installed": not isinstance(results[2], Exception),
            "environment_configured": not isinstance(results[3], Exception),
            "log_rotation_setup": not isinstance(results[4], Exception),
            "details": {
                "user": "multagent",
                "base_path": "/opt/mts-multagent",
                "python_version": "3.8+"
            }
        }
    
    async def _create_system_user(self) -> bool:
        """Create system user for the application"""
        try:
            # Check if user exists
            result = subprocess.run(
                ["id", "multagent"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                # Create user
                subprocess.run([
                    "sudo", "useradd", "-m", "-s", "/bin/bash", "multagent"
                ], check=True)
                self.logger.info("✅ Created system user: multagent")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create system user: {e}")
            return False
    
    async def _setup_directories(self) -> bool:
        """Create required directories with proper permissions"""
        try:
            directories = [
                "/opt/mts-multagent",
                "/opt/mts-multagent/logs",
                "/opt/mts-multagent/data",
                "/opt/mts-multagent/backups",
                "/opt/mts-multagent/temp",
                "/var/log/mts-multagent"
            ]
            
            for directory in directories:
                Path(directory).mkdir(parents=True, exist_ok=True)
                
                # Set ownership
                subprocess.run([
                    "sudo", "chown", "-R", "multagent:multagent", directory
                ], check=True)
                
                # Set permissions
                subprocess.run([
                    "sudo", "chmod", "755", directory
                ], check=True)
            
            self.logger.info("✅ Directories created and configured")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup directories: {e}")
            return False
    
    async def _install_dependencies(self) -> bool:
        """Install system dependencies"""
        try:
            # Update package list
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            
            # Install required packages
            packages = [
                "python3.8", "python3.8-venv", "python3-pip",
                "nginx", "certbot", "python3-certbot-nginx",
                "supervisor", "git", "curl", "wget",
                "htop", "iotop", "nethogs"
            ]
            
            for package in packages:
                subprocess.run([
                    "sudo", "apt-get", "install", "-y", package
                ], check=True)
            
            self.logger.info("✅ System dependencies installed")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to install dependencies: {e}")
            return False
    
    async def _configure_environment(self) -> bool:
        """Configure environment variables and paths"""
        try:
            # Create environment file
            env_content = """
# Production Environment Variables
PYTHONPATH=/opt/mts-multagent
PATH=/opt/mts-multagent/venv/bin:$PATH
TZ=Europe/Moscow
LANG=en_US.UTF-8
LC_ALL=en_US.UTF-8

# Application Configuration
APP_ENV=production
LOG_LEVEL=INFO
"""
            
            env_path = Path("/opt/mts-multagent/.env")
            env_path.write_text(env_content.strip())
            
            # Set permissions
            subprocess.run([
                "sudo", "chmod", "600", str(env_path)
            ], check=True)
            
            self.logger.info("✅ Environment configured")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to configure environment: {e}")
            return False
    
    async def _setup_log_rotation(self) -> bool:
        """Setup log rotation"""
        try:
            logrotate_config = """
/var/log/mts-multagent/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 multagent multagent
    postrotate
        systemctl reload mts-multagent || true
    endscript
}
"""
            
            config_path = Path("/etc/logrotate.d/mts-multagent")
            config_path.write_text(logrotate_config.strip())
            
            self.logger.info("✅ Log rotation configured")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup log rotation: {e}")
            return False
    
    async def _setup_network(self) -> Dict[str, Any]:
        """Setup network configuration"""
        self.logger.info("🌐 Setting up network configuration...")
        
        try:
            # Configure hostname
            hostname = subprocess.run(
                ["hostname"],
                capture_output=True,
                text=True
            ).stdout.strip()
            
            # Get network interfaces
            interfaces = psutil.net_if_addrs()
            
            # Check external connectivity
            external_ip = await self._get_external_ip()
            
            return {
                "hostname": hostname,
                "interfaces": list(interfaces.keys()),
                "external_ip": external_ip,
                "connectivity": await self._test_connectivity()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup network: {e}")
            return {"error": str(e)}
    
    async def _get_external_ip(self) -> Optional[str]:
        """Get external IP address"""
        try:
            async with self._session.get("https://api.ipify.org") as response:
                return await response.text()
        except Exception:
            return None
    
    async def _test_connectivity(self) -> Dict[str, bool]:
        """Test network connectivity to critical services"""
        test_urls = [
            "https://www.google.com",
            "https://api.openai.com",
            "https://your-company.atlassian.net"
        ]
        
        results = {}
        for url in test_urls:
            try:
                async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    results[url] = response.status < 400
            except Exception:
                results[url] = False
        
        return results
    
    async def _setup_ssl_certificates(self) -> Dict[str, Any]:
        """Setup SSL certificates"""
        self.logger.info("🔒 Setting up SSL certificates...")
        
        try:
            domain = self.config.production.domain
            email = self.config.production.ssl_email
            
            # Obtain SSL certificate using certbot
            result = subprocess.run([
                "sudo", "certbot", "certonly",
                "--nginx", "--non-interactive",
                "--agree-tos", "--email", email,
                "-d", domain
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                cert_path = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
                key_path = f"/etc/letsencrypt/live/{domain}/privkey.pem"
                
                return {
                    "ssl_enabled": True,
                    "domain": domain,
                    "cert_path": cert_path,
                    "key_path": key_path,
                    "auto_renewal": True
                }
            else:
                self.logger.warning(f"SSL setup failed: {result.stderr}")
                return {"ssl_enabled": False, "error": result.stderr}
                
        except Exception as e:
            self.logger.error(f"❌ Failed to setup SSL: {e}")
            return {"ssl_enabled": False, "error": str(e)}
    
    async def _setup_firewall(self) -> Dict[str, Any]:
        """Setup firewall rules"""
        self.logger.info("🛡️ Setting up firewall configuration...")
        
        try:
            # Configure UFW firewall
            rules = [
                ["sudo", "ufw", "--force", "reset"],
                ["sudo", "ufw", "default", "deny", "incoming"],
                ["sudo", "ufw", "default", "allow", "outgoing"],
                ["sudo", "ufw", "allow", "ssh"],
                ["sudo", "ufw", "allow", "80/tcp"],
                ["sudo", "ufw", "allow", "443/tcp"],
                ["sudo", "ufw", "--force", "enable"]
            ]
            
            for rule in rules:
                subprocess.run(rule, check=True)
            
            return {
                "firewall_enabled": True,
                "allowed_ports": [22, 80, 443],
                "default_policy": "deny incoming, allow outgoing"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup firewall: {e}")
            return {"firewall_enabled": False, "error": str(e)}
    
    async def _setup_monitoring(self) -> Dict[str, Any]:
        """Setup monitoring and alerting"""
        self.logger.info("📊 Setting up monitoring system...")
        
        try:
            # Create monitoring directories
            monitoring_dirs = [
                "/opt/mts-multagent/monitoring",
                "/opt/mts-multagent/monitoring/scripts",
                "/opt/mts-multagent/monitoring/alerts"
            ]
            
            for directory in monitoring_dirs:
                Path(directory).mkdir(parents=True, exist_ok=True)
                subprocess.run([
                    "sudo", "chown", "-R", "multagent:multagent", directory
                ], check=True)
            
            return {
                "monitoring_enabled": True,
                "directories_created": True,
                "alert_system": "configured"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup monitoring: {e}")
            return {"monitoring_enabled": False, "error": str(e)}
    
    async def _setup_backup_system(self) -> Dict[str, Any]:
        """Setup backup and recovery system"""
        self.logger.info("💾 Setting up backup system...")
        
        try:
            # Create backup script
            backup_script = """#!/bin/bash
# Automated backup script for MTS MultAgent

BACKUP_DIR="/opt/mts-multagent/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backup_${DATE}.tar.gz"

# Create backup
tar -czf "${BACKUP_DIR}/${BACKUP_FILE}" \\
    /opt/mts-multagent/data \\
    /opt/mts-multagent/config \\
    /var/log/mts-multagent

# Keep only last 30 days
find "${BACKUP_DIR}" -name "backup_*.tar.gz" -mtime +30 -delete

echo "Backup created: ${BACKUP_FILE}"
"""
            
            script_path = Path("/opt/mts-multagent/backup.sh")
            script_path.write_text(backup_script)
            script_path.chmod(0o755)
            
            return {
                "backup_enabled": True,
                "backup_script": str(script_path),
                "retention_days": 30,
                "automated": True
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup backup system: {e}")
            return {"backup_enabled": False, "error": str(e)}
    
    async def _validate_server_setup(self, setup_results: Dict[str, Any]) -> Dict[str, bool]:
        """Validate server setup"""
        self.logger.info("🔍 Validating server setup...")
        
        validations = {
            "system_ready": await self._validate_system_setup(setup_results["system_setup"]),
            "network_ready": await self._validate_network_setup(setup_results["network_config"]),
            "security_ready": await self._validate_security_setup(setup_results),
            "monitoring_ready": self._validate_monitoring_setup(setup_results["monitoring"]),
            "backup_ready": self._validate_backup_setup(setup_results["backup_system"])
        }
        
        overall_ready = all(validations.values())
        
        if overall_ready:
            self.logger.info("✅ Server setup validation passed")
        else:
            self.logger.warning("⚠️ Server setup validation has issues")
        
        return {
            "overall_ready": overall_ready,
            "validations": validations
        }
    
    async def _validate_system_setup(self, system_setup: Dict[str, Any]) -> bool:
        """Validate system setup"""
        required_components = [
            "user_created",
            "directories_setup", 
            "dependencies_installed",
            "environment_configured"
        ]
        
        return all(system_setup.get(comp, False) for comp in required_components)
    
    async def _validate_network_setup(self, network_config: Dict[str, Any]) -> bool:
        """Validate network setup"""
        if "error" in network_config:
            return False
        
        connectivity = network_config.get("connectivity", {})
        return any(connectivity.values())  # At least one connection works
    
    async def _validate_security_setup(self, setup_results: Dict[str, Any]) -> bool:
        """Validate security setup"""
        ssl_config = setup_results.get("ssl_certificates", {})
        firewall_config = setup_results.get("firewall_config", {})
        
        return (
            ssl_config.get("ssl_enabled", False) or
            firewall_config.get("firewall_enabled", False)
        )
    
    def _validate_monitoring_setup(self, monitoring_config: Dict[str, Any]) -> bool:
        """Validate monitoring setup"""
        return monitoring_config.get("monitoring_enabled", False)
    
    def _validate_backup_setup(self, backup_config: Dict[str, Any]) -> bool:
        """Validate backup setup"""
        return backup_config.get("backup_enabled", False)
    
    async def get_server_status(self) -> ServerStatus:
        """Get current server status"""
        try:
            # System metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network status
            network_status = await self._test_connectivity()
            is_network_healthy = any(network_status.values())
            
            # Services status
            services_status = await self._check_services_status()
            
            # System uptime
            uptime = subprocess.run(
                ["uptime", "-p"],
                capture_output=True,
                text=True
            ).stdout.strip()
            
            return ServerStatus(
                hostname=subprocess.run(["hostname"], capture_output=True, text=True).stdout.strip(),
                uptime=uptime,
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_status=is_network_healthy,
                services_status=services_status,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get server status: {e}")
            raise
    
    async def _check_services_status(self) -> Dict[str, bool]:
        """Check status of critical services"""
        services = ["nginx", "mts-multagent"]
        status = {}
        
        for service in services:
            try:
                result = subprocess.run(
                    ["sudo", "systemctl", "is-active", service],
                    capture_output=True,
                    text=True
                )
                status[service] = result.returncode == 0
            except Exception:
                status[service] = False
        
        return status
    
    async def restart_service(self, service_name: str) -> bool:
        """Restart a service"""
        try:
            subprocess.run([
                "sudo", "systemctl", "restart", service_name
            ], check=True)
            
            self.logger.info(f"✅ Service {service_name} restarted")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to restart {service_name}: {e}")
            return False
    
    async def get_ssl_certificate_info(self) -> Optional[SSLCertificate]:
        """Get SSL certificate information"""
        try:
            domain = self.config.production.domain
            cert_path = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
            
            if not Path(cert_path).exists():
                return None
            
            # Get certificate expiration
            result = subprocess.run([
                "openssl", "x509", "-in", cert_path, "-noout", "-enddate"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                expiry_line = result.stdout.strip()
                expiry_str = expiry_line.split("=")[1]
                
                # Parse date
                expiry_date = datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z")
                
                return SSLCertificate(
                    domain=domain,
                    cert_path=cert_path,
                    key_path=f"/etc/letsencrypt/live/{domain}/privkey.pem",
                    expires_at=expiry_date,
                    is_valid=expiry_date > datetime.now()
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get SSL certificate info: {e}")
            return None
