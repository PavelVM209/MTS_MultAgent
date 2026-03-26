"""
Meeting Analyzer Agent - Employee Monitoring System

Analyzes meeting protocols to track employee activity, engagement,
and generate insights for employee monitoring and reporting.
"""

import asyncio
import logging
import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List,Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from ..core.base_agent import BaseAgent, AgentConfig, AgentResult
from ..core.llm_client import LLMClient, analyze_meeting_protocol
from ..core.json_memory_store import JSONMemoryStore
from ..core.quality_metrics import QualityMetrics
from ..core.config import get_employee_monitoring_config

logger = logging.getLogger(__name__)


class ActivityLevel(Enum):
    """Employee activity level in meetings."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ParticipationType(Enum):
    """Types of participation in meetings."""
    SPEAKER = "speaker"
    ORGANIZER = "organizer"
    NOTE_TAKER = "note_taker"
    DECISION_MAKER = "decision_maker"
    ACTION_OWNER = "action_owner"


@dataclass
class EmployeeMeetingActivity:
    """Employee meeting activity information."""
    employee_name: str
    analysis_date: datetime
    
    # Meeting participation metrics
    meeting_participations: int
    speaking_turns: int
    topics_initiated: int
    questions_asked: int
    decisions_influenced: int
    
    # Action items
    action_items_assigned: int
    action_items_completed: int
    action_items_overdue: int
    
    # Engagement metrics
    engagement_score: float  # 0-1 scale
    participation_score: float  # 0-1 scale
    leadership_indicators: List[str] = field(default_factory=list)
    
    # Activity patterns
    meeting_types_attended: Set[str] = field(default_factory=set)
    average_meeting_duration: Optional[timedelta] = None
    
    # LLM insights
    llm_insights: str = ""
    activity_rating: float = 0.0  # 1-10 scale
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class DailyMeetingAnalysisResult:
    """Complete daily meeting analysis result for employee monitoring."""
    analysis_date: datetime
    employees_activity: Dict[str, EmployeeMeetingActivity]
    
    # Summary statistics
    total_employees: int
    total_meetings_analyzed: int
    avg_engagement_score: float
    most_active_employees: List[str]
    least_active_employees: List[str]
    
    # Meeting insights
    meeting_types_distribution: Dict[str, int]
    total_action_items: int
    completion_rate_action_items: float
    
    # Insights and recommendations
    team_insights: List[str]
    recommendations: List[str]
    
    # Quality and metadata
    quality_score: float
    analysis_duration: timedelta
    metadata: Dict[str, Any] = field(default_factory=dict)


class MeetingAnalyzerAgent(BaseAgent):
    """
    Meeting Analysis Agent for Employee Monitoring System.
    
    Analyzes meeting protocols to track:
    - Individual employee participation and engagement
    - Action items assignment and completion
    - Leadership indicators and influence
    - Communication patterns and collaboration
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize Meeting Analyzer Agent.
        
        Args:
            config: Agent configuration
        """
        super().__init__(
            config or AgentConfig(
                name="MeetingAnalyzerAgent",
                description="Analyzes meeting protocols for employee activity monitoring",
                version="1.0.0"
            )
        )
        
        # Initialize components
        self.llm_client = LLMClient()
        self.memory_store = JSONMemoryStore()
        self.quality_metrics = QualityMetrics()
        
        # Load employee monitoring configuration
        self.emp_config = get_employee_monitoring_config()
        self.protocols_config = self.emp_config.get('protocols', {})
        self.reports_config = self.emp_config.get('reports', {})
        self.quality_config = self.emp_config.get('quality', {})
        self.employees_config = self.emp_config.get('employees', {})
        
        # Analysis parameters
        self.protocols_directory = Path(self.protocols_config.get('directory_path', '/data/meeting-protocols'))
        self.file_formats = self.protocols_config.get('file_formats', ['txt', 'pdf', 'docx'])
        self.excluded_users = set(self.employees_config.get('excluded_users', []))
        self.quality_threshold = self.quality_config.get('threshold', 0.9)
        
        # Reports directory
        self.daily_reports_dir = Path(self.reports_config.get('daily_reports_dir', './reports/daily'))
        self.daily_reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Regex patterns for parsing
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.name_pattern = re.compile(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b|\b[А-Я][а-я]+\s+[А-Я][а-я]+\b')
        self.action_item_pattern = re.compile(r'(?:действие|action|задача|task)(?::|ы)\s*(.+?)(?:\n|$)', re.IGNORECASE)
        self.responsible_pattern = re.compile(r'(?:ответственный|responsible|исполнитель)(?::|)\s*([^\n,;]+)', re.IGNORECASE)
        
        logger.info("MeetingAnalyzerAgent initialized for employee monitoring")
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute meeting analysis for employee monitoring.
        
        Args:
            input_data: Analysis input data containing meeting protocols
            
        Returns:
            AgentResult with employee activity analysis
        """
        try:
            logger.info("Starting Meeting Analysis for Employee Monitoring")
            start_time = datetime.now()
            
            # Extract meeting protocols from input
            meeting_protocols = input_data.get('meeting_protocols', [])
            
            if not meeting_protocols:
                # If no protocols provided, try to scan directory
                meeting_protocols = await self._scan_protocols_directory()
            
            if not meeting_protocols:
                return AgentResult(
                    success=False,
                    message="No meeting protocols found for analysis",
                    data={}
                )
            
            # Parse and validate protocols
            protocols = await self._parse_meeting_protocols(meeting_protocols)
            
            if not protocols:
                return AgentResult(
                    success=False,
                    message="No valid meeting protocols parsed",
                    data={}
                )
            
            # Extract employee mentions and activities
            employee_activities = await self._extract_employee_activities(protocols)
            
            # Analyze each employee's meeting activity
            employees_activity = {}
            for employee, activities in employee_activities.items():
                if employee not in self.excluded_users:
                    activity = await self._analyze_employee_activity(employee, activities, protocols)
                    employees_activity[employee] = activity
            
            # Generate team-level insights
            analysis_result = await self._generate_team_analysis(employees_activity, protocols)
            
            # Add LLM insights if quality threshold requires
            if self.quality_threshold > 0.7:
                await self._add_llm_insights(analysis_result, employees_activity)
            
            # Calculate final quality score
            analysis_result.quality_score = await self._calculate_analysis_quality(analysis_result)
            
            # Save analysis results
            await self._save_daily_analysis(analysis_result)
            
            # Update memory store with employee state
            await self._update_employee_memory_store(employees_activity)
            
            # Calculate execution time
            execution_time = datetime.now() - start_time
            analysis_result.analysis_duration = execution_time
            
            logger.info(f"Meeting Analysis completed in {execution_time.total_seconds():.2f}s, "
                       f"analyzed {len(protocols)} protocols for {len(employees_activity)} employees")
            
            return AgentResult(
                success=True,
                message=f"Successfully analyzed meeting activity for {len(employees_activity)} employees",
                data=analysis_result,
                metadata={
                    'execution_time': execution_time.total_seconds(),
                    'protocols_analyzed': len(protocols),
                    'employees_analyzed': len(employees_activity),
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
    
    async def _scan_protocols_directory(self) -> List[Dict[str, Any]]:
        """Scan protocols directory for meeting files."""
        protocols = []
        
        if not self.protocols_directory.exists():
            logger.warning(f"Protocols directory not found: {self.protocols_directory}")
            return protocols
        
        try:
            # Scan for supported file formats
            for file_path in self.protocols_directory.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower().lstrip('.') in self.file_formats:
                    try:
                        # Read file content based on format
                        content = await self._read_protocol_file(file_path)
                        
                        protocol = {
                            'id': str(file_path),
                            'title': file_path.stem,
                            'date': self._extract_date_from_filename(file_path.name) or datetime.now(),
                            'content': content,
                            'format': file_path.suffix.lower().lstrip('.'),
                            'file_path': str(file_path)
                        }
                        
                        protocols.append(protocol)
                        
                    except Exception as e:
                        logger.warning(f"Failed to read protocol file {file_path}: {e}")
                        continue
            
            logger.info(f"Scanned {len(protocols)} protocol files from {self.protocols_directory}")
            
        except Exception as e:
            logger.error(f"Failed to scan protocols directory: {e}")
        
        return protocols
    
    async def _read_protocol_file(self, file_path: Path) -> str:
        """Read protocol file content based on format."""
        content = ""
        
        try:
            if file_path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            elif file_path.suffix.lower() in ['.doc', '.docx']:
                # For now, just read as text (would need python-docx for proper parsing)
                try:
                    import docx
                    doc = docx.Document(file_path)
                    content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                except ImportError:
                    logger.warning(f"python-docx not available, treating {file_path} as text")
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
            
            elif file_path.suffix.lower() == '.pdf':
                # For now, just read as text (would need PyPDF2/pdfplumber for proper parsing)
                logger.warning(f"PDF parsing not implemented, treating {file_path} as text")
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            
            else:
                # Try to read as text
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
        
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
        
        return content
    
    def _extract_date_from_filename(self, filename: str) -> Optional[datetime]:
        """Extract date from filename."""
        # Common date patterns in filenames
        date_patterns = [
            r'(\d{4})-(\d{2})-(\d{2})',
            r'(\d{2})-(\d{2})-(\d{4})',
            r'(\d{2})\.(\d{2})\.(\d{4})',
            r'(\d{4})_(\d{2})_(\d{2})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                try:
                    groups = match.groups()
                    if len(groups[0]) == 4:  # YYYY-MM-DD format
                        year, month, day = groups
                    else:  # DD-MM-YYYY format
                        day, month, year = groups
                    
                    return datetime(int(year), int(month), int(day))
                except ValueError:
                    continue
        
        return None
    
    async def _parse_meeting_protocols(self, protocols_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse and validate meeting protocol data."""
        valid_protocols = []
        
        for protocol in protocols_data:
            try:
                # Basic validation
                if not protocol.get('content'):
                    continue
                
                # Ensure required fields
                parsed_protocol = {
                    'id': protocol.get('id', f"protocol_{len(valid_protocols)}"),
                    'title': protocol.get('title', 'Meeting Protocol'),
                    'date': self._parse_datetime(protocol.get('date')) or datetime.now(),
                    'content': protocol['content'],
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
            
        if isinstance(dt_str, datetime):
            return dt_str
        
        try:
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
    
    async def _extract_employee_activities(self, protocols: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Extract employee activities from meeting protocols."""
        employee_activities = {}
        
        for protocol in protocols:
            content = protocol['content']
            meeting_date = protocol['date']
            
            # Extract employee names from content
            mentioned_employees = self._extract_employee_names(content)
            
            # Extract action items
            action_items = self._extract_action_items(content, meeting_date)
            
            # Determine participation level
            participation_data = self._analyze_participation(content)
            
            for employee in mentioned_employees:
                if employee not in employee_activities:
                    employee_activities[employee] = []
                
                # Collect activity data for this employee in this meeting
                activity = {
                    'protocol_id': protocol['id'],
                    'meeting_title': protocol['title'],
                    'meeting_date': meeting_date,
                    'meeting_type': self._determine_meeting_type(protocol['title'], content),
                    'participation': participation_data.get(employee, {}),
                    'action_items': [item for item in action_items if item.get('responsible') == employee],
                    'mentions': content.count(employee),
                    'content_length': len(content)
                }
                
                employee_activities[employee].append(activity)
        
        return employee_activities
    
    def _extract_employee_names(self, content: str) -> List[str]:
        """Extract employee names from content."""
        names = set()
        
        # Find names using regex patterns
        found_names = self.name_pattern.findall(content)
        names.update(found_names)
        
        # Extract email addresses and convert to names if possible
        emails = self.email_pattern.findall(content)
        for email in emails:
            # Extract name from email (before @)
            local_part = email.split('@')[0]
            # Convert common formats (first.last, first_last) to names
            name_variations = [
                local_part.replace('.', ' ').title(),
                local_part.replace('_', ' ').title()
            ]
            names.update(name_variations)
        
        # Filter out common non-employee names
        excluded_names = {
            'Meeting', 'Protocol', 'Project', 'Task', 'Action',
            'Decision', 'Plan', 'Review', 'Status', 'Report',
            'Team', 'Group', 'Department', 'Management'
        }
        
        employee_names = [name for name in names if name not in excluded_names and len(name) > 2]
        
        return employee_names
    
    def _extract_action_items(self, content: str, meeting_date: datetime) -> List[Dict[str, Any]]:
        """Extract action items from content."""
        action_items = []
        
        # Split content into lines
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for action item patterns
            if any(keyword.lower() in line.lower() for keyword in ['действие', 'action', 'задача', 'task']):
                # Extract responsible person
                responsible = self._extract_responsible_person(line)
                
                # Extract deadline
                deadline = self._extract_deadline(line, meeting_date)
                
                # Clean description
                description = self._clean_action_item_description(line)
                
                if description:
                    action_item = {
                        'id': f"action_{i}",
                        'description': description,
                        'responsible': responsible,
                        'deadline': deadline,
                        'status': 'pending',
                        'meeting_date': meeting_date,
                        'context': line
                    }
                    action_items.append(action_item)
        
        return action_items
    
    def _extract_responsible_person(self, line: str) -> Optional[str]:
        """Extract responsible person from line."""
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
    
    def _clean_action_item_description(self, line: str) -> str:
        """Clean action item description."""
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
    
    def _analyze_participation(self, content: str) -> Dict[str, Dict[str, Any]]:
        """Analyze participation patterns in content."""
        participation = {}
        
        # Simple participation analysis based on mentions and context
        employees = self._extract_employee_names(content)
        
        for employee in employees:
            employee_participation = {
                'speaking_turns': content.count(employee),
                'topics_initiated': 0,  # Would need more sophisticated analysis
                'questions_asked': 0,   # Would need NLP analysis
                'decisions_influenced': 0,  # Would need context analysis
                'participation_level': self._estimate_participation_level(employee, content)
            }
            participation[employee] = employee_participation
        
        return participation
    
    def _estimate_participation_level(self, employee: str, content: str) -> str:
        """Estimate participation level for employee."""
        mentions = content.count(employee)
        content_length = len(content)
        
        # Calculate relative mention frequency
        mention_frequency = mentions / max(content_length / 1000, 1)  # mentions per 1000 characters
        
        if mention_frequency >= 5:
            return "very_high"
        elif mention_frequency >= 3:
            return "high"
        elif mention_frequency >= 1:
            return "medium"
        else:
            return "low"
    
    def _determine_meeting_type(self, title: str, content: str) -> str:
        """Determine meeting type from title and content."""
        type_keywords = {
            'планирование': 'Planning',
            'ретроспектива': 'Retrospective',
            'стендап': 'Daily Standup',
            'обзор': 'Review',
            'спринт': 'Sprint',
            'техническое': 'Technical',
            'проектное': 'Project',
            'plan': 'Planning',
            'retro': 'Retrospective',
            'standup': 'Daily Standup',
            'review': 'Review',
            'sprint': 'Sprint',
            'technical': 'Technical',
            'project': 'Project'
        }
        
        text = (title + ' ' + content).lower()
        
        for keyword, meeting_type in type_keywords.items():
            if keyword in text:
                return meeting_type
        
        return 'General'
    
    async def _analyze_employee_activity(self, employee: str, activities: List[Dict[str, Any]], protocols: List[Dict[str, Any]]) -> EmployeeMeetingActivity:
        """Analyze individual employee meeting activity."""
        analysis_date = datetime.now()
        
        # Meeting participation metrics
        meeting_participations = len(activities)
        speaking_turns = sum(activity.get('participation', {}).get('speaking_turns', 0) for activity in activities)
        topics_initiated = sum(activity.get('participation', {}).get('topics_initiated', 0) for activity in activities)
        questions_asked = sum(activity.get('participation', {}).get('questions_asked', 0) for activity in activities)
        decisions_influenced = sum(activity.get('participation', {}).get('decisions_influenced', 0) for activity in activities)
        
        # Action items
        action_items_assigned = sum(len(activity.get('action_items', [])) for activity in activities)
        action_items_completed = 0  # Would need historical data
        action_items_overdue = 0   # Would need deadline tracking
        
        # Calculate engagement and participation scores
        engagement_score = await self._calculate_engagement_score(employee, activities)
        participation_score = await self._calculate_participation_score(employee, activities)
        
        # Identify leadership indicators
        leadership_indicators = await self._identify_leadership_indicators(employee, activities)
        
        # Activity patterns
        meeting_types_attended = set(activity.get('meeting_type', 'Unknown') for activity in activities)
        average_meeting_duration = None  # Would need duration data
        
        # Initial activity rating
        activity_rating = await self._calculate_activity_rating(engagement_score, participation_score, leadership_indicators)
        
        return EmployeeMeetingActivity(
            employee_name=employee,
            analysis_date=analysis_date,
            meeting_participations=meeting_participations,
            speaking_turns=speaking_turns,
            topics_initiated=topics_initiated,
            questions_asked=questions_asked,
            decisions_influenced=decisions_influenced,
            action_items_assigned=action_items_assigned,
            action_items_completed=action_items_completed,
            action_items_overdue=action_items_overdue,
            engagement_score=engagement_score,
            participation_score=participation_score,
            leadership_indicators=leadership_indicators,
            meeting_types_attended=meeting_types_attended,
            average_meeting_duration=average_meeting_duration,
            activity_rating=activity_rating
        )
    
    async def _calculate_engagement_score(self, employee: str, activities: List[Dict[str, Any]]) -> float:
        """Calculate engagement score (0-1 scale)."""
        if not activities:
            return 0.0
        
        total_mentions = sum(activity.get('mentions', 0) for activity in activities)
        total_action_items = sum(len(activity.get('action_items', [])) for activity in activities)
        total_participations = len(activities)
        
        # Base score from participation
        participation_score = min(1.0, total_participations / 10.0)  # Normalize to 10 meetings
        
        # Bonus for action items
        action_item_bonus = min(0.3, total_action_items / 10.0)
        
        # Bonus for mentions
        mention_bonus = min(0.2, total_mentions / 20.0)
        
        total_score = participation_score + action_item_bonus + mention_bonus
        return min(1.0, total_score)
    
    async def _calculate_participation_score(self, employee: str, activities: List[Dict[str, Any]]) -> float:
        """Calculate participation score (0-1 scale)."""
        if not activities:
            return 0.0
        
        participation_levels = [activity.get('participation', {}).get('participation_level', 'low') for activity in activities]
        
        # Convert participation levels to scores
        level_scores = {
            'very_high': 1.0,
            'high': 0.8,
            'medium': 0.6,
            'low': 0.3
        }
        
        total_score = sum(level_scores.get(level, 0.3) for level in participation_levels)
        return min(1.0, total_score / len(activities))
    
    async def _identify_leadership_indicators(self, employee: str, activities: List[Dict[str, Any]]) -> List[str]:
        """Identify leadership indicators for employee."""
        indicators = []
        
        total_action_items = sum(len(activity.get('action_items', [])) for activity in activities)
        total_meetings = len(activities)
        
        # High action item ownership
        if total_action_items >= 5:
            indicators.append("High action item ownership")
        
        # Consistent participation
        if total_meetings >= 3:
            indicators.append("Consistent meeting participation")
        
        # Multi-meeting attendance
        meeting_types = set(activity.get('meeting_type', 'Unknown') for activity in activities)
        if len(meeting_types) >= 3:
            indicators.append("Cross-functional involvement")
        
        return indicators
    
    async def _calculate_activity_rating(self, engagement_score: float, participation_score: float, leadership_indicators: List[str]) -> float:
        """Calculate overall activity rating (1-10 scale)."""
        # Base rating from engagement and participation
        base_rating = (engagement_score * 5) + (participation_score * 3)  # Max 8 points
        
        # Leadership bonus
        leadership_bonus = min(2, len(leadership_indicators) * 0.5)
        
        # Calculate final rating
        final_rating = base_rating + leadership_bonus
        
        # Ensure rating is within 1-10 range
        return max(1.0, min(10.0, final_rating))
    
    async def _generate_team_analysis(self, employees_activity: Dict[str, EmployeeMeetingActivity], protocols: List[Dict[str, Any]]) -> DailyMeetingAnalysisResult:
        """Generate team-level analysis."""
        analysis_date = datetime.now()
        
        # Summary statistics
        total_employees = len(employees_activity)
        total_meetings_analyzed = len(protocols)
        
        # Calculate average engagement score
        if employees_activity:
            avg_engagement_score = sum(activity.engagement_score for activity in employees_activity.values()) / total_employees
        else:
            avg_engagement_score = 0.0
        
        # Identify most and least active employees
        sorted_employees = sorted(employees_activity.items(), key=lambda x: x[1].activity_rating, reverse=True)
        most_active_employees = [emp for emp, _ in sorted_employees[:3]]
        least_active_employees = [emp for emp, _ in sorted_employees[-3:]]
        
        # Meeting types distribution
        meeting_types_distribution = {}
        for protocol in protocols:
            meeting_type = self._determine_meeting_type(protocol['title'], protocol['content'])
            meeting_types_distribution[meeting_type] = meeting_types_distribution.get(meeting_type, 0) + 1
        
        # Action items statistics
        total_action_items = sum(activity.action_items_assigned for activity in employees_activity.values())
        completion_rate_action_items = 0.0  # Would need historical data
        
        # Generate team insights
        team_insights = await self._generate_team_insights(employees_activity)
        
        # Generate recommendations
        recommendations = await self._generate_team_recommendations(employees_activity, team_insights)
        
        return DailyMeetingAnalysisResult(
            analysis_date=analysis_date,
            employees_activity=employees_activity,
            total_employees=total_employees,
            total_meetings_analyzed=total_meetings_analyzed,
            avg_engagement_score=avg_engagement_score,
            most_active_employees=most_active_employees,
            least_active_employees=least_active_employees,
            meeting_types_distribution=meeting_types_distribution,
            total_action_items=total_action_items,
            completion_rate_action_items=completion_rate_action_items,
            team_insights=team_insights,
            recommendations=recommendations,
            quality_score=0.0,  # Will be calculated later
            analysis_duration=timedelta()  # Will be set later
        )
    
    async def _generate_team_insights(self, employees_activity: Dict[str, EmployeeMeetingActivity]) -> List[str]:
        """Generate team-level insights."""
        insights = []
        
        if not employees_activity:
            return insights
        
        # Overall engagement insight
        avg_engagement = sum(activity.engagement_score for activity in employees_activity.values()) / len(employees_activity)
        if avg_engagement >= 0.8:
            insights.append("Team showing high engagement in meetings")
        elif avg_engagement >= 0.6:
            insights.append("Team engagement is moderate with room for improvement")
        else:
            insights.append("Team needs encouragement for better meeting participation")
        
        # Action items insight
        total_action_items = sum(activity.action_items_assigned for activity in employees_activity.values())
        if total_action_items >= len(employees_activity) * 2:
            insights.append("Team demonstrates strong ownership with many action items")
        
        # Leadership insight
        leaders_count = sum(1 for activity in employees_activity.values() if len(activity.leadership_indicators) >= 2)
        if leaders_count >= len(employees_activity) // 2:
            insights.append("Strong leadership presence across team members")
        
        return insights
    
    async def _generate_team_recommendations(self, employees_activity: Dict[str, EmployeeMeetingActivity], insights: List[str]) -> List[str]:
        """Generate team-level recommendations."""
        recommendations = []
        
        if not employees_activity:
            return recommendations
        
        # Engagement-based recommendations
        low_engagement_employees = [emp for emp, activity in employees_activity.items() if activity.engagement_score < 0.5]
        if low_engagement_employees:
            recommendations.append(f"Encourage {len(low_engagement_employees)} employees to participate more actively")
        
        # Action items recommendations
        high_action_items = [emp for emp, activity in employees_activity.items() if activity.action_items_assigned >= 5]
        if high_action_items:
            recommendations.append(f"Monitor workload for {len(high_action_items)} employees with many action items")
        
        # Leadership development recommendations
        potential_leaders = [emp for emp, activity in employees_activity.items() if len(activity.leadership_indicators) >= 3]
        if potential_leaders:
            recommendations.append(f"Consider leadership development for {len(potential_leaders)} showing leadership potential")
        
        return recommendations
    
    async def _add_llm_insights(self, analysis_result: DailyMeetingAnalysisResult, employees_activity: Dict[str, EmployeeMeetingActivity]) -> None:
        """Add LLM-powered insights to analysis results."""
        try:
            # Prepare data for LLM analysis
            meeting_summary = self._prepare_meeting_data_for_llm(employees_activity)
            
            # Get LLM insights
            llm_analysis = await analyze_meeting_protocol(meeting_summary)
            
            # Extract and distribute insights to employees
            if 'employee_insights' in llm_analysis:
                for employee_name, insights in llm_analysis['employee_insights'].items():
                    if employee_name in employees_activity:
                        employees_activity[employee_name].llm_insights = insights.get('analysis', '')
                        # Update activity rating based on LLM assessment
                        if 'activity_rating' in insights:
                            employees_activity[employee_name].activity_rating = insights['activity_rating']
            
            # Add team-level insights
            if 'team_insights' in llm_analysis:
                analysis_result.team_insights.extend(llm_analysis['team_insights'])
            
            if 'recommendations' in llm_analysis:
                analysis_result.recommendations.extend(llm_analysis['recommendations'])
            
        except Exception as e:
            logger.warning(f"Failed to add LLM insights: {e}")
    
    def _prepare_meeting_data_for_llm(self, employees_activity: Dict[str, EmployeeMeetingActivity]) -> str:
        """Prepare meeting data summary for LLM analysis."""
        summary_parts = [
            "Employee Meeting Activity Analysis Summary",
            f"Analysis Date: {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "Employee Details:"
        ]
        
        for employee, activity in employees_activity.items():
            summary_parts.extend([
                f"\nEmployee: {employee}",
                f"  Activity Rating: {activity.activity_rating:.1f}/10",
                f"  Meetings Attended: {activity.meeting_participations}",
                f"  Engagement Score: {activity.engagement_score:.2f}",
                f"  Participation Score: {activity.participation_score:.2f}",
                f"  Action Items: {activity.action_items_assigned}",
                f"  Meeting Types: {', '.join(activity.meeting_types_attended) if activity.meeting_types_attended else 'None'}",
                f"  Leadership Indicators: {', '.join(activity.leadership_indicators) if activity.leadership_indicators else 'None'}"
            ])
        
        return "\n".join(summary_parts)
    
    async def _calculate_analysis_quality(self, analysis_result: DailyMeetingAnalysisResult) -> float:
        """Calculate analysis quality score."""
        try:
            quality_factors = []
            
            # Employee coverage score
            if analysis_result.total_employees > 0:
                coverage_score = min(1.0, analysis_result.total_employees / 5.0)  # Expect at least 5 employees
                quality_factors.append(coverage_score)
            
            # Data completeness score
            if analysis_result.employees_activity:
                employees_with_data = len([emp for emp, activity in analysis_result.employees_activity.items() 
                                         if activity.meeting_participations > 0])
                completeness_score = employees_with_data / len(analysis_result.employees_activity)
                quality_factors.append(completeness_score)
            
            # Insight quality score
            insight_score = min(1.0, len(analysis_result.team_insights) / 2.0)  # Expect at least 2 insights
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
    
    async def _save_daily_analysis(self, analysis_result: DailyMeetingAnalysisResult) -> None:
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
                'total_meetings_analyzed': analysis_result.total_meetings_analyzed,
                'avg_engagement_score': analysis_result.avg_engagement_score,
                'most_active_employees': analysis_result.most_active_employees,
                'least_active_employees': analysis_result.least_active_employees,
                'meeting_types_distribution': analysis_result.meeting_types_distribution,
                'total_action_items': analysis_result.total_action_items,
                'completion_rate_action_items': analysis_result.completion_rate_action_items,
                'team_insights': analysis_result.team_insights,
                'recommendations': analysis_result.recommendations,
                'quality_score': analysis_result.quality_score,
                'analysis_duration_seconds': analysis_result.analysis_duration.total_seconds(),
                'employees_activity': {},
                'metadata': analysis_result.metadata
            }
            
            # Serialize employee activity
            for employee, activity in analysis_result.employees_activity.items():
                analysis_data['employees_activity'][employee] = {
                    'employee_name': activity.employee_name,
                    'analysis_date': activity.analysis_date.isoformat(),
                    'meeting_participations': activity.meeting_participations,
                    'speaking_turns': activity.speaking_turns,
                    'topics_initiated': activity.topics_initiated,
                    'questions_asked': activity.questions_asked,
                    'decisions_influenced': activity.decisions_influenced,
                    'action_items_assigned': activity.action_items_assigned,
                    'action_items_completed': activity.action_items_completed,
                    'action_items_overdue': activity.action_items_overdue,
                    'engagement_score': activity.engagement_score,
                    'participation_score': activity.participation_score,
                    'leadership_indicators': activity.leadership_indicators,
                    'meeting_types_attended': list(activity.meeting_types_attended),
                    'average_meeting_duration_seconds': activity.average_meeting_duration.total_seconds() if activity.average_meeting_duration else None,
                    'llm_insights': activity.llm_insights,
                    'activity_rating': activity.activity_rating,
                    'last_updated': activity.last_updated.isoformat()
                }
            
            # Save to JSON file
            report_file = daily_dir / f"meeting-analysis_{date_str}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Meeting analysis saved to {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save daily analysis: {e}")
    
    async def _update_employee_memory_store(self, employees_activity: Dict[str, EmployeeMeetingActivity]) -> None:
        """Update memory store with employee state."""
        try:
            for employee, activity in employees_activity.items():
                # Save employee state to memory store
                employee_data = {
                    'employee_name': activity.employee_name,
                    'analysis_date': activity.analysis_date.isoformat(),
                    'meeting_metrics': {
                        'meeting_participations': activity.meeting_participations,
                        'speaking_turns': activity.speaking_turns,
                        'engagement_score': activity.engagement_score,
                        'participation_score': activity.participation_score,
                        'activity_rating': activity.activity_rating
                    },
                    'action_items': {
                        'assigned': activity.action_items_assigned,
                        'completed': activity.action_items_completed,
                        'overdue': activity.action_items_overdue
                    },
                    'leadership_tracking': {
                        'indicators': activity.leadership_indicators,
                        'meeting_types_attended': list(activity.meeting_types_attended)
                    },
                    'llm_insights': activity.llm_insights,
                    'last_updated': activity.last_updated.isoformat()
                }
                
                await self.memory_store.save_record(
                    data=employee_data,
                    record_type='employee_meeting_state',
                    record_id=employee,
                    source='meeting_analyzer_agent'
                )
            
            logger.info(f"Updated memory store with meeting activity for {len(employees_activity)} employees")
            
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
                'protocols_directory': str(self.protocols_directory),
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
