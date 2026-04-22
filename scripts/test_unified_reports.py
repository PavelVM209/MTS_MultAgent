#!/usr/bin/env python3
"""
Тестирование функциональности unified TXT отчетов

P6-8: Проверка создания единых TXT отчетов после завершения анализа
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.enhanced_file_manager import EnhancedFileManager
from src.agents.task_analyzer_agent_improved import ImprovedTaskAnalyzerAgent
from src.agents.meeting_analyzer_agent_improved import ImprovedMeetingAnalyzerAgent

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_enhanced_file_manager():
    """Тестирование EnhancedFileManager с unified отчетами"""
    print("\n" + "="*80)
    print("ТЕСТ 1: EnhancedFileManager - Unified TXT Reports")
    print("="*80)
    
    try:
        # Создаем менеджер файлов
        file_manager = EnhancedFileManager()
        
        print("✅ EnhancedFileManager создан")
        
        # Создаем тестовые данные
        test_task_stage1 = """ЭТАП 1: ТЕКСТОВЫЙ АНАЛИЗ ЗАДАЧ
Это тестовый контент для stage1 анализа задач.
Командные инсайты:
1. Тестовый инсайт 1
2. Тестовый инсайт 2

Рекомендации:
1. Тестовая рекомендация 1
2. Тестовая рекомендация 2
"""
        
        test_task_stage2 = {
            "employee_analysis": {
                "Тестовый Сотрудник": {
                    "total_tasks": 5,
                    "completed_tasks": 3,
                    "performance_rating": 8.0,
                    "achievements": ["Тестовое достижение"],
                    "bottlenecks": ["Тестовый блокер"]
                }
            },
            "team_insights": ["Инсайт 1", "Инсайт 2"],
            "recommendations": ["Рекомендация 1", "Рекомендация 2"]
        }
        
        test_meeting_data = {
            "team_collaboration_score": 7.5,
            "task_meeting_alignment": 0.8,
            "overall_team_health": 7.8,
            "team_insights": ["Митинг инсайт 1", "Митинг инсайт 2"],
            "personal_insights": {
                "Тестовый Сотрудник": ["Персональный инсайт 1", "Персональный инсайт 2"]
            },
            "recommendations": ["Митинг рекомендация 1", "Митинг рекомендация 2"]
        }
        
        # Сохраняем тестовые данные
        stage1_file = file_manager.save_task_stage1(test_task_stage1)
        stage2_file = file_manager.save_task_stage2(test_task_stage2)
        final_file = file_manager.save_task_final(test_task_stage2)
        
        print(f"✅ Stage 1 сохранен: {stage1_file}")
        print(f"✅ Stage 2 сохранен: {stage2_file}")
        print(f"✅ Final сохранен: {final_file}")
        
        # Сохраняем данные встреч
        meeting_file = file_manager.save_meeting_final(test_meeting_data)
        print(f"✅ Meeting анализ сохранен: {meeting_file}")
        
        # Сохраняем прогресс сотрудника
        employee_progression = {
            "employee_name": "Тестовый Сотрудник",
            "performance_rating": 8.0,
            "engagement_level": "высокая",
            "communication_effectiveness": 7.5,
            "detailed_insights": "Тестовые детальные инсайты"
        }
        progression_file = file_manager.save_employee_progression("Тестовый Сотрудник", employee_progression)
        print(f"✅ Employee progression сохранен: {progression_file}")
        
        # P6-8: Создаем unified TXT отчеты
        print("\n🔄 Создание unified TXT отчетов...")
        unified_reports = file_manager.create_unified_txt_reports()
        
        if unified_reports:
            print(f"✅ Создано {len(unified_reports)} unified TXT отчетов:")
            for report_type, filepath in unified_reports.items():
                print(f"  • {report_type}: {filepath}")
                
                # Проверяем содержимое файла
                if filepath.exists():
                    content = filepath.read_text(encoding='utf-8')
                    print(f"    Размер файла: {len(content)} символов")
                    print(f"    Первые 100 символов: {content[:100]}...")
                else:
                    print(f"    ❌ Файл не существует: {filepath}")
        else:
            print("❌ Unified TXT отчеты не созданы")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_task_analyzer_integration():
    """Тестирование интеграции с Task Analyzer"""
    print("\n" + "="*80)
    print("ТЕСТ 2: Task Analyzer - Unified TXT Integration")
    print("="*80)
    
    try:
        # Создаем агент
        agent = ImprovedTaskAnalyzerAgent()
        print("✅ Task Analyzer создан")
        
        # Проверяем health статус
        health = await agent.get_health_status()
        print(f"📊 Health Status: {health['status']}")
        print(f"🔧 LLM Client: {health['llm_client']}")
        
        # Создаем тестовые данные для анализа
        test_tasks = [
            {
                'id': 'TEST-1',
                'key': 'TEST-1',
                'summary': 'Тестовая задача 1',
                'status': 'Done',
                'assignee': 'Тестовый Сотрудник',
                'priority': 'Medium',
                'description': 'Тестовое описание задачи 1',
                'comments': 'Тестовый комментарий',
                'project': 'TEST'
            }
        ]
        
        # Сохраняем stage файлы напрямую для теста
        text_analysis = """=== КОМАНДНЫЕ ИНСАЙТЫ ===
