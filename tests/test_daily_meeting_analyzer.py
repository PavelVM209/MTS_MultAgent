"""
Tests for Daily Meeting Analyzer Agent
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.daily_meeting_analyzer import (
    DailyMeetingAnalyzer,
    ActionItem,
    ActionItemStatus,
    Priority,
    Participant,
    MeetingInfo,
    MeetingAnalysisResult
)
from src.core.base_agent import AgentResult


@pytest.fixture
def sample_meeting_protocols():
    """Sample meeting protocols for testing."""
    return [
        {
            "id": "meeting_1",
            "title": "Ежедневное стендап совещание",
            "date": "2024-03-25T09:00:00Z",
            "content": """
Ежедневное стендап совещание - 25.03.2024

Участники: Иван Иванов, Мария Сидорова, Петр Петров

1. Обсуждение прогресса по задачам
   Иван: Завершил модуль аутентификации
   Мария: Работает над схемой базы данных
   Петр: Настроил CI/CD pipeline

2. Действия:
   - Подготовить документацию по API: ответственный Иван, срок 28.03.2024
   - Провести code review схемы БД: ответственный Мария, срок 27.03.2024
   - Настроить тестовое окружение: ответственный Петр, приоритет high

3. Решения:
   - Принят план спринта на следующую неделю
   - Договорились о ежедневных демо в 15:00

4. Следующие шаги:
   - Подготовить релиз-ноты к пятнице
   - Провести обучение новой команде
""",
            "format": "text",
            "metadata": {}
        },
        {
            "id": "meeting_2",
            "title": "Планирование спринта",
            "date": "2024-03-24T14:00:00Z",
            "content": """
Совещание по планированию спринта

Организатор: Алексей Смирнов
Место: Конференц-зал 301

Участники: Алексей Смирнов, Елена Козлова, Дмитрий Новиков

Повестка дня:
1. Обзор результатов предыдущего спринта
2. Планирование задач на новый спринт
3. Распределение ответственности

Решения:
- Утверждены backlog задачи на спринт
- Назначены ответственные за каждая задача

