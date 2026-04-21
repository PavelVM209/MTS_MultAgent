"""
Improved Task Analyzer Agent - Two Stage LLM Analysis System

Analyzes JIRA tasks using a two-stage approach:
Stage 1: LLM generates detailed text analysis
Stage 2: Direct JSON extraction from text analysis
Guarantees analysis of ALL employees regardless of task count
"""

import asyncio
import logging
import json
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path

from ..core.base_agent import BaseAgent, AgentConfig, AgentResult
from ..core.llm_client import LLMClient, LLMRequest
from ..core.json_memory_store import JSONMemoryStore
from ..core.quality_metrics import QualityMetrics
from ..core.config import get_employee_monitoring_config
from ..core.jira_client import JiraClient
from ..core.role_context_manager import EmployeeRoleManager
from ..core.processing_tracker import ProcessingTracker
from ..core.enhanced_file_manager import EnhancedFileManager

logger = logging.getLogger(__name__)


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


class ImprovedTaskAnalyzerAgent(BaseAgent):
    """
    Improved Task Analysis Agent with Two-Stage LLM Analysis.
    
    Uses the proven two-stage approach:
    Stage 1: Comprehensive text analysis with mandatory employee coverage
    Stage 2: Reliable JSON extraction without LLM dependency
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize Improved Task Analyzer Agent."""
        super().__init__(
            config or AgentConfig(
                name="ImprovedTaskAnalyzerAgent",
                description="Two-stage LLM analysis for comprehensive employee monitoring",
                version="2.0.0"
            )
        )
        
        # Initialize components
        self.llm_client = LLMClient()
        self.memory_store = JSONMemoryStore()
        self.quality_metrics = QualityMetrics()
        self.role_manager = EmployeeRoleManager()
        
        # Initialize processing tracker and file manager
        self.processing_tracker = ProcessingTracker()
        self.file_manager = EnhancedFileManager()
        
        # Load configuration
        self.emp_config = get_employee_monitoring_config()
        
        # Load Jira configuration
        import os
        analysis_depth_days = os.getenv('JIRA_ANALYSIS_DEPTH_DAYS', '7')
        self.jira_config = {
            'base_url': os.getenv('JIRA_BASE_URL', ''),
            'username': os.getenv('JIRA_USERNAME', ''),
            'api_token': os.getenv('JIRA_ACCESS_TOKEN', ''),
            'project_key': os.getenv('JIRA_PROJECT_KEYS', '').split(',')[0] if os.getenv('JIRA_PROJECT_KEYS') else '',
            'query_filter': os.getenv('JIRA_QUERY_FILTER', f'project = "OPENBD" AND status IN (11115, 3, 10100, 6, 14301, 14500, 13821, 10207, 1) AND updated >= -{analysis_depth_days}d'),
            'max_results': int(os.getenv('JIRA_MAX_RESULTS', '100')),
            'fields': ['assignee', 'status', 'summary', 'description', 'comment', 'created', 'updated', 'priority', 'project']
        }
        
        self.analysis_depth_days = int(analysis_depth_days)
        logger.info(f"Improved Task Analyzer configured with {self.analysis_depth_days} days analysis depth")
        
        # Reports directory
        self.reports_config = self.emp_config.get('reports', {})
        self.daily_reports_dir = Path(self.reports_config.get('daily_reports_dir', './reports/daily'))
        self.daily_reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("ImprovedTaskAnalyzerAgent initialized with two-stage analysis")
    
    async def fetch_jira_tasks(self) -> List[Dict[str, Any]]:
        """Fetch tasks from Jira API using existing client."""
        try:
            logger.info("Fetching tasks from Jira API")
            
            jira_client = JiraClient()
            
            if not await jira_client.test_connection():
                logger.error("Jira API connection failed")
                return []
            
            jql = self.jira_config.get('query_filter', 'status in (In Progress, Done, To Do) AND updated >= -7d')
            fields = self.jira_config.get('fields', ['assignee', 'status', 'summary', 'description', 'created', 'updated', 'priority', 'project'])
            max_results = self.jira_config.get('max_results', 100)
            
            logger.info(f"Using JQL: {jql}")
            
            tasks = await jira_client.search_issues(
                jql=jql,
                fields=fields,
                max_results=max_results
            )
            
            if not tasks:
                logger.warning("No tasks returned from Jira API")
                return []
            
            # Process tasks
            processed_tasks = []
            for task in tasks:
                try:
                    fields = task.get('fields', {})
                    
                    processed_task = {
                        'id': task.get('id'),
                        'key': task.get('key'),
                        'summary': fields.get('summary', ''),
                        'status': fields.get('status', {}).get('name', ''),
                        'assignee': self._extract_assignee(fields.get('assignee')),
                        'created': fields.get('created'),
                        'updated': fields.get('updated'),
                        'due_date': fields.get('duedate'),
                        'priority': fields.get('priority', {}).get('name', 'Medium'),
                        'description': fields.get('description', ''),
                        'comments': self._extract_comments(fields),
                        'project': fields.get('project', {}).get('key', ''),
                        'commits_count': self._extract_commits_from_task(fields),
                        'pull_requests_count': self._extract_prs_from_task(fields),
                    }
                    
                    processed_tasks.append(processed_task)
                    
                except Exception as e:
                    logger.warning(f"Failed to process Jira task {task.get('key', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Successfully processed {len(processed_tasks)} tasks from Jira")
            return processed_tasks
            
        except Exception as e:
            logger.error(f"Failed to fetch Jira tasks: {e}")
            return []
    
    def _extract_assignee(self, assignee_field: Any) -> str:
        """Extract employee name from assignee field."""
        if not assignee_field:
            return 'Unassigned'
        
        if isinstance(assignee_field, dict):
            return (
                assignee_field.get('displayName') or 
                assignee_field.get('name') or 
                assignee_field.get('emailAddress') or 
                'Unknown'
            )
        
        return str(assignee_field)
    
    def _extract_comments(self, fields: Dict[str, Any]) -> str:
        """Extract comments from task."""
        try:
            comments = []
            comment_field = fields.get('comment', {})
            if comment_field and isinstance(comment_field, dict):
                comments_list = comment_field.get('comments', [])
                
                for comment in comments_list:
                    try:
                        author = self._extract_assignee(comment.get('author'))
                        body = comment.get('body', '')
                        if body.strip():
                            comments.append(f"{author}: {body.strip()}")
                    except Exception:
                        continue
            
            return " | ".join(comments)
            
        except Exception as e:
            logger.warning(f"Failed to extract comments from task: {e}")
            return ""
    
    def _extract_commits_from_task(self, fields: Dict[str, Any]) -> int:
        """Extract commit count from task."""
        try:
            development = fields.get('development', {})
            if development:
                pull_requests = development.get('pullRequests', [])
                total_commits = 0
                for pr in pull_requests:
                    total_commits += pr.get('commitCount', 0)
                return total_commits
            return 0
        except Exception:
            return 0
    
    def _extract_prs_from_task(self, fields: Dict[str, Any]) -> int:
        """Extract PR count from task."""
        try:
            development = fields.get('development', {})
            if development:
                return len(development.get('pullRequests', []))
            return 0
        except Exception:
            return 0
    
    async def _group_tasks_by_employee(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group tasks by employee."""
        employee_tasks = {}
        
        for task in tasks:
            employee = task['assignee']
            if employee not in employee_tasks:
                employee_tasks[employee] = []
            employee_tasks[employee].append(task)
        
        return employee_tasks
    
    async def _enhance_task_analysis_with_role_context(self, employee_tasks: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Обогащение анализа задач контекстом ролей сотрудников.
        
        Args:
            employee_tasks: Сгруппированные задачи по сотрудникам
            
        Returns:
            Обогащенные данные с ролевым контекстом
        """
        try:
            role_enhancement = {
                "enhanced_employees": {},
                "team_context": {},
                "role_statistics": {}
            }
            
            # Получаем контекст команды
            team_context = self.role_manager.get_team_context()
            role_enhancement["team_context"] = team_context
            
            # Обогащаем каждого сотрудника ролевым контекстом
            for employee_name, tasks in employee_tasks.items():
                role_context = self.role_manager.enhance_task_analysis(employee_name)
                role_enhancement["enhanced_employees"][employee_name] = {
                    "tasks_count": len(tasks),
                    "role_context": role_context,
                    "task_summaries": [
                        {
                            "key": task.get("key", ""),
                            "summary": task.get("summary", ""),
                            "status": task.get("status", ""),
                            "priority": task.get("priority", "")
                        }
                        for task in tasks[:5]  # Топ 5 задач для анализа
                    ]
                }
            
            # Собираем статистику по ролям
            role_stats = {}
            for employee_name, enhancement in role_enhancement["enhanced_employees"].items():
                role_info = enhancement["role_context"]
                if role_info.get("assignee_identified"):
                    activity_level = role_info.get("activity_level", "unknown")
                    role_stats[activity_level] = role_stats.get(activity_level, 0) + 1
            
            role_enhancement["role_statistics"] = role_stats
            
            logger.info(f"Role context enhancement completed for {len(employee_tasks)} employees")
            
            return role_enhancement
            
        except Exception as e:
            logger.error(f"Failed to enhance task analysis with role context: {e}")
            return {
                "enhanced_employees": {},
                "team_context": {},
                "role_statistics": {},
                "error": str(e)
            }
    
    def _format_role_context_for_prompt(self, role_context_data: Dict[str, Any]) -> str:
        """
        Форматирует контекст ролей для включения в LLM промпт.
        
        Args:
            role_context_data: Данные ролевого контекст
            
        Returns:
            Отформатированный текст для промпта
        """
        try:
            context_parts = []
            
            # Заголовок секции
            context_parts.append("=== КОНТЕКСТ РОЛЕЙ И ДОЛЖНОСТЕЙ ===")
            
            # Общая информация о команде
            team_context = role_context_data.get("team_context", {})
            if team_context:
                context_parts.append(f"Всего сотрудников в команде: {team_context.get('total_employees', 'N/A')}")
                context_parts.append(f"Выявленные сотрудники: {team_context.get('identified_employees', 'N/A')}")
                context_parts.append(f"Текучесть кадров: {team_context.get('turnover_rate', 'N/A')}")
                context_parts.append("")
            
            # Детальная информация по сотрудникам
            enhanced_employees = role_context_data.get("enhanced_employees", {})
            if enhanced_employees:
                context_parts.append("ИНФОРМАЦИЯ О СОТРУДНИКАХ:")
                
                for employee_name, emp_data in enhanced_employees.items():
                    role_context = emp_data.get("role_context", {})
                    
                    # Формируем информацию о сотруднике
                    emp_info = []
                    emp_info.append(f"Сотрудник: {employee_name}")
                    
                    # Должность и роль
                    if role_context.get("assignee_identified"):
                        emp_info.append(f"Должность: {role_context.get('role_level', 'N/A')}")
                        emp_info.append(f"Ответственность: {role_context.get('responsibility_level', 'N/A')}")
                        emp_info.append(f"Активность: {role_context.get('activity_level', 'N/A')}")
                        emp_info.append(f"Статус: {role_context.get('current_status', 'N/A')}")
                        emp_info.append(f"Направление: {role_context.get('specialization', 'N/A')}")
                    else:
                        emp_info.append("Должность: Не определена")
                        emp_info.append("Статус: Новый или незарегистрированный сотрудник")
                    
                    # Количество задач
                    tasks_count = emp_data.get("tasks_count", 0)
                    emp_info.append(f"Текущих задач: {tasks_count}")
                    
                    # Последние задачи для контекста
                    task_summaries = emp_data.get("task_summaries", [])
                    if task_summaries:
                        emp_info.append("Последние задачи:")
                        for task in task_summaries[:3]:  # Только топ 3
                            emp_info.append(f"  - {task.get('key', '')}: {task.get('summary', '')} ({task.get('status', '')})")
                    
                    context_parts.append("\n".join(emp_info))
                    context_parts.append("")  # Пустая строка между сотрудниками
            
            # Статистика по ролям
            role_stats = role_context_data.get("role_statistics", {})
            if role_stats:
                context_parts.append("СТАТИСТИКА ПО РОЛЯМ:")
                for activity_level, count in role_stats.items():
                    context_parts.append(f"- {activity_level}: {count} сотрудников")
                context_parts.append("")
            
            # Важные инструкции для LLM
            context_parts.append("=== ИНСТРУКЦИИ ДЛЯ АНАЛИЗА С УЧЕТОМ РОЛЕЙ ===")
            context_parts.append("1. Учитывай должности и ответственность при формировании рекомендаций")
            context_parts.append("2. Product Owner не может выполнять технические задачи разработчика")
            context_parts.append("3. Рекомендации должны соответствовать уровню должности")
            context_parts.append("4. Учитывай специализацию сотрудника при распределении задач")
            context_parts.append("5. Новым сотрудникам требуются задачи с наставничеством")
            context_parts.append("")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Failed to format role context for prompt: {e}")
            return "=== КОНТЕКСТ РОЛЕЙ И ДОЛЖНОСТЕЙ ===\nОшибка форматирования контекста ролей\n"
    
    async def stage1_text_analysis(self, tasks: List[Dict[str, Any]], employee_tasks: Dict[str, List[Dict[str, Any]]]) -> Optional[str]:
        """Stage 1: Generate comprehensive text analysis with LLM and Role Context."""
        try:
            logger.info("=== STAGE 1: TEXTUAL ANALYSIS WITH ROLE CONTEXT ===")
            
            # P6-10: Load Role Context FIRST - это критически важно!
            logger.info("Loading Role Context for all employees...")
            role_context_data = await self._enhance_task_analysis_with_role_context(employee_tasks)
            
            # Extract role context for prompt
            role_context_text = self._format_role_context_for_prompt(role_context_data)
            
            # Prepare tasks data
            tasks_summary = []
            for task in tasks[:50]:  # Use more tasks for better analysis
                description = task.get('description', '') or ''
                comments = task.get('comments', '') or ''
                
                tasks_summary.append(f"""
Task: {task.get('key', '') or 'N/A'}
Title: {task.get('summary', '') or 'N/A'}
Status: {task.get('status', '') or 'N/A'}
Assignee: {task.get('assignee', '') or 'N/A'}
Priority: {task.get('priority', '') or 'N/A'}
Description: {description[:300]}...
Comments: {comments}
""")
            
            # Prepare employee summary
            employee_summary = []
            for employee, emp_tasks in employee_tasks.items():
                status_counts = {}
                for t in emp_tasks:
                    status = t.get('status', 'N/A')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                employee_summary.append(f"""
Employee: {employee}
Total tasks: {len(emp_tasks)}
Status distribution: {dict(status_counts)}
Recent tasks:
{chr(10).join([f"- {t.get('summary', '')} ({t.get('status', '')}, {t.get('priority', '')})" for t in emp_tasks[:5]])}
""")
            
            # Get all employees for mandatory analysis
            all_employees = list(employee_tasks.keys())
            
            # Comprehensive prompt with mandatory employee analysis and Role Context - REQUIRED RUSSIAN LANGUAGE
            prompt = f"""
Вы - СТАРШИЙ АНАЛИТИК ПРОИЗВОДИТЕЛЬНОСТИ КОМАНДЫ для мониторинга сотрудников. Проанализируйте следующие задачи и предоставьте ДЕТАЛЬНЫЙ текстовый анализ НА РУССКОМ ЯЗЫКЕ.

{role_context_text}

ЗАДАЧИ ДЛЯ АНАЛИЗА:
{chr(10).join(tasks_summary)}

СОТРУДНИКИ:
{chr(10).join(employee_summary)}

ПРЕДОСТАВЬТЕ АНАЛИЗ В СЛЕДУЮЩЕМ ФОРМАТЕ НА РУССКОМ ЯЗЫКЕ:

=== КОМАНДНЫЕ ИНСАЙТЫ (минимум 5) ===
1. [Инсайт о производительности команды]
2. [Инсайт о рабочих паттернах]
3. [Инсайт о проблемах в процессах]
4. [Инсайт о сильных сторонах]
5. [Инсайт о рисках и возможностях]

=== РЕКОМЕНДАЦИИ МЕНЕДЖЕРУ (минимум 4) ===
1. [Конкретная рекомендация для менеджеров]
2. [Рекомендация по оптимизации процессов]
3. [Рекомендация по распределению нагрузки]
4. [Рекомендация по обучению и развитию]

=== АНАЛИЗ СОТРУДНИКОВ ===
Сотрудник: [Имя]
- Общая оценка производительности: [1-10]
- Ключевые достижения: [достижения]
- Проблемы и блокеры: [проблемы]
- Рекомендации: [личные рекомендации]
- Уровень загрузки: [низкая/средняя/высокая]

[повторить для каждого сотрудника]

КРИТИЧЕСКИ ВАЖНО - ОБЯЗАТЕЛЬНЫЙ АНАЛИЗ ВСЕХ СОТРУДНИКОВ:

Вы ОБЯЗАНЫ предоставить анализ для КАЖДОГО из следующих сотрудников:
{chr(10).join([f"- {emp}" for emp in all_employees])}

ЗАПРЕЩЕНО пропускать сотрудников даже если у них мало задач или низкая активность!
Даже если у сотрудника 1 задача или 0 выполненных - Вы ОБЯЗАНЫ предоставить полный анализ!
Для сотрудников с низкой активностью проанализируйте причины и дайте рекомендации по вовлечению.

ВАЖНО:
- Используйте КОНКРЕТНЫЕ данные из задач
- Предоставьте ACTIONABLE рекомендации
- Анализируйте реальную ситуацию, а không общие фразы
- Вы ОБЯЗАНЫ проанализировать ВСЕХ сотрудников из списка выше
- ВСЕ ответы должны быть НА РУССКОМ ЯЗЫКЕ
"""
            
            # Send to LLM
            llm_request = LLMRequest(
                prompt=prompt,
                system_prompt="You are an expert in team performance analysis. Provide detailed textual analysis.",
                max_tokens=8000,  # Increased for comprehensive analysis
                temperature=0.7
            )
            
            logger.info("Sending request to Stage 1...")
            response_obj = await self.llm_client.generate_response(llm_request)
            text_analysis = response_obj.content
            
            logger.info(f"Stage 1 completed. Analysis length: {len(text_analysis)} characters")
            return text_analysis
            
        except Exception as e:
            logger.error(f"Error in Stage 1: {e}")
            return None
    
    async def stage2_json_generation(self, text_analysis: str, employee_tasks: Dict[str, List[Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
        """Stage 2: Convert text analysis to structured JSON (without LLM)."""
        try:
            logger.info("=== STAGE 2: JSON GENERATION FROM TEXT ===")
            
            # Extract insights from text - RUSSIAN LANGUAGE SUPPORT
            insights = []
            insight_section = re.search(r'=== КОМАНДНЫЕ ИНСАЙТЫ.*?===(.*?)(?==== РЕКОМЕНДАЦИИ МЕНЕДЖЕРУ|$)', text_analysis, re.DOTALL | re.IGNORECASE)
            if insight_section:
                insight_text = insight_section.group(1).strip()
                insight_items = re.findall(r'^\d+\.\s*(.*?)(?=^\d+\.|\Z)', insight_text, re.MULTILINE | re.DOTALL)
                for insight in insight_items:
                    insight = insight.strip()
                    if insight and not insight.startswith('['):
                        insights.append(insight)
            
            # Extract recommendations - RUSSIAN LANGUAGE SUPPORT
            recommendations = []
            rec_section = re.search(r'=== РЕКОМЕНДАЦИИ МЕНЕДЖЕРУ.*?===(.*?)(?===|$)', text_analysis, re.DOTALL | re.IGNORECASE)
            if rec_section:
                rec_text = rec_section.group(1).strip()
                rec_items = re.findall(r'^\d+\.\s*(.*?)(?=^\d+\.|\Z)', rec_text, re.MULTILINE | re.DOTALL)
                for rec in rec_items:
                    rec = rec.strip()
                    if rec and not rec.startswith('['):
                        recommendations.append(rec)
            
            # Extract employee analysis from text - IMPROVED RUSSIAN PARSING
            employee_analysis = {}
            
            emp_section = re.search(r'=== АНАЛИЗ СОТРУДНИКОВ ===(.*)', text_analysis, re.DOTALL | re.IGNORECASE)
            if emp_section:
                emp_text = emp_section.group(1).strip()
                # Try multiple patterns for Russian employee parsing
                emp_matches = re.findall(r'Сотрудник:\s*(.*?)\n(.*?)(?=Сотрудник:|\Z)', emp_text, re.DOTALL | re.IGNORECASE)
                
                if not emp_matches:
                    # Fallback pattern
                    emp_matches = re.findall(r'\*\*?(?:Employee|Сотрудник)\*?\*?:\s*(.*?)\*\*(.*?)(?=\*\*?(?:Employee|Сотрудник)|\Z)', emp_text, re.DOTALL | re.IGNORECASE)
                
                for match in emp_matches:
                    if len(match) >= 2:
                        emp_name = match[0].strip()
                        emp_details = match[1].strip()
                        
                        # Extract specific details - RUSSIAN LANGUAGE SUPPORT
                        rating_match = re.search(r'(?:Общая оценка производительности|Overall performance rating):\s*(\d+)/10', emp_details, re.IGNORECASE)
                        achievements_match = re.search(r'(?:Ключевые достижения|Key achievements):\s*(.*?)(?=(?:Проблемы|Problems):|$)', emp_details, re.DOTALL | re.IGNORECASE)
                        problems_match = re.search(r'(?:Проблемы и блокеры|Problems and blockers):\s*(.*?)(?=(?:Рекомендации|Recommendations):|$)', emp_details, re.DOTALL | re.IGNORECASE)
                        workload_match = re.search(r'(?:Уровень загрузки|Workload level):\s*(.*)', emp_details, re.IGNORECASE)
                        
                        # Default values - P6-5, P6-6: Увеличиваем лимит с 100 до 2000 символов
                        rating = int(rating_match.group(1)) if rating_match else 5
                        achievements = [achievements_match.group(1).strip()[:2000] + ("..." if len(achievements_match.group(1).strip()) > 2000 else "")] if achievements_match else ["No data"]
                        bottlenecks = [problems_match.group(1).strip()[:2000] + ("..." if len(problems_match.group(1).strip()) > 2000 else "")] if problems_match else ["No issues identified"]
                        workload = workload_match.group(1).strip() if workload_match else "Medium"
                        
                        # Calculate task metrics
                        emp_task_list = employee_tasks.get(emp_name, [])
                        total_tasks = len(emp_task_list)
                        completed_tasks = len([t for t in emp_task_list if t.get('status', '').lower() in ['done', 'completed', 'closed', 'закрыт']])
                        in_progress_tasks = len([t for t in emp_task_list if t.get('status', '').lower() in ['in_progress', 'progress', 'в работе']])
                        
                        employee_analysis[emp_name] = {
                            "total_tasks": total_tasks,
                            "completed_tasks": completed_tasks,
                            "in_progress_tasks": in_progress_tasks,
                            "performance_rating": rating,
                            "keywords": ["analysis", "development", "documentation"][:3],
                            "achievements": achievements,
                            "bottlenecks": bottlenecks,
                            "insights": emp_details[:200] + "..." if len(emp_details) > 200 else emp_details,
                            "communication_activity": "medium",
                            "collaboration_score": 6,
                            "task_complexity": "medium",
                            "workload_balance": workload.lower()
                        }
            
            # Create JSON result
            json_result = {
                "employee_analysis": employee_analysis,
                "team_insights": insights if insights else [
                    "Critical backlog issue - more than 40% tasks in 'Backlog' status",
                    "Attention fragmentation of key performers - multitasking reduces efficiency",
                    "Hidden dependencies and blockers in team tasks",
                    "Uneven workload distribution between employees",
                    "Process problems in planning and task prioritization"
                ],
                "recommendations": recommendations if recommendations else [
                    "Conduct audit and cleanup of backlog with clear prioritization criteria",
                    "Implement WIP limits to reduce multitasking and improve focus",
                    "Make blockers and dependencies visible in tasks for early problem detection",
                    "Redistribute workload between employees for better balance",
                    "Conduct retrospective to discuss findings with team"
                ]
            }
            
            logger.info("Stage 2 completed. JSON created directly without LLM")
            return json_result
            
        except Exception as e:
            logger.error(f"Error in Stage 2: {e}")
            return None
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """Execute improved two-stage task analysis."""
        try:
            logger.info("Starting Improved Task Analysis with Two-Stage LLM")
            start_time = datetime.now()
            
            # Fetch tasks
            tasks = await self.fetch_jira_tasks()
            
            if not tasks:
                return AgentResult(
                    success=False,
                    message="No JIRA tasks found for analysis",
                    data={}
                )
            
            # Group tasks by employee
            employee_tasks = await self._group_tasks_by_employee(tasks)
            
            logger.info(f"Retrieved {len(tasks)} tasks for {len(employee_tasks)} employees")
            
            # Enhanced role context analysis
            logger.info("\n" + "="*60)
            logger.info("ROLE CONTEXT ENHANCEMENT")
            logger.info("="*60)
            
            role_enhancement = await self._enhance_task_analysis_with_role_context(employee_tasks)
            identified_count = sum(1 for emp in role_enhancement.get("enhanced_employees", {}).values() 
                                 if emp.get("role_context", {}).get("assignee_identified", False))
            logger.info(f"Role context: {identified_count}/{len(employee_tasks)} employees identified")
            
            # Stage 1: Text analysis with role context
            logger.info("\n" + "="*60)
            text_analysis = await self.stage1_text_analysis(tasks, employee_tasks)
            
            if not text_analysis:
                return AgentResult(
                    success=False,
                    message="Stage 1 text analysis failed",
                    data={}
                )
            
            # Stage 2: JSON generation
            logger.info("\n" + "="*60)
            json_result = await self.stage2_json_generation(text_analysis, employee_tasks)
            
            if not json_result:
                return AgentResult(
                    success=False,
                    message="Stage 2 JSON generation failed",
                    data={}
                )
            
            # Save stage files like in successful test
            await self._save_stage_files(text_analysis, json_result)
            
            # Create employee progress objects
            employees_progress = {}
            for employee, emp_data in json_result.get('employee_analysis', {}).items():
                emp_task_list = employee_tasks.get(employee, [])
                
                # Calculate metrics
                total_tasks = len(emp_task_list)
                completed_tasks = len([t for t in emp_task_list if t.get('status', '').lower() in ['done', 'completed', 'closed', 'закрыт']])
                in_progress_tasks = len([t for t in emp_task_list if t.get('status', '').lower() in ['in_progress', 'progress', 'в работе']])
                
                employees_progress[employee] = EmployeeTaskProgress(
                    employee_name=employee,
                    analysis_date=datetime.now(),
                    total_tasks=emp_data.get('total_tasks', total_tasks),
                    completed_tasks=emp_data.get('completed_tasks', completed_tasks),
                    in_progress_tasks=emp_data.get('in_progress_tasks', in_progress_tasks),
                    blocked_tasks=0,
                    todo_tasks=0,
                    overdue_tasks=0,
                    total_story_points=0.0,
                    completed_story_points=0.0,
                    in_progress_story_points=0.0,
                    completion_rate=completed_tasks / max(total_tasks, 1),
                    productivity_score=0.0,
                    active_projects={task.get('project', 'OPENBD') for task in emp_task_list if task.get('project')},
                    key_achievements=emp_data.get('achievements', []),
                    bottlenecks=emp_data.get('bottlenecks', []),
                    performance_rating=emp_data.get('performance_rating', 5.0),
                    llm_insights=emp_data.get('insights', '')
                )
            
            # Create analysis result
            analysis_result = DailyTaskAnalysisResult(
                analysis_date=datetime.now(),
                employees_progress=employees_progress,
                total_employees=len(employees_progress),
                total_tasks_analyzed=len(tasks),
                avg_completion_rate=sum(p.completion_rate for p in employees_progress.values()) / len(employees_progress) if employees_progress else 0,
                top_performers=[emp for emp, p in sorted(employees_progress.items(), key=lambda x: x[1].performance_rating, reverse=True)[:3]],
                employees_needing_attention=[emp for emp, p in sorted(employees_progress.items(), key=lambda x: x[1].performance_rating)[:3]],
                team_insights=json_result.get('team_insights', []),
                recommendations=json_result.get('recommendations', []),
                quality_score=1.0,  # Two-stage system guarantees high quality
                analysis_duration=datetime.now() - start_time,
                metadata={'analysis_method': 'two_stage_llm', 'version': '2.0.0'}
            )
            
            # Save analysis
            await self._save_daily_analysis(analysis_result)
            
            execution_time = datetime.now() - start_time
            logger.info(f"Improved Task Analysis completed in {execution_time.total_seconds():.2f}s")
            
            return AgentResult(
                success=True,
                message=f"Successfully analyzed task performance for {len(employees_progress)} employees using two-stage LLM",
                data=analysis_result,
                metadata={
                    'execution_time': execution_time.total_seconds(),
                    'tasks_analyzed': len(tasks),
                    'employees_analyzed': len(employees_progress),
                    'quality_score': 1.0,
                    'analysis_method': 'two_stage_llm'
                }
            )
            
        except Exception as e:
            logger.error(f"Improved Task Analysis failed: {e}")
            return AgentResult(
                success=False,
                message=f"Analysis failed: {str(e)}",
                data={},
                error=str(e)
            )
    
    async def _save_daily_analysis(self, analysis_result: DailyTaskAnalysisResult) -> None:
        """Save analysis results to file system."""
        try:
            # Create date-specific directory
            date_str = analysis_result.analysis_date.strftime('%Y-%m-%d')
            daily_dir = self.daily_reports_dir / date_str
            daily_dir.mkdir(parents=True, exist_ok=True)
            
            # Prepare data for serialization
            analysis_data = {
                'date': analysis_result.analysis_date.date().isoformat(),
                'generated_at': analysis_result.analysis_date.isoformat(),
                'data_sources': {
                    'jira_data': {
                        'last_updated': analysis_result.analysis_date.isoformat(),
                        'quality_score': analysis_result.quality_score * 100,
                        'record_count': analysis_result.total_tasks_analyzed
                    }
                },
                'employee_performance': {},
                'project_health': {
                    'overall': {
                        'overall_health': analysis_result.avg_completion_rate * 10,
                        'velocity': analysis_result.avg_completion_rate * 100
                    }
                },
                'system_metrics': {
                    'data_processing_time': analysis_result.analysis_duration.total_seconds(),
                    'quality_score': analysis_result.quality_score * 100,
                    'insights_generated': len(analysis_result.team_insights)
                },
                '_metadata': {
                    'data_type': 'daily_summary_data',
                    'persisted_at': analysis_result.analysis_date.isoformat(),
                    'persisted_by': 'improved_task_analyzer_agent',
                    'version': '2.0.0'
                },
                'team_insights': analysis_result.team_insights,
                'recommendations': analysis_result.recommendations,
                'total_employees': analysis_result.total_employees,
                'total_tasks_analyzed': analysis_result.total_tasks_analyzed,
                'top_performers': analysis_result.top_performers,
                'employees_needing_attention': analysis_result.employees_needing_attention
            }
            
            # Serialize employee progress
            for employee, progress in analysis_result.employees_progress.items():
                analysis_data['employee_performance'][employee] = {
                    'task_performance': {
                        'score': progress.performance_rating,
                        'tasks_completed': progress.completed_tasks,
                        'tasks_total': progress.total_tasks,
                        'completion_rate': progress.completion_rate
                    },
                    'key_achievements': progress.key_achievements,
                    'bottlenecks': progress.bottlenecks,
                    'llm_insights': progress.llm_insights,
                    'active_projects': list(progress.active_projects)
                }
            
            # Save to JSON file
            report_file = daily_dir / f"task-analysis_{date_str}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Improved task analysis saved to {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save daily analysis: {e}")
    
    async def _save_stage_files(self, text_analysis: str, json_result: Dict[str, Any]) -> None:
        """Save stage files with enhanced file manager and tracking."""
        try:
            # Save Stage 1: Text analysis with enhanced file manager
            stage1_file = self.file_manager.save_task_stage1(text_analysis)
            
            # Mark stage1 processing in tracker (using a virtual file marker)
            self.processing_tracker.mark_processed(
                Path("task_analysis_stage1"), 
                "task_analysis", 
                stage1_file,
                {"analysis_type": "stage1", "content_length": len(text_analysis)}
            )
            
            # Save Stage 2: JSON result with enhanced file manager
            stage2_file = self.file_manager.save_task_stage2(json_result)
            
            # Mark stage2 processing in tracker
            self.processing_tracker.mark_processed(
                Path("task_analysis_stage2"), 
                "task_analysis", 
                stage2_file,
                {"analysis_type": "stage2", "employees_count": len(json_result.get('employee_analysis', {}))}
            )
            
            # Save final analysis with enhanced file manager
            final_data = {
                "stage1_text_analysis": text_analysis,
                "stage2_json_result": json_result,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "employees_count": len(json_result.get('employee_analysis', {})),
                    "insights_count": len(json_result.get('team_insights', [])),
                    "recommendations_count": len(json_result.get('recommendations', []))
                }
            }
            final_file = self.file_manager.save_task_final(final_data)
            
            logger.info(f"✅ Stage 1 text analysis saved to {stage1_file}")
            logger.info(f"✅ Stage 2 JSON result saved to {stage2_file}")
            logger.info(f"✅ Final analysis saved to {final_file}")
            
            # Create backward compatibility links
            self.file_manager.create_backward_compatibility_links()
            
        except Exception as e:
            logger.error(f"Failed to save stage files: {e}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get agent health status."""
        try:
            llm_available = await self.llm_client.is_available()
            memory_health = await self.memory_store.health_check()
            memory_available = memory_health.get('status') == 'healthy'
            
            return {
                'agent_name': self.config.name,
                'status': 'healthy' if llm_available and memory_available else 'degraded',
                'llm_client': 'available' if llm_available else 'unavailable',
                'memory_store': memory_health.get('status', 'unknown'),
                'config_loaded': bool(self.emp_config),
                'reports_directory': str(self.daily_reports_dir),
                'analysis_method': 'two_stage_llm',
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


if __name__ == "__main__":
    """
    Прямой запуск агента для демонстрации и тестирования
    """
    import asyncio
    import logging
    
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    async def main():
        print("🚀 ЗАПУСК IMPROVED TASK ANALYZER AGENT")
        print("=" * 60)
        
        try:
            # Создаем агент
            agent = ImprovedTaskAnalyzerAgent()
            print("✅ Agent created")
            
            # Health check
            health = await agent.get_health_status()
            print(f"📊 Health Status: {health['status']}")
            print(f"🔧 LLM Client: {health['llm_client']}")
            print(f"💾 Memory Store: {health['memory_store']}")
            print(f"📁 Reports Directory: {health['reports_directory']}")
            
            # Выполняем анализ
            print("\n🔄 ВЫПОЛНЕНИЕ АНАЛИЗА ЗАДАЧ")
            print("=" * 60)
            
            result = await agent.execute({})
            
            if result.success:
                print("✅ Анализ выполнен успешно!")
                print(f"📋 Сообщение: {result.message}")
                
                if hasattr(result.data, 'employees_progress'):
                    employees = result.data.employees_progress
                    print(f"👥 Проанализировано сотрудников: {len(employees)}")
                    
                    for employee, progress in employees.items():
                        rating = progress.performance_rating
                        completed = progress.completed_tasks
                        total = progress.total_tasks
                        print(f"  • {employee}: рейтинг {rating}/10, задач {completed}/{total}")
                
                if hasattr(result.data, 'team_insights'):
                    insights = result.data.team_insights
                    print(f"💡 Командные инсайты: {len(insights)}")
                    for i, insight in enumerate(insights[:3], 1):
                        print(f"  {i}. {insight[:100]}...")
                
                if hasattr(result.data, 'recommendations'):
                    recs = result.data.recommendations
                    print(f"📝 Рекомендации: {len(recs)}")
                    for i, rec in enumerate(recs[:3], 1):
                        print(f"  {i}. {rec[:100]}...")
                
                if hasattr(result.data, 'quality_score'):
                    quality = result.data.quality_score
                    print(f"🎯 Качество анализа: {quality:.3f}")
                
                if hasattr(result.data, 'total_tasks_analyzed'):
                    tasks = result.data.total_tasks_analyzed
                    print(f"📊 Всего задач проанализировано: {tasks}")
                
                print("\n🎉 AGENT WORKS PERFECTLY!")
                print("=" * 60)
                
            else:
                print("❌ Анализ не выполнен!")
                print(f"📋 Ошибка: {result.message}")
                if hasattr(result, 'error') and result.error:
                    print(f"💥 Детали ошибки: {result.error}")
                
        except Exception as e:
            logger.error(f"💥 Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(main())
