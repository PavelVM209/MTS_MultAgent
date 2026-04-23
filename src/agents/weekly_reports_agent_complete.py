# -*- coding: utf-8 -*-
"""
Weekly Reports Agent - Employee Monitoring System (Complete version)

Генерирует еженедельные отчеты по сотрудникам с публикацией в Confluence.
"""

import asyncio
import logging
import json
import aiohttp
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

from ..core.base_agent import BaseAgent, AgentConfig, AgentResult
from ..core.llm_client import LLMClient, LLMRequest
from ..core.json_memory_store import JSONMemoryStore
from ..core.quality_metrics import QualityMetrics
from ..core.config import get_employee_monitoring_config
from ..core.analysis_index_db import AnalysisIndexDB

logger = logging.getLogger(__name__)


@dataclass
class EmployeeWeeklySummary:
    """Еженедельная сводка по сотруднику."""
    employee_name: str
    week_start: datetime
    week_end: datetime
    
    # Task metrics (из Jira)
    total_tasks: int = 0
    completed_tasks: int = 0
    in_progress_tasks: int = 0
    story_points_completed: float = 0.0
    commits_count: int = 0  # Из Jira development panel
    
    # Meeting metrics
    meetings_attended: int = 0
    meetings_total: int = 0
    speaking_turns: int = 0
    action_items_completed: int = 0
    suggestions_made: int = 0
    
    # Performance indicators
    task_completion_rate: float = 0.0
    meeting_engagement_score: float = 0.0
    overall_performance_score: float = 0.0
    
    # Insights
    key_achievements: List[str] = field(default_factory=list)
    areas_for_improvement: List[str] = field(default_factory=list)
    llm_insights: str = ""
    evidence_bundle: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class WeeklyReportResult:
    """Результат еженедельного отчета."""
    # Required fields for schema validation
    week_start: str
    week_end: str
    period: str
    generated_at: datetime
    aggregated_metrics: Dict[str, Any] = field(default_factory=dict)
    trend_analysis: Dict[str, Any] = field(default_factory=dict)
    strategic_insights: List[Dict[str, Any]] = field(default_factory=list)
    system_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Original fields
    week_start_dt: datetime = field(default=None)  # Keep original datetime
    week_end_dt: datetime = field(default=None)    # Keep original datetime
    employees_summaries: Dict[str, EmployeeWeeklySummary] = field(default_factory=dict)
    
    # Summary statistics
    total_employees: int = 0
    total_tasks_completed: int = 0
    total_story_points: int = 0
    total_meetings: int = 0
    avg_performance_score: float = 0.0
    
    # Team insights
    top_performers: List[str] = field(default_factory=list)
    employees_needing_attention: List[str] = field(default_factory=list)
    team_achievements: List[str] = field(default_factory=list)
    team_challenges: List[str] = field(default_factory=list)
    
    # Recommendations
    individual_recommendations: Dict[str, List[str]] = field(default_factory=dict)
    team_recommendations: List[str] = field(default_factory=list)
    
    # Quality and metadata
    quality_score: float = 0.0
    report_generated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class WeeklyReportsAgentComplete(BaseAgent):
    """
    Агент еженедельных отчетов для Employee Monitoring System.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(
            config or AgentConfig(
                name="WeeklyReportsAgent",
                description="Generates weekly employee reports with Confluence publishing",
                version="1.0.0"
            )
        )
        
        # Initialize components
        self.llm_client = LLMClient()
        self.memory_store = JSONMemoryStore()
        self.quality_metrics = QualityMetrics()
        
        # Load configuration
        self.emp_config = get_employee_monitoring_config()
        self.reports_config = self.emp_config.get('reports', {})
        self.confluence_config = self.emp_config.get('confluence', {})
        self.quality_config = self.emp_config.get('quality', {})
        
        project_root = Path(__file__).resolve().parents[2]
        self.reports_root = project_root / "reports"
        self.runs_root = self.reports_root / "runs"
        self.analysis_index_db = AnalysisIndexDB(project_root)

        # Analysis parameters
        self.weekly_reports_dir = Path(self.reports_config.get("weekly_reports_dir", str(self.reports_root / "weekly")))
        self.weekly_reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Confluence configuration - map environment variables
        import os
        self.confluence_url = os.getenv('CONFLUENCE_BASE_URL', '')
        self.confluence_api_token = os.getenv('CONFLUENCE_ACCESS_TOKEN', '')
        self.confluence_space_key = os.getenv('CONFLUENCE_SPACE_KEY', '')
        self.confluence_parent_page_id = os.getenv('CONFLUENCE_PARENT_PAGE_ID', '')
        
        logger.info("WeeklyReportsAgent initialized (without Git integration)")
    
    async def publish_to_confluence(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Публикация отчета в Confluence."""
        try:
            if not all([self.confluence_url, self.confluence_api_token]):
                logger.warning("Confluence configuration incomplete, skipping publication")
                return {
                    'success': False,
                    'error': 'Confluence configuration incomplete'
                }
            
            # Формируем контент страницы
            page_title = f"Weekly Report - Week {report_data.get('week_number', 'Unknown')} ({report_data.get('period', {}).get('start', 'Unknown')[:10]})"
            page_content = await self._format_confluence_content(report_data)
            
            # Создаем или обновляем страницу
            page_url = await self._create_confluence_page(page_title, page_content)
            
            if page_url:
                logger.info(f"Successfully published weekly report to Confluence: {page_url}")
                return {
                    'success': True,
                    'url': page_url,
                    'title': page_title
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to create Confluence page'
                }
                
        except Exception as e:
            logger.error(f"Failed to publish to Confluence: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _format_confluence_content(self, report_data: Dict[str, Any]) -> str:
        """Форматирование контента для Confluence."""
        try:
            content_parts = [
                f"h1. Weekly Employee Report - Week {report_data.get('week_number', 'Unknown')}",
                "",
                f"*Period:* {report_data.get('period', {}).get('start', 'Unknown')[:10]} - {report_data.get('period', {}).get('end', 'Unknown')[:10]}",
                f"*Generated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "h2. Summary Statistics",
                "",
                f"* Total Employees: {report_data.get('total_employees', 0)}",
                f"* Total Tasks Completed: {report_data.get('total_tasks_completed', 0)}",
                f"* Total Story Points: {report_data.get('total_story_points', 0)}",
                f"* Average Performance Score: {report_data.get('avg_performance_score', 0):.2f}/10",
                "",
                "h2. Top Performers",
                ""
            ]
            
            # Добавляем топ performers
            top_performers = report_data.get('top_performers', [])
            if top_performers:
                for i, performer in enumerate(top_performers[:5], 1):
                    content_parts.append(f"# {i}. {performer}")
                content_parts.append("")
            else:
                content_parts.append("No top performers identified this week.")
                content_parts.append("")
            
            content_parts.extend([
                "h2. Employees Needing Attention",
                ""
            ])
            
            # Добавляем сотрудников нуждающихся во внимании
            employees_needing_attention = report_data.get('employees_needing_attention', [])
            if employees_needing_attention:
                for employee in employees_needing_attention:
                    content_parts.append(f"* {employee}")
                content_parts.append("")
            else:
                content_parts.append("All employees performing well this week.")
                content_parts.append("")
            
            content_parts.extend([
                "h2. Team Achievements",
                ""
            ])
            
            # Добавляем достижения команды
            team_achievements = report_data.get('team_achievements', [])
            if team_achievements:
                for achievement in team_achievements:
                    content_parts.append(f"* {achievement}")
                content_parts.append("")
            else:
                content_parts.append("No specific team achievements identified this week.")
                content_parts.append("")
            
            content_parts.extend([
                "h2. Team Challenges",
                ""
            ])
            
            # Добавляем проблемы команды
            team_challenges = report_data.get('team_challenges', [])
            if team_challenges:
                for challenge in team_challenges:
                    content_parts.append(f"* {challenge}")
                content_parts.append("")
            else:
                content_parts.append("No significant team challenges identified this week.")
                content_parts.append("")
            
            content_parts.extend([
                "h2. Team Recommendations",
                ""
            ])
            
            # Добавляем рекомендации команде
            team_recommendations = report_data.get('team_recommendations', [])
            if team_recommendations:
                for recommendation in team_recommendations:
                    content_parts.append(f"* {recommendation}")
                content_parts.append("")
            else:
                content_parts.append("No specific team recommendations for this week.")
                content_parts.append("")
            
            # Добавляем детальную информацию по сотрудникам
            employees_summaries = report_data.get('employees_summaries', {})
            if employees_summaries:
                content_parts.extend([
                    "h2. Individual Employee Details",
                    ""
                ])
                
                for employee_name, summary in employees_summaries.items():
                    content_parts.extend([
                        f"h3. {employee_name}",
                        "",
                        f"* Total Tasks: {summary.get('total_tasks', 0)}",
                        f"* Completed Tasks: {summary.get('completed_tasks', 0)} ({summary.get('task_completion_rate', 0):.1%})",
                        f"* Story Points: {summary.get('story_points_completed', 0)}",
                        f"* Commits: {summary.get('commits_count', 0)}",
                        f"* Meetings Attended: {summary.get('meetings_attended', 0)}/{summary.get('meetings_total', 0)}",
                        f"* Speaking Turns: {summary.get('speaking_turns', 0)}",
                        f"* Action Items Completed: {summary.get('action_items_completed', 0)}",
                        f"* Suggestions Made: {summary.get('suggestions_made', 0)}",
                        f"* Overall Performance Score: {summary.get('overall_performance_score', 0):.2f}/10",
                        ""
                    ])
                    
                    # Ключевые достижения
                    key_achievements = summary.get('key_achievements', [])
                    if key_achievements:
                        content_parts.extend([
                            "*Key Achievements:*",
                            ""
                        ])
                        for achievement in key_achievements:
                            content_parts.append(f"** {achievement}")
                        content_parts.append("")
                    
                    # Области для улучшения
                    areas_for_improvement = summary.get('areas_for_improvement', [])
                    if areas_for_improvement:
                        content_parts.extend([
                            "*Areas for Improvement:*",
                            ""
                        ])
                        for area in areas_for_improvement:
                            content_parts.append(f"** {area}")
                        content_parts.append("")
            
            return "\n".join(content_parts)
            
        except Exception as e:
            logger.error(f"Failed to format Confluence content: {e}")
            return "Error formatting report content"
    
    async def _create_confluence_page(self, title: str, content: str) -> Optional[str]:
        """Создание страницы в Confluence."""
        try:
            # Используем Bearer токен для авторизации
            headers = {
                "Authorization": f"Bearer {self.confluence_api_token}",
                "Content-Type": "application/json"
            }
            
            # Сначала проверяем существует ли страница
            existing_page = await self._find_existing_page(title)
            
            if existing_page:
                # Обновляем существующую страницу
                page_data = {
                    "id": existing_page['id'],
                    "title": title,
                    "type": "page",
                    "space": {"key": self.confluence_space_key},
                    "body": {
                        "storage": {
                            "value": content,
                            "representation": "wiki"
                        }
                    },
                    "version": {"number": existing_page['version'] + 1}
                }
                
                url = f"{self.confluence_url}/rest/api/content/{existing_page['id']}"
                method = "PUT"
            else:
                # Создаем новую страницу
                page_data = {
                    "title": title,
                    "type": "page",
                    "space": {"key": self.confluence_space_key},
                    "ancestors": [{"id": self.confluence_parent_page_id}] if self.confluence_parent_page_id else None,
                    "body": {
                        "storage": {
                            "value": content,
                            "representation": "wiki"
                        }
                    }
                }
                
                url = f"{self.confluence_url}/rest/api/content"
                method = "POST"
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.request(method, url, json=page_data) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        page_id = result.get('id')
                        return f"{self.confluence_url}/pages/viewpage.action?pageId={page_id}"
                    else:
                        error_text = await response.text()
                        logger.error(f"Confluence API error: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Failed to create Confluence page: {e}")
            return None
    
    async def _find_existing_page(self, title: str) -> Optional[Dict[str, Any]]:
        """Поиск существующей страницы по заголовку."""
        try:
            # Используем Bearer токен для авторизации
            headers = {
                "Authorization": f"Bearer {self.confluence_api_token}",
                "Content-Type": "application/json"
            }
            
            # Ищем страницу по заголовку
            search_url = f"{self.confluence_url}/rest/api/content"
            params = {
                "title": title,
                "spaceKey": self.confluence_space_key,
                "expand": "version"
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(search_url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        results = result.get('results', [])
                        if results:
                            return results[0]
                    return None
                        
        except Exception as e:
            logger.error(f"Failed to find existing Confluence page: {e}")
            return None
    
    async def execute(self, input_data: Dict[str, Any] = None, **kwargs) -> AgentResult:
        """Основной метод выполнения агента."""
        try:
            # Handle both old and new calling conventions
            if input_data is None:
                input_data = {}
            
            week_start = input_data.get('week_start') or kwargs.get('week_start')
            week_end = input_data.get('week_end') or kwargs.get('week_end')
            
            # Generate weekly report
            report_result = await self.generate_weekly_report(week_start, week_end)
            
            if report_result and report_result.quality_score >= self.quality_config.get('threshold', 0.8):
                # Publish to Confluence if quality is good
                publication_result = await self.publish_to_confluence(report_result.__dict__)
                
                if publication_result.get('success'):
                    return AgentResult(
                        success=True,
                        message=f"Weekly report generated and published to Confluence successfully",
                        data={
                            'report': report_result.__dict__,
                            'publication': publication_result
                        }
                    )
                else:
                    return AgentResult(
                        success=False,
                        message=f"Weekly report generated but publication failed: {publication_result.get('error')}",
                        data={
                            'report': report_result.__dict__,
                            'publication_error': publication_result.get('error')
                        }
                    )
            else:
                return AgentResult(
                    success=False,
                    message="Weekly report generated but quality check failed",
                    data={'report': report_result.__dict__ if report_result else None}
                )
                
        except Exception as e:
            logger.error(f"WeeklyReportsAgent execution failed: {e}")
            return AgentResult(
                success=False,
                message=f"Weekly report generation failed: {str(e)}",
                data={'error': str(e)}
            )
    
    async def generate_weekly_report(self, week_start: datetime = None, week_end: datetime = None) -> WeeklyReportResult:
        """Генерация еженедельного отчета."""
        try:
            # Определяем период отчета
            if week_end is None:
                week_end = datetime.now()
            if week_start is None:
                # Начало недели (понедельник)
                days_since_monday = week_end.weekday()
                week_start = week_end - timedelta(days=days_since_monday)
            
            # Convert string inputs to datetime if needed
            if isinstance(week_start, str):
                week_start = datetime.fromisoformat(week_start.replace('Z', '+00:00'))
            if isinstance(week_end, str):
                week_end = datetime.fromisoformat(week_end.replace('Z', '+00:00'))
            
            logger.info(f"Generating weekly report for period {week_start.date()} to {week_end.date()}")
            
            # Собираем данные из run-артефактов (единая “шина” интеграции между агентами)
            run_task_data = await self._load_run_task_stage2_data(week_start, week_end)
            run_meeting_data = await self._load_run_meeting_final_data(week_start, week_end)
            run_task_evidence = await self._load_run_task_evidence(week_start, week_end)
            run_employee_evidence = await self._load_run_employee_evidence(week_start, week_end)

            # Анализируем данные по сотрудникам
            employees_summaries = await self._analyze_employee_data_from_runs(
                run_task_data,
                run_meeting_data,
                week_start,
                week_end,
                task_evidence_runs=run_task_evidence,
                employee_evidence_runs=run_employee_evidence,
            )
            
            # Формируем статистику
            total_employees = len(employees_summaries)
            total_tasks_completed = sum(s.completed_tasks for s in employees_summaries.values())
            total_story_points = int(sum(s.story_points_completed for s in employees_summaries.values()))
            total_meetings = sum(s.meetings_attended for s in employees_summaries.values())
            avg_performance_score = sum(s.overall_performance_score for s in employees_summaries.values()) / total_employees if total_employees > 0 else 0
            
            # Генерируем инсайты с помощью LLM
            team_insights = await self._generate_team_insights(employees_summaries)
            
            # Build required schema fields
            week_start_str = week_start.strftime('%Y-%m-%d')
            week_end_str = week_end.strftime('%Y-%m-%d')
            week_number = week_start.isocalendar()[1]
            period = f"W{week_number}-{week_start.year}"
            
            # Build aggregated metrics
            aggregated_metrics = {
                'employee_performance': {
                    'average': round(avg_performance_score, 2),
                    'min': round(min(s.overall_performance_score for s in employees_summaries.values()), 2) if employees_summaries else 0,
                    'max': round(max(s.overall_performance_score for s in employees_summaries.values()), 2) if employees_summaries else 0,
                    'trend': 'stable'  # Would be calculated from historical data
                },
                'project_health': {
                    'average': 7.5,  # Default value
                    'min': 6.0,
                    'max': 9.0,
                    'trend': 'improving'
                },
                'productivity': {
                    'average': round(total_tasks_completed / max(total_employees, 1), 2),
                    'min': 0,
                    'max': round(max(s.completed_tasks for s in employees_summaries.values()), 2) if employees_summaries else 0,
                    'trend': 'stable'
                }
            }
            
            # Build trend analysis
            trend_analysis = {
                'employee_trends': {
                    'trends': [
                        {
                            'employee': emp,
                            'trend': 'stable',
                            'change_percentage': 0.0
                        } for emp in employees_summaries.keys()
                    ]
                },
                'project_trends': {
                    'trends': []
                },
                'productivity_trends': {
                    'trends': []
                }
            }
            
            # Build strategic insights
            strategic_insights = []
            for achievement in team_insights.get('team_achievements', []):
                strategic_insights.append({
                    'type': 'performance_improvement',
                    'impact_level': 'medium',
                    'description': achievement,
                    'recommendations': []
                })
            
            for challenge in team_insights.get('team_challenges', []):
                strategic_insights.append({
                    'type': 'risk_alert',
                    'impact_level': 'high',
                    'description': challenge,
                    'recommendations': team_insights.get('team_recommendations', [])
                })
            
            # Build system metrics
            days_processed = min(7, (week_end - week_start).days + 1)  # Ensure max 7 days
            system_metrics = {
                'days_processed': days_processed,
                'data_processing_time': 0.0,  # Would be calculated
                'quality_score': await self._calculate_report_quality(employees_summaries),
                'insights_generated': len(strategic_insights)
            }
            
            report_result = WeeklyReportResult(
                # Required schema fields
                week_start=week_start_str,
                week_end=week_end_str,
                period=period,
                generated_at=datetime.now(),
                aggregated_metrics=aggregated_metrics,
                trend_analysis=trend_analysis,
                strategic_insights=strategic_insights,
                system_metrics=system_metrics,
                
                # Original fields
                week_start_dt=week_start,
                week_end_dt=week_end,
                employees_summaries=employees_summaries,
                total_employees=total_employees,
                total_tasks_completed=total_tasks_completed,
                total_story_points=total_story_points,
                total_meetings=total_meetings,
                avg_performance_score=avg_performance_score,
                top_performers=team_insights.get('top_performers', []),
                employees_needing_attention=team_insights.get('employees_needing_attention', []),
                team_achievements=team_insights.get('team_achievements', []),
                team_challenges=team_insights.get('team_challenges', []),
                individual_recommendations=team_insights.get('individual_recommendations', {}),
                team_recommendations=team_insights.get('team_recommendations', []),
                quality_score=await self._calculate_report_quality(employees_summaries),
                report_generated_at=datetime.now()
            )
            
            # Сохраняем отчет в хранилище
            await self._save_report_to_storage(report_result)
            
            logger.info(f"Weekly report generated successfully for {total_employees} employees")
            return report_result
            
        except Exception as e:
            logger.error(f"Failed to generate weekly report: {e}")
            raise
    
    async def _load_run_task_stage2_data(self, week_start: datetime, week_end: datetime) -> List[Dict[str, Any]]:
        """Загрузка stage2_task_result.json из reports/runs/* за период."""
        results: List[Dict[str, Any]] = []
        try:
            indexed_runs = self.analysis_index_db.get_runs_in_period("task_analysis", week_start, week_end)
            if indexed_runs:
                for run in indexed_runs:
                    artifact_path = run.get("artifact_path")
                    if not artifact_path:
                        continue
                    task_analysis_path = Path(artifact_path).parent / "stage2" / "stage2_task_result.json"
                    if task_analysis_path.exists():
                        results.append(json.loads(task_analysis_path.read_text(encoding="utf-8")))
                if results:
                    return results

            if not self.runs_root.exists():
                logger.warning(f"Runs root missing: {self.runs_root}")
                return results

            for run_dir in sorted(self.runs_root.iterdir()):
                if not run_dir.is_dir():
                    continue
                try:
                    run_dt = datetime.strptime(run_dir.name, "%Y%m%d_%H%M%S")
                except ValueError:
                    continue

                if run_dt.date() < week_start.date() or run_dt.date() > week_end.date():
                    continue

                stage2_path = run_dir / "task-analysis" / "stage2" / "stage2_task_result.json"
                if stage2_path.exists():
                    results.append(json.loads(stage2_path.read_text(encoding="utf-8")))
            return results
        except Exception as e:
            logger.error(f"Failed to load run task stage2 data: {e}")
            return results

    async def _load_run_meeting_final_data(self, week_start: datetime, week_end: datetime) -> List[Dict[str, Any]]:
        """Загрузка meeting-analysis.json из reports/runs/* за период."""
        results: List[Dict[str, Any]] = []
        try:
            indexed_runs = self.analysis_index_db.get_runs_in_period("meeting_analysis", week_start, week_end)
            if indexed_runs:
                for run in indexed_runs:
                    artifact_path = run.get("artifact_path")
                    if artifact_path and Path(artifact_path).exists():
                        results.append(json.loads(Path(artifact_path).read_text(encoding="utf-8")))
                if results:
                    return results

            if not self.runs_root.exists():
                logger.warning(f"Runs root missing: {self.runs_root}")
                return results

            for run_dir in sorted(self.runs_root.iterdir()):
                if not run_dir.is_dir():
                    continue
                try:
                    run_dt = datetime.strptime(run_dir.name, "%Y%m%d_%H%M%S")
                except ValueError:
                    continue

                if run_dt.date() < week_start.date() or run_dt.date() > week_end.date():
                    continue

                meeting_path = run_dir / "meeting-analysis" / "final" / "meeting-analysis.json"
                if meeting_path.exists():
                    results.append(json.loads(meeting_path.read_text(encoding="utf-8")))
            return results
        except Exception as e:
            logger.error(f"Failed to load run meeting data: {e}")
            return results

    async def _load_run_task_evidence(self, week_start: datetime, week_end: datetime) -> List[Dict[str, Any]]:
        """Load structured task evidence from reports/runs/* for the weekly period."""
        results: List[Dict[str, Any]] = []
        try:
            indexed_rows = self.analysis_index_db.get_task_evidence_rows(week_start, week_end)
            if indexed_rows:
                grouped: Dict[str, Dict[str, Any]] = {}
                for row in indexed_rows:
                    run_id = row["run_id"]
                    grouped.setdefault(run_id, {"employees": {}})
                    artifact_path = row.get("artifact_path")
                    if artifact_path and Path(artifact_path).exists():
                        grouped[run_id]["employees"][row["employee_name"]] = json.loads(
                            Path(artifact_path).read_text(encoding="utf-8")
                        )
                if grouped:
                    return list(grouped.values())

            if not self.runs_root.exists():
                return results
            for run_dir in sorted(self.runs_root.iterdir()):
                if not run_dir.is_dir():
                    continue
                try:
                    run_dt = datetime.strptime(run_dir.name, "%Y%m%d_%H%M%S")
                except ValueError:
                    continue
                if run_dt.date() < week_start.date() or run_dt.date() > week_end.date():
                    continue
                evidence_path = run_dir / "task-analysis" / "evidence" / "task_evidence.json"
                if evidence_path.exists():
                    results.append(json.loads(evidence_path.read_text(encoding="utf-8")))
            return results
        except Exception as e:
            logger.error(f"Failed to load run task evidence: {e}")
            return results

    async def _load_run_employee_evidence(self, week_start: datetime, week_end: datetime) -> List[Dict[str, Any]]:
        """Load per-employee evidence traces produced by meeting analysis."""
        results: List[Dict[str, Any]] = []
        try:
            indexed_rows = self.analysis_index_db.get_meeting_employee_evidence_rows(week_start, week_end)
            if indexed_rows:
                for row in indexed_rows:
                    artifact_path = row.get("artifact_path")
                    if artifact_path and Path(artifact_path).exists():
                        results.append(json.loads(Path(artifact_path).read_text(encoding="utf-8")))
                if results:
                    return results

            if not self.runs_root.exists():
                return results
            for run_dir in sorted(self.runs_root.iterdir()):
                if not run_dir.is_dir():
                    continue
                try:
                    run_dt = datetime.strptime(run_dir.name, "%Y%m%d_%H%M%S")
                except ValueError:
                    continue
                if run_dt.date() < week_start.date() or run_dt.date() > week_end.date():
                    continue
                trace_dir = run_dir / "employee_evidence"
                if trace_dir.exists():
                    for trace_path in sorted(trace_dir.glob("*.json")):
                        results.append(json.loads(trace_path.read_text(encoding="utf-8")))
            return results
        except Exception as e:
            logger.error(f"Failed to load run employee evidence: {e}")
            return results

    async def _analyze_employee_data_from_runs(
        self,
        task_stage2_runs: List[Dict[str, Any]],
        meeting_final_runs: List[Dict[str, Any]],
        week_start: datetime,
        week_end: datetime,
        task_evidence_runs: Optional[List[Dict[str, Any]]] = None,
        employee_evidence_runs: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, EmployeeWeeklySummary]:
        """Анализ данных по сотрудникам на основе run-артефактов."""
        try:
            employees_summaries: Dict[str, EmployeeWeeklySummary] = {}
            task_evidence_runs = task_evidence_runs or []
            employee_evidence_runs = employee_evidence_runs or []

            # TASKS (stage2 employee_analysis: totals/completed/in_progress)
            for stage2 in task_stage2_runs:
                employee_analysis = stage2.get("employee_analysis", {})
                for employee_name, emp in employee_analysis.items():
                    if employee_name not in employees_summaries:
                        employees_summaries[employee_name] = EmployeeWeeklySummary(
                            employee_name=employee_name,
                            week_start=week_start,
                            week_end=week_end,
                        )

                    summary = employees_summaries[employee_name]
                    summary.total_tasks += int(emp.get("total_tasks", 0) or 0)
                    summary.completed_tasks += int(emp.get("completed_tasks", 0) or 0)
                    summary.in_progress_tasks += int(emp.get("in_progress_tasks", 0) or 0)

            # TASK EVIDENCE (richer Jira facts, comments, signals)
            for evidence_run in task_evidence_runs:
                for employee_name, evidence in evidence_run.get("employees", {}).items():
                    if employee_name not in employees_summaries:
                        employees_summaries[employee_name] = EmployeeWeeklySummary(
                            employee_name=employee_name,
                            week_start=week_start,
                            week_end=week_end,
                        )
                    summary = employees_summaries[employee_name]
                    summary.evidence_bundle.setdefault("task_evidence", []).append(evidence)
                    for achievement in evidence.get("achievements", [])[:3]:
                        if achievement and achievement not in summary.key_achievements:
                            summary.key_achievements.append(achievement)
                    for bottleneck in evidence.get("bottlenecks", [])[:3]:
                        if bottleneck and bottleneck not in summary.areas_for_improvement:
                            summary.areas_for_improvement.append(bottleneck)

            # MEETINGS (final analysis contains employee metrics, employee_evidence contains facts)
            meetings_count = len(meeting_final_runs)
            if meetings_count > 0:
                for summary in employees_summaries.values():
                    summary.meetings_total += meetings_count
                    summary.meetings_attended += meetings_count

            for meeting_run in meeting_final_runs:
                for employee_name, meeting_perf in meeting_run.get("employees_performance", {}).items():
                    if employee_name not in employees_summaries:
                        employees_summaries[employee_name] = EmployeeWeeklySummary(
                            employee_name=employee_name,
                            week_start=week_start,
                            week_end=week_end,
                        )
                    summary = employees_summaries[employee_name]
                    summary.meetings_total += max(1, int(meeting_run.get("total_meetings_analyzed", 1) or 1))
                    summary.meetings_attended += max(1, int(meeting_run.get("total_meetings_analyzed", 1) or 1))
                    summary.speaking_turns += int(meeting_perf.get("speaking_turns", 0) or 0)
                    summary.action_items_completed += int(meeting_perf.get("action_items_assigned", 0) or 0)
                    summary.suggestions_made += int(meeting_perf.get("suggestions_made", 0) or 0)
                    summary.evidence_bundle.setdefault("meeting_performance", []).append(meeting_perf)

            for trace in employee_evidence_runs:
                employee_name = trace.get("employee")
                if not employee_name:
                    continue
                if employee_name not in employees_summaries:
                    employees_summaries[employee_name] = EmployeeWeeklySummary(
                        employee_name=employee_name,
                        week_start=week_start,
                        week_end=week_end,
                    )
                employees_summaries[employee_name].evidence_bundle.setdefault("employee_evidence_traces", []).append(trace)

            # Производные метрики + инсайты
            for summary in employees_summaries.values():
                summary.task_completion_rate = summary.completed_tasks / summary.total_tasks if summary.total_tasks > 0 else 0.0
                summary.meeting_engagement_score = min(
                    10.0, (summary.speaking_turns + summary.suggestions_made) / max(1, summary.meetings_attended)
                )
                await self._generate_employee_insights(summary)

            return employees_summaries

        except Exception as e:
            logger.error(f"Failed to analyze employee data from runs: {e}")
            return {}

    async def _load_daily_jira_data(self, week_start: datetime, week_end: datetime) -> List[Dict[str, Any]]:
        """Legacy: загрузка ежедневных данных Jira за неделю из memory store."""
        try:
            jira_data: List[Dict[str, Any]] = []
            current_date = week_start.date()

            while current_date <= week_end.date():
                try:
                    daily_data = await self.memory_store.load_json_data("daily_jira_data", current_date)
                    jira_data.append(daily_data)
                except FileNotFoundError:
                    logger.warning(f"No Jira data found for {current_date}")
                except Exception as e:
                    logger.error(f"Error loading Jira data for {current_date}: {e}")
                current_date += timedelta(days=1)

            return jira_data
        except Exception as e:
            logger.error(f"Failed to load daily Jira data: {e}")
            return []

    async def _load_daily_meeting_data(self, week_start: datetime, week_end: datetime) -> List[Dict[str, Any]]:
        """Legacy: загрузка ежедневных данных собраний за неделю из memory store."""
        try:
            meeting_data: List[Dict[str, Any]] = []
            current_date = week_start.date()

            while current_date <= week_end.date():
                try:
                    daily_data = await self.memory_store.load_json_data("daily_meeting_data", current_date)
                    meeting_data.append(daily_data)
                except FileNotFoundError:
                    logger.warning(f"No meeting data found for {current_date}")
                except Exception as e:
                    logger.error(f"Error loading meeting data for {current_date}: {e}")
                current_date += timedelta(days=1)

            return meeting_data
        except Exception as e:
            logger.error(f"Failed to load daily meeting data: {e}")
            return []

    async def _analyze_employee_data(
        self, jira_data: List[Dict[str, Any]], meeting_data: List[Dict[str, Any]], week_start: datetime, week_end: datetime
    ) -> Dict[str, EmployeeWeeklySummary]:
        """Legacy: анализ данных по сотрудникам (для collect_weekly_data)."""
        try:
            employees_summaries: Dict[str, EmployeeWeeklySummary] = {}

            # Пытаемся поддержать старый формат memory store, если он есть
            for daily_jira in jira_data:
                employees = daily_jira.get("employees", {})
                for employee_name, employee_tasks in employees.items():
                    if employee_name not in employees_summaries:
                        employees_summaries[employee_name] = EmployeeWeeklySummary(
                            employee_name=employee_name,
                            week_start=week_start,
                            week_end=week_end,
                        )

                    summary = employees_summaries[employee_name]
                    tasks = employee_tasks.get("tasks", [])
                    summary.total_tasks += len(tasks)
                    summary.completed_tasks += len([t for t in tasks if t.get("status") == "Done"])
                    summary.in_progress_tasks += len([t for t in tasks if t.get("status") == "In Progress"])
                    summary.story_points_completed += sum(t.get("story_points", 0) for t in tasks if t.get("status") == "Done")
                    summary.commits_count += int(employee_tasks.get("commits_count", 0) or 0)

            for summary in employees_summaries.values():
                summary.task_completion_rate = summary.completed_tasks / summary.total_tasks if summary.total_tasks > 0 else 0.0
                summary.meeting_engagement_score = min(
                    10.0, (summary.speaking_turns + summary.suggestions_made) / max(1, summary.meetings_attended)
                )
                await self._generate_employee_insights(summary)

            return employees_summaries
        except Exception as e:
            logger.error(f"Failed to analyze employee data (legacy): {e}")
            return {}
    
    async def _generate_employee_insights(self, summary: EmployeeWeeklySummary):
        """Генерация инсайтов по сотруднику с помощью LLM."""
        try:
            llm_available = await self.llm_client.is_available()
            if not llm_available:
                # Базовая логика без LLM
                if summary.task_completion_rate >= 0.9:
                    summary.key_achievements.append("Excellent task completion rate")
                    summary.overall_performance_score = 9.0
                elif summary.task_completion_rate >= 0.7:
                    summary.key_achievements.append("Good task completion rate")
                    summary.overall_performance_score = 7.0
                else:
                    summary.areas_for_improvement.append("Task completion needs improvement")
                    summary.overall_performance_score = 5.0
                return
            
            evidence_bundle = json.dumps(summary.evidence_bundle, ensure_ascii=False, indent=2, default=str)

            prompt = f"""
            Проанализируй недельную производительность сотрудника строго на основе evidence.
            
            Employee: {summary.employee_name}
            Week: {summary.week_start.date()} to {summary.week_end.date()}
            
            Task Metrics:
            - Total tasks: {summary.total_tasks}
            - Completed tasks: {summary.completed_tasks} ({summary.task_completion_rate:.1%})
            - In progress tasks: {summary.in_progress_tasks}
            - Story points completed: {summary.story_points_completed}
            - Commits: {summary.commits_count}
            
            Meeting Metrics:
            - Meetings attended: {summary.meetings_attended}/{summary.meetings_total}
            - Speaking turns: {summary.speaking_turns}
            - Action items completed: {summary.action_items_completed}
            - Suggestions made: {summary.suggestions_made}

            Evidence bundle:
            {evidence_bundle}
            
            Верни строгий JSON по схеме:
            {{
                "key_achievements": ["1-3 достижения, подтвержденные evidence"],
                "areas_for_improvement": ["1-3 зоны развития или риска, подтвержденные evidence"],
                "overall_performance_score": 8.5,
                "insights_comment": "Короткий вывод с опорой на Jira/meeting evidence",
                "evidence_references": ["короткие ссылки на issue/meeting/excerpt"]
            }}
            
            Требования:
            - только JSON без markdown
            - не выдумывай факты, которых нет в evidence
            - если evidence мало, явно напиши это в insights_comment
            """
            
            llm_request = LLMRequest(
                prompt=prompt,
                system_prompt="Ты - аналитик производительности. Верни только валидный JSON без markdown.",
                max_tokens=1200,
                temperature=0.2,
            )
            response = await self.llm_client.generate_response(llm_request)

            if response and getattr(response, "content", None):
                insights_data = await self._parse_or_repair_employee_insights(response.content, summary.employee_name)
                if insights_data:
                    summary.key_achievements = insights_data.get("key_achievements", [])
                    summary.areas_for_improvement = insights_data.get("areas_for_improvement", [])
                    summary.overall_performance_score = insights_data.get("overall_performance_score", 5.0)
                    summary.llm_insights = insights_data.get("insights_comment", "")
                else:
                    logger.warning(f"Failed to parse LLM response for {summary.employee_name}")
                    self._save_unparsed_employee_insight(summary.employee_name, response.content)
                    summary.overall_performance_score = min(10, summary.task_completion_rate * 10)
            
        except Exception as e:
            logger.error(f"Failed to generate insights for {summary.employee_name}: {e}")
            # Базовая оценка
            summary.overall_performance_score = min(10, summary.task_completion_rate * 10)

    async def _parse_or_repair_employee_insights(self, raw_response: str, employee_name: str) -> Optional[Dict[str, Any]]:
        """Parse strict JSON, then ask for a repair pass before giving up."""
        parsed = self._parse_json_object(raw_response)
        if parsed:
            return parsed

        try:
            repair_prompt = f"""
Исправь ответ LLM в валидный JSON без markdown и без добавления новых фактов.

Сотрудник: {employee_name}

Исходный ответ:
{raw_response}

Верни JSON по схеме:
{{
  "key_achievements": [],
  "areas_for_improvement": [],
  "overall_performance_score": 5.0,
  "insights_comment": "",
  "evidence_references": []
}}
"""
            repair_request = LLMRequest(
                prompt=repair_prompt,
                system_prompt="Ты исправляешь невалидный JSON. Верни только JSON.",
                max_tokens=800,
                temperature=0.0,
            )
            repair_response = await self.llm_client.generate_response(repair_request)
            if repair_response and getattr(repair_response, "content", None):
                return self._parse_json_object(repair_response.content)
        except Exception as e:
            logger.warning(f"JSON repair failed for {employee_name}: {e}")
        return None

    def _parse_json_object(self, raw_response: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(raw_response)
        except Exception:
            pass

        json_patterns = [
            r"```json\s*(\{.*?\})\s*```",
            r"```\s*(\{.*?\})\s*```",
            r"(\{.*\})",
        ]
        for pattern in json_patterns:
            match = re.search(pattern, raw_response, re.DOTALL | re.IGNORECASE)
            if not match:
                continue
            json_text = re.sub(r",\s*([}\]])", r"\1", match.group(1).strip())
            try:
                parsed = json.loads(json_text)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue
        return None

    def _save_unparsed_employee_insight(self, employee_name: str, raw_response: str) -> None:
        try:
            errors_dir = self.weekly_reports_dir / "llm_parse_errors"
            errors_dir.mkdir(parents=True, exist_ok=True)
            safe_name = re.sub(r"[^\w\s-]", "", employee_name).strip()
            safe_name = re.sub(r"[-\s]+", "_", safe_name)
            error_file = errors_dir / f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            error_file.write_text(raw_response, encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save unparsed insight for {employee_name}: {e}")
    
    async def _generate_team_insights(self, employees_summaries: Dict[str, EmployeeWeeklySummary]) -> Dict[str, Any]:
        """Генерация командных инсайтов."""
        try:
            if not employees_summaries:
                return {}
            
            # Сортируем сотрудников по производительности
            sorted_employees = sorted(
                employees_summaries.items(),
                key=lambda x: x[1].overall_performance_score,
                reverse=True
            )
            
            # Топ performers (топ 20%)
            top_performers = [name for name, _ in sorted_employees[:max(1, len(sorted_employees) // 5)]]
            
            # Сотрудники нуждающиеся во внимании (низкие показатели)
            employees_needing_attention = [
                name for name, summary in employees_summaries.items()
                if summary.overall_performance_score < 6.0 or summary.task_completion_rate < 0.7
            ]
            
            # Генерируем достижения и проблемы команды
            total_tasks = sum(s.total_tasks for s in employees_summaries.values())
            completed_tasks = sum(s.completed_tasks for s in employees_summaries.values())
            avg_completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
            
            team_achievements = []
            team_challenges = []
            
            if avg_completion_rate >= 0.9:
                team_achievements.append("Excellent overall task completion rate")
            elif avg_completion_rate >= 0.7:
                team_achievements.append("Good team task completion rate")
            else:
                team_challenges.append("Low overall task completion rate")
            
            # Рекомендации команде
            team_recommendations = []
            if employees_needing_attention:
                team_recommendations.append("Provide additional support and training for underperforming employees")
            if avg_completion_rate < 0.8:
                team_recommendations.append("Review and optimize task assignment process")
            
            # Индивидуальные рекомендации
            individual_recommendations = {}
            for name, summary in employees_summaries.items():
                recommendations = []
                if summary.task_completion_rate < 0.7:
                    recommendations.append("Focus on completing assigned tasks on time")
                if summary.meeting_engagement_score < 5:
                    recommendations.append("Increase participation in team meetings")
                if recommendations:
                    individual_recommendations[name] = recommendations
            
            return {
                'top_performers': top_performers,
                'employees_needing_attention': employees_needing_attention,
                'team_achievements': team_achievements,
                'team_challenges': team_challenges,
                'team_recommendations': team_recommendations,
                'individual_recommendations': individual_recommendations
            }
            
        except Exception as e:
            logger.error(f"Failed to generate team insights: {e}")
            return {}
    
    async def _calculate_report_quality(self, employees_summaries: Dict[str, EmployeeWeeklySummary]) -> float:
        """Расчет качества отчета."""
        try:
            if not employees_summaries:
                return 0.0
            
            # Базовые метрики качества
            completeness = min(1.0, len(employees_summaries) / 5.0)  # Ожидаем минимум 5 сотрудников
            
            # Средняя полнота данных
            avg_completeness = 0.0
            for summary in employees_summaries.values():
                employee_completeness = 0.0
                if summary.total_tasks > 0:
                    employee_completeness += 0.3  # Есть данные по задачам
                if summary.meetings_total > 0:
                    employee_completeness += 0.3  # Есть данные по собраниям
                if summary.key_achievements or summary.areas_for_improvement:
                    employee_completeness += 0.4  # Есть инсайты
                
                avg_completeness += employee_completeness
            
            if employees_summaries:
                avg_completeness /= len(employees_summaries)
            
            # Итоговый скор качества
            quality_score = (completeness * 0.4) + (avg_completeness * 0.6)
            return min(1.0, quality_score)
            
        except Exception as e:
            logger.error(f"Failed to calculate report quality: {e}")
            return 0.0
    
    async def _save_report_to_storage(self, report_result: WeeklyReportResult):
        """Сохранение отчета в хранилище."""
        try:
            report_data = report_result.__dict__
            
            # Убираем не-сериализуемые объекты
            report_data['employees_summaries'] = {
                name: summary.__dict__ 
                for name, summary in report_result.employees_summaries.items()
            }
            
            # Сохраняем в JSON memory store - используем datetime object вместо строки
            await self.memory_store.persist_json_data(
                'weekly_summary_data', 
                report_data,
                report_result.week_start_dt  # Передаем datetime object
            )
            
            # Также сохраняем локально - используем week_start_dt вместо week_start
            filename = f"weekly_report_{report_result.week_start_dt.strftime('%Y-%m-%d')}.json"
            file_path = self.weekly_reports_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Weekly report saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save weekly report to storage: {e}")
            raise
    
    async def collect_weekly_data(self, week_start: datetime = None, week_end: datetime = None) -> Dict[str, Any]:
        """
        Collect weekly data for analysis and reporting.
        
        This method provides a simplified interface for collecting weekly data
        that can be used by other components in the system.
        
        Args:
            week_start: Start of the week (defaults to Monday of current week)
            week_end: End of the week (defaults to current time)
            
        Returns:
            Dictionary containing collected weekly data with task and meeting metrics
        """
        try:
            logger.info("Starting weekly data collection")
            
            # Define week period if not provided
            if week_end is None:
                week_end = datetime.now()
            if week_start is None:
                # Start of week (Monday)
                days_since_monday = week_end.weekday()
                week_start = week_end - timedelta(days=days_since_monday)
            
            # Load daily Jira data for the week
            daily_jira_data = await self._load_daily_jira_data(week_start, week_end)
            
            # Load daily meeting data for the week
            daily_meeting_data = await self._load_daily_meeting_data(week_start, week_end)
            
            # Analyze employee data from both sources
            employees_summaries = await self._analyze_employee_data(
                daily_jira_data, 
                daily_meeting_data, 
                week_start, 
                week_end
            )
            
            # Calculate weekly statistics
            total_employees = len(employees_summaries)
            total_tasks_completed = sum(s.completed_tasks for s in employees_summaries.values())
            total_story_points = int(sum(s.story_points_completed for s in employees_summaries.values()))
            total_commits = sum(s.commits_count for s in employees_summaries.values())
            total_meetings_attended = sum(s.meetings_attended for s in employees_summaries.values())
            avg_performance_score = sum(s.overall_performance_score for s in employees_summaries.values()) / total_employees if total_employees > 0 else 0
            
            # Prepare employee details for output
            employees_data = {}
            for name, summary in employees_summaries.items():
                employees_data[name] = {
                    'total_tasks': summary.total_tasks,
                    'completed_tasks': summary.completed_tasks,
                    'completion_rate': summary.task_completion_rate,
                    'story_points_completed': summary.story_points_completed,
                    'commits_count': summary.commits_count,
                    'meetings_attended': summary.meetings_attended,
                    'meetings_total': summary.meetings_total,
                    'meeting_engagement_score': summary.meeting_engagement_score,
                    'speaking_turns': summary.speaking_turns,
                    'action_items_completed': summary.action_items_completed,
                    'suggestions_made': summary.suggestions_made,
                    'overall_performance_score': summary.overall_performance_score,
                    'key_achievements': summary.key_achievements,
                    'areas_for_improvement': summary.areas_for_improvement,
                    'llm_insights': summary.llm_insights
                }
            
            # Generate team insights
            team_insights = await self._generate_team_insights(employees_summaries)
            
            # Prepare result data
            weekly_data = {
                'collection_metadata': {
                    'week_start': week_start.isoformat(),
                    'week_end': week_end.isoformat(),
                    'collection_time': datetime.now().isoformat(),
                    'total_days_analyzed': (week_end - week_start).days + 1,
                    'agent_name': self.config.name
                },
                'weekly_summary': {
                    'total_employees': total_employees,
                    'total_tasks_completed': total_tasks_completed,
                    'total_story_points': total_story_points,
                    'total_commits': total_commits,
                    'total_meetings_attended': total_meetings_attended,
                    'avg_performance_score': round(avg_performance_score, 2),
                    'quality_score': await self._calculate_report_quality(employees_summaries)
                },
                'employees_data': employees_data,
                'team_insights': {
                    'top_performers': team_insights.get('top_performers', []),
                    'employees_needing_attention': team_insights.get('employees_needing_attention', []),
                    'team_achievements': team_insights.get('team_achievements', []),
                    'team_challenges': team_insights.get('team_challenges', []),
                    'team_recommendations': team_insights.get('team_recommendations', []),
                    'individual_recommendations': team_insights.get('individual_recommendations', {})
                },
                'data_sources': {
                    'jira_data_days': len(daily_jira_data),
                    'meeting_data_days': len(daily_meeting_data),
                    'data_quality': 'good' if len(daily_jira_data) > 0 and len(daily_meeting_data) > 0 else 'limited'
                }
            }
            
            logger.info(f"Weekly data collection completed: {total_employees} employees, "
                       f"{total_tasks_completed} tasks completed, {total_commits} commits")
            
            return weekly_data
            
        except Exception as e:
            logger.error(f"Failed to collect weekly data: {e}")
            return {
                'success': False,
                'error': str(e),
                'collection_metadata': {
                    'collection_time': datetime.now().isoformat(),
                    'agent_name': self.config.name
                }
            }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Проверка состояния агента."""
        try:
            llm_available = await self.llm_client.is_available()
            memory_health = await self.memory_store.health_check()
            memory_available = memory_health.get('status') == 'healthy'
            confluence_configured = bool(self.confluence_url and self.confluence_api_token)
            
            return {
                'agent_name': self.config.name,
                'status': 'healthy' if llm_available and memory_available else 'degraded',
                'llm_client': 'available' if llm_available else 'unavailable',
                'memory_store': memory_health.get('status', 'unknown'),
                'confluence_client': 'configured' if confluence_configured else 'not_configured',
                'confluence_configured': confluence_configured,
                'reports_directory': str(self.weekly_reports_dir),
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


# Add alias for backward compatibility
WeeklyReportsAgent = WeeklyReportsAgentComplete
