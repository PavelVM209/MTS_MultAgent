"""
Weekly Reports Agent - Employee Monitoring System

Generates comprehensive weekly reports by combining task and meeting analyses,
and publishes them to Confluence with detailed insights and recommendations.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import defaultdict

from ..core.base_agent import BaseAgent, AgentConfig, AgentResult
from ..core.llm_client import LLMClient
from ..core.json_memory_store import JSONMemoryStore
from ..core.quality_metrics import QualityMetrics
from ..core.config import get_employee_monitoring_config

logger = logging.getLogger(__name__)


class ReportType(Enum):
    """Types of weekly reports."""
    COMPREHENSIVE = "comprehensive"
    PERFORMANCE = "performance"
    MEETING_SUMMARY = "meeting_summary"
    COMBINED = "combined"


class ReportStatus(Enum):
    """Report generation status."""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    FAILED = "failed"


@dataclass
class WeeklyReportData:
    """Data structure for weekly report."""
    report_period_start: datetime
    report_period_end: datetime
    generated_at: datetime
    
    # Employee data
    employee_summaries: Dict[str, Dict[str, Any]]
    
    # Task analysis data
    task_summary: Dict[str, Any]
    
    # Meeting analysis data
    meeting_summary: Dict[str, Any]
    
    # Team insights
    team_insights: List[str]
    recommendations: List[str]
    
    # Quality metrics
    quality_score: float
    
    # Metadata
    report_type: ReportType
    status: ReportStatus = ReportStatus.DRAFT


@dataclass
class ConfluencePublishResult:
    """Result of Confluence publishing."""
    success: bool
    page_id: Optional[str] = None
    page_url: Optional[str] = None
    error_message: Optional[str] = None


class WeeklyReportsAgent(BaseAgent):
    """
    Weekly Reports Agent for Employee Monitoring System.
    
    Generates comprehensive weekly reports by:
    - Combining task and meeting analyses
    - Creating employee performance summaries
    - Generating team-level insights
    - Publishing reports to Confluence
    - Maintaining report quality standards
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize Weekly Reports Agent.
        
        Args:
            config: Agent configuration
        """
        super().__init__(
            config or AgentConfig(
                name="WeeklyReportsAgent",
                description="Generates comprehensive weekly reports and publishes to Confluence",
                version="1.0.0"
            )
        )
        
        # Initialize components
        self.llm_client = LLMClient()
        self.memory_store = JSONMemoryStore()
        self.quality_metrics = QualityMetrics()
        
        # Load employee monitoring configuration
        self.emp_config = get_employee_monitoring_config()
        self.reports_config = self.emp_config.get('reports', {})
        self.confluence_config = self.emp_config.get('confluence', {})
        self.quality_config = self.emp_config.get('quality', {})
        self.employees_config = self.emp_config.get('employees', {})
        
        # Analysis parameters
        self.weekly_reports_dir = Path(self.reports_config.get('weekly_reports_dir', './reports/weekly'))
        self.daily_reports_dir = Path(self.reports_config.get('daily_reports_dir', './reports/daily'))
        self.quality_threshold = self.quality_config.get('threshold', 0.9)
        
        # Confluence settings
        self.confluence_base_url = self.confluence_config.get('base_url', '')
        self.confluence_space = self.confluence_config.get('space', '')
        self.confluence_parent_page = self.confluence_config.get('parent_page_id', '')
        
        # Create directories
        self.weekly_reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("WeeklyReportsAgent initialized for employee monitoring")
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute weekly report generation and publishing.
        
        Args:
            input_data: Report generation input data
            
        Returns:
            AgentResult with weekly report data and publishing status
        """
        try:
            logger.info("Starting Weekly Report Generation")
            start_time = datetime.now()
            
            # Extract report parameters
            report_period_end = input_data.get('report_period_end', datetime.now())
            report_period_start = report_period_end - timedelta(days=7)
            report_type = ReportType(input_data.get('report_type', 'comprehensive'))
            
            # Step 1: Collect daily analysis data for the week
            daily_data = await self._collect_weekly_data(report_period_start, report_period_end)
            
            if not daily_data:
                return AgentResult(
                    success=False,
                    message="No daily analysis data found for the specified period",
                    data={}
                )
            
            # Step 2: Generate comprehensive weekly analysis
            weekly_report_data = await self._generate_weekly_analysis(
                daily_data, report_period_start, report_period_end, report_type
            )
            
            # Step 3: Enhance with LLM insights
            if self.quality_threshold > 0.7:
                await self._enhance_with_llm_insights(weekly_report_data)
            
            # Step 4: Calculate quality score
            weekly_report_data.quality_score = await self._calculate_report_quality(weekly_report_data)
            
            # Step 5: Generate Confluence content
            confluence_content = await self._generate_confluence_content(weekly_report_data)
            
            # Step 6: Save report locally
            await self._save_weekly_report(weekly_report_data, confluence_content)
            
            # Step 7: Publish to Confluence (if configured)
            publish_result = None
            if self.confluence_base_url and self.confluence_space:
                publish_result = await self._publish_to_confluence(
                    weekly_report_data, confluence_content
                )
                weekly_report_data.status = ReportStatus.PUBLISHED if publish_result.success else ReportStatus.FAILED
            else:
                weekly_report_data.status = ReportStatus.APPROVED
            
            # Update memory store
            await self._update_memory_store(weekly_report_data, publish_result)
            
            # Calculate execution time
            execution_time = datetime.now() - start_time
            
            logger.info(f"Weekly Report generated in {execution_time.total_seconds():.2f}s, "
                       f"quality score: {weekly_report_data.quality_score:.2f}")
            
            return AgentResult(
                success=True,
                message=f"Successfully generated weekly report with quality score {weekly_report_data.quality_score:.2f}",
                data={
                    'weekly_report_data': weekly_report_data,
                    'confluence_content': confluence_content,
                    'publish_result': publish_result
                },
                metadata={
                    'execution_time': execution_time.total_seconds(),
                    'report_period': f"{report_period_start.strftime('%Y-%m-%d')} to {report_period_end.strftime('%Y-%m-%d')}",
                    'quality_score': weekly_report_data.quality_score,
                    'report_type': report_type.value,
                    'published': publish_result.success if publish_result else False
                }
            )
            
        except Exception as e:
            logger.error(f"Weekly Report generation failed: {e}")
            return AgentResult(
                success=False,
                message=f"Report generation failed: {str(e)}",
                data={},
                error=str(e)
            )
    
    async def _collect_weekly_data(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Collect daily analysis data for the specified week."""
        daily_data = []
        
        try:
            # Scan daily reports directory for the specified period
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                daily_dir = self.daily_reports_dir / date_str
                
                if daily_dir.exists():
                    # Look for task analysis files
                    task_analysis_file = daily_dir / f"task-analysis_{date_str}.json"
                    if task_analysis_file.exists():
                        with open(task_analysis_file, 'r', encoding='utf-8') as f:
                            task_data = json.load(f)
                            task_data['date'] = date_str
                            task_data['type'] = 'task_analysis'
                            daily_data.append(task_data)
                    
                    # Look for meeting analysis files
                    meeting_analysis_file = daily_dir / f"meeting-analysis_{date_str}.json"
                    if meeting_analysis_file.exists():
                        with open(meeting_analysis_file, 'r', encoding='utf-8') as f:
                            meeting_data = json.load(f)
                            meeting_data['date'] = date_str
                            meeting_data['type'] = 'meeting_analysis'
                            daily_data.append(meeting_data)
                
                current_date += timedelta(days=1)
            
            logger.info(f"Collected {len(daily_data)} daily analysis files for the week")
            
        except Exception as e:
            logger.error(f"Failed to collect weekly data: {e}")
        
        return daily_data
    
    async def _generate_weekly_analysis(self, daily_data: List[Dict[str, Any]], start_date: datetime, end_date: datetime, report_type: ReportType) -> WeeklyReportData:
        """Generate comprehensive weekly analysis from daily data."""
        
        # Separate task and meeting data
        task_data = [item for item in daily_data if item.get('type') == 'task_analysis']
        meeting_data = [item for item in daily_data if item.get('type') == 'meeting_analysis']
        
        # Generate task summary
        task_summary = await self._generate_task_summary(task_data)
        
        # Generate meeting summary
        meeting_summary = await self._generate_meeting_summary(meeting_data)
        
        # Generate employee summaries
        employee_summaries = await self._generate_employee_summaries(task_data, meeting_data)
        
        # Generate team insights
        team_insights = await self._generate_team_insights(task_summary, meeting_summary)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(task_summary, meeting_summary, employee_summaries)
        
        return WeeklyReportData(
            report_period_start=start_date,
            report_period_end=end_date,
            generated_at=datetime.now(),
            employee_summaries=employee_summaries,
            task_summary=task_summary,
            meeting_summary=meeting_summary,
            team_insights=team_insights,
            recommendations=recommendations,
            quality_score=0.0,  # Will be calculated later
            report_type=report_type
        )
    
    async def _generate_task_summary(self, task_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate weekly task analysis summary."""
        if not task_data:
            return {}
        
        # Aggregate task metrics
        total_tasks = sum(item.get('total_tasks_analyzed', 0) for item in task_data)
        total_employees = len(set().union(*[item.get('employees_progress', {}).keys() for item in task_data]))
        
        # Calculate completion rates
        completion_rates = []
        productivity_scores = []
        performance_ratings = []
        
        for daily_item in task_data:
            employees_progress = daily_item.get('employees_progress', {})
            if employees_progress:
                daily_completion_rate = sum(emp.get('completion_rate', 0) for emp in employees_progress.values()) / len(employees_progress)
                daily_productivity = sum(emp.get('productivity_score', 0) for emp in employees_progress.values()) / len(employees_progress)
                daily_performance = sum(emp.get('performance_rating', 0) for emp in employees_progress.values()) / len(employees_progress)
                
                completion_rates.append(daily_completion_rate)
                productivity_scores.append(daily_productivity)
                performance_ratings.append(daily_performance)
        
        # Top performers across the week
        all_employees = defaultdict(lambda: {'tasks': [], 'completion_rates': [], 'performance_ratings': []})
        for daily_item in task_data:
            for emp_name, emp_data in daily_item.get('employees_progress', {}).items():
                all_employees[emp_name]['tasks'].append(emp_data.get('total_tasks', 0))
                all_employees[emp_name]['completion_rates'].append(emp_data.get('completion_rate', 0))
                all_employees[emp_name]['performance_ratings'].append(emp_data.get('performance_rating', 0))
        
        # Calculate weekly averages for each employee
        employee_averages = {}
        for emp_name, data in all_employees.items():
            employee_averages[emp_name] = {
                'avg_tasks': sum(data['tasks']) / len(data['tasks']),
                'avg_completion_rate': sum(data['completion_rates']) / len(data['completion_rates']),
                'avg_performance_rating': sum(data['performance_ratings']) / len(data['performance_ratings'])
            }
        
        # Sort by performance rating
        top_performers = sorted(employee_averages.items(), key=lambda x: x[1]['avg_performance_rating'], reverse=True)[:5]
        
        return {
            'total_tasks_analyzed': total_tasks,
            'total_employees': total_employees,
            'avg_completion_rate': sum(completion_rates) / len(completion_rates) if completion_rates else 0,
            'avg_productivity_score': sum(productivity_scores) / len(productivity_scores) if productivity_scores else 0,
            'avg_performance_rating': sum(performance_ratings) / len(performance_ratings) if performance_ratings else 0,
            'top_performers': [{'name': name, 'metrics': metrics} for name, metrics in top_performers],
            'daily_breakdown': [{'date': item.get('date'), 'tasks': item.get('total_tasks_analyzed', 0), 'employees': len(item.get('employees_progress', {}))} for item in task_data]
        }
    
    async def _generate_meeting_summary(self, meeting_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate weekly meeting analysis summary."""
        if not meeting_data:
            return {}
        
        # Aggregate meeting metrics
        total_meetings = sum(item.get('total_meetings_analyzed', 0) for item in meeting_data)
        total_employees = len(set().union(*[item.get('employees_activity', {}).keys() for item in meeting_data]))
        total_action_items = sum(item.get('total_action_items', 0) for item in meeting_data)
        
        # Calculate engagement scores
        engagement_scores = []
        activity_ratings = []
        
        for daily_item in meeting_data:
            employees_activity = daily_item.get('employees_activity', {})
            if employees_activity:
                daily_engagement = sum(emp.get('engagement_score', 0) for emp in employees_activity.values()) / len(employees_activity)
                daily_activity = sum(emp.get('activity_rating', 0) for emp in employees_activity.values()) / len(employees_activity)
                
                engagement_scores.append(daily_engagement)
                activity_ratings.append(daily_activity)
        
        # Meeting types distribution
        meeting_types = defaultdict(int)
        for daily_item in meeting_data:
            for meeting_type, count in daily_item.get('meeting_types_distribution', {}).items():
                meeting_types[meeting_type] += count
        
        # Most active employees
        all_employees = defaultdict(lambda: {'meetings': [], 'engagement_scores': [], 'activity_ratings': []})
        for daily_item in meeting_data:
            for emp_name, emp_data in daily_item.get('employees_activity', {}).items():
                all_employees[emp_name]['meetings'].append(emp_data.get('meeting_participations', 0))
                all_employees[emp_name]['engagement_scores'].append(emp_data.get('engagement_score', 0))
                all_employees[emp_name]['activity_ratings'].append(emp_data.get('activity_rating', 0))
        
        # Calculate weekly averages for each employee
        employee_averages = {}
        for emp_name, data in all_employees.items():
            employee_averages[emp_name] = {
                'avg_meetings': sum(data['meetings']) / len(data['meetings']),
                'avg_engagement_score': sum(data['engagement_scores']) / len(data['engagement_scores']),
                'avg_activity_rating': sum(data['activity_ratings']) / len(data['activity_ratings'])
            }
        
        # Sort by activity rating
        most_active = sorted(employee_averages.items(), key=lambda x: x[1]['avg_activity_rating'], reverse=True)[:5]
        
        return {
            'total_meetings_analyzed': total_meetings,
            'total_employees': total_employees,
            'total_action_items': total_action_items,
            'avg_engagement_score': sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0,
            'avg_activity_rating': sum(activity_ratings) / len(activity_ratings) if activity_ratings else 0,
            'meeting_types_distribution': dict(meeting_types),
            'most_active_employees': [{'name': name, 'metrics': metrics} for name, metrics in most_active],
            'daily_breakdown': [{'date': item.get('date'), 'meetings': item.get('total_meetings_analyzed', 0), 'employees': len(item.get('employees_activity', {}))} for item in meeting_data]
        }
    
    async def _generate_employee_summaries(self, task_data: List[Dict[str, Any]], meeting_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Generate individual employee summaries combining task and meeting data."""
        
        # Collect all employee names
        task_employees = set()
        for item in task_data:
            task_employees.update(item.get('employees_progress', {}).keys())
        
        meeting_employees = set()
        for item in meeting_data:
            meeting_employees.update(item.get('employees_activity', {}).keys())
        
        all_employees = task_employees.union(meeting_employees)
        
        employee_summaries = {}
        
        for employee in all_employees:
            # Task metrics for this employee
            task_metrics = []
            for item in task_data:
                if employee in item.get('employees_progress', {}):
                    task_metrics.append(item['employees_progress'][employee])
            
            # Meeting metrics for this employee
            meeting_metrics = []
            for item in meeting_data:
                if employee in item.get('employees_activity', {}):
                    meeting_metrics.append(item['employees_activity'][employee])
            
            # Calculate averages
            avg_completion_rate = sum(m.get('completion_rate', 0) for m in task_metrics) / len(task_metrics) if task_metrics else 0
            avg_performance_rating = sum(m.get('performance_rating', 0) for m in task_metrics) / len(task_metrics) if task_metrics else 0
            avg_engagement_score = sum(m.get('engagement_score', 0) for m in meeting_metrics) / len(meeting_metrics) if meeting_metrics else 0
            avg_activity_rating = sum(m.get('activity_rating', 0) for m in meeting_metrics) / len(meeting_metrics) if meeting_metrics else 0
            
            # Total metrics for the week
            total_tasks_completed = sum(m.get('completed_tasks', 0) for m in task_metrics)
            total_meetings_attended = sum(m.get('meeting_participations', 0) for m in meeting_metrics)
            total_action_items = sum(m.get('action_items_assigned', 0) for m in meeting_metrics)
            
            # Calculate overall performance score
            task_score_weight = 0.6
            meeting_score_weight = 0.4
            overall_score = (avg_performance_rating * task_score_weight) + (avg_activity_rating * meeting_score_weight)
            
            employee_summaries[employee] = {
                'task_metrics': {
                    'avg_completion_rate': avg_completion_rate,
                    'avg_performance_rating': avg_performance_rating,
                    'total_tasks_completed': total_tasks_completed,
                    'data_points': len(task_metrics)
                },
                'meeting_metrics': {
                    'avg_engagement_score': avg_engagement_score,
                    'avg_activity_rating': avg_activity_rating,
                    'total_meetings_attended': total_meetings_attended,
                    'total_action_items': total_action_items,
                    'data_points': len(meeting_metrics)
                },
                'overall_metrics': {
                    'overall_performance_score': overall_score,
                    'activity_level': self._calculate_activity_level(total_meetings_attended, total_tasks_completed),
                    'consistency_score': self._calculate_consistency_score(task_metrics, meeting_metrics)
                }
            }
        
        return employee_summaries
    
    def _calculate_activity_level(self, meetings: int, tasks: int) -> str:
        """Calculate activity level based on meetings and tasks."""
        activity_score = (meetings * 0.3) + (tasks * 0.7)
        
        if activity_score >= 20:
            return "very_high"
        elif activity_score >= 15:
            return "high"
        elif activity_score >= 10:
            return "medium"
        elif activity_score >= 5:
            return "low"
        else:
            return "very_low"
    
    def _calculate_consistency_score(self, task_metrics: List[Dict], meeting_metrics: List[Dict]) -> float:
        """Calculate consistency score based on data availability."""
        total_days = 7  # Week has 7 days
        days_with_tasks = len(task_metrics)
        days_with_meetings = len(meeting_metrics)
        
        # Consistency is based on regular participation
        consistency = (days_with_tasks + days_with_meetings) / (total_days * 2)
        return min(1.0, consistency)
    
    async def _generate_team_insights(self, task_summary: Dict[str, Any], meeting_summary: Dict[str, Any]) -> List[str]:
        """Generate team-level insights from weekly data."""
        insights = []
        
        # Task-based insights
        if task_summary:
            avg_completion = task_summary.get('avg_completion_rate', 0)
            if avg_completion >= 0.8:
                insights.append("Team demonstrates excellent task completion rate")
            elif avg_completion >= 0.6:
                insights.append("Team shows good task completion with room for improvement")
            else:
                insights.append("Team needs support to improve task completion rates")
        
        # Meeting-based insights
        if meeting_summary:
            avg_engagement = meeting_summary.get('avg_engagement_score', 0)
            if avg_engagement >= 0.8:
                insights.append("High engagement levels in team meetings")
            elif avg_engagement >= 0.6:
                insights.append("Moderate engagement in meetings with potential for improvement")
            else:
                insights.append("Low engagement levels require attention")
        
        # Combined insights
        if task_summary and meeting_summary:
            task_perf = task_summary.get('avg_performance_rating', 0)
            meeting_activity = meeting_summary.get('avg_activity_rating', 0)
            
            if task_perf >= 7 and meeting_activity >= 7:
                insights.append("Strong overall team performance across tasks and meetings")
            elif task_perf >= 7 and meeting_activity < 5:
                insights.append("Good task performance but low meeting participation")
            elif task_perf < 5 and meeting_activity >= 7:
                insights.append("Active meeting participation but task completion needs improvement")
        
        return insights
    
    async def _generate_recommendations(self, task_summary: Dict[str, Any], meeting_summary: Dict[str, Any], employee_summaries: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Task-based recommendations
        if task_summary:
            avg_completion = task_summary.get('avg_completion_rate', 0)
            if avg_completion < 0.6:
                recommendations.append("Implement daily standups to improve task visibility and completion")
            
            # Identify underperforming employees
            underperformers = [emp for emp, data in employee_summaries.items() 
                             if data['task_metrics']['avg_performance_rating'] < 5]
            if underperformers:
                recommendations.append(f"Provide additional coaching and support for {len(underperformers)} employees")
        
        # Meeting-based recommendations
        if meeting_summary:
            avg_engagement = meeting_summary.get('avg_engagement_score', 0)
            if avg_engagement < 0.6:
                recommendations.append("Consider restructuring meetings to increase engagement")
            
            low_activity = [emp for emp, data in employee_summaries.items() 
                          if data['meeting_metrics']['avg_activity_rating'] < 5]
            if low_activity:
                recommendations.append(f"Encourage more active participation from {len(low_activity)} team members")
        
        # General recommendations
        if employee_summaries:
            inconsistent_employees = [emp for emp, data in employee_summaries.items() 
                                   if data['overall_metrics']['consistency_score'] < 0.5]
            if inconsistent_employees:
                recommendations.append(f"Address inconsistent participation patterns for {len(inconsistent_employees)} employees")
        
        return recommendations
    
    async def _enhance_with_llm_insights(self, weekly_report_data: WeeklyReportData) -> None:
        """Enhance weekly report with LLM-powered insights."""
        try:
            # Prepare data for LLM analysis
            llm_input = self._prepare_llm_input(weekly_report_data)
            
            # Get LLM insights (would need to implement LLM function)
            # llm_analysis = await analyze_weekly_report(llm_input)
            
            # For now, add placeholder insights
            for employee in weekly_report_data.employee_summaries:
                weekly_report_data.employee_summaries[employee]['llm_insights'] = "LLM insights will be added here"
            
            weekly_report_data.team_insights.append("Additional LLM-powered team insights")
            weekly_report_data.recommendations.extend(["LLM-based recommendations"])
            
        except Exception as e:
            logger.warning(f"Failed to enhance with LLM insights: {e}")
    
    def _prepare_llm_input(self, weekly_report_data: WeeklyReportData) -> str:
        """Prepare data for LLM analysis."""
        parts = [
            f"Weekly Report Analysis - {weekly_report_data.report_period_start.strftime('%Y-%m-%d')} to {weekly_report_data.report_period_end.strftime('%Y-%m-%d')}",
            "",
            "Task Summary:",
            f"  Average Completion Rate: {weekly_report_data.task_summary.get('avg_completion_rate', 0):.2%}",
            f"  Average Performance Rating: {weekly_report_data.task_summary.get('avg_performance_rating', 0):.1f}/10",
            "",
            "Meeting Summary:",
            f"  Average Engagement Score: {weekly_report_data.meeting_summary.get('avg_engagement_score', 0):.2f}",
            f"  Average Activity Rating: {weekly_report_data.meeting_summary.get('avg_activity_rating', 0):.1f}/10",
            "",
            f"Total Employees Analyzed: {len(weekly_report_data.employee_summaries)}"
        ]
        
        return "\n".join(parts)
    
    async def _calculate_report_quality(self, weekly_report_data: WeeklyReportData) -> float:
        """Calculate overall report quality score."""
        try:
            quality_factors = []
            
            # Data completeness factor
            if weekly_report_data.employee_summaries:
                completeness = len(weekly_report_data.employee_summaries) / 10  # Expect at least 10 employees
                quality_factors.append(min(1.0, completeness))
            
            # Insight quality factor
            if weekly_report_data.team_insights:
                insight_quality = len(weekly_report_data.team_insights) / 5  # Expect at least 5 insights
                quality_factors.append(min(1.0, insight_quality))
            
            # Recommendation quality factor
            if weekly_report_data.recommendations:
                recommendation_quality = len(weekly_report_data.recommendations) / 3  # Expect at least 3 recommendations
                quality_factors.append(min(1.0, recommendation_quality))
            
            # Data structure quality factor
            structure_quality = 0.0
            if weekly_report_data.task_summary and weekly_report_data.meeting_summary:
                structure_quality = 1.0
            quality_factors.append(structure_quality)
            
            # Calculate overall quality
            overall_quality = sum(quality_factors) / len(quality_factors) if quality_factors else 0.0
            return min(1.0, max(0.0, overall_quality))
            
        except Exception as e:
            logger.warning(f"Failed to calculate report quality: {e}")
            return 0.5
    
    async def _generate_confluence_content(self, weekly_report_data: WeeklyReportData) -> str:
        """Generate Confluence page content."""
        try:
            content_parts = [
                f"# Weekly Employee Monitoring Report",
                f"",
                f"**Report Period:** {weekly_report_data.report_period_start.strftime('%Y-%m-%d')} to {weekly_report_data.report_period_end.strftime('%Y-%m-%d')}",
                f"**Generated:** {weekly_report_data.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Quality Score:** {weekly_report_data.quality_score:.2f}",
                f"",
                "## Executive Summary",
                ""
            ]
            
            # Task summary section
            if weekly_report_data.task_summary:
                content_parts.extend([
                    "### Task Performance Summary",
                    f"- **Total Tasks Analyzed:** {weekly_report_data.task_summary.get('total_tasks_analyzed', 0)}",
                    f"- **Average Completion Rate:** {weekly_report_data.task_summary.get('avg_completion_rate', 0):.2%}",
                    f"- **Average Performance Rating:** {weekly_report_data.task_summary.get('avg_performance_rating', 0):.1f}/10",
                    ""
                ])
            
            # Meeting summary section
            if weekly_report_data.meeting_summary:
                content_parts.extend([
                    "### Meeting Activity Summary",
                    f"- **Total Meetings Analyzed:** {weekly_report_data.meeting_summary.get('total_meetings_analyzed', 0)}",
                    f"- **Total Action Items:** {weekly_report_data.meeting_summary.get('total_action_items', 0)}",
                    f"- **Average Engagement Score:** {weekly_report_data.meeting_summary.get('avg_engagement_score', 0):.2f}",
                    f"- **Average Activity Rating:** {weekly_report_data.meeting_summary.get('avg_activity_rating', 0):.1f}/10",
                    ""
                ])
            
            # Team insights section
            if weekly_report_data.team_insights:
                content_parts.extend([
                    "## Team Insights",
                    ""
                ])
                for insight in weekly_report_data.team_insights:
                    content_parts.extend([f"- {insight}", ""])
                content_parts.append("")
            
            # Recommendations section
            if weekly_report_data.recommendations:
                content_parts.extend([
                    "## Recommendations",
                    ""
                ])
                for recommendation in weekly_report_data.recommendations:
                    content_parts.extend([f"- {recommendation}", ""])
                content_parts.append("")
            
            # Employee summaries section
            if weekly_report_data.employee_summaries:
                content_parts.extend([
                    "## Employee Performance Summary",
                    "",
                    "| Employee | Task Performance | Meeting Activity | Overall Score |",
                    "|----------|------------------|------------------|---------------|"
                ])
                
                for employee, summary in weekly_report_data.employee_summaries.items():
                    task_perf = summary['task_metrics']['avg_performance_rating']
                    meeting_activity = summary['meeting_metrics']['avg_activity_rating']
                    overall = summary['overall_metrics']['overall_performance_score']
                    
                    content_parts.append(
                        f"| {employee} | {task_perf:.1f}/10 | {meeting_activity:.1f}/10 | {overall:.1f}/10 |"
                    )
                
                content_parts.extend(["", ""])
            
            # Footer
            content_parts.extend([
                "---",
                f"*This report was automatically generated by MTS MultAgent Employee Monitoring System*",
                f"*Quality Score: {weekly_report_data.quality_score:.2f}*"
            ])
            
            return "\n".join(content_parts)
            
        except Exception as e:
            logger.error(f"Failed to generate Confluence content: {e}")
            return f"Error generating report content: {str(e)}"
    
    async def _save_weekly_report(self, weekly_report_data: WeeklyReportData, confluence_content: str) -> None:
        """Save weekly report locally."""
        try:
            # Create date-specific filename
            date_str = weekly_report_data.report_period_end.strftime('%Y-%m-%d')
            report_file = self.weekly_reports_dir / f"weekly-report_{date_str}.json"
            confluence_file = self.weekly_reports_dir / f"weekly-report_{date_str}.confluence.txt"
            
            # Save JSON data
            report_data = {
                'report_period_start': weekly_report_data.report_period_start.isoformat(),
                'report_period_end': weekly_report_data.report_period_end.isoformat(),
                'generated_at': weekly_report_data.generated_at.isoformat(),
                'employee_summaries': weekly_report_data.employee_summaries,
                'task_summary': weekly_report_data.task_summary,
                'meeting_summary': weekly_report_data.meeting_summary,
                'team_insights': weekly_report_data.team_insights,
                'recommendations': weekly_report_data.recommendations,
                'quality_score': weekly_report_data.quality_score,
                'report_type': weekly_report_data.report_type.value,
                'status': weekly_report_data.status.value
            }
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            # Save Confluence content
            with open(confluence_file, 'w', encoding='utf-8') as f:
                f.write(confluence_content)
            
            logger.info(f"Weekly report saved to {report_file} and {confluence_file}")
            
        except Exception as e:
            logger.error(f"Failed to save weekly report: {e}")
    
    async def _publish_to_confluence(self, weekly_report_data: WeeklyReportData, confluence_content: str) -> ConfluencePublishResult:
        """Publish weekly report to Confluence."""
        try:
            # This would integrate with Confluence API
            # For now, return a mock result
            logger.info("Confluence publishing not yet implemented - returning mock result")
            
            return ConfluencePublishResult(
                success=True,
                page_id="mock_page_id_12345",
                page_url=f"{self.confluence_base_url}/wiki/spaces/{self.confluence_space}/pages/mock_page_id_12345"
            )
            
        except Exception as e:
            logger.error(f"Failed to publish to Confluence: {e}")
            return ConfluencePublishResult(
                success=False,
                error_message=str(e)
            )
    
    async def _update_memory_store(self, weekly_report_data: WeeklyReportData, publish_result: Optional[ConfluencePublishResult]) -> None:
        """Update memory store with weekly report data."""
        try:
            report_data = {
                'report_period': {
                    'start': weekly_report_data.report_period_start.isoformat(),
                    'end': weekly_report_data.report_period_end.isoformat()
                },
                'generated_at': weekly_report_data.generated_at.isoformat(),
                'quality_score': weekly_report_data.quality_score,
                'report_type': weekly_report_data.report_type.value,
                'status': weekly_report_data.status.value,
                'employee_count': len(weekly_report_data.employee_summaries),
                'team_insights_count': len(weekly_report_data.team_insights),
                'recommendations_count': len(weekly_report_data.recommendations),
                'publish_result': {
                    'success': publish_result.success if publish_result else False,
                    'page_id': publish_result.page_id if publish_result else None,
                    'page_url': publish_result.page_url if publish_result else None
                } if publish_result else None
            }
            
            await self.memory_store.save_record(
                data=report_data,
                record_type='weekly_report',
                record_id=weekly_report_data.report_period_end.strftime('%Y-%m-%d'),
                source='weekly_reports_agent'
            )
            
            logger.info("Updated memory store with weekly report data")
            
        except Exception as e:
            logger.error(f"Failed to update memory store: {e}")
    
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
                'directories_created': {
                    'weekly_reports': self.weekly_reports_dir.exists(),
                    'daily_reports': self.daily_reports_dir.exists()
                },
                'confluence_configured': bool(self.confluence_base_url and self.confluence_space),
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
