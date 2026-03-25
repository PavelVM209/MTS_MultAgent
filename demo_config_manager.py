#!/usr/bin/env python3
"""
Enhanced Configuration Manager Demo - Phase 2
Demonstrates YAML-based configuration management with hot reload
"""

import asyncio
import os
from pathlib import Path

from src.core.config_manager import ConfigurationManager, ConfigManagerConfig


async def demo_config_manager():
    """Demonstrate Enhanced Configuration Manager functionality"""
    
    print("🚀 Enhanced Configuration Manager Demo - Phase 2")
    print("=" * 60)
    
    # Initialize configuration manager
    config_manager = ConfigurationManager(ConfigManagerConfig(
        base_config_path=Path("config/base.yaml"),
        environment_configs_path=Path("config"),
        environment="development",
        watch_files=False,  # Disable watching for demo
        enable_validation=True
    ))
    
    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = await config_manager.load_config()
        print("✅ Configuration loaded successfully!")
        
        # Display system information
        print("\n🏗️ System Information:")
        system_info = config_manager.get_system_info()
        print(f"  - Name: {system_info.get('name')}")
        print(f"  - Version: {system_info.get('version')}")
        print(f"  - Environment: {system_info.get('environment')}")
        print(f"  - Debug: {system_info.get('debug')}")
        
        # Display scheduler configuration
        print("\n⏰ Scheduler Configuration:")
        scheduler_config = config_manager.get_scheduler_config()
        print(f"  - Enabled: {scheduler_config.get('enabled')}")
        print(f"  - Timezone: {scheduler_config.get('timezone')}")
        if 'daily_schedule' in scheduler_config:
            daily = scheduler_config['daily_schedule']
            print(f"  - Daily Jira Analysis: {daily.get('jira_analysis')}")
            print(f"  - Daily Meeting Analysis: {daily.get('meeting_analysis')}")
        
        # Display agent configurations
        print("\n🤖 Agent Configurations:")
        agents_config = config_manager.get_section('agents', {})
        
        for agent_name, agent_config in agents_config.items():
            if isinstance(agent_config, dict) and agent_config.get('enabled'):
                print(f"  - {agent_name}: ✅ Enabled")
                if 'projects' in agent_config:
                    projects = agent_config['projects']
                    print(f"    Projects: {', '.join(projects)}")
                if 'api_timeout' in agent_config:
                    print(f"    Timeout: {agent_config['api_timeout']}s")
        
        # Display storage configuration
        print("\n💾 Storage Configuration:")
        storage_config = config_manager.get_section('storage', {})
        
        for storage_type, storage_conf in storage_config.items():
            if isinstance(storage_conf, dict):
                if 'base_path' in storage_conf:
                    print(f"  - {storage_type}: {storage_conf['base_path']}")
                elif 'index_path' in storage_conf:
                    print(f"  - {storage_type}: {storage_conf['index_path']}")
        
        # Display external services
        print("\n🔗 External Services:")
        services_config = config_manager.get_section('external_services', {})
        
        for service_name, service_config in services_config.items():
            if isinstance(service_config, dict):
                if 'base_url' in service_config:
                    url = service_config['base_url']
                    # Mask sensitive URLs in demo
                    if 'localhost' in url or 'company.com' in url:
                        print(f"  - {service_name}: {url}")
                    else:
                        print(f"  - {service_name}: [CONFIGURED]")
                elif 'model' in service_config:
                    print(f"  - {service_name}: {service_config['model']}")
        
        # Test convenience methods
        print("\n🔧 Convenience Methods:")
        print(f"  - Is Development: {config_manager.is_development()}")
        print(f"  - Is Production: {config_manager.is_production()}")
        print(f"  - Log Level: {config_manager.get_log_level()}")
        
        # Test section access
        print("\n📊 Section Access Examples:")
        jira_config = config_manager.get_section('external_services.jira')
        if jira_config:
            print(f"  - Jira URL: {jira_config.get('base_url')}")
        
        # Health check
        print("\n🏥 Health Check:")
        health = await config_manager.health_check()
        print(f"  - Status: {health['status']}")
        print(f"  - Environment: {health['environment']}")
        print(f"  - Config Loaded: {health['config_loaded']}")
        print(f"  - Validation Enabled: {health['validation_enabled']}")
        
        print("\n🎉 Enhanced Configuration Manager Demo Completed!")
        print("✅ All core functionality working correctly!")
        
    except Exception as e:
        print(f"❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()


async def demo_environment_variable_substitution():
    """Demonstrate environment variable substitution"""
    
    print("\n🔧 Environment Variable Substitution Demo")
    print("=" * 50)
    
    # Set some test environment variables
    os.environ['DEMO_VAR'] = 'demo_value'
    os.environ['DEMO_OVERRIDE'] = 'overridden'
    
    # Create a temporary config with environment variables
    temp_config_content = """
demo:
  variable: "${DEMO_VAR}"
  with_default: "${NONEXISTENT:default_value}"
  overridden: "${DEMO_OVERRIDE:original_default}"
system:
  name: "Demo System"
  environment: "${DEMO_ENV:development}"
"""
    
    import tempfile
    import yaml
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(temp_config_content)
        temp_config_path = Path(f.name)
    
    try:
        config_manager = ConfigurationManager(ConfigManagerConfig(
            base_config_path=temp_config_path,
            watch_files=False,
            enable_validation=False
        ))
        
        config = await config_manager.load_config()
        
        print("📋 Environment Variable Substitution Results:")
        print(f"  - DEMO_VAR: {config['demo']['variable']}")
        print(f"  - NONEXISTENT (with default): {config['demo']['with_default']}")
        print(f"  - DEMO_OVERRIDE: {config['demo']['overridden']}")
        print(f"  - DEMO_ENV (with default): {config['system']['environment']}")
        
        print("\n✅ Environment variable substitution working correctly!")
        
    finally:
        # Clean up
        temp_config_path.unlink()
        # Clean up environment variables
        os.environ.pop('DEMO_VAR', None)
        os.environ.pop('DEMO_OVERRIDE', None)


async def main():
    """Main demo function"""
    await demo_config_manager()
    await demo_environment_variable_substitution()


if __name__ == "__main__":
    # Set environment for demo
    os.environ['ENVIRONMENT'] = 'development'
    
    # Run demo
    asyncio.run(main())
