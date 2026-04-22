#!/usr/bin/env python3
"""
Final Orchestrator - Объединение анализов Task Analyzer и Meeting Analyzer

Создает единый комплексный анализ на основе:
1. Анализа задач от Improved Task Analyzer Agent  
2. Анализа совещаний от Improved Meeting Analyzer Agent
3. Role Context для учета должностей
4. Финальных инсайтов и рекомендаций с учетом всех данных

Результат: Единый файл с полным анализом производительности команды
"""

import asyncio
import logging
import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from ..core.base_agent import BaseAgent, AgentConfig, AgentResult
from ..core.llm_client import LLMClient, LLMRequest
from ..core.json_memory_store import JSONMemoryStore
from ..core.quality_metrics import QualityMetrics
from ..core.config import get_employee_monitoring_config
from ..core.role_context_manager import EmployeeRoleManager
from ..core.processing_tracker import ProcessingTracker
from ..core.run_file_manager import RunFileManager
from ..agents.task_analyzer_agent_improved import ImprovedTaskAnalyzerAgent, DailyTaskAnalysisResult, EmployeeTaskProgress
from ..agents.meeting_analyzer_agent_improved import ImprovedMeetingAnalyzerAgent, ComprehensiveMeetingAnalysis, EmployeeMeetingPerformance

logger = logging.getLogger(__name__)


@dataclass
class UnifiedEmployeeAnalysis:
    """Унифицированный анализ сотрудника на основе задач и встреч."""
    employee_name: str
    analysis_date: datetime
    
    # Task metrics
    task_performance: EmployeeTaskProgress
    # Meeting performance  
    meeting_performance: EmployeeMeetingPerformance
    
    # Combined metrics
    overall_performance_score: float = 0.0
    task_meeting_correlation: float = 0.0
    consistency_score: float = 0.0
    growth_potential: float = 0.0
    
    # Unified insights
    key_strengths: List[str] = field(default_factory=list)
    development_areas: List[str] = field(default_factory=list)
    action_recommendations: List[str] = field(default_factory=list)
    
    # Role-aware recommendations
    role_specific_guidance: str = ""
    career_trajectory_insights: List[str] = field(default_factory=list)
    
    # Metadata
    confidence_level: float = 0.0
    analysis_completeness: str = "partial"  # partial, complete, comprehensive


@dataclass
class FinalUnifiedAnalysis:
    """Финальный объединенный анализ команды."""
    analysis_date: datetime
    unified_employees: Dict[str, UnifiedEmployeeAnalysis]
    
    # Source analyses
    task_analysis: Optional[DailyTaskAnalysisResult] = None
    meeting_analysis: Optional[ComprehensiveMeetingAnalysis] = None
    
    # Team-level insights
    overall_team_health: float = 0.0
    team_dynamics_score: float = 0.0
    productivity_efficiency: float = 0.0
    collaboration_quality: float = 0.0
    
    # Strategic insights
    strategic_recommendations: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    growth_opportunities: List[str] = field(default_factory=list)
    
    # Quality and metadata
    analysis_quality_score: float = 0.0
    data_sources_count: int = 0
    analysis_duration: timedelta = field(default_factory=timedelta)
    metadata: Dict[str, Any] = field(default_factory=dict)


