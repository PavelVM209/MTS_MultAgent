"""
Jira Analysis Schema for Scheduled Architecture

Validates JSON data structure for DailyJiraAgent outputs.
"""

from typing import Dict, Any, List
from datetime import datetime, date
from .base_schema import BaseSchema, ValidationResult, ValidationPatterns, ValidationUtils


class JiraAnalysisSchema(BaseSchema):
    """Schema for validating Jira analysis data from DailyJiraAgent"""
    
    def __init__(self):
        super().__init__("jira_analysis")
    
    async def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate Jira analysis data structure.
        
        Expected structure:
        {
            "date": "2026-03-25",
            "timestamp": "2026-03-25T19:00:00",
            "projects": {
                "CSI": {
                    "total_tasks": 45,
                    "completed_tasks": 12,
                    "in_progress_tasks": 25,
                    "blocked_tasks": 8,
                    "employees": {...}
                }
            },
            "system_metrics": {...},
            "_metadata": {...}
        }
        """
        result = ValidationResult(valid=True, errors=[], warnings=[])
        
        # 🔹 Required top-level fields
        required_fields = ["date", "timestamp", "projects", "system_metrics"]
        self._validate_required_fields(data, required_fields, result)
        
        # 🔹 Field type validation
        field_types = {
            "date": (str, date),
            "timestamp": (str, datetime),
            "projects": dict,
            "system_metrics": dict
        }
        self._validate_field_types(data, field_types, result)
        
        # 🔹 String pattern validation
        field_patterns = {
            "date": ValidationPatterns.DATE,
            "timestamp": ValidationPatterns.ISO_DATETIME
        }
        self._validate_string_patterns(data, field_patterns, result)
        
        # 🔹 Projects validation
        if "projects" in data and isinstance(data["projects"], dict):
            await self._validate_projects(data["projects"], result)
        
        # 🔹 System metrics validation
        if "system_metrics" in data and isinstance(data["system_metrics"], dict):
            self._validate_system_metrics(data["system_metrics"], result)
        
        # 🔹 Metadata validation (optional but should be valid if present)
        if "_metadata" in data and isinstance(data["_metadata"], dict):
            self._validate_metadata(data["_metadata"], result)
        
        return result
    
    async def _validate_projects(self, projects: Dict[str, Any], result: ValidationResult):
        """Validate projects structure"""
        if not projects:
            result.add_warning("No projects found in data")
            return
        
        for project_key, project_data in projects.items():
            if not isinstance(project_data, dict):
                result.add_error(
                    field=f"projects.{project_key}",
                    message=f"Project data must be dict",
                    value=project_data,
                    expected_type="dict"
                )
                continue
            
            # Validate project key format
            if not ValidationUtils.is_valid_jira_key(f"{project_key}-123"):
                result.add_warning(f"Project key '{project_key}' may not follow Jira conventions")
            
            # Validate project fields
            project_result = ValidationResult(valid=True, errors=[], warnings=[])
            
            required_project_fields = [
                "total_tasks", "completed_tasks", 
                "in_progress_tasks", "blocked_tasks"
            ]
            self._validate_required_fields(project_data, required_project_fields, project_result)
            
            # Validate task counts are non-negative integers
            task_fields = ["total_tasks", "completed_tasks", "in_progress_tasks", "blocked_tasks"]
            for field in task_fields:
                if field in project_data:
                    if not isinstance(project_data[field], int) or project_data[field] < 0:
                        project_result.add_error(
                            field=field,
                            message=f"Task count must be non-negative integer",
                            value=project_data[field],
                            expected_type="int>=0"
                        )
            
            # Validate task count consistency
            completed = project_data.get("completed_tasks", 0)
            in_progress = project_data.get("in_progress_tasks", 0)
            blocked = project_data.get("blocked_tasks", 0)
            total = project_data.get("total_tasks", 0)
            
            if completed + in_progress + blocked > total:
                project_result.add_error(
                    field="task_counts",
                    message="Sum of task states exceeds total tasks",
                    value={
                        "completed": completed,
                        "in_progress": in_progress,
                        "blocked": blocked,
                        "total": total
                    },
                    expected_type="consistent_counts"
                )
            
            # Validate employees if present
            if "employees" in project_data:
                await self._validate_project_employees(
                    project_data["employees"], 
                    f"projects.{project_key}.employees", 
                    project_result
                )
            
            # Add project errors to main result
            for error in project_result.errors:
                result.add_error(
                    field=f"projects.{project_key}.{error.field}",
                    message=error.message,
                    value=error.value,
                    expected_type=error.expected_type
                )
            
            for warning in project_result.warnings:
                result.add_warning(f"projects.{project_key}: {warning}")
    
    async def _validate_project_employees(
        self, 
        employees: Dict[str, Any], 
        field_prefix: str, 
        result: ValidationResult
    ):
        """Validate employee data within projects"""
        if not isinstance(employees, dict):
            result.add_error(
                field=field_prefix,
                message="Employees data must be dict",
                value=employees,
                expected_type="dict"
            )
            return
        
        for username, employee_data in employees.items():
            if not isinstance(employee_data, dict):
                result.add_error(
                    field=f"{field_prefix}.{username}",
                    message="Employee data must be dict",
                    value=employee_data,
                    expected_type="dict"
                )
                continue
            
            # Validate username format
            if not ValidationUtils.is_valid_jira_key(f"{username}-123"):
                result.add_warning(f"Username '{username}' may not follow Jira conventions")
            
            # Validate required employee fields
            required_employee_fields = ["username", "tasks", "metrics"]
            self._validate_required_fields(employee_data, required_employee_fields, result)
            
            # Validate tasks structure
            if "tasks" in employee_data:
                await self._validate_employee_tasks(
                    employee_data["tasks"],
                    f"{field_prefix}.{username}.tasks",
                    result
                )
            
            # Validate metrics structure
            if "metrics" in employee_data:
                self._validate_employee_metrics(
                    employee_data["metrics"],
                    f"{field_prefix}.{username}.metrics",
                    result
                )
    
    async def _validate_employee_tasks(
        self, 
        tasks: Dict[str, Any], 
        field_prefix: str, 
        result: ValidationResult
    ):
        """Validate employee task data"""
        if not isinstance(tasks, dict):
            result.add_error(
                field=field_prefix,
                message="Employee tasks must be dict",
                value=tasks,
                expected_type="dict"
            )
            return
        
        # Validate task count fields
        task_count_fields = ["total", "completed", "in_progress", "blocked"]
        for field in task_count_fields:
            if field in tasks:
                if not isinstance(tasks[field], int) or tasks[field] < 0:
                    result.add_error(
                        field=f"{field_prefix}.{field}",
                        message=f"Task count must be non-negative integer",
                        value=tasks[field],
                        expected_type="int>=0"
                    )
        
        # Validate task list if present
        if "task_list" in tasks:
            task_list = tasks["task_list"]
            if not isinstance(task_list, list):
                result.add_error(
                    field=f"{field_prefix}.task_list",
                    message="Task list must be array",
                    value=task_list,
                    expected_type="list"
                )
            else:
                # Validate individual task entries
                for i, task in enumerate(task_list):
                    if isinstance(task, dict):
                        self._validate_task_entry(
                            task,
                            f"{field_prefix}.task_list[{i}]",
                            result
                        )
    
    def _validate_task_entry(self, task: Dict[str, Any], field_prefix: str, result: ValidationResult):
        """Validate individual task entry"""
        required_task_fields = ["key", "summary", "status", "assignee"]
        self._validate_required_fields(task, required_task_fields, result)
        
        # Validate Jira issue key
        if "key" in task:
            if not ValidationUtils.is_valid_jira_key(task["key"]):
                result.add_error(
                    field=f"{field_prefix}.key",
                    message="Invalid Jira issue key format",
                    value=task["key"],
                    expected_type="jira_issue_key"
                )
        
        # Validate status
        if "status" in task:
            valid_statuses = [
                "To Do", "In Progress", "In Review", "Done", 
                "Blocked", "Ready for Testing", "Testing"
            ]
            if task["status"] not in valid_statuses:
                result.add_warning(
                    f"Task status '{task['status']}' at {field_prefix}.status may not be standard"
                )
        
        # Validate timestamp if present
        if "updated" in task:
            if not ValidationUtils.is_valid_datetime(task["updated"]):
                result.add_error(
                    field=f"{field_prefix}.updated",
                    message="Invalid datetime format",
                    value=task["updated"],
                    expected_type="iso_datetime"
                )
    
    def _validate_employee_metrics(
        self, 
        metrics: Dict[str, Any], 
        field_prefix: str, 
        result: ValidationResult
    ):
        """Validate employee performance metrics"""
        if not isinstance(metrics, dict):
            result.add_error(
                field=field_prefix,
                message="Employee metrics must be dict",
                value=metrics,
                expected_type="dict"
            )
            return
        
        # Validate performance score if present
        if "performance_score" in metrics:
            score = metrics["performance_score"]
            if not ValidationUtils.is_valid_performance_score(score):
                result.add_error(
                    field=f"{field_prefix}.performance_score",
                    message="Performance score must be between 0-10",
                    value=score,
                    expected_type="performance_score"
                )
        
        # Validate completion rate
        if "completion_rate" in metrics:
            rate = metrics["completion_rate"]
            if not isinstance(rate, (int, float)) or not (0 <= rate <= 100):
                result.add_error(
                    field=f"{field_prefix}.completion_rate",
                    message="Completion rate must be percentage (0-100)",
                    value=rate,
                    expected_type="percentage"
                )
        
        # Validate numeric metrics
        numeric_fields = [
            "avg_task_duration", "status_changes_today", 
            "git_commits_today", "tasks_assigned"
        ]
        for field in numeric_fields:
            if field in metrics:
                value = metrics[field]
                if not isinstance(value, (int, float)) or value < 0:
                    result.add_error(
                        field=f"{field_prefix}.{field}",
                        message=f"Metric must be non-negative number",
                        value=value,
                        expected_type="number>=0"
                    )
    
    def _validate_system_metrics(self, metrics: Dict[str, Any], result: ValidationResult):
        """Validate system metrics structure"""
        required_metrics = ["jira_api_calls", "processing_time_seconds", "quality_score"]
        self._validate_required_fields(metrics, required_metrics, result)
        
        # Validate numeric metrics
        numeric_ranges = {
            "jira_api_calls": (0, 1000),  # Reasonable range for daily API calls
            "processing_time_seconds": (0, 3600),  # Max 1 hour processing
            "quality_score": (0, 100)  # Percentage
        }
        self._validate_numeric_ranges(metrics, numeric_ranges, result)
    
    def _validate_metadata(self, metadata: Dict[str, Any], result: ValidationResult):
        """Validate metadata structure"""
        # Check for required metadata fields
        required_metadata = ["data_type", "persisted_at", "persisted_by", "version"]
        self._validate_required_fields(metadata, required_metadata, result)
        
        # Validate data type
        if "data_type" in metadata:
            if metadata["data_type"] != "daily_jira_data":
                result.add_error(
                    field="_metadata.data_type",
                    message="Incorrect data type for Jira analysis",
                    value=metadata["data_type"],
                    expected_type="daily_jira_data"
                )
        
        # Validate timestamps
        if "persisted_at" in metadata:
            if not ValidationUtils.is_valid_datetime(metadata["persisted_at"]):
                result.add_error(
                    field="_metadata.persisted_at",
                    message="Invalid datetime format",
                    value=metadata["persisted_at"],
                    expected_type="iso_datetime"
                )
        
        # Validate version format
        if "version" in metadata:
            version = metadata["version"]
            if not isinstance(version, str) or not version:
                result.add_error(
                    field="_metadata.version",
                    message="Version must be non-empty string",
                    value=version,
                    expected_type="version_string"
                )


# Additional validation functions for Jira-specific scenarios
def validate_employee_consistency(projects_data: Dict[str, Any]) -> List[str]:
    """
    Validate employee consistency across projects.
    Returns list of warnings about inconsistent data.
    """
    warnings = []
    
    # Collect all employees across projects
    all_employees = {}
    for project_key, project_data in projects_data.items():
        if "employees" in project_data and isinstance(project_data["employees"], dict):
            for username, employee_data in project_data["employees"].items():
                if username not in all_employees:
                    all_employees[username] = []
                all_employees[username].append(project_key)
    
    # Check for employees working on too many projects
    for username, project_list in all_employees.items():
        if len(project_list) > 3:
            warnings.append(
                f"Employee '{username}' assigned to {len(project_list)} projects: {', '.join(project_list)}"
            )
    
    return warnings


def validate_task_distribution(projects_data: Dict[str, Any]) -> List[str]:
    """
    Validate task distribution for reasonableness.
    Returns list of warnings about unusual distributions.
    """
    warnings = []
    
    for project_key, project_data in projects_data.items():
        total_tasks = project_data.get("total_tasks", 0)
        in_progress = project_data.get("in_progress_tasks", 0)
        blocked = project_data.get("blocked_tasks", 0)
        
        # Warn about too many blocked tasks
        if total_tasks > 0 and (blocked / total_tasks) > 0.3:  # 30% blocked
            warnings.append(
                f"Project '{project_key}' has {blocked} blocked tasks ({blocked/total_tasks*100:.1f}%)"
            )
        
        # Warn about idle project (no tasks in progress)
        if total_tasks > 10 and in_progress == 0:
            warnings.append(
                f"Project '{project_key}' has no tasks in progress (idle project)"
            )
    
    return warnings
