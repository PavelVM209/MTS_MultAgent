# -*- coding: utf-8 -*-
"""
Base Agent - Foundation for all agents in Employee Monitoring System

Provides common functionality and interface for all agents.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent status enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class AgentConfig:
    """Configuration for agents."""
    name: str
    description: str
    version: str = "1.0.0"
    enabled: bool = True
    max_retries: int = 3
    timeout_seconds: int = 300
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Result from agent execution."""
    success: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)


class BaseAgent(ABC):
    """
    Base class for all agents in the Employee Monitoring System.
    
    Provides common functionality:
    - Configuration management
    - Error handling and retries
    - Logging and monitoring
    - Result standardization
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize base agent.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.status = AgentStatus.IDLE
        self.last_execution_time: Optional[datetime] = None
        self.execution_count = 0
        self.error_count = 0
        
        logger.info(f"BaseAgent initialized: {config.name} v{config.version}")
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute agent's main logic.
        
        Args:
            input_data: Input data for agent processing
            
        Returns:
            AgentResult: Execution result
        """
        pass
    
    async def execute_with_retry(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute agent with retry logic.
        
        Args:
            input_data: Input data for agent processing
            
        Returns:
            AgentResult: Execution result
        """
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                logger.info(f"Executing {self.config.name} (attempt {attempt + 1}/{self.config.max_retries + 1})")
                
                # Update status
                self.status = AgentStatus.RUNNING
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    self.execute(input_data),
                    timeout=self.config.timeout_seconds
                )
                
                # Update status and metrics
                self.status = AgentStatus.COMPLETED
                self.execution_count += 1
                self.last_execution_time = datetime.now()
                
                logger.info(f"{self.config.name} completed successfully")
                return result
                
            except asyncio.TimeoutError:
                last_error = f"Execution timeout after {self.config.timeout_seconds} seconds"
                logger.warning(f"{self.config.name} timeout on attempt {attempt + 1}")
                
            except Exception as e:
                last_error = str(e)
                self.error_count += 1
                logger.error(f"{self.config.name} failed on attempt {attempt + 1}: {e}")
            
            # Wait before retry (exponential backoff)
            if attempt < self.config.max_retries:
                wait_time = 2 ** attempt
                logger.info(f"Retrying {self.config.name} in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
        
        # All retries failed
        self.status = AgentStatus.ERROR
        error_result = AgentResult(
            success=False,
            message=f"Agent execution failed after {self.config.max_retries + 1} attempts",
            error=last_error,
            data={'attempts': self.config.max_retries + 1}
        )
        
        logger.error(f"{self.config.name} failed after all retries: {last_error}")
        return error_result
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get agent health status.
        
        Returns:
            Dict[str, Any]: Health status information
        """
        return {
            'agent_name': self.config.name,
            'status': self.status.value,
            'version': self.config.version,
            'enabled': self.config.enabled,
            'execution_count': self.execution_count,
            'error_count': self.error_count,
            'last_execution': self.last_execution_time.isoformat() if self.last_execution_time else None,
            'last_check': datetime.now().isoformat()
        }
    
    def reset_metrics(self) -> None:
        """Reset agent metrics."""
        self.execution_count = 0
        self.error_count = 0
        self.last_execution_time = None
        self.status = AgentStatus.IDLE
        
        logger.info(f"Reset metrics for {self.config.name}")
    
    def is_healthy(self) -> bool:
        """
        Check if agent is healthy.
        
        Returns:
            bool: True if agent is healthy
        """
        # Agent is unhealthy if too many errors
        if self.execution_count > 0:
            error_rate = self.error_count / self.execution_count
            return error_rate < 0.5  # Less than 50% error rate
        
        return True
    
    def __str__(self) -> str:
        """String representation of agent."""
        return f"{self.config.name} v{self.config.version} ({self.status.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation of agent."""
        return (f"{self.__class__.__name__}(name='{self.config.name}', "
                f"version='{self.config.version}', status='{self.status.value}')")


class AgentOrchestrator(BaseAgent):
    """
    Specialized agent for orchestrating other agents.
    
    Provides functionality to:
    - Coordinate multiple agents
    - Manage agent dependencies
    - Aggregate results
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.agents: Dict[str, BaseAgent] = {}
        self.dependency_graph: Dict[str, List[str]] = {}
    
    def register_agent(self, agent: BaseAgent, dependencies: List[str] = None) -> None:
        """
        Register an agent with the orchestrator.
        
        Args:
            agent: Agent to register
            dependencies: List of agent names this agent depends on
        """
        self.agents[agent.config.name] = agent
        self.dependency_graph[agent.config.name] = dependencies or []
        
        logger.info(f"Registered agent: {agent.config.name}")
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """
        Get agent by name.
        
        Args:
            name: Agent name
            
        Returns:
            Optional[BaseAgent]: Agent if found
        """
        return self.agents.get(name)
    
    async def get_orchestrator_status(self) -> Dict[str, Any]:
        """
        Get orchestrator and all agents status.
        
        Returns:
            Dict[str, Any]: Comprehensive status information
        """
        base_status = await self.get_health_status()
        
        agents_status = {}
        for name, agent in self.agents.items():
            agents_status[name] = await agent.get_health_status()
        
        return {
            **base_status,
            'registered_agents': len(self.agents),
            'agents': agents_status,
            'dependency_graph': self.dependency_graph
        }
