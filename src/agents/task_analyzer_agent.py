"""
Task Analyzer Agent - Employee Monitoring System

Analyzes JIRA tasks to track employee performance, workload,
and generate insights for employee monitoring and reporting.
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from ..core.base_agent import BaseAgent, AgentConfig, AgentResult
from ..core.llm_client import LLMClient, analyze_jira_data
from ..core.json_memory_store import JSONMemoryStore
from ..core.quality_metrics import QualityMetrics
from ..core.config import get_employee_monitoring_config

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """JIRA task status for employee monitoring."""
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
class EmployeeTaskProgress:
    """Employee task progress information."""
    employee_name: str
    analysis_date: datetime
    
    # Task metrics
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    blocked_tasks: int
    todo_tasks: int
    overdue_tasks: int
    
    # Story points
    total_story_points: float
    completed_story_points: float
    in_progress_story_points: float
    
    # Performance metrics
    completion_rate: float
    productivity_score: float
    avg_task_duration: Optional[timedelta] = None
    
    # Activity tracking
    active_projects: Set[str] = field(default_factory=set)
    key_achievements: List[str] = field(default_factory=list)
    bottlenecks: List[str] = field(default_factory=list)
    
    # LLM insights
    llm_insights: str = ""
    performance_rating: float = 0.0  # 1-10 scale
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class DailyTaskAnalysisResult:
    """Complete daily task analysis result for employee monitoring."""
    analysis_date: datetime
    employees_progress: Dict[str, EmployeeTaskProgress]
    
    # Summary statistics
    total_employees: int
    total_tasks_analyzed: int
    avg_completion_rate: float
    top_performers: List[str]
    employees_needing_attention: List[str]
    
    # Insights and recommendations
    team_insights: List[str]
    recommendations: List[str]
    
    # Quality and metadata
    quality_score: float
    analysis_duration: timedelta
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskAnalyzerAgent(BaseAgent):
    """
    Task Analysis Agent for Employee Monitoring System.
    
    Analyzes JIRA tasks to track:
    - Individual employee performance and workload
    - Task completion rates and productivity
    - Project progress and bottlenecks
    - Achievement recognition and areas for improvement
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize Task Analyzer Agent.
        
        Args:
            config: Agent configuration
        """
        super().__init__(
            config or AgentConfig(
                name="TaskAnalyzerAgent",
                description="Analyzes JIRA tasks for employee performance monitoring",
                version="1.0.0"
            )
        )
        
        # Initialize components
        self.llm_client = LLMClient()
        self.memory_store = JSONMemoryStore()
        self.quality_metrics = QualityMetrics()
        
        # Load employee monitoring configuration
        self.emp_config = get_employee_monitoring_config()
        self.jira_config = self.emp_config.get('jira', {})
        self.reports_config = self.emp_config.get('reports', {})
        self.quality_config = self.emp_config.get('quality', {})
        self.employees_config = self.emp_config.get('employees', {})
        
        # Analysis parameters
        self.min_activity_threshold = self.employees_config.get('min_activity_threshold', 0.1)
        self.excluded_users = set(self.employees_config.get('excluded_users', []))
        self.quality_threshold = self.quality_config.get('threshold', 0.9)
        
        # Reports directory
        self.daily_reports_dir = Path(self.reports_config.get('daily_reports_dir', './reports/daily'))
        self.daily_reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("TaskAnalyzerAgent initialized for employee monitoring")
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute task analysis for employee monitoring.
        
        Args:
            input_data: Analysis input data containing JIRA tasks
            
        Returns:
            AgentResult with employee performance analysis
        """
        try:
            logger.info("Starting Task Analysis for Employee Monitoring")
            start_time = datetime.now()
            
            # Extract JIRA tasks from input
            jira_tasks_data = input_data.get('jira_tasks', [])
            
            if not jira_tasks_data:
                return AgentResult(
                    success=False,
                    message="No JIRA tasks found for analysis",
                    data={}
                )
            
            # Parse and validate tasks
            tasks = await self._parse_jira_tasks(jira_tasks_data)
            
            if not tasks:
                return AgentResult(
                    success=False,
                    message="No valid JIRA tasks parsed",
                    data={}
                )
            
            # Group tasks by employee
            employee_tasks = await self._group_tasks_by_employee(tasks)
            
            # Analyze each employee's performance
            employees_progress = {}
            for employee, emp_tasks in employee_tasks.items():
                if employee not in self.excluded_users:
                    progress = await self._analyze_employee_performance(employee, emp_tasks)
                    employees_progress[employee] = progress
            
            # Generate team-level insights
            analysis_result = await self._generate_team_analysis(employees_progress, tasks)
            
            # Add LLM insights if quality threshold requires
            if self.quality_threshold > 0.7:
                await self._add_llm_insights(analysis_result, employees_progress)
            
            # Calculate final quality score
            analysis_result.quality_score = await self._calculate_analysis_quality(analysis_result)
            
            # Save analysis results
            await self._save_daily_analysis(analysis_result)
            
            # Update memory store with employee state
            await self._update_employee_memory_store(employees_progress)
            
            # Calculate execution time
            execution_time = datetime.now() - start_time
            analysis_result.analysis_duration = execution_time
            
            logger.info(f"Task Analysis completed in {execution_time.total_seconds():.2f}s, "
                       f"analyzed {len(tasks)} tasks for {len(employees_progress)} employees")
            
            return AgentResult(
                success=True,
                message=f"Successfully analyzed task performance for {len(employees_progress)} employees",
                data=analysis_result,
                metadata={
                    'execution_time': execution_time.total_seconds(),
                    'tasks_analyzed': len(tasks),
                    'employees_analyzed': len(employees_progress),
                    'quality_score': analysis_result.quality_score,
                    'analysis_date': analysis_result.analysis_date.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Task Analysis failed: {e}")
            return AgentResult(
                success=False,
                message=f"Analysis failed: {str(e)}",
                data={},
                error=str(e)
            )
    
    async def _parse_jira_tasks(self, tasks_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse and validate JIRA task data."""
        valid_tasks = []
        
        for task_data in tasks_data:
            try:
                # Basic validation
                if not task_data.get('assignee') or task_data['assignee'] in self.excluded_users:
                    continue
                
                # Ensure required fields
                task = {
                    'id': task_data.get('id', ''),
                    'key': task_data.get('key', ''),
                    'summary': task_data.get('summary', ''),
                    'status': task_data.get('status', '').lower().replace(' ', '_'),
                    'priority': task_data.get('priority', 'medium').lower(),
                    'assignee': task_data['assignee'],
                    'project': task_data.get('project', ''),
                    'created': self._parse_datetime(task_data.get('created')),
                    'updated': self._parse_datetime(task_data.get('updated')),
                    'due_date': self._parse_datetime(task_data.get('due_date')),
                    'story_points': self._parse_story_points(task_data.get('story_points')),
                    'description': task_data.get('description', ''),
                    'labels': task_data.get('labels', [])
                }
                
                valid_tasks.append(task)
                
            except Exception as e:
                logger.warning(f"Failed to parse JIRA task {task_data.get('key', 'unknown')}: {e}")
                continue
        
        return valid_tasks
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string."""
        if not dt_str:
            return None
            
        try:
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
                import re
                match = re.search(r'(\d+(?:\.\d+)?)', sp_value)
                if match:
                    return float(match.group(1))
                
                try:
                    return float(sp_value)
                except ValueError:
                    pass
                    
        except Exception as e:
            logger.warning(f"Failed to parse story points '{sp_value}': {e}")
        
        return None
    
    async def _group_tasks_by_employee(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group tasks by employee."""
        employee_tasks = {}
        
        for task in tasks:
            employee = task['assignee']
            if employee not in employee_tasks:
                employee_tasks[employee] = []
            employee_tasks[employee].append(task)
        
        return employee_tasks
    
    async def _analyze_employee_performance(self, employee: str, tasks: List[Dict[str, Any]]) -> EmployeeTaskProgress:
        """Analyze individual employee performance."""
        analysis_date = datetime.now()
        
        # Basic task counts
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task['status'] in ['done', 'completed', 'closed'])
        in_progress_tasks = sum(1 for task in tasks if task['status'] in ['in_progress', 'progress'])
        blocked_tasks = sum(1 for task in tasks if task['status'] in ['blocked', 'blocked_issue'])
        todo_tasks = sum(1 for task in tasks if task['status'] in ['to_do', 'todo'])
        
        # Calculate overdue tasks
        now = datetime.now()
        overdue_tasks = sum(1 for task in tasks 
                           if task['due_date'] and task['due_date'] < now and task['status'] not in ['done', 'completed', 'closed'])
        
        # Calculate story points
        total_story_points = sum(task['story_points'] or 0 for task in tasks)
        completed_story_points = sum(task['story_points'] or 0 
                                   for task in tasks if task['status'] in ['done', 'completed', 'closed'])
        in_progress_story_points = sum(task['story_points'] or 0 
                                      for task in tasks if task['status'] in ['in_progress', 'progress'])
        
        # Calculate performance metrics
        completion_rate = completed_tasks / max(total_tasks, 1)
        productivity_score = min(1.0, (completed_story_points / max(total_story_points, 1)) * 10) if total_story_points > 0 else 0.0
        
        # Calculate average task duration
        completed_tasks_with_dates = [task for task in tasks 
                                    if task['status'] in ['done', 'completed', 'closed'] 
                                    and task['created'] and task['updated']]
        
        avg_task_duration = None
        if completed_tasks_with_dates:
            durations = [(task['updated'] - task['created']) for task in completed_tasks_with_dates]
            avg_task_duration = sum(durations, timedelta()) / len(durations)
        
        # Track active projects
        active_projects = {task['project'] for task in tasks if task['project']}
        
        # Identify achievements and bottlenecks
        key_achievements = await self._identify_key_achievements(employee, tasks)
        bottlenecks = await self._identify_bottlenecks(employee, tasks)
        
        # Initial performance rating
        performance_rating = await self._calculate_performance_rating(completion_rate, productivity_score, len(bottlenecks))
        
        return EmployeeTaskProgress(
            employee_name=employee,
            analysis_date=analysis_date,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            in_progress_tasks=in_progress_tasks,
            blocked_tasks=blocked_tasks,
            todo_tasks=todo_tasks,
            overdue_tasks=overdue_tasks,
            total_story_points=total_story_points,
            completed_story_points=completed_story_points,
            in_progress_story_points=in_progress_story_points,
            completion_rate=completion_rate,
            productivity_score=productivity_score,
            avg_task_duration=avg_task_duration,
            active_projects=active_projects,
            key_achievements=key_achievements,
            bottlenecks=bottlenecks,
            performance_rating=performance_rating
        )
    
    async def _identify_key_achievements(self, employee: str, tasks: List[Dict[str, Any]]) -> List[str]:
        """Identify key achievements for employee."""
        achievements = []
        
        completed_tasks = [task for task in tasks if task['status'] in ['done', 'completed', 'closed']]
        
        # High task completion
        if len(completed_tasks) >= 5:
            achievements.append(f"Completed {len(completed_tasks)} tasks")
        
        # High story points completed
        total_sp = sum(task['story_points'] or 0 for task in completed_tasks)
        if total_sp >= 20:
            achievements.append(f"Delivered {total_sp} story points")
        
        # Tasks completed ahead of deadline
        ahead_deadline = 0
        for task in completed_tasks:
            if task['due_date'] and task['updated'] and task['updated'] < task['due_date']:
                ahead_deadline += 1
        
        if ahead_deadline >= 2:
            achievements.append(f"Completed {ahead_deadline} tasks ahead of deadline")
        
        # Active in multiple projects
        projects = {task['project'] for task in tasks if task['project']}
        if len(projects) >= 2:
            achievements.append(f"Active across {len(projects)} projects")
        
        return achievements
    
    async def _identify_bottlenecks(self, employee: str, tasks: List[Dict[str, Any]]) -> List[str]:
        """Identify bottlenecks and challenges for employee."""
        bottlenecks = []
        
        # High stuck task count
        stuck_tasks = sum(1 for task in tasks if task['status'] in ['blocked', 'blocked_issue'])
        if stuck_tasks >= 2:
            bottlenecks.append(f"Has {stuck_tasks} blocked tasks")
        
        # High overdue count
        overdue_tasks = sum(1 for task in tasks 
                           if task['due_date'] and task['due_date'] < datetime.now() 
                           and task['status'] not in ['done', 'completed', 'closed'])
        if overdue_tasks >= 3:
            bottlenecks.append(f"Has {overdue_tasks} overdue tasks")
        
        # High work in progress
        wip_tasks = sum(1 for task in tasks if task['status'] in ['in_progress', 'progress'])
        if wip_tasks >= 7:
            bottlenecks.append(f"High workload with {wip_tasks} tasks in progress")
        
        # Long running tasks
        long_running = 0
        for task in tasks:
            if task['created'] and (datetime.now() - task['created']).days > 14:
                if task['status'] not in ['done', 'completed', 'closed']:
                    long_running += 1
        
        if long_running >= 2:
            bottlenecks.append(f"Has {long_running} tasks running for over 2 weeks")
        
        return bottlenecks
    
    async def _calculate_performance_rating(self, completion_rate: float, productivity_score: float, bottlenecks_count: int) -> float:
        """Calculate overall performance rating (1-10 scale)."""
        # Base rating from completion rate
        base_rating = completion_rate * 8  # Max 8 points from completion
        
        # Add productivity bonus
        productivity_bonus = productivity_score * 2  # Max 2 points from productivity
        
        # Subtract bottlenecks penalty
        bottlenecks_penalty = min(3, bottlenecks_count * 0.5)  # Max 3 points penalty
        
        # Calculate final rating
        final_rating = base_rating + productivity_bonus - bottlenecks_penalty
        
        # Ensure rating is within 1-10 range
        return max(1.0, min(10.0, final_rating))
    
    async def _generate_team_analysis(self, employees_progress: Dict[str, EmployeeTaskProgress], all_tasks: List[Dict[str, Any]]) -> DailyTaskAnalysisResult:
        """Generate team-level analysis."""
        analysis_date = datetime.now()
        
        # Summary statistics
        total_employees = len(employees_progress)
        total_tasks_analyzed = len(all_tasks)
        
        # Calculate average completion rate
        if employees_progress:
            avg_completion_rate = sum(progress.completion_rate for progress in employees_progress.values()) / total_employees
        else:
            avg_completion_rate = 0.0
        
        # Identify top performers (top 20% by performance rating)
        sorted_employees = sorted(employees_progress.items(), key=lambda x: x[1].performance_rating, reverse=True)
        top_20_percent_count = max(1, total_employees // 5)
        top_performers = [emp for emp, _ in sorted_employees[:top_20_percent_count]]
        
        # Identify employees needing attention (bottom 20% by performance rating)
        bottom_20_percent_count = max(1, total_employees // 5)
        employees_needing_attention = [emp for emp, _ in sorted_employees[-bottom_20_percent_count:]]
        
        # Generate team insights
        team_insights = await self._generate_team_insights(employees_progress)
        
        # Generate recommendations
        recommendations = await self._generate_team_recommendations(employees_progress, team_insights)
        
        return DailyTaskAnalysisResult(
            analysis_date=analysis_date,
            employees_progress=employees_progress,
            total_employees=total_employees,
            total_tasks_analyzed=total_tasks_analyzed,
            avg_completion_rate=avg_completion_rate,
            top_performers=top_performers,
            employees_needing_attention=employees_needing_attention,
            team_insights=team_insights,
            recommendations=recommendations,
            quality_score=0.0,  # Will be calculated later
            analysis_duration=timedelta()  # Will be set later
        )
    
    async def _generate_team_insights(self, employees_progress: Dict[str, EmployeeTaskProgress]) -> List[str]:
        """Generate team-level insights."""
        insights = []
        
        if not employees_progress:
            return insights
        
        # Overall performance insight
        avg_rating = sum(progress.performance_rating for progress in employees_progress.values()) / len(employees_progress)
        if avg_rating >= 8:
            insights.append("Team showing excellent performance overall")
        elif avg_rating >= 6:
            insights.append("Team performance is good with room for improvement")
        else:
            insights.append("Team needs performance improvement initiatives")
        
        # Workload distribution insight
        total_tasks = sum(progress.total_tasks for progress in employees_progress.values())
        avg_workload = total_tasks / len(employees_progress)
        overloaded = sum(1 for progress in employees_progress.values() if progress.total_tasks > avg_workload * 1.5)
        
        if overloaded > 0:
            insights.append(f"{overloaded} employees have significantly higher workload than average")
        
        # Bottleneck insight
        total_bottlenecks = sum(len(progress.bottlenecks) for progress in employees_progress.values())
        if total_bottlenecks > len(employees_progress):
            insights.append("Multiple team members experiencing bottlenecks")
        
        # Achievement insight
        total_achievements = sum(len(progress.key_achievements) for progress in employees_progress.values())
        if total_achievements >= len(employees_progress) * 2:
            insights.append("Team achieving significant milestones")
        
        return insights
    
    async def _generate_team_recommendations(self, employees_progress: Dict[str, EmployeeTaskProgress], insights: List[str]) -> List[str]:
        """Generate team-level recommendations."""
        recommendations = []
        
        if not employees_progress:
            return recommendations
        
        # Performance-based recommendations
        low_performers = [emp for emp, progress in employees_progress.items() if progress.performance_rating < 5]
        if low_performers:
            recommendations.append(f"Consider coaching and support for {len(low_performers)} underperforming employees")
        
        # Workload recommendations
        max_workload = max(progress.total_tasks for progress in employees_progress.values())
        min_workload = min(progress.total_tasks for progress in employees_progress.values())
        if max_workload > min_workload * 3:
            recommendations.append("Consider workload redistribution to balance team capacity")
        
        # Bottleneck recommendations
        employees_with_blockers = [emp for emp, progress in employees_progress.items() if progress.bottlenecks]
        if len(employees_with_blockers) > len(employees_progress) // 2:
            recommendations.append("Address systemic blockers affecting multiple team members")
        
        # Recognition recommendations
        top_performers = [emp for emp, progress in employees_progress.items() if progress.performance_rating >= 8]
        if top_performers:
            recommendations.append(f"Recognize and reward {len(top_performers)} top performing employees")
        
        # Process improvement recommendations
        overdue_tasks = sum(progress.overdue_tasks for progress in employees_progress.values())
        if overdue_tasks > 5:
            recommendations.append("Review and improve deadline management processes")
        
        return recommendations
    
    async def _add_llm_insights(self, analysis_result: DailyTaskAnalysisResult, employees_progress: Dict[str, EmployeeTaskProgress]) -> None:
        """Add LLM-powered insights to analysis results."""
        try:
            # Prepare data for LLM analysis
            employee_summary = self._prepare_employee_data_for_llm(employees_progress)
            
            # Get LLM insights
            llm_analysis = await analyze_jira_data(employee_summary)
            
            # Extract and distribute insights to employees
            if 'employee_insights' in llm_analysis:
                for employee_name, insights in llm_analysis['employee_insights'].items():
                    if employee_name in employees_progress:
                        employees_progress[employee_name].llm_insights = insights.get('analysis', '')
                        # Update performance rating based on LLM assessment
                        if 'performance_rating' in insights:
                            employees_progress[employee_name].performance_rating = insights['performance_rating']
            
            # Add team-level insights
            if 'team_insights' in llm_analysis:
                analysis_result.team_insights.extend(llm_analysis['team_insights'])
            
            if 'recommendations' in llm_analysis:
                analysis_result.recommendations.extend(llm_analysis['recommendations'])
            
        except Exception as e:
            logger.warning(f"Failed to add LLM insights: {e}")
    
    def _prepare_employee_data_for_llm(self, employees_progress: Dict[str, EmployeeTaskProgress]) -> str:
        """Prepare employee data summary for LLM analysis."""
        summary_parts = [
            "Employee Performance Analysis Summary",
            f"Analysis Date: {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "Employee Details:"
        ]
        
        for employee, progress in employees_progress.items():
            summary_parts.extend([
                f"\nEmployee: {employee}",
                f"  Performance Rating: {progress.performance_rating:.1f}/10",
                f"  Tasks: {progress.total_tasks} total, {progress.completed_tasks} completed ({progress.completion_rate:.1%})",
                f"  Story Points: {progress.completed_story_points}/{progress.total_story_points}",
                f"  Active Projects: {', '.join(progress.active_projects) if progress.active_projects else 'None'}",
                f"  Key Achievements: {', '.join(progress.key_achievements) if progress.key_achievements else 'None'}",
                f"  Bottlenecks: {', '.join(progress.bottlenecks) if progress.bottlenecks else 'None'}"
            ])
        
        return "\n".join(summary_parts)
    
    async def _calculate_analysis_quality(self, analysis_result: DailyTaskAnalysisResult) -> float:
        """Calculate analysis quality score."""
        try:
            quality_factors = []
            
            # Employee coverage score
            if analysis_result.total_employees > 0:
                coverage_score = min(1.0, analysis_result.total_employees / 5.0)  # Expect at least 5 employees
                quality_factors.append(coverage_score)
            
            # Data completeness score
            if analysis_result.employees_progress:
                employees_with_data = len([emp for emp, progress in analysis_result.employees_progress.items() 
                                         if progress.total_tasks > 0])
                completeness_score = employees_with_data / len(analysis_result.employees_progress)
                quality_factors.append(completeness_score)
            
            # Insight quality score
            insight_score = min(1.0, len(analysis_result.team_insights) / 3.0)  # Expect at least 3 insights
            quality_factors.append(insight_score)
            
            # Recommendation quality score
            recommendation_score = min(1.0, len(analysis_result.recommendations) / 2.0)  # Expect at least 2 recommendations
            quality_factors.append(recommendation_score)
            
            # Calculate overall quality
            overall_quality = sum(quality_factors) / len(quality_factors) if quality_factors else 0.5
            return min(1.0, max(0.0, overall_quality))
            
        except Exception as e:
            logger.warning(f"Failed to calculate quality score: {e}")
            return 0.5
    
    async def _save_daily_analysis(self, analysis_result: DailyTaskAnalysisResult) -> None:
        """Save analysis results to file system."""
        try:
            # Create date-specific directory
            date_str = analysis_result.analysis_date.strftime('%Y-%m-%d')
            daily_dir = self.daily_reports_dir / date_str
            daily_dir.mkdir(parents=True, exist_ok=True)
            
            # Prepare data for serialization
            analysis_data = {
                'analysis_date': analysis_result.analysis_date.isoformat(),
                'total_employees': analysis_result.total_employees,
                'total_tasks_analyzed': analysis_result.total_tasks_analyzed,
                'avg_completion_rate': analysis_result.avg_completion_rate,
                'top_performers': analysis_result.top_performers,
                'employees_needing_attention': analysis_result.employees_needing_attention,
                'team_insights': analysis_result.team_insights,
                'recommendations': analysis_result.recommendations,
                'quality_score': analysis_result.quality_score,
                'analysis_duration_seconds': analysis_result.analysis_duration.total_seconds(),
                'employees_progress': {},
                'metadata': analysis_result.metadata
            }
            
            # Serialize employee progress
            for employee, progress in analysis_result.employees_progress.items():
                analysis_data['employees_progress'][employee] = {
                    'employee_name': progress.employee_name,
                    'analysis_date': progress.analysis_date.isoformat(),
                    'total_tasks': progress.total_tasks,
                    'completed_tasks': progress.completed_tasks,
                    'in_progress_tasks': progress.in_progress_tasks,
                    'blocked_tasks': progress.blocked_tasks,
                    'todo_tasks': progress.todo_tasks,
                    'overdue_tasks': progress.overdue_tasks,
                    'total_story_points': progress.total_story_points,
                    'completed_story_points': progress.completed_story_points,
                    'in_progress_story_points': progress.in_progress_story_points,
                    'completion_rate': progress.completion_rate,
                    'productivity_score': progress.productivity_score,
                    'avg_task_duration_seconds': progress.avg_task_duration.total_seconds() if progress.avg_task_duration else None,
                    'active_projects': list(progress.active_projects),
                    'key_achievements': progress.key_achievements,
                    'bottlenecks': progress.bottlenecks,
                    'llm_insights': progress.llm_insights,
                    'performance_rating': progress.performance_rating,
                    'last_updated': progress.last_updated.isoformat()
                }
            
            # Save to JSON file
            report_file = daily_dir / f"task-analysis_{date_str}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Task analysis saved to {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save daily analysis: {e}")
    
    async def _update_employee_memory_store(self, employees_progress: Dict[str, EmployeeTaskProgress]) -> None:
        """Update memory store with employee state."""
        try:
            for employee, progress in employees_progress.items():
                # Save employee state to memory store
                employee_data = {
                    'employee_name': progress.employee_name,
                    'analysis_date': progress.analysis_date.isoformat(),
                    'performance_metrics': {
                        'total_tasks': progress.total_tasks,
                        'completed_tasks': progress.completed_tasks,
                        'completion_rate': progress.completion_rate,
                        'productivity_score': progress.productivity_score,
                        'performance_rating': progress.performance_rating
                    },
                    'activity_tracking': {
                        'active_projects': list(progress.active_projects),
                        'key_achievements': progress.key_achievements,
                        'bottlenecks': progress.bottlenecks
                    },
                    'story_points': {
                        'total': progress.total_story_points,
                        'completed': progress.completed_story_points,
                        'in_progress': progress.in_progress_story_points
                    },
                    'llm_insights': progress.llm_insights,
                    'last_updated': progress.last_updated.isoformat()
                }
                
                await self.memory_store.save_record(
                    data=employee_data,
                    record_type='employee_task_state',
                    record_id=employee,
                    source='task_analyzer_agent'
                )
            
            logger.info(f"Updated memory store with task state for {len(employees_progress)} employees")
            
        except Exception as e:
            logger.error(f"Failed to update employee memory store: {e}")
    
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
                'config_loaded': bool(self.emp_config),
                'reports_directory': str(self.daily_reports_dir),
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
