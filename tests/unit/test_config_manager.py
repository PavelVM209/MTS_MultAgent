"""
Unit Tests for Enhanced Configuration Manager - Phase 2 Foundation Component

Tests YAML-based configuration management with hot reload,
environment variable substitution, and schema validation.
"""

import pytest
import asyncio
import tempfile
import yaml
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from dataclasses import asdict

from src.core.config_manager import (
    ConfigurationManager,
    ConfigManagerConfig,
    ConfigValidationError,
    ConfigLoadError,
    ConfigurationSchema,
    ConfigurationWatcher,
    get_config_manager,
    reload_global_config,
    get_config,
    get_section
)


class TestConfigurationSchema:
    """Test configuration schema validation"""
    
    def test_validate_empty_config(self):
        """Test validation of empty configuration"""
        config = {}
        errors = ConfigurationSchema.validate_config(config)
        
        # Should have errors for all required sections
        assert len(errors) > 0
        error_codes = [error.error_code for error in errors]
        assert "MISSING_SECTION" in error_codes
    
    def test_validate_valid_config(self):
        """Test validation of valid configuration"""
        config = {
            'system': {
                'name': 'test',
                'version': '1.0.0',
                'environment': 'development'
            },
            'scheduler': {
                'enabled': True,
                'timezone': 'Europe/Moscow'
            },
            'storage': {
                'json_store': {'base_path': '/data/json'},
                'index_manager': {'index_path': '/data/index'},
                'reports': {'base_path': '/data/reports'}
            },
            'agents': {
                'jira_analyzer': {'enabled': True},
                'meeting_analyzer': {'enabled': True}
            },
            'external_services': {
                'jira': {'base_url': 'http://jira.com'},
                'openai': {'api_key': 'test-key'}
            }
        }
        
        errors = ConfigurationSchema.validate_config(config)
        assert len(errors) == 0
    
    def test_validate_invalid_environment(self):
        """Test validation of invalid environment"""
        config = {
            'system': {
                'name': 'test',
                'version': '1.0.0',
                'environment': 'invalid_env'
            }
        }
        
        errors = ConfigurationSchema.validate_config(config)
        assert len(errors) >= 1
        
        env_errors = [e for e in errors if e.error_code == "INVALID_ENVIRONMENT"]
        assert len(env_errors) == 1
        assert "invalid_env" in env_errors[0].message
    
    def test_validate_invalid_scheduler_type(self):
        """Test validation of scheduler type"""
        config = {
            'system': {
                'name': 'test',
                'version': '1.0.0',
                'environment': 'development'
            },
            'scheduler': {
                'enabled': 'not_boolean',  # Should be boolean
                'timezone': 'Europe/Moscow'
            }
        }
        
        errors = ConfigurationSchema.validate_config(config)
        assert len(errors) >= 1
        
        type_errors = [e for e in errors if e.error_code == "INVALID_TYPE"]
        assert len(type_errors) == 1
        assert "scheduler.enabled" in type_errors[0].field_path
    
    def test_validate_invalid_paths(self):
        """Test validation of invalid paths"""
        config = {
            'system': {
                'name': 'test',
                'version': '1.0.0',
                'environment': 'development'
            },
            'scheduler': {
                'enabled': True,
                'timezone': 'Europe/Moscow'
            },
            'storage': {
                'json_store': {
                    'base_path': '',  # Invalid empty path
                    'backup_path': 'valid_path'
                },
                'index_manager': {'index_path': '/data/index'},
                'reports': {'base_path': '/data/reports'}
            },
            'agents': {
                'jira_analyzer': {'enabled': True},
                'meeting_analyzer': {'enabled': True}
            },
            'external_services': {
                'jira': {'base_url': 'http://jira.com'},
                'openai': {'api_key': 'test-key'}
            }
        }
        
        errors = ConfigurationSchema.validate_config(config)
        assert len(errors) >= 1
        
        path_errors = [e for e in errors if e.error_code == "INVALID_PATH"]
        assert len(path_errors) >= 1
        assert any("json_store.base_path" in error.field_path for error in path_errors)


