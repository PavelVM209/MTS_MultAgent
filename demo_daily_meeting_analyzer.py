#!/usr/bin/env python3
"""
Daily Meeting Analyzer Demonstration

Shows comprehensive meeting protocol analysis capabilities including:
- Multi-format protocol parsing (TXT, PDF, DOCX)
- Action item extraction and tracking
- Participant analysis and role identification
- Decision and topic extraction
- LLM-powered insights generation
- Quality metrics and validation
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.agents.daily_meeting_analyzer import DailyMeetingAnalyzer
from src.core.base_agent import AgentConfig
from src.core.llm_client import LLMClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_protocols():
    """Create realistic sample meeting protocols for demonstration."""
    return [
        {
            "id": "daily_standup_2024_03_25",
            "title": "Ежедневный стендап - Команда разработки",
            "date": "2024-03-25T09:00:00Z",
            "content": """
Ежедневное стендап совещание - 25.03.2024
==============================================

Участники: Иван Иванов (Team Lead), Мария Сидорова (Backend), Петр Петров (Frontend), Елена Козлова (QA)

1. ПРОГРЕСС ЗА ВЧЕРА
--------------------
Иван: Завершил настройку CI/CD pipeline, подключил автоматическое тестирование
Мария: Реализовала API endpoints для аутентификации, начала работу с профилями пользователей
Петр: Создал компоненты для навигации, настроил роутинг в приложении
Елена: Написала тесты для модуля аутентификации, обнаружила 2 бага

2. ПЛАН НА СЕГОДНЯ
------------------
Иван: Провести code review для команды, помочь с развертыванием на тестовом стенде
Мария: Закончить профиль пользователя, интегрировать с frontend
Петр: Подключить backend API, реализовать формы для входа/регистрации
Елена: Протестировать интеграцию frontend-backend, обновить тестовую документацию

3. БЛОКЕРЫ И ПРОБЛЕМЫ
---------------------
Мария: Нужна консультация по архитектуре баз данных от опытного разработчика
Петр: Возникли проблемы с CORS, нужна помощь с настройкой
Елена: Тестовый стенд недоступен с 10:00 до 12:00 на техобслуживании

4. ДЕЙСТВИЯ (ACTION ITEMS)
--------------------------
- Подготовить архитектурную схему БД: ответственный Мария, срок 26.03.2024, приоритет high
- Настроить CORS для frontend: ответственный Петр, срок 25.03.2024, приоритет critical
- Провести code review API endpoints: ответственный Иван, срок 25.03.2024
- Обновить тестовую документацию: ответственный Елена, срок 27.03.2024

5. РЕШЕНИЯ
-----------
- Принять новую архитектуру для базы данных (postgresql + redis)
- Провести дополнительное code review для всех новых компонентов
- Запланировать демо функциональности на пятницу в 15:00

6. СЛЕДУЮЩИЕ ШАГИ
----------------
- Подготовить релиз-ноты к релизу v1.2.0
- Провести обучение новой команды QA
- Настроить мониторинг production среды

""",
            "format": "text",
            "metadata": {
                "meeting_type": "daily_standup",
                "team": "development",
                "duration_minutes": 30
            }
        },
        {
            "id": "sprint_planning_2024_03_24",
            "title": "Планирование Спринт 8 - Проект MTS MultAgent",
            "date": "2024-03-24T14:00:00Z",
            "content": """
Совещание по планированию Спринт 8
==================================

Организатор: Алексей Смирнов (Scrum Master)
Место: Конференц-зал 301 (онлайн + оффлайн)
Дата: 24 марта 2024, 14:00-16:00

ПРИСУТСТВУЮЩИЕ:
- Алексей Смирнов (Scrum Master)
- Иван Иванов (Team Lead, Backend)
- Мария Сидорова (Senior Backend Developer)
- Петр Петров (Frontend Developer)
- Елена Козлова (QA Lead)
- Дмитрий Новиков (DevOps Engineer)
- Анна Белова (Product Owner)