Действия:
- @дмитрий подготовить estimate для задач (срок: 29.03.2024)
- @елена провести планирование ресурсов (priority: critical)
- @алексей согласовать сроки с заказчиком
""",
            "format": "text",
            "metadata": {}
        }
    ]


@pytest.fixture
def mock_analyzer():
    """Create a mock DailyMeetingAnalyzer for testing."""
    with patch('src.agents.daily_meeting_analyzer.LLMClient'), \
         patch('src.agents.daily_meeting_analyzer.JSONMemoryStore'), \
         patch('src.agents.daily_meeting_analyzer.QualityMetrics'), \
         patch('src.agents.daily_meeting_analyzer.get_config', return_value={}):
        
        analyzer = DailyMeetingAnalyzer()
        return analyzer


class TestDailyMeetingAnalyzer:
    """Test cases for DailyMeetingAnalyzer."""
    
    @pytest.mark.asyncio
    async def test_execute_successful_analysis(self, mock_analyzer, sample_meeting_protocols):
        """Test successful meeting analysis execution."""
        # Mock LLM client
        mock_analyzer.llm_client.is_available = AsyncMock(return_value=True)
        
        # Mock memory store
        mock_analyzer.memory_store.save_record = AsyncMock()
        
        # Mock schema validation
        mock_schema = AsyncMock()
        mock_schema.validate = AsyncMock(return_value={"validated": True})
        
        with patch('src.agents.daily_meeting_analyzer.MeetingAnalysisSchema', return_value=mock_schema):
            # Execute analysis
            result = await mock_analyzer.execute({
                'meeting_protocols': sample_meeting_protocols,
                'include_llm_analysis': False  # Disable LLM for simpler test
            })
            
            # Verify results
            assert result.success is True
            assert 'Successfully analyzed' in result.message
            assert 'execution_time' in result.metadata
            assert 'protocols_analyzed' in result.metadata
            assert result.metadata['protocols_analyzed'] == 2
    
    @pytest.mark.asyncio
    async def test_execute_no_protocols(self, mock_analyzer):
        """Test execution with no protocols."""
        result = await mock_analyzer.execute({'meeting_protocols': []})
        
        assert result.success is False
        assert 'No meeting protocols found' in result.message
        assert result.data == {}
    
    @pytest.mark.asyncio
    async def test_parse_meeting_protocols(self, mock_analyzer, sample_meeting_protocols):
        """Test meeting protocol parsing."""
        protocols = await mock_analyzer._parse_meeting_protocols(sample_meeting_protocols)
        
        assert len(protocols) == 2
        
        # Check first protocol
        protocol = protocols[0]
        assert protocol['id'] == 'meeting_1'
        assert protocol['title'] == 'Ежедневное стендап совещание'
        assert protocol['format'] == 'text'
        assert len(protocol['content']) > 0
    
    def test_parse_datetime(self, mock_analyzer):
        """Test datetime parsing."""
        # Test valid datetime formats
        dt1 = mock_analyzer._parse_datetime("2024-03-25T09:00:00Z")
        assert dt1 is not None
        assert dt1.year == 2024
        assert dt1.month == 3
        assert dt1.day == 25
        
        dt2 = mock_analyzer._parse_datetime("25.03.2024")
        assert dt2 is not None
        assert dt2.year == 2024
        assert dt2.month == 3
        assert dt2.day == 25
        
        dt3 = mock_analyzer._parse_datetime("25/03/2024")
        assert dt3 is not None
        assert dt3.year == 2024
        assert dt3.month == 3
        assert dt3.day == 25
        
        # Test invalid datetime
        dt4 = mock_analyzer._parse_datetime("invalid")
        assert dt4 is None
        
        # Test empty string
        dt5 = mock_analyzer._parse_datetime("")
        assert dt5 is None
    
    @pytest.mark.asyncio
    async def test_extract_meeting_info(self, mock_analyzer, sample_meeting_protocols):
        """Test meeting information extraction."""
        protocol = sample_meeting_protocols[0]
        meeting_info = await mock_analyzer._extract_meeting_info(protocol)
        
        assert meeting_info.meeting_id == 'meeting_1'
        assert meeting_info.title == 'Ежедневное стендап совещание'
        assert meeting_info.date.year == 2024
        assert meeting_info.meeting_type == 'Ежедневный стендап'
        assert meeting_info.total_attendees > 0
    
    def test_extract_duration(self, mock_analyzer):
        """Test duration extraction."""
        # Test hour patterns
        content1 = "Продолжительность: 2 часа"
        duration1 = mock_analyzer._extract_duration(content1)
        assert duration1 == timedelta(hours=2)
        
        content2 = "Meeting lasted 1 час"
        duration2 = mock_analyzer._extract_duration(content2)
        assert duration2 == timedelta(hours=1)
        
        # Test minute patterns
        content3 = "Длительность: 30 минут"
        duration3 = mock_analyzer._extract_duration(content3)
        assert duration3 == timedelta(minutes=30)
        
        content4 = "Duration: 45 мин"
        duration4 = mock_analyzer._extract_duration(content4)
        assert duration4 == timedelta(minutes=45)
        
        # Test no duration
        content5 = "No duration mentioned"
        duration5 = mock_analyzer._extract_duration(content5)
        assert duration5 is None
    
    def test_extract_location(self, mock_analyzer):
        """Test location extraction."""
        content1 = "Место: Конференц-зал 301"
        location1 = mock_analyzer._extract_location(content1)
        assert location1 == "Конференц-зал 301"
        
        content2 = "Location: Office Room 5"
        location2 = mock_analyzer._extract_location(content2)
        assert location2 == "Office Room 5"
        
        content3 = "Адрес: ул. Ленина, д. 1"
        location3 = mock_analyzer._extract_location(content3)
        assert location3 == "ул. Ленина, д. 1"
        
        content4 = "No location mentioned"
        location4 = mock_analyzer._extract_location(content4)
        assert location4 is None
    
    def test_extract_meeting_type(self, mock_analyzer):
        """Test meeting type extraction."""
        # Test various meeting types
        content1 = "Ежедневный стендап по проекту"
        type1 = mock_analyzer._extract_meeting_type(content1, "")
        assert type1 == 'Ежедневный стендап'
        
        content2 = "Sprint planning meeting"
        type2 = mock_analyzer._extract_meeting_type(content2, "")
        assert type2 == 'Спринт'
        
        content3 = "Проектное совещание команды"
        type3 = mock_analyzer._extract_meeting_type(content3, "")
        assert type3 == 'Проектное совещание'
        
        content4 = "Regular team sync"
        type4 = mock_analyzer._extract_meeting_type(content4, "")
        assert type4 == 'Общее совещание'
    
    def test_extract_organizer(self, mock_analyzer):
        """Test organizer extraction."""
        content1 = "Организатор: Алексей Смирнов"
        organizer1 = mock_analyzer._extract_organizer(content1)
        assert organizer1 == "Алексей Смирнов"
        
        content2 = "Ведущий: Иван Петров"
        organizer2 = mock_analyzer._extract_organizer(content2)
        assert organizer2 == "Иван Петров"
        
        content3 = "Chair: John Doe"
        organizer3 = mock_analyzer._extract_organizer(content3)
        assert organizer3 == "John Doe"
        
        content4 = "No organizer mentioned"
        organizer4 = mock_analyzer._extract_organizer(content4)
        assert organizer4 is None
    
    @pytest.mark.asyncio
    async def test_extract_participants(self, mock_analyzer):
        """Test participant extraction."""
        content = """
        Участники: Иван Иванов, Мария Сидорова, Петр Петров
        Также присутствовали: Елена Козлова, Дмитрий Новиков
        
        Контакты:
        - ivan.ivanov@example.com
        - maria.sidorova@company.com
        """
        
        participants = await mock_analyzer._extract_participants(content, None)
        
        assert len(participants) > 0
        
        # Check for expected participants
        participant_names = [p.name for p in participants]
        assert "Иван Иванов" in participant_names
        assert "Мария Сидорова" in participant_names
        assert "Петр Петров" in participant_names
        
        # Check email association
        ivan = next((p for p in participants if "Иван" in p.name), None)
        if ivan:
            assert ivan.email is not None
    
    def test_is_common_name(self, mock_analyzer):
        """Test common name detection."""
        # Should return True for common names
        assert mock_analyzer._is_common_name("Meeting") is True
        assert mock_analyzer._is_common_name("Protocol") is True
        assert mock_analyzer._is_common_name("Task") is True
        
        # Should return False for real person names
        assert mock_analyzer._is_common_name("Иван Иванов") is False
        assert mock_analyzer._is_common_name("John Doe") is False
        assert mock_analyzer._is_common_name("Мария Сидорова") is False
    
    @pytest.mark.asyncio
    async def test_extract_action_items(self, mock_analyzer):
        """Test action item extraction."""
        content = """
        Действия:
        - Подготовить документацию по API: ответственный Иван, срок 28.03.2024
        - Провести code review схемы БД: ответственный Мария, срок 27.03.2024
        - Настроить тестовое окружение: ответственный Петр, приоритет high
        """
        
        meeting_date = datetime(2024, 3, 25)
        action_items = await mock_analyzer._extract_action_items(content, meeting_date)
        
        assert len(action_items) >= 2
        
        # Check first action item
        item1 = action_items[0]
        assert "документацию" in item1.description.lower()
        assert item1.responsible == "Иван"
        assert item1.status == ActionItemStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_parse_action_item_line(self, mock_analyzer):
        """Test action item line parsing."""
        line = "Подготовить документацию по API: ответственный Иван, срок 28.03.2024"
        meeting_date = datetime(2024, 3, 25)
        
        action_item = await mock_analyzer._parse_action_item_line(line, 1, "", meeting_date)
        
        assert action_item is not None
        assert "документацию" in action_item.description.lower()
        assert action_item.responsible == "Иван"
        assert action_item.status == ActionItemStatus.PENDING
        assert action_item.id == "action_1"
    
    def test_extract_responsible_person(self, mock_analyzer):
        """Test responsible person extraction."""
        # Test various patterns
        line1 = "Task: responsible Иван Иванов"
        person1 = mock_analyzer._extract_responsible_person(line1)
        assert person1 == "Иван Иванов"
        
        line2 = "Действие: ответственный Мария"
        person2 = mock_analyzer._extract_responsible_person(line2)
        assert person2 == "Мария"
        
        line3 = "Assignee: Петр Петров"
        person3 = mock_analyzer._extract_responsible_person(line3)
        assert person3 == "Петр Петров"
        
        line4 = "@john.doe will handle this"
        person4 = mock_analyzer._extract_responsible_person(line4)
        assert person4 == "john.doe"
        
        line5 = "No responsible person mentioned"
        person5 = mock_analyzer._extract_responsible_person(line5)
        assert person5 is None
    
    def test_extract_deadline(self, mock_analyzer):
        """Test deadline extraction."""
        meeting_date = datetime(2024, 3, 25)
        
        # Test various patterns
        line1 = "Срок: 28.03.2024"
        deadline1 = mock_analyzer._extract_deadline(line1, meeting_date)
        assert deadline1 is not None
        assert deadline1.day == 28
        assert deadline1.month == 3
        assert deadline1.year == 2024
        
        line2 = "Deadline: 2024-03-30"
        deadline2 = mock_analyzer._extract_deadline(line2, meeting_date)
        assert deadline2 is not None
        assert deadline2.day == 30
        assert deadline2.month == 3
        assert deadline2.year == 2024
        
        line3 = "До 01.04.2024 нужно завершить"
        deadline3 = mock_analyzer._extract_deadline(line3, meeting_date)
        assert deadline3 is not None
        assert deadline3.day == 1
        assert deadline3.month == 4
        
        line4 = "No deadline mentioned"
        deadline4 = mock_analyzer._extract_deadline(line4, meeting_date)
        assert deadline4 is None
    
    def test_extract_priority(self, mock_analyzer):
        """Test priority extraction."""
        # Test various priorities
        line1 = "Task with priority high"
        priority1 = mock_analyzer._extract_priority(line1)
        assert priority1 == Priority.HIGH
        
        line2 = "Критичная задача"
        priority2 = mock_analyzer._extract_priority(line2)
        assert priority2 == Priority.CRITICAL
        
        line3 = "Medium priority task"
        priority3 = mock_analyzer._extract_priority(line3)
        assert priority3 == Priority.MEDIUM
        
        line4 = "Низкий приоритет"
        priority4 = mock_analyzer._extract_priority(line4)
        assert priority4 == Priority.LOW
        
        line5 = "No priority specified"
        priority5 = mock_analyzer._extract_priority(line5)
        assert priority5 == Priority.MEDIUM
    
    def test_clean_action_item_description(self, mock_analyzer):
        """Test action item description cleaning."""
        # Test various prefixes
        line1 = "Действие: Подготовить документацию"
        desc1 = mock_analyzer._clean_action_item_description(line1)
        assert desc1 == "Подготовить документацию"
        
        line2 = "Action: Complete the review"
        desc2 = mock_analyzer._clean_action_item_description(line2)
        assert desc2 == "Complete the review"
        
        line3 = "Задача: Настроить окружение"
        desc3 = mock_analyzer._clean_action_item_description(line3)
        assert desc3 == "Настроить окружение"
        
        line4 = "Already clean description"
        desc4 = mock_analyzer._clean_action_item_description(line4)
        assert desc4 == "Already clean description"
    
    @pytest.mark.asyncio
    async def test_extract_decisions(self, mock_analyzer):
        """Test decision extraction."""
        content = """
        Мы приняли решение о переходе на новую архитектуру.
        Решили изменить подход к тестированию.
        Договорились о ежедневных встречах.
        This is just a regular sentence.
        Another decision: we will use microservices.
        """
        
        decisions = await mock_analyzer._extract_decisions(content)
        
        assert len(decisions) >= 3
        
        # Check for expected decisions
        decision_text = ' '.join(decisions)
        assert "архитектуру" in decision_text.lower()
        assert "тестированию" in decision_text.lower()
    
    @pytest.mark.asyncio
    async def test_extract_key_topics(self, mock_analyzer):
        """Test key topics extraction."""
        content = """
        Тема: Обзор результатов предыдущего спринта
        Topic: Planning new features
        Вопрос: Распределение ресурсов
        Обсудили интеграцию с платежной системой
        """
        
        topics = await mock_analyzer._extract_key_topics(content)
        
        assert len(topics) >= 3
        
        # Check for expected topics
        topic_text = ' '.join(topics)
        assert "спринта" in topic_text
        assert "features" in topic_text
        assert "ресурсов" in topic_text
    
    @pytest.mark.asyncio
    async def test_extract_next_steps(self, mock_analyzer):
        """Test next steps extraction."""
        content = """
        Следующий шаг: подготовить презентацию для заказчика
        Next steps: complete the documentation
        Дальнейшие действия: провести тестирование
        Regular sentence about nothing important.
        """
        
        next_steps = await mock_analyzer._extract_next_steps(content)
        
        assert len(next_steps) >= 3
        
        # Check for expected next steps
        steps_text = ' '.join(next_steps)
        assert "презентацию" in steps_text.lower()
        assert "documentation" in steps_text.lower()
        assert "тестирование" in steps_text.lower()
    
    @pytest.mark.asyncio
    async def test_aggregate_analysis_results(self, mock_analyzer):
        """Test analysis results aggregation."""
        # Create sample results
        result1 = MeetingAnalysisResult(
            analysis_date=datetime.now(),
            meeting_info=MeetingInfo(
                meeting_id="meeting_1",
                title="Meeting 1",
                date=datetime.now(),
                duration=None,
                location=None,
                meeting_type="Type1",
                organizer=None,
                attendees=[Participant(name="Иван Иванов")],
                total_attendees=1
            ),
            action_items=[
                ActionItem(
                    id="action_1",
                    description="Task 1",
                    responsible="Иван",
                    deadline=None,
                    status=ActionItemStatus.PENDING,
                    priority=Priority.MEDIUM,
                    context="Context",
                    meeting_date=datetime.now()
                )
            ],
            decisions=["Decision 1"],
            key_topics=["Topic 1"],
            next_steps=["Step 1"],
            quality_score=0.8
        )
        
        result2 = MeetingAnalysisResult(
            analysis_date=datetime.now(),
            meeting_info=MeetingInfo(
                meeting_id="meeting_2",
                title="Meeting 2",
                date=datetime.now(),
                duration=None,
                location=None,
                meeting_type="Type2",
                organizer=None,
                attendees=[Participant(name="Мария Сидорова")],
                total_attendees=1
            ),
            action_items=[
                ActionItem(
                    id="action_2",
                    description="Task 2",
                    responsible="Мария",
                    deadline=None,
                    status=ActionItemStatus.PENDING,
                    priority=Priority.HIGH,
                    context="Context",
                    meeting_date=datetime.now()
                )
            ],
            decisions=["Decision 2"],
            key_topics=["Topic 2"],
            next_steps=["Step 2"],
            quality_score=0.9
        )
        
        aggregated = await mock_analyzer._aggregate_analysis_results([result1, result2])
        
        assert aggregated.meeting_info.title == "Aggregated Meeting Analysis"
        assert aggregated.meeting_info.meeting_type == "Multiple"
        assert len(aggregated.action_items) == 2
        assert len(aggregated.decisions) == 2
        assert len(aggregated.key_topics) == 2
        assert len(aggregated.next_steps) == 2
        assert len(aggregated.meeting_info.attendees) == 2
        assert aggregated.quality_score == 0.85  # (0.8 + 0.9) / 2
    
    @pytest.mark.asyncio
    async def test_calculate_analysis_quality(self, mock_analyzer):
        """Test analysis quality calculation."""
        meeting_info = MeetingInfo(
            meeting_id="test",
            title="Test Meeting",
            date=datetime.now(),
            duration=None,
            location=None,
            meeting_type="Test",
            organizer=None,
            attendees=[Participant(name="Test") for _ in range(5)],
            total_attendees=5
        )
        
        action_items = [
            ActionItem(
                id="1", description="Task 1", responsible="User1",
                deadline=None, status=ActionItemStatus.PENDING,
                priority=Priority.MEDIUM, context="Context",
                meeting_date=datetime.now()
            ) for _ in range(3)
        ]
        
        decisions = ["Decision 1", "Decision 2"]
        key_topics = ["Topic 1", "Topic 2", "Topic 3"]
        
        quality = await mock_analyzer._calculate_analysis_quality(
            meeting_info, action_items, decisions, key_topics
        )
        
        assert 0.0 <= quality <= 1.0
        assert quality > 0.5  # Should be decent quality with good data
    
    @pytest.mark.asyncio
    async def test_validate_and_format_results(self, mock_analyzer):
        """Test result validation and formatting."""
        result = MeetingAnalysisResult(
            analysis_date=datetime.now(),
            meeting_info=MeetingInfo(
                meeting_id="test",
                title="Test Meeting",
                date=datetime.now(),
                duration=timedelta(hours=1),
                location="Room 1",
                meeting_type="Test",
                organizer="Organizer",
                attendees=[Participant(name="Test User")],
                total_attendees=1
            ),
            action_items=[
                ActionItem(
                    id="1", description="Test Action", responsible="User",
                    deadline=datetime.now(), status=ActionItemStatus.PENDING,
                    priority=Priority.MEDIUM, context="Context",
                    meeting_date=datetime.now()
                )
            ],
            decisions=["Test decision"],
            key_topics=["Test topic"],
            next_steps=["Test step"],
            quality_score=0.8
        )
        
        # Mock schema validation
        mock_schema = AsyncMock()
        mock_schema.validate = AsyncMock(return_value={"validated": True})
        
        formatted = await mock_analyzer._validate_and_format_results(result, mock_schema)
        
        assert 'analysis_date' in formatted
        assert 'meeting_info' in formatted
        assert 'action_items' in formatted
        assert 'decisions' in formatted
        assert 'key_topics' in formatted
        assert 'next_steps' in formatted
        assert 'quality_score' in formatted
        assert formatted['quality_score'] == 0.8
    
    @pytest.mark.asyncio
    async def test_get_health_status(self, mock_analyzer):
        """Test health status check."""
        # Mock component availability
        mock_analyzer.llm_client.is_available = AsyncMock(return_value=True)
        mock_analyzer.memory_store.is_healthy = MagicMock(return_value=True)
        
        health = await mock_analyzer.get_health_status()
        
        assert health['agent_name'] == 'DailyMeetingAnalyzer'
        assert health['status'] == 'healthy'
        assert health['llm_client'] == 'available'
        assert health['memory_store'] == 'healthy'
        assert 'last_check' in health
    
    @pytest.mark.asyncio
    async def test_get_health_status_degraded(self, mock_analyzer):
        """Test health status when components are unavailable."""
        # Mock component unavailability
        mock_analyzer.llm_client.is_available = AsyncMock(return_value=False)
        mock_analyzer.memory_store.is_healthy = MagicMock(return_value=False)
        
        health = await mock_analyzer.get_health_status()
        
        assert health['status'] == 'degraded'
        assert health['llm_client'] == 'unavailable'
        assert health['memory_store'] == 'unhealthy'
    
    @pytest.mark.asyncio
    async def test_add_llm_insights(self, mock_analyzer):
        """Test adding LLM insights."""
        # Create sample analysis result
        result = MeetingAnalysisResult(
            analysis_date=datetime.now(),
            meeting_info=MeetingInfo(
                meeting_id="test", title="Test", date=datetime.now(),
                duration=None, location=None, meeting_type="Test",
                organizer=None, attendees=[], total_attendees=0
            ),
            action_items=[], decisions=[], key_topics=[], next_steps=[],
            quality_score=0.8
        )
        
        # Create sample individual results
        individual_results = [result]
        
        # Mock LLM analysis
        mock_llm_analysis = {
            'action_items': [
                {'description': 'LLM Action', 'responsible': 'LLM User'}
            ],
            'decisions': ['LLM Decision'],
            'key_topics': ['LLM Topic'],
            'next_steps': ['LLM Step']
        }
        
        with patch('src.agents.daily_meeting_analyzer.analyze_meeting_protocol',
                  return_value=mock_llm_analysis):
            await mock_analyzer._add_llm_insights(result, individual_results)
        
        # Check that LLM insights were added
        assert len(result.action_items) > 0
        assert len(result.decisions) > 0
        assert len(result.key_topics) > 0
        assert len(result.next_steps) > 0
        assert 'llm_analysis' in result.metadata
    
    @pytest.mark.asyncio
    async def test_prepare_protocol_text_for_llm(self, mock_analyzer):
        """Test protocol text preparation for LLM."""
        result = MeetingAnalysisResult(
            analysis_date=datetime.now(),
            meeting_info=MeetingInfo(
                meeting_id="test", title="Test Meeting", date=datetime.now(),
                duration=None, location=None, meeting_type="Test",
                organizer=None, attendees=[Participant(name="John Doe")],
                total_attendees=1
            ),
            action_items=[
                ActionItem(
                    id="1", description="Test Action", responsible="John",
                    deadline=None, status=ActionItemStatus.PENDING,
                    priority=Priority.MEDIUM, context="Context",
                    meeting_date=datetime.now()
                )
            ],
            decisions=["Test decision"],
            key_topics=["Test topic"],
            next_steps=["Test step"],
            quality_score=0.8
        )
        
        protocol_text = mock_analyzer._prepare_protocol_text_for_llm([result])
        
        assert "Meeting Protocols Analysis:" in protocol_text
        assert "Test Meeting" in protocol_text
        assert "John Doe" in protocol_text
        assert "Test Action" in protocol_text
        assert "Test decision" in protocol_text


if __name__ == "__main__":
    pytest.main([__file__])
