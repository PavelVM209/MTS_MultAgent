#!/usr/bin/env python3
"""
Configuration validation script for Employee Monitoring System
checks all environment variables, config files and paths
"""

import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class ValidationResult:
    name: str
    status: str  # PASSED, FAILED, WARNING
    message: str
    details: Dict[str, Any] = None

class ConfigurationValidator:
    def __init__(self):
        self.project_root = Path(__file__).parents[1]
        self.results: List[ValidationResult] = []
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def add_result(self, name: str, status: str, message: str, details: Dict = None):
        self.results.append(ValidationResult(name, status, message, details))
        status_icon = "✅" if status == "PASSED" else "❌" if status == "FAILED" else "⚠️"
        self.logger.info(f"{status_icon} {name}: {message}")
    
    def validate_environment_variables(self) -> bool:
        """Проверка всех required environment variables"""
        self.logger.info("🔍 Validating environment variables...")
        
        required_vars = {
            # Jira Configuration
            'JIRA_BASE_URL': str,
            'JIRA_USERNAME': str,
            'JIRA_ACCESS_TOKEN': str,
            'JIRA_PROJECT_KEYS': str,
            
            # LLM Configuration
            'LLM_API_KEY': str,
            'LLM_API_BASE_URL': str,
            'LLM_MODEL': str,
            
            # Confluence Configuration
            'CONFLUENCE_BASE_URL': str,
            'CONFLUENCE_ACCESS_TOKEN': str,
            'CONFLUENCE_PARENT_PAGE_ID': str,
            
            # Paths
            'DAILY_REPORTS_DIR': str,
            'WEEKLY_REPORTS_DIR': str,
            'PROTOCOLS_DIRECTORY_PATH': str,
        }
        
        all_passed = True
        
        for var_name, var_type in required_vars.items():
            value = os.getenv(var_name)
            if not value:
                self.add_result(
                    f"ENV: {var_name}",
                    "FAILED",
                    f"Required environment variable {var_name} is missing"
                )
                all_passed = False
            else:
                # Type validation
                try:
                    if var_type == int:
                        int(value)
                    elif var_type == float:
                        float(value)
                    
                    self.add_result(
                        f"ENV: {var_name}",
                        "PASSED",
                        f"Environment variable {var_name} is set",
                        {"value": value[:50] + "..." if len(value) > 50 else value}
                    )
                except (ValueError, TypeError) as e:
                    self.add_result(
                        f"ENV: {var_name}",
                        "FAILED",
                        f"Environment variable {var_name} has invalid type: {e}"
                    )
                    all_passed = False
        
        return all_passed
    
    def validate_configuration_files(self) -> bool:
        """Проверка конфигурационных файлов YAML"""
        self.logger.info("🔍 Validating configuration files...")
        
        config_files = [
            "config/employee_monitoring.yaml",
            "config/base.yaml",
            "config/development.yaml",
            "config/production.yaml"
        ]
        
        all_passed = True
        
        for config_file in config_files:
            config_path = self.project_root / config_file
            
            if not config_path.exists():
                self.add_result(
                    f"CONFIG: {config_file}",
                    "WARNING",
                    f"Configuration file {config_file} does not exist"
                )
                continue
            
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                # Basic structure validation
                if config_file == "config/employee_monitoring.yaml":
                    required_sections = ["employee_monitoring"]
                    for section in required_sections:
                        if section not in config_data:
                            self.add_result(
                                f"CONFIG: {config_file}",
                                "FAILED",
                                f"Missing required section: {section}"
                            )
                            all_passed = False
                        else:
                            self.add_result(
                                f"CONFIG: {config_file}",
                                "PASSED",
                                f"Configuration file {config_file} has valid structure",
                                {"sections": list(config_data.keys())}
                            )
                else:
                    self.add_result(
                        f"CONFIG: {config_file}",
                        "PASSED",
                        f"Configuration file {config_file} is valid YAML"
                    )
                
            except yaml.YAMLError as e:
                self.add_result(
                    f"CONFIG: {config_file}",
                    "FAILED",
                    f"Invalid YAML in {config_file}: {e}"
                )
                all_passed = False
            except Exception as e:
                self.add_result(
                    f"CONFIG: {config_file}",
                    "FAILED",
                    f"Error reading {config_file}: {e}"
                )
                all_passed = False
        
        return all_passed
    
    def validate_directories_and_paths(self) -> bool:
        """Проверка директорий и путей"""
        self.logger.info("🔍 Validating directories and paths...")
        
        directories = [
            "protocols",
            "reports/daily",
            "reports/weekly",
            "reports/quality",
            "data/memory",
            "src/agents",
            "src/core",
            "tests"
        ]
        
        all_passed = True
        
        for directory in directories:
            dir_path = self.project_root / directory
            
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    self.add_result(
                        f"DIRECTORY: {directory}",
                        "PASSED",
                        f"Directory {directory} created"
                    )
                except Exception as e:
                    self.add_result(
                        f"DIRECTORY: {directory}",
                        "FAILED",
                        f"Cannot create directory {directory}: {e}"
                    )
                    all_passed = False
            else:
                self.add_result(
                    f"DIRECTORY: {directory}",
                    "PASSED",
                    f"Directory {directory} exists"
                )
        
        return all_passed
    
    def validate_api_connectivity(self) -> bool:
        """Базовая проверка API endpoints"""
        self.logger.info("🔍 Validating API connectivity...")
        
        apis = {
            "LLM_API": {
                "url": os.getenv("LLM_API_BASE_URL"),
                "headers": {"Authorization": f"Bearer {os.getenv('LLM_API_KEY')}"}
            },
            "JIRA_API": {
                "url": os.getenv("JIRA_BASE_URL"),
                "auth": (os.getenv("JIRA_USERNAME"), os.getenv("JIRA_ACCESS_TOKEN"))
            },
            "CONFLUENCE_API": {
                "url": os.getenv("CONFLUENCE_BASE_URL"),
                "headers": {"Authorization": f"Bearer {os.getenv('CONFLUENCE_ACCESS_TOKEN')}"}
            }
        }
        
        all_passed = True
        
        for api_name, config in apis.items():
            try:
                url = config["url"]
                headers = config.get("headers", {})
                auth = config.get("auth")
                
                # Simple connectivity test
                response = requests.get(
                    url,
                    headers=headers,
                    auth=auth,
                    timeout=10,
                    verify=False  # Только для теста
                )
                
                if response.status_code in [200, 401, 403]:  # 401/403 значит endpoint существует
                    self.add_result(
                        f"API: {api_name}",
                        "PASSED",
                        f"API {api_name} is reachable",
                        {"status_code": response.status_code, "url": url}
                    )
                else:
                    self.add_result(
                        f"API: {api_name}",
                        "WARNING",
                        f"API {api_name} returned unexpected status: {response.status_code}"
                    )
                    
            except requests.exceptions.Timeout:
                self.add_result(
                    f"API: {api_name}",
                    "WARNING",
                    f"API {api_name} timeout (might be expected)"
                )
            except requests.exceptions.ConnectionError:
                self.add_result(
                    f"API: {api_name}",
                    "FAILED",
                    f"Cannot connect to API {api_name}"
                )
                all_passed = False
            except Exception as e:
                self.add_result(
                    f"API: {api_name}",
                    "WARNING",
                    f"API {api_name} test failed: {e}"
                )
        
        return all_passed
    
    def validate_python_modules(self) -> bool:
        """Проверка доступности Python модулей"""
        self.logger.info("🔍 Validating Python modules...")
        
        required_modules = [
            "yaml",
            "requests",
            "asyncio",
            "pydantic",
            "dotenv",
            "pathlib",
            "logging",
            "datetime"
        ]
        
        all_passed = True
        
        for module_name in required_modules:
            try:
                __import__(module_name)
                self.add_result(
                    f"MODULE: {module_name}",
                    "PASSED",
                    f"Module {module_name} is available"
                )
            except ImportError:
                self.add_result(
                    f"MODULE: {module_name}",
                    "FAILED",
                    f"Module {module_name} is not installed"
                )
                all_passed = False
        
        return all_passed
    
    def generate_report(self) -> str:
        """Генерация отчета валидации"""
        passed = sum(1 for r in self.results if r.status == "PASSED")
        failed = sum(1 for r in self.results if r.status == "FAILED")
        warnings = sum(1 for r in self.results if r.status == "WARNING")
        total = len(self.results)
        
        report = f"""
# Employee Monitoring System - Configuration Validation Report

**Generated:** {datetime.now().isoformat()}
**Total Checks:** {total}
**Passed:** {passed}
**Failed:** {failed}
**Warnings:** {warnings}

## Summary Status: {'✅ HEALTHY' if failed == 0 else '❌ NEEDS ATTENTION'}

## Detailed Results

"""
        
        # Group by category
        categories = {}
        for result in self.results:
            category = result.name.split(':')[0]
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        for category, results in categories.items():
            report += f"### {category}\n\n"
            for result in results:
                icon = "✅" if result.status == "PASSED" else "❌" if result.status == "FAILED" else "⚠️"
                report += f"- {icon} **{result.name}**: {result.message}\n"
                if result.details:
                    for key, value in result.details.items():
                        report += f"  - {key}: {value}\n"
                report += "\n"
        
        # Recommendations
        if failed > 0:
            report += "## Recommendations\n\n"
            report += "1. Fix all FAILED items before proceeding with development\n"
            report += "2. Address WARNING items to improve system reliability\n"
            report += "3. Re-run validation after making changes\n"
        
        return report
    
    def run_full_validation(self) -> bool:
        """Запуск полной валидации"""
        self.logger.info("🚀 Starting comprehensive configuration validation...")
        
        all_passed = True
        
        all_passed &= self.validate_environment_variables()
        all_passed &= self.validate_configuration_files()
        all_passed &= self.validate_directories_and_paths()
        all_passed &= self.validate_python_modules()
        # API connectivity can fail due to network, so don't fail the whole validation
        self.validate_api_connectivity()
        
        # Generate and save report
        report = self.generate_report()
        
        # Save report to file
        reports_dir = self.project_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        report_file = reports_dir / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"📄 Validation report saved to: {report_file}")
        print(f"\n{report}")
        
        return all_passed

if __name__ == "__main__":
    validator = ConfigurationValidator()
    success = validator.run_full_validation()
    
    if not success:
        print("\n❌ Configuration validation failed! Please fix the issues before proceeding.")
        sys.exit(1)
    else:
        print("\n✅ Configuration validation passed! System is ready for development.")
        sys.exit(0)