ПОВЕСТКА ДНЯ:
1. Обзор результатов Спринта 7
2. Демонстрация готового функционала
3. Ретроспектива спринта
4. Планирование Спринта 8
5. Распределение задач команде

1. ОБЗОР РЕЗУЛЬТАТОВ СПРИНТА 7
---------------------------------
Завершенные задачи:
- ✅ Модуль аутентификации пользователей (Иван, Мария)
- ✅ Базовый интерфейс администратора (Петр)
- ✅ Настройка CI/CD pipeline (Дмитрий)
- ✅ Автоматизированные тесты для аутентификации (Елена)
- ✅ Документация API endpoints (Мария)

Метрики спринта:
- Запланировано: 35 story points
- Выполнено: 32 story points (91%)
- Баги найдены: 5 (все исправлены)
- Velocity команды: 91%

2. ДЕМОНСТРАЦИЯ ФУНКЦИОНАЛА
----------------------------
Продемонстрированы:
- Система регистрации и входа пользователей
- Панель администратора с базовыми функциями
- Автоматическое развертывание на тестовый стенд
- Отчеты о прохождении тестов

Обратная связь от Product Owner:
- Функционал соответствует требованиям
- Нужны улучшения в UX для мобильных устройств
- Добавить возможность экспорта отчетов в PDF

3. РЕТРОСПЕКТИВА СПРИНТА
-------------------------
Что прошло хорошо:
- Хорошая коммуникация в команде
- Быстрое решение технических проблем
- Качественное code review

Что можно улучшить:
- Улучшить estimation process (недооценили сложность frontend)
- Увеличить coverage автоматических тестов
- Лучше планировать зависимые задачи

Действия по ретроспективе:
3.1. Внедрить planning poker для estimation: ответственный Алексей, срок 28.03.2024
3.2. Целевой coverage тестов: 80%: ответственная Елена, срок 15.04.2024
3.3. Создать dependency matrix для задач: ответственный Иван, срок 28.03.2024

4. ПЛАНИРОВАНИЕ СПРИНТА 8
--------------------------
Цель Спринта 8: "Интеллектуальная аналитика и отчетность"

Backlog на спринт:
- Система аналитики для пользовательского поведения (8 story points)
- Автоматическая генерация отчетов (5 story points)
- Интеграция с Confluence (3 story points)
- Mobile-responsive design (8 story points)
- Advanced search functionality (5 story points)
- Performance optimization (3 story points)
- Security audit (5 story points)

Итого: 37 story points

Capacity команды:
- Иван: 8 story points
- Мария: 10 story points
- Петр: 9 story points
- Елена: 5 story points
- Дмитрий: 5 story points
Итого: 37 story points

5. РАСПРЕДЕЛЕНИЕ ЗАДАЧ
-----------------------
5.1. Система аналитики: Иван (lead) + Мария (backend), 8 sp
5.2. Автоматические отчеты: Мария, 5 sp
5.3. Интеграция с Confluence: Иван, 3 sp
5.4. Mobile-responsive: Петр, 8 sp
5.5. Advanced search: Петр, 5 sp
5.6. Performance optimization: Дмитрий, 3 sp
5.7. Security audit: Елена + Дмитрий, 5 sp

6. РЕШЕНИЯ И ДОГОВОРЕННОСТИ
-----------------------------
- Утвержден backlog Спринта 8 (37 story points)
- Проведение спринт-демо: 15.04.2024 в 15:00
- Ежедневные стендапы: 09:00-09:30 (онлайн)
- Code review обязательный для всех задач
- Weekly sync с архитектором каждый вторник в 16:00

7. СЛЕДУЮЩИЕ ШАГИ
------------------
7.1. Создать задачи в Jira для всех элементов backlog: @мария, до 25.03.2024
7.2. Настроить dashboard для мониторинга спринта: @алексей, до 26.03.2024
7.3. Провести kick-off meeting Спринта 8: @алексей, 26.03.2024 в 10:00
7.4. Подготовить тестовый план для новых компонентов: @елена, до 29.03.2024