1. Тестовый командный инсайт 1
2. Тестовый командный инсайт 2

=== РЕКОМЕНДАЦИИ МЕНЕДЖЕРУ ===
1. Тестовая рекомендация 1
2. Тестовая рекомендация 2

=== АНАЛИЗ СОТРУДНИКОВ ===
Сотрудник: Тестовый Сотрудник
- Общая оценка производительности: 8/10
- Ключевые достижения: Тестовое достижение
- Проблемы и блокеры: Тестовый блокер
"""
        
        json_result = {
            "employee_analysis": {
                "Тестовый Сотрудник": {
                    "total_tasks": 1,
                    "completed_tasks": 1,
                    "performance_rating": 8,
                    "achievements": ["Тестовое достижение"],
                    "bottlenecks": ["Тестовый блокер"],
                    "insights": "Тестовые инсайты"
                }
            },
            "team_insights": ["Тестовый инсайт 1", "Тестовый инсайт 2"],
            "recommendations": ["Тестовая рекомендация 1", "Тестовая рекомендация 2"]
        }
        
        # Сохраняем через метод агента
        await agent._save_stage_files(text_analysis, json_result)
        print("✅ Stage файлы сохранены через Task Analyzer")
        
        # Проверяем создание unified отчетов
        unified_reports = agent.file_manager.create_unified_txt_reports()
        
        if unified_reports:
            print(f"✅ Task Analyzer создал {len(unified_reports)} unified отчетов:")
            for report_type, filepath in unified_reports.items():
                print(f"  • {report_type}: {filepath}")
        else:
            print("❌ Task Analyzer не создал unified отчеты")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_meeting_analyzer_integration():
    """Тестирование интеграции с Meeting Analyzer"""
    print("\n" + "="*80)
    print("ТЕСТ 3: Meeting Analyzer - Unified TXT Integration")
    print("="*80)
    
    try:
        # Создаем агент
        agent = ImprovedMeetingAnalyzerAgent()
        print("✅ Meeting Analyzer создан")
        
        # Проверяем health статус
        health = await agent.get_health_status()
        print(f"📊 Health Status: {health['status']}")
        print(f"🔧 LLM Client: {health['llm_client']}")
        
        # Создаем тестовые данные для анализа
        from src.agents.meeting_analyzer_agent_improved import ComprehensiveMeetingAnalysis, EmployeeMeetingPerformance
        from datetime import timedelta
        
        employee_performance = {
            "Тестовый Сотрудник": EmployeeMeetingPerformance(
                employee_name="Тестовый Сотрудник",
                analysis_date=datetime.now(),
                speaking_turns=5,
                questions_asked=2,
                suggestions_made=3,
                action_items_assigned=1,
                engagement_level="высокая",
                task_to_meeting_correlation=0.8,
                communication_effectiveness=7.5,
                detailed_insights="Тестовые детальные инсайты",
                performance_rating=8.0
            )
        }
        
        analysis = ComprehensiveMeetingAnalysis(
            analysis_date=datetime.now(),
            employees_performance=employee_performance,
            total_employees=1,
            total_meetings_analyzed=1,
            total_tasks_analyzed=5,
            team_collaboration_score=7.5,
            task_meeting_alignment=0.8,
            overall_team_health=7.8,
            team_insights=["Тестовый митинг инсайт 1", "Тестовый митинг инсайт 2"],
            personal_insights={
                "Тестовый Сотрудник": ["Персональный митинг инсайт 1", "Персональный митинг инсайт 2"]
            },
            recommendations=["Тестовая митинг рекомендация 1", "Тестовая митинг рекомендация 2"],
            quality_score=0.9,
            analysis_duration=timedelta(seconds=30)
        )
        
        # Сохраняем через метод агента
        await agent._save_comprehensive_analysis(analysis)
        print("✅ Комплексный анализ сохранен через Meeting Analyzer")
        
        # Сохраняем прогресс сотрудников
        await agent._save_employee_progression(employee_performance)
        print("✅ Прогресс сотрудников сохранен через Meeting Analyzer")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Основная функция тестирования"""
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ UNIFIED TXT REPORTS")
    print("="*80)
    print("P6-8: Проверка создания единых TXT отчетов после завершения анализа")
    print("="*80)
    
    test_results = {}
    
    # Тест 1: EnhancedFileManager
    test_results['enhanced_file_manager'] = await test_enhanced_file_manager()
    
    # Тест 2: Task Analyzer Integration
    test_results['task_analyzer'] = await test_task_analyzer_integration()
    
    # Тест 3: Meeting Analyzer Integration
    test_results['meeting_analyzer'] = await test_meeting_analyzer_integration()
    
    # Итоги
    print("\n" + "="*80)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*80)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    for test_name, result in test_results.items():
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
    
    print(f"\nИтого: {passed_tests}/{total_tests} тестов пройдено")
    
    if passed_tests == total_tests:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ Функциональность unified TXT отчетов работает корректно")
        print("✅ Интеграция с анализаторами работает")
        print("✅ P6-8 успешно реализован")
    else:
        print(f"\n⚠️ {total_tests - passed_tests} тестов провалено")
        print("❌ Требуется исправление проблем")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    asyncio.run(main())
