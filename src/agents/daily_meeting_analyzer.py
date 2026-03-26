"""
Daily Meeting Analyzer Agent

Analyzes meeting protocols to extract action items, decisions,
participants, and generate insights for daily reporting.
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from ..core.base_agent import BaseAgent, AgentConfig, AgentResult
from ..core.llm_client import LLMClient, LLMRequest, analyze_meeting_protocol
from ..core.json_memory_store import JSONMemoryStore
from ..core.schemas.meeting_schema import MeetingAnalysisSchema
from ..core.quality_metrics import QualityMetrics
from ..core.config import get_config

logger = logging.getLogger(__name__)


class ActionItemStatus(Enum):
    """Action item status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class Priority(Enum):
    """Priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Participant:
    """Meeting participant information."""
    name: str
    role: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    is_responsible: bool = False
    action_items_count: int = 0


@dataclass
class ActionItem:
    """Action item extracted from meeting."""
    id: str
    description: str
    responsible: str
    deadline: Optional[datetime]
    status: ActionItemStatus
    priority: Priority
    context: str
    meeting_date: datetime
    project_kanban: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class MeetingInfo:
    """Basic meeting information."""
    meeting_id: str
    title: str
    date: datetime
    duration: Optional[timedelta]
    location: Optional[str]
    meeting_type: str
    organizer: Optional[str]
    attendees: List[Participant]
    total_attendees: int


@dataclass
class MeetingAnalysisResult:
    """Complete meeting analysis result."""
    analysis_date: datetime
    meeting_info: MeetingInfo
    action_items: List[ActionItem]
    decisions: List[str]
    key_topics: List[str]
    next_steps: List[str]
    quality_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class DailyMeetingAnalyzer(BaseAgent):
    """
    Daily Meeting Analysis Agent.
    
    Analyzes meeting protocols to extract:
    - Action items with responsibility tracking
    - Meeting decisions and outcomes
    - Participants and their roles
    - Key topics and discussions
    - Next steps and follow-ups
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize Daily Meeting Analyzer.
        
        Args:
            config: Agent configuration
        """
        super().__init__(
            config or AgentConfig(
                name="DailyMeetingAnalyzer",
                description="Analyzes meeting protocols for action items and insights",
                version="1.0.0"
            )
        )
        
        # Initialize components
        self.llm_client = LLMClient()
        self.memory_store = JSONMemoryStore()
        self.quality_metrics = QualityMetrics()
        
        # Load configuration
        app_config = get_config()
        self.meeting_config = app_config.get('meeting', {})
        self.analysis_config = self.config.parameters.get('analysis', {})
        
        # Analysis parameters
        self.max_protocols_per_run = self.analysis_config.get('max_protocols_per_run', 50)
        self.min_participants_for_analysis = self.analysis_config.get('min_participants_for_analysis', 2)
        self.action_item_keywords = self.analysis_config.get('action_item_keywords', [
            'действие', 'ответственный', 'срок', 'выполнить', 'подготовить',
            'action', 'responsible', 'deadline', 'complete', 'prepare'
        ])
        
        # Regex patterns for parsing
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.date_pattern = re.compile(r'\b\d{1,2}\.\d{1,2}\.\d{4}\b|\b\d{4}-\d{2}-\d{2}\b')
        self.time_pattern = re.compile(r'\b\d{1,2}:\d{2}\b')
        self.name_pattern = re.compile(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b|\b[А-Я][а-я]+\s+[А-Я][а-я]+\b')
        
        logger.info("DailyMeetingAnalyzer initialized")
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute meeting analysis.
        
        Args:
            input_data: Analysis input data containing meeting protocols and filters
            
        Returns:
            AgentResult with analysis findings
        """
        try:
            logger.info("Starting Daily Meeting Analysis")
            start_time = datetime.now()
            
            # Extract input parameters
            meeting_protocols = input_data.get('meeting_protocols', [])
            analysis_filters = input_data.get('filters', {})
            include_llm_analysis = input_data.get('include_llm_analysis', True)
            
            # Parse and validate protocols
            protocols = await self._parse_meeting_protocols(meeting_protocols)
            
            if not protocols:
                return AgentResult(
                    success=False,
                    message="No meeting protocols found for analysis",
                    data={}
                )
            
            # Limit protocols if necessary
            if len(protocols) > self.max_protocols_per_run:
                protocols = protocols[:self.max_protocols_per_run]
                logger.info(f"Limited analysis to {self.max_protocols_per_run} protocols")
            
            # Analyze each protocol
            analysis_results = []
            for protocol in protocols:
                try:
                    result = await self._analyze_protocol(protocol, analysis_filters)
                    if result:
                        analysis_results.append(result)
                except Exception as e:
                    logger.warning(f"Failed to analyze protocol {protocol.get('id', 'unknown')}: {e}")
                    continue
            
            if not analysis_results:
                return AgentResult(
                    success=False,
                    message="No successful protocol analyses completed",
                    data={}
                )
            
            # Aggregate results across all protocols
            aggregated_result = await self._aggregate_analysis_results(analysis_results)
            
            # Add LLM insights if requested
            if include_llm_analysis:
                await self._add_llm_insights(aggregated_result, analysis_results)
            
            # Validate and save results
            schema = MeetingAnalysisSchema()
            validated_data = await self._validate_and_format_results(aggregated_result, schema)
            
            # Save to memory store
            await self._save_analysis_results(validated_data)
            
            # Calculate execution time
            execution_time = datetime.now() - start_time
            
            logger.info(f"Daily Meeting Analysis completed in {execution_time.total_seconds():.2f}s, "
                       f"analyzed {len(analysis_results)} protocols, quality score: {aggregated_result.quality_score:.2f}")
            
            return AgentResult(
                success=True,
                message=f"Successfully analyzed {len(analysis_results)} meeting protocols",
                data=validated_data,
                metadata={
                    'execution_time': execution_time.total_seconds(),
                    'protocols_analyzed': len(analysis_results),
                    'quality_score': aggregated_result.quality_score,
                    'analysis_date': aggregated_result.analysis_date.isoformat(),
                    'total_action_items': len(aggregated_result.action_items),
                    'total_decisions': len(aggregated_result.decisions),
                    'total_participants': aggregated_result.meeting_info.total_attendees
                }
            )
            
        except Exception as e:
            logger.error(f"Daily Meeting Analysis failed: {e}")
            return AgentResult(
                success=False,
                message=f"Analysis failed: {str(e)}",
                data={},
                error=str(e)
            )
    
    async def _parse_meeting_protocols(self, protocols_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse and validate meeting protocol data."""
        valid_protocols = []
        
        for protocol in protocols_data:
            try:
                # Basic validation
                if not protocol.get('content') and not protocol.get('text'):
                    logger.warning(f"Protocol {protocol.get('id', 'unknown')} has no content")
                    continue
                
                # Ensure required fields
                parsed_protocol = {
                    'id': protocol.get('id', f"protocol_{len(valid_protocols)}"),
                    'title': protocol.get('title', 'Meeting Protocol'),
                    'date': self._parse_datetime(protocol.get('date')) or datetime.now(),
                    'content': protocol.get('content') or protocol.get('text', ''),
                    'format': protocol.get('format', 'text'),
                    'metadata': protocol.get('metadata', {})
                }
                
                valid_protocols.append(parsed_protocol)
                
            except Exception as e:
                logger.warning(f"Failed to parse protocol {protocol.get('id', 'unknown')}: {e}")
                continue
        
        return valid_protocols
    
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
                '%Y-%m-%d',
                '%d.%m.%Y %H:%M:%S',
                '%d.%m.%Y',
                '%d/%m/%Y',
                '%d-%m-%Y'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(dt_str, fmt)
                except ValueError:
                    continue
                    
        except Exception as e:
            logger.warning(f"Failed to parse datetime '{dt_str}': {e}")
        
        return None
    
    async def _analyze_protocol(self, protocol: Dict[str, Any], filters: Dict[str, Any]) -> Optional[MeetingAnalysisResult]:
        """Analyze a single meeting protocol."""
        try:
            content = protocol['content']
            meeting_date = protocol['date']
            
            # Extract meeting information
            meeting_info = await self._extract_meeting_info(protocol)
            
            # Extract participants
            participants = await self._extract_participants(content, meeting_info)
            
            # Extract action items
            action_items = await self._extract_action_items(content, meeting_date)
            
            # Extract decisions
            decisions = await self._extract_decisions(content)
            
            # Extract key topics
            key_topics = await self._extract_key_topics(content)
            
            # Extract next steps
            next_steps = await self._extract_next_steps(content)
            
            # Calculate quality score
            quality_score = await self._calculate_analysis_quality(
                meeting_info, action_items, decisions, key_topics
            )
            
            return MeetingAnalysisResult(
                analysis_date=datetime.now(),
                meeting_info=meeting_info,
                action_items=action_items,
                decisions=decisions,
                key_topics=key_topics,
                next_steps=next_steps,
                quality_score=quality_score,
                metadata={
                    'protocol_id': protocol['id'],
                    'format': protocol['format'],
                    'content_length': len(content)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze protocol {protocol.get('id', 'unknown')}: {e}")
            return None
    
    async def _extract_meeting_info(self, protocol: Dict[str, Any]) -> MeetingInfo:
        """Extract basic meeting information."""
        content = protocol['content']
        meeting_date = protocol['date']
        
        # Extract title
        title = protocol.get('title', 'Meeting Protocol')
        
        # Extract duration from content
        duration = self._extract_duration(content)
        
        # Extract location
        location = self._extract_location(content)
        
        # Extract meeting type
        meeting_type = self._extract_meeting_type(content, title)
        
        # Extract organizer
        organizer = self._extract_organizer(content)
        
        # Extract attendees
        attendees = await self._extract_participants(content, None)
        
        return MeetingInfo(
            meeting_id=protocol['id'],
            title=title,
            date=meeting_date,
            duration=duration,
            location=location,
            meeting_type=meeting_type,
            organizer=organizer,
            attendees=attendees,
            total_attendees=len(attendees)
        )
    
    def _extract_duration(self, content: str) -> Optional[timedelta]:
        """Extract meeting duration from content."""
        # Look for duration patterns
        duration_patterns = [
            r'(\d+)\s*час(?:а|ов)?',
            r'(\d+)\s*минут(?:ы|)?',
            r'(\d+)\s*ч(?:ас)?',
            r'(\d+)\s*мин'
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                if 'час' in pattern or 'ч' in pattern:
                    return timedelta(hours=value)
                else:
                    return timedelta(minutes=value)
        
        return None
    
    def _extract_location(self, content: str) -> Optional[str]:
        """Extract meeting location from content."""
        location_patterns = [
            r'Место\s*[:]\s*([^\n]+)',
            r'Локация\s*[:]\s*([^\n]+)',
            r'Location\s*[:]\s*([^\n]+)',
            r'Адрес\s*[:]\s*([^\n]+)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_meeting_type(self, content: str, title: str) -> str:
        """Extract meeting type from content and title."""
        type_keywords = {
            'plan': 'Планирование',
            'retro': 'Ретроспектива',
            'standup': 'Ежедневный стендап',
            'review': 'Обзор',
            'sprint': 'Спринт',
            'board': 'Совет директоров',
            'technical': 'Техническое совещание',
            'project': 'Проектное совещание'
        }
        
        # Check title and content for type keywords
        text = (title + ' ' + content).lower()
        
        for keyword, meeting_type in type_keywords.items():
            if keyword in text:
                return meeting_type
        
        return 'Общее совещание'
    
    def _extract_organizer(self, content: str) -> Optional[str]:
        """Extract meeting organizer from content."""
        organizer_patterns = [
            r'Организатор\s*[:]\s*([^\n]+)',
            r'Ведущий\s*[:]\s*([^\n]+)',
            r'Organizer\s*[:]\s*([^\n]+)',
            r'Chair\s*[:]\s*([^\n]+)'
        ]
        
        for pattern in organizer_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    async def _extract_participants(self, content: str, meeting_info: Optional[MeetingInfo]) -> List[Participant]:
        """Extract meeting participants from content."""
        participants = []
        
        # Find names in content
        names = self.name_pattern.findall(content)
        
        for name in names:
            # Check if it's a real name (not too common)
            if len(name.split()) >= 2 and not self._is_common_name(name):
                participant = Participant(
                    name=name,
                    is_responsible=False,
                    action_items_count=0
                )
                participants.append(participant)
        
        # Extract email addresses and associate with participants
        emails = self.email_pattern.findall(content)
        for email in emails:
            # Try to find participant with matching email domain
            for participant in participants:
                if email.lower() in participant.name.lower():
                    participant.email = email
                    break
        
        return participants
    
    def _is_common_name(self, name: str) -> bool:
        """Check if name is too common to be a person."""
        common_names = {
            'Meeting', 'Protocol', 'Project', 'Task', 'Action',
            'Decision', 'Plan', 'Review', 'Status', 'Report'
        }
        return name.strip() in common_names
    
    async def _extract_action_items(self, content: str, meeting_date: datetime) -> List[ActionItem]:
        """Extract action items from content."""
        action_items = []
        
        # Split content into lines
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Check if line contains action item keywords
            if any(keyword.lower() in line.lower() for keyword in self.action_item_keywords):
                action_item = await self._parse_action_item_line(line, i, content, meeting_date)
                if action_item:
                    action_items.append(action_item)
        
        return action_items
    
    async def _parse_action_item_line(self, line: str, line_number: int, content: str, meeting_date: datetime) -> Optional[ActionItem]:
        """Parse a single action item line."""
        try:
            # Extract responsible person
            responsible = self._extract_responsible_person(line)
            
            # Extract deadline
            deadline = self._extract_deadline(line, meeting_date)
            
            # Extract priority
            priority = self._extract_priority(line)
            
            # Clean description
            description = self._clean_action_item_description(line)
            
            if not description or not responsible:
                return None
            
            return ActionItem(
                id=f"action_{line_number}",
                description=description,
                responsible=responsible,
                deadline=deadline,
                status=ActionItemStatus.PENDING,
                priority=priority,
                context=line,
                meeting_date=meeting_date
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse action item line '{line[:50]}...': {e}")
            return None
    
    def _extract_responsible_person(self, line: str) -> Optional[str]:
        """Extract responsible person from line."""
        # Look for "ответственный:", "responsible:" patterns
        patterns = [
            r'ответственный\s*[:]\s*([^\n,;]+)',
            r'responsible\s*[:]\s*([^\n,;]+)',
            r'исполнитель\s*[:]\s*([^\n,;]+)',
            r'assignee\s*[:]\s*([^\n,;]+)',
            r'@([^\s,;]+)'  # @ mentions
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Basic validation for person name
                if len(name) > 2 and not name.isdigit():
                    return name
        
        return None
    
    def _extract_deadline(self, line: str, meeting_date: datetime) -> Optional[datetime]:
        """Extract deadline from line."""
        date_patterns = [
            r'срок\s*[:]\s*(\d{1,2}\.\d{1,2}\.\d{4})',
            r'deadline\s*[:]\s*(\d{1,2}\.\d{1,2}\.\d{4})',
            r'до\s*(\d{1,2}\.\d{1,2}\.\d{4})',
            r'до\s*(\d{4}-\d{2}-\d{2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                return self._parse_datetime(date_str)
        
        return None
    
    def _extract_priority(self, line: str) -> Priority:
        """Extract priority from line."""
        priority_keywords = {
            '_critical': Priority.CRITICAL,
            'критичный': Priority.CRITICAL,
            'high': Priority.HIGH,
            'высокий': Priority.HIGH,
            'medium': Priority.MEDIUM,
            'средний': Priority.MEDIUM,
            'low': Priority.LOW,
            'низкий': Priority.LOW
        }
        
        line_lower = line.lower()
        for keyword, priority in priority_keywords.items():
            if keyword in line_lower:
                return priority
        
        return Priority.MEDIUM
    
    def _clean_action_item_description(self, line: str) -> str:
        """Clean action item description."""
        # Remove common prefixes
        prefixes_to_remove = [
            r'^Действие\s*[:]\s*',
            r'^Action\s*[:]\s*',
            r'^Задача\s*[:]\s*',
            r'^Task\s*[:]\s*'
        ]
        
        cleaned = line.strip()
        for prefix in prefixes_to_remove:
            cleaned = re.sub(prefix, '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
    
    async def _extract_decisions(self, content: str) -> List[str]:
        """Extract decisions from content."""
        decisions = []
        lines = content.split('\n')
        
        decision_keywords = [
            'решение', 'решили', 'договорились', 'принято',
            'decision', 'decided', 'agreed', 'resolved'
        ]
        
        for line in lines:
            line = line.strip()
            if any(keyword.lower() in line.lower() for keyword in decision_keywords):
                # Check if it's a complete sentence
                if len(line) > 20 and ('.' in line or ';' in line):
                    decisions.append(line)
        
        return decisions
    
    async def _extract_key_topics(self, content: str) -> List[str]:
        """Extract key topics from content."""
        topics = []
        
        # Look for topic indicators
        topic_patterns = [
            r'Тема\s*[:]\s*([^\n]+)',
            r'Topic\s*[:]\s*([^\n]+)',
            r'Вопрос\s*[:]\s*([^\n]+)',
            r'Обсудили\s*([^\n]+)'
        ]
        
        for pattern in topic_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                topic = match.strip()
                if len(topic) > 5:
                    topics.append(topic)
        
        return topics
    
    async def _extract_next_steps(self, content: str) -> List[str]:
        """Extract next steps from content."""
        next_steps = []
        lines = content.split('\n')
        
        next_step_keywords = [
            'следующий шаг', 'далее', 'дальнейшие действия',
            'next step', 'next steps', 'further actions'
        ]
        
        for line in lines:
            line = line.strip()
            if any(keyword.lower() in line.lower() for keyword in next_step_keywords):
                if len(line) > 10:
                    next_steps.append(line)
        
        return next_steps
    
    async def _aggregate_analysis_results(self, results: List[MeetingAnalysisResult]) -> MeetingAnalysisResult:
        """Aggregate analysis results from multiple protocols."""
        if not results:
            raise ValueError("No analysis results to aggregate")
        
        # Use the first result as base
        base_result = results[0]
        
        # Aggregate action items
        all_action_items = []
        for result in results:
            all_action_items.extend(result.action_items)
        
        # Aggregate decisions
        all_decisions = []
        for result in results:
            all_decisions.extend(result.decisions)
        
        # Aggregate key topics
        all_topics = []
        for result in results:
            all_topics.extend(result.key_topics)
        
        # Aggregate next steps
        all_next_steps = []
        for result in results:
            all_next_steps.extend(result.next_steps)
        
        # Aggregate participants
        all_participants = []
        seen_participants = set()
        for result in results:
            for participant in result.meeting_info.attendees:
                if participant.name not in seen_participants:
                    all_participants.append(participant)
                    seen_participants.add(participant.name)
        
        # Create aggregated meeting info
        aggregated_meeting_info = MeetingInfo(
            meeting_id="aggregated",
            title="Aggregated Meeting Analysis",
            date=base_result.meeting_info.date,
            duration=None,
            location=None,
            meeting_type="Multiple",
            organizer=base_result.meeting_info.organizer,
            attendees=all_participants,
            total_attendees=len(all_participants)
        )
        
        # Calculate aggregate quality score
        avg_quality = sum(result.quality_score for result in results) / len(results)
        
        return MeetingAnalysisResult(
            analysis_date=datetime.now(),
            meeting_info=aggregated_meeting_info,
            action_items=all_action_items,
            decisions=all_decisions,
            key_topics=all_topics,
            next_steps=all_next_steps,
            quality_score=avg_quality,
            metadata={
                'aggregated_from': len(results),
                'original_protocols': [result.metadata.get('protocol_id') for result in results]
            }
        )
    
    async def _add_llm_insights(self, result: MeetingAnalysisResult, individual_results: List[MeetingAnalysisResult]) -> None:
        """Add LLM-powered insights to analysis results."""
        try:
            # Prepare protocol text for LLM analysis
            protocol_text = self._prepare_protocol_text_for_llm(individual_results)
            
            # Get LLM analysis
            llm_analysis = await analyze_meeting_protocol(protocol_text)
            
            # Merge with existing results
            if 'action_items' in llm_analysis:
                # Add LLM-detected action items
                for item in llm_analysis['action_items']:
                    try:
                        action_item = ActionItem(
                            id=f"llm_{len(result.action_items)}",
                            description=item.get('description', ''),
                            responsible=item.get('responsible', ''),
                            deadline=self._parse_datetime(item.get('deadline')),
                            status=ActionItemStatus.PENDING,
                            priority=Priority.MEDIUM,
                            context="LLM detected",
                            meeting_date=result.meeting_info.date
                        )
                        result.action_items.append(action_item)
                    except Exception as e:
                        logger.warning(f"Failed to parse LLM action item: {e}")
            
            if 'decisions' in llm_analysis:
                result.decisions.extend(llm_analysis['decisions'])
            
            if 'key_topics' in llm_analysis:
                result.key_topics.extend(llm_analysis['key_topics'])
            
            if 'next_steps' in llm_analysis:
                result.next_steps.extend(llm_analysis['next_steps'])
            
            # Add LLM metadata
            result.metadata['llm_analysis'] = llm_analysis
            
        except Exception as e:
            logger.warning(f"Failed to add LLM insights: {e}")
    
    def _prepare_protocol_text_for_llm(self, results: List[MeetingAnalysisResult]) -> str:
        """Prepare protocol text for LLM analysis."""
        text_parts = ["Meeting Protocols Analysis:"]
        
        for result in results:
            text_parts.append(f"\nMeeting: {result.meeting_info.title}")
            text_parts.append(f"Date: {result.meeting_info.date.strftime('%Y-%m-%d')}")
            text_parts.append(f"Participants: {', '.join([p.name for p in result.meeting_info.attendees[:5]])}")
            
            if result.action_items:
                text_parts.append("Action Items:")
                for item in result.action_items[:3]:
                    text_parts.append(f"- {item.description} (Responsible: {item.responsible})")
            
            if result.decisions:
                text_parts.append("Decisions:")
                for decision in result.decisions[:3]:
                    text_parts.append(f"- {decision}")
        
        return '\n'.join(text_parts)
    
    async def _calculate_analysis_quality(
        self, 
        meeting_info: MeetingInfo, 
        action_items: List[ActionItem], 
        decisions: List[str], 
        key_topics: List[str]
    ) -> float:
        """Calculate analysis quality score."""
        try:
            quality_factors = []
            
            # Participant count score
            participant_score = min(1.0, meeting_info.total_attendees / 5.0)
            quality_factors.append(participant_score)
            
            # Action items score
            action_items_score = min(1.0, len(action_items) / 3.0)
            quality_factors.append(action_items_score)
            
            # Decisions score
            decisions_score = min(1.0, len(decisions) / 2.0)
            quality_factors.append(decisions_score)
            
            # Topics score
            topics_score = min(1.0, len(key_topics) / 3.0)
            quality_factors.append(topics_score)
            
            # Calculate overall quality
            overall_quality = sum(quality_factors) / len(quality_factors)
            return min(1.0, max(0.0, overall_quality))
            
        except Exception as e:
            logger.warning(f"Failed to calculate quality score: {e}")
            return 0.5
    
    async def _validate_and_format_results(self, result: MeetingAnalysisResult, schema) -> Dict[str, Any]:
        """Validate and format analysis results."""
        try:
            # Convert to dictionary for schema validation
            result_dict = {
                'analysis_date': result.analysis_date.isoformat(),
                'meeting_info': {
                    'meeting_id': result.meeting_info.meeting_id,
                    'title': result.meeting_info.title,
                    'date': result.meeting_info.date.isoformat(),
                    'duration': result.meeting_info.duration.total_seconds() if result.meeting_info.duration else None,
                    'location': result.meeting_info.location,
                    'meeting_type': result.meeting_info.meeting_type,
                    'organizer': result.meeting_info.organizer,
                    'attendees': [
                        {
                            'name': att.name,
                            'role': att.role,
                            'email': att.email,
                            'department': att.department,
                            'is_responsible': att.is_responsible,
                            'action_items_count': att.action_items_count
                        }
                        for att in result.meeting_info.attendees
                    ],
                    'total_attendees': result.meeting_info.total_attendees
                },
                'action_items': [
                    {
                        'id': item.id,
                        'description': item.description,
                        'responsible': item.responsible,
                        'deadline': item.deadline.isoformat() if item.deadline else None,
                        'status': item.status.value,
                        'priority': item.priority.value,
                        'context': item.context,
                        'meeting_date': item.meeting_date.isoformat(),
                        'project_kanban': item.project_kanban,
                        'tags': item.tags
                    }
                    for item in result.action_items
                ],
                'decisions': result.decisions,
                'key_topics': result.key_topics,
                'next_steps': result.next_steps,
                'quality_score': result.quality_score,
                'metadata': result.metadata
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
                record_type='meeting_analysis',
                source='daily_meeting_analyzer'
            )
            
            logger.info("Meeting analysis results saved to memory store")
            
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
