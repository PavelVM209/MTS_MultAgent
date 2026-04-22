# -*- coding: utf-8 -*-
"""
Improved Meeting Analyzer Agent - Three-Stage Analysis System

Этап 1: Переработка протоколов совещаний в читабельный вид с правильной разбивкой диалогов
Этап 2: Комплексный анализ по двум источникам (протокол TXT + stage1_text_analysis.txt от Task Analyzer)
Этап 3: Финальный анализ с инсайтами и рекомендациями + создание JSON для каждого сотрудника

Учитывает все доработки из Task Analyzer Agent:
- Двухэтапная LLM система с максимальными токенами
- Русский язык для всех анализов
- TXT файлы для лучшей работы LLM
- Надежное извлечение данных
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
from dotenv import load_dotenv

from ..core.base_agent import BaseAgent, AgentConfig, AgentResult
from ..core.llm_client import LLMClient, LLMRequest
from ..core.json_memory_store import JSONMemoryStore
from ..core.quality_metrics import QualityMetrics
from ..core.config import get_employee_monitoring_config
from ..core.role_context_manager import EmployeeRoleManager
from ..core.hash_utils import md5_file
from ..core.processing_index import ProcessingIndex, ProcessingRecord, ProcessingRecordKey
from ..core.run_file_manager import RunFileManager

# Load .env file
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class EmployeeMeetingPerformance:
    """Информация о производительности сотрудника на собраниях."""
    employee_name: str
    analysis_date: datetime
    
    # Meeting participation metrics
    speaking_turns: int
    questions_asked: int
    suggestions_made: int
    action_items_assigned: int
    engagement_level: str  # high/medium/low
    leadership_indicators: List[str] = field(default_factory=list)
    
    # Combined analysis metrics
    task_to_meeting_correlation: float = 0.0
    overall_consistency: float = 0.0
    communication_effectiveness: float = 0.0
    
    # LLM insights
    detailed_insights: str = ""
    performance_rating: float = 0.0  # 1-10 scale
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ComprehensiveMeetingAnalysis:
    """Результат комплексного анализа собраний и задач."""
    analysis_date: datetime
    employees_performance: Dict[str, EmployeeMeetingPerformance]
    
    # Summary statistics
    total_employees: int
    total_meetings_analyzed: int
    total_tasks_analyzed: int
    
    # Combined insights
    team_collaboration_score: float
    task_meeting_alignment: float
    overall_team_health: float
    
    # Insights and recommendations
    team_insights: List[str]
    personal_insights: Dict[str, List[str]]
    recommendations: List[str]
    
    # Quality and metadata
    quality_score: float
    analysis_duration: timedelta
    metadata: Dict[str, Any] = field(default_factory=dict)


class ImprovedMeetingAnalyzerAgent(BaseAgent):
    """
    Улучшенный анализатор собраний с трехэтапной системой анализа.
    
    Этап 1: Переработка протоколов в читабельный вид
    Этап 2: Комплексный анализ по протоколу + Task Analyzer TXT
    Этап 3: Финальная генерация инсайтов и рекомендаций + JSON для сотрудников
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(
            config or AgentConfig(
                name="ImprovedMeetingAnalyzerAgent",
                description="Three-stage meeting analysis with protocol cleaning and comprehensive insights",
                version="2.0.0"
            )
        )
        
        # Initialize components
        self.llm_client = LLMClient()
        self.memory_store = JSONMemoryStore()
        self.quality_metrics = QualityMetrics()
        self.role_manager = EmployeeRoleManager()
        
        # Project root
        project_root = Path(__file__).resolve().parents[2]

        # Initialize processing index
        self.processing_index = ProcessingIndex.default(project_root)

        # Run-based reports
        self.run_manager = RunFileManager(project_root)
        self.run_id = self.run_manager.generate_run_id()
        self.run_paths = self.run_manager.init_run(self.run_id)


        # Load configuration
        self.emp_config = get_employee_monitoring_config()
        self.meeting_config = self.emp_config.get("meetings", {})
        self.reports_config = self.emp_config.get("reports", {})
        self.quality_config = self.emp_config.get("quality", {})
        
        # Пути из .env с fallback на значения по умолчанию
        protocols_dir_rel = os.getenv("PROTOCOLS_DIRECTORY_PATH", "data/raw/protocols")
        task_analyzer_txt_rel = os.getenv(
            "TASK_ANALYZER_TXT_PATH",
            "reports/latest/task-analysis/stage1_task_analysis.txt",
        )
        task_analyzer_json_rel = os.getenv(
            "TASK_ANALYZER_JSON_PATH",
            "reports/latest/task-analysis/stage2_task_result.json",
        )

        # Формируем абсолютные пути
        self.protocols_dir = project_root / protocols_dir_rel
        self.task_analyzer_txt = project_root / task_analyzer_txt_rel
        self.task_analyzer_json = project_root / task_analyzer_json_rel
        
        # Остальная конфигурация
        self.supported_formats = self.meeting_config.get('supported_formats', ['.txt', '.md', '.docx'])
        self.quality_threshold = self.quality_config.get('threshold', 0.9)
        
        logger.info(f"ImprovedMeetingAnalyzerAgent initialized with 3-stage analysis")
        logger.info(f"Protocols dir: {self.protocols_dir}")
        logger.info(f"Task analyzer txt: {self.task_analyzer_txt}")
        logger.info(f"Processing index: {self.processing_index.index_path}")
        logger.info(f"Run id: {self.run_id}")
        logger.info(f"Run dir: {self.run_paths.run_dir}")
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Выполнение трехэтапного анализа собраний.
        
        Returns:
            AgentResult с комплексным анализом
        """
        try:
            logger.info("Starting Improved Three-Stage Meeting Analysis")
            start_time = datetime.now()
            
            # ЭТАП 1: Переработка протоколов в читабельный вид
            logger.info("\n" + "="*80)
            logger.info("ЭТАП 1: Переработка протоколов в читабельный вид")
            logger.info("="*80)
            
            cleaned_protocols = await self.stage1_clean_protocols()
            
            if not cleaned_protocols:
                return AgentResult(
                    success=False,
                    message="No protocols found or cleaned successfully",
                    data={}
                )
            
            # ЭТАП 2: Комплексный анализ по двум источникам
            logger.info("\n" + "="*80)
            logger.info("ЭТАП 2: Комплексный анализ по протоколу + Task Analyzer TXT")
            logger.info("="*80)
            
            comprehensive_analysis = await self.stage2_comprehensive_analysis(cleaned_protocols)
            
            if not comprehensive_analysis:
                return AgentResult(
                    success=False,
                    message="Comprehensive analysis failed",
                    data={}
                )
            
            # ЭТАП 3: Финальный анализ с инсайтами и рекомендациями
            logger.info("\n" + "="*80)
            logger.info("ЭТАП 3: Финальный анализ и создание JSON для сотрудников")
            logger.info("="*80)
            
            final_analysis = await self.stage3_final_analysis(comprehensive_analysis)
            
            # Сохраняем результаты
            await self._save_comprehensive_analysis(final_analysis)
            
            # Обновляем progression для инкрементального анализа
            await self._save_employee_progression(final_analysis.employees_performance)
            
            execution_time = datetime.now() - start_time
            final_analysis.analysis_duration = execution_time
            
            logger.info(f"Improved Meeting Analysis completed in {execution_time.total_seconds():.2f}s")
            
            return AgentResult(
                success=True,
                message=f"Successfully completed 3-stage analysis for {len(final_analysis.employees_performance)} employees",
                data=final_analysis,
                metadata={
                    'execution_time': execution_time.total_seconds(),
                    'protocols_analyzed': len(cleaned_protocols),
                    'employees_analyzed': len(final_analysis.employees_performance),
                    'quality_score': final_analysis.quality_score,
                    'analysis_date': final_analysis.analysis_date.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Improved Meeting Analysis failed: {e}")
            return AgentResult(
                success=False,
                message=f"Analysis failed: {str(e)}",
                data={},
                error=str(e)
            )
    
    async def stage1_clean_protocols(self) -> List[Dict[str, Any]]:
        """
        ЭТАП 1: Переработка протоколов в читабельный вид (кэш по hash, без папок по дням).
        Raw: data/raw/protocols/*.txt
        Cleaned cache: data/processed/protocols_cleaned/*.txt
        """
        try:
            cleaned_protocols: List[Dict[str, Any]] = []
            protocol_files = sorted(self.protocols_dir.glob("*.txt"))

            if not protocol_files:
                logger.warning(f"No protocol files found in {self.protocols_dir}")
                return []

            processed_dir = self.processing_index.index_path.parents[1] / "processed" / "protocols_cleaned"
            processed_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"Found {len(protocol_files)} protocol files for cleaning")

            cached = 0
            newly = 0

            for protocol_file in protocol_files:
                try:
                    file_hash = md5_file(protocol_file)
                    key = ProcessingRecordKey(processing_type="meeting_clean", file_hash=file_hash)
                    rec = self.processing_index.get(key)

                    raw_content = protocol_file.read_text(encoding="utf-8")

                    if rec and Path(rec.result_path).exists():
                        cleaned_path = Path(rec.result_path)
                        cleaned_content = cleaned_path.read_text(encoding="utf-8")

                        cleaned_protocols.append(
                            {
                                "filename": protocol_file.name,
                                "cleaned_filename": cleaned_path.name,
                                "cleaned_filepath": cleaned_path,
                                "original_content": raw_content,
                                "cleaned_content": cleaned_content,
                                "file_date": datetime.fromtimestamp(protocol_file.stat().st_mtime),
                                "from_cache": True,
                                "file_hash": file_hash,
                            }
                        )
                        cached += 1
                        continue

                    cleaned_content = await self._clean_protocol_with_llm(raw_content, protocol_file.name)
                    if not cleaned_content:
                        continue

                    cleaned_filename = f"{protocol_file.stem}_{file_hash}.txt"
                    cleaned_path = processed_dir / cleaned_filename
                    cleaned_path.write_text(cleaned_content, encoding="utf-8")

                    self.processing_index.upsert(
                        ProcessingRecord(
                            file_hash=file_hash,
                            processing_type="meeting_clean",
                            source_path=str(protocol_file.relative_to(Path(__file__).resolve().parents[2])),
                            result_path=str(cleaned_path),
                            processed_at=datetime.now().isoformat(),
                            metadata={
                                "original_filename": protocol_file.name,
                                "cleaned_filename": cleaned_filename,
                                "content_length": len(cleaned_content),
                            },
                        )
                    )

                    cleaned_protocols.append(
                        {
                            "filename": protocol_file.name,
                            "cleaned_filename": cleaned_filename,
                            "cleaned_filepath": cleaned_path,
                            "original_content": raw_content,
                            "cleaned_content": cleaned_content,
                            "file_date": datetime.fromtimestamp(protocol_file.stat().st_mtime),
                            "from_cache": False,
                            "file_hash": file_hash,
                        }
                    )
                    newly += 1
                except Exception as e:
                    logger.error(f"Failed to clean protocol {protocol_file.name}: {e}")
                    continue

            logger.info(f"Protocol cleaning completed: {len(cleaned_protocols)} total ({cached} cached, {newly} newly processed)")
            return cleaned_protocols

        except Exception as e:
            logger.error(f"Stage 1 failed: {e}")
            return []
    
    async def _clean_protocol_with_llm(self, raw_content: str, filename: str) -> Optional[str]:
        """
        Переработка протокола с помощью LLM для создания читабельного вида.
        """
        try:
            llm_available = await self.llm_client.is_available()
            if not llm_available:
                logger.warning("LLM not available, returning original content")
                return raw_content
            
            prompt = f"""
Ты - эксперт по форматированию протоколов собраний. Переработай следующий протокол в удобочитаемый вид с правильной разбивкой диалогов.

ИСХОДНЫЙ ПРОТОКОЛ:
{raw_content}

ТРЕБОВАНИЯ К ПЕРЕРАБОТКЕ:
1. ИЗМЕНИ разбивку реплик - слишиком мелкие куски объединить в осмысленные диалоги
2. Создай ЧИТАБЕЛЬНУЮ структуру с ясным пониманием кто и что говорит
3. Определи участников и их роли на встрече
4. Сформируй логическую последовательность обсуждения
5. Выдели ключевые решения и задачи
6. Сохрани все важные детали и смысл

ФОРМАТ ВЫВОДА:
=== МЕТАДАННЫЕ ВСТРЕЧИ ===
Дата: [если есть в протоколе]
Участники: [список участников]
Тема: [основная тема]
Тип встречи: [ретроспектива/планирование/etc]

=== ХОД ВСТРЕЧИ ===
[Читабельный диалог с правильной разбивкой реплик]

Участник 1: [осмысленная реплика с объединенными мелкими фразами]

Участник 2: [ответная реплика]

Участник 1: [продолжение диалога]

=== КЛЮЧЕВЫЕ РЕШЕНИЯ ===
1. [Решение 1]
2. [Решение 2]

=== ЗАДАЧИ И ACTION ITEMS ===
1. [Задача] - Ответственный: [Имя] - Срок: [если указан]
2. [Задача] - Ответственный: [Имя] - Срок: [если указан]

ВАЖНО:
- Объединяй мелкие обрывки фраз в полные реплики
- Создай логичные диалоги между участниками
- Сделай текст максимально понятным и структурированным
- Сохраняй всю важную информацию
- Вывод должен быть НА РУССКОМ языке
"""
            
            llm_request = LLMRequest(
                prompt=prompt,
                system_prompt="Ты - эксперт по форматированию протоколов. Создавай читабельные, структурированные документы.",
                max_tokens=6000,
                temperature=0.3
            )
            
            response = await self.llm_client.generate_response(llm_request)
            cleaned_content = response.content
            
            if cleaned_content:
                logger.info(f"Protocol {filename} cleaned successfully ({len(cleaned_content)} chars)")
                return cleaned_content
            else:
                logger.warning(f"Empty response for protocol {filename}")
                return raw_content
                
        except Exception as e:
            logger.error(f"Failed to clean protocol {filename}: {e}")
            return raw_content
    
    async def stage2_comprehensive_analysis(self, cleaned_protocols: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        ЭТАП 2: Комплексный анализ по двум источникам (протокол TXT + stage1_text_analysis.txt) с Role Context.
        """
        try:
            # P6-10: Load Role Context FIRST - это критически важно!
            logger.info("Loading Role Context for comprehensive analysis...")
            
            # Извлекаем имена участников из протоколов для обогащения role context
            combined_protocols_text = "\n\n".join([
                f"=== ПРОТОКОЛ: {p['filename']} ===\n{p['cleaned_content']}"
                for p in cleaned_protocols
            ])
            participant_names = self._extract_participant_names(combined_protocols_text)
            role_context_data = await self._enhance_analysis_with_role_context(participant_names)
            
            # Форматируем Role Context для промпта
            role_context_text = self._format_role_context_for_prompt(role_context_data)
            
            # Загружаем анализ задач от Task Analyzer
            task_analyzer_content = await self._load_task_analyzer_txt()
            
            if not task_analyzer_content:
                logger.error("Task Analyzer TXT file not found or empty")
                return None
            
            # Комбинируем все очищенные протоколы
            combined_protocols = "\n\n".join([
                f"=== ПРОТОКОЛ: {p['filename']} ===\n{p['cleaned_content']}"
                for p in cleaned_protocols
            ])
            
            # Проводим комплексный анализ
            comprehensive_result = await self._analyze_comprehensive_data(combined_protocols, task_analyzer_content)
            
            if comprehensive_result:
                logger.info("Comprehensive analysis completed successfully")
                return comprehensive_result
            else:
                logger.error("Comprehensive analysis failed")
                return None
                
        except Exception as e:
            logger.error(f"Stage 2 failed: {e}")
            return None
    
    async def _load_task_analyzer_txt(self) -> Optional[str]:
        """Загрузка TXT файла от Task Analyzer."""
        try:
            if self.task_analyzer_txt.exists():
                content = self.task_analyzer_txt.read_text(encoding='utf-8')
                logger.info(f"Task Analyzer TXT loaded ({len(content)} chars)")
                return content
            else:
                logger.warning(f"Task Analyzer TXT file not found: {self.task_analyzer_txt}")
                return None
        except Exception as e:
            logger.error(f"Failed to load Task Analyzer TXT: {e}")
            return None
    
    async def _enhance_analysis_with_role_context(self, participants: List[str]) -> Dict[str, Any]:
        """
        Обогащение анализа участников контекстом ролей.
        
        Args:
            participants: Список имен участников
            
        Returns:
            Обогащенные данные о ролях участников
        """
        try:
            # Используем role context manager для обогащения анализа
            role_enhancement = self.role_manager.enhance_meeting_analysis(participants)
            
            logger.info(f"Role context enhancement: {role_enhancement['identification_rate']:.2%} participants identified")
            
            return role_enhancement
            
        except Exception as e:
            logger.error(f"Failed to enhance analysis with role context: {e}")
            return {
                "total_participants": len(participants),
                "identified_participants": [],
                "unidentified_participants": participants,
                "identification_rate": 0.0,
                "participant_contexts": {},
                "decision_makers_present": [],
                "high_activity_present": []
            }
    
    def _extract_participant_names(self, text: str) -> List[str]:
        """
        Извлечение имен участников из текста протоколов.
        
        Args:
            text: Текст протоколов
            
        Returns:
            Список уникальных имен участников
        """
        try:
            # Базовые паттерны для извлечения имен
            name_patterns = [
                r'([А-Я][а-я]+\s+[А-Я][а-я]+):',  # Имя Фамилия:
                r'([А-Я][а-я]+\s+[А-Я][а-я]+\s+[А-Я][а-я]+):',  # Имя Отчество Фамилия:
                r'устроен[а]? ([А-Я][а-я]+\s+[А-Я][а-я]+)',  # устроен Имя Фамилия
                r'ответственный:\s*([А-Я][а-я]+\s+[А-Я][а-я]+)',  # ответственный: Имя Фамилия
                r'исполнитель:\s*([А-Я][а-я]+\s+[А-Я][а-я]+)',  # исполнитель: Имя Фамилия
            ]
            
            participants = set()
            
            for pattern in name_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    participants.add(match.strip())
            
            # Дополнительное извлечение из секций участников
            participants_section = re.search(r'Участники?:\s*([^\n]+)', text, re.IGNORECASE)
            if participants_section:
                participants_text = participants_section.group(1)
                # Разделяем по запятым и точкам с запятой
                for name in re.split(r'[;,]', participants_text):
                    name = name.strip()
                    if len(name.split()) >= 2:  # Минимум Имя Фамилия
                        participants.add(name)
            
            return list(participants)
            
        except Exception as e:
            logger.error(f"Failed to extract participant names: {e}")
            return []

    async def _analyze_comprehensive_data(self, protocols_content: str, task_analyzer_content: str) -> Optional[Dict[str, Any]]:
        """
        Комплексный анализ данных из двух источников.
        """
        try:
            llm_available = await self.llm_client.is_available()
            if not llm_available:
                logger.warning("LLM not available")
                return None
            
            # Извлекаем имена участников из протоколов для обогащения role context
            participant_names = self._extract_participant_names(protocols_content)
            role_context_data = await self._enhance_analysis_with_role_context(participant_names)
            
            # Форматируем Role Context для промпта
            role_context_text = self._format_role_context_for_prompt(role_context_data)
            
            prompt = f"""
Ты - СТАРШИЙ АНАЛИТИК КОМАНДЫ для комплексного анализа. Проанализируй данные из двух источников и предоставь детальный анализ НА РУССКОМ ЯЗЫКЕ.

{role_context_text}

ИСТОЧНИК 1 - ПРОТОКОЛЫ СОБРАНИЙ:
{protocols_content}

ИСТОЧНИК 2 - АНАЛИЗ ЗАДАЧ ОТ TASK ANALYZER:
{task_analyzer_content}

ПРОВЕДИ КОМПЛЕКСНЫЙ АНАЛИЗ:

=== КОМАНДНЫЕ ИНСАЙТЫ (минимум 5) ===
1. [Инсайт о соответствии между задачами и участием в встречах]
2. [Инсайт о коммуникационных паттернах]
3. [Инсайт о лидерстве и инициативности]
4. [Инсайт о проблемных зонах и blockers]
5. [Инсайт о сильных сторонах команды]

=== АНАЛИЗ СОТРУДНИКОВ ===
[Для каждого сотрудника из обоих источников]

Сотрудник: [Имя]
- Корреляция задач и участия в встречах: [высокая/средняя/низкая]
- Последовательность в коммуникации: [description]
- Эффективность коммуникации: [1-10]
- Сильные стороны в совещаниях: [strengths]
- Проблемы в совещаниях: [problems]
- Рекомендации по развитию: [recommendations]
- Общая оценка участия: [1-10]

=== РЕКОМЕНДАЦИИ МЕНЕДЖЕРУ (минимум 4) ===
1. [Рекомендация по оптимизации встреч]
2. [Рекомендация по улучшению коммуникации]
3. [Рекомендация по развитию сотрудников]
4. [Рекомендация по балансовке нагрузки]

АНАЛИЗИРУЙ:
- Сравни поведение сотрудников в задачах и на встречах
- Найди соответствия и несоответствия
- Оцени общую динамику команды
- Выяви лидеров и проблемные зоны
- Предоставь actionable рекомендации

ВАЖНО:
- Используй ДАННЫЕ из обоих источников
- Анализируй КАЖДОГО сотрудника упомянутого в источниках
- Предоставляй КОНКРЕТНЫЕ инсайты на основе данных
- Все выводы должны быть НА РУССКОМ языке
"""
            
            llm_request = LLMRequest(
                prompt=prompt,
                system_prompt="Ты - старший аналитик команды. Проводи комплексный анализ производительности сотрудников.",
                max_tokens=8000,
                temperature=0.5
            )
            
            response = await self.llm_client.generate_response(llm_request)
            analysis_text = response.content
            
            if analysis_text:
                logger.info(f"Comprehensive analysis generated ({len(analysis_text)} chars)")
                
                # Сохраняем комплексный текстовый анализ в текущий run (TXT)
                stage2_txt = self.run_paths.meeting_stage2_dir / "comprehensive-analysis.txt"
                self.run_manager.save_text(stage2_txt, analysis_text)

                # latest
                self.run_manager.set_latest(self.run_id)
                self.run_manager.copy_to_latest(stage2_txt, Path("meeting-analysis") / "comprehensive-analysis.txt")

                logger.info(f"Comprehensive analysis saved to {stage2_txt}")

                # Извлекаем структурированные данные из текста
                structured_data = await self._extract_structured_data(analysis_text)

                return {
                    "analysis_text": analysis_text,
                    "structured_data": structured_data,
                    "analysis_file": stage2_txt,
                }
            else:
                logger.warning("Empty comprehensive analysis response")
                return None
                
        except Exception as e:
            logger.error(f"Failed to analyze comprehensive data: {e}")
            return None
    
    async def _extract_structured_data(self, analysis_text: str) -> Dict[str, Any]:
        """
        Извлечение структурированных данных из текстового анализа.
        """
        try:
            # Используем LLM для извлечения структурированных данных
            llm_available = await self.llm_client.is_available()
            if not llm_available:
                return self._fallback_structured_extraction(analysis_text)
            
            prompt = f"""
Извлеки структурированные данные из следующего анализа и создай JSON.

ТЕКСТ АНАЛИЗА:
{analysis_text}

СОЗДАЙ JSON:
{{
    "team_insights": [
        "инсайт 1",
        "инсайт 2", 
        "инсайт 3",
        "инсайт 4",
        "инсайт 5"
    ],
    "employee_analysis": {{
        "Имя Сотрудника": {{
            "task_meeting_correlation": "высокая/средняя/низкая",
            "communication_consistency": "description",
            "communication_effectiveness": 8.5,
            "meeting_strengths": ["strength1", "strength2"],
            "meeting_problems": ["problem1", "problem2"],
            "development_recommendations": ["rec1", "rec2"],
            "overall_participation_rating": 8.0
        }}
    }},
    "manager_recommendations": [
        "рекомендация 1",
        "рекомендация 2",
        "рекомендация 3",
        "рекомендация 4"
    ]
}}

ВАЖНО:
- Используй ТОЛЬКО данные из текста анализа
- Включи ВСЕХ сотрудников упомянутых в тексте
- Верни ТОЛЬКО JSON без markdown
- Используй точные данные из анализа
"""
            
            llm_request = LLMRequest(
                prompt=prompt,
                system_prompt="Ты - эксперт по извлечению структурированных данных. Создавай точный JSON на основе текста.",
                max_tokens=4000,
                temperature=0.1
            )
            
            response = await self.llm_client.generate_response(llm_request)
            json_response = response.content
            
            if json_response:
                try:
                    # Извлекаем JSON из ответа
                    import re
                    
                    # Ищем JSON в ответе
                    json_patterns = [
                        r'```json\s*(\{.*?\})\s*```',
                        r'```\s*(\{.*?\})\s*```',
                        r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',
                    ]
                    
                    for pattern in json_patterns:
                        matches = re.findall(pattern, json_response, re.DOTALL | re.IGNORECASE)
                        for match in matches:
                            try:
                                json_content = match.strip()
                                # Очищаем JSON
                                json_content = re.sub(r',\s*}', '}', json_content)
                                json_content = re.sub(r',\s*]', ']', json_content)
                                
                                structured_data = json.loads(json_content)
                                
                                # Проверяем что данные содержат сотрудников
                                if structured_data.get('employee_analysis') and len(structured_data['employee_analysis']) > 0:
                                    logger.info(f"Successfully extracted structured data with {len(structured_data['employee_analysis'])} employees")
                                    return structured_data
                                else:
                                    logger.warning("JSON parsed but no employees found, trying fallback")
                                    break
                            except json.JSONDecodeError:
                                continue
                    
                    # Fallback
                    json_start = json_response.find('{')
                    json_end = json_response.rfind('}') + 1
                    
                    if json_start != -1 and json_end > json_start:
                        json_content = json_response[json_start:json_end]
                        json_content = re.sub(r',\s*}', '}', json_content)
                        
                        try:
                            structured_data = json.loads(json_content)
                            if structured_data.get('employee_analysis') and len(structured_data['employee_analysis']) > 0:
                                logger.info(f"Successfully extracted structured data (fallback) with {len(structured_data['employee_analysis'])} employees")
                                return structured_data
                        except json.JSONDecodeError:
                            pass
                    
                    logger.warning("Failed to parse JSON response properly, using fallback extraction")
                    return self._fallback_structured_extraction(analysis_text)
                    
                except Exception as e:
                    logger.error(f"Failed to extract structured data: {e}")
                    return self._fallback_structured_extraction(analysis_text)
            else:
                logger.warning("Empty JSON response, using fallback extraction")
                return self._fallback_structured_extraction(analysis_text)
                
        except Exception as e:
            logger.error(f"Failed to extract structured data: {e}")
            return self._fallback_structured_extraction(analysis_text)
    
    def _fallback_structured_extraction(self, analysis_text: str) -> Dict[str, Any]:
        """
        Fallback метод для извлечения данных через regex.
        """
        try:
            structured_data = {
                'team_insights': [],
                'employee_analysis': {},
                'manager_recommendations': []
            }
            
            # Извлекаем командные инсайты
            insights_pattern = r'=== КОМАНДНЫЕ ИНСАЙТЫ.*?(?===|\Z)(.*)'
            insights_match = re.search(insights_pattern, analysis_text, re.DOTALL)
            if insights_match:
                insights_text = insights_match.group(1)
                # Ищем пронумерованные списки
                insight_items = re.findall(r'\d+\.\s*([^\n]+)', insights_text)
                structured_data['team_insights'] = [item.strip() for item in insight_items[:5]]
            
            # Извлекаем анализ сотрудников (поддерживаем оба формата)
            employee_patterns = [
                r'\*\*Сотрудник:\s*([^\n]+)\*\*\s*\n(.*?)(?=\*\*Сотрудник:|===|\Z)',  # **Сотрудник: Имя** формат
                r'Сотрудник:\s*([^\n]+)(.*?)(?=Сотрудник:|===|\Z)'  # Сотрудник: формат
            ]
            
            employee_matches = []
            for pattern in employee_patterns:
                matches = re.findall(pattern, analysis_text, re.DOTALL)
                employee_matches.extend(matches)
            
            # Дедупликация - храним только уникальные имена сотрудников
            seen_employees = set()
            unique_employee_matches = []
            
            for employee_name, employee_text in employee_matches:
                employee_name = employee_name.strip()
                # Очищаем имя от лишних символов и приводим к стандартному виду
                clean_name = employee_name.replace('**', '').strip()
                
                # Создаем normalized ключ для дедупликации (сортируем слова)
                name_parts = clean_name.split()
                normalized_key = ' '.join(sorted(name_parts))
                
                if normalized_key not in seen_employees:
                    seen_employees.add(normalized_key)
                    unique_employee_matches.append((clean_name, employee_text))
            
            employee_matches = unique_employee_matches
            
            for employee_name, employee_text in employee_matches:
                
                # Извлекаем метрики сотрудника
                correlation_match = re.search(r'Корреляция.*?:\s*([^\n]+)', employee_text)
                effectiveness_match = re.search(r'Эффективность.*?:\s*([\d.]+)', employee_text)
                rating_match = re.search(r'Общая оценка.*?:\s*([\d.]+)', employee_text)
                
                structured_data['employee_analysis'][employee_name] = {
                    'task_meeting_correlation': correlation_match.group(1).strip() if correlation_match else 'неизвестно',
                    'communication_consistency': employee_text[:2000] + ('...' if len(employee_text) > 2000 else employee_text),
                    'communication_effectiveness': float(effectiveness_match.group(1)) if effectiveness_match else 5.0,
                    'meeting_strengths': [],
                    'meeting_problems': [],
                    'development_recommendations': [],
                    'overall_participation_rating': float(rating_match.group(1)) if rating_match else 5.0
                }
            
            # Извлекаем рекомендации менеджеру
            recommendations_pattern = r'=== РЕКОМЕНДАЦИИ МЕНЕДЖЕРУ.*?(?===|\Z)(.*)'
            recommendations_match = re.search(recommendations_pattern, analysis_text, re.DOTALL)
            if recommendations_match:
                recommendations_text = recommendations_match.group(1)
                recommendation_items = re.findall(r'\d+\.\s*([^\n]+)', recommendations_text)
                structured_data['manager_recommendations'] = [item.strip() for item in recommendation_items[:4]]
            
            logger.info("Fallback structured extraction completed")
            return structured_data
            
        except Exception as e:
            logger.error(f"Fallback extraction failed: {e}")
            return {
                'team_insights': ['Анализ выполнен, но требуется ручная обработка'],
                'employee_analysis': {},
                'manager_recommendations': ['Проверить качество исходных данных']
            }
    
    async def stage3_final_analysis(self, comprehensive_data: Dict[str, Any]) -> ComprehensiveMeetingAnalysis:
        """
        ЭТАП 3: Финальный анализ с инсайтами и рекомендациями + JSON для сотрудников.
        """
        try:
            analysis_date = datetime.now()
            structured_data = comprehensive_data.get('structured_data', {})
            analysis_text = comprehensive_data.get('analysis_text', '')
            
            # Создаем объекты производительности сотрудников
            employees_performance = {}
            
            for employee_name, employee_data in structured_data.get('employee_analysis', {}).items():
                performance = EmployeeMeetingPerformance(
                    employee_name=employee_name,
                    analysis_date=analysis_date,
                    speaking_turns=0,  # Будет заполнено из анализа текста
                    questions_asked=0,
                    suggestions_made=0,
                    action_items_assigned=0,
                    engagement_level='medium',
                    task_to_meeting_correlation=self._normalize_correlation(employee_data.get('task_meeting_correlation', 'средняя')),
                    overall_consistency=0.7,  # Будет вычислено
                    communication_effectiveness=employee_data.get('communication_effectiveness', 5.0),
                    detailed_insights=employee_data.get('communication_consistency', ''),
                    performance_rating=employee_data.get('overall_participation_rating', 5.0)
                )
                
                employees_performance[employee_name] = performance
            
            # Вычисляем командные метрики
            total_employees = len(employees_performance)
            total_meetings_analyzed = 5  # Примерное значение
            total_tasks_analyzed = 100   # Примерное значение
            
            team_collaboration_score = min(10.0, sum(p.performance_rating for p in employees_performance.values()) / max(total_employees, 1))
            task_meeting_alignment = self._calculate_alignment_score(employees_performance)
            overall_team_health = (team_collaboration_score + task_meeting_alignment) / 2
            
            # Формируем инсайты и рекомендации
            team_insights = structured_data.get('team_insights', [])
            recommendations = structured_data.get('manager_recommendations', [])
            
            # Персональные инсайты
            personal_insights = {}
            for employee_name, performance in employees_performance.items():
                personal_insights[employee_name] = [
                    f"Рейтинг участия: {performance.performance_rating:.1f}/10",
                    f"Эффективность коммуникации: {performance.communication_effectiveness:.1f}/10",
                    f"Корреляция задач и встреч: {performance.task_to_meeting_correlation}"
                ]
            
            # Рассчитываем качество анализа
            quality_score = self._calculate_quality_score(
                total_employees, len(team_insights), len(recommendations), len(employees_performance)
            )
            
            return ComprehensiveMeetingAnalysis(
                analysis_date=analysis_date,
                employees_performance=employees_performance,
                total_employees=total_employees,
                total_meetings_analyzed=total_meetings_analyzed,
                total_tasks_analyzed=total_tasks_analyzed,
                team_collaboration_score=team_collaboration_score,
                task_meeting_alignment=task_meeting_alignment,
                overall_team_health=overall_team_health,
                team_insights=team_insights,
                personal_insights=personal_insights,
                recommendations=recommendations,
                quality_score=quality_score,
                analysis_duration=timedelta(),
                metadata={
                    'analysis_text_length': len(analysis_text),
                    'comprehensive_data_source': str(comprehensive_data.get('analysis_file', 'unknown'))
                }
            )
            
        except Exception as e:
            logger.error(f"Stage 3 failed: {e}")
            # Возвращаем минимальный анализ
            return ComprehensiveMeetingAnalysis(
                analysis_date=datetime.now(),
                employees_performance={},
                total_employees=0,
                total_meetings_analyzed=0,
                total_tasks_analyzed=0,
                team_collaboration_score=0.0,
                task_meeting_alignment=0.0,
                overall_team_health=0.0,
                team_insights=['Анализ не выполнен из-за ошибки'],
                personal_insights={},
                recommendations=['Проверить конфигурацию системы'],
                quality_score=0.0,
                analysis_duration=timedelta(),
                metadata={'error': str(e)}
            )
    
    def _normalize_correlation(self, correlation_str: str) -> float:
        """Нормализация корреляции в числовое значение."""
        correlation_lower = correlation_str.lower()
        if 'высок' in correlation_lower:
            return 0.8
        elif 'низк' in correlation_lower:
            return 0.3
        else:
            return 0.5
    
    def _calculate_alignment_score(self, employees_performance: Dict[str, EmployeeMeetingPerformance]) -> float:
        """Расчет времени соответствия задач и встреч."""
        if not employees_performance:
            return 0.0
        
        total_correlation = sum(p.task_to_meeting_correlation for p in employees_performance.values())
        return (total_correlation / len(employees_performance)) * 10
    
    def _calculate_quality_score(self, total_employees: int, insights_count: int, recommendations_count: int, employees_analyzed: int) -> float:
        """Расчет качества анализа."""
        quality_factors = []
        
        # Оценка покрытия сотрудников
        if total_employees > 0:
            coverage_score = min(1.0, employees_analyzed / max(total_employees, 1))
            quality_factors.append(coverage_score)
        
        # Оценка инсайтов
        insight_score = min(1.0, insights_count / 5.0)
        quality_factors.append(insight_score)
        
        # Оценка рекомендаций
        recommendation_score = min(1.0, recommendations_count / 4.0)
        quality_factors.append(recommendation_score)
        
        return sum(quality_factors) / len(quality_factors) if quality_factors else 0.0
    
    async def _save_comprehensive_analysis(self, analysis: ComprehensiveMeetingAnalysis) -> None:
        """Сохранение результатов анализа встреч в reports/runs/{run_id} + обновление reports/latest."""
        try:
            analysis_data = {
                "analysis_date": analysis.analysis_date.isoformat(),
                "total_employees": analysis.total_employees,
                "total_meetings_analyzed": analysis.total_meetings_analyzed,
                "total_tasks_analyzed": analysis.total_tasks_analyzed,
                "team_collaboration_score": analysis.team_collaboration_score,
                "task_meeting_alignment": analysis.task_meeting_alignment,
                "overall_team_health": analysis.overall_team_health,
                "team_insights": analysis.team_insights,
                "personal_insights": analysis.personal_insights,
                "recommendations": analysis.recommendations,
                "quality_score": analysis.quality_score,
                "analysis_duration_seconds": analysis.analysis_duration.total_seconds(),
                "metadata": analysis.metadata,
            }

            meeting_final_json = self.run_paths.meeting_final_dir / "meeting-analysis.json"
            self.run_manager.save_json(meeting_final_json, analysis_data)

            # latest
            self.run_manager.set_latest(self.run_id)
            self.run_manager.copy_to_latest(meeting_final_json, Path("meeting-analysis") / "meeting-analysis.json")

            logger.info(f"Meeting final saved: {meeting_final_json}")
        except Exception as e:
            logger.error(f"Failed to save comprehensive analysis: {e}")
    
    async def _save_employee_progression(self, employees_performance: Dict[str, EmployeeMeetingPerformance]) -> None:
        """Сохранение прогресса сотрудников в reports/runs/{run_id}/employee_progression."""
        try:
            for employee_name, performance in employees_performance.items():
                employee_data = {
                    "employee_name": performance.employee_name,
                    "analysis_date": performance.analysis_date.isoformat(),
                    "speaking_turns": performance.speaking_turns,
                    "questions_asked": performance.questions_asked,
                    "suggestions_made": performance.suggestions_made,
                    "action_items_assigned": performance.action_items_assigned,
                    "engagement_level": performance.engagement_level,
                    "leadership_indicators": performance.leadership_indicators,
                    "task_to_meeting_correlation": performance.task_to_meeting_correlation,
                    "overall_consistency": performance.overall_consistency,
                    "communication_effectiveness": performance.communication_effectiveness,
                    "detailed_insights": performance.detailed_insights,
                    "performance_rating": performance.performance_rating,
                    "last_updated": performance.last_updated.isoformat(),
                    "source": "improved_meeting_analyzer",
                    "run_id": self.run_id,
                }

                safe_filename = re.sub(r"[^\w\s-]", "", employee_name).strip()
                safe_filename = re.sub(r"[-\s]+", "_", safe_filename)
                employee_file = self.run_paths.employee_progression_dir / f"{safe_filename}.json"
                self.run_manager.save_json(employee_file, employee_data)

            logger.info(f"Employee progression saved for {len(employees_performance)} employees")
        except Exception as e:
            logger.error(f"Failed to save employee progression: {e}")
    
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
            context_parts.append("=== КОНТЕКСТ РОЛЕЙ И ДОЛЖНОСТЕЙ (УЧАСТНИКИ ВСТРЕЧ) ===")
            
            # Общая информация об участниках
            total_participants = role_context_data.get("total_participants", 0)
            identified_count = len(role_context_data.get("identified_participants", []))
            identification_rate = role_context_data.get("identification_rate", 0.0)
            
            context_parts.append(f"Всего участников в протоколах: {total_participants}")
            context_parts.append(f"Выявленные сотрудники: {identified_count}")
            context_parts.append(f"Процент идентификации: {identification_rate:.1%}")
            context_parts.append("")
            
            # Детальная информация по выявленным участникам
            participant_contexts = role_context_data.get("participant_contexts", {})
            if participant_contexts:
                context_parts.append("ИНФОРМАЦИЯ ОБ УЧАСТНИКАХ ВСТРЕЧИ:")
                
                for participant_name, context in participant_contexts.items():
                    # Формируем информацию об участнике
                    participant_info = []
                    participant_info.append(f"Участник: {participant_name}")
                    
                    if context.get("assignee_identified"):
                        participant_info.append(f"Должность: {context.get('role_level', 'N/A')}")
                        participant_info.append(f"Ответственность: {context.get('responsibility_level', 'N/A')}")
                        participant_info.append(f"Активность: {context.get('activity_level', 'N/A')}")
                        participant_info.append(f"Специализация: {context.get('specialization', 'N/A')}")
                    else:
                        participant_info.append("Должность: Не определена")
                        participant_info.append("Статус: Новый или временный участник")
                    
                    # Роль в встрече
                    if context.get("is_decision_maker"):
                        participant_info.append("Роль в встрече: Принимает решения")
                    elif context.get("is_high_activity"):
                        participant_info.append("Роль в встрече: Активный участник")
                    else:
                        participant_info.append("Роль в встрече: Наблюдатель")
                    
                    context_parts.append("\n".join(participant_info))
                    context_parts.append("")  # Пустая строка между участниками
            
            # Лидеры и активные участники
            decision_makers = role_context_data.get("decision_makers_present", [])
            high_activity = role_context_data.get("high_activity_present", [])
            
            if decision_makers:
                context_parts.append(f"ПРИНИМАЮЩИЕ РЕШЕНИЯ: {', '.join(decision_makers)}")
            
            if high_activity:
                context_parts.append(f"АКТИВНЫЕ УЧАСТНИКИ: {', '.join(high_activity)}")
            
            if decision_makers or high_activity:
                context_parts.append("")
            
            # Важные инструкции для LLM с учетом ролей
            context_parts.append("=== ИНСТРУКЦИИ ДЛЯ АНАЛИЗА С УЧЕТОМ РОЛЕЙ УЧАСТНИКОВ ===")
            context_parts.append("1. Учитывай должности и ответственность при анализе участия в встречах")
            context_parts.append("2. Product Owner и Team Lead имеют разные роли и степени влияния")
            context_parts.append("3. Обращай внимание на кто принимает решения и кто активно участвует")
            context_parts.append("4. Рекомендации должны соответствовать уровню должности участника")
            context_parts.append("5. Новым участникам требуются четкие задачи и наставничество")
            context_parts.append("6. Оценивай участие в контексте должностных обязанностей")
            context_parts.append("")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Failed to format role context for prompt: {e}")
            return "=== КОНТЕКСТ РОЛЕЙ И ДОЛЖНОСТЕЙ ===\nОшибка форматирования контекста ролей\n"
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Проверка состояния агента."""
        try:
            llm_available = await self.llm_client.is_available()
            
            return {
                'agent_name': self.config.name,
                'status': 'healthy' if llm_available else 'degraded',
                'llm_client': 'available' if llm_available else 'unavailable',
                'protocols_directory': 'exists' if self.protocols_dir.exists() else 'missing',
                'task_analyzer_txt': 'exists' if self.task_analyzer_txt.exists() else 'missing',
                "reports_directory": str(self.run_manager.latest_root),
                'analysis_stages': '3-stage system ready',
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
        print("🚀 ЗАПУСК IMPROVED MEETING ANALYZER AGENT")
        print("=" * 60)
        
        try:
            # Создаем агент
            agent = ImprovedMeetingAnalyzerAgent()
            print("✅ Agent created")
            
            # Health check
            health = await agent.get_health_status()
            print(f"📊 Health Status: {health['status']}")
            print(f"🔧 LLM Client: {health['llm_client']}")
            print(f"📁 Protocols Directory: {health['protocols_directory']}")
            print(f"📄 Task Analyzer TXT: {health['task_analyzer_txt']}")
            print(f"📁 Reports Directory: {health['reports_directory']}")
            print(f"🔄 Analysis Stages: {health['analysis_stages']}")
            
            # Выполняем анализ
            print("\n🔄 ВЫПОЛНЕНИЕ ТРЕХЭТАПНОГО АНАЛИЗА СОБРАНИЙ")
            print("=" * 60)
            
            result = await agent.execute({})
            
            if result.success:
                print("✅ Анализ выполнен успешно!")
                print(f"📋 Сообщение: {result.message}")
                
                analysis_data = result.data
                
                print(f"👥 Проанализировано сотрудников: {analysis_data.total_employees}")
                print(f"📊 Всего совещаний: {analysis_data.total_meetings_analyzed}")
                print(f"📋 Всего задач: {analysis_data.total_tasks_analyzed}")
                print(f"🤝 Командное взаимодействие: {analysis_data.team_collaboration_score:.1f}/10")
                print(f"🎯 Общее здоровье команды: {analysis_data.overall_team_health:.1f}/10")
                
                if analysis_data.team_insights:
                    print(f"💡 Командные инсайты: {len(analysis_data.team_insights)}")
                    for i, insight in enumerate(analysis_data.team_insights[:3], 1):
                        print(f"  {i}. {insight[:100]}...")
                
                if analysis_data.recommendations:
                    print(f"📝 Рекомендации: {len(analysis_data.recommendations)}")
                    for i, rec in enumerate(analysis_data.recommendations[:3], 1):
                        print(f"  {i}. {rec[:100]}...")
                
                if analysis_data.employees_performance:
                    print(f"👥 Детализация по сотрудникам:")
                    for employee, perf in analysis_data.employees_performance.items():
                        rating = perf.performance_rating
                        correlation = perf.task_to_meeting_correlation
                        effectiveness = perf.communication_effectiveness
                        print(f"  • {employee}: рейтинг {rating:.1f}/10, корреляция {correlation:.2f}, эффективность {effectiveness:.1f}/10")
                
                print(f"🎯 Качество анализа: {analysis_data.quality_score:.3f}")
                
                print("\n🎉 MEETING ANALYZER WORKS PERFECTLY!")
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