class TestConfigurationManager:
    """Test configuration manager functionality"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            yield config_dir
    
    @pytest.fixture
    def base_config(self):
        """Base configuration content"""
        return {
            'system': {
                'name': 'MTS_MultAgent',
                'version': '3.0.0',
                'environment': '${ENVIRONMENT:development}',
                'debug': '${DEBUG:false}'
            },
            'scheduler': {
                'enabled': True,
                'timezone': 'Europe/Moscow'
            },
            'storage': {
                'json_store': {
                    'base_path': '/data/json',
                    'retention_days': 365
                },
                'index_manager': {
                    'index_path': '/data/index'
                },
                'reports': {
                    'base_path': '/data/reports'
                }
            },
            'agents': {
                'jira_analyzer': {
                    'enabled': True,
                    'projects': ['CSI', 'PROJ']
                },
                'meeting_analyzer': {
                    'enabled': True,
                    'max_file_size_mb': 10
                }
            },
            'external_services': {
                'jira': {
                    'base_url': '${JIRA_BASE_URL:http://localhost:8080}',
                    'api_token': '${JIRA_API_TOKEN:}'
                },
                'openai': {
                    'model': '${OPENAI_MODEL:gpt-4}',
                    'api_key': '${OPENAI_API_KEY:}'
                }
            }
        }
    
    @pytest.fixture
    def dev_config(self):
        """Development environment configuration"""
        return {
            'system': {
                'environment': 'development',
                'debug': True
            },
            'scheduler': {
                'enabled': True,
                'daily_schedule': {
                    'jira_analysis': '*/5'  # Every 5 minutes
                }
            },
            'agents': {
                'jira_analyzer': {
                    'projects': ['CSI'],  # Single project for dev
                    'api_timeout': 10
                }
            },
            'external_services': {
                'jira': {
                    'base_url': 'http://localhost:8080'
                },
                'openai': {
                    'model': 'gpt-3.5-turbo'
                }
            }
        }
    
    def setup_config_files(self, temp_dir: Path, base_config: dict, dev_config: dict):
        """Create configuration files"""
        config_dir = temp_dir / "config"
        config_dir.mkdir()
        
        # Write base config
        base_file = config_dir / "base.yaml"
        with open(base_file, 'w') as f:
            yaml.dump(base_config, f)
        
        # Write dev config
        dev_file = config_dir / "development.yaml"
        with open(dev_file, 'w') as f:
            yaml.dump(dev_config, f)
        
        return config_dir
    
    @pytest.mark.asyncio
    async def test_load_base_config(self, temp_config_dir, base_config, dev_config):
        """Test loading base configuration"""
        config_dir = self.setup_config_files(temp_config_dir, base_config, dev_config)
        
        config_manager = ConfigurationManager(ConfigManagerConfig(
            base_config_path=config_dir / "base.yaml",
            environment_configs_path=config_dir,
            environment="development",
            watch_files=False  # Disable watching for tests
        ))
        
        loaded_config = await config_manager.load_config()
        
        # Check that base config was loaded
        assert loaded_config['system']['name'] == 'MTS_MultAgent'
        assert loaded_config['system']['version'] == '3.0.0'
        assert loaded_config['scheduler']['enabled'] is True
        assert loaded_config['agents']['jira_analyzer']['enabled'] is True
    
    @pytest.mark.asyncio
    async def test_load_config_with_env_override(self, temp_config_dir, base_config, dev_config):
        """Test loading configuration with environment override"""
        config_dir = self.setup_config_files(temp_config_dir, base_config, dev_config)
        
        config_manager = ConfigurationManager(ConfigManagerConfig(
            base_config_path=config_dir / "base.yaml",
            environment_configs_path=config_dir,
            environment="development",
            watch_files=False
        ))
        
        loaded_config = await config_manager.load_config()
        
        # Check that environment overrides were applied
        assert loaded_config['system']['environment'] == 'development'
        assert loaded_config['system']['debug'] is True
        assert loaded_config['agents']['jira_analyzer']['projects'] == ['CSI']
        
        # Check that base config values are preserved where not overridden
        assert loaded_config['system']['name'] == 'MTS_MultAgent'
        assert loaded_config['system']['version'] == '3.0.0'
    
    @pytest.mark.asyncio
    async def test_env_variable_substitution(self, temp_config_dir, base_config, dev_config):
        """Test environment variable substitution"""
        config_dir = self.setup_config_files(temp_config_dir, base_config, dev_config)
        
        # Set environment variables
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DEBUG': 'true',
            'JIRA_BASE_URL': 'https://jira.company.com',
            'OPENAI_MODEL': 'gpt-4-turbo'
        }):
            config_manager = ConfigurationManager(ConfigManagerConfig(
                base_config_path=config_dir / "base.yaml",
                environment_configs_path=config_dir,
                environment="production",  # Use production to test env var
                watch_files=False
            ))
            
            loaded_config = await config_manager.load_config()
            
            # Check that environment variables were substituted
            assert loaded_config['system']['environment'] == 'production'
            assert loaded_config['system']['debug'] == 'true'
            assert loaded_config['external_services']['jira']['base_url'] == 'https://jira.company.com'
            assert loaded_config['external_services']['openai']['model'] == 'gpt-4-turbo'
    
    @pytest.mark.asyncio
    async def test_env_variable_default_values(self, temp_config_dir, base_config, dev_config):
        """Test environment variable default values"""
        config_dir = self.setup_config_files(temp_config_dir, base_config, dev_config)
        
        # Don't set environment variables, should use defaults
        with patch.dict(os.environ, {}, clear=True):
            config_manager = ConfigurationManager(ConfigManagerConfig(
                base_config_path=config_dir / "base.yaml",
                environment_configs_path=config_dir,
                environment="production",
                watch_files=False
            ))
            
            loaded_config = await config_manager.load_config()
            
            # Check that default values were used
            assert loaded_config['system']['environment'] == 'production'
            assert loaded_config['system']['debug'] == 'false'
            assert loaded_config['external_services']['jira']['base_url'] == 'http://localhost:8080'
            assert loaded_config['external_services']['openai']['model'] == 'gpt-4'
    
    @pytest.mark.asyncio
    async def test_missing_config_file(self, temp_config_dir):
        """Test handling of missing configuration file"""
        config_manager = ConfigurationManager(ConfigManagerConfig(
            base_config_path=temp_config_dir / "nonexistent.yaml",
            watch_files=False
        ))
        
        with pytest.raises(ConfigLoadError) as exc_info:
            await config_manager.load_config()
        
        assert "Configuration file not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_yaml(self, temp_config_dir):
        """Test handling of invalid YAML"""
        config_file = temp_config_dir / "invalid.yaml"
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        config_manager = ConfigurationManager(ConfigManagerConfig(
            base_config_path=config_file,
            watch_files=False
        ))
        
        with pytest.raises(ConfigLoadError) as exc_info:
            await config_manager.load_config()
        
        assert "Invalid YAML" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_validation_errors(self, temp_config_dir):
        """Test configuration validation errors"""
        config_dir = temp_config_dir / "config"
        config_dir.mkdir()
        
        # Create invalid config (missing required sections)
        invalid_config = {
            'system': {
                'name': 'test'
                # Missing version and environment
            }
        }
        
        base_file = config_dir / "base.yaml"
        with open(base_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        config_manager = ConfigurationManager(ConfigManagerConfig(
            base_config_path=base_file,
            environment_configs_path=config_dir,
            watch_files=False
        ))
        
        with pytest.raises(ConfigValidationError) as exc_info:
            await config_manager.load_config()
        
        assert "Configuration validation failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_section(self, temp_config_dir, base_config, dev_config):
        """Test getting configuration sections"""
        config_dir = self.setup_config_files(temp_config_dir, base_config, dev_config)
        
        config_manager = ConfigurationManager(ConfigManagerConfig(
            base_config_path=config_dir / "base.yaml",
            environment_configs_path=config_dir,
            environment="development",
            watch_files=False
        ))
        
        await config_manager.load_config()
        
        # Test getting existing sections
        system_config = config_manager.get_section('system')
        assert system_config['name'] == 'MTS_MultAgent'
        
        scheduler_config = config_manager.get_section('scheduler')
        assert scheduler_config['enabled'] is True
        
        # Test getting nested sections
        jira_config = config_manager.get_section('agents.jira_analyzer')
        assert jira_config['projects'] == ['CSI']
        
        # Test getting non-existent section with default
        missing = config_manager.get_section('nonexistent.section', 'default_value')
        assert missing == 'default_value'
    
    @pytest.mark.asyncio
    async def test_reload_config(self, temp_config_dir, base_config, dev_config):
        """Test configuration reloading"""
        config_dir = self.setup_config_files(temp_config_dir, base_config, dev_config)
        
        config_manager = ConfigurationManager(ConfigManagerConfig(
            base_config_path=config_dir / "base.yaml",
            environment_configs_path=config_dir,
            environment="development",
            watch_files=False
        ))
        
        # Load initial config
        initial_config = await config_manager.load_config()
        assert initial_config['system']['debug'] is True
        
        # Modify dev config file
        dev_config['system']['debug'] = False
        dev_file = config_dir / "development.yaml"
        with open(dev_file, 'w') as f:
            yaml.dump(dev_config, f)
        
        # Reload config
        reloaded_config = await config_manager.reload_config()
        assert reloaded_config['system']['debug'] is False
    
    @pytest.mark.asyncio
    async def test_change_callbacks(self, temp_config_dir, base_config, dev_config):
        """Test configuration change callbacks"""
        config_dir = self.setup_config_files(temp_config_dir, base_config, dev_config)
        
        config_manager = ConfigurationManager(ConfigManagerConfig(
            base_config_path=config_dir / "base.yaml",
            environment_configs_path=config_dir,
            environment="development",
            watch_files=False
        ))
        
        callback_called = False
        callback_config = None
        
        def test_callback(config):
            nonlocal callback_called, callback_config
            callback_called = True
            callback_config = config
        
        config_manager.add_change_callback(test_callback)
        
        # Load initial config
        await config_manager.load_config()
        
        # Modify and reload
        dev_config['system']['debug'] = False
        dev_file = config_dir / "development.yaml"
        with open(dev_file, 'w') as f:
            yaml.dump(dev_config, f)
        
        await config_manager.reload_config()
        
        # Check callback was called
        assert callback_called
        assert callback_config is not None
        assert callback_config['system']['debug'] is False
        
        # Remove callback
        config_manager.remove_change_callback(test_callback)
        callback_called = False
        
        # Reload again
        await config_manager.reload_config()
        
        # Callback should not be called
        assert not callback_called
    
    def test_thread_safety(self, temp_config_dir, base_config, dev_config):
        """Test thread safety of configuration operations"""
        config_dir = self.setup_config_files(temp_config_dir, base_config, dev_config)
        
        config_manager = ConfigurationManager(ConfigManagerConfig(
            base_config_path=config_dir / "base.yaml",
            environment_configs_path=config_dir,
            environment="development",
            watch_files=False
        ))
        
        # Test that lock works
        with config_manager._lock:
            # Should be able to acquire lock
            assert config_manager._lock._is_owned()
    
    def test_convenience_methods(self, temp_config_dir, base_config, dev_config):
        """Test convenience methods for configuration access"""
        config_dir = self.setup_config_files(temp_config_dir, base_config, dev_config)
        
        config_manager = ConfigurationManager(ConfigManagerConfig(
            base_config_path=config_dir / "base.yaml",
            environment_configs_path=config_dir,
            environment="development",
            watch_files=False
        ))
        
        # Mock loaded config
        config_manager._merged_config = {
            'system': {'environment': 'development', 'debug': True},
            'scheduler': {'enabled': True},
            'storage': {'json_store': {'base_path': '/data/json'}},
            'agents': {'jira_analyzer': {'enabled': True}},
            'external_services': {'jira': {'base_url': 'http://jira.com'}}
        }
        
        # Test convenience methods
        assert config_manager.is_development() is True
        assert config_manager.is_production() is False
        assert config_manager.get_log_level() == 'INFO'
        
        system_info = config_manager.get_system_info()
        assert system_info['environment'] == 'development'
        
        scheduler_config = config_manager.get_scheduler_config()
        assert scheduler_config['enabled'] is True
        
        agent_config = config_manager.get_agent_config('jira_analyzer')
        assert agent_config['enabled'] is True


class TestConfigurationWatcher:
    """Test configuration file watcher"""
    
    def test_watcher_creation(self):
        """Test configuration watcher creation"""
        # Mock config manager
        config_manager = MagicMock()
        config_manager.reload_delay = 1.0
        
        watcher = ConfigurationWatcher(config_manager)
        assert watcher.config_manager == config_manager
        assert isinstance(watcher.last_modified, dict)
    
    def test_watcher_file_filtering(self, temp_config_dir):
        """Test configuration watcher file filtering"""
        # Mock config manager
        config_manager = MagicMock()
        config_manager.reload_delay = 1.0
        
        watcher = ConfigurationWatcher(config_manager)
        
        # Create mock event for non-YAML file
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = str(temp_config_dir / "test.txt")
        
        # Should not trigger reload for non-YAML file
        watcher.on_modified(mock_event)
        
        # Verify reload was not called
        config_manager.reload_config.assert_not_called()
        
        # Create mock event for YAML file
        mock_yaml_event = MagicMock()
        mock_yaml_event.is_directory = False
        mock_yaml_event.src_path = str(temp_config_dir / "config.yaml")
        
        # Should trigger reload for YAML file (but won't actually call due to loop being None)
        watcher.on_modified(mock_yaml_event)


class TestGlobalConfigManager:
    """Test global configuration manager functions"""
    
    @pytest.mark.asyncio
    async def test_get_config_manager(self, temp_config_dir, base_config, dev_config):
        """Test global configuration manager"""
        config_dir = temp_config_dir / "config"
        config_dir.mkdir()
        
        # Write base config
        base_file = config_dir / "base.yaml"
        with open(base_file, 'w') as f:
            yaml.dump(base_config, f)
        
        # Mock environment
        with patch.dict(os.environ, {'ENVIRONMENT': 'development'}):
            # Clear global instance
            from src.core import config_manager
            config_manager._config_manager = None
            
            # Set up config paths
            original_base_path = config_manager.ConfigManagerConfig.base_config_path
            config_manager.ConfigManagerConfig.base_config_path = base_file
            
            try:
                config_mgr = await config_manager.get_config_manager()
                assert config_mgr is not None
                
                # Test that subsequent calls return same instance
                config_mgr2 = await config_manager.get_config_manager()
                assert config_mgr is config_mgr2
                
            finally:
                # Restore original path
                config_manager.ConfigManagerConfig.base_config_path = original_base_path
                config_manager._config_manager = None
    
    @pytest.mark.asyncio
    async def test_config_access_functions(self, temp_config_dir, base_config, dev_config):
        """Test configuration access convenience functions"""
        config_dir = temp_config_dir / "config"
        config_dir.mkdir()
        
        # Write base config
        base_file = config_dir / "base.yaml"
        with open(base_file, 'w') as f:
            yaml.dump(base_config, f)
        
        # Mock environment and global config manager
        with patch.dict(os.environ, {'ENVIRONMENT': 'development'}):
            from src.core import config_manager
            
            # Create and set global config manager
            config_mgr = config_manager.ConfigurationManager(config_manager.ConfigManagerConfig(
                base_config_path=base_file,
                environment="development",
                watch_files=False
            ))
            await config_mgr.load_config()
            config_manager._config_manager = config_mgr
            
            try:
                # Test get_config function
                config = config_manager.get_config()
                assert config['system']['name'] == 'MTS_MultAgent'
                
                # Test get_section function
                system_config = config_manager.get_section('system')
                assert system_config['name'] == 'MTS_MultAgent'
                
                # Test with default
                missing = config_manager.get_section('nonexistent', 'default')
                assert missing == 'default'
                
            finally:
                config_manager._config_manager = None


class TestConfigManagerConfig:
    """Test configuration manager configuration"""
    
    def test_default_config(self):
        """Test default configuration"""
        config = ConfigManagerConfig()
        
        assert config.base_config_path == Path("config/base.yaml")
        assert config.environment_configs_path == Path("config")
        assert config.environment == "development"
        assert config.watch_files is True
        assert config.reload_delay_seconds == 1.0
        assert config.enable_validation is True
        assert config.cache_config is True
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = ConfigManagerConfig(
            base_config_path=Path("/custom/base.yaml"),
            environment="production",
            watch_files=False,
            reload_delay_seconds=2.0
        )
        
        assert config.base_config_path == Path("/custom/base.yaml")
        assert config.environment == "production"
        assert config.watch_files is False
        assert config.reload_delay_seconds == 2.0


class TestConfigManagerHealthCheck:
    """Test configuration manager health check"""
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, temp_config_dir, base_config, dev_config):
        """Test health check when system is healthy"""
        config_dir = self.setup_config_files(temp_config_dir, base_config, dev_config)
        
        config_manager = ConfigurationManager(ConfigManagerConfig(
            base_config_path=config_dir / "base.yaml",
            environment_configs_path=config_dir,
            environment="development",
            watch_files=False
        ))
        
        await config_manager.load_config()
        
        health = await config_manager.health_check()
        
        assert health["status"] == "healthy"
        assert health["environment"] == "development"
        assert health["config_loaded"] is True
        assert health["watching_enabled"] is True
        assert health["validation_enabled"] is True
        assert "last_check" in health
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, temp_config_dir):
        """Test health check when system is unhealthy"""
        config_manager = ConfigurationManager(ConfigManagerConfig(
            base_config_path=temp_config_dir / "nonexistent.yaml",
            watch_files=False
        ))
        
        # Don't load config to simulate unhealthy state
        health = await config_manager.health_check()
        
        assert health["status"] == "unhealthy"
        assert "error" in health
        assert health["environment"] == "development"
        assert "last_check" in health


@pytest.mark.asyncio
async def test_config_manager_edge_cases():
    """Test configuration manager edge cases"""
    
    # Test with empty environment config
    config_manager = ConfigurationManager(ConfigManagerConfig(
        enable_validation=False,  # Disable validation for this test
        watch_files=False
    ))
    
    # Mock config loading to return empty configs
    config_manager._base_config = {}
    config_manager._env_config = {}
    config_manager._merged_config = {}
    config_manager._cached_config = {}
    
    # Test getting sections from empty config
    assert config_manager.get_section('system') is None
    assert config_manager.get_section('system', 'default') == 'default'
    
    # Test convenience methods with empty config
    assert config_manager.is_development() is False
    assert config_manager.is_production() is False
    assert config_manager.get_log_level() == 'INFO'
    
    # Test get_config methods return empty dicts
    assert config_manager.get_system_info() == {}
    assert config_manager.get_scheduler_config() == {}
    assert config_manager.get_agent_config('test') == {}
    assert config_manager.get_storage_config('test') == {}
    assert config_manager.get_external_service_config('test') == {}


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