""",
            "format": "text",
            "metadata": {
                "meeting_type": "sprint_planning",
                "duration_minutes": 120,
                "sprint_number": 8
            }
        },
        {
            "id": "tech_review_2024_03_22",
            "title": "Технический ревью - Архитектура микросервисов",
            "date": "2024-03-22T16:00:00Z",
            "content": """
Технический ревью: Новая архитектура микросервисов
==================================================

Дата: 22 марта 2024, 16:00-17:30
Формат: Online (Zoom)
Участники: Иван Иванов (Team Lead), Мария Сидорова (Senior), Дмитрий Новиков (DevOps), Внешний эксперт: Александр Воробьев

ЦЕЛЬ Встречи:
Ревью предложений по переходу на микросервисную архитектуру

ПРЕЗЕНТАЦИЯ ПРЕДЛОЖЕНИЯ (Иван):
--------------------------------
Текущая проблема:
- Монолит стал слишком большим (>100K строк кода)
- Сложности с развертыванием (2+ часа)
- Проблемы с масштабированием отдельных компонентов
- Зависимости между модулями замедляют разработку

Предлагаемая архитектура:
- API Gateway: маршрутизация и аутентификация
- Auth Service: управление пользователями и правами
- Analytics Service: сбор и обработка аналитики
- Report Service: генерация отчетов
- Notification Service: уведомления
- Shared Database: PostgreSQL + Redis
- Message Queue: RabbitMQ для асинхронной коммуникации

Преимущества:
- Независимое развертывание сервисов
- Масштабирование отдельных компонентов
- Технологическое разнообразие
- Упрощение тестирования

ОБСУЖДЕНИЕ:
-------------
Александр (эксперт): "Архитектура выглядит разумной, но есть риски с distributed transactions"

Мария: "Нужно убедиться, что у нас достаточно expertise для работы с микросервисами"

Дмитрий: "DevOps complexity значительно возрастет, нужна автоматизация"

Иван: "Предлагаю начать с pilot проекта - выделить Auth Service как первый микросервис"

КЛЮЧЕВЫЕ ТЕМЫ ДЛЯ ОБСУЖДЕНИЯ:
--------------------------------
1. Технологический стек для каждого сервиса
2. Стратегия миграции данных
3. Мониторинг и логирование
4. Резервное копирование и восстановление

РЕШЕНИЯ:
---------
1. Одобрен поэтапный переход на микросервисы
2. Начать с Auth Service как pilot проекта
3. Выбрать стек: Python + FastAPI для сервисов, Docker + Kubernetes для развертывания
4. Запланировать proof of concept на 2 недели

ДЕЙСТВИЯ:
----------
4.1. Создать техническое задание для Auth Service: @мария, срок 29.03.2024, приоритет critical
4.2. Исследовать возможности мониторинга микросервисов: @дмитрий, срок 01.04.2024
4.3. Подготовить training для команды по микросервисам: @иван, срок 05.04.2024
4.4. Оценить бюджет на переход: @александр, срок 02.04.2024

СЛЕДУЮЩАЯ ВСТРЕЧА:
-------------------
Follow-up meeting: 29 марта 2024, 16:00
Обзор: Прогресс по Auth Service PoC

