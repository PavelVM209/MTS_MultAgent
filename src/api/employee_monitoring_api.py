"""
Employee Monitoring REST API

Provides RESTful API endpoints for managing the Employee Monitoring System,
including status monitoring, task management, and workflow control.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..scheduler.employee_monitoring_scheduler import EmployeeMonitoringScheduler, WorkflowType, ScheduleType
from ..orchestrator.employee_monitoring_orchestrator import EmployeeMonitoringOrchestrator
from ..core.config import get_employee_monitoring_config

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class TaskScheduleRequest(BaseModel):
    """Request model for scheduling a task."""
    name: str = Field(..., description="Human-readable name for the task")
    workflow_type: str = Field(..., description="Type of workflow to execute")
    schedule_type: str = Field(..., description="Type of scheduling")
    schedule_expression: str = Field(..., description="Schedule expression")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data for the workflow")
    enabled: bool = Field(default=True, description="Whether the task is enabled")
    max_retries: Optional[int] = Field(default=3, description="Maximum number of retries")
    timeout_minutes: Optional[int] = Field(default=60, description="Timeout in minutes")

class TaskExecuteRequest(BaseModel):
    """Request model for executing a task immediately."""
    workflow_type: str = Field(..., description="Type of workflow to execute")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data for the workflow")
    timeout_minutes: Optional[int] = Field(default=60, description="Timeout in minutes")

class SystemStatusResponse(BaseModel):
    """Response model for system status."""
    system_running: bool
    timestamp: str
    components: Dict[str, Any]

class TaskStatusResponse(BaseModel):
    """Response model for task status."""
    task_id: str
    name: str
    workflow_type: str
    schedule_type: str
    schedule_expression: str
    enabled: bool
    status: str
    last_run: Optional[str]
    next_run: Optional[str]
    run_count: int
    success_count: int
    failure_count: int

class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""
    workflow_id: str
    workflow_type: str
    status: str
    start_time: str
    end_time: Optional[str]
    duration: Optional[str]
    steps_completed: int
    total_steps: int
    error_message: Optional[str]

# Initialize FastAPI app
app = FastAPI(
    title="MTS Employee Monitoring API",
    description="REST API for MTS MultAgent Employee Monitoring System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for system components
scheduler: Optional[EmployeeMonitoringScheduler] = None
orchestrator: Optional[EmployeeMonitoringOrchestrator] = None
system_running = False

@app.on_event("startup")
async def startup_event():
    """Initialize API components on startup."""
    global scheduler, orchestrator, system_running
    
    try:
        # Initialize components
        scheduler = EmployeeMonitoringScheduler()
        orchestrator = EmployeeMonitoringOrchestrator()
        
        # Start the scheduler
        await scheduler.start()
        system_running = True
        
        logger.info("Employee Monitoring API started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start API: {e}")
        system_running = False

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global scheduler, system_running
    
    if scheduler and system_running:
        await scheduler.stop()
        system_running = False
        logger.info("Employee Monitoring API stopped")

# Root endpoint
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "MTS Employee Monitoring API",
        "version": "1.0.0",
        "status": "running" if system_running else "stopped",
        "docs": "/docs",
        "health": "/health"
    }

# Health check endpoint
@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Comprehensive health check endpoint."""
    if not system_running:
        raise HTTPException(status_code=503, detail="System not running")
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # Check scheduler
    if scheduler:
        try:
            scheduler_status = await scheduler.get_scheduler_status()
            health_status["components"]["scheduler"] = scheduler_status
        except Exception as e:
            health_status["components"]["scheduler"] = {"status": "error", "error": str(e)}
    
    # Check orchestrator
    if orchestrator:
        try:
            orchestrator_status = await orchestrator.get_orchestrator_status()
            health_status["components"]["orchestrator"] = orchestrator_status
        except Exception as e:
            health_status["components"]["orchestrator"] = {"status": "error", "error": str(e)}
    
    return health_status

