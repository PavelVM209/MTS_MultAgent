"""
Base Agent Class for MTS MultAgent System

This module provides the abstract base class that all agents must inherit from.
It defines the common interface and provides shared functionality for validation,
error handling, and execution monitoring.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, ValidationError

import structlog

logger = structlog.get_logger()


class AgentResult(BaseModel):
    """Standard result format for all agent operations."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    agent_name: str
    task_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the MTS MultAgent System.
    
    All agents must inherit from this class and implement:
    - execute(): Main logic for processing tasks
    - validate(): Input validation logic
    
    The base class provides:
    - Error handling with graceful degradation
    - Execution timing and logging
    - Standardized result format
    - Configuration management
    """
    
    def __init__(self, config: Dict[str, Any], name: Optional[str] = None):
        """
        Initialize the agent with configuration.
        
        Args:
            config: Configuration dictionary
            name: Optional custom name (defaults to class name)
        """
        self.config = config
        self.name = name or self.__class__.__name__
        self.logger = logger.bind(agent=self.name)
        
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        """
        Execute the main task logic.
        
        Args:
            task: Task payload with required parameters
            
        Returns:
            AgentResult with execution results
        """
        pass
    
    @abstractmethod
    async def validate(self, task: Dict[str, Any]) -> bool:
        """
        Validate input task parameters.
        
        Args:
            task: Task payload to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    async def execute_with_fallback(self, task: Dict[str, Any], task_id: Optional[str] = None) -> AgentResult:
        """
        Execute task with comprehensive error handling and fallback strategies.
        
        This method provides:
        - Input validation
        - Timing and logging
        - Error catching and reporting
        - Graceful degradation when possible
        
        Args:
            task: Task payload
            task_id: Optional task identifier for tracking
            
        Returns:
            AgentResult with execution results or error information
        """
        start_time = time.time()
        
        try:
            self.logger.info("Agent execution started", task_id=task_id)
            
            # Validate input
            if not await self.validate(task):
                error_msg = f"Validation failed for {self.name}"
                self.logger.error("Validation failed", task_id=task_id, error=error_msg)
                return AgentResult(
                    success=False,
                    error=error_msg,
                    execution_time=time.time() - start_time,
                    agent_name=self.name,
                    task_id=task_id
                )
            
            # Execute main logic
            result = await self.execute(task)
            result.execution_time = time.time() - start_time
            result.agent_name = self.name
            result.task_id = task_id
            
            if result.success:
                self.logger.info(
                    "Agent execution completed successfully",
                    task_id=task_id,
                    execution_time=result.execution_time
                )
            else:
                self.logger.error(
                    "Agent execution failed",
                    task_id=task_id,
                    execution_time=result.execution_time,
                    error=result.error
                )
            
            return result
            
        except asyncio.TimeoutError:
            error_msg = f"Timeout occurred in {self.name}"
            self.logger.error("Timeout error", task_id=task_id, error=error_msg)
            return await self._handle_timeout_error(task, start_time, task_id)
            
        except ValidationError as e:
            error_msg = f"Validation error in {self.name}: {str(e)}"
            self.logger.error("Pydantic validation error", task_id=task_id, error=error_msg)
            return AgentResult(
                success=False,
                error=error_msg,
                execution_time=time.time() - start_time,
                agent_name=self.name,
                task_id=task_id
            )
            
        except Exception as e:
            error_msg = f"Unexpected error in {self.name}: {str(e)}"
            self.logger.error("Unexpected error", task_id=task_id, error=error_msg, exc_info=True)
            return await self._handle_unexpected_error(task, e, start_time, task_id)
    
    async def _handle_timeout_error(self, task: Dict[str, Any], start_time: float, task_id: Optional[str] = None) -> AgentResult:
        """
        Handle timeout errors with fallback strategy.
        
        Override this method in subclasses to provide agent-specific timeout handling.
        """
        return AgentResult(
            success=False,
            error=f"Timeout in {self.name} after {time.time() - start_time:.2f}s",
            execution_time=time.time() - start_time,
            agent_name=self.name,
            task_id=task_id,
            metadata={"fallback_used": "timeout_handling"}
        )
    
    async def _handle_unexpected_error(self, task: Dict[str, Any], error: Exception, start_time: float, task_id: Optional[str] = None) -> AgentResult:
        """
        Handle unexpected errors with fallback strategy.
        
        Override this method in subclasses to provide agent-specific error handling.
        """
        return AgentResult(
            success=False,
            error=f"Error in {self.name}: {str(error)}",
            execution_time=time.time() - start_time,
            agent_name=self.name,
            task_id=task_id,
            metadata={"fallback_used": "error_handling", "error_type": type(error).__name__}
        )
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with optional default.
        Supports dot notation for nested keys (e.g., "jira.base_url").
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        if '.' in key:
            # Handle nested keys with dot notation
            parts = key.split('.')
            current = self.config
            
            try:
                for part in parts:
                    current = current[part]
                return current
            except (KeyError, TypeError):
                return default
        else:
            # Handle top-level keys
            return self.config.get(key, default)
    
    def validate_config(self, required_keys: list[str]) -> bool:
        """
        Validate that required configuration keys are present.
        Supports dot notation for nested keys (e.g., "jira.base_url").
        
        Args:
            required_keys: List of required configuration keys
            
        Returns:
            True if all required keys are present, False otherwise
        """
        missing_keys = []
        
        for key in required_keys:
            if '.' in key:
                # Handle nested keys with dot notation
                parts = key.split('.')
                current = self.config
                
                try:
                    for part in parts:
                        current = current[part]
                    # If we get here, the key exists
                except (KeyError, TypeError):
                    missing_keys.append(key)
            else:
                # Handle top-level keys
                if key not in self.config:
                    missing_keys.append(key)
        
        if missing_keys:
            self.logger.error("Missing required configuration", missing_keys=missing_keys)
            return False
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for the agent.
        
        Override this method in subclasses to provide agent-specific health checks.
        
        Returns:
            Health check result dictionary
        """
        return {
            "agent_name": self.name,
            "status": "healthy",
            "timestamp": time.time(),
            "config_valid": len(self.config) > 0
        }
    
    def __str__(self) -> str:
        return f"{self.name}(config_keys={list(self.config.keys())})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', config={self.config})"


class AgentError(Exception):
    """Custom exception for agent-related errors."""
    
    def __init__(self, message: str, agent_name: str, task_id: Optional[str] = None):
        self.agent_name = agent_name
        self.task_id = task_id
        super().__init__(f"[{agent_name}] {message}" + (f" (task: {task_id})" if task_id else ""))


class ValidationError(AgentError):
    """Exception raised when task validation fails."""
    pass


class ConfigurationError(AgentError):
    """Exception raised when agent configuration is invalid."""
    pass
