"""
Configuration Management for MTS_MultAgent

This module handles loading and managing configuration from environment variables
and configuration files. Provides a centralized configuration system with
validation and type safety.
"""

import os
from typing import Any, Dict, Optional, Union
from pathlib import Path
from pydantic import BaseModel, Field, validator

from dotenv import load_dotenv

import structlog

logger = structlog.get_logger()


class JiraConfig(BaseModel):
    """Configuration for Jira integration."""
    base_url: str = Field(..., description="Jira base URL")
    access_token: str = Field(..., description="Jira access token")
    username: str = Field(..., description="Jira username")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    
    @validator('base_url')
    def validate_base_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Jira base_url must start with http:// or https://')
        return v


class ConfluenceConfig(BaseModel):
    """Configuration for Confluence integration."""
    base_url: str = Field(..., description="Confluence base URL")
    access_token: str = Field(..., description="Confluence access token")
    space: str = Field(..., description="Confluence space key")
    root_page_id: int = Field(..., description="Root page ID for new pages")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    
    @validator('base_url')
    def validate_base_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Confluence base_url must start with http:// or https://')
        return v


class ExcelConfig(BaseModel):
    """Configuration for Excel file processing."""
    file_path: str = Field(default="data/excel/", description="Path to Excel files")
    sheet_name: str = Field(default="Sheet1", description="Default sheet name")
    max_file_size_mb: int = Field(default=100, description="Maximum file size in MB")
    chunk_size: int = Field(default=1000, description="Chunk size for processing")
    
    @validator('file_path')
    def validate_file_path(cls, v):
        path = Path(v)
        return str(path.absolute())


class LoggingConfig(BaseModel):
    """Configuration for logging."""
    level: str = Field(default="INFO", description="Log level")
    file_path: str = Field(default="logs/mts_agent.log", description="Log file path")
    format: str = Field(default="json", description="Log format (json or text)")
    
    @validator('level')
    def validate_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()


class PerformanceConfig(BaseModel):
    """Configuration for performance tuning."""
    max_concurrent_requests: int = Field(default=10, description="Maximum concurrent requests")
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")
    retry_max_attempts: int = Field(default=3, description="Maximum retry attempts")
    retry_backoff_seconds: int = Field(default=1, description="Retry backoff in seconds")
    
    @validator('max_concurrent_requests')
    def validate_max_requests(cls, v):
        if v < 1 or v > 100:
            raise ValueError('max_concurrent_requests must be between 1 and 100')
        return v


class SecurityConfig(BaseModel):
    """Configuration for security features."""
    enable_auth: bool = Field(default=False, description="Enable authentication")
    secret_key: Optional[str] = Field(default=None, description="Secret key for authentication")
    
    @validator('secret_key')
    def validate_secret_key(cls, v, values):
        if values.get('enable_auth') and not v:
            raise ValueError('secret_key is required when enable_auth is True')
        return v


class WebConfig(BaseModel):
    """Configuration for web interface."""
    host: str = Field(default="localhost", description="Web server host")
    port: int = Field(default=8000, description="Web server port")
    iis_site_port: Optional[int] = Field(default=None, description="IIS site port")
    
    @validator('port')
    def validate_port(cls, v):
        if v < 1 or v > 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v


class AppConfig(BaseModel):
    """Main application configuration."""
    project_name: str = Field(..., description="Project name")
    debug: bool = Field(default=False, description="Debug mode")
    test_mode: bool = Field(default=False, description="Test mode")
    
    jira: JiraConfig
    confluence: ConfluenceConfig
    excel: ExcelConfig
    logging: LoggingConfig
    performance: PerformanceConfig
    security: SecurityConfig
    web: WebConfig


