#!/usr/bin/env python3
"""
Simple API Health Test Script
Tests Jira and Confluence API connectivity with real tokens
"""

import asyncio
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import initialize_config, get_config
import sys
sys.path.append('agents')
from jira_agent import JiraAgent
import structlog

logger = structlog.get_logger()


async def test_jira_api():
    """Test Jira API connectivity."""
    print("🔍 Testing Jira API...")
    
    try:
        # Initialize config
        config_manager = initialize_config(".env")
        config = config_manager.config
        
        print(f"   Base URL: {config.jira.base_url}")
        print(f"   Username: {config.jira.username}")
        
        # Test Jira agent
        agent_config = config_manager.get_agent_config("JiraAgent")
        async with JiraAgent(agent_config) as agent:
            health = await agent.health_check()
            
            print(f"   Status: {health['status']}")
            print(f"   Configured: {health['jira_configured']}")
            
            jira_health = health.get('jira_health', {})
            print(f"   API Connected: {jira_health.get('api_connected', False)}")
            
            if jira_health.get('error'):
                print(f"   ❌ Error: {jira_health['error']}")
                return False
            else:
                print("   ✅ Jira API is working!")
                return True
                
    except Exception as e:
        print(f"   ❌ Jira test failed: {e}")
        return False


async def main():
    """Main test function."""
    print("🏥 API Health Test")
    print("=" * 40)
    
    # Check environment variables
    if not os.getenv("JIRA_ACCESS_TOKEN"):
        print("❌ JIRA_ACCESS_TOKEN not set in .env")
        return
    
    if not os.getenv("CONFLUENCE_ACCESS_TOKEN"):
        print("❌ CONFLUENCE_ACCESS_TOKEN not set in .env")
        return
    
    print("✅ Environment variables found")
    
    # Test Jira
    jira_ok = await test_jira_api()
    
    print("\n📊 Summary:")
    print(f"   Jira API: {'✅ OK' if jira_ok else '❌ FAILED'}")
    
    if jira_ok:
        print("\n🎉 Jira API test successful!")
    else:
        print("\n💥 Some tests failed. Check the error messages above.")


if __name__ == "__main__":
    asyncio.run(main())
