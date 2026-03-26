"""
Employee Monitoring Orchestrator

Coordinates the execution of all employee monitoring agents,
manages workflows, and handles scheduling and error recovery.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from ..agents.task_analyzer_agent import TaskAnalyzerAgent
from ..agents.meeting_analyzer_agent import MeetingAnalyzerAgent
from ..agents.weekly_reports_agent import WeeklyReportsAgent
from ..agents.quality_validator_agent import QualityValidatorAgent
from ..core.base_agent import AgentConfig, AgentResult
from ..core.llm_client import LLMClient
from ..core.json_memory_store import JSONMemoryStore
from ..core.config import get_employee_monitoring_config

logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """Types of workflows."""
    DAILY_TASK_ANALYSIS = "daily_task_analysis"
    DAILY_MEETING_ANALYSIS = "daily_meeting_analysis"
    WEEKLY_REPORT_GENERATION = "weekly_report_generation"
    QUALITY_VALIDATION = "quality_validation"
    COMPREHENSIVE_MONITORING = "comprehensive_monitoring"


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class AgentType(Enum):
    """Types of agents."""
    TASK_ANALYZER = "task_analyzer"
    MEETING_ANALYZER = "meeting_analyzer"
    WEEKLY_REPORTS = "weekly_reports"
    QUALITY_VALIDATOR = "quality_validator"


@dataclass
class WorkflowStep:
    """Individual step in a workflow."""
    name: str
    agent_type: AgentType
    input_data: Dict[str, Any]
    depends_on: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 300


@dataclass
class WorkflowExecution:
    """Workflow execution context."""
    workflow_id: str
    workflow_type: WorkflowType
    status: WorkflowStatus
    steps: List[WorkflowStep]
    results: Dict[str, AgentResult] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class EmployeeMonitoringOrchestrator:
    """
    Orchestrator for Employee Monitoring System.
    
    Coordinates agent execution by:
    - Managing workflows and scheduling
    - Handling dependencies between agents
    - Implementing error recovery and retries
    - Providing execution monitoring and logging
    - Optimizing resource utilization
    """
    
    def __init__(self):
        """Initialize the orchestrator."""
        # Load configuration
        self.emp_config = get_employee_monitoring_config()
        self.orchestrator_config = self.emp_config.get('orchestrator', {})
        
        # Initialize agents
        self.agents = {
            AgentType.TASK_ANALYZER: TaskAnalyzerAgent(),
            AgentType.MEETING_ANALYZER: MeetingAnalyzerAgent(),
            AgentType.WEEKLY_REPORTS: WeeklyReportsAgent(),
            AgentType.QUALITY_VALIDATOR: QualityValidatorAgent()
        }
        
        # Initialize components
        self.llm_client = LLMClient()
        self.memory_store = JSONMemoryStore()
        
        # Execution parameters
        self.max_concurrent_workflows = self.orchestrator_config.get('max_concurrent_workflows', 3)
        self.default_timeout = self.orchestrator_config.get('default_timeout', 600)
        self.retry_delay = self.orchestrator_config.get('retry_delay', 60)
        
        # Workflow tracking
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.workflow_history: List[WorkflowExecution] = []
        
        # Results storage
        self.results_dir = Path(self.emp_config.get('reports', {}).get('results_dir', './reports/orchestrator'))
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("EmployeeMonitoringOrchestrator initialized")
    
    async def execute_workflow(self, workflow_type: WorkflowType, input_data: Dict[str, Any], workflow_id: Optional[str] = None) -> WorkflowExecution:
        """
        Execute a workflow with the specified type and input data.
        
        Args:
            workflow_type: Type of workflow to execute
            input_data: Input data for the workflow
            workflow_id: Optional custom workflow ID
            
        Returns:
            WorkflowExecution with results
        """
        if workflow_id is None:
            workflow_id = f"{workflow_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create workflow steps based on type
        steps = self._create_workflow_steps(workflow_type, input_data)
        
        # Initialize workflow execution
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            status=WorkflowStatus.PENDING,
            steps=steps,
            metadata=input_data
        )
        
        # Check concurrent workflow limit
        if len(self.active_workflows) >= self.max_concurrent_workflows:
            await self._wait_for_available_slot()
        
        # Add to active workflows
        self.active_workflows[workflow_id] = execution
        
        try:
            logger.info(f"Starting workflow execution: {workflow_id} ({workflow_type.value})")
            execution.status = WorkflowStatus.RUNNING
            
            # Execute workflow steps
            await self._execute_workflow_steps(execution)
            
            # Mark as completed
            execution.status = WorkflowStatus.COMPLETED
            execution.end_time = datetime.now()
            
            logger.info(f"Workflow completed successfully: {workflow_id}")
            
        except Exception as e:
            logger.error(f"Workflow failed: {workflow_id} - {str(e)}")
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.end_time = datetime.now()
        
        finally:
            # Move from active to history
            if workflow_id in self.active_workflows:
                self.active_workflows.pop(workflow_id)
            self.workflow_history.append(execution)
            
            # Save results
            await self._save_workflow_results(execution)
        
        return execution
    
    def _create_workflow_steps(self, workflow_type: WorkflowType, input_data: Dict[str, Any]) -> List[WorkflowStep]:
        """Create workflow steps based on workflow type."""
        steps = []
        
        if workflow_type == WorkflowType.DAILY_TASK_ANALYSIS:
            steps = [
                WorkflowStep(
                    name="task_analysis",
                    agent_type=AgentType.TASK_ANALYZER,
                    input_data=input_data,
                    timeout_seconds=300
                ),
                WorkflowStep(
                    name="quality_validation",
                    agent_type=AgentType.QUALITY_VALIDATOR,
                    input_data={"analysis_data": None},  # Will be populated from task_analysis
                    depends_on=["task_analysis"],
                    timeout_seconds=180
                )
            ]
        
        elif workflow_type == WorkflowType.DAILY_MEETING_ANALYSIS:
            steps = [
                WorkflowStep(
                    name="meeting_analysis",
                    agent_type=AgentType.MEETING_ANALYZER,
                    input_data=input_data,
                    timeout_seconds=300
                ),
                WorkflowStep(
                    name="quality_validation",
                    agent_type=AgentType.QUALITY_VALIDATOR,
                    input_data={"analysis_data": None},  # Will be populated from meeting_analysis
                    depends_on=["meeting_analysis"],
                    timeout_seconds=180
                )
            ]
        
        elif workflow_type == WorkflowType.WEEKLY_REPORT_GENERATION:
            steps = [
                WorkflowStep(
                    name="weekly_report",
                    agent_type=AgentType.WEEKLY_REPORTS,
                    input_data=input_data,
                    timeout_seconds=600
                ),
                WorkflowStep(
                    name="quality_validation",
                    agent_type=AgentType.QUALITY_VALIDATOR,
                    input_data={"analysis_data": None},  # Will be populated from weekly_report
                    depends_on=["weekly_report"],
                    timeout_seconds=300
                )
            ]
        
        elif workflow_type == WorkflowType.COMPREHENSIVE_MONITORING:
            # Comprehensive workflow with all agents
            steps = [
                # Parallel task and meeting analysis
                WorkflowStep(
                    name="task_analysis",
                    agent_type=AgentType.TASK_ANALYZER,
                    input_data=input_data.get("tasks", {}),
                    timeout_seconds=300
                ),
                WorkflowStep(
                    name="meeting_analysis",
                    agent_type=AgentType.MEETING_ANALYZER,
                    input_data=input_data.get("meetings", {}),
                    timeout_seconds=300
                ),
                # Weekly report (depends on both analyses)
                WorkflowStep(
                    name="weekly_report",
                    agent_type=AgentType.WEEKLY_REPORTS,
                    input_data=input_data.get("weekly_data", {}),
                    depends_on=["task_analysis", "meeting_analysis"],
                    timeout_seconds=600
                ),
                # Quality validation for each component
                WorkflowStep(
                    name="task_quality_validation",
                    agent_type=AgentType.QUALITY_VALIDATOR,
                    input_data={"analysis_data": None, "analysis_type": "task_analysis"},
                    depends_on=["task_analysis"],
                    timeout_seconds=180
                ),
                WorkflowStep(
                    name="meeting_quality_validation",
                    agent_type=AgentType.QUALITY_VALIDATOR,
                    input_data={"analysis_data": None, "analysis_type": "meeting_analysis"},
                    depends_on=["meeting_analysis"],
                    timeout_seconds=180
                ),
                WorkflowStep(
                    name="report_quality_validation",
                    agent_type=AgentType.QUALITY_VALIDATOR,
                    input_data={"analysis_data": None, "analysis_type": "weekly_report"},
                    depends_on=["weekly_report"],
                    timeout_seconds=300
                )
            ]
        
        return steps
    
    async def _execute_workflow_steps(self, execution: WorkflowExecution) -> None:
        """Execute all steps in a workflow with dependency management."""
        
        # Create a mapping of step name to step object
        step_map = {step.name: step for step in execution.steps}
        
        # Track completed steps
        completed_steps = set()
        
        # Execute steps in dependency order
        while len(completed_steps) < len(execution.steps):
            # Find steps that can be executed (all dependencies completed)
            ready_steps = []
            for step in execution.steps:
                if step.name not in completed_steps:
                    dependencies_met = all(dep in completed_steps for dep in step.depends_on)
                    if dependencies_met:
                        ready_steps.append(step)
            
            if not ready_steps:
                # No steps ready to execute - check for circular dependencies
                raise RuntimeError("No steps ready for execution - possible circular dependency")
            
            # Execute ready steps in parallel
            await self._execute_steps_parallel(execution, ready_steps, completed_steps, step_map)
    
    async def _execute_steps_parallel(self, execution: WorkflowExecution, ready_steps: List[WorkflowStep], completed_steps: set, step_map: Dict[str, WorkflowStep]) -> None:
        """Execute multiple steps in parallel."""
        
        async def execute_step_with_timeout(step: WorkflowStep) -> None:
            """Execute a single step with timeout and retry logic."""
            
            # Prepare input data with dependencies
            input_data = step.input_data.copy()
            
            # Inject results from dependencies
            for dep_name in step.depends_on:
                if dep_name in execution.results:
                    dep_result = execution.results[dep_name]
                    if "analysis_data" in input_data:
                        input_data["analysis_data"] = dep_result.data
                    else:
                        input_data[dep_name] = dep_result.data
            
            # Execute the step with retries
            for attempt in range(step.max_retries + 1):
                try:
                    # Execute with timeout
                    result = await asyncio.wait_for(
                        self.agents[step.agent_type].execute(input_data),
                        timeout=step.timeout_seconds
                    )
                    
                    # Store result
                    execution.results[step.name] = result
                    
                    # Add to completed steps
                    completed_steps.add(step.name)
                    
                    logger.info(f"Step completed: {execution.workflow_id}.{step.name} (attempt {attempt + 1})")
                    return
                    
                except asyncio.TimeoutError:
                    logger.warning(f"Step timeout: {execution.workflow_id}.{step.name} (attempt {attempt + 1})")
                except Exception as e:
                    logger.warning(f"Step failed: {execution.workflow_id}.{step.name} - {str(e)} (attempt {attempt + 1})")
                
                # Retry logic
                if attempt < step.max_retries:
                    step.retry_count = attempt + 1
                    await asyncio.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                else:
                    # All retries failed
                    raise RuntimeError(f"Step {step.name} failed after {step.max_retries + 1} attempts")
        
        # Execute ready steps in parallel
        tasks = [execute_step_with_timeout(step) for step in ready_steps]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _wait_for_available_slot(self) -> None:
        """Wait for an available workflow execution slot."""
        while len(self.active_workflows) >= self.max_concurrent_workflows:
            await asyncio.sleep(1)
    
    async def _save_workflow_results(self, execution: WorkflowExecution) -> None:
        """Save workflow execution results to file system."""
        try:
            # Create results file
            results_file = self.results_dir / f"workflow_{execution.workflow_id}.json"
            
            # Prepare execution data for serialization
            execution_data = {
                'workflow_id': execution.workflow_id,
                'workflow_type': execution.workflow_type.value,
                'status': execution.status.value,
                'start_time': execution.start_time.isoformat(),
                'end_time': execution.end_time.isoformat() if execution.end_time else None,
                'error_message': execution.error_message,
                'metadata': execution.metadata,
                'steps': [
                    {
                        'name': step.name,
                        'agent_type': step.agent_type.value,
                        'depends_on': step.depends_on,
                        'retry_count': step.retry_count,
                        'max_retries': step.max_retries,
                        'timeout_seconds': step.timeout_seconds
                    }
                    for step in execution.steps
                ],
                'results': {
                    step_name: {
                        'success': result.success,
                        'message': result.message,
                        'metadata': result.metadata,
                        'error': result.error if hasattr(result, 'error') else None
                    }
                    for step_name, result in execution.results.items()
                }
            }
            
            # Save to JSON file
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(execution_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Workflow results saved to {results_file}")
            
        except Exception as e:
            logger.error(f"Failed to save workflow results: {e}")
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowExecution]:
        """Get the status of a specific workflow."""
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]
        
        for execution in self.workflow_history:
            if execution.workflow_id == workflow_id:
                return execution
        
        return None
    
    async def get_active_workflows(self) -> List[WorkflowExecution]:
        """Get all currently active workflows."""
        return list(self.active_workflows.values())
    
    async def get_workflow_history(self, limit: int = 50) -> List[WorkflowExecution]:
        """Get workflow execution history."""
        return self.workflow_history[-limit:]
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow."""
        if workflow_id in self.active_workflows:
            execution = self.active_workflows[workflow_id]
            execution.status = WorkflowStatus.CANCELLED
            execution.end_time = datetime.now()
            
            # Move from active to history
            self.active_workflows.pop(workflow_id)
            self.workflow_history.append(execution)
            
            logger.info(f"Workflow cancelled: {workflow_id}")
            return True
        
        return False
    
    async def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get overall orchestrator status and statistics."""
        
        # Calculate statistics
        total_workflows = len(self.workflow_history) + len(self.active_workflows)
        successful_workflows = sum(1 for w in self.workflow_history if w.status == WorkflowStatus.COMPLETED)
        failed_workflows = sum(1 for w in self.workflow_history if w.status == WorkflowStatus.FAILED)
        
        # Agent health check
        agent_health = {}
        for agent_type, agent in self.agents.items():
            try:
                health = await agent.get_health_status()
                agent_health[agent_type.value] = health
            except Exception as e:
                agent_health[agent_type.value] = {'status': 'error', 'error': str(e)}
        
        return {
            'orchestrator_status': 'healthy',
            'active_workflows': len(self.active_workflows),
            'total_workflows': total_workflows,
            'successful_workflows': successful_workflows,
            'failed_workflows': failed_workflows,
            'success_rate': successful_workflows / max(total_workflows, 1),
            'agent_health': agent_health,
            'max_concurrent_workflows': self.max_concurrent_workflows,
            'default_timeout': self.default_timeout,
            'last_check': datetime.now().isoformat()
        }
    
    async def schedule_daily_workflows(self) -> None:
        """Schedule and execute daily monitoring workflows."""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Prepare input data for daily workflows
        task_input = {
            'jira_tasks': [],  # Would be populated from Jira API
            'analysis_date': today
        }
        
        meeting_input = {
            'meeting_protocols': [],  # Would be populated from protocol directory
            'analysis_date': today
        }
        
        # Execute daily workflows
        task_workflow = await self.execute_workflow(
            WorkflowType.DAILY_TASK_ANALYSIS,
            task_input,
            f"daily_tasks_{today}"
        )
        
        meeting_workflow = await self.execute_workflow(
            WorkflowType.DAILY_MEETING_ANALYSIS,
            meeting_input,
            f"daily_meetings_{today}"
        )
        
        logger.info(f"Daily workflows scheduled: {task_workflow.workflow_id}, {meeting_workflow.workflow_id}")
    
    async def schedule_weekly_workflow(self) -> None:
        """Schedule and execute weekly report workflow."""
        today = datetime.now()
        week_end = today.strftime('%Y-%m-%d')
        
        # Prepare input data for weekly workflow
        weekly_input = {
            'report_period_end': today,
            'report_type': 'comprehensive'
        }
        
        # Execute weekly workflow
        weekly_workflow = await self.execute_workflow(
            WorkflowType.WEEKLY_REPORT_GENERATION,
            weekly_input,
            f"weekly_report_{week_end}"
        )
        
        logger.info(f"Weekly workflow scheduled: {weekly_workflow.workflow_id}")
    
    async def start_comprehensive_monitoring(self, input_data: Dict[str, Any]) -> WorkflowExecution:
        """Start comprehensive monitoring with all agents."""
        return await self.execute_workflow(
            WorkflowType.COMPREHENSIVE_MONITORING,
            input_data,
            f"comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
