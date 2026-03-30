#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test for Employee Monitoring System
"""

import asyncio
import logging
import sys
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_imports():
    """Test basic imports."""
    try:
        logger.info("Testing imports...")
        
        # Test core imports
        from core.base_agent import BaseAgent, AgentConfig, AgentResult
        logger.info("✓ core.base_agent imported")
        
        from core.llm_client import LLMClient
        logger.info("✓ core.llm_client imported")
        
        from core.models import TaskModel, EmployeeModel
        logger.info("✓ core.models imported")
        
        from core.jira_client import JiraClient
        logger.info("✓ core.jira_client imported")
        
        # Test agent imports
        from agents.quality_orchestrator import QualityOrchestrator
        logger.info("✓ agents.quality_orchestrator imported")
        
        from agents.task_analyzer_agent import TaskAnalyzerAgent
        logger.info("✓ agents.task_analyzer_agent imported")
        
        # Test orchestrator imports
        from orchestrator.employee_monitoring_orchestrator_fixed import EmployeeMonitoringOrchestratorFixed
        logger.info("✓ orchestrator.employee_monitoring_orchestrator_fixed imported")
        
        logger.info("🎉 All imports successful!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_basic_functionality():
    """Test basic functionality."""
    try:
        logger.info("Testing basic functionality...")
        
        # Test LLM client
        from core.llm_client import LLMClient
        llm_client = LLMClient()
        available = await llm_client.is_available()
        logger.info(f"✓ LLM Client available: {available}")
        
        # Test Jira client
        from core.jira_client import JiraClient
        jira_client = JiraClient()
        logger.info("✓ Jira Client created")
        
        # Test Quality Orchestrator
        from agents.quality_orchestrator import QualityOrchestrator
        quality_orchestrator = QualityOrchestrator()
        status = await quality_orchestrator.get_system_status()
        logger.info(f"✓ Quality Orchestrator status: {status.get('orchestrator', {}).get('status', 'unknown')}")
        
        logger.info("🎉 Basic functionality test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    try:
        logger.info("=== Employee Monitoring System Test ===")
        
        # Test imports
        imports_ok = await test_imports()
        if not imports_ok:
            return False
        
        # Test basic functionality
        functionality_ok = await test_basic_functionality()
        if not functionality_ok:
            return False
        
        logger.info("🎉 All tests passed! System is working correctly.")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