# System status endpoint
@app.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    """Get comprehensive system status."""
    if not system_running:
        raise HTTPException(status_code=503, detail="System not running")
    
    status = {
        "system_running": system_running,
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # Get detailed component status
    if scheduler:
        status["components"]["scheduler"] = await scheduler.get_scheduler_status()
    
    if orchestrator:
        status["components"]["orchestrator"] = await orchestrator.get_orchestrator_status()
    
    return status

# Task management endpoints
@app.get("/tasks", response_model=List[TaskStatusResponse])
async def get_scheduled_tasks():
    """Get all scheduled tasks."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    
    try:
        tasks = await scheduler.get_scheduled_tasks()
        return [
            TaskStatusResponse(
                task_id=task.task_id,
                name=task.name,
                workflow_type=task.workflow_type.value,
                schedule_type=task.schedule_type.value,
                schedule_expression=task.schedule_expression,
                enabled=task.enabled,
                status=task.status.value,
                last_run=task.last_run.isoformat() if task.last_run else None,
                next_run=task.next_run.isoformat() if task.next_run else None,
                run_count=task.run_count,
                success_count=task.success_count,
                failure_count=task.failure_count
            )
            for task in tasks
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {str(e)}")

@app.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get status of a specific task."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    
    try:
        task = await scheduler.get_task_status(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskStatusResponse(
            task_id=task.task_id,
            name=task.name,
            workflow_type=task.workflow_type.value,
            schedule_type=task.schedule_type.value,
            schedule_expression=task.schedule_expression,
            enabled=task.enabled,
            status=task.status.value,
            last_run=task.last_run.isoformat() if task.last_run else None,
            next_run=task.next_run.isoformat() if task.next_run else None,
            run_count=task.run_count,
            success_count=task.success_count,
            failure_count=task.failure_count
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")

@app.post("/tasks", response_model=Dict[str, str])
async def schedule_task(task_request: TaskScheduleRequest):
    """Schedule a new task."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    
    try:
        # Validate workflow type
        try:
            workflow_type = WorkflowType(task_request.workflow_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid workflow type: {task_request.workflow_type}")
        
        # Validate schedule type
        try:
            schedule_type = ScheduleType(task_request.schedule_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid schedule type: {task_request.schedule_type}")
        
        # Schedule the task
        task_id = await scheduler.add_scheduled_task(
            name=task_request.name,
            workflow_type=workflow_type,
            schedule_type=schedule_type,
            schedule_expression=task_request.schedule_expression,
            input_data=task_request.input_data,
            enabled=task_request.enabled,
            max_retries=task_request.max_retries,
            timeout_minutes=task_request.timeout_minutes
        )
        
        return {"task_id": task_id, "message": "Task scheduled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule task: {str(e)}")

@app.delete("/tasks/{task_id}", response_model=Dict[str, str])
async def remove_task(task_id: str):
    """Remove a scheduled task."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    
    try:
        success = await scheduler.remove_scheduled_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {"message": "Task removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove task: {str(e)}")

@app.post("/tasks/{task_id}/run", response_model=Dict[str, str])
async def run_task_immediately(task_id: str):
    """Run a task immediately."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    
    try:
        success = await scheduler.run_task_now(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {"message": "Task started successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run task: {str(e)}")

@app.put("/tasks/{task_id}/enable", response_model=Dict[str, str])
async def enable_task(task_id: str):
    """Enable a scheduled task."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    
    try:
        success = await scheduler.enable_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {"message": "Task enabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enable task: {str(e)}")

@app.put("/tasks/{task_id}/disable", response_model=Dict[str, str])
async def disable_task(task_id: str):
    """Disable a scheduled task."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    
    try:
        success = await scheduler.disable_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {"message": "Task disabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disable task: {str(e)}")

# Workflow management endpoints
@app.post("/workflows/execute", response_model=Dict[str, str])
async def execute_workflow(workflow_request: TaskExecuteRequest, background_tasks: BackgroundTasks):
    """Execute a workflow immediately."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")
    
    try:
        # Validate workflow type
        try:
            workflow_type = WorkflowType(workflow_request.workflow_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid workflow type: {workflow_request.workflow_type}")
        
        # Execute workflow in background
        async def run_workflow():
            try:
                await orchestrator.execute_workflow(
                    workflow_type=workflow_type,
                    input_data=workflow_request.input_data
                )
            except Exception as e:
                logger.error(f"Background workflow execution failed: {e}")
        
        background_tasks.add_task(run_workflow)
        
        return {"message": "Workflow execution started", "workflow_type": workflow_request.workflow_type}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {str(e)}")

@app.get("/workflows", response_model=List[WorkflowStatusResponse])
async def get_active_workflows():
    """Get all active workflows."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")
    
    try:
        workflows = await orchestrator.get_active_workflows()
        return [
            WorkflowStatusResponse(
                workflow_id=workflow.workflow_id,
                workflow_type=workflow.workflow_type.value,
                status=workflow.status.value,
                start_time=workflow.start_time.isoformat(),
                end_time=workflow.end_time.isoformat() if workflow.end_time else None,
                duration=str(workflow.end_time - workflow.start_time) if workflow.end_time else None,
                steps_completed=len(workflow.results),
                total_steps=len(workflow.steps),
                error_message=workflow.error_message
            )
            for workflow in workflows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflows: {str(e)}")

@app.get("/workflows/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str):
    """Get status of a specific workflow."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")
    
    try:
        workflow = await orchestrator.get_workflow_status(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return WorkflowStatusResponse(
            workflow_id=workflow.workflow_id,
            workflow_type=workflow.workflow_type.value,
            status=workflow.status.value,
            start_time=workflow.start_time.isoformat(),
            end_time=workflow.end_time.isoformat() if workflow.end_time else None,
            duration=str(workflow.end_time - workflow.start_time) if workflow.end_time else None,
            steps_completed=len(workflow.results),
            total_steps=len(workflow.steps),
            error_message=workflow.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")

@app.delete("/workflows/{workflow_id}", response_model=Dict[str, str])
async def cancel_workflow(workflow_id: str):
    """Cancel a running workflow."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")
    
    try:
        success = await orchestrator.cancel_workflow(workflow_id)
        if not success:
            raise HTTPException(status_code=404, detail="Workflow not found or not running")
        
        return {"message": "Workflow cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel workflow: {str(e)}")

# Configuration endpoints
@app.get("/config", response_model=Dict[str, Any])
async def get_configuration():
    """Get current system configuration."""
    try:
        config = get_employee_monitoring_config()
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        # Remove sensitive information
        safe_config = {
            "jira": {
                "base_url": config.get("jira", {}).get("base_url"),
                "projects": config.get("jira", {}).get("projects", [])[:5],  # Limit to first 5
                "projects_count": len(config.get("jira", {}).get("projects", []))
            },
            "confluence": {
                "base_url": config.get("confluence", {}).get("base_url"),
                "space": config.get("confluence", {}).get("space")
            },
            "employees": {
                "count": len(config.get("employees", {}).get("list", [])),
                "groups": list(config.get("employees", {}).get("groups", {}).keys())
            },
            "scheduler": config.get("scheduler", {}),
            "quality": config.get("quality", {}),
            "reports": config.get("reports", {})
        }
        
        return safe_config
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")

# Reports endpoints
@app.get("/reports/history", response_model=List[Dict[str, Any]])
async def get_report_history(limit: int = Query(default=50, le=100)):
    """Get report execution history."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    
    try:
        history = await scheduler.get_task_history(limit)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report history: {str(e)}")

# Utility endpoints
@app.get("/info", response_model=Dict[str, Any])
async def get_system_info():
    """Get detailed system information."""
    config = get_employee_monitoring_config()
    
    return {
        "api_version": "1.0.0",
        "system_running": system_running,
        "configuration_loaded": bool(config),
        "supported_workflow_types": [wt.value for wt in WorkflowType],
        "supported_schedule_types": [st.value for st in ScheduleType],
        "features": {
            "task_scheduling": True,
            "workflow_execution": True,
            "quality_validation": True,
            "confluence_publishing": True,
            "interactive_mode": True,
            "health_monitoring": True
        },
        "endpoints": {
            "tasks": "/tasks",
            "workflows": "/workflows", 
            "status": "/status",
            "health": "/health",
            "config": "/config",
            "reports": "/reports/history"
        }
    }

# Main function to run the API server
def run_api_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the API server."""
    uvicorn.run(
        "src.api.employee_monitoring_api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    run_api_server()
