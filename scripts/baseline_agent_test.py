#!/usr/bin/env python3
"""
Baseline testing script for all Employee Monitoring System agents
Runs each agent sequentially and records results, errors, and performance metrics
"""

import asyncio
import sys
import os
import time
import traceback
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass
import json

# Add project root to path and PYTHONPATH
project_root = Path(__file__).parents[1]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))  # Add src to path for core imports

# Change to project root directory for relative imports to work
os.chdir(project_root)

# Set PYTHONPATH environment variable
os.environ['PYTHONPATH'] = str(project_root) + ":" + str(project_root / "src")

from dotenv import load_dotenv
load_dotenv()

# Import agents with proper relative imports
try:
    from src.agents.task_analyzer_agent_improved import ImprovedTaskAnalyzerAgent
    from src.agents.meeting_analyzer_agent_improved import ImprovedMeetingAnalyzerAgent
    from src.agents.weekly_reports_agent_complete import WeeklyReportsAgentComplete
    from src.agents.quality_validator_agent import QualityValidatorAgent
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Project root: {project_root}")
    print(f"Python path: {sys.path[:5]}")  # First 5 entries
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    # Try direct import as fallback
    try:
        import sys
        sys.path.append(str(project_root / "src"))
        # Now test if core modules are importable
        import core.base_agent
        print("✅ core.base_agent imported successfully")
        
        # Try importing agents again
        from src.agents.task_analyzer_agent_improved import ImprovedTaskAnalyzerAgent
        print("✅ ImprovedTaskAnalyzerAgent imported successfully")
    except Exception as e2:
        print(f"❌ Fallback import also failed: {e2}")
        raise

@dataclass
class AgentTestResult:
    agent_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    success: bool
    message: str
    error: str = None
    traceback: str = None
    metadata: Dict[str, Any] = None

