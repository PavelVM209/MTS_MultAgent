"""
Daily JIRA Analyzer Agent

Analyzes JIRA tasks and projects to track employee workload,
project progress, and generate insights for daily reporting.
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from ..core.base_agent import BaseAgent, AgentConfig, AgentResult
from ..core.llm_client import LLMClient, LLMRequest, analyze_jira_data
from ..core.json_memory_store import JSONMemoryStore
from ..core.schemas.jira_schema import JiraAnalysisSchema
from ..core.quality_metrics import QualityMetrics
from ..core.config import get_config

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """JIRA task status."""
    TODO = "to_do"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    BLOCKED = "blocked"


class Priority(Enum):
    """Task priority levels."""
    LOWEST = "lowest"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    HIGHEST = "highest"


@dataclass
class JiraTask:
    """Represents a JIRA task."""
    id: str
    key: str
    summary: str
    status: TaskStatus
    priority: Priority
    assignee: Optional[str]
    reporter: Optional[str]
    project: str
    created: datetime
    updated: datetime
    due_date: Optional[datetime]
    story_points: Optional[float]
    labels: List[str] = field(default_factory=list)
    components: List[str] = field(default_factory=list)
    description: Optional[str] = None
    comments_count: int = 0


@dataclass
class EmployeeWorkload:
    """Employee workload information."""
    employee: str
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    blocked_tasks: int
    overdue_tasks: int
    total_story_points: float
    completed_story_points: float
    completion_rate: float
    avg_task_duration: Optional[timedelta] = None


@dataclass
class ProjectProgress:
    """Project progress information."""
    project: str
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    total_story_points: float
    completed_story_points: float
    completion_percentage: float
    active_employees: Set[str] = field(default_factory=set)
    last_activity: Optional[datetime] = None
    blockers: List[str] = field(default_factory=list)


@dataclass
class JiraAnalysisResult:
    """Complete JIRA analysis result."""
    analysis_date: datetime
    tasks_analyzed: int
    employees_workload: Dict[str, EmployeeWorkload]
    projects_progress: Dict[str, ProjectProgress]
    insights: List[str]
    recommendations: List[str]
    quality_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class DailyJiraAnalyzer(BaseAgent):
    """
    Daily JIRA Analysis Agent.
    
    Analyzes JIRA tasks to track:
    - Employee workload and performance
    - Project progress and completion rates
    - Blockers and risks
    - Quality metrics and insights
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize Daily JIRA Analyzer.
        
        Args:
            config: Agent configuration
        """
        super().__init__(
            config or AgentConfig(
                name="DailyJiraAnalyzer",
                description="Analyzes JIRA tasks for employee workload and project progress",
                version="1.0.0"
            )
        )
        
        # Initialize components
        self.llm_client = LLMClient()
        self.memory_store = JSONMemoryStore()
        self.quality_metrics = QualityMetrics()
        
        # Load configuration
        app_config = get_config()
        self.jira_config = app_config.get('jira', {})
        self.analysis_config = self.config.parameters.get('analysis', {})
        
        # Analysis parameters
        self.max_tasks_per_run = self.analysis_config.get('max_tasks_per_run', 1000)
        self.due_date_threshold_days = self.analysis_config.get('due_date_threshold_days', 3)
        self.min_story_points_for_analysis = self.analysis_config.get('min_story_points', 0)
        
        # Regex patterns for parsing
        self.task_key_pattern = re.compile(r'[A-Z]+-\d+')
        self.story_points_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(?:sp|story\s*points?)', re.IGNORECASE)
        
        logger.info("DailyJiraAnalyzer initialized")
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute JIRA analysis.
        
        Args:
            input_data: Analysis input data containing JIRA tasks and filters
            
        Returns:
            AgentResult with analysis findings
        """
        try:
            logger.info("Starting Daily JIRA Analysis")
            start_time = datetime.now()
            
            # Extract input parameters
            jira_tasks_data = input_data.get('jira_tasks', [])
            analysis_filters = input_data.get('filters', {})
            include_llm_analysis = input_data.get('include_llm_analysis', True)
            
            # Parse and validate tasks
            tasks = await self._parse_jira_tasks(jira_tasks_data)
            
            if not tasks:
                return AgentResult(
                    success=False,
                    message="No JIRA tasks found for analysis",
                    data={}
                )
            
            # Limit tasks if necessary
            if len(tasks) > self.max_tasks_per_run:
                tasks = tasks[:self.max_tasks_per_run]
                logger.info(f"Limited analysis to {self.max_tasks_per_run} tasks")
            
            # Perform analysis
            analysis_result = await self._analyze_tasks(tasks, analysis_filters)
            
            # Add LLM insights if requested
            if include_llm_analysis:
                await self._add_llm_insights(analysis_result, tasks)
            
            # Validate and save results
            schema = JiraAnalysisSchema()
            validated_data = await self._validate_and_format_results(analysis_result, schema)
            
            # Save to memory store
            await self._save_analysis_results(validated_data)
            
            # Calculate execution time
            execution_time = datetime.now() - start_time
            
            logger.info(f"Daily JIRA Analysis completed in {execution_time.total_seconds():.2f}s, "
                       f"analyzed {len(tasks)} tasks, quality score: {analysis_result.quality_score:.2f}")
            
            return AgentResult(
                success=True,
                message=f"Successfully analyzed {len(tasks)} JIRA tasks",
                data=validated_data,
                metadata={
                    'execution_time': execution_time.total_seconds(),
                    'tasks_analyzed': len(tasks),
                    'quality_score': analysis_result.quality_score,
                    'analysis_date': analysis_result.analysis_date.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Daily JIRA Analysis failed: {e}")
            return AgentResult(
                success=False,
                message=f"Analysis failed: {str(e)}",
                data={},
                error=str(e)
            )
    
    async def _parse_jira_tasks(self, tasks_data: List[Dict[str, Any]]) -> List[JiraTask]:
        """Parse raw JIRA task data into structured objects."""
        tasks = []
        
        for task_data in tasks_data:
            try:
                # Parse basic fields
                task = JiraTask(
                    id=str(task_data.get('id', ''")),
                    key=task_data.get('key', ''),
                    summary=task_data.get('summary', ''),
                    status=self._parse_status(task_data.get('status', '')),
                    priority=self._parse_priority(task_data.get('priority', '')),
                    assignee=task_data.get('assignee'),
                    reporter=task_data.get('reporter'),
                    project=task_data.get('project', ''),
                    created=self._parse_datetime(task_data.get('created')),
                    updated=self._parse_datetime(task_data.get('updated')),
                    due_date=self._parse_datetime(task_data.get('due_date')),
                    story_points=self._parse_story_points(task_data.get('story_points')),
                    labels=task_data.get('labels', []),
                    components=task_data.get('components', []),
                    description=task_data.get('description'),
                    comments_count=task_data.get('comments_count', 0)
                )
                
                tasks.append(task)
                
            except Exception as e:
                logger.warning(f"Failed to parse JIRA task {task_data.get('key', 'unknown')}: {e}")
                continue
        
        return tasks
    
    def _parse_status(self, status_str: str) -> TaskStatus:
        """Parse task status string."""
        status_str = status_str.lower().replace(' ', '_')
        
        status_mapping = {
            'to_do': TaskStatus.TODO,
            'todo': TaskStatus.TODO,
            'in_progress': TaskStatus.IN_PROGRESS,
            'progress': TaskStatus.IN_PROGRESS,
            'in_review': TaskStatus.IN_REVIEW,
            'review': TaskStatus.IN_REVIEW,
            'done': TaskStatus.DONE,
            'completed': TaskStatus.DONE,
            'closed': TaskStatus.DONE,
            'blocked': TaskStatus.BLOCKED,
            'blocked_issue': TaskStatus.BLOCKED
        }
        
        return status_mapping.get(status_str, TaskStatus.TODO)
    
    def _parse_priority(self, priority_str: str) -> Priority:
        """Parse priority string."""
        priority_str = priority_str.lower()
        
        priority_mapping = {
            'lowest': Priority.LOWEST,
            'low': Priority.LOW,
            'medium': Priority.MEDIUM,
            'high': Priority.HIGH,
            'highest': Priority.HIGHEST
        }
        
        return priority_mapping.get(priority_str, Priority.MEDIUM)
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string."""
        if not dt_str:
            return None
            
        try:
            # Try common datetime formats
            formats = [
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(dt_str, fmt)
                except ValueError:
                    continue
                    
        except Exception as e:
            logger.warning(f"Failed to parse datetime '{dt_str}': {e}")
        
        return None
    
    def _parse_story_points(self, sp_value: Any) -> Optional[float]:
        """Parse story points value."""
        if sp_value is None:
            return None
            
        try:
            if isinstance(sp_value, (int, float)):
                return float(sp_value)
            
            if isinstance(sp_value, str):
                # Extract number from string
                match = self.story_points_pattern.search(sp_value)
                if match:
                    return float(match.group(1))
                
                # Try direct conversion
                try:
                    return float(sp_value)
                except ValueError:
                    pass
                    
        except Exception as e:
            logger.warning(f"Failed to parse story points '{sp_value}': {e}")
        
        return None
    
    async def _analyze_tasks(self, tasks: List[JiraTask], filters: Dict[str, Any]) -> JiraAnalysisResult:
        """Analyze JIRA tasks and generate insights."""
        analysis_date = datetime.now()
        
        # Group tasks by assignee and project
        employees_tasks = {}
        projects_tasks = {}
        
        for task in tasks:
            # Group by employee
            if task.assignee:
                if task.assignee not in employees_tasks:
                    employees_tasks[task.assignee] = []
                employees_tasks[task.assignee].append(task)
            
            # Group by project
            if task.project:
                if task.project not in projects_tasks:
                    projects_tasks[task.project] = []
                projects_tasks[task.project].append(task)
        
        # Analyze employee workloads
        employees_workload = {}
        for employee, emp_tasks in employees_tasks.items():
            employees_workload[employee] = await self._analyze_employee_workload(employee, emp_tasks)
        
        # Analyze project progress
        projects_progress = {}
        for project, proj_tasks in projects_tasks.items():
            projects_progress[project] = await self._analyze_project_progress(project, proj_tasks)
        
        # Generate insights and recommendations
        insights = await self._generate_insights(employees_workload, projects_progress, tasks)
        recommendations = await self._generate_recommendations(employees_workload, projects_progress, tasks)
        
        # Calculate quality score
        quality_score = await self._calculate_analysis_quality(employees_workload, projects_progress)
        
        return JiraAnalysisResult(
            analysis_date=analysis_date,
            tasks_analyzed=len(tasks),
            employees_workload=employees_workload,
            projects_progress=projects_progress,
            insights=insights,
            recommendations=recommendations,
            quality_score=quality_score
        )
    
    async def _analyze_employee_workload(self, employee: str, tasks: List[JiraTask]) -> EmployeeWorkload:
        """Analyze individual employee workload."""
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task.status == TaskStatus.DONE)
        in_progress_tasks = sum(1 for task in tasks if task.status == TaskStatus.IN_PROGRESS)
        blocked_tasks = sum(1 for task in tasks if task.status == TaskStatus.BLOCKED)
        
        # Calculate overdue tasks
        now = datetime.now()
        overdue_tasks = sum(1 for task in tasks 
                           if task.due_date and task.due_date < now and task.status != TaskStatus.DONE)
        
        # Calculate story points
        total_story_points = sum(task.story_points or 0 for task in tasks)
        completed_story_points = sum(task.story_points or 0 
                                   for task in tasks if task.status == TaskStatus.DONE)
        
        # Calculate completion rate
        completion_rate = completed_tasks / max(total_tasks, 1)
        
        # Calculate average task duration
        completed_tasks_with_dates = [task for task in tasks 
                                    if task.status == TaskStatus.DONE and task.created and task.updated]
        
        avg_task_duration = None
        if completed_tasks_with_dates:
            durations = [(task.updated - task.created) for task in completed_tasks_with_dates]
            avg_task_duration = sum(durations, timedelta()) / len(durations)
        
        return EmployeeWorkload(
            employee=employee,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            in_progress_tasks=in_progress_tasks,
            blocked_tasks=blocked_tasks,
            overdue_tasks=overdue_tasks,
            total_story_points=total_story_points,
            completed_story_points=completed_story_points,
            completion_rate=completion_rate,
            avg_task_duration=avg_task_duration
        )
    
    async def _analyze_project_progress(self, project: str, tasks: List[JiraTask]) -> ProjectProgress:
        """Analyze project progress."""
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task.status == TaskStatus.DONE)
        in_progress_tasks = sum(1 for task in tasks if task.status == TaskStatus.IN_PROGRESS)
        
        # Calculate story points
        total_story_points = sum(task.story_points or 0 for task in tasks)
        completed_story_points = sum(task.story_points or 0 
                                   for task in tasks if task.status == TaskStatus.DONE)
        
        # Calculate completion percentage
        completion_percentage = (completed_story_points / max(total_story_points, 1)) * 100
        
        # Get active employees
        active_employees = {task.assignee for task in tasks if task.assignee}
        
        # Get last activity
        last_activity = max((task.updated for task in tasks), default=None)
        
        # Identify blockers
        blockers = [
            f"{task.key}: {task.summary}" 
            for task in tasks if task.status == TaskStatus.BLOCKED
        ]
        
        return ProjectProgress(
            project=project,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            in_progress_tasks=in_progress_tasks,
            total_story_points=total_story_points,
            completed_story_points=completed_story_points,
            completion_percentage=completion_percentage,
            active_employees=active_employees,
            last_activity=last_activity,
            blockers=blockers
        )
    
    async def _generate_insights(
        self, 
        employees_workload: Dict[str, EmployeeWorkload], 
        projects_progress: Dict[str, ProjectProgress],
        all_tasks: List[JiraTask]
    ) -> List[str]:
        """Generate analysis insights."""
        insights = []
        
        # Workload insights
        overloaded_employees = [
            emp for emp, workload in employees_workload.items()
            if workload.in_progress_tasks > 5
        ]
        if overloaded_employees:
            insights.append(f"High workload detected for {len(overloaded_employees)} employees")
        
        # Project progress insights
        stalled_projects = [
            proj for proj, progress in projects_progress.items()
            if progress.completion_percentage < 20 and progress.total_tasks > 10
        ]
        if stalled_projects:
            insights.append(f"{len(stalled_projects)} projects showing slow progress")
        
        # Blocker insights
        total_blocked = sum(workload.blocked_tasks for workload in employees_workload.values())
        if total_blocked > 0:
            insights.append(f"{total_blocked} tasks currently blocked")
        
        # Completion rate insights
        avg_completion_rate = sum(wl.completion_rate for wl in employees_workload.values()) / max(len(employees_workload), 1)
        if avg_completion_rate < 0.7:
            insights.append("Below average task completion rate detected")
        
        # Overdue tasks insights
        total_overdue = sum(workload.overdue_tasks for workload in employees_workload.values())
        if total_overdue > 0:
            insights.append(f"{total_overdue} tasks are overdue")
        
        return insights
    
    async def _generate_recommendations(
        self, 
        employees_workload: Dict[str, EmployeeWorkload], 
        projects_progress: Dict[str, ProjectProgress],
        all_tasks: List[JiraTask]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Workload balancing recommendations
        overloaded_employees = [
            emp for emp, workload in employees_workload.items()
            if workload.in_progress_tasks > 5
        ]
        if overloaded_employees:
            recommendations.append("Consider redistributing tasks from overloaded team members")
        
        # Blocker resolution recommendations
        total_blocked = sum(workload.blocked_tasks for workload in employees_workload.values())
        if total_blocked > 0:
            recommendations.append("Address blocked tasks to prevent delays")
        
        # Overdue tasks recommendations
        overdue_employees = [
            emp for emp, workload in employees_workload.items()
            if workload.overdue_tasks > 0
        ]
        if overdue_employees:
            recommendations.append("Review and update overdue task deadlines")
        
        # Project progress recommendations
        low_completion_projects = [
            proj for proj, progress in projects_progress.items()
            if progress.completion_percentage < 50 and progress.total_tasks > 5
        ]
        if low_completion_projects:
            recommendations.append("Focus on projects with low completion rates")
        
        # Story points recommendations
        projects_without_points = [
            proj for proj, progress in projects_progress.items()
            if progress.total_story_points == 0 and progress.total_tasks > 0
        ]
        if projects_without_points:
            recommendations.append("Consider adding story points for better estimation")
        
        return recommendations
    
    async def _add_llm_insights(self, analysis_result: JiraAnalysisResult, tasks: List[JiraTask]) -> None:
        """Add LLM-powered insights to analysis results."""
        try:
            # Prepare data for LLM analysis
            jira_data_summary = self._prepare_jira_data_for_llm(analysis_result, tasks)
            
            # Get LLM insights
            llm_analysis = await analyze_jira_data(jira_data_summary)
            
            # Merge with existing insights and recommendations
            if 'insights' in llm_analysis:
                analysis_result.insights.extend(llm_analysis['insights'])
            
            if 'recommendations' in llm_analysis:
                analysis_result.recommendations.extend(llm_analysis['recommendations'])
            
            # Add LLM metadata
            analysis_result.metadata['llm_analysis'] = llm_analysis
            
        except Exception as e:
            logger.warning(f"Failed to add LLM insights: {e}")
    
    def _prepare_jira_data_for_llm(self, analysis_result: JiraAnalysisResult, tasks: List[JiraTask]) -> str:
        """Prepare JIRA data summary for LLM analysis."""
        summary_parts = [
            f"JIRA Analysis Summary - {analysis_result.analysis_date.strftime('%Y-%m-%d')}",
            f"Total Tasks Analyzed: {analysis_result.tasks_analyzed}",
            "",
            "Employee Workload Summary:"
        ]
        
        for employee, workload in analysis_result.employees_workload.items():
            summary_parts.append(
                f"- {employee}: {workload.total_tasks} tasks, "
                f"{workload.completion_rate:.1%} completion rate, "
                f"{workload.in_progress_tasks} in progress"
            )
        
        summary_parts.extend([
            "",
            "Project Progress Summary:"
        ])
        
        for project, progress in analysis_result.projects_progress.items():
            summary_parts.append(
                f"- {project}: {progress.completion_percentage:.1f}% complete, "
                f"{progress.total_tasks} total tasks"
            )
        
        summary_parts.extend([
            "",
            "Current Insights:",
        ] + [f"- {insight}" for insight in analysis_result.insights])
        
        return "\n".join(summary_parts)
    
    async def _calculate_analysis_quality(
        self, 
        employees_workload: Dict[str, EmployeeWorkload], 
        projects_progress: Dict[str, ProjectProgress]
    ) -> float:
        """Calculate analysis quality score."""
        try:
            quality_factors = []
            
            # Data completeness score
            if employees_workload and projects_progress:
                completeness_score = min(1.0, len(employees_workload) / 5.0)  # Expect at least 5 employees
                quality_factors.append(completeness_score)
            
            # Insight quality score
            total_employees = len(employees_workload)
            if total_employees > 0:
                overloaded_count = sum(1 for wl in employees_workload.values() if wl.in_progress_tasks > 5)
                insight_score = 1.0 - (overloaded_count / max(total_employees, 1))
                quality_factors.append(insight_score)
            
            # Project health score
            if projects_progress:
                avg_completion = sum(p.completion_percentage for p in projects_progress.values()) / len(projects_progress)
                health_score = avg_completion / 100.0
                quality_factors.append(health_score)
            
            # Calculate overall quality
            overall_quality = sum(quality_factors) / len(quality_factors) if quality_factors else 0.5
            return min(1.0, max(0.0, overall_quality))
            
        except Exception as e:
            logger.warning(f"Failed to calculate quality score: {e}")
            return 0.5
    
    async def _validate_and_format_results(self, analysis_result: JiraAnalysisResult, schema) -> Dict[str, Any]:
        """Validate and format analysis results."""
        try:
            # Convert to dictionary for schema validation
            result_dict = {
                'analysis_date': analysis_result.analysis_date.isoformat(),
                'tasks_analyzed': analysis_result.tasks_analyzed,
                'employees_workload': {
                    emp: {
                        'employee': workload.employee,
                        'total_tasks': workload.total_tasks,
                        'completed_tasks': workload.completed_tasks,
                        'in_progress_tasks': workload.in_progress_tasks,
                        'blocked_tasks': workload.blocked_tasks,
                        'overdue_tasks': workload.overdue_tasks,
                        'total_story_points': workload.total_story_points,
                        'completed_story_points': workload.completed_story_points,
                        'completion_rate': workload.completion_rate,
                        'avg_task_duration': workload.avg_task_duration.total_seconds() if workload.avg_task_duration else None
                    }
                    for emp, workload in analysis_result.employees_workload.items()
                },
                'projects_progress': {
                    proj: {
                        'project': progress.project,
                        'total_tasks': progress.total_tasks,
                        'completed_tasks': progress.completed_tasks,
                        'in_progress_tasks': progress.in_progress_tasks,
                        'total_story_points': progress.total_story_points,
                        'completed_story_points': progress.completed_story_points,
                        'completion_percentage': progress.completion_percentage,
                        'active_employees': list(progress.active_employees),
                        'last_activity': progress.last_activity.isoformat() if progress.last_activity else None,
                        'blockers': progress.blockers
                    }
                    for proj, progress in analysis_result.projects_progress.items()
                },
                'insights': analysis_result.insights,
                'recommendations': analysis_result.recommendations,
                'quality_score': analysis_result.quality_score,
                'metadata': analysis_result.metadata
            }
            
            # Validate with schema
            validated_data = await schema.validate(result_dict)
            
            return validated_data
            
        except Exception as e:
            logger.warning(f"Schema validation failed: {e}")
            return result_dict  # Return unvalidated data on schema error
    
    async def _save_analysis_results(self, validated_data: Dict[str, Any]) -> None:
        """Save analysis results to memory store."""
        try:
            # Save with appropriate record type
            await self.memory_store.save_record(
                data=validated_data,
                record_type='jira_analysis',
                source='daily_jira_analyzer'
            )
            
            logger.info("JIRA analysis results saved to memory store")
            
        except Exception as e:
            logger.error(f"Failed to save analysis results: {e}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get agent health status."""
        try:
            llm_available = await self.llm_client.is_available()
            memory_available = self.memory_store.is_healthy()
            
            return {
                'agent_name': self.config.name,
                'status': 'healthy' if llm_available and memory_available else 'degraded',
                'llm_client': 'available' if llm_available else 'unavailable',
                'memory_store': 'healthy' if memory_available else 'unhealthy',
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'agent_name': self.config.name,
                'status': 'error',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