class FinalOrchestrator(BaseAgent):
    """
    Final Orchestrator - объединяет результаты анализов в единый комплексный отчет.
    
    Процесс:
    1. Загружает результаты от Task Analyzer и Meeting Analyzer
    2. Обогащает Role Context
    3. Создает унифицированный анализ для каждого сотрудника
    4. Генерирует финальные инсайты и рекомендации
    5. Сохраняет единый файл с полным анализом
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(
            config or AgentConfig(
                name="FinalOrchestrator",
                description="Final orchestrator for unified team analysis",
                version="1.0.0"
            )
        )
        
        # Initialize components
        self.llm_client = LLMClient()
        self.memory_store = JSONMemoryStore()
        self.quality_metrics = QualityMetrics()
        self.role_manager = EmployeeRoleManager()
        self.processing_tracker = ProcessingTracker()

        project_root = Path(__file__).resolve().parents[2]
        self.run_manager = RunFileManager(project_root)
        self.run_id = self.run_manager.generate_run_id()
        self.run_paths = self.run_manager.init_run(self.run_id)
        
        # Initialize agents
        self.task_analyzer = ImprovedTaskAnalyzerAgent()
        self.meeting_analyzer = ImprovedMeetingAnalyzerAgent()
        
        # Load configuration
        self.emp_config = get_employee_monitoring_config()

        logger.info("FinalOrchestrator initialized for unified analysis")
        logger.info(f"Run id: {self.run_id}")
        logger.info(f"Run dir: {self.run_paths.run_dir}")
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Выполнить финальную орхестрацию и объединение анализов.
        """
        try:
            logger.info("Starting Final Orchestrator - Unified Analysis")
            start_time = datetime.now()
            
            # ЭТАП 1: Загрузка результатов анализов
            logger.info("\n" + "="*80)
            logger.info("ЭТАП 1: Загрузка результатов анализов")
            logger.info("="*80)
            
            task_analysis, meeting_analysis = await self._load_analysis_results()
            
            # ЭТАП 2: Обогащение Role Context
            logger.info("\n" + "="*80)
            logger.info("ЭТАП 2: Обогащение Role Context для унифицированного анализа")
            logger.info("="*80)
            
            all_employees = self._extract_all_employees(task_analysis, meeting_analysis)
            role_context = await self._enhance_unified_analysis_with_roles(all_employees)
            
            # ЭТАП 3: Создание унифицированного анализа
            logger.info("\n" + "="*80)
            logger.info("ЭТАП 3: Создание унифицированного анализа сотрудников")
            logger.info("="*80)
            
            unified_analysis = await self._create_unified_analysis(
                task_analysis, meeting_analysis, role_context
            )
            
            # ЭТАП 4: Генерация финальных инсайтов
            logger.info("\n" + "="*80)
            logger.info("ЭТАП 4: Генерация финальных инсайтов и рекомендаций")
            logger.info("="*80)
            
            final_insights = await self._generate_final_insights(unified_analysis)
            unified_analysis.strategic_recommendations = final_insights.get('strategic_recommendations', [])
            unified_analysis.risk_factors = final_insights.get('risk_factors', [])
            unified_analysis.growth_opportunities = final_insights.get('growth_opportunities', [])
            
            # ЭТАП 5: Сохранение финального анализа
            logger.info("\n" + "="*80)
            logger.info("ЭТАП 5: Сохранение финального объединенного анализа")
            logger.info("="*80)
            
            await self._save_final_unified_analysis(unified_analysis)
            
            # Calculate execution time
            execution_time = datetime.now() - start_time
            unified_analysis.analysis_duration = execution_time
            
            # Quality assessment
            unified_analysis.analysis_quality_score = self._calculate_quality_score(unified_analysis)
            
            logger.info(f"Final Orchestrator completed in {execution_time.total_seconds():.2f}s")
            logger.info(f"Unified {len(unified_analysis.unified_employees)} employees")
            logger.info(f"Overall team health: {unified_analysis.overall_team_health:.2f}/10")
            
            return AgentResult(
                success=True,
                message=f"Successfully created unified analysis for {len(unified_analysis.unified_employees)} employees",
                data=unified_analysis,
                metadata={
                    'execution_time': execution_time.total_seconds(),
                    'employees_analyzed': len(unified_analysis.unified_employees),
                    'task_analysis_available': task_analysis is not None,
                    'meeting_analysis_available': meeting_analysis is not None,
                    'role_context_enhanced': role_context is not None,
                    'quality_score': unified_analysis.analysis_quality_score,
                    'analysis_date': unified_analysis.analysis_date.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Final Orchestrator failed: {e}")
            return AgentResult(
                success=False,
                message=f"Unified analysis failed: {str(e)}",
                data={},
                error=str(e)
            )
    
    async def _load_analysis_results(self) -> Tuple[Optional[DailyTaskAnalysisResult], Optional[ComprehensiveMeetingAnalysis]]:
        """Загрузить результаты анализов от агентов."""
        task_analysis = None
        meeting_analysis = None
        
        try:
            latest_root = self.run_manager.latest_root

            task_analysis_file = latest_root / "task-analysis" / "task-analysis.json"
            if task_analysis_file.exists():
                task_analysis = await self._load_task_analysis_from_file(task_analysis_file)
                logger.info(f"✅ Task analysis loaded (latest): {len(task_analysis.employees_progress)} employees")
            else:
                logger.warning("⚠️ Task analysis not found in reports/latest, will run analyzer")
                task_result = await self.task_analyzer.execute({})
                if task_result.success:
                    task_analysis = task_result.data

            meeting_analysis_file = latest_root / "meeting-analysis" / "meeting-analysis.json"
            if meeting_analysis_file.exists():
                meeting_analysis = await self._load_meeting_analysis_from_file(meeting_analysis_file)
                logger.info(f"✅ Meeting analysis loaded (latest): {len(meeting_analysis.employees_performance)} employees")
            else:
                logger.warning("⚠️ Meeting analysis not found in reports/latest, will run analyzer")
                meeting_result = await self.meeting_analyzer.execute({})
                if meeting_result.success:
                    meeting_analysis = meeting_result.data
            
        except Exception as e:
            logger.error(f"Failed to load analysis results: {e}")
        
        return task_analysis, meeting_analysis
    
    async def _load_task_analysis_from_file(self, file_path: Path) -> DailyTaskAnalysisResult:
        """Загрузить анализ задач из файла."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Преобразование данных в объекты
        employees_progress = {}
        for emp_name, emp_data in data.get('employee_performance', {}).items():
            task_perf = emp_data.get('task_performance', {})
            
            employees_progress[emp_name] = EmployeeTaskProgress(
                employee_name=emp_name,
                analysis_date=datetime.fromisoformat(data.get('date', datetime.now().isoformat())),
                total_tasks=task_perf.get('tasks_total', 0),
                completed_tasks=task_perf.get('tasks_completed', 0),
                in_progress_tasks=0,  # Будет вычислено
                blocked_tasks=0,
                todo_tasks=0,
                overdue_tasks=0,
                total_story_points=0.0,
                completed_story_points=0.0,
                in_progress_story_points=0.0,
                completion_rate=task_perf.get('completion_rate', 0.0),
                productivity_score=task_perf.get('score', 0.0),
                active_projects=set(),
                key_achievements=emp_data.get('key_achievements', []),
                bottlenecks=emp_data.get('bottlenecks', []),
                performance_rating=task_perf.get('score', 5.0),
                llm_insights=emp_data.get('llm_insights', '')
            )
        
        return DailyTaskAnalysisResult(
            analysis_date=datetime.fromisoformat(data.get('date', datetime.now().isoformat())),
            employees_progress=employees_progress,
            total_employees=data.get('total_employees', len(employees_progress)),
            total_tasks_analyzed=data.get('total_tasks_analyzed', 0),
            avg_completion_rate=data.get('employee_performance', {}).get('overall', {}).get('completion_rate', 0.0),
            top_performers=data.get('top_performers', []),
            employees_needing_attention=data.get('employees_needing_attention', []),
            team_insights=data.get('team_insights', []),
            recommendations=data.get('recommendations', []),
            quality_score=data.get('system_metrics', {}).get('quality_score', 0.0) / 100,
            analysis_duration=timedelta(),
            metadata=data.get('_metadata', {})
        )
    
    async def _load_meeting_analysis_from_file(self, file_path: Path) -> ComprehensiveMeetingAnalysis:
        """Загрузить анализ совещаний из файла."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Преобразование данных в объекты
        employees_performance = {}
        personal_insights = data.get('personal_insights', {})
        
        latest_run_id_path = self.run_manager.latest_root / "run_id.txt"
        run_dir: Optional[Path] = None
        if latest_run_id_path.exists():
            run_id = latest_run_id_path.read_text(encoding="utf-8").strip()
            run_dir = self.run_manager.runs_root / run_id

        for emp_name in personal_insights.keys():
            detailed_data = {}
            if run_dir:
                safe_filename = emp_name.replace(" ", "_")
                progression_file = run_dir / "employee_progression" / f"{safe_filename}.json"
                if not progression_file.exists():
                    # fallback: пытались сохранить без пробелов/служебных символов
                    safe_filename = re.sub(r"[^\w\s-]", "", emp_name).strip()
                    safe_filename = re.sub(r"[-\s]+", "_", safe_filename)
                    progression_file = run_dir / "employee_progression" / f"{safe_filename}.json"
                if progression_file.exists():
                    with open(progression_file, "r", encoding="utf-8") as f:
                        detailed_data = json.load(f)
            
            employees_performance[emp_name] = EmployeeMeetingPerformance(
                employee_name=emp_name,
                analysis_date=datetime.fromisoformat(data.get('analysis_date', datetime.now().isoformat())),
                speaking_turns=detailed_data.get('speaking_turns', 0),
                questions_asked=detailed_data.get('questions_asked', 0),
                suggestions_made=detailed_data.get('suggestions_made', 0),
                action_items_assigned=detailed_data.get('action_items_assigned', 0),
                engagement_level=detailed_data.get('engagement_level', 'medium'),
                leadership_indicators=detailed_data.get('leadership_indicators', []),
                task_to_meeting_correlation=detailed_data.get('task_to_meeting_correlation', 0.5),
                overall_consistency=detailed_data.get('overall_consistency', 0.7),
                communication_effectiveness=detailed_data.get('communication_effectiveness', 5.0),
                detailed_insights=detailed_data.get('detailed_insights', ''),
                performance_rating=detailed_data.get('performance_rating', 5.0)
            )
        
        return ComprehensiveMeetingAnalysis(
            analysis_date=datetime.fromisoformat(data.get('analysis_date', datetime.now().isoformat())),
            employees_performance=employees_performance,
            total_employees=len(employees_performance),
            total_meetings_analyzed=data.get('total_meetings_analyzed', 0),
            total_tasks_analyzed=data.get('total_tasks_analyzed', 0),
            team_collaboration_score=data.get('team_collaboration_score', 0.0),
            task_meeting_alignment=data.get('task_meeting_alignment', 0.0),
            overall_team_health=data.get('overall_team_health', 0.0),
            team_insights=data.get('team_insights', []),
            personal_insights=personal_insights,
            recommendations=data.get('recommendations', []),
            quality_score=data.get('quality_score', 0.0),
            analysis_duration=timedelta(seconds=data.get('analysis_duration_seconds', 0)),
            metadata=data.get('metadata', {})
        )
    
    def _extract_all_employees(self, task_analysis: Optional[DailyTaskAnalysisResult], 
                             meeting_analysis: Optional[ComprehensiveMeetingAnalysis]) -> List[str]:
        """Извлечь всех сотрудников из анализов."""
        employees = set()
        
        if task_analysis:
            employees.update(task_analysis.employees_progress.keys())
        
        if meeting_analysis:
            employees.update(meeting_analysis.employees_performance.keys())
        
        return list(employees)
    
    async def _enhance_unified_analysis_with_roles(self, employees: List[str]) -> Dict[str, Any]:
        """Обогатить унифицированный анализ Role Context."""
        try:
            # Используем role context manager для обогащения
            role_enhancement = self.role_manager.enhance_team_analysis(employees)
            
            logger.info(f"Role context enhancement: {role_enhancement['identification_rate']:.2%} employees identified")
            
            return role_enhancement
            
        except Exception as e:
            logger.error(f"Failed to enhance unified analysis with role context: {e}")
            return {
                "total_employees": len(employees),
                "identified_employees": [],
                "unidentified_employees": employees,
                "identification_rate": 0.0,
                "employee_contexts": {}
            }
    
    async def _create_unified_analysis(self, task_analysis: Optional[DailyTaskAnalysisResult],
                                     meeting_analysis: Optional[ComprehensiveMeetingAnalysis], 
                                     role_context: Dict[str, Any]) -> FinalUnifiedAnalysis:
        """Создать унифицированный анализ на основе всех данных."""
        try:
            analysis_date = datetime.now()
            unified_employees = {}
            
            # Получаем всех сотрудников
            all_employees = self._extract_all_employees(task_analysis, meeting_analysis)
            
            for employee_name in all_employees:
                # Получаем данные из анализов
                task_perf = task_analysis.employees_progress.get(employee_name) if task_analysis else None
                meeting_perf = meeting_analysis.employees_performance.get(employee_name) if meeting_analysis else None
                
                # Создаем заглушки если данных нет
                if not task_perf:
                    task_perf = EmployeeTaskProgress(
                        employee_name=employee_name,
                        analysis_date=analysis_date,
                        total_tasks=0,
                        completed_tasks=0,
                        in_progress_tasks=0,
                        blocked_tasks=0,
                        todo_tasks=0,
                        overdue_tasks=0,
                        total_story_points=0.0,
                        completed_story_points=0.0,
                        in_progress_story_points=0.0,
                        completion_rate=0.0,
                        productivity_score=0.0,
                        performance_rating=5.0
                    )
                
                if not meeting_perf:
                    meeting_perf = EmployeeMeetingPerformance(
                        employee_name=employee_name,
                        analysis_date=analysis_date,
                        speaking_turns=0,
                        questions_asked=0,
                        suggestions_made=0,
                        action_items_assigned=0,
                        engagement_level='unknown',
                        performance_rating=5.0
                    )
                
                # Создаем унифицированный анализ
                unified_analysis = await self._create_employee_unified_analysis(
                    employee_name, task_perf, meeting_perf, role_context
                )
                
                unified_employees[employee_name] = unified_analysis
            
            # Вычисляем командные метрики
            overall_team_health = self._calculate_team_health(unified_employees)
            team_dynamics_score = self._calculate_team_dynamics(unified_employees, task_analysis, meeting_analysis)
            productivity_efficiency = self._calculate_productivity_efficiency(unified_employees)
            collaboration_quality = self._calculate_collaboration_quality(unified_employees)
            
            # Считаем источники данных
            data_sources_count = 0
            if task_analysis:
                data_sources_count += 1
            if meeting_analysis:
                data_sources_count += 1
            if role_context:
                data_sources_count += 1
            
            return FinalUnifiedAnalysis(
                analysis_date=analysis_date,
                unified_employees=unified_employees,
                task_analysis=task_analysis,
                meeting_analysis=meeting_analysis,
                overall_team_health=overall_team_health,
                team_dynamics_score=team_dynamics_score,
                productivity_efficiency=productivity_efficiency,
                collaboration_quality=collaboration_quality,
                data_sources_count=data_sources_count,
                metadata={
                    'sources_used': {
                        'task_analysis': task_analysis is not None,
                        'meeting_analysis': meeting_analysis is not None,
                        'role_context': role_context is not None
                    },
                    'total_employees': len(unified_employees),
                    'analysis_completeness': 'comprehensive' if data_sources_count == 3 else 'partial'
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create unified analysis: {e}")
            # Возвращаем минимальный анализ
            return FinalUnifiedAnalysis(
                analysis_date=datetime.now(),
                unified_employees={},
                data_sources_count=0,
                metadata={'error': str(e)}
            )
    
    async def _create_employee_unified_analysis(self, employee_name: str,
                                               task_perf: EmployeeTaskProgress,
                                               meeting_perf: EmployeeMeetingPerformance,
                                               role_context: Dict[str, Any]) -> UnifiedEmployeeAnalysis:
        """Создать унифицированный анализ для конкретного сотрудника."""
        try:
            # Получаем Role Context для сотрудника
            employee_role = role_context.get('employee_contexts', {}).get(employee_name, {})
            
            # Вычисляем объединенные метрики
            overall_performance_score = (task_perf.performance_rating + meeting_perf.performance_rating) / 2
            task_meeting_correlation = 0.5  # Будет вычислено на основе корреляции
            
            if task_perf.completion_rate > 0 and meeting_perf.communication_effectiveness > 0:
                task_meeting_correlation = min(1.0, task_perf.completion_rate * meeting_perf.communication_effectiveness / 50)
            
            consistency_score = abs(task_perf.performance_rating - meeting_perf.performance_rating)
            consistency_score = 1.0 - (consistency_score / 10.0)  # Инвертируем для consistency
            
            growth_potential = 0.7  # Будет уточнено через LLM
            
            # Формируем инсайты
            key_strengths = []
            development_areas = []
            action_recommendations = []
            
            # Анализируем сильные стороны
            if task_perf.completion_rate > 0.8:
                key_strengths.append("Высокая эффективность выполнения задач")
            
            if meeting_perf.communication_effectiveness > 7.0:
                key_strengths.append("Эффективная коммуникация на встречах")
            
            if meeting_perf.engagement_level == 'high':
                key_strengths.append("Активное участие в командных процессах")
            
            # Анализируем зоны развития
            if task_perf.completion_rate < 0.5:
                development_areas.append("Нуждается в улучшении выполнения задач")
            
            if meeting_perf.communication_effectiveness < 5.0:
                development_areas.append("Требуется развитие коммуникационных навыков")
            
            if task_perf.bottlenecks and len(task_perf.bottlenecks) > 0:
                development_areas.append(f"Проблемы: {task_perf.bottlenecks[0][:100]}...")
            
            # Генерируем рекомендации
            if overall_performance_score < 6.0:
                action_recommendations.append("Рекомендуется дополнительное обучение и менторство")
            
            if task_meeting_correlation < 0.5:
                action_recommendations.append("Улучшить координацию между задачами и участием в встречах")
            
            # Role-aware рекомендации
            role_specific_guidance = ""
            if employee_role.get('assignee_identified'):
                role_level = employee_role.get('role_level', 'Unknown')
                if 'Product Owner' in role_level:
                    role_specific_guidance = "Фокусироваться на управлении продуктом, приоритизации и коммуникации с командой"
                elif 'Разработчик' in role_level:
                    role_specific_guidance = "Развивать технические навыки, участвовать в code review, делиться знаниями"
                elif 'Team Lead' in role_level:
                    role_specific_guidance = "Развивать лидерские качества, менторить команду, оптимизировать процессы"
                else:
                    role_specific_guidance = "Продолжать развитие в текущей должности, изучать лучшие практики"
            
            # Career trajectory insights
            career_trajectory_insights = []
            if overall_performance_score > 8.0:
                career_trajectory_insights.append("Лидер команды, готов к повышению ответственности")
            elif overall_performance_score > 6.0:
                career_trajectory_insights.append("Стабильный сотрудник с потенциалом роста")
            else:
                career_trajectory_insights.append("Требует поддержки и развития для достижения стабильной производительности")
            
            return UnifiedEmployeeAnalysis(
                employee_name=employee_name,
                analysis_date=datetime.now(),
                task_performance=task_perf,
                meeting_performance=meeting_perf,
                overall_performance_score=overall_performance_score,
                task_meeting_correlation=task_meeting_correlation,
                consistency_score=consistency_score,
                growth_potential=growth_potential,
                key_strengths=key_strengths,
                development_areas=development_areas,
                action_recommendations=action_recommendations,
                role_specific_guidance=role_specific_guidance,
                career_trajectory_insights=career_trajectory_insights,
                confidence_level=0.8 if role_context.get('identification_rate', 0) > 0.5 else 0.6,
                analysis_completeness='comprehensive' if task_perf and meeting_perf else 'partial'
            )
            
        except Exception as e:
            logger.error(f"Failed to create employee unified analysis for {employee_name}: {e}")
            return UnifiedEmployeeAnalysis(
                employee_name=employee_name,
                analysis_date=datetime.now(),
                task_performance=task_perf,
                meeting_performance=meeting_perf,
                overall_performance_score=5.0,
                confidence_level=0.3,
                analysis_completeness='minimal',
                metadata={'error': str(e)}
            )
    
    def _calculate_team_health(self, unified_employees: Dict[str, UnifiedEmployeeAnalysis]) -> float:
        """Рассчитать общее здоровье команды."""
        if not unified_employees:
            return 0.0
        
        total_score = sum(emp.overall_performance_score for emp in unified_employees.values())
        return total_score / len(unified_employees)
    
    def _calculate_team_dynamics(self, unified_employees: Dict[str, UnifiedEmployeeAnalysis],
                                task_analysis: Optional[DailyTaskAnalysisResult],
                                meeting_analysis: Optional[ComprehensiveMeetingAnalysis]) -> float:
        """Рассчитать командную динамику."""
        if not unified_employees:
            return 0.0
        
        # Базовая оценка на основе consistency
        avg_consistency = sum(emp.consistency_score for emp in unified_employees.values()) / len(unified_employees)
        
        # Добавим факторы из исходных анализов
        additional_factors = 0.0
        if task_analysis and hasattr(task_analysis, 'quality_score'):
            additional_factors += task_analysis.quality_score * 0.3
        
        if meeting_analysis and hasattr(meeting_analysis, 'team_collaboration_score'):
            additional_factors += (meeting_analysis.team_collaboration_score / 10) * 0.3
        
        return min(10.0, avg_consistency * 10 + additional_factors)
    
    def _calculate_productivity_efficiency(self, unified_employees: Dict[str, UnifiedEmployeeAnalysis]) -> float:
        """Рассчитать эффективность продуктивности."""
        if not unified_employees:
            return 0.0
        
        # Основано на task performance
        task_scores = []
        for emp in unified_employees.values():
            if emp.task_performance and emp.task_performance.completion_rate > 0:
                task_scores.append(emp.task_performance.completion_rate * 10)
        
        if not task_scores:
            return 5.0  # Среднее значение если нет данных
        
        return sum(task_scores) / len(task_scores)
    
    def _calculate_collaboration_quality(self, unified_employees: Dict[str, UnifiedEmployeeAnalysis]) -> float:
        """Рассчитать качество сотрудничества."""
        if not unified_employees:
            return 0.0
        
        # Основано на meeting performance
        meeting_scores = []
        for emp in unified_employees.values():
            if emp.meeting_performance:
                meeting_scores.append(emp.meeting_performance.communication_effectiveness)
        
        if not meeting_scores:
            return 5.0  # Среднее значение если нет данных
        
        return sum(meeting_scores) / len(meeting_scores)
    
    async def _generate_final_insights(self, unified_analysis: FinalUnifiedAnalysis) -> Dict[str, List[str]]:
        """Генерировать финальные инсайты с помощью LLM."""
        try:
            # Подготавливаем данные для LLM
            employees_summary = []
            for emp_name, emp_unified in unified_analysis.unified_employees.items():
                summary = f"""
                Сотрудник: {emp_name}
                Общая оценка: {emp_unified.overall_performance_score:.1f}/10
                Корреляция задач и встреч: {emp_unified.task_meeting_correlation:.2f}
                Сильные стороны: {', '.join(emp_unified.key_strengths)}
                Зоны развития: {', '.join(emp_unified.development_areas)}
                Рекомендации: {', '.join(emp_unified.action_recommendations)}
                """
                employees_summary.append(summary)
            
            role_context_text = self._format_role_context_for_insights(unified_analysis.metadata.get('sources_used', {}))
            
            prompt = f"""
                Ты - СТРАТЕГИЧЕСКИЙ АНАЛИТИК КОМАНДЫ. Проанализируй унифицированные данные и предоставь стратегические инсайты НА РУССКОМ ЯЗЫКЕ.
                
                {role_context_text}
                
                УНИФИЦИРОВАННЫЙ АНАЛИЗ КОМАНДЫ:
                
                Общее здоровье команды: {unified_analysis.overall_team_health:.2f}/10
                Командная динамика: {unified_analysis.team_dynamics_score:.2f}/10
                Эффективность продуктивности: {unified_analysis.productivity_efficiency:.2f}/10
                Качество сотрудничества: {unified_analysis.collaboration_quality:.2f}/10
                
                АНАЛИЗ СОТРУДНИКОВ:
                {chr(10).join(employees_summary)}
                
                ПРЕДОСТАВЬ АНАЛИЗ:
                
                === СТРАТЕГИЧЕСКИЕ РЕКОМЕНДАЦИИ (минимум 4) ===
                1. [Рекомендация по развитию команды]
                2. [Рекомендация по оптимизации процессов]
                3. [Рекомендация по управлению талантами]
                4. [Рекомендация по улучшению производительности]
                
                === ФАКТОРЫ РИСКА (минимум 3) ===
                1. [Potential risk factor]
                2. [Another risk factor]
                3. [Additional risk factor]
                
                === ВОЗМОЖНОСТИ РОСТА (минимум 3) ===
                1. [Growth opportunity for team]
                2. [Individual development opportunity]
                3. [Process improvement opportunity]
                
                ВАЖНО:
                - Используй КОНКРЕТНЫЕ данные из анализа
                - Предоставляй ACTIONABLE рекомендации
                - Учитывай сильные и слабые стороны каждого сотрудника
                - Инсайты должны быть НА РУССКОМ языке
                """
            
            llm_request = LLMRequest(
                prompt=prompt,
                system_prompt="Ты - стратегический аналитик команды. Предоставляй глубокие, основанные на данных инсайты.",
                max_tokens=3000,
                temperature=0.5
            )
            
            response = await self.llm_client.generate_response(llm_request)
            insights_text = response.content
            
            # Извлекаем структурированные данные
            insights = self._extract_insights_from_text(insights_text)
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate final insights: {e}")
            return {
                'strategic_recommendations': ['Проверить качество исходных данных анализа'],
                'risk_factors': ['Отсутствуют данные для оценки рисков'],
                'growth_opportunities': ['Требуется дополнительный анализ возможностей']
            }
    
    def _format_role_context_for_insights(self, sources_used: Dict[str, bool]) -> str:
        """Форматировать Role Context для инсайтов."""
        try:
            context_parts = []
            
            if sources_used.get('role_context', False):
                context_parts.append("=== КОНТЕКСТ РОЛЕЙ И ДОЛЖНОСТЕЙ ===")
                context_parts.append("Анализ учитывает должности и роли сотрудников при формировании рекомендаций")
                context_parts.append("Рекомендации адаптированы под уровень ответственности и специализацию")
                context_parts.append("")
            
            if sources_used.get('task_analysis', False):
                context_parts.append("=== АНАЛИЗ ЗАДАЧ ===")
                context_parts.append("Включены данные о выполнении задач, продуктивности и достижениях")
                context_parts.append("")
            
            if sources_used.get('meeting_analysis', False):
                context_parts.append("=== АНАЛИЗ ВСТРЕЧ ===")
                context_parts.append("Включены данные об участии в совещаниях и коммуникационной эффективности")
                context_parts.append("")
            
            if not any(sources_used.values()):
                context_parts.append("=== ОГРАНИЧЕННЫЕ ДАННЫЕ ===")
                context_parts.append("Анализ основан на ограниченном наборе данных")
                context_parts.append("")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Failed to format role context for insights: {e}")
            return "=== КОНТЕКСТ АНАЛИЗА ===\nОшибка форматирования контекста\n"
    
    def _extract_insights_from_text(self, text: str) -> Dict[str, List[str]]:
        """Извлечь инсайты из текстового ответа LLM."""
        try:
            insights = {
                'strategic_recommendations': [],
                'risk_factors': [],
                'growth_opportunities': []
            }
            
            # Извлекаем стратегические рекомендации
            rec_match = re.search(r'=== СТРАТЕГИЧЕСКИЕ РЕКОМЕНДАЦИИ.*?(?===|\Z)(.*)', text, re.DOTALL | re.IGNORECASE)
            if rec_match:
                rec_items = re.findall(r'\d+\.\s*([^\n]+)', rec_match.group(1))
                insights['strategic_recommendations'] = [item.strip() for item in rec_items[:4]]
            
            # Извлекаем факторы риска
            risk_match = re.search(r'=== ФАКТОРЫ РИСКА.*?(?===|\Z)(.*)', text, re.DOTALL | re.IGNORECASE)
            if risk_match:
                risk_items = re.findall(r'\d+\.\s*([^\n]+)', risk_match.group(1))
                insights['risk_factors'] = [item.strip() for item in risk_items[:3]]
            
            # Извлекаем возможности роста
            growth_match = re.search(r'=== ВОЗМОЖНОСТИ РОСТА.*?(?===|\Z)(.*)', text, re.DOTALL | re.IGNORECASE)
            if growth_match:
                growth_items = re.findall(r'\d+\.\s*([^\n]+)', growth_match.group(1))
                insights['growth_opportunities'] = [item.strip() for item in growth_items[:3]]
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to extract insights from text: {e}")
            return {
                'strategic_recommendations': ['Ошибка извлечения рекомендаций'],
                'risk_factors': ['Ошибка извлечения рисков'],
                'growth_opportunities': ['Ошибка извлечения возможностей']
            }
    
    async def _save_final_unified_analysis(self, unified_analysis: FinalUnifiedAnalysis) -> None:
        """Сохранить финальный объединенный анализ."""
        try:
            unified_dir = self.run_paths.run_dir / "unified-analysis"
            unified_dir.mkdir(parents=True, exist_ok=True)
            
            # Сохраняем основной файл
            analysis_data = {
                'analysis_date': unified_analysis.analysis_date.isoformat(),
                'analysis_type': 'final_unified_analysis',
                'team_metrics': {
                    'overall_team_health': unified_analysis.overall_team_health,
                    'team_dynamics_score': unified_analysis.team_dynamics_score,
                    'productivity_efficiency': unified_analysis.productivity_efficiency,
                    'collaboration_quality': unified_analysis.collaboration_quality
                },
                'strategic_insights': {
                    'strategic_recommendations': unified_analysis.strategic_recommendations,
                    'risk_factors': unified_analysis.risk_factors,
                    'growth_opportunities': unified_analysis.growth_opportunities
                },
                'employees_analysis': {},
                'quality_metrics': {
                    'analysis_quality_score': unified_analysis.analysis_quality_score,
                    'data_sources_count': unified_analysis.data_sources_count,
                    'analysis_duration_seconds': unified_analysis.analysis_duration.total_seconds()
                },
                'metadata': unified_analysis.metadata
            }
            
            # Сериализуем анализ сотрудников
            for emp_name, emp_unified in unified_analysis.unified_employees.items():
                analysis_data['employees_analysis'][emp_name] = {
                    'overall_performance_score': emp_unified.overall_performance_score,
                    'task_meeting_correlation': emp_unified.task_meeting_correlation,
                    'consistency_score': emp_unified.consistency_score,
                    'growth_potential': emp_unified.growth_potential,
                    'key_strengths': emp_unified.key_strengths,
                    'development_areas': emp_unified.development_areas,
                    'action_recommendations': emp_unified.action_recommendations,
                    'role_specific_guidance': emp_unified.role_specific_guidance,
                    'career_trajectory_insights': emp_unified.career_trajectory_insights,
                    'confidence_level': emp_unified.confidence_level,
                    'analysis_completeness': emp_unified.analysis_completeness,
                    'task_performance_metrics': {
                        'performance_rating': emp_unified.task_performance.performance_rating,
                        'completion_rate': emp_unified.task_performance.completion_rate,
                        'total_tasks': emp_unified.task_performance.total_tasks,
                        'completed_tasks': emp_unified.task_performance.completed_tasks
                    },
                    'meeting_performance_metrics': {
                        'performance_rating': emp_unified.meeting_performance.performance_rating,
                        'communication_effectiveness': emp_unified.meeting_performance.communication_effectiveness,
                        'engagement_level': emp_unified.meeting_performance.engagement_level
                    }
                }
            
            # Сохраняем основной файл
            main_file = unified_dir / "unified-analysis.json"
            self.run_manager.save_json(main_file, analysis_data)

            # Сохраняем TXT отчет
            await self._save_unified_report_txt(unified_analysis, unified_dir)

            # latest
            self.run_manager.set_latest(self.run_id)
            self.run_manager.copy_to_latest(main_file, Path("unified-analysis") / "unified-analysis.json")
            txt_path = unified_dir / "unified-report.txt"
            if txt_path.exists():
                self.run_manager.copy_to_latest(txt_path, Path("unified-analysis") / "unified-report.txt")
            
            # Отмечаем в processing tracker
            self.processing_tracker.mark_processed(
                main_file,
                "final_unified_analysis",
                main_file,
                {
                    "analysis_type": "final_unified",
                    "employees_analyzed": len(unified_analysis.unified_employees),
                    "quality_score": unified_analysis.analysis_quality_score,
                    "data_sources": unified_analysis.data_sources_count
                }
            )
            
            logger.info(f"✅ Final unified analysis saved to {main_file}")
            logger.info(f"📊 Analyzed {len(unified_analysis.unified_employees)} employees")
            logger.info(f"🎯 Quality score: {unified_analysis.analysis_quality_score:.3f}")
            
        except Exception as e:
            logger.error(f"Failed to save final unified analysis: {e}")
    
    async def _save_unified_report_txt(self, unified_analysis: FinalUnifiedAnalysis, output_dir: Path) -> None:
        """Сохранить унифицированный отчет в TXT формате."""
        try:
            report_file = output_dir / "unified-report.txt"
            
            report_lines = []
            report_lines.append("ФИНАЛЬНЫЙ ОБЪЕДИНЕННЫЙ АНАЛИЗ КОМАНДЫ")
            report_lines.append("=" * 80)
            report_lines.append(f"Дата анализа: {unified_analysis.analysis_date.strftime('%d.%m.%Y %H:%M')}")
            report_lines.append(f"Качество анализа: {unified_analysis.analysis_quality_score:.3f}")
            report_lines.append(f"Источников данных: {unified_analysis.data_sources_count}")
            report_lines.append(f"Сотрудников проанализировано: {len(unified_analysis.unified_employees)}")
            report_lines.append("")
            
            # Командные метрики
            report_lines.append("ОБЩИЕ МЕТРИКИ КОМАНДЫ")
            report_lines.append("-" * 40)
            report_lines.append(f"Общее здоровье команды: {unified_analysis.overall_team_health:.2f}/10")
            report_lines.append(f"Командная динамика: {unified_analysis.team_dynamics_score:.2f}/10")
            report_lines.append(f"Эффективность продуктивности: {unified_analysis.productivity_efficiency:.2f}/10")
            report_lines.append(f"Качество сотрудничества: {unified_analysis.collaboration_quality:.2f}/10")
            report_lines.append("")
            
            # Стратегические рекомендации
            if unified_analysis.strategic_recommendations:
                report_lines.append("СТРАТЕГИЧЕСКИЕ РЕКОМЕНДАЦИИ")
                report_lines.append("-" * 40)
                for i, rec in enumerate(unified_analysis.strategic_recommendations, 1):
                    report_lines.append(f"{i}. {rec}")
                report_lines.append("")
            
            # Факторы риска
            if unified_analysis.risk_factors:
                report_lines.append("ФАКТОРЫ РИСКА")
                report_lines.append("-" * 40)
                for i, risk in enumerate(unified_analysis.risk_factors, 1):
                    report_lines.append(f"{i}. {risk}")
                report_lines.append("")
            
            # Возможности роста
            if unified_analysis.growth_opportunities:
                report_lines.append("ВОЗМОЖНОСТИ РОСТА")
                report_lines.append("-" * 40)
                for i, opportunity in enumerate(unified_analysis.growth_opportunities, 1):
                    report_lines.append(f"{i}. {opportunity}")
                report_lines.append("")
            
            # Анализ сотрудников
            report_lines.append("АНАЛИЗ СОТРУДНИКОВ")
            report_lines.append("-" * 40)
            report_lines.append("")
            
            for emp_name, emp_unified in sorted(unified_analysis.unified_employees.items()):
                report_lines.append(f"СОТРУДНИК: {emp_name}")
                report_lines.append(f"Общая оценка: {emp_unified.overall_performance_score:.1f}/10")
                report_lines.append(f"Корреляция задач и встреч: {emp_unified.task_meeting_correlation:.2f}")
                report_lines.append(f"Уровень уверенности: {emp_unified.confidence_level:.2f}")
                report_lines.append("")
                
                if emp_unified.key_strengths:
                    report_lines.append("Сильные стороны:")
                    for strength in emp_unified.key_strengths:
                        report_lines.append(f"  • {strength}")
                    report_lines.append("")
                
                if emp_unified.development_areas:
                    report_lines.append("Зоны развития:")
                    for area in emp_unified.development_areas:
                        report_lines.append(f"  • {area}")
                    report_lines.append("")
                
                if emp_unified.role_specific_guidance:
                    report_lines.append("Рекомендации по должности:")
                    report_lines.append(f"  {emp_unified.role_specific_guidance}")
                    report_lines.append("")
                
                if emp_unified.action_recommendations:
                    report_lines.append("Действия:")
                    for action in emp_unified.action_recommendations:
                        report_lines.append(f"  • {action}")
                    report_lines.append("")
                
                report_lines.append("-" * 60)
                report_lines.append("")
            
            # Сохраняем TXT файл
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            
            logger.info(f"✅ Unified report saved to {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save unified report TXT: {e}")
    
    def _calculate_quality_score(self, unified_analysis: FinalUnifiedAnalysis) -> float:
        """Рассчитать общее качество анализа."""
        try:
            quality_factors = []
            
            # Оценка покрытия сотрудников
            if unified_analysis.unified_employees:
                completeness_scores = []
                for emp in unified_analysis.unified_employees.values():
                    if emp.analysis_completeness == 'comprehensive':
                        completeness_scores.append(1.0)
                    elif emp.analysis_completeness == 'partial':
                        completeness_scores.append(0.7)
                    else:  # minimal
                        completeness_scores.append(0.3)
                
                avg_completeness = sum(completeness_scores) / len(completeness_scores)
                quality_factors.append(avg_completeness)
            
            # Оценка источников данных
            data_source_factor = min(1.0, unified_analysis.data_sources_count / 3.0)
            quality_factors.append(data_source_factor)
            
            # Оценка стратегических инсайтов
            insights_count = (len(unified_analysis.strategic_recommendations) + 
                            len(unified_analysis.risk_factors) + 
                            len(unified_analysis.growth_opportunities))
            
            expected_insights = 10  # 4 + 3 + 3
            insights_factor = min(1.0, insights_count / expected_insights)
            quality_factors.append(insights_factor)
            
            # Оценка командных метрик
            if unified_analysis.overall_team_health > 0:
                team_health_factor = min(1.0, unified_analysis.overall_team_health / 8.0)
                quality_factors.append(team_health_factor)
            
            return sum(quality_factors) / len(quality_factors) if quality_factors else 0.0
            
        except Exception as e:
            logger.error(f"Failed to calculate quality score: {e}")
            return 0.5  # Среднее значение при ошибке
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Проверить состояние Final Orchestrator."""
        try:
            llm_available = await self.llm_client.is_available()
            
            return {
                'agent_name': self.config.name,
                'status': 'healthy' if llm_available else 'degraded',
                'llm_client': 'available' if llm_available else 'unavailable',
                'task_analyzer': 'available',
                'meeting_analyzer': 'available',
                'role_manager': 'available',
                "reports_directory": str(self.run_manager.latest_root),
                'unified_analysis_ready': True,
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
    Прямой запуск Final Orchestrator для демонстрации и тестирования
    """
    import asyncio
    import logging
    
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    async def main():
        print("🚀 ЗАПУСК FINAL ORCHESTRATOR")
        print("=" * 60)
        
        try:
            # Создаем orchestrator
            orchestrator = FinalOrchestrator()
            print("✅ Final Orchestrator created")
            
            # Health check
            health = await orchestrator.get_health_status()
            print(f"📊 Health Status: {health['status']}")
            print(f"🔧 LLM Client: {health['llm_client']}")
            print(f"📁 Reports Directory: {health['reports_directory']}")
            print(f"🔄 Unified Analysis Ready: {health['unified_analysis_ready']}")
            
            # Выполняем объединенный анализ
            print("\n🔄 ВЫПОЛНЕНИЕ ФИНАЛЬНОГО ОБЪЕДИНЕННОГО АНАЛИЗА")
            print("=" * 60)
            
            result = await orchestrator.execute({})
            
            if result.success:
                print("✅ Объединенный анализ выполнен успешно!")
                print(f"📋 Сообщение: {result.message}")
                
                analysis_data = result.data
                
                print(f"👥 Проанализировано сотрудников: {len(analysis_data.unified_employees)}")
                print(f"🎯 Общее здоровье команды: {analysis_data.overall_team_health:.2f}/10")
                print(f"📊 Качество анализа: {analysis_data.analysis_quality_score:.3f}")
                print(f"🔄 Источников данных: {analysis_data.data_sources_count}")
                
                if analysis_data.strategic_recommendations:
                    print(f"📝 Стратегических рекомендаций: {len(analysis_data.strategic_recommendations)}")
                    for i, rec in enumerate(analysis_data.strategic_recommendations[:3], 1):
                        print(f"  {i}. {rec[:80]}...")
                
                if analysis_data.risk_factors:
                    print(f"⚠️ Факторов риска: {len(analysis_data.risk_factors)}")
                    for i, risk in enumerate(analysis_data.risk_factors[:2], 1):
                        print(f"  {i}. {risk[:80]}...")
                
                if analysis_data.growth_opportunities:
                    print(f"📈 Возможностей роста: {len(analysis_data.growth_opportunities)}")
                    for i, opp in enumerate(analysis_data.growth_opportunities[:2], 1):
                        print(f"  {i}. {opp[:80]}...")
                
                print(f"⏱️ Время выполнения: {result.metadata.get('execution_time', 0):.2f} секунд")
                
                print("\n🎉 FINAL ORCHESTRATOR WORKS PERFECTLY!")
                print("=" * 60)
                
            else:
                print("❌ Объединенный анализ не выполнен!")
                print(f"📋 Ошибка: {result.message}")
                if hasattr(result, 'error') and result.error:
                    print(f"💥 Детали ошибки: {result.error}")
                
        except Exception as e:
            logger.error(f"💥 Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(main())
