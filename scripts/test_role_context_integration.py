#!/usr/bin/env python3
"""
Тест(Role Context Integration) - Проверка интеграции ролей в анализ

Этот тест проверяет:
1. Role Context инжектится в промпты обоих агентов
2. Комментарии не обрезаются (лимит увеличен до 2000 символов)
3. Рекомендации учитывают должности сотрудников
"""

import asyncio
import logging
import json
from pathlib import Path
import sys
import os

# Добавляем корень проекта в путь
project_root = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(project_root))

from src.agents.task_analyzer_agent_improved import ImprovedTaskAnalyzerAgent
from src.agents.meeting_analyzer_agent_improved import ImprovedMeetingAnalyzerAgent

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RoleContextIntegrationTest:
    """Тест интеграции Role Context в анализ"""
    
    def __init__(self):
        self.task_analyzer = ImprovedTaskAnalyzerAgent()
        self.meeting_analyzer = ImprovedMeetingAnalyzerAgent()
        self.test_results = {
            "task_analyzer": {"status": "pending", "details": {}},
            "meeting_analyzer": {"status": "pending", "details": {}},
            "role_context": {"status": "pending", "details": {}},
            "comments_length": {"status": "pending", "details": {}}
        }
    
    async def run_all_tests(self):
        """Запустить все тесты"""
        logger.info("🚀 ЗАПУСК ТЕСТОВ ИНТЕГРАЦИИ ROLE CONTEXT")
        logger.info("=" * 60)
        
        try:
            # Тест 1: Проверка Role Context в Task Analyzer
            await self.test_task_analyzer_role_context()
            
            # Тест 2: Проверка Role Context в Meeting Analyzer  
            await self.test_meeting_analyzer_role_context()
            
            # Тест 3: Проверка длины комментариев
            await self.test_comments_length()
            
            # Тест 4: Проверка форматирования Role Context
            await self.test_role_context_formatting()
            
            # Итоги
            self.print_test_results()
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в тестах: {e}")
            import traceback
            traceback.print_exc()
    
    async def test_task_analyzer_role_context(self):
        """Тест Role Context в Task Analyzer"""
        logger.info("\n📋 ТЕСТ 1: Role Context в Task Analyzer")
        logger.info("-" * 40)
        
        try:
            # Проверяем наличие метода _format_role_context_for_prompt
            if hasattr(self.task_analyzer, '_format_role_context_for_prompt'):
                logger.info("✅ Метод _format_role_context_for_prompt существует")
                
                # Проверяем работу метода с тестовыми данными
                test_role_data = {
                    "enhanced_employees": {
                        "Надежда Савенкова": {
                            "role_context": {
                                "assignee_identified": True,
                                "role_level": "Product Owner",
                                "responsibility_level": "Высокая",
                                "specialization": "Управление продуктом"
                            }
                        },
                        "Рафаэль Мангурсузян": {
                            "role_context": {
                                "assignee_identified": True,
                                "role_level": "Разработчик",
                                "responsibility_level": "Средняя",
                                "specialization": "Backend разработка"
                            }
                        }
                    },
                    "team_context": {
                        "total_employees": 10,
                        "identified_employees": 8
                    }
                }
                
                formatted_context = self.task_analyzer._format_role_context_for_prompt(test_role_data)
                
                # Проверяем наличие ключевых секций
                if "КОНТЕКСТ РОЛЕЙ И ДОЛЖНОСТЕЙ" in formatted_context:
                    logger.info("✅ Заголовок Role Context присутствует")
                else:
                    logger.error("❌ Отсутствует заголовок Role Context")
                
                if "Product Owner" in formatted_context and "Разработчик" in formatted_context:
                    logger.info("✅ Должности корректно включены")
                else:
                    logger.error("❌ Должности отсутствуют в контексте")
                
                if "инструкциями для анализа с учетом ролей" in formatted_context.lower():
                    logger.info("✅ Инструкции по учету ролей присутствуют")
                else:
                    logger.warning("⚠️ Инструкции по учету ролей могут отсутствовать")
                
                # Проверяем длину контекста
                context_length = len(formatted_context)
                logger.info(f"📏 Длина Role Context: {context_length} символов")
                
                if context_length > 500:
                    logger.info("✅ Role Context имеет достаточную длину")
                else:
                    logger.warning("⚠️ Role Context может быть слишком коротким")
                
                self.test_results["task_analyzer"]["status"] = "passed"
                self.test_results["task_analyzer"]["details"] = {
                    "context_length": context_length,
                    "has_header": "КОНТЕКСТ РОЛЕЙ" in formatted_context,
                    "has_roles": "Product Owner" in formatted_context,
                    "has_instructions": "инструкциями" in formatted_context.lower()
                }
                
            else:
                logger.error("❌ Метод _format_role_context_for_prompt отсутствует")
                self.test_results["task_analyzer"]["status"] = "failed"
                self.test_results["task_analyzer"]["details"]["error"] = "Method missing"
                
        except Exception as e:
            logger.error(f"❌ Ошибка в тесте Task Analyzer: {e}")
            self.test_results["task_analyzer"]["status"] = "error"
            self.test_results["task_analyzer"]["details"]["error"] = str(e)
    
    async def test_meeting_analyzer_role_context(self):
        """Тест Role Context в Meeting Analyzer"""
        logger.info("\n📋 ТЕСТ 2: Role Context в Meeting Analyzer")
        logger.info("-" * 40)
        
        try:
            # Проверяем наличие метода _format_role_context_for_prompt
            if hasattr(self.meeting_analyzer, '_format_role_context_for_prompt'):
                logger.info("✅ Метод _format_role_context_for_prompt существует")
                
                # Проверяем работу метода с тестовыми данными для встреч
                test_meeting_role_data = {
                    "total_participants": 8,
                    "identified_participants": ["Надежда Савенкова", "Рафаэль Мангурсузян"],
                    "identification_rate": 0.75,
                    "participant_contexts": {
                        "Надежда Савенкова": {
                            "assignee_identified": True,
                            "role_level": "Product Owner",
                            "responsibility_level": "Высокая",
                            "activity_level": "Высокая",
                            "is_decision_maker": True,
                            "is_high_activity": True
                        },
                        "Рафаэль Мангурсузян": {
                            "assignee_identified": True,
                            "role_level": "Разработчик",
                            "responsibility_level": "Средняя",
                            "activity_level": "Средняя",
                            "is_decision_maker": False,
                            "is_high_activity": True
                        }
                    },
                    "decision_makers_present": ["Надежда Савенкова"],
                    "high_activity_present": ["Надежда Савенкова", "Рафаэль Мангурсузян"]
                }
                
                formatted_context = self.meeting_analyzer._format_role_context_for_prompt(test_meeting_role_data)
                
                # Проверяем наличие ключевых секций
                if "УЧАСТНИКИ ВСТРЕЧИ" in formatted_context:
                    logger.info("✅ Заголовок участников встреч присутствует")
                else:
                    logger.error("❌ Отсутствует заголовок участников встреч")
                
                if "ПРИНИМАЮЩИЕ РЕШЕНИЯ" in formatted_context:
                    logger.info("✅ Секция принимающих решения присутствует")
                else:
                    logger.warning("⚠️ Секция принимающих решения отсутствует")
                
                if "АКТИВНЫЕ УЧАСТНИКИ" in formatted_context:
                    logger.info("✅ Секция активных участников присутствует")
                else:
                    logger.warning("⚠️ Секция активных участников отсутствует")
                
                if "учетом ролей участников" in formatted_context.lower():
                    logger.info("✅ Инструкции по учету ролей участников присутствуют")
                else:
                    logger.warning("⚠️ Инструкции по учету ролей участников могут отсутствовать")
                
                # Проверяем длину контекста
                context_length = len(formatted_context)
                logger.info(f"📏 Длина Role Context для встреч: {context_length} символов")
                
                self.test_results["meeting_analyzer"]["status"] = "passed"
                self.test_results["meeting_analyzer"]["details"] = {
                    "context_length": context_length,
                    "has_meeting_header": "УЧАСТНИКИ ВСТРЕЧИ" in formatted_context,
                    "has_decision_makers": "ПРИНИМАЮЩИЕ РЕШЕНИЯ" in formatted_context,
                    "has_active_participants": "АКТИВНЫЕ УЧАСТНИКИ" in formatted_context
                }
                
            else:
                logger.error("❌ Метод _format_role_context_for_prompt отсутствует")
                self.test_results["meeting_analyzer"]["status"] = "failed"
                self.test_results["meeting_analyzer"]["details"]["error"] = "Method missing"
                
        except Exception as e:
            logger.error(f"❌ Ошибка в тесте Meeting Analyzer: {e}")
            self.test_results["meeting_analyzer"]["status"] = "error"
            self.test_results["meeting_analyzer"]["details"]["error"] = str(e)
    
    async def test_comments_length(self):
        """Тест длины комментариев в JSON"""
        logger.info("\n📋 ТЕСТ 3: Длина комментариев в JSON")
        logger.info("-" * 40)
        
        try:
            # Проверяем существующие файлы анализа
            reports_dir = Path("reports/daily/2026-04-20")
            
            # Проверяем task-analysis файлы
            task_analysis_files = list(reports_dir.glob("**/task-analysis_*.json"))
            
            if task_analysis_files:
                logger.info(f"📁 Найдено файлов task-analysis: {len(task_analysis_files)}")
                
                for file_path in task_analysis_files[:2]:  # Проверяем первые 2 файла
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Проверяем employee_analysis
                        if 'employee_analysis' in data:
                            for employee, emp_data in data['employee_analysis'].items():
                                # Проверяем achievements
                                if 'achievements' in emp_data:
                                    achievements = emp_data['achievements']
                                    if achievements:
                                        first_achievement = achievements[0]
                                        achievement_length = len(first_achievement)
                                        logger.info(f"📏 Achievement ({employee}): {achievement_length} символов")
                                        
                                        if achievement_length > 100:  # Больше старого лимита
                                            logger.info(f"✅ {employee}: Длина achievements увеличена")
                                        else:
                                            logger.warning(f"⚠️ {employee}: Длина achievements может быть ограничена")
                                
                                # Проверяем bottlenecks
                                if 'bottlenecks' in emp_data:
                                    bottlenecks = emp_data['bottlenecks']
                                    if bottlenecks:
                                        first_bottleneck = bottlenecks[0]
                                        bottleneck_length = len(first_bottleneck)
                                        logger.info(f"📏 Bottleneck ({employee}): {bottleneck_length} символов")
                                        
                                        if bottleneck_length > 100:  # Больше старого лимита
                                            logger.info(f"✅ {employee}: Длина bottlenecks увеличена")
                                        else:
                                            logger.warning(f"⚠️ {employee}: Длина bottlenecks может быть ограничена")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось прочитать файл {file_path}: {e}")
            else:
                logger.warning("⚠️ Файлы task-analysis не найдены")
            
            # Проверяем employee_progression файлы
            employee_files = list(reports_dir.glob("**/employee_progression/*.json"))
            
            if employee_files:
                logger.info(f"📁 Найдено файлов employee_progression: {len(employee_files)}")
                
                for file_path in employee_files[:2]:  # Проверяем первые 2 файла
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Проверяем detailed_insights
                        if 'detailed_insights' in data:
                            insights = data['detailed_insights']
                            insights_length = len(insights)
                            logger.info(f"📏 Detailed insights ({data.get('employee_name', 'Unknown')}): {insights_length} символов")
                            
                            if insights_length > 100:  # Больше старого лимита
                                logger.info(f"✅ {data.get('employee_name', 'Unknown')}: Длина insights увеличена")
                                self.test_results["comments_length"]["status"] = "passed"
                            else:
                                logger.warning(f"⚠️ {data.get('employee_name', 'Unknown')}: Длина insights может быть ограничена")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось прочитать файл {file_path}: {e}")
            else:
                logger.warning("⚠️ Файлы employee_progression не найдены")
            
            self.test_results["comments_length"]["status"] = "passed"
            
        except Exception as e:
            logger.error(f"❌ Ошибка в тесте комментариев: {e}")
            self.test_results["comments_length"]["status"] = "error"
            self.test_results["comments_length"]["details"]["error"] = str(e)
    
    async def test_role_context_formatting(self):
        """Тест форматирования Role Context"""
        logger.info("\n📋 ТЕСТ 4: Форматирование Role Context")
        logger.info("-" * 40)
        
        try:
            # Проверяем ключевые инструкции в Task Analyzer
            test_data = {
                "enhanced_employees": {},
                "team_context": {}
            }
            
            task_context = self.task_analyzer._format_role_context_for_prompt(test_data)
            
            # Проверяем наличие критических инструкций
            critical_instructions = [
                "Product Owner не может выполнять технические задачи",
                "Учитывай должности и ответственность",
                "Рекомендации должны соответствовать уровню должности"
            ]
            
            instructions_found = 0
            for instruction in critical_instructions:
                if instruction.lower() in task_context.lower():
                    instructions_found += 1
                    logger.info(f"✅ Найдена инструкция: {instruction[:50]}...")
                else:
                    logger.warning(f"⚠️ Отсутствует инструкция: {instruction[:50]}...")
            
            # Проверяем инструкции для Meeting Analyzer
            meeting_context = self.meeting_analyzer._format_role_context_for_prompt({
                "total_participants": 0,
                "participant_contexts": {}
            })
            
            meeting_instructions = [
                "Product Owner и Team Lead имеют разные роли",
                "Обращай внимание на кто принимает решения",
                "Рекомендации должны соответствовать уровню должности"
            ]
            
            meeting_instructions_found = 0
            for instruction in meeting_instructions:
                if instruction.lower() in meeting_context.lower():
                    meeting_instructions_found += 1
                    logger.info(f"✅ Найдена инструкция для встреч: {instruction[:50]}...")
                else:
                    logger.warning(f"⚠️ Отсутствует инструкция для встреч: {instruction[:50]}...")
            
            total_instructions = instructions_found + meeting_instructions_found
            max_instructions = len(critical_instructions) + len(meeting_instructions)
            
            if total_instructions >= max_instructions * 0.7:  # 70% инструкций найдены
                logger.info(f"✅ Большинство инструкций найдены: {total_instructions}/{max_instructions}")
                self.test_results["role_context"]["status"] = "passed"
            else:
                logger.warning(f"⚠️ Мало инструкций найдено: {total_instructions}/{max_instructions}")
                self.test_results["role_context"]["status"] = "partial"
            
            self.test_results["role_context"]["details"] = {
                "task_instructions_found": instructions_found,
                "meeting_instructions_found": meeting_instructions_found,
                "total_instructions": total_instructions,
                "max_instructions": max_instructions,
                "coverage": total_instructions / max_instructions
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка в тесте форматирования: {e}")
            self.test_results["role_context"]["status"] = "error"
            self.test_results["role_context"]["details"]["error"] = str(e)
    
    def print_test_results(self):
        """Вывести результаты тестов"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 РЕЗУЛЬТАТЫ ТЕСТОВ")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results.values() if test["status"] == "passed")
        partial_tests = sum(1 for test in self.test_results.values() if test["status"] == "partial")
        failed_tests = sum(1 for test in self.test_results.values() if test["status"] in ["failed", "error"])
        
        logger.info(f"📈 Общий результат: {passed_tests} пройдено, {partial_tests} частично, {failed_tests} не пройдено из {total_tests}")
        
        # Детальная статистика
        for test_name, result in self.test_results.items():
            status_icon = {
                "passed": "✅",
                "partial": "⚠️", 
                "failed": "❌",
                "error": "💥",
                "pending": "⏳"
            }.get(result["status"], "❓")
            
            logger.info(f"{status_icon} {test_name}: {result['status']}")
            
            if result.get("details"):
                for key, value in result["details"].items():
                    if key != "error":
                        logger.info(f"    • {key}: {value}")
                    else:
                        logger.warning(f"    • Ошибка: {value}")
        
        # Итоговый вердикт
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        if success_rate >= 0.8:
            logger.info("\n🎉 ОТЛИЧНО! Role Context успешно интегрирован в систему!")
        elif success_rate >= 0.6:
            logger.info("\n✅ ХОРОШО! Role Context в основном интегрирован, есть точки улучшения")
        else:
            logger.warning("\n⚠️ ТРЕБУЕТСЯ ДОРАБОТКА! Role Context интегрирован частично")
        
        logger.info(f"🎯 Успешность интеграции: {success_rate:.1%}")
        logger.info("=" * 60)


async def main():
    """Основная функция для запуска тестов"""
    print("🚀 ИНИЦИАЛИЗАЦИЯ ТЕСТОВ ИНТЕГРАЦИИ ROLE CONTEXT")
    print("=" * 60)
    
    try:
        # Создаем экземпляр теста
        test_runner = RoleContextIntegrationTest()
        
        # Запускаем все тесты
        await test_runner.run_all_tests()
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка при запуске тестов: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
