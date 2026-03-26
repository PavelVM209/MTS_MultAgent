"""
Enhanced Configuration Manager - Phase 2 Foundation Component

Provides YAML-based configuration management with hot reload,
environment variable substitution, and schema validation.
"""

import os
import yaml
import asyncio
import aiofiles
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
import structlog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
from contextlib import asynccontextmanager

logger = structlog.get_logger()


@dataclass
class ConfigValidationError(Exception):
    """Configuration validation error"""
    message: str
    field_path: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class ConfigLoadError(Exception):
    """Configuration loading error"""
    message: str
    file_path: Optional[str] = None
    original_error: Optional[Exception] = None


@dataclass
class ConfigManagerConfig:
    """Configuration for the config manager itself"""
    base_config_path: Path = Path("config/base.yaml")
    environment_configs_path: Path = Path("config")
    environment: str = "development"
    watch_files: bool = True
    reload_delay_seconds: float = 1.0
    enable_validation: bool = True
    cache_config: bool = True


class ConfigurationWatcher(FileSystemEventHandler):
    """File system watcher for configuration changes"""
    
    def __init__(self, config_manager: 'ConfigurationManager'):
        self.config_manager = config_manager
        self.last_modified = {}
        
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if not file_path.suffix in ['.yaml', '.yml']:
            return
            
        # Debounce rapid file changes
        current_time = datetime.now().timestamp()
        last_time = self.last_modified.get(str(file_path), 0)
        
        if current_time - last_time < self.config_manager.reload_delay:
            return
            
        self.last_modified[str(file_path)] = current_time
        
        # Schedule reload in async context
        if self.config_manager.loop:
            asyncio.run_coroutine_threadsafe(
                self.config_manager.reload_config(),
                self.config_manager.loop
            )


class ConfigurationSchema:
    """Schema validation for configuration"""
    
    REQUIRED_FIELDS = {
        'system': ['name', 'version', 'environment'],
        'scheduler': ['enabled', 'timezone'],
        'storage': ['json_store', 'index_manager', 'reports'],
        'agents': ['jira_analyzer', 'meeting_analyzer'],
        'external_services': ['jira', 'openai']
    }
    
    VALID_ENVIRONMENTS = ['development', 'staging', 'production']
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[ConfigValidationError]:
        """Validate configuration structure and values"""
        errors = []
        
        # Validate required top-level sections
        for section, required_fields in cls.REQUIRED_FIELDS.items():
            if section not in config:
                errors.append(ConfigValidationError(
                    message=f"Missing required section: {section}",
                    field_path=section,
                    error_code="MISSING_SECTION"
                ))
                continue
                
            section_config = config[section]
            if not isinstance(section_config, dict):
                errors.append(ConfigValidationError(
                    message=f"Section {section} must be a dictionary",
                    field_path=section,
                    error_code="INVALID_SECTION_TYPE"
                ))
                continue
                
            # Validate required fields in section
            for required_field in required_fields:
                if required_field not in section_config:
                    errors.append(ConfigValidationError(
                        message=f"Missing required field: {section}.{required_field}",
                        field_path=f"{section}.{required_field}",
                        error_code="MISSING_FIELD"
                    ))
        
        # Validate environment
        if 'system' in config:
            env = config['system'].get('environment')
            if env and env not in cls.VALID_ENVIRONMENTS:
                errors.append(ConfigValidationError(
                    message=f"Invalid environment: {env}. Must be one of {cls.VALID_ENVIRONMENTS}",
                    field_path="system.environment",
                    error_code="INVALID_ENVIRONMENT"
                ))
        
        # Validate scheduler configuration
        if 'scheduler' in config:
            scheduler_config = config['scheduler']
            if not isinstance(scheduler_config.get('enabled'), bool):
                errors.append(ConfigValidationError(
                    message="scheduler.enabled must be a boolean",
                    field_path="scheduler.enabled",
                    error_code="INVALID_TYPE"
                ))
        
        # Validate storage paths
        if 'storage' in config:
            storage_config = config['storage']
            for storage_type in ['json_store', 'index_manager', 'reports']:
                if storage_type in storage_config:
                    path_fields = ['base_path', 'index_path', 'base_path']
                    if storage_type == 'json_store':
                        path_fields = ['base_path', 'backup_path']
                    elif storage_type == 'index_manager':
                        path_fields = ['index_path']
                    elif storage_type == 'reports':
                        path_fields = ['base_path', 'human_readable_path', 'json_path']
                    
                    for path_field in path_fields:
                        if path_field in storage_config[storage_type]:
                            path_value = storage_config[storage_type][path_field]
                            if not isinstance(path_value, str) or not path_value.strip():
                                errors.append(ConfigValidationError(
                                    message=f"Invalid path for {storage_type}.{path_field}",
                                    field_path=f"storage.{storage_type}.{path_field}",
                                    error_code="INVALID_PATH"
                                ))
        
        return errors