class BaselineAgentTester:
    def __init__(self):
        self.project_root = Path(__file__).parents[1]
        self.results: List[AgentTestResult] = []
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        # Create logs directory if it doesn't exist FIRST
        logs_dir = self.project_root / "tests" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(str(logs_dir / 'baseline_test.log')),
                logging.StreamHandler()
            ]
        )
        
        return logging.getLogger(__name__)
    
    async def test_task_analyzer(self) -> AgentTestResult:
        """Test Task Analyzer Agent"""
        self.logger.info("🚀 Testing Task Analyzer Agent...")
        start_time = datetime.now()
        
        try:
            agent = ImprovedTaskAnalyzerAgent()
            
            # Health check first
            health = await agent.get_health_status()
            self.logger.info(f"Task Analyzer Health: {health}")
            
            # Execute analysis
            result = await agent.execute({})
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result.success:
                self.logger.info(f"✅ Task Analyzer completed successfully in {duration:.2f}s")
                return AgentTestResult(
                    agent_name="Task Analyzer",
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=duration,
                    success=True,
                    message=result.message,
                    metadata={
                        'execution_time': result.metadata.get('execution_time'),
                        'employees_analyzed': result.metadata.get('employees_analyzed'),
                        'tasks_processed': result.metadata.get('tasks_processed'),
                        'quality_score': result.metadata.get('quality_score')
                    }
                )
            else:
                self.logger.error(f"❌ Task Analyzer failed: {result.message}")
                return AgentTestResult(
                    agent_name="Task Analyzer",
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=duration,
                    success=False,
                    message=result.message,
                    error=getattr(result, 'error', 'Unknown error')
                )
                
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            error_msg = str(e)
            traceback_str = traceback.format_exc()
            
            self.logger.error(f"💥 Task Analyzer crashed: {error_msg}")
            self.logger.error(f"Traceback: {traceback_str}")
            
            return AgentTestResult(
                agent_name="Task Analyzer",
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                success=False,
                message=f"Agent crashed: {error_msg}",
                error=error_msg,
                traceback=traceback_str
            )
    
    async def test_meeting_analyzer(self) -> AgentTestResult:
        """Test Meeting Analyzer Agent"""
        self.logger.info("🚀 Testing Meeting Analyzer Agent...")
        start_time = datetime.now()
        
        try:
            agent = ImprovedMeetingAnalyzerAgent()
            
            # Health check first
            health = await agent.get_health_status()
            self.logger.info(f"Meeting Analyzer Health: {health}")
            
            # Execute analysis
            result = await agent.execute({})
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result.success:
                self.logger.info(f"✅ Meeting Analyzer completed successfully in {duration:.2f}s")
                return AgentTestResult(
                    agent_name="Meeting Analyzer",
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=duration,
                    success=True,
                    message=result.message,
                    metadata={
                        'execution_time': result.metadata.get('execution_time'),
                        'protocols_analyzed': result.metadata.get('protocols_analyzed'),
                        'employees_analyzed': result.metadata.get('employees_analyzed'),
                        'quality_score': result.metadata.get('quality_score')
                    }
                )
            else:
                self.logger.error(f"❌ Meeting Analyzer failed: {result.message}")
                return AgentTestResult(
                    agent_name="Meeting Analyzer",
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=duration,
                    success=False,
                    message=result.message,
                    error=getattr(result, 'error', 'Unknown error')
                )
                
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            error_msg = str(e)
            traceback_str = traceback.format_exc()
            
            self.logger.error(f"💥 Meeting Analyzer crashed: {error_msg}")
            self.logger.error(f"Traceback: {traceback_str}")
            
            return AgentTestResult(
                agent_name="Meeting Analyzer",
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                success=False,
                message=f"Agent crashed: {error_msg}",
                error=error_msg,
                traceback=traceback_str
            )
    
    async def test_weekly_reports(self) -> AgentTestResult:
        """Test Weekly Reports Agent"""
        self.logger.info("🚀 Testing Weekly Reports Agent...")
        start_time = datetime.now()
        
        try:
            agent = WeeklyReportsAgentComplete()
            
            # Health check first
            health = await agent.get_health_status()
            self.logger.info(f"Weekly Reports Health: {health}")
            
            # Execute with minimal data for testing
            test_data = {
                'test_mode': True,
                'employees': ['Test Employee'],
                'date_range': '2026-04-01 to 2026-04-10'
            }
            
            result = await agent.execute(test_data)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result.success:
                self.logger.info(f"✅ Weekly Reports completed successfully in {duration:.2f}s")
                return AgentTestResult(
                    agent_name="Weekly Reports",
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=duration,
                    success=True,
                    message=result.message,
                    metadata={
                        'execution_time': result.metadata.get('execution_time'),
                        'report_generated': result.metadata.get('report_generated'),
                        'confluence_published': result.metadata.get('confluence_published')
                    }
                )
            else:
                self.logger.error(f"❌ Weekly Reports failed: {result.message}")
                return AgentTestResult(
                    agent_name="Weekly Reports",
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=duration,
                    success=False,
                    message=result.message,
                    error=getattr(result, 'error', 'Unknown error')
                )
                
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            error_msg = str(e)
            traceback_str = traceback.format_exc()
            
            self.logger.error(f"💥 Weekly Reports crashed: {error_msg}")
            self.logger.error(f"Traceback: {traceback_str}")
            
            return AgentTestResult(
                agent_name="Weekly Reports",
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                success=False,
                message=f"Agent crashed: {error_msg}",
                error=error_msg,
                traceback=traceback_str
            )
    
    async def test_quality_validator(self) -> AgentTestResult:
        """Test Quality Validator Agent"""
        self.logger.info("🚀 Testing Quality Validator Agent...")
        start_time = datetime.now()
        
        try:
            agent = QualityValidatorAgent()
            
            # Health check first
            health = await agent.get_health_status()
            self.logger.info(f"Quality Validator Health: {health}")
            
            # Execute with test data
            test_data = {
                'test_mode': True,
                'analysis_results': {
                    'task_analysis': 'Test task analysis content',
                    'meeting_analysis': 'Test meeting analysis content'
                }
            }
            
            result = await agent.execute(test_data)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result.success:
                self.logger.info(f"✅ Quality Validator completed successfully in {duration:.2f}s")
                return AgentTestResult(
                    agent_name="Quality Validator",
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=duration,
                    success=True,
                    message=result.message,
                    metadata={
                        'execution_time': result.metadata.get('execution_time'),
                        'quality_score': result.metadata.get('quality_score'),
                        'validation_passed': result.metadata.get('validation_passed')
                    }
                )
            else:
                self.logger.error(f"❌ Quality Validator failed: {result.message}")
                return AgentTestResult(
                    agent_name="Quality Validator",
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=duration,
                    success=False,
                    message=result.message,
                    error=getattr(result, 'error', 'Unknown error')
                )
                
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            error_msg = str(e)
            traceback_str = traceback.format_exc()
            
            self.logger.error(f"💥 Quality Validator crashed: {error_msg}")
            self.logger.error(f"Traceback: {traceback_str}")
            
            return AgentTestResult(
                agent_name="Quality Validator",
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                success=False,
                message=f"Agent crashed: {error_msg}",
                error=error_msg,
                traceback=traceback_str
            )
    
    async def run_all_tests(self) -> List[AgentTestResult]:
        """Run all agent tests sequentially"""
        self.logger.info("🎯 Starting baseline agent testing...")
        
        # Test agents in order
        agents_to_test = [
            self.test_task_analyzer,
            self.test_meeting_analyzer,
            self.test_weekly_reports,
            self.test_quality_validator
        ]
        
        for test_func in agents_to_test:
            try:
                result = await test_func()
                self.results.append(result)
                
                # Wait a bit between tests
                await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Failed to run {test_func.__name__}: {e}")
                continue
        
        return self.results
    
    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        successful_tests = sum(1 for r in self.results if r.success)
        failed_tests = len(self.results) - successful_tests
        total_duration = sum(r.duration_seconds for r in self.results)
        
        report = f"""
# Employee Monitoring System - Baseline Agent Test Report

**Generated:** {datetime.now().isoformat()}
**Total Tests:** {len(self.results)}
**Successful:** {successful_tests}
**Failed:** {failed_tests}
**Total Duration:** {total_duration:.2f} seconds

## Summary Status: {'✅ HEALTHY' if failed_tests == 0 else '❌ NEEDS ATTENTION'}

## Agent Test Results

"""
        
        for result in self.results:
            status_icon = "✅" if result.success else "❌"
            report += f"""
### {result.agent_name}

- **Status:** {status_icon} {result.message}
- **Duration:** {result.duration_seconds:.2f} seconds
- **Start:** {result.start_time.strftime('%H:%M:%S')}
- **End:** {result.end_time.strftime('%H:%M:%S')}

"""
            
            if result.success and result.metadata:
                report += "**Metadata:**\n"
                for key, value in result.metadata.items():
                    report += f"- {key}: {value}\n"
                report += "\n"
            
            if not result.success:
                if result.error:
                    report += f"**Error:** {result.error}\n\n"
                if result.traceback:
                    report += f"**Traceback:**\n```\n{result.traceback[:1000]}...\n```\n\n"
        
        # Performance summary
        report += "## Performance Summary\n\n"
        for result in self.results:
            report += f"- **{result.agent_name}:** {result.duration_seconds:.2f}s\n"
        
        # Recommendations
        if failed_tests > 0:
            report += "\n## Recommendations\n\n"
            report += "1. Fix all FAILED agents before proceeding with development\n"
            report += "2. Review error messages and tracebacks for root causes\n"
            report += "3. Check API connectivity and data availability\n"
            report += "4. Re-run tests after fixes\n"
        
        return report
    
    def save_results(self) -> str:
        """Save test results to files"""
        # Generate markdown report
        report = self.generate_report()
        
        # Create reports directory if it doesn't exist
        reports_dir = self.project_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        # Save markdown report
        report_file = reports_dir / f"baseline_agent_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Save JSON results
        json_results = []
        for result in self.results:
            json_results.append({
                'agent_name': result.agent_name,
                'start_time': result.start_time.isoformat(),
                'end_time': result.end_time.isoformat(),
                'duration_seconds': result.duration_seconds,
                'success': result.success,
                'message': result.message,
                'error': result.error,
                'metadata': result.metadata
            })
        
        json_file = reports_dir / f"baseline_agent_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"📄 Test report saved to: {report_file}")
        self.logger.info(f"📄 Test results saved to: {json_file}")
        
        return str(report_file)

async def main():
    """Main test execution"""
    print("🚀 STARTING BASELINE AGENT TESTING")
    print("=" * 60)
    
    tester = BaselineAgentTester()
    
    try:
        # Run all tests
        results = await tester.run_all_tests()
        
        # Save results
        report_file = tester.save_results()
        
        # Print summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        print(f"\n📊 TEST SUMMARY:")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"⏱️ Total Duration: {sum(r.duration_seconds for r in results):.2f}s")
        print(f"📄 Report: {report_file}")
        
        if failed == 0:
            print("\n🎉 ALL AGENTS PASSED BASELINE TESTING!")
            sys.exit(0)
        else:
            print(f"\n⚠️ {failed} AGENT(S) FAILED - CHECK REPORT FOR DETAILS")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR IN TESTING: {e}")
        traceback.print_exc()
        sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())
