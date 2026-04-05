#!/usr/bin/env python3
"""
Simple test script to check system imports and basic functionality
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test basic imports"""
    print("Python version:", sys.version)
    print("Testing basic imports...")
    
    success_count = 0
    total_tests = 0
    
    # Test agent imports
    agents_to_test = [
        ('TaskAnalyzerAgent', 'src.agents.task_analyzer_agent'),
        ('MeetingAnalyzerAgent', 'src.agents.meeting_analyzer_agent_auto'),
        ('WeeklyReportsAgentComplete', 'src.agents.weekly_reports_agent_complete'),
        ('QualityValidatorAgent', 'src.agents.quality_validator_agent'),
        ('QualityOrchestrator', 'src.agents.quality_orchestrator')
    ]
    
    for class_name, module_name in agents_to_test:
        total_tests += 1
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✓ {class_name} imported successfully")
            success_count += 1
        except Exception as e:
            print(f"✗ {class_name} import failed: {e}")
    
    # Test configuration
    total_tests += 1
    try:
        from core.config import get_employee_monitoring_config
        config = get_employee_monitoring_config()
        print("✓ Configuration loaded successfully")
        print(f"  Quality threshold: {config.get('quality', {}).get('threshold')}")
        print(f"  Scheduler enabled: {config.get('scheduler', {}).get('enabled')}")
        print(f"  Weekly report time: {config.get('scheduler', {}).get('weekly_report_time')}")
        print(f"  Weekly report day: {config.get('scheduler', {}).get('weekly_report_day')}")
        success_count += 1
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
    
    # Test LLM client
    total_tests += 1
    try:
        from core.llm_client import LLMClient
        llm_client = LLMClient()
        print("✓ LLM client initialized")
        print(f"  Model: {getattr(llm_client, 'default_model', 'Unknown')}")
        print(f"  Base URL: {getattr(llm_client, 'base_url', 'Unknown')}")
        success_count += 1
    except Exception as e:
        print(f"✗ LLM client initialization failed: {e}")
    
    print(f"\nSummary: {success_count}/{total_tests} tests passed")
    return success_count == total_tests

def test_basic_functionality():
    """Test basic functionality"""
    print("\nTesting basic functionality...")
    
    try:
        # Test task analyzer creation
        from src.agents.task_analyzer_agent import TaskAnalyzerAgent
        task_analyzer = TaskAnalyzerAgent()
        print("✓ TaskAnalyzerAgent created successfully")
        
        # Test quality validator creation
        from src.agents.quality_validator_agent import QualityValidatorAgent
        quality_validator = QualityValidatorAgent()
        print("✓ QualityValidatorAgent created successfully")
        
        # Test orchestrator creation
        from src.agents.quality_orchestrator import QualityOrchestrator
        orchestrator = QualityOrchestrator()
        print("✓ QualityOrchestrator created successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== MTS MultAgent System Test ===")
    
    imports_ok = test_imports()
    functionality_ok = test_basic_functionality()
    
    if imports_ok and functionality_ok:
        print("\n🎉 All tests passed! System is ready.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
