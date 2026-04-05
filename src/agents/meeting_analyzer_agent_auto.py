# -*- coding: utf-8 -*-
"""
Meeting Analyzer Agent - Employee Monitoring System (Auto-scan version)

Анализирует протоколы собраний для отслеживания прогресса сотрудников,
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
from core.llm_client import LLMClient, analyze_meeting_protocol
from core.json_memory_store import JSONMemoryStore
from core.quality_metrics import QualityMetrics
from core.config import get_employee_monitoring_config

logger = logging.getLogger(__name__)


class MeetingType(Enum):
    """Типы собраний."""
    STANDUP = "standup"
    PLANNING = "planning"
    RETROSPECTIVE = "retrospective"
    DEMO = "demo"
    REVIEW = "review"
    TECHNICAL = "technical"
    GENERAL = "general"


@dataclass
class EmployeeMeetingParticipation:
    """Информация об участии сотрудника в собраниях."""
    employee_name: str
    analysis_date: datetime
    
    # Participation metrics
    total_meetings: int
    meetings_attended: int
    meetings_absent: int
    attendance_rate: float
    
    # Contribution metrics
    speaking_turns: int
    action_items_assigned: int
    action_items_completed: int
    questions_asked: int
    suggestions_made: int
    
    # Quality indicators
    engagement_score: float
    contribution_quality: float
    leadership_indicators: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    
    # Meeting types analysis
    meeting_type_participation: Dict[str, int] = field(default_factory=dict)
    
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
    completed_action_items: int
    
    # Insights and trends
    team_collaboration_insights: List[str]
    participation_patterns: List[str]
    recommendations: List[str]
    
    # Quality and metadata
    quality_score: float
    analysis_duration: timedelta
    metadata: Dict[str, Any] = field(default_factory=dict)


class MeetingAnalyzerAgent(BaseAgent):
    """
    Анализатор протоколов собраний для Employee Monitoring.
    
    Анализирует:
    - Участие сотрудников в собраниях
    - Вклад и активность
    - Выполнение действий
    - Паттерны совместной работы
    
    ВАЖНО: Удалена Git интеграция согласно первоначальным требованиям
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(
            config or AgentConfig(
                name="MeetingAnalyzerAgent",
                description="Analyzes meeting protocols for employee monitoring",
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
        
        logger.info(f"MeetingAnalyzerAgent initialized. Protocols dir: {self.protocols_dir}")
    
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
        """Парсинг файла протокола."""
        try:
            # Определяем тип файла по названию
            meeting_type = self._detect_meeting_type(file_path.name)
            
            # Извлекаем дату из имени файла или содержимого
            meeting_date = self._extract_date_from_filename(file_path.name)
            
            # Читаем содержимое
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            protocol_info = {
                'file_path': str(file_path),
                'filename': file_path.name,
                'format': file_path.suffix.lower(),
                'meeting_type': meeting_type,
                'meeting_date': meeting_date,
                'file_date': datetime.fromtimestamp(file_path.stat().st_mtime),
                'content': content,
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
            MeetingType.STANDUP.value: ['standup', 'дейли', 'daily', 'утреннее'],
            MeetingType.PLANNING.value: ['planning', 'планирование', 'sprint', 'план'],
            MeetingType.RETROSPECTIVE.value: ['retro', 'retrospective', 'ретро', 'обратная связь'],
            MeetingType.DEMO.value: ['demo', 'демо', 'showcase', 'показ'],
            MeetingType.REVIEW.value: ['review', 'обзор', 'code review', 'ревью'],
            MeetingType.TECHNICAL.value: ['technical', 'tech', 'архитектура', 'техническое'],
        }
        
        for meeting_type, keywords in type_keywords.items():
            if any(keyword in filename_lower for keyword in keywords):
                return meeting_type
        
        return MeetingType.GENERAL.value
    
    def _extract_date_from_filename(self, filename: str) -> Optional[datetime]:
        """Извлечение даты из имени файла."""
        # Паттерны для дат в именах файлов
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{2}-\d{2}-\d{4})',  # DD-MM-YYYY
            r'(\d{2}\.\d{2}\.\d{4})',  # DD.MM.YYYY
            r'(\d{4}_\d{2}_\d{2})',  # YYYY_MM_DD
            r'(\d{2}\d{2}\d{4})',  # DDMMYYYY
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
        
        # Если дату не нашли, используем дату модификации файла
        return None
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Выполнение анализа протоколов собраний.
        
        Args:
            input_data: Данные с протоколами собраний (опционально)
            
        Returns:
            AgentResult с анализом участия сотрудников
        """
        try:
            logger.info("Starting Meeting Protocol Analysis for Employee Monitoring")
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
            
            # Анализируем каждый протокол
            analyzed_protocols = []
            for protocol in meeting_protocols:
                try:
                    analysis = await self._analyze_single_protocol(protocol)
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
            
            # Добавляем LLM инсайты при необходимости
            if self.quality_threshold > 0.7:
                await self._add_llm_insights(analysis_result, employees_participation)
            
            # Рассчитываем качество анализа
            analysis_result.quality_score = await self._calculate_analysis_quality(analysis_result)
            
            # Сохраняем результаты
            await self._save_daily_analysis(analysis_result)
            
            # Обновляем memory store
            await self._update_employee_memory_store(employees_participation)
            
            # Время выполнения
            execution_time = datetime.now() - start_time
            analysis_result.analysis_duration = execution_time
            
            logger.info(f"Meeting Analysis completed in {execution_time.total_seconds():.2f}s, "
                       f"analyzed {len(analyzed_protocols)} protocols for {len(employees_participation)} employees")
            
            return AgentResult(
                success=True,
                message=f"Successfully analyzed meeting participation for {len(employees_participation)} employees",
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
            logger.error(f"Meeting Analysis failed: {e}")
            return AgentResult(
                success=False,
                message=f"Analysis failed: {str(e)}",
                data={},
                error=str(e)
            )
    
    async def _analyze_single_protocol(self, protocol: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Анализ одного протокола собрания."""
        try:
            content = protocol.get('content', '')
            meeting_type = protocol.get('meeting_type', 'general')
            
            # Извлекаем участников
            participants = await self._extract_participants(content)
            
            # Извлекаем nói участников
            speakers = await self._extract_speakers(content)
            
            # Извлекаем действия
            action_items = await self._extract_action_items(content)
            
            # Извлекаем вопросы и предложения
            questions = await self._extract_questions(content)
            suggestions = await self._extract_suggestions(content)
            
            protocol_analysis = {
                'filename': protocol.get('filename', ''),
                'meeting_type': meeting_type,
                'meeting_date': protocol.get('meeting_date'),
                'participants': participants,
                'speakers': speakers,
                'action_items': action_items,
                'questions': questions,
                'suggestions': suggestions,
                'content_length': len(content),
                'analysis_timestamp': datetime.now()
            }
            
            return protocol_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing protocol {protocol.get('filename', 'unknown')}: {e}")
            return None
    
    async def _extract_participants(self, content: str) -> List[str]:
        """Извлечение списка участников из протокола."""
        participants = []
        
        # Ищем паттерны для участников
        participant_patterns = [
            r'Участники[:\s]*([^\n]+)',
            r'Participants[:\s]*([^\n]+)',
            r'Присутствовали[:\s]*([^\n]+)',
            r'Attendees[:\s]*([^\n]+)',
            r'На встрече[:\s]*([^\n]+)',
        ]
        
        for pattern in participant_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # Разделяем по запятым, точкам с запятой и т.д.
                names = re.split(r'[,;]\s*', match.strip())
                participants.extend([name.strip() for name in names if name.strip()])
        
        # Ищем имена в тексте (с заглавной буквы)
        name_pattern = r'\b([А-Я][а-я]+\s+[А-Я][а-я]+|[A-Z][a-z]+\s+[A-Z][a-z]+)\b'
        potential_names = set(re.findall(name_pattern, content))
        
        # Фильтруем общие слова
        common_words = {
            'Тема', 'Повестка', 'Цель', 'Решение', 'Итог', 'Вывод',
            'Topic', 'Agenda', 'Goal', 'Decision', 'Result', 'Conclusion'
        }
        
        for name in potential_names:
            if name not in common_words and len(name.split()) >= 2:
                participants.append(name)
        
        return list(set(participants))  # Убираем дубликаты
    
    async def _extract_speakers(self, content: str) -> Dict[str, int]:
        """Извлекаем кто и сколько раз говорил."""
        speakers = {}
        
        # Ищем паттерны вроде "Имя: текст" или "- Имя: текст"
        speaker_patterns = [
            r'^([А-Я][а-я]+\s+[А-Я][а-я]+|[А-Я]\.\s*[А-Я][а-я]+)\s*[:\-]\s',
            r'^([A-Z][a-z]+\s+[A-Z][a-z]+|[A-Z]\.\s*[A-Z][a-z]+)\s*[:\-]\s',
            r'^\s*-\s*([А-Я][а-я]+\s+[А-Я][а-я]+|[А-Я]\.\s*[А-Я][а-я]+)\s*[:\-]\s',
        ]
        
        for pattern in speaker_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for speaker in matches:
                speakers[speaker] = speakers.get(speaker, 0) + 1
        
        return speakers
    
    async def _extract_action_items(self, content: str) -> List[Dict[str, Any]]:
        """Извлечение действий и ответственных."""
        action_items = []
        
        # Паттерны для действий
        action_patterns = [
            r'Действия?[:\s]*([^\n]+)',
            r'Action items?[:\s]*([^\n]+)',
            r'Решения?[:\s]*([^\n]+)',
            r'Decisions?[:\s]*([^\n]+)',
            r'Дальнейшие шаги?[:\s]*([^\n]+)',
            r'Next steps?[:\s]*([^\n]+)',
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # Ищем ответственных в каждом действии
                responsible = await self._extract_responsible_from_action(match)
                
                action_items.append({
                    'description': match.strip(),
                    'responsible': responsible,
                    'status': 'pending'  # По умолчанию
                })
        
        return action_items
    
    async def _extract_responsible_from_action(self, action_text: str) -> List[str]:
        """Извлечение ответственных из текста действия."""
        responsible = []
        
        # Ищем паттерны вроде "Имя сделает", "Ответственный: Имя"
        responsible_patterns = [
            r'Ответственный[:\s]*([А-Я][а-я]+\s+[А-Я][а-я]+|[A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'Ответственны[:\s]*([^\n]+)',
            r'([А-Я][а-я]+\s+[А-Я][а-я]+|[A-Z][a-z]+\s+[A-Z][a-z]+)\s*(сделает|выполнит|подготовит|отвечает)',
        ]
        
        for pattern in responsible_patterns:
            matches = re.findall(pattern, action_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                responsible.append(match.strip())
        
        return list(set(responsible))
    
    async def _extract_questions(self, content: str) -> List[Dict[str, Any]]:
        """Извлечение вопросов из протокола."""
        questions = []
        
        # Ищем паттерны вопросов
        question_patterns = [
            r'([А-Я][а-я]+\s+[А-Я][а-я]+|[A-Z][a-z]+\s+[A-Z][a-z]+)[^\n]*\?[^\n]*',
            r'Вопрос[:\s]*([^\n?]*\?)',
            r'Вопросы?[:\s]*([^\n]+)',
        ]
        
        for pattern in question_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[1] if len(match) > 1 else match[0]
                
                # Извлекаем автора вопроса
                author = None
                author_match = re.search(r'([А-Я][а-я]+\s+[А-Я][а-я]+|[A-Z][a-z]+\s+[A-Z][a-z]+)', match)
                if author_match:
                    author = author_match.group(1)
                
                questions.append({
                    'text': match.strip(),
                    'author': author,
                    'answered': False  # По умолчанию
                })
        
        return questions
    
    async def _extract_suggestions(self, content: str) -> List[Dict[str, Any]]:
        """Извлечение предложений из протокола."""
        suggestions = []
        
        # Ищем паттерны предложений
        suggestion_patterns = [
            r'Предложения?[:\s]*([^\n]+)',
            r'Suggestions?[:\s]*([^\n]+)',
            r'([А-Я][а-я]+\s+[А-Я][а-я]+)[^\n]*(предлагает|предложила|предложил)[^\n]*',
        ]
        
        for pattern in suggestion_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[1] if len(match) > 1 else match[0]
                
                # Извлекаем автора предложения
                author = None
                author_match = re.search(r'([А-Я][а-я]+\s+[А-Я][а-я]+|[A-Z][a-z]+\s+[A-Z][a-z]+)', match)
                if author_match:
                    author = author_match.group(1)
                
                suggestions.append({
                    'text': match.strip(),
                    'author': author
                })
        
        return suggestions
    
    async def _group_participation_by_employee(self, analyzed_protocols: List[Dict[str, Any]]) -> Dict[str, EmployeeMeetingParticipation]:
        """Группировка анализа по сотрудникам."""
        employees_participation = {}
        
        for protocol in analyzed_protocols:
            participants = protocol.get('participants', [])
            speakers = protocol.get('speakers', {})
            action_items = protocol.get('action_items', [])
            questions = protocol.get('questions', [])
            suggestions = protocol.get('suggestions', [])
            meeting_type = protocol.get('meeting_type', 'general')
            
            # Обрабатываем всех участников
            for participant in participants:
                if participant in self.excluded_users:
                    continue
                
                if participant not in employees_participation:
                    employees_participation[participant] = EmployeeMeetingParticipation(
                        employee_name=participant,
                        analysis_date=datetime.now(),
                        total_meetings=0,
                        meetings_attended=0,
                        meetings_absent=0,
                        attendance_rate=0.0,
                        speaking_turns=0,
                        action_items_assigned=0,
                        action_items_completed=0,
                        questions_asked=0,
                        suggestions_made=0,
                        engagement_score=0.0,
                        contribution_quality=0.0,
                        meeting_type_participation={}
                    )
                
                participation = employees_participation[participant]
                
                # Обновляем метрики
                participation.total_meetings += 1
                participation.meetings_attended += 1
                
                # Участие в обсуждении
                speaking_turns = speakers.get(participant, 0)
                participation.speaking_turns += speaking_turns
                
                # Действия
                for action in action_items:
                    if participant in action.get('responsible', []):
                        participation.action_items_assigned += 1
                        if action.get('status') == 'completed':
                            participation.action_items_completed += 1
                
                # Вопросы
                for question in questions:
                    if question.get('author') == participant:
                        participation.questions_asked += 1
                
                # Предложения
                for suggestion in suggestions:
                    if suggestion.get('author') == participant:
                        participation.suggestions_made += 1
                
                # Типы встреч
                participation.meeting_type_participation[meeting_type] = \
                    participation.meeting_type_participation.get(meeting_type, 0) + 1
        
        # Рассчитываем производные метрики
        for participation in employees_participation.values():
            # Attendance rate
            participation.attendance_rate = participation.meetings_attended / max(participation.total_meetings, 1)
            
            # Engagement score
            participation.engagement_score = min(1.0, (
                participation.speaking_turns * 0.3 +
                participation.questions_asked * 0.2 +
                participation.suggestions_made * 0.3 +
                participation.action_items_assigned * 0.2
            ) / max(participation.total_meetings, 1))
            
            # Contribution quality
            completion_rate = participation.action_items_completed / max(participation.action_items_assigned, 1)
            participation.contribution_quality = min(1.0, completion_rate * 0.7 + participation.engagement_score * 0.3)
            
            # Leadership indicators
            if participation.speaking_turns > participation.total_meetings * 2:
                participation.leadership_indicators.append("Активное участие в обсуждениях")
            
            if participation.suggestions_made > participation.total_meetings:
                participation.leadership_indicators.append("Делает предложения")
            
            if participation.action_items_assigned > participation.total_meetings:
                participation.leadership_indicators.append("Берет на себя ответственность")
            
            # Concerns
            if participation.attendance_rate < 0.7:
                participation.concerns.append("Низкая посещаемость")
            
            if participation.speaking_turns == 0:
                participation.concerns.append("Не участвует в обсуждениях")
        
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
        completed_action_items = sum(p.action_items_completed for p in employees_participation.values())
        
        # Generate insights
        team_insights = await self._generate_team_insights(employees_participation, analyzed_protocols)
        
        # Generate participation patterns
        patterns = await self._identify_participation_patterns(employees_participation)
        
        # Generate recommendations
        recommendations = await self._generate_team_recommendations(employees_participation, patterns)
        
        return DailyMeetingAnalysisResult(
            analysis_date=analysis_date,
            employees_participation=employees_participation,
            total_employees=total_employees,
            total_meetings_analyzed=total_meetings_analyzed,
            avg_attendance_rate=avg_attendance_rate,
            total_action_items=total_action_items,
            completed_action_items=completed_action_items,
            team_collaboration_insights=team_insights,
            participation_patterns=patterns,
            recommendations=recommendations,
            quality_score=0.0,  # Will be calculated later
            analysis_duration=timedelta()  # Will be set later
        )
    
    async def _generate_team_insights(self, employees_participation: Dict[str, EmployeeMeetingParticipation],
                                    analyzed_protocols: List[Dict[str, Any]]) -> List[str]:
        """Генерация инсайтов по командной работе."""
        insights = []
        
        if not employees_participation:
            return insights
        
        # Attendance insights
        avg_attendance = sum(p.attendance_rate for p in employees_participation.values()) / len(employees_participation)
        if avg_attendance >= 0.9:
            insights.append("Отличная посещаемость командных встреч")
        elif avg_attendance >= 0.7:
            insights.append("Хорошая посещаемость встреч")
        else:
            insights.append("Требуется улучшить посещаемость встреч")
        
        # Engagement insights
        avg_engagement = sum(p.engagement_score for p in employees_participation.values()) / len(employees_participation)
        if avg_engagement >= 0.7:
            insights.append("Высокая вовлеченность команды в обсуждения")
        elif avg_engagement >= 0.5:
            insights.append("Средняя вовлеченность команды")
        else:
            insights.append("Низкая вовлеченность команды в обсуждения")
        
        # Action items insights
        total_assigned = sum(p.action_items_assigned for p in employees_participation.values())
        total_completed = sum(p.action_items_completed for p in employees_participation.values())
        
        if total_assigned > 0:
            completion_rate = total_completed / total_assigned
            if completion_rate >= 0.8:
                insights.append("Хорошее выполнение задач по итогам встреч")
            elif completion_rate >= 0.6:
                insights.append("Среднее выполнение задач по итогам встреч")
            else:
                insights.append("Требуется улучшение выполнения задач по итогам встреч")
        
        # Meeting type insights
        meeting_types = {}
        for protocol in analyzed_protocols:
            meeting_type = protocol.get('meeting_type', 'general')
            meeting_types[meeting_type] = meeting_types.get(meeting_type, 0) + 1
        
        if len(meeting_types) >= 3:
            insights.append("Разнообразный формат встреч - хорошо для команды")
        
        # Leadership insights
        leaders_count = sum(1 for p in employees_participation.values() if p.leadership_indicators)
        if leaders_count >= len(employees_participation) * 0.3:
            insights.append("Хорошая развитость лидерских качеств в команде")
        
        return insights
    
    async def _identify_participation_patterns(self, employees_participation: Dict[str, EmployeeMeetingParticipation]) -> List[str]:
        """Идентификация паттернов участия."""
        patterns = []
        
        if not employees_participation:
            return patterns
        
        # Active vs passive
        active_count = sum(1 for p in employees_participation.values() if p.engagement_score >= 0.7)
        passive_count = sum(1 for p in employees_participation.values() if p.engagement_score < 0.3)
        
        if active_count >= len(employees_participation) * 0.5:
            patterns.append(f"Большинство команды ({active_count} человек) активно участвуют в обсуждениях")
        
        if passive_count >= len(employees_participation) * 0.3:
            patterns.append(f"Значительная часть команды ({passive_count} человек) пассивна на встречах")
        
        # Attendance patterns
        good_attendance = sum(1 for p in employees_participation.values() if p.attendance_rate >= 0.9)
        poor_attendance = sum(1 for p in employees_participation.values() if p.attendance_rate < 0.7)
        
        if good_attendance >= len(employees_participation) * 0.7:
            patterns.append(f"Стабильная посещаемость у {good_attendance} сотрудников")
        
        if poor_attendance > 0:
            patterns.append(f"Проблемы с посещаемостью у {poor_attendance} сотрудников")
        
        # Suggestion patterns
        suggesters = sum(1 for p in employees_participation.values() if p.suggestions_made > 0)
        if suggesters >= len(employees_participation) * 0.4:
            patterns.append("Множество сотрудников вносят предложения и идеи")
        
        return patterns
    
    async def _generate_team_recommendations(self, employees_participation: Dict[str, EmployeeMeetingParticipation],
                                           patterns: List[str]) -> List[str]:
        """Генерация рекомендаций для команды."""
        recommendations = []
        
        if not employees_participation:
            return recommendations
        
        # Low participation recommendations
        low_participation = [emp for emp, p in employees_participation.items() if p.engagement_score < 0.3]
        if low_participation:
            recommendations.append(f"Стимулировать участие {len(low_participation)} пассивных сотрудников в обсуждениях")
        
        # Attendance recommendations
        poor_attendance = [emp for emp, p in employees_participation.items() if p.attendance_rate < 0.7]
        if poor_attendance:
            recommendations.append(f"Обсудить причины низкой посещаемости у {len(poor_attendance)} сотрудников")
        
        # Action items recommendations
        low_completion = [emp for emp, p in employees_participation.items() 
                         if p.action_items_assigned > 0 and p.action_items_completed / p.action_items_assigned < 0.5]
        if low_completion:
            recommendations.append(f"Помочь с выполнением задач {len(low_completion)} сотрудникам")
        
        # Meeting format recommendations
        meeting_types = {}
        for p in employees_participation.values():
            for meeting_type, count in p.meeting_type_participation.items():
                meeting_types[meeting_type] = meeting_types.get(meeting_type, 0) + count
        
        if not meeting_types:
            recommendations.append("Внести больше структурированности в формат встреч")
        
        # Leadership recommendations
        potential_leaders = [emp for emp, p in employees_participation.items() 
                           if len(p.leadership_indicators) >= 2]
        if potential_leaders:
            recommendations.append(f"Рассмотреть лидерский потенциал у {len(potential_leaders)} сотрудников")
        
        return recommendations
    
    async def _add_llm_insights(self, analysis_result: DailyMeetingAnalysisResult,
                              employees_participation: Dict[str, EmployeeMeetingParticipation]) -> None:
        """Добавление LLM-инсайтов к анализу."""
        try:
            # Готовим данные для LLM
            summary_data = self._prepare_meeting_data_for_llm(employees_participation)
            
            # Log full meeting data being sent to LLM
            logger.info("=== FULL MEETING DATA BEING SENT TO LLM ===")
            logger.info(f"Total employees: {len(employees_participation)}")
            for employee, participation in employees_participation.items():
                employee_data = {
                    'employee_name': participation.employee_name,
                    'total_meetings': participation.total_meetings,
                    'meetings_attended': participation.meetings_attended,
                    'attendance_rate': participation.attendance_rate,
                    'speaking_turns': participation.speaking_turns,
                    'action_items_assigned': participation.action_items_assigned,
                    'action_items_completed': participation.action_items_completed,
                    'questions_asked': participation.questions_asked,
                    'suggestions_made': participation.suggestions_made,
                    'engagement_score': participation.engagement_score,
                    'contribution_quality': participation.contribution_quality,
                    'leadership_indicators': participation.leadership_indicators,
                    'concerns': participation.concerns,
                    'meeting_type_participation': participation.meeting_type_participation
                }
                logger.info(f"Employee {employee}: {json.dumps(employee_data, ensure_ascii=False, indent=2)}")
            logger.info("=== END MEETING DATA ===")
            
            # Создаем промпт для LLM с строгим JSON форматом
            llm_prompt = f"""
Ты - аналитик протоколов собраний для системы мониторинга сотрудников. Проанализируй следующие данные о участии в собраниях и предоставь СТРОГО ВАЛИДНЫЙ JSON ответ.

ДАННЫЕ О УЧАСТИИ В СОБРАНИЯХ:
{json.dumps(summary_data, ensure_ascii=False, indent=2)}

ВАЖНО: Верни ТОЛЬКО JSON объект, без дополнительного текста, markdown форматирования или объяснений.

Формат ответа:
{{
    "employee_analysis": {{
        "ИмяСотрудника1": {{
            "attendance_rate": число от 0 до 1,
            "engagement_level": "high/medium/low",
            "participation_rating": число от 1 до 10,
            "leadership_indicators": ["признак1", "признак2"],
            "collaboration_insights": "детальный анализ участия",
            "concerns": ["проблема1", "проблема2"],
            "recommendations": ["рекомендация1", "рекомендация2"]
        }}
    }},
    "team_insights": ["инсайт1", "инсайт2"],
    "recommendations": ["рекомендация1", "рекомендация2"]
}}

Анализируй:
1. Уровень участия и вовлеченности каждого сотрудника
2. Лидерские качества и инициативность
3. Качество вклада в командную работу
4. Проблемы и области для улучшения
5. Командные паттерны взаимодействия

СТРОГО СЛЕДУЙ ФОРМАТУ JSON БЕЗ ОТКЛОНЕНИЙ!
"""
            
            # Send to LLM using correct API
            logger.info("Sending comprehensive meeting analysis to LLM")
            from core.llm_client import LLMRequest
            
            llm_request = LLMRequest(
                prompt=llm_prompt,
                system_prompt="Ты - эксперт по анализу протоколов собраний и мониторингу командной работы. Предоставляй детальный анализ в формате JSON.",
                max_tokens=4000,
                temperature=0.7
            )
            
            llm_response_obj = await self.llm_client.generate_response(llm_request)
            llm_response = llm_response_obj.content
            
            if llm_response:
                logger.info("Received LLM analysis response")
                # Try to parse JSON response with improved error handling
                try:
                    # First, try to parse as-is
                    try:
                        analysis_result_llm = json.loads(llm_response)
                    except json.JSONDecodeError:
                        pass
                    
                    # Extract JSON from response (handle markdown and extra text)
                    json_patterns = [
                        r'```json\s*(\{.*?\})\s*```',  # JSON in code blocks
                        r'```\s*(\{.*?\})\s*```',      # JSON in code blocks without language
                        r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',  # Simple JSON
                    ]
                    
                    import re
                    for pattern in json_patterns:
                        matches = re.findall(pattern, llm_response, re.DOTALL | re.IGNORECASE)
                        for match in matches:
                            try:
                                # Clean up the JSON string
                                json_content = match.strip()
                                # Fix common JSON issues
                                json_content = re.sub(r',\s*}', '}', json_content)  # Remove trailing commas
                                json_content = re.sub(r',\s*]', ']', json_content)  # Remove trailing commas in arrays
                                
                                analysis_result_llm = json.loads(json_content)
                                logger.info(f"Successfully parsed JSON using pattern: {pattern}")
                                break
                            except json.JSONDecodeError as e:
                                logger.debug(f"Pattern {pattern} failed: {e}")
                                continue
                        else:
                            continue
                        break
                    else:
                        # Try to find JSON between first { and last }
                        json_start = llm_response.find('{')
                        json_end = llm_response.rfind('}') + 1
                        
                        if json_start != -1 and json_end > json_start:
                            json_content = llm_response[json_start:json_end]
                            # Clean up common issues
                            json_content = re.sub(r',\s*}', '}', json_content)
                            json_content = re.sub(r',\s*]', ']', json_content)
                            
                            try:
                                analysis_result_llm = json.loads(json_content)
                                logger.info("Successfully parsed JSON using fallback method")
                            except json.JSONDecodeError as e:
                                logger.debug(f"Fallback JSON parse failed: {e}")
                                logger.warning("No valid JSON found in LLM response")
                                logger.debug(f"LLM response preview: {llm_response[:500]}...")
                                return
                    
                    # Распределяем инсайты по сотрудникам
                    if 'employee_analysis' in analysis_result_llm:
                        for employee_name, insights in analysis_result_llm['employee_analysis'].items():
                            if employee_name in employees_participation:
                                employees_participation[employee_name].llm_insights = insights.get('collaboration_insights', '')
                                # Обновляем рейтинг на основе LLM оценки
                                if 'participation_rating' in insights:
                                    employees_participation[employee_name].participation_rating = insights['participation_rating']
                    
                    # Добавляем командные инсайты
                    if 'team_insights' in analysis_result_llm:
                        analysis_result.team_collaboration_insights.extend(analysis_result_llm['team_insights'])
                    
                    if 'recommendations' in analysis_result_llm:
                        analysis_result.recommendations.extend(analysis_result_llm['recommendations'])
                    
                except Exception as e:
                    logger.error(f"Failed to parse LLM response: {e}")
                    logger.warning("Failed to add LLM insights: Invalid JSON response")
            else:
                logger.warning("Empty LLM response")
                logger.warning("Failed to add LLM insights: Invalid JSON response")
                
        except Exception as e:
            logger.warning(f"Failed to add LLM insights: {e}")
    
    def _prepare_meeting_data_for_llm(self, employees_participation: Dict[str, EmployeeMeetingParticipation]) -> str:
        """Подготовка данных о встречах для LLM анализа."""
        summary_parts = [
            "Meeting Participation Analysis Summary",
            f"Analysis Date: {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "Employee Participation Details:"
        ]
        
        for employee, participation in employees_participation.items():
            summary_parts.extend([
                f"\nEmployee: {employee}",
                f"  Attendance: {participation.attendance_rate:.1%} ({participation.meetings_attended}/{participation.total_meetings})",
                f"  Speaking Turns: {participation.speaking_turns}",
                f"  Action Items: {participation.action_items_completed}/{participation.action_items_assigned}",
                f"  Questions: {participation.questions_asked}",
                f"  Suggestions: {participation.suggestions_made}",
                f"  Engagement Score: {participation.engagement_score:.2f}",
                f"  Leadership: {', '.join(participation.leadership_indicators) if participation.leadership_indicators else 'None'}",
                f"  Concerns: {', '.join(participation.concerns) if participation.concerns else 'None'}"
            ])
        
        return "\n".join(summary_parts)
    
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
                'participation_patterns': analysis_result.participation_patterns,
                'recommendations': analysis_result.recommendations,
                'quality_score': analysis_result.quality_score,
                'analysis_duration_seconds': analysis_result.analysis_duration.total_seconds(),
                'employees_participation': {},
                'metadata': analysis_result.metadata
            }
            
            # Serialize employee participation
            for employee, participation in analysis_result.employees_participation.items():
                analysis_data['employees_participation'][employee] = {
                    'employee_name': participation.employee_name,
                    'analysis_date': participation.analysis_date.isoformat(),
                    'total_meetings': participation.total_meetings,
                    'meetings_attended': participation.meetings_attended,
                    'meetings_absent': participation.meetings_absent,
                    'attendance_rate': participation.attendance_rate,
                    'speaking_turns': participation.speaking_turns,
                    'action_items_assigned': participation.action_items_assigned,
                    'action_items_completed': participation.action_items_completed,
                    'questions_asked': participation.questions_asked,
                    'suggestions_made': participation.suggestions_made,
                    'engagement_score': participation.engagement_score,
                    'contribution_quality': participation.contribution_quality,
                    'leadership_indicators': participation.leadership_indicators,
                    'concerns': participation.concerns,
                    'meeting_type_participation': participation.meeting_type_participation,
                    'llm_insights': participation.llm_insights,
                    'participation_rating': participation.participation_rating,
                    'last_updated': participation.last_updated.isoformat()
                }
            
            # Save to JSON file
            report_file = daily_dir / f"meeting-analysis_{date_str}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Meeting analysis saved to {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save daily analysis: {e}")
    
    async def _update_employee_memory_store(self, employees_participation) -> None:
        """Обновление memory store с данными о сотрудниках."""
        try:
            from datetime import date
            
            for employee, participation in employees_participation.items():
                # Save employee state to memory store with required schema fields
                employee_data = {
                    # Required fields for schema validation
                    'date': participation.analysis_date.date().isoformat(),
                    'generated_at': participation.analysis_date.isoformat(),
                    'data_sources': {
                        'meeting_data': {
                            'last_updated': participation.analysis_date.isoformat(),
                            'quality_score': participation.contribution_quality * 100,
                            'record_count': participation.total_meetings
                        }
                    },
                    'employee_performance': {
                        employee: {
                            'collaboration': {
                                'score': participation.engagement_score * 10,
                                'meetings_attended': participation.meetings_attended,
                                'meetings_total': participation.total_meetings,
                                'speaking_turns': participation.speaking_turns,
                                'suggestions_made': participation.suggestions_made,
                                'action_items_completed': participation.action_items_completed
                            }
                        }
                    },
                    'project_health': {
                        'team_collaboration': {
                            'overall_health': participation.engagement_score * 10,
                            'team_utilization': participation.attendance_rate * 100
                        }
                    },
                    'system_metrics': {
                        'data_processing_time': 0.0,
                        'quality_score': participation.contribution_quality * 100,
                        'insights_generated': len(participation.leadership_indicators) + len(participation.concerns)
                    },
                    '_metadata': {
                        'data_type': 'daily_summary_data',
                        'persisted_at': participation.analysis_date.isoformat(),
                        'persisted_by': 'meeting_analyzer_agent',
                        'version': '1.0.0'
                    },
                    
                    # Original data for compatibility
                    'employee_name': participation.employee_name,
                    'analysis_date': participation.analysis_date.isoformat(),
                    'participation_metrics': {
                        'total_meetings': participation.total_meetings,
                        'meetings_attended': participation.meetings_attended,
                        'attendance_rate': participation.attendance_rate,
                        'speaking_turns': participation.speaking_turns,
                        'engagement_score': participation.engagement_score
                    },
                    'contribution_metrics': {
                        'action_items_assigned': participation.action_items_assigned,
                        'action_items_completed': participation.action_items_completed,
                        'questions_asked': participation.questions_asked,
                        'suggestions_made': participation.suggestions_made,
                        'contribution_quality': participation.contribution_quality
                    },
                    'leadership_indicators': participation.leadership_indicators,
                    'concerns': participation.concerns,
                    'meeting_type_participation': participation.meeting_type_participation,
                    'llm_insights': participation.llm_insights,
                    'participation_rating': participation.participation_rating,
                    'last_updated': participation.last_updated.isoformat()
                }
                
                await self.memory_store.save_record(
                    data=employee_data,
                    record_type='daily_summary_data',
                    record_id=employee,
                    source='meeting_analyzer_agent'
                )
            
            logger.info(f"Updated memory store with meeting state for {len(employees_participation)} employees")
            
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