class ConfigurationManager:
    """
    Enhanced configuration manager with hot reload and validation.
    
    Provides:
    - YAML-based configuration loading
    - Environment variable substitution
    - Configuration validation
    - Hot reload capabilities
    - Configuration caching
    - Environment-specific overrides
    """
    
    def __init__(self, config: ConfigManagerConfig = None):
        self.config = config or ConfigManagerConfig()
        self.environment = self.config.environment
        
        # Configuration storage
        self._base_config: Optional[Dict[str, Any]] = None
        self._env_config: Optional[Dict[str, Any]] = None
        self._merged_config: Optional[Dict[str, Any]] = None
        self._cached_config: Optional[Dict[str, Any]] = None
        
        # File watching
        self.observer: Optional[Observer] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.reload_delay = self.config.reload_delay_seconds
        
        # Change callbacks
        self._change_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
        # Validation
        self.schema = ConfigurationSchema()
        
        # Lock for thread safety
        self._lock = threading.RLock()
    
    async def load_config(self) -> Dict[str, Any]:
        """
        Load and merge configuration from base, environment, and feature-specific files.
        
        Returns:
            Merged configuration dictionary
            
        Raises:
            ConfigLoadError: If configuration cannot be loaded
            ConfigValidationError: If configuration is invalid
        """
        try:
            with self._lock:
                # Load base configuration
                self._base_config = await self._load_yaml_file(self.config.base_config_path)
                
                # Load environment-specific configuration
                env_config_path = self.config.environment_configs_path / f"{self.environment}.yaml"
                if env_config_path.exists():
                    self._env_config = await self._load_yaml_file(env_config_path)
                else:
                    logger.warning(f"Environment config not found: {env_config_path}")
                    self._env_config = {}
                
                # Load feature-specific configurations
                feature_configs = {}
                feature_config_files = [
                    'employee_monitoring.yaml',
                    'production.yaml'
                ]
                
                for config_file in feature_config_files:
                    config_path = self.config.environment_configs_path / config_file
                    if config_path.exists():
                        try:
                            feature_config = await self._load_yaml_file(config_path)
                            feature_config_name = config_file.replace('.yaml', '')
                            feature_configs[feature_config_name] = feature_config
                            logger.info(f"Loaded feature configuration: {config_file}")
                        except Exception as e:
                            logger.warning(f"Failed to load feature config {config_file}: {e}")
                
                # Merge configurations
                self._merged_config = self._merge_configs(self._base_config, self._env_config)
                
                # Merge feature configurations
                for feature_name, feature_config in feature_configs.items():
                    self._merged_config = self._merge_configs(self._merged_config, feature_config)
                
                # Substitute environment variables
                self._merged_config = self._substitute_env_vars(self._merged_config)
                
                # Validate configuration
                if self.config.enable_validation:
                    validation_errors = self.schema.validate_config(self._merged_config)
                    if validation_errors:
                        error_messages = [error.message for error in validation_errors]
                        raise ConfigValidationError(
                            message=f"Configuration validation failed: {'; '.join(error_messages)}"
                        )
                
                # Cache the merged configuration
                if self.config.cache_config:
                    self._cached_config = self._merged_config.copy()
                
                logger.info("Configuration loaded successfully", environment=self.environment)
                return self._merged_config
                
        except Exception as e:
            if isinstance(e, (ConfigLoadError, ConfigValidationError)):
                raise
            raise ConfigLoadError(
                message=f"Failed to load configuration: {str(e)}",
                original_error=e
            )
    
    async def reload_config(self) -> Dict[str, Any]:
        """
        Reload configuration from files.
        
        Returns:
            Reloaded configuration dictionary
        """
        try:
            logger.info("Reloading configuration...")
            
            # Clear cache
            self._cached_config = None
            
            # Reload configuration
            new_config = await self.load_config()
            
            # Notify callbacks
            for callback in self._change_callbacks:
                try:
                    callback(new_config)
                except Exception as e:
                    logger.error("Configuration change callback failed", error=str(e))
            
            logger.info("Configuration reloaded successfully")
            return new_config
            
        except Exception as e:
            logger.error("Failed to reload configuration", error=str(e))
            raise
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.
        
        Returns:
            Current configuration dictionary
        """
        with self._lock:
            if self._cached_config:
                return self._cached_config
            elif self._merged_config:
                return self._merged_config
            else:
                raise ConfigLoadError("Configuration not loaded. Call load_config() first.")
    
    def get_section(self, section_path: str, default: Any = None) -> Any:
        """
        Get a specific section of configuration using dot notation.
        
        Args:
            section_path: Dot-separated path to configuration section
            default: Default value if section not found
            
        Returns:
            Configuration section value
        """
        config = self.get_config()
        keys = section_path.split('.')
        
        current = config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    async def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load YAML file with async support"""
        try:
            if not file_path.exists():
                raise ConfigLoadError(
                    message=f"Configuration file not found: {file_path}",
                    file_path=str(file_path)
                )
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return yaml.safe_load(content) or {}
                
        except yaml.YAMLError as e:
            raise ConfigLoadError(
                message=f"Invalid YAML in {file_path}: {str(e)}",
                file_path=str(file_path),
                original_error=e
            )
        except Exception as e:
            raise ConfigLoadError(
                message=f"Failed to load {file_path}: {str(e)}",
                file_path=str(file_path),
                original_error=e
            )
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two configuration dictionaries.
        
        Args:
            base: Base configuration
            override: Override configuration
            
        Returns:
            Merged configuration
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _substitute_env_vars(self, config: Any) -> Any:
        """
        Substitute environment variables in configuration values.
        
        Supports patterns:
        - ${VAR_NAME}
        - ${VAR_NAME:default_value}
        
        Args:
            config: Configuration value to process
            
        Returns:
            Processed configuration value
        """
        import re
        
        if isinstance(config, dict):
            return {k: self._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            # Find all environment variable patterns
            pattern = r'\$\{([^}]+)\}'
            
            def replace_var(match):
                var_expr = match.group(1)
                if ':' in var_expr:
                    var_name, default_value = var_expr.split(':', 1)
                else:
                    var_name, default_value = var_expr, ''
                
                return os.getenv(var_name, default_value)
            
            return re.sub(pattern, replace_var, config)
        else:
            return config
    
    def start_watching(self, loop: asyncio.AbstractEventLoop = None):
        """
        Start watching configuration files for changes.
        
        Args:
            loop: Event loop for async operations
        """
        if not self.config.watch_files:
            return
        
        self.loop = loop or asyncio.get_event_loop()
        self.observer = Observer()
        
        # Create watcher
        event_handler = ConfigurationWatcher(self)
        
        # Watch config directory
        watch_path = self.config.environment_configs_path
        self.observer.schedule(event_handler, str(watch_path), recursive=True)
        
        # Start observer
        self.observer.start()
        logger.info("Configuration file watching started", watch_path=str(watch_path))
    
    def stop_watching(self):
        """Stop watching configuration files"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("Configuration file watching stopped")
    
    def add_change_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Add callback for configuration changes.
        
        Args:
            callback: Function to call when configuration changes
        """
        self._change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Remove configuration change callback.
        
        Args:
            callback: Function to remove
        """
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
    
    @asynccontextmanager
    async def auto_reload_context(self):
        """Context manager for automatic reload setup and cleanup"""
        try:
            loop = asyncio.get_event_loop()
            self.start_watching(loop)
            yield self
        finally:
            self.stop_watching()
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information from configuration"""
        config = self.get_config()
        return config.get('system', {})
    
    def get_scheduler_config(self) -> Dict[str, Any]:
        """Get scheduler configuration"""
        return self.get_section('scheduler', {})
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get specific agent configuration"""
        return self.get_section(f'agents.{agent_name}', {})
    
    def get_storage_config(self, storage_type: str) -> Dict[str, Any]:
        """Get storage configuration"""
        return self.get_section(f'storage.{storage_type}', {})
    
    def get_external_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get external service configuration"""
        return self.get_section(f'external_services.{service_name}', {})
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.get_section('system.environment') == 'development'
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.get_section('system.environment') == 'production'
    
    def get_log_level(self) -> str:
        """Get configured log level"""
        return self.get_section('system.log_level', 'INFO')
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on configuration system.
        
        Returns:
            Health check results
        """
        try:
            config = self.get_config()
            
            return {
                "status": "healthy",
                "environment": self.get_section('system.environment'),
                "config_loaded": bool(config),
                "watching_enabled": self.config.watch_files,
                "watching_active": self.observer is not None and self.observer.is_alive(),
                "last_check": datetime.now().isoformat(),
                "validation_enabled": self.config.enable_validation
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "environment": self.environment,
                "last_check": datetime.now().isoformat()
            }


# Global configuration manager instance
_config_manager: Optional[ConfigurationManager] = None


async def get_config_manager() -> ConfigurationManager:
    """Get global configuration manager instance"""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigurationManager()
        await _config_manager.load_config()
    
    return _config_manager


async def reload_global_config() -> Dict[str, Any]:
    """Reload global configuration"""
    config_manager = await get_config_manager()
    return await config_manager.reload_config()


def get_config() -> Dict[str, Any]:
    """Get current global configuration"""
    # This should be called after configuration is loaded
    global _config_manager
    if _config_manager is None:
        raise ConfigLoadError("Configuration not loaded. Call get_config_manager() first.")
    return _config_manager.get_config()


def get_section(section_path: str, default: Any = None) -> Any:
    """Get configuration section using dot notation"""
    config = get_config()
    keys = section_path.split('.')
    
    current = config
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


# Convenience functions for common configuration access
def get_system_config() -> Dict[str, Any]:
    """Get system configuration"""
    return get_section('system', {})


def get_scheduler_config() -> Dict[str, Any]:
    """Get scheduler configuration"""
    return get_section('scheduler', {})


def get_storage_config() -> Dict[str, Any]:
    """Get storage configuration"""
    return get_section('storage', {})


def get_agents_config() -> Dict[str, Any]:
    """Get agents configuration"""
    return get_section('agents', {})


def get_external_services_config() -> Dict[str, Any]:
    """Get external services configuration"""
    return get_section('external_services', {})


def is_development() -> bool:
    """Check if running in development environment"""
    return get_section('system.environment') == 'development'


def is_production() -> bool:
    """Check if running in production environment"""
    return get_section('system.environment') == 'production'


def get_employee_monitoring_config() -> Dict[str, Any]:
    """Get employee monitoring configuration"""
    return get_section('employee_monitoring', {})
