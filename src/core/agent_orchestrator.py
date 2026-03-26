"""
Agent Orchestrator

Coordinates multiple analysis agents and manages workflow execution.
Provides unified interface for running DailyJiraAnalyzer and DailyMeetingAnalyzer
with proper data flow and result aggregation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .base_agent import AgentResult
from .config import get_config
from .llm_client import LLMClient
from .json_memory_store import JSONMemoryStore
from .quality_metrics import QualityMetrics

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class AgentExecutionResult:
    """Result of agent execution."""
    agent_name: str
    execution_time: float
    success: bool
    result: AgentResult
    quality_score: float
    error_message: Optional[str] = None


@dataclass
class WorkflowResult:
    """Complete workflow execution result."""
    workflow_id: str
    status: WorkflowStatus
    start_time: datetime
    end_time: datetime
    total_execution_time: float
    agent_results: List[AgentExecutionResult]
    aggregated_data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentOrchestrator:
    """
    Orchestrates multiple analysis agents for unified workflow execution.
    
    Features:
    - Agent coordination and execution order management
    - Data flow between agents
    - Result aggregation and correlation
    - Error handling and recovery
    - Performance monitoring
    - Quality assurance
    """
    
    def __init__(self):
        """Initialize agent orchestrator."""
        self.config = get_config()
        self.llm_client = LLMClient()
        self.memory_store = JSONMemoryStore()
        self.quality_metrics = QualityMetrics()
        
        # Agent registry
        self.agents = {}
        
        # Workflow configuration
        self.workflow_config = self.config.get('orchestrator', {}).get('workflow', {})
        
        # Execution parameters
        self.max_parallel_agents = self.workflow_config.get('max_parallel_agents', 4)
        self.agent_timeout = self.workflow_config.get('agent_timeout', 300)  # 5 minutes
        self.enable_data_sharing = self.workflow_config.get('enable_data_sharing', True)
        
        logger.info("AgentOrchestrator initialized")
    
    def register_agent(self, name: str, agent: Any, priority: int = 0) -> None:
        """
        Register an agent with the orchestrator.
        
        Args:
            name: Agent name
            agent: Agent instance
            priority: Execution priority (higher = earlier)
        """
        self.agents[name] = {
            'agent': agent,
            'priority': priority,
            'last_execution': None,
            'success_count': 0,
            'failure_count': 0
        }
        logger.info(f"Registered agent: {name} (priority: {priority})")
    
    async def execute_workflow(
        self, 
        workflow_config: Dict[str, Any],
        data_sources: Dict[str, Any]
    ) -> WorkflowResult:
        """
        Execute complete workflow with multiple agents.
        
        Args:
            workflow_config: Workflow configuration
            data_sources: Data sources for agents
            
        Returns:
            WorkflowResult with execution details
        """
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        logger.info(f"Starting workflow: {workflow_id}")
        
        try:
            # Determine execution order
            execution_order = self._determine_execution_order(workflow_config)
            
            # Execute agents in order
            agent_results = []
            shared_data = {}
            
            for agent_name in execution_order:
                if agent_name not in self.agents:
                    logger.warning(f"Agent {agent_name} not registered, skipping")
                    continue
                
                agent_result = await self._execute_agent(
                    agent_name, 
                    data_sources.get(agent_name, {}),
                    shared_data
                )
                
                agent_results.append(agent_result)
                
                # Update shared data if agent succeeded
                if agent_result.success and self.enable_data_sharing:
                    shared_data.update(self._extract_shared_data(agent_result))
                
                # Check if workflow should continue
                if not agent_result.success and workflow_config.get('fail_fast', False):
                    logger.error(f"Agent {agent_name} failed, stopping workflow")
                    break
            
            # Aggregate results
            aggregated_data = await self._aggregate_results(agent_results, shared_data)
            
            # Determine workflow status
            status = self._determine_workflow_status(agent_results)
            
            end_time = datetime.now()
            total_execution_time = (end_time - start_time).total_seconds()
            
            workflow_result = WorkflowResult(
                workflow_id=workflow_id,
                status=status,
                start_time=start_time,
                end_time=end_time,
                total_execution_time=total_execution_time,
                agent_results=agent_results,
                aggregated_data=aggregated_data,
                metadata={
                    'execution_order': execution_order,
                    'shared_data_keys': list(shared_data.keys()),
                    'workflow_config': workflow_config
                }
            )
            
            # Save workflow result
            await self._save_workflow_result(workflow_result)
            
            logger.info(f"Workflow {workflow_id} completed in {total_execution_time:.2f}s "
                       f"with status: {status.value}")
            
            return workflow_result
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {e}")
            
            end_time = datetime.now()
            total_execution_time = (end_time - start_time).total_seconds()
            
            return WorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                total_execution_time=total_execution_time,
                agent_results=agent_results,
                aggregated_data={},
                metadata={'error': str(e)}
            )
    
    async def execute_parallel_workflow(
        self,
        workflow_config: Dict[str, Any],
        data_sources: Dict[str, Any]
    ) -> WorkflowResult:
        """
        Execute workflow with parallel agent execution.
        
        Args:
            workflow_config: Workflow configuration
            data_sources: Data sources for agents
            
        Returns:
            WorkflowResult with execution details
        """
        workflow_id = f"parallel_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        logger.info(f"Starting parallel workflow: {workflow_id}")
        
        try:
            # Determine which agents can run in parallel
            parallel_groups = self._determine_parallel_groups(workflow_config)
            
            agent_results = []
            shared_data = {}
            
            # Execute agents in parallel groups
            for group in parallel_groups:
                group_tasks = []
                
                for agent_name in group:
                    if agent_name not in self.agents:
                        continue
                    
                    task = self._execute_agent(
                        agent_name,
                        data_sources.get(agent_name, {}),
                        shared_data
                    )
                    group_tasks.append(task)
                
                # Wait for group completion
                if group_tasks:
                    group_results = await asyncio.gather(*group_tasks, return_exceptions=True)
                    
                    for result in group_results:
                        if isinstance(result, Exception):
                            logger.error(f"Agent execution failed: {result}")
                            continue
                        
                        agent_results.append(result)
                        
                        # Update shared data
                        if result.success and self.enable_data_sharing:
                            shared_data.update(self._extract_shared_data(result))
            
            # Aggregate results
            aggregated_data = await self._aggregate_results(agent_results, shared_data)
            
            end_time = datetime.now()
            total_execution_time = (end_time - start_time).total_seconds()
            
            workflow_result = WorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                total_execution_time=total_execution_time,
                agent_results=agent_results,
                aggregated_data=aggregated_data,
                metadata={
                    'parallel_groups': len(parallel_groups),
                    'shared_data_keys': list(shared_data.keys())
                }
            )
            
            await self._save_workflow_result(workflow_result)
            
            logger.info(f"Parallel workflow {workflow_id} completed in {total_execution_time:.2f}s")
            
            return workflow_result
            
        except Exception as e:
            logger.error(f"Parallel workflow {workflow_id} failed: {e}")
            
            end_time = datetime.now()
            total_execution_time = (end_time - start_time).total_seconds()
            
            return WorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                total_execution_time=total_execution_time,
                agent_results=agent_results,
                aggregated_data={},
                metadata={'error': str(e)}
            )
    
    async def _execute_agent(
        self,
        agent_name: str,
        input_data: Dict[str, Any],
        shared_data: Dict[str, Any]
    ) -> AgentExecutionResult:
        """Execute a single agent with timeout and error handling."""
        agent_info = self.agents[agent_name]
        agent = agent_info['agent']
        
        start_time = datetime.now()
        
        try:
            logger.info(f"Executing agent: {agent_name}")
            
            # Prepare input data with shared context
            enhanced_input = {
                **input_data,
                'shared_context': shared_data,
                'workflow_metadata': {
                    'agent_name': agent_name,
                    'execution_time': start_time.isoformat()
                }
            }
            
            # Execute agent with timeout
            result = await asyncio.wait_for(
                agent.execute(enhanced_input),
                timeout=self.agent_timeout
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Calculate quality score
            quality_score = await self._calculate_agent_quality(agent_name, result)
            
            # Update agent statistics
            if result.success:
                agent_info['success_count'] += 1
                logger.info(f"Agent {agent_name} completed successfully in {execution_time:.2f}s")
            else:
                agent_info['failure_count'] += 1
                logger.warning(f"Agent {agent_name} failed: {result.message}")
            
            agent_info['last_execution'] = datetime.now()
            
            return AgentExecutionResult(
                agent_name=agent_name,
                execution_time=execution_time,
                success=result.success,
                result=result,
                quality_score=quality_score,
                error_message=None if result.success else result.message
            )
            
        except asyncio.TimeoutError:
            execution_time = (datetime.now() - start_time).total_seconds()
            agent_info['failure_count'] += 1
            
            logger.error(f"Agent {agent_name} timed out after {self.agent_timeout}s")
            
            return AgentExecutionResult(
                agent_name=agent_name,
                execution_time=execution_time,
                success=False,
                result=AgentResult(success=False, message="Agent execution timeout"),
                quality_score=0.0,
                error_message=f"Agent execution timed out after {self.agent_timeout}s"
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            agent_info['failure_count'] += 1
            
            logger.error(f"Agent {agent_name} failed with exception: {e}")
            
            return AgentExecutionResult(
                agent_name=agent_name,
                execution_time=execution_time,
                success=False,
                result=AgentResult(success=False, message=f"Agent execution failed: {str(e)}"),
                quality_score=0.0,
                error_message=str(e)
            )
    
    def _determine_execution_order(self, workflow_config: Dict[str, Any]) -> List[str]:
        """Determine agent execution order based on priority and dependencies."""
        # Get agents from workflow config or use all registered agents
        configured_agents = workflow_config.get('agents', list(self.agents.keys()))
        
        # Sort by priority (descending)
        sorted_agents = sorted(
            configured_agents,
            key=lambda x: self.agents.get(x, {}).get('priority', 0),
            reverse=True
        )
        
        # Apply execution constraints from config
        execution_constraints = workflow_config.get('execution_constraints', {})
        
        if execution_constraints.get('sequenced', False):
            return sorted_agents
        else:
            # For parallel execution, we'll group in execute_parallel_workflow
            return sorted_agents
    
    def _determine_parallel_groups(self, workflow_config: Dict[str, Any]) -> List[List[str]]:
        """Determine which agents can run in parallel."""
        configured_agents = workflow_config.get('agents', list(self.agents.keys()))
        
        # Simple grouping: all agents can run in parallel up to max_parallel_agents
        groups = []
        for i in range(0, len(configured_agents), self.max_parallel_agents):
            groups.append(configured_agents[i:i + self.max_parallel_agents])
        
        return groups
    
    def _extract_shared_data(self, agent_result: AgentExecutionResult) -> Dict[str, Any]:
        """Extract data to be shared between agents."""
        shared_data = {}
        
        if agent_result.success and agent_result.result.data:
            # Extract key data types that might be useful for other agents
            data = agent_result.result.data
            
            # Common sharing patterns
            if 'projects' in data:
                shared_data['projects'] = data['projects']
            
            if 'employees' in data:
                shared_data['employees'] = data['employees']
            
            if 'action_items' in data:
                shared_data['action_items'] = data['action_items']
            
            if 'participants' in data:
                shared_data['participants'] = data['participants']
            
            # Add agent-specific data
            shared_data[f"{agent_result.agent_name}_data"] = data
            shared_data[f"{agent_result.agent_name}_timestamp"] = datetime.now().isoformat()
        
        return shared_data
    
    async def _aggregate_results(
        self,
        agent_results: List[AgentExecutionResult],
        shared_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Aggregate results from multiple agents."""
        aggregated = {
            'summary': {
                'total_agents': len(agent_results),
                'successful_agents': sum(1 for r in agent_results if r.success),
                'failed_agents': sum(1 for r in agent_results if not r.success),
                'average_quality': sum(r.quality_score for r in agent_results) / len(agent_results) if agent_results else 0,
                'total_execution_time': sum(r.execution_time for r in agent_results)
            },
            'agent_results': {},
            'shared_data': shared_data,
            'correlations': {}
        }
        
        # Collect individual agent results
        for result in agent_results:
            if result.success and result.result.data:
                aggregated['agent_results'][result.agent_name] = {
                    'data': result.result.data,
                    'quality_score': result.quality_score,
                    'execution_time': result.execution_time,
                    'metadata': result.result.metadata
                }
        
        # Perform cross-agent correlations
        if len([r for r in agent_results if r.success]) >= 2:
            aggregated['correlations'] = await self._perform_cross_agent_analysis(agent_results)
        
        return aggregated
    
    async def _perform_cross_agent_analysis(
        self,
        agent_results: List[AgentExecutionResult]
    ) -> Dict[str, Any]:
        """Perform analysis across agent results."""
        correlations = {}
        
        # Find common themes across agents
        successful_results = [r for r in agent_results if r.success]
        
        if len(successful_results) >= 2:
            # Extract common entities
            common_projects = set()
            common_employees = set()
            
            for result in successful_results:
                if result.result.data:
                    data = result.result.data
                    
                    if 'projects' in data:
                        if isinstance(data['projects'], list):
                            common_projects.update(p.get('key', str(p)) for p in data['projects'])
                    
                    if 'employees' in data:
                        if isinstance(data['employees'], list):
                            common_employees.update(e.get('name', str(e)) for e in data['employees'])
            
            correlations['common_entities'] = {
                'projects': list(common_projects),
                'employees': list(common_employees)
            }
            
            # Quality correlation analysis
            quality_scores = [r.quality_score for r in successful_results]
            correlations['quality_analysis'] = {
                'average_quality': sum(quality_scores) / len(quality_scores),
                'quality_variance': sum((q - sum(quality_scores)/len(quality_scores))**2 for q in quality_scores) / len(quality_scores),
                'highest_quality_agent': max(successful_results, key=lambda r: r.quality_score).agent_name,
                'lowest_quality_agent': min(successful_results, key=lambda r: r.quality_score).agent_name
            }
        
        return correlations
    
    async def _calculate_agent_quality(self, agent_name: str, result: AgentResult) -> float:
        """Calculate quality score for agent execution."""
        base_quality = 0.0
        
        if not result.success:
            return base_quality
        
        # Base success score
        base_quality += 0.5
        
        # Execution time factor (faster is better up to a point)
        execution_time = result.metadata.get('execution_time', 0)
        if execution_time < 10:  # Very fast
            base_quality += 0.2
        elif execution_time < 30:  # Fast
            base_quality += 0.1
        elif execution_time < 60:  # Normal
            base_quality += 0.05
        
        # Data quality factor
        if result.data:
            data_score = 0.3
            
            # Check for key fields
            if isinstance(result.data, dict):
                field_count = len(result.data)
                if field_count > 5:
                    data_score += 0.1
                elif field_count > 2:
                    data_score += 0.05
            
            base_quality += data_score
        
        # Historical performance factor
        agent_info = self.agents.get(agent_name, {})
        success_count = agent_info.get('success_count', 0)
        failure_count = agent_info.get('failure_count', 0)
        total_executions = success_count + failure_count
        
        if total_executions > 0:
            success_rate = success_count / total_executions
            base_quality += success_rate * 0.2
        
        return min(1.0, max(0.0, base_quality))
    
    def _determine_workflow_status(self, agent_results: List[AgentExecutionResult]) -> WorkflowStatus:
        """Determine overall workflow status based on agent results."""
        if not agent_results:
            return WorkflowStatus.FAILED
        
        successful_count = sum(1 for r in agent_results if r.success)
        total_count = len(agent_results)
        
        if successful_count == total_count:
            return WorkflowStatus.COMPLETED
        elif successful_count == 0:
            return WorkflowStatus.FAILED
        else:
            return WorkflowStatus.PARTIAL
    
    async def _save_workflow_result(self, workflow_result: WorkflowResult) -> None:
        """Save workflow result to memory store."""
        try:
            # Convert to dictionary for storage
            result_dict = {
                'workflow_id': workflow_result.workflow_id,
                'status': workflow_result.status.value,
                'start_time': workflow_result.start_time.isoformat(),
                'end_time': workflow_result.end_time.isoformat(),
                'total_execution_time': workflow_result.total_execution_time,
                'aggregated_data': workflow_result.aggregated_data,
                'metadata': workflow_result.metadata
            }
            
            # Save agent results separately to avoid deep nesting
            for agent_result in workflow_result.agent_results:
                agent_dict = {
                    'workflow_id': workflow_result.workflow_id,
                    'agent_name': agent_result.agent_name,
                    'execution_time': agent_result.execution_time,
                    'success': agent_result.success,
                    'quality_score': agent_result.quality_score,
                    'error_message': agent_result.error_message,
                    'result_data': agent_result.result.data if agent_result.success else None,
                    'result_metadata': agent_result.result.metadata
                }
                
                await self.memory_store.save_record(
                    data=agent_dict,
                    record_type='agent_execution',
                    source='agent_orchestrator'
                )
            
            # Save workflow summary
            await self.memory_store.save_record(
                data=result_dict,
                record_type='workflow_execution',
                source='agent_orchestrator'
            )
            
            logger.info(f"Workflow result {workflow_result.workflow_id} saved to memory store")
            
        except Exception as e:
            logger.error(f"Failed to save workflow result: {e}")
    
    async def get_workflow_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get workflow execution history."""
        try:
            records = await self.memory_store.get_records(
                record_type='workflow_execution',
                limit=limit,
                order_by='start_time',
                order_direction='desc'
            )
            
            return [record.data for record in records]
            
        except Exception as e:
            logger.error(f"Failed to get workflow history: {e}")
            return []
    
    async def get_agent_statistics(self) -> Dict[str, Any]:
        """Get agent execution statistics."""
        try:
            stats = {}
            
            for agent_name, agent_info in self.agents.items():
                success_count = agent_info.get('success_count', 0)
                failure_count = agent_info.get('failure_count', 0)
                total_executions = success_count + failure_count
                
                stats[agent_name] = {
                    'success_count': success_count,
                    'failure_count': failure_count,
                    'total_executions': total_executions,
                    'success_rate': success_count / total_executions if total_executions > 0 else 0,
                    'last_execution': agent_info.get('last_execution'),
                    'priority': agent_info.get('priority', 0)
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get agent statistics: {e}")
            return {}
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get orchestrator health status."""
        try:
            # Check components
            llm_available = await self.llm_client.is_available()
            memory_healthy = self.memory_store.is_healthy()
            
            # Agent health
            healthy_agents = 0
            total_agents = len(self.agents)
            
            for agent_name, agent_info in self.agents.items():
                try:
                    # Add health check method to agents
                    agent = agent_info['agent']
                    if hasattr(agent, 'get_health_status'):
                        health = await agent.get_health_status()
                        if health.get('status') == 'healthy':
                            healthy_agents += 1
                    else:
                        # Basic health check - if agent exists, consider it healthy
                        healthy_agents += 1
                except Exception:
                    # Agent health check failed
                    continue
            
            overall_status = 'healthy' if (
                llm_available and memory_healthy and healthy_agents == total_agents
            ) else 'degraded' if healthy_agents > 0 else 'unhealthy'
            
            return {
                'orchestrator_status': overall_status,
                'llm_client': 'available' if llm_available else 'unavailable',
                'memory_store': 'healthy' if memory_healthy else 'unhealthy',
                'agent_health': f'{healthy_agents}/{total_agents}',
                'total_agents': total_agents,
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'orchestrator_status': 'error',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    def reset_agent_statistics(self, agent_name: Optional[str] = None) -> None:
        """Reset statistics for specific agent or all agents."""
        if agent_name and agent_name in self.agents:
            self.agents[agent_name]['success_count'] = 0
            self.agents[agent_name]['failure_count'] = 0
            self.agents[agent_name]['last_execution'] = None
            logger.info(f"Reset statistics for agent: {agent_name}")
        else:
            for name in self.agents:
                self.agents[name]['success_count'] = 0
                self.agents[name]['failure_count'] = 0
                self.agents[name]['last_execution'] = None
            logger.info("Reset statistics for all agents")
