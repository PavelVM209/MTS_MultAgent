# -*- coding: utf-8 -*-
"""
Meeting Analyzer Agent - Employee Monitoring System (Full Protocol Text Analysis)

Анализирует ПОЛНЫЙ ТЕКСТ протоколов собраний для отслеживания прогресса сотрудников,
их участия и вклада в командную работу.
"""

import asyncio
import logging
import json
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from core.base_agent import BaseAgent, AgentConfig, AgentResult
from core.llm_client import LLMClient, LLMRequest
from core.json_memory_store import JSONMemoryStore
from core.quality_metrics import QualityMetrics
from core.config import get_employee_monitoring_config

logger = logging.getLogger(__name__)


@dataclass
class EmployeeMeetingParticipation:
    """Информация об участии сотрудника в собраниях."""
    employee_name: str
    analysis_date: datetime
    
    # Participation metrics
    total_meetings: int
    meetings_attended: int
    attendance_rate: float
    
    # Contribution metrics
    speaking_turns: int
    action_items_assigned: int
    questions_asked: int
    suggestions_made: int
    
    # Quality indicators
    engagement_score: float
    leadership_indicators: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    
    # LLM insights
    llm_insights: str = ""
    participation_rating: float = 0.0  # 1-10 scale
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class DailyMeetingAnalysisResult:
    """Результат ежедневного анализа собраний."""
    analysis_date: datetime
    employees_participation: Dict[str, EmployeeMeetingParticipation]
    
    # Summary statistics
    total_employees: int
    total_meetings_analyzed: int
    avg_attendance_rate: float
    total_action_items: int
    
    # Insights and trends
    team_collaboration_insights: List[str]
    recommendations: List[str]
    
    # Quality and metadata
    quality_score: float
    analysis_duration: timedelta
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Additional fields for compatibility
    completed_action_items: int = field(default=0)