class ConfigManager:
    """
    Configuration manager for the MTS_MultAgent.
    
    Handles loading configuration from environment variables and .env files,
    validates configuration, and provides access to configuration values.
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            env_file: Optional path to .env file
        """
        self.env_file = env_file or ".env"
        self._config: Optional[AppConfig] = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from environment variables."""
        # Load .env file if it exists
        if os.path.exists(self.env_file):
            logger.info(f"Loading configuration from {self.env_file}")
            load_dotenv(self.env_file)
        else:
            logger.warning(f"Environment file {self.env_file} not found, using system environment")
        
        # Prepare configuration dictionary
        config_dict = {
            "project_name": self._get_env_var("PROJECT_NAME", required=True),
            "debug": self._get_env_var("DEBUG", default="false").lower() == "true",
            "test_mode": self._get_env_var("TEST_MODE", default="false").lower() == "true",
            
            "jira": {
                "base_url": self._get_env_var("JIRA_BASE_URL", required=True),
                "access_token": self._get_env_var("JIRA_ACCESS_TOKEN", required=True),
                "username": self._get_env_var("JIRA_USERNAME", required=True),
                "timeout": int(self._get_env_var("WEB_REQUEST_TIMEOUT_IN_SECONDS", default="30")),
            },
            
            "confluence": {
                "base_url": self._get_env_var("CONFLUENCE_BASE_URL", required=True),
                "access_token": self._get_env_var("CONFLUENCE_ACCESS_TOKEN", required=True),
                "space": self._get_env_var("CONFLUENCE_SPACE", required=True),
                "root_page_id": int(self._get_env_var("ROOT_PAGE_ID_TO_ADD_NEW_PAGES", required=True)),
                "timeout": int(self._get_env_var("WEB_REQUEST_TIMEOUT_IN_SECONDS", default="30")),
            },
            
            "excel": {
                "file_path": self._get_env_var("EXCEL_FILE_PATH", default="data/excel/"),
                "sheet_name": self._get_env_var("EXCEL_SHEET_NAME", default="Sheet1"),
                "max_file_size_mb": 100,  # Default value
                "chunk_size": 1000,  # Default value
            },
            
            "logging": {
                "level": self._get_env_var("LOG_LEVEL", default="INFO"),
                "file_path": self._get_env_var("LOG_FILE", default="logs/mts_agent.log"),
                "format": "json",
            },
            
            "performance": {
                "max_concurrent_requests": int(self._get_env_var("MAX_CONCURRENT_REQUESTS", default="10")),
                "cache_ttl_seconds": int(self._get_env_var("CACHE_TTL_SECONDS", default="3600")),
                "retry_max_attempts": int(self._get_env_var("RETRY_MAX_ATTEMPTS", default="3")),
                "retry_backoff_seconds": int(self._get_env_var("RETRY_BACKOFF_SECONDS", default="1")),
            },
            
            "security": {
                "enable_auth": self._get_env_var("ENABLE_AUTH", default="false").lower() == "true",
                "secret_key": self._get_env_var("SECRET_KEY", default=None),
            },
            
            "web": {
                "host": self._get_env_var("HOST", default="localhost"),
                "port": int(self._get_env_var("PORT", default="8000")),
                "iis_site_port": self._get_env_int("IIS_SITE_PORT", default=None),
            }
        }
        
        try:
            self._config = AppConfig(**config_dict)
            logger.info("Configuration loaded successfully", project_name=self._config.project_name)
        except Exception as e:
            logger.error("Failed to load configuration", error=str(e))
            raise
    
    def _get_env_var(self, key: str, required: bool = False, default: Optional[str] = None) -> str:
        """
        Get environment variable with optional default and required validation.
        
        Args:
            key: Environment variable key
            required: Whether the variable is required
            default: Default value if not found
            
        Returns:
            Environment variable value
            
        Raises:
            ValueError: If required variable is not found
        """
        value = os.getenv(key, default)
        if required and value is None:
            raise ValueError(f"Required environment variable {key} not found")
        return value or ""
    
    def _get_env_int(self, key: str, required: bool = False, default: Optional[int] = None) -> Optional[int]:
        """
        Get integer environment variable.
        
        Args:
            key: Environment variable key
            required: Whether the variable is required
            default: Default value if not found
            
        Returns:
            Integer value or None
        """
        value = os.getenv(key)
        if value is None:
            if required:
                raise ValueError(f"Required environment variable {key} not found")
            return default
        
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"Environment variable {key} must be an integer, got: {value}")
    
    @property
    def config(self) -> AppConfig:
        """Get the loaded configuration."""
        if self._config is None:
            raise RuntimeError("Configuration not loaded")
        return self._config
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Configuration dictionary for the agent
        """
        base_config = {
            "debug": self.config.debug,
            "test_mode": self.config.test_mode,
            "logging": self.config.logging.dict(),
            "performance": self.config.performance.dict(),
        }
        
        if agent_name.lower() == "jira":
            base_config["jira"] = self.config.jira.dict()
        elif agent_name.lower() == "confluence":
            base_config["confluence"] = self.config.confluence.dict()
        elif agent_name.lower() == "excel":
            base_config["excel"] = self.config.excel.dict()
        
        return base_config
    
    def validate_required_config(self) -> bool:
        """
        Validate that all required configuration is present.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # This will raise ValidationError if config is invalid
            _ = self.config
            return True
        except Exception as e:
            logger.error("Configuration validation failed", error=str(e))
            return False
    
    def create_directories(self) -> None:
        """Create necessary directories based on configuration."""
        directories = [
            os.path.dirname(self.config.logging.file_path),
            self.config.excel.file_path,
        ]
        
        for directory in directories:
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created directory: {directory}")
    
    def __str__(self) -> str:
        return f"ConfigManager(project={self.config.project_name}, debug={self.config.debug})"


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> AppConfig:
    """
    Get the global configuration instance.
    
    Returns:
        Global configuration
        
    Raises:
        RuntimeError: If configuration is not initialized
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.config


def initialize_config(env_file: Optional[str] = None) -> ConfigManager:
    """
    Initialize the global configuration manager.
    
    Args:
        env_file: Optional path to .env file
        
    Returns:
        Configuration manager instance
    """
    global _config_manager
    _config_manager = ConfigManager(env_file)
    _config_manager.create_directories()
    return _config_manager
