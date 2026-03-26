#!/usr/bin/env python3
"""
MTS Employee Monitoring System Deployment Script

Automates the deployment process including:
- Environment setup
- Dependency installation
- Configuration validation
- Service setup
- Health checks
"""

import os
import sys
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class DeploymentManager:
    """Manages the deployment process for the Employee Monitoring System."""
    
    def __init__(self, environment: str = "development"):
        """Initialize deployment manager.
        
        Args:
            environment: Target environment (development, staging, production)
        """
        self.environment = environment
        self.project_root = Path(__file__).parent
        self.config_dir = self.project_root / "config"
        self.src_dir = self.project_root / "src"
        self.reports_dir = self.project_root / "reports"
        
        # Required directories
        self.required_dirs = [
            self.reports_dir / "daily",
            self.reports_dir / "weekly", 
            self.reports_dir / "quality",
            self.reports_dir / "monitoring",
            self.reports_dir / "scheduler"
        ]
        
        logger.info(f"Deployment manager initialized for {environment} environment")
    
    def check_prerequisites(self) -> bool:
        """Check deployment prerequisites."""
        logger.info("Checking prerequisites...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 8):
            logger.error(f"Python 3.8+ required, found {python_version.major}.{python_version.minor}")
            return False
        
        # Check if required files exist
        required_files = [
            "requirements.txt",
            "config/employee_monitoring.yaml",
            "src/main_employee_monitoring.py",
            ".env.example"
        ]
        
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                logger.error(f"Required file missing: {file_path}")
                return False
        
        logger.info("✅ Prerequisites check passed")
        return True
    
    def setup_environment(self) -> bool:
        """Setup deployment environment."""
        logger.info("Setting up environment...")
        
        try:
            # Create .env file from example if it doesn't exist
            env_file = self.project_root / ".env"
            env_example = self.project_root / ".env.example"
            
            if not env_file.exists() and env_example.exists():
                logger.info("Creating .env file from .env.example")
                with open(env_example, 'r') as src, open(env_file, 'w') as dst:
                    dst.write(src.read())
                
                logger.warning("⚠️  Please update .env file with your actual configuration")
                logger.warning("   Required: JIRA_TOKEN, CONFLUENCE_TOKEN, OPENAI_API_KEY")
            
            # Create required directories
            for directory in self.required_dirs:
                directory.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {directory}")
            
            # Set up Python path
            python_path = os.environ.get('PYTHONPATH', '')
            src_path = str(self.src_dir)
            if src_path not in python_path:
                os.environ['PYTHONPATH'] = f"{src_path}:{python_path}"
            
            logger.info("✅ Environment setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup environment: {e}")
            return False
    
    def install_dependencies(self) -> bool:
        """Install required dependencies."""
        logger.info("Installing dependencies...")
        
        try:
            # Install requirements
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                logger.error(f"Failed to install dependencies: {result.stderr}")
                return False
            
            logger.info("✅ Dependencies installed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False
    
    def validate_configuration(self) -> bool:
        """Validate system configuration."""
        logger.info("Validating configuration...")
        
        try:
            # Test configuration loading
            config_script = self.src_dir / "core" / "config.py"
            result = subprocess.run([
                sys.executable, "-c", 
                f"import sys; sys.path.insert(0, '{self.src_dir}'); "
                "from core.config import get_employee_monitoring_config; "
                "config = get_employee_monitoring_config(); "
                "print('Configuration loaded successfully' if config else 'Configuration failed');"
                "exit(0 if config else 1)"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Configuration validation failed: {result.stdout}")
                return False
            
            logger.info("✅ Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate configuration: {e}")
            return False
    
    def run_tests(self) -> bool:
        """Run system tests."""
        logger.info("Running system tests...")
        
        try:
            # Run basic configuration test
            test_script = self.project_root / "test_employee_monitoring_config.py"
            if test_script.exists():
                result = subprocess.run([
                    sys.executable, str(test_script)
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"Configuration tests failed: {result.stdout}")
                    return False
            
            # Run pytest if available
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pytest", 
                    "tests/test_employee_monitoring_system.py",
                    "-v", "--tb=short"
                ], capture_output=True, text=True, cwd=self.project_root)
                
                if result.returncode != 0:
                    logger.warning(f"Some tests failed: {result.stdout}")
                    # Don't fail deployment for test failures in development
                    if self.environment == "production":
                        return False
                else:
                    logger.info("✅ All tests passed")
                    
            except subprocess.CalledProcessError:
                logger.warning("pytest not available, skipping tests")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to run tests: {e}")
            return False
    
    def setup_services(self) -> bool:
        """Setup system services."""
        logger.info("Setting up system services...")
        
        try:
            # Create systemd service file (Linux only)
            if sys.platform.startswith('linux'):
                service_content = f"""[Unit]
Description=MTS Employee Monitoring System
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'mts-user')}
WorkingDirectory={self.project_root}
Environment=PYTHONPATH={self.src_dir}
ExecStart={sys.executable} {self.src_dir}/main_employee_monitoring.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
                
                service_file = Path("/etc/systemd/system/mts-employee-monitoring.service")
                if os.access("/etc/systemd/system", os.W_OK):
                    with open(service_file, 'w') as f:
                        f.write(service_content)
                    
                    logger.info("✅ Systemd service file created")
                    logger.info("   Enable with: sudo systemctl enable mts-employee-monitoring")
                    logger.info("   Start with: sudo systemctl start mts-employee-monitoring")
                else:
                    logger.warning("Cannot create systemd service file (insufficient permissions)")
            
            # Create startup scripts
            startup_script = self.project_root / "start_system.sh"
            startup_content = f"""#!/bin/bash
# MTS Employee Monitoring System Startup Script

cd {self.project_root}
export PYTHONPATH={self.src_dir}

echo "Starting MTS Employee Monitoring System..."
python src/main_employee_monitoring.py
"""
            
            with open(startup_script, 'w') as f:
                f.write(startup_content)
            startup_script.chmod(0o755)
            
            # Create API server startup script
            api_script = self.project_root / "start_api.sh"
            api_content = f"""#!/bin/bash
# MTS Employee Monitoring API Server Startup Script

cd {self.project_root}
export PYTHONPATH={self.src_dir}

echo "Starting MTS Employee Monitoring API Server..."
python src/api_server.py
"""
            
            with open(api_script, 'w') as f:
                f.write(api_content)
            api_script.chmod(0o755)
            
            logger.info("✅ Service setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup services: {e}")
            return False
    
    def run_health_checks(self) -> bool:
        """Run post-deployment health checks."""
        logger.info("Running health checks...")
        
        try:
            # Test configuration
            config_result = subprocess.run([
                sys.executable, "-c",
                f"import sys; sys.path.insert(0, '{self.src_dir}'); "
                "from core.config import get_employee_monitoring_config; "
                "config = get_employee_monitoring_config(); "
                "print('OK' if config else 'FAIL');"
            ], capture_output=True, text=True)
            
            if config_result.stdout.strip() != "OK":
                logger.error("Configuration health check failed")
                return False
            
            # Test API connectivity (if tokens are configured)
            try:
                api_result = subprocess.run([
                    sys.executable, "-c",
                    f"import sys; sys.path.insert(0, '{self.src_dir}'); "
                    "import asyncio; "
                    "from src.agents.jira_agent import JiraAgent; "
                    "from src.agents.confluence_agent import ConfluenceAgent; "
                    "async def test(): "
                    "  jira = JiraAgent(); "
                    "  confluence = ConfluenceAgent(); "
                    "  jira_ok = await jira.test_connection(); "
                    "  confluence_ok = await confluence.test_connection(); "
                    "  print(f'JIRA: {{jira_ok}}, CONFLUENCE: {{confluence_ok}}'); "
                    "asyncio.run(test());"
                ], capture_output=True, text=True, timeout=30)
                
                if api_result.returncode == 0:
                    logger.info(f"API connectivity check: {api_result.stdout.strip()}")
                else:
                    logger.warning(f"API connectivity check failed: {api_result.stderr}")
                    
            except (subprocess.TimeoutExpired, Exception):
                logger.warning("API connectivity check skipped (tokens may not be configured)")
            
            logger.info("✅ Health checks completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to run health checks: {e}")
            return False
    
    def deploy(self) -> bool:
        """Execute complete deployment process."""
        logger.info(f"Starting deployment for {self.environment} environment...")
        
        steps = [
            ("Prerequisites", self.check_prerequisites),
            ("Environment Setup", self.setup_environment),
            ("Dependencies", self.install_dependencies),
            ("Configuration", self.validate_configuration),
            ("Tests", self.run_tests),
            ("Services", self.setup_services),
            ("Health Checks", self.run_health_checks)
        ]
        
        failed_step = None
        for step_name, step_func in steps:
            logger.info(f"Executing: {step_name}")
            if not step_func():
                failed_step = step_name
                break
            logger.info(f"✅ {step_name} completed")
        
        if failed_step:
            logger.error(f"❌ Deployment failed at: {failed_step}")
            return False
        
        logger.info("🎉 Deployment completed successfully!")
        self.print_next_steps()
        return True
    
    def print_next_steps(self):
        """Print next steps after successful deployment."""
        print("\n" + "="*60)
        print("🎉 MTS EMPLOYEE MONITORING SYSTEM DEPLOYED!")
        print("="*60)
        
        print("\n📋 NEXT STEPS:")
        print("1. Configure your .env file with actual API tokens:")
        print("   - JIRA_TOKEN: Your Jira API token")
        print("   - CONFLUENCE_TOKEN: Your Confluence API token")
        print("   - OPENAI_API_KEY: OpenAI API key (optional)")
        
        print("\n2. Test the system:")
        print(f"   python {self.src_dir}/main_employee_monitoring.py --config-test")
        
        print("\n3. Start the system:")
        print(f"   python {self.src_dir}/main_employee_monitoring.py")
        
        print("\n4. Start API server (optional):")
        print(f"   python {self.src_dir}/api_server.py")
        
        if sys.platform.startswith('linux'):
            print("\n5. Enable as system service (Linux):")
            print("   sudo systemctl enable mts-employee-monitoring")
            print("   sudo systemctl start mts-employee-monitoring")
        
        print("\n📊 Monitoring:")
        print(f"   - Reports will be saved to: {self.reports_dir}")
        print("   - API Documentation: http://localhost:8000/docs")
        print("   - System Monitor: python src/utils/system_monitor.py")
        
        print("\n📚 For more information, see README.md")
        print("="*60)


def main():
    """Main deployment entry point."""
    parser = argparse.ArgumentParser(
        description="Deploy MTS Employee Monitoring System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python deploy.py                    # Deploy to development
  python deploy.py --env staging      # Deploy to staging
  python deploy.py --env production   # Deploy to production
        """
    )
    
    parser.add_argument(
        '--env', '--environment',
        choices=['development', 'staging', 'production'],
        default='development',
        help='Target environment (default: development)'
    )
    
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Skip tests during deployment'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize deployment manager
    deployer = DeploymentManager(environment=args.env)
    
    # Override test step if --skip-tests
    if args.skip_tests:
        deployer.run_tests = lambda: True
        logger.info("Tests skipped by user request")
    
    # Run deployment
    success = deployer.deploy()
    
    if success:
        print("\n✅ Deployment completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Deployment failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