""",
            "format": "text",
            "metadata": {
                "meeting_type": "technical_review",
                "duration_minutes": 90,
                "expert_review": True
            }
        }
    ]


def print_section(title: str):
    """Print formatted section title."""
    print(f"\n{'='*60}")
    print(f"🎯 {title}")
    print(f"{'='*60}")


def print_subsection(title: str):
    """Print formatted subsection title."""
    print(f"\n📋 {title}")
    print("-" * 40)


async def demo_basic_analysis():
    """Demonstrate basic meeting analysis without LLM."""
    print_section("Daily Meeting Analyzer - Basic Analysis Demo")
    
    # Create analyzer
    config = AgentConfig(
        name="DailyMeetingAnalyzer",
        description="Demo meeting analysis without LLM",
        version="1.0.0"
    )
    
    analyzer = DailyMeetingAnalyzer(config)
    
    # Check health status
    print("🏥 Checking analyzer health...")
    health = await analyzer.get_health_status()
    print(f"   Status: {health['status']}")
    print(f"   LLM Client: {health['llm_client']}")
    print(f"   Memory Store: {health['memory_store']}")
    
    # Create sample data
    sample_data = create_sample_protocols()
    print(f"\n📊 Analyzing {len(sample_data)} meeting protocols...")
    
    # Execute analysis without LLM
    start_time = datetime.now()
    
    result = await analyzer.execute({
        'meeting_protocols': sample_data,
        'include_llm_analysis': False,
        'filters': {
            'meeting_types': ['daily_standup', 'sprint_planning'],
            'min_participants': 2
        }
    })
    
    execution_time = (datetime.now() - start_time).total_seconds()
    
    if result.success:
        print_subsection("Analysis Results Summary")
        print(f"✅ Status: {result.success}")
        print(f"📝 Message: {result.message}")
        print(f"⏱️  Execution Time: {execution_time:.2f}s")
        print(f"📊 Protocols Analyzed: {result.metadata.get('protocols_analyzed', 0)}")
        print(f"🎯 Quality Score: {result.metadata.get('quality_score', 0):.2f}")
        
        # Display meeting info
        if 'meeting_info' in result.data:
            print_subsection("Meeting Information Summary")
            meeting_info = result.data['meeting_info']
            print(f"🏢 Title: {meeting_info['title']}")
            print(f"📅 Date: {meeting_info['date']}")
            print(f"👥 Total Attendees: {meeting_info['total_attendees']}")
            print(f"📋 Meeting Type: {meeting_info['meeting_type']}")
            if meeting_info['organizer']:
                print(f"👔 Organizer: {meeting_info['organizer']}")
            if meeting_info['location']:
                print(f"📍 Location: {meeting_info['location']}")
        
        # Display action items
        if 'action_items' in result.data:
            print_subsection("Action Items Extracted")
            for i, item in enumerate(result.data['action_items'][:5], 1):
                print(f"\n🎯 Action Item {i}:")
                print(f"   📝 Description: {item['description'][:80]}...")
                print(f"   👤 Responsible: {item['responsible']}")
                print(f"   📅 Deadline: {item['deadline'] or 'Not specified'}")
                print(f"   🔥 Priority: {item['priority']}")
                print(f"   📊 Status: {item['status']}")
        
        # Display decisions
        if 'decisions' in result.data:
            print_subsection("Meeting Decisions")
            for i, decision in enumerate(result.data['decisions'][:5], 1):
                print(f"💡 {i}. {decision[:100]}...")
        
        # Display key topics
        if 'key_topics' in result.data:
            print_subsection("Key Topics Discussed")
            for i, topic in enumerate(result.data['key_topics'][:5], 1):
                print(f"📌 {i}. {topic}")
        
        # Display next steps
        if 'next_steps' in result.data:
            print_subsection("Next Steps Identified")
            for i, step in enumerate(result.data['next_steps'][:5], 1):
                print(f"🚀 {i}. {step}")
    
    else:
        print(f"❌ Analysis failed: {result.message}")
        if result.error:
            print(f"Error: {result.error}")


async def demo_advanced_parsing():
    """Demonstrate advanced parsing capabilities."""
    print_section("Advanced Parsing Capabilities Demo")
    
    analyzer = DailyMeetingAnalyzer()
    
    # Test datetime parsing
    print_subsection("DateTime Parsing")
    test_dates = [
        "2024-03-25T09:00:00Z",
        "25.03.2024",
        "25/03/2024",
        "2024-03-25",
        "invalid date"
    ]
    
    for date_str in test_dates:
        parsed = analyzer._parse_datetime(date_str)
        if parsed:
            print(f"   '{date_str}' -> {parsed.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"   '{date_str}' -> Failed to parse")
    
    # Test duration extraction
    print_subsection("Duration Extraction")
    duration_tests = [
        "Продолжительность: 2 часа",
        "Meeting lasted 45 мин",
        "Длительность: 30 минут",
        "No duration mentioned"
    ]
    
    for text in duration_tests:
        duration = analyzer._extract_duration(text)
        if duration:
            print(f"   '{text}' -> {duration}")
        else:
            print(f"   '{text}' -> No duration found")
    
    # Test location extraction
    print_subsection("Location Extraction")
    location_tests = [
        "Место: Конференц-зал 301",
        "Location: Office Room 5",
        "Адрес: ул. Ленина, д. 1",
        "No location mentioned"
    ]
    
    for text in location_tests:
        location = analyzer._extract_location(text)
        if location:
            print(f"   '{text}' -> '{location}'")
        else:
            print(f"   '{text}' -> No location found")
    
    # Test priority extraction
    print_subsection("Priority Extraction")
    priority_tests = [
        "Task with priority high",
        "Критичная задача",
        "Medium priority task",
        "Низкий приоритет",
        "No priority specified"
    ]
    
    for text in priority_tests:
        priority = analyzer._extract_priority(text)
        print(f"   '{text}' -> {priority.value}")


async def demo_action_item_parsing():
    """Demonstrate action item parsing capabilities."""
    print_section("Action Item Parsing Demo")
    
    analyzer = DailyMeetingAnalyzer()
    
    # Test action item lines
    test_action_items = [
        "Подготовить документацию по API: ответственный Иван, срок 28.03.2024",
        "Провести code review: responsible Мария, deadline 27.03.2024, priority high",
        "Настроить тестовое окружение: ответственный Петр, приоритет critical",
        "@john.doe will handle the integration testing",
        "Действие: Обновить документацию - ответственный: Елена, срок: 30.03.2024"
    ]
    
    print_subsection("Action Item Line Parsing")
    
    for i, line in enumerate(test_action_items, 1):
        print(f"\n📝 Test {i}: {line}")
        
        # Extract responsible person
        responsible = analyzer._extract_responsible_person(line)
        print(f"   👤 Responsible: {responsible or 'Not found'}")
        
        # Extract deadline
        deadline = analyzer._extract_deadline(line, datetime.now())
        print(f"   📅 Deadline: {deadline.strftime('%Y-%m-%d') if deadline else 'Not found'}")
        
        # Extract priority
        priority = analyzer._extract_priority(line)
        print(f"   🔥 Priority: {priority.value}")
        
        # Clean description
        description = analyzer._clean_action_item_description(line)
        print(f"   📄 Clean Description: {description}")


async def main():
    """Main demonstration function."""
    print("🚀 Daily Meeting Analyzer Demonstration")
    print("=" * 60)
    
    try:
        # Run basic analysis demo
        await demo_basic_analysis()
        
        # Run advanced parsing demo
        await demo_advanced_parsing()
        
        # Run action item parsing demo
        await demo_action_item_parsing()
        
        print_section("Demo Complete")
        print("✅ All demonstrations completed successfully!")
        print("\nKey capabilities demonstrated:")
        print("1. ✅ Multi-meeting protocol analysis")
        print("2. ✅ Action item extraction and tracking")
        print("3. ✅ Participant identification and analysis")
        print("4. ✅ Decision and topic extraction")
        print("5. ✅ Advanced parsing capabilities")
        print("6. ✅ Quality metrics and validation")
        
        print("\nNext steps:")
        print("1. Configure OpenAI API key for LLM-enhanced analysis")
        print("2. Set up JIRA integration for action item tracking")
        print("3. Configure Confluence integration for reporting")
        print("4. Set up scheduler for daily automated analysis")
        
    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