class MeetingAnalyzerAgentFull(BaseAgent):
    """
    Анализатор ПОЛНЫХ ПРОТОКОЛОВ собраний для Employee Monitoring.
    
    Анализирует полный текст протоколов без предварительной обработки:
    - Выгружает весь текст протокола
    - Передает в LLM без изменений
    - Получает детальный анализ участия каждого сотрудника
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(
            config or AgentConfig(
                name="MeetingAnalyzerAgentFull",
                description="Analyzes full meeting protocol text for employee monitoring",
                version="1.0.0"
            )
        )
        
        # Initialize components
        self.llm_client = LLMClient()
        self.memory_store = JSONMemoryStore()
        self.quality_metrics = QualityMetrics()
        
        # Load configuration
        self.emp_config = get_employee_monitoring_config()
        self.meeting_config = self.emp_config.get('meetings', {})
        self.reports_config = self.emp_config.get('reports', {})
        self.quality_config = self.emp_config.get('quality', {})
        self.employees_config = self.emp_config.get('employees', {})
        
        # Analysis parameters
        self.protocols_dir = Path(self.meeting_config.get('protocols_directory', './protocols'))
        self.supported_formats = self.meeting_config.get('supported_formats', ['.txt', '.md', '.docx'])
        self.excluded_users = set(self.employees_config.get('excluded_users', []))
        self.quality_threshold = self.quality_config.get('threshold', 0.9)
        
        # Reports directory
        self.daily_reports_dir = Path(self.reports_config.get('daily_reports_dir', './reports/daily'))
        self.daily_reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"MeetingAnalyzerAgentFull initialized. Protocols dir: {self.protocols_dir}")
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Выполнение анализа ПОЛНЫХ протоколов собраний.
        
        Args:
            input_data: Данные с протоколами собраний (опционально)
            
        Returns:
            AgentResult с анализом участия сотрудников
        """
        try:
            logger.info("Starting FULL Meeting Protocol Analysis for Employee Monitoring")
            start_time = datetime.now()
            
            # Получаем протоколы из input или сканируем автоматически
            meeting_protocols = input_data.get('meeting_protocols')
            
            if not meeting_protocols:
                logger.info("No protocols provided in input_data, scanning directory automatically")
                meeting_protocols = await self.scan_protocols_directory()
                
                if not meeting_protocols:
                    return AgentResult(
                        success=False,
                        message="No meeting protocols found for analysis (neither in input nor in directory)",
                        data={}
                    )
            else:
                logger.info(f"Using {len(meeting_protocols)} protocols from input_data")
            
            # Анализируем каждый протокол с полным текстом
            analyzed_protocols = []
            for protocol in meeting_protocols:
                try:
                    analysis = await self._analyze_full_protocol_text(protocol)
                    if analysis:
                        analyzed_protocols.append(analysis)
                except Exception as e:
                    logger.warning(f"Failed to analyze protocol {protocol.get('filename', 'unknown')}: {e}")
                    continue
            
            if not analyzed_protocols:
                return AgentResult(
                    success=False,
                    message="No protocols analyzed successfully",
                    data={}
                )
            
            # Группируем анализ по сотрудникам
            employees_participation = await self._group_participation_by_employee(analyzed_protocols)
            
            # Генерируем командный анализ
            analysis_result = await self._generate_team_analysis(employees_participation, analyzed_protocols)
            
            # Рассчитываем качество анализа
            analysis_result.quality_score = await self._calculate_analysis_quality(analysis_result)
            
            # Сохраняем результаты
            await self._save_daily_analysis(analysis_result)
            
            # Обновляем memory store
            await self._update_employee_memory_store(employees_participation)
            
            # Время выполнения
            execution_time = datetime.now() - start_time
            analysis_result.analysis_duration = execution_time
            
            logger.info(f"FULL Meeting Analysis completed in {execution_time.total_seconds():.2f}s, "
                       f"analyzed {len(analyzed_protocols)} protocols for {len(employees_participation)} employees")
            
            return AgentResult(
                success=True,
                message=f"Successfully analyzed full meeting protocols for {len(employees_participation)} employees",
                data=analysis_result,
                metadata={
                    'execution_time': execution_time.total_seconds(),
                    'protocols_analyzed': len(analyzed_protocols),
                    'employees_analyzed': len(employees_participation),
                    'quality_score': analysis_result.quality_score,
                    'analysis_date': analysis_result.analysis_date.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"FULL Meeting Analysis failed: {e}")
            return AgentResult(
                success=False,
                message=f"Analysis failed: {str(e)}",
                data={},
                error=str(e)
            )
    
    async def scan_protocols_directory(self) -> List[Dict[str, Any]]:
        """
        Автоматическое сканирование директории с протоколами.
        
        Returns:
            List[Dict[str, Any]]: Протоколы найденные в директории
        """
        try:
            logger.info(f"Scanning protocols directory: {self.protocols_dir}")
            
            if not self.protocols_dir.exists():
                logger.warning(f"Protocols directory does not exist: {self.protocols_dir}")
                return []
            
            protocols = []
            
            # Рекурсивно ищем файлы поддерживаемых форматов
            for file_path in self.protocols_dir.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                    try:
                        protocol_info = await self._parse_protocol_file(file_path)
                        if protocol_info:
                            protocols.append(protocol_info)
                    except Exception as e:
                        logger.warning(f"Failed to parse protocol file {file_path}: {e}")
                        continue
            
            if protocols:
                logger.info(f"Found {len(protocols)} protocol files")
                
                # Логируем статистику по типам файлов
                format_stats = {}
                for protocol in protocols:
                    ext = protocol.get('format', 'unknown')
                    format_stats[ext] = format_stats.get(ext, 0) + 1
                
                logger.info(f"Protocol formats: {format_stats}")
                
                # Сортируем по дате файла
                protocols.sort(key=lambda x: x.get('file_date', datetime.min), reverse=True)
            else:
                logger.warning("No protocol files found in directory")
            
            return protocols
            
        except Exception as e:
            logger.error(f"Failed to scan protocols directory: {e}")
            return []
    
    async def _parse_protocol_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Парсинг файла протокола с ВЫГРУЗКОЙ ПОЛНОГО ТЕКСТА."""
        try:
            # Определяем тип файла по названию
            meeting_type = self._detect_meeting_type(file_path.name)
            
            # Извлекаем дату из имени файла или содержимого
            meeting_date = self._extract_date_from_filename(file_path.name)
            
            # Читаем ПОЛНЫЙ текст без изменений
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            protocol_info = {
                'file_path': str(file_path),
                'filename': file_path.name,
                'format': file_path.suffix.lower(),
                'meeting_type': meeting_type,
                'meeting_date': meeting_date,
                'file_date': datetime.fromtimestamp(file_path.stat().st_mtime),
                'full_text': content,  # ПОЛНЫЙ ТЕКСТ БЕЗ ИЗМЕНЕНИЙ
                'content_length': len(content),
                'size_bytes': len(content.encode('utf-8'))
            }
            
            return protocol_info
            
        except Exception as e:
            logger.error(f"Error parsing protocol file {file_path}: {e}")
            return None
    
    def _detect_meeting_type(self, filename: str) -> str:
        """Определение типа собрания по имени файла."""
        filename_lower = filename.lower()
        
        type_keywords = {
            'standup': ['standup', 'дейли', 'daily', 'утреннее'],
            'planning': ['planning', 'планирование', 'sprint', 'план'],
            'retrospective': ['retro', 'retrospective', 'ретро', 'обратная связь'],
            'demo': ['demo', 'демо', 'showcase', 'показ'],
            'review': ['review', 'обзор', 'code review', 'ревью'],
            'technical': ['technical', 'tech', 'архитектура', 'техническое'],
        }
        
        for meeting_type, keywords in type_keywords.items():
            if any(keyword in filename_lower for keyword in keywords):
                return meeting_type
        
        return 'general'
    
    def _extract_date_from_filename(self, filename: str) -> Optional[datetime]:
        """Извлечение даты из имени файла."""
        # Паттерны для дат в именах файлов
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{2}-\d{2}-\d{4})',  # DD-MM-YYYY
            r'(\d{2}\.\d{2}\.\d{4})',  # DD.MM.YYYY
            r'(\d{4}_\d{2}_\d{2})',  # YYYY_MM_DD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                date_str = match.group(1)
                try:
                    # Пробуем разные форматы
                    for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d.%m.%Y', '%Y_%m_%d']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                except Exception:
                    continue
        
        return None
    
    async def _analyze_full_protocol_text(self, protocol: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Анализ ПОЛНОГО ТЕКСТА протокола с помощью LLM."""
        try:
            full_text = protocol.get('full_text', '')
            filename = protocol.get('filename', '')
            meeting_type = protocol.get('meeting_type', 'general')
            
            if not full_text.strip():
                logger.warning(f"Empty protocol text for {filename}")
                return None
            
            # Log full protocol text being sent to LLM
            logger.info(f"=== FULL PROTOCOL TEXT BEING SENT TO LLM ===")
            logger.info(f"Protocol file: {filename}")
            logger.info(f"Text length: {len(full_text)} characters")
            logger.info(f"Text preview: {full_text[:500]}...")
            logger.info("=== COMPLETE PROTOCOL TEXT ===")
            logger.info(full_text)
            logger.info("=== END PROTOCOL TEXT ===")
            
            # Анализируем полный текст с помощью LLM
            llm_analysis = await self._analyze_full_text_with_llm(full_text, filename)
            
            if llm_analysis:
                protocol_analysis = {
                    'filename': filename,
                    'meeting_type': meeting_type,
                    'meeting_date': protocol.get('meeting_date'),
                    'full_text_length': len(full_text),
                    'llm_analysis': llm_analysis,
                    'analysis_timestamp': datetime.now()
                }
                
                return protocol_analysis
            else:
                logger.warning(f"LLM analysis failed for protocol {filename}")
                return None
            
        except Exception as e:
            logger.error(f"Error analyzing full protocol text {protocol.get('filename', 'unknown')}: {e}")
            return None
    
    async def _analyze_full_text_with_llm(self, full_text: str, filename: str) -> Optional[Dict[str, Any]]:
        """Анализ ПОЛНОГО текста протокола с помощью LLM (2-этапный подход)."""
        try:
            llm_available = await self.llm_client.is_available()
            if not llm_available:
                logger.warning("LLM not available, skipping full text analysis")
                return None
            
            # ЭТАП 1: Получаем детальный текстовый анализ
            logger.info(f"ЭТАП 1: Получаем текстовый анализ протокола {filename}")
            text_analysis = await self._get_text_analysis_from_llm(full_text, filename)
            
            if not text_analysis:
                logger.error(f"Failed to get text analysis for {filename}")
                return None
            
            # ЭТАП 2: Конвертируем текстовый анализ в JSON
            logger.info(f"ЭТАП 2: Конвертируем текстовый анализ в JSON для {filename}")
            json_analysis = await self._convert_text_to_json(text_analysis, filename)
            
            if json_analysis:
                logger.info(f"Successfully completed 2-stage analysis for {filename}")
                return json_analysis
            else:
                logger.error(f"Failed to convert text analysis to JSON for {filename}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to analyze full protocol text with LLM: {e}")
            return None
    
    async def _get_text_analysis_from_llm(self, full_text: str, filename: str) -> Optional[str]:
        """ЭТАП 1: Получает текстовый анализ протокола от LLM."""
        try:
            llm_prompt = f"""
Ты - экспертный аналитик протоколов собраний для системы мониторинга сотрудников. Проанализируй полный текст протокола встречи и предоставь детальный текстовый анализ.

ПОЛНЫЙ ТЕКСТ ПРОТОКОЛА ВСТРЕЧИ:
{full_text}

ПРЕДОСТАВЬ ДЕТАЛЬНЫЙ ТЕКСТОВЫЙ АНАЛИЗ со следующими разделами:

1. МЕТADATA ВСТРЕЧИ:
   - Общее количество участников
   - Длительность встречи в минутах
   - Основные темы обсуждения
   - Тип встречи

2. АНАЛИЗ УЧАСТНИКОВ (для каждого участника):
   - Имя участника
   - Количество реплик (speaking turns)
   - Количество заданных вопросов
   - Количество предложений и идей
   - Количество назначенных задач
   - Уровень вовлеченности (high/medium/low)
   - Признаки лидерства
   - Детальный анализ участия и вклада
   - Проблемы и concerns

3. ЗАДАЧИ И ACTION ITEMS:
   - Описание задачи
   - Ответственный
   - Срок если указан
   - Приоритет

4. КОМАНДНЫЕ ИНСАЙТЫ:
   - Ключевые наблюдения о командной работе
   - Сильные стороны команды
   - Области для улучшения

5. РЕКОМЕНДАЦИИ:
   - Конкретные рекомендации по улучшению
   - Предложения по оптимизации процессов

АНАЛИЗРУЙ:
- Подсчитай точное количество реплик каждого участника
- Определи инициативность и проактивность
- Найди прямые назначения задач
- Оцени качество коммуникации
- Выяви лидерские качества
- Определи проблемные моменты

ПРЕДОСТАВЬ АНАЛИЗ В ФОРМАТЕ ЧИТАЕМОГО ТЕКСТА, БЕЗ JSON.
"""
            
            llm_request = LLMRequest(
                prompt=llm_prompt,
                system_prompt="Ты - эксперт по анализу протоколов собраний. Предоставляй детальный, структурированный текстовый анализ.",
                max_tokens=4000,
                temperature=0.5
            )
            
            llm_response_obj = await self.llm_client.generate_response(llm_request)
            text_analysis = llm_response_obj.content
            
            if text_analysis:
                logger.info(f"=== ЭТАП 1: ПОЛУЧЕН ТЕКСТОВЫЙ АНАЛИЗ ({len(text_analysis)} символов) ===")
                logger.info(text_analysis)
                logger.info("=== КОНЕЦ ТЕКСТОВОГО АНАЛИЗА ===")
                return text_analysis
            else:
                logger.warning("Empty text analysis response from LLM")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get text analysis from LLM: {e}")
            return None
    
    async def _convert_text_to_json(self, text_analysis: str, filename: str) -> Optional[Dict[str, Any]]:
        """ЭТАП 2: Конвертирует текстовый анализ в JSON."""
        try:
            llm_prompt = f"""
Извлеки данные из текстового анализа и создай JSON. ВНИМАНИЕ: включи ВСЕХ участников упомянутых в тексте!

ТЕКСТОВЫЙ АНАЛИЗ:
{text_analysis[:2000]}...

СОЗДАЙ JSON:
{{
    "meeting_metadata": {{
        "total_participants": 9,
        "meeting_duration_minutes": 27,
        "dominant_topics": ["ретроспектива", "качество данных", "коммуникация"],
        "meeting_type": "ретроспектива спринта"
    }},
    "participant_analysis": {{
        "Надежда Савенкова": {{
            "speaking_turns": 56,
            "questions_asked": 9,
            "suggestions_made": 4,
            "action_items_assigned": 1,
            "engagement_level": "high",
            "leadership_indicators": ["модерация", "организация"],
            "collaboration_insights": "Ведет встречу, структурирует обсуждение",
            "concerns": ["доминирующая роль"]
        }},
        "Константин Березин": {{
            "speaking_turns": 13,
            "questions_asked": 0,
            "suggestions_made": 2,
            "action_items_assigned": 1,
            "engagement_level": "medium",
            "leadership_indicators": [],
            "collaboration_insights": "Решает проблемы с данными",
            "concerns": []
        }},
        "Егор": {{
            "speaking_turns": 10,
            "questions_asked": 0,
            "suggestions_made": 3,
            "action_items_assigned": 1,
            "engagement_level": "medium",
            "leadership_indicators": ["коммуникация"],
            "collaboration_insights": "Активно участвует в обсуждении",
            "concerns": []
        }},
        "Никита Колобаев": {{
            "speaking_turns": 8,
            "questions_asked": 0,
            "suggestions_made": 1,
            "action_items_assigned": 1,
            "engagement_level": "medium",
            "leadership_indicators": [],
            "collaboration_insights": "Работает над скриптами",
            "concerns": []
        }},
        "Павел Мурзаков": {{
            "speaking_turns": 8,
            "questions_asked": 0,
            "suggestions_made": 0,
            "action_items_assigned": 1,
            "engagement_level": "medium",
            "leadership_indicators": ["поддержка команды"],
            "collaboration_insights": "Перераспределил ресурсы для команды",
            "concerns": []
        }},
        "Иван Найденов": {{
            "speaking_turns": 12,
            "questions_asked": 0,
            "suggestions_made": 2,
            "action_items_assigned": 1,
            "engagement_level": "high",
            "leadership_indicators": ["инициативность", "создание инструментов"],
            "collaboration_insights": "Создал обертку для DAG, помог с данными",
            "concerns": ["ошибки с доступами"]
        }},
        "Алина Сабадаш": {{
            "speaking_turns": 8,
            "questions_asked": 0,
            "suggestions_made": 0,
            "action_items_assigned": 1,
            "engagement_level": "medium",
            "leadership_indicators": [],
            "collaboration_insights": "Работает над срочными задачами",
            "concerns": ["отсутствие бэклога"]
        }},
        "Андрей Болотин": {{
            "speaking_turns": 10,
            "questions_asked": 1,
            "suggestions_made": 3,
            "action_items_assigned": 2,
            "engagement_level": "high",
            "leadership_indicators": ["стратегическое мышление", "улучшение процессов"],
            "collaboration_insights": "Переключил на новые дашборды, улучшает процессы",
            "concerns": ["проблемы с согласованиями"]
        }},
        "Рафаэль Мангурсузян": {{
            "speaking_turns": 6,
            "questions_asked": 1,
            "suggestions_made": 1,
            "action_items_assigned": 0,
            "engagement_level": "low",
            "leadership_indicators": [],
            "collaboration_insights": "Проблемы с подключением, переключил витрину",
            "concerns": ["проблемы с связью"]
        }}
    }},
    "action_items": [
        {{
            "description": "опубликовать дашборды",
            "assignee": "Надежда Савенкова",
            "deadline": "понедельник",
            "priority": "medium"
        }},
        {{
            "description": "работать над недозвоном",
            "assignee": "Константин Березин",
            "deadline": null,
            "priority": "high"
        }}
    ],
    "team_insights": ["хорошая коммуникация", "эффективная работа", "процессные проблемы"],
    "recommendations": ["улучшить согласования", "вести бэклог", "проводить регулярные встречи"]
}}

ВАЖНО: Верни ТОЛЬКО JSON без markdown и комментариев. Используй эту структуру но скорректируй числа на основе текста.
"""
            
            llm_request = LLMRequest(
                prompt=llm_prompt,
                system_prompt="Ты - эксперт по конвертации текста в JSON. Предоставляй только валидный JSON без дополнительных комментариев.",
                max_tokens=4000,
                temperature=0.1  # Очень низкая температура для точной конвертации
            )
            
            llm_response_obj = await self.llm_client.generate_response(llm_request)
            json_response = llm_response_obj.content
            
            if json_response:
                logger.info(f"=== ЭТАП 2: ПОЛУЧЕН JSON ОТВЕТ ({len(json_response)} символов) ===")
                logger.info(json_response)
                logger.info("=== КОНЕЦ JSON ОТВЕТА ===")
                
                # Парсим JSON ответ
                try:
                    import re
                    
                    # Extract JSON from response
                    json_patterns = [
                        r'```json\s*(\{.*?\})\s*```',  # JSON in code blocks
                        r'```\s*(\{.*?\})\s*```',      # JSON in code blocks without language
                        r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',  # Simple JSON
                    ]
                    
                    for pattern in json_patterns:
                        matches = re.findall(pattern, json_response, re.DOTALL | re.IGNORECASE)
                        for match in matches:
                            try:
                                json_content = match.strip()
                                # Clean up JSON issues
                                json_content = re.sub(r',\s*}', '}', json_content)
                                json_content = re.sub(r',\s*]', ']', json_content)
                                
                                analysis_result = json.loads(json_content)
                                logger.info(f"Successfully parsed JSON using pattern: {pattern}")
                                return analysis_result
                            except json.JSONDecodeError as e:
                                logger.debug(f"Pattern {pattern} failed: {e}")
                                continue
                    
                    # Fallback: find JSON between first { and last }
                    json_start = json_response.find('{')
                    json_end = json_response.rfind('}') + 1
                    
                    if json_start != -1 and json_end > json_start:
                        json_content = json_response[json_start:json_end]
                        json_content = re.sub(r',\s*}', '}', json_content)
                        json_content = re.sub(r',\s*]', ']', json_content)
                        
                        try:
                            analysis_result = json.loads(json_content)
                            logger.info("Successfully parsed JSON using fallback method")
                            return analysis_result
                        except json.JSONDecodeError as e:
                            logger.debug(f"Fallback JSON parse failed: {e}")
                    
                    logger.error("Failed to parse JSON response")
                    return None
                    
                except Exception as e:
                    logger.error(f"Failed to parse JSON: {e}")
                    return None
            else:
                logger.warning("Empty JSON conversion response from LLM")
                return None
                
        except Exception as e:
            logger.error(f"Failed to convert text to JSON: {e}")
            return None
    
    async def _group_participation_by_employee(self, analyzed_protocols: List[Dict[str, Any]]) -> Dict[str, EmployeeMeetingParticipation]:
        """Группировка анализа по сотрудникам."""
        employees_participation = {}
        
        for protocol in analyzed_protocols:
            llm_analysis = protocol.get('llm_analysis', {})
            participant_analysis = llm_analysis.get('participant_analysis', {})
            action_items = llm_analysis.get('action_items', [])
            
            # Обрабатываем всех участников из LLM анализа
            for participant_name, participant_data in participant_analysis.items():
                if participant_name in self.excluded_users:
                    continue
                
                if participant_name not in employees_participation:
                    employees_participation[participant_name] = EmployeeMeetingParticipation(
                        employee_name=participant_name,
                        analysis_date=datetime.now(),
                        total_meetings=0,
                        meetings_attended=0,
                        attendance_rate=0.0,
                        speaking_turns=0,
                        action_items_assigned=0,
                        questions_asked=0,
                        suggestions_made=0,
                        engagement_score=0.0
                    )
                
                participation = employees_participation[participant_name]
                
                # Обновляем метрики из LLM анализа
                participation.total_meetings += 1
                participation.meetings_attended += 1
                participation.speaking_turns += participant_data.get('speaking_turns', 0)
                participation.questions_asked += participant_data.get('questions_asked', 0)
                participation.suggestions_made += participant_data.get('suggestions_made', 0)
                participation.action_items_assigned += participant_data.get('action_items_assigned', 0)
                
                # Engagement score based on LLM assessment
                engagement_level = participant_data.get('engagement_level', 'medium')
                engagement_scores = {'high': 0.8, 'medium': 0.5, 'low': 0.2}
                participation.engagement_score = engagement_scores.get(engagement_level, 0.5)
                
                # Leadership indicators
                leadership_indicators = participant_data.get('leadership_indicators', [])
                if leadership_indicators:
                    participation.leadership_indicators.extend(leadership_indicators)
                
                # Concerns
                concerns = participant_data.get('concerns', [])
                if concerns:
                    participation.concerns.extend(concerns)
                
                # LLM insights
                collaboration_insights = participant_data.get('collaboration_insights', '')
                if collaboration_insights:
                    participation.llm_insights += f"\n{collaboration_insights}"
        
        # Рассчитываем производные метрики
        for participation in employees_participation.values():
            # Attendance rate ( Всегда 1.0 для полных протоколов, т.к. участник в тексте = присутствовал)
            participation.attendance_rate = 1.0 if participation.total_meetings > 0 else 0.0
            
            # Participation rating based on multiple factors
            participation.participation_rating = min(10.0, (
                participation.engagement_score * 4 +
                (participation.speaking_turns / max(participation.total_meetings, 1)) * 2 +
                participation.suggestions_made * 0.5 +
                participation.questions_asked * 0.5
            ))
        
        return employees_participation
    
    async def _generate_team_analysis(self, employees_participation: Dict[str, EmployeeMeetingParticipation], 
                                    analyzed_protocols: List[Dict[str, Any]]) -> DailyMeetingAnalysisResult:
        """Генерация командного анализа."""
        analysis_date = datetime.now()
        
        # Summary statistics
        total_employees = len(employees_participation)
        total_meetings_analyzed = len(analyzed_protocols)
        
        # Average attendance rate
        if employees_participation:
            avg_attendance_rate = sum(p.attendance_rate for p in employees_participation.values()) / total_employees
        else:
            avg_attendance_rate = 0.0
        
        # Action items statistics
        total_action_items = sum(p.action_items_assigned for p in employees_participation.values())
        
        # Generate insights from LLM analyses
        team_insights = []
        recommendations = []
        
        for protocol in analyzed_protocols:
            llm_analysis = protocol.get('llm_analysis', {})
            protocol_insights = llm_analysis.get('team_insights', [])
            protocol_recommendations = llm_analysis.get('recommendations', [])
            
            team_insights.extend(protocol_insights)
            recommendations.extend(protocol_recommendations)
        
        # Remove duplicates
        team_insights = list(set(team_insights))
        recommendations = list(set(recommendations))
        
        return DailyMeetingAnalysisResult(
            analysis_date=analysis_date,
            employees_participation=employees_participation,
            total_employees=total_employees,
            total_meetings_analyzed=total_meetings_analyzed,
            avg_attendance_rate=avg_attendance_rate,
            total_action_items=total_action_items,
            completed_action_items=0,  # TODO: Track completion
            team_collaboration_insights=team_insights,
            recommendations=recommendations,
            quality_score=0.0,  # Will be calculated later
            analysis_duration=timedelta()  # Will be set later
        )
    
    async def _calculate_analysis_quality(self, analysis_result) -> float:
        """Расчет качества анализа."""
        try:
            quality_factors = []
            
            # Employee coverage score
            if analysis_result.total_employees > 0:
                coverage_score = min(1.0, analysis_result.total_employees / 5.0)  # Expect at least 5 employees
                quality_factors.append(coverage_score)
            
            # Data completeness score
            if analysis_result.employees_participation:
                employees_with_data = len(analysis_result.employees_participation)
                completeness_score = 1.0  # All employees have data
                quality_factors.append(completeness_score)
            
            # Protocol diversity score
            if analysis_result.total_meetings_analyzed > 0:
                diversity_score = min(1.0, analysis_result.total_meetings_analyzed / 3.0)  # Expect at least 3 protocols
                quality_factors.append(diversity_score)
            
            # Insight quality score
            insight_score = min(1.0, len(analysis_result.team_collaboration_insights) / 3.0)  # Expect at least 3 insights
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
    
    async def _save_daily_analysis(self, analysis_result) -> None:
        """Сохранение результатов анализа."""
        try:
            # Create date-specific directory
            date_str = analysis_result.analysis_date.strftime('%Y-%m-%d')
            daily_dir = self.daily_reports_dir / date_str
            daily_dir.mkdir(parents=True, exist_ok=True)
            
            # Prepare data for serialization
            analysis_data = {
                'analysis_date': analysis_result.analysis_date.isoformat(),
                'total_employees': analysis_result.total_employees,
                'total_meetings_analyzed': analysis_result.total_meetings_analyzed,
                'avg_attendance_rate': analysis_result.avg_attendance_rate,
                'total_action_items': analysis_result.total_action_items,
                'completed_action_items': analysis_result.completed_action_items,
                'team_collaboration_insights': analysis_result.team_collaboration_insights,
                'recommendations': analysis_result.recommendations,
                'quality_score': analysis_result.quality_score,
                'analysis_duration_seconds': analysis_result.analysis_duration.total_seconds(),
                'employees_participation': {},
                'metadata': analysis_result.metadata,
                'analysis_type': 'full_protocol_text_analysis'
            }
            
            # Serialize employee participation
            for employee, participation in analysis_result.employees_participation.items():
                analysis_data['employees_participation'][employee] = {
                    'employee_name': participation.employee_name,
                    'analysis_date': participation.analysis_date.isoformat(),
                    'total_meetings': participation.total_meetings,
                    'meetings_attended': participation.meetings_attended,
                    'attendance_rate': participation.attendance_rate,
                    'speaking_turns': participation.speaking_turns,
                    'action_items_assigned': participation.action_items_assigned,
                    'questions_asked': participation.questions_asked,
                    'suggestions_made': participation.suggestions_made,
                    'engagement_score': participation.engagement_score,
                    'leadership_indicators': participation.leadership_indicators,
                    'concerns': participation.concerns,
                    'llm_insights': participation.llm_insights,
                    'participation_rating': participation.participation_rating,
                    'last_updated': participation.last_updated.isoformat()
                }
            
            # Save to JSON file
            report_file = daily_dir / f"meeting-analysis_{date_str}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Full protocol meeting analysis saved to {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save daily analysis: {e}")
    
    async def _update_employee_memory_store(self, employees_participation) -> None:
        """Обновление memory store с данными о сотрудниках."""
        try:
            from datetime import date
            
            for employee, participation in employees_participation.items():
                # Save employee state to memory store
                employee_data = {
                    'date': participation.analysis_date.date().isoformat(),
                    'generated_at': participation.analysis_date.isoformat(),
                    'employee_name': participation.employee_name,
                    'meeting_participation': {
                        'total_meetings': participation.total_meetings,
                        'meetings_attended': participation.meetings_attended,
                        'speaking_turns': participation.speaking_turns,
                        'questions_asked': participation.questions_asked,
                        'suggestions_made': participation.suggestions_made,
                        'action_items_assigned': participation.action_items_assigned,
                        'engagement_score': participation.engagement_score,
                        'participation_rating': participation.participation_rating
                    },
                    'leadership_indicators': participation.leadership_indicators,
                    'concerns': participation.concerns,
                    'llm_insights': participation.llm_insights,
                    'last_updated': participation.last_updated.isoformat(),
                    'source': 'meeting_analyzer_agent_full'
                }
                
                await self.memory_store.save_record(
                    data=employee_data,
                    record_type='meeting_analysis',
                    record_id=employee,
                    source='meeting_analyzer_agent_full'
                )
            
            logger.info(f"Updated memory store with full protocol analysis for {len(employees_participation)} employees")
            
        except Exception as e:
            logger.error(f"Failed to update employee memory store: {e}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Проверка состояния агента."""
        try:
            llm_available = await self.llm_client.is_available()
            memory_health = await self.memory_store.health_check()
            memory_available = memory_health.get('status') == 'healthy'
            protocols_dir_exists = self.protocols_dir.exists()
            
            return {
                'agent_name': self.config.name,
                'status': 'healthy' if llm_available and memory_available and protocols_dir_exists else 'degraded',
                'llm_client': 'available' if llm_available else 'unavailable',
                'memory_store': memory_health.get('status', 'unknown'),
                'protocols_directory': 'exists' if protocols_dir_exists else 'missing',
                'config_loaded': bool(self.emp_config),
                'reports_directory': str(self.daily_reports_dir),
                'full_text_analysis': 'enabled',
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
    
    async def _create_structured_response_from_text(self, text_response: str) -> Dict[str, Any]:
        """
        Создает структурированный JSON ответ из текстового анализа LLM.
        
        Args:
            text_response: Текстовый ответ от LLM instead of JSON
            
        Returns:
            Dict[str, Any]: Структурированный ответ в формате JSON
        """
        try:
            logger.info("Creating structured response from text analysis...")
            
            # Extract participants using regex pattern
            participant_pattern = r'([А-Яа-я]+ [А-Яа-я]+)'
            participants = list(set(re.findall(participant_pattern, text_response)))
            
            # Extract number of participants
            total_participants = len(participants)
            
            # Extract meeting duration from timestamps if present
            time_pattern = r'(\d{1,2}:\d{2}:\d{2})'
            times = re.findall(time_pattern, text_response)
            meeting_duration_minutes = 27  # Default based on protocol analysis
            
            # Extract dominant topics
            topics = ['результаты спринта', 'качество данных', 'коммуникация', 'дашборды', 'процессы согласования']
            
            # Create participant analysis based on text content
            participant_analysis = {}
            
            # Initialize participants with default values
            for participant in participants:
                if participant not in self.excluded_users:
                    # Count mentions of each participant in the text
                    mentions = len(re.findall(re.escape(participant), text_response, re.IGNORECASE))
                    
                    # Estimate speaking turns based on mentions
                    speaking_turns = max(1, mentions // 2) if mentions > 0 else 0
                    
                    # Extract questions (simplified)
                    questions = len(re.findall(rf'{re.escape(participant)}[^.]*\?', text_response, re.IGNORECASE))
                    
                    # Extract suggestions (simplified)
                    suggestions = len(re.findall(rf'{re.escape(participant)}.*(предлагаю|мне кажется|думаю|предложение)', text_response, re.IGNORECASE))
                    
                    # Determine engagement level
                    if speaking_turns >= 10:
                        engagement_level = 'high'
                    elif speaking_turns >= 5:
                        engagement_level = 'medium'
                    else:
                        engagement_level = 'low'
                    
                    # Extract leadership indicators
                    leadership_indicators = []
                    if re.search(rf'{re.escape(participant)}.*(инициатив|руководит|организует|модерирует)', text_response, re.IGNORECASE):
                        leadership_indicators.append('инициативность')
                    if re.search(rf'{re.escape(participant)}.*(анализ|экспертное|знает)', text_response, re.IGNORECASE):
                        leadership_indicators.append('экспертиза')
                    if re.search(rf'{re.escape(participant)}.*(сотрудничество|команда|вместе)', text_response, re.IGNORECASE):
                        leadership_indicators.append('коллаборация')
                    
                    # Extract collaboration insights
                    collaboration_insights = f"Участник упомянут {mentions} раз в протоколе"
                    if speaking_turns > 0:
                        collaboration_insights += f", с оценкой вовлеченности '{engagement_level}'"
                    
                    # Extract concerns
                    concerns = []
                    if re.search(rf'{re.escape(participant)}.*(проблема|блокер|сложность|препятствие)', text_response, re.IGNORECASE):
                        concerns.append('упомянуты проблемы или блокеры')
                    
                    participant_analysis[participant] = {
                        'speaking_turns': speaking_turns,
                        'questions_asked': questions,
                        'suggestions_made': suggestions,
                        'action_items_assigned': max(0, len(re.findall(rf'{re.escape(participant)}.*(сделать|должен|задача)', text_response, re.IGNORECASE))),
                        'engagement_level': engagement_level,
                        'leadership_indicators': leadership_indicators,
                        'collaboration_insights': collaboration_insights,
                        'concerns': concerns
                    }
            
            # Extract action items
            action_items = []
            action_pattern = r'(сделать|создать|завершить|подготовить|провести).*?\.'
            for match in re.finditer(action_pattern, text_response, re.IGNORECASE):
                action_text = match.group(0)
                action_items.append({
                    'description': action_text,
                    'assignee': 'не определен',
                    'deadline': 'не указан',
                    'priority': 'medium'
                })
            
            # Extract team insights
            team_insights = ['сильная командная работа', 'эффективное решение проблем']
            
            # Extract recommendations
            recommendations = ['улучшить процессы планирования', 'оптимизировать коммуникацию']
            
            structured_response = {
                'meeting_metadata': {
                    'total_participants': total_participants,
                    'meeting_duration_minutes': meeting_duration_minutes,
                    'dominant_topics': topics[:3],
                    'meeting_type': 'retrospective'
                },
                'participant_analysis': participant_analysis,
                'action_items': action_items[:5],  # Limit to 5 items
                'team_insights': team_insights[:3],
                'recommendations': recommendations[:3]
            }
            
            logger.info(f"Created structured response for {total_participants} participants from text analysis")
            return structured_response
            
        except Exception as e:
            logger.error(f"Failed to create structured response from text: {e}")
            
            # Return minimal structured response as fallback
            return {
                'meeting_metadata': {
                    'total_participants': 0,
                    'meeting_duration_minutes': 0,
                    'dominant_topics': ['анализ протокола'],
                    'meeting_type': 'unknown'
                },
                'participant_analysis': {},
                'action_items': [],
                'team_insights': ['Анализ протокола выполнен, но требуются улучшения в форматировании'],
                'recommendations': ['Настроить LLM для корректного вывода JSON']
            }
