#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug Quality Assessment
Проверка почему качество анализа 0.50
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Активация виртуального окружения
import subprocess
import sys

def activate_venv():
    """Активация виртуального окружения"""
    try:
        activate_cmd = "source venv_py311/bin/activate && python3 debug_quality_assessment.py"
        logger.info("Для активации venv выполните:")
        logger.info(activate_cmd)
        return False
    except Exception as e:
        logger.error(f"Ошибка активации venv: {e}")
        return False

# Загрузка переменных окружения
def load_env():
    """Загрузка .env файла"""
    try:
        from dotenv import load_dotenv
        env_path = Path('.env')
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(".env файл загружен")
        else:
            logger.warning(".env файл не найден")
    except ImportError:
        logger.info("dotenv не установлен, пропускаем загрузку .env")
    except Exception as e:
        logger.error(f"Ошибка загрузки .env: {e}")

load_env()

async def debug_quality_assessment():
    """Диагностика системы качества"""
    try:
        # Добавляем путь к проекту
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        # Импорты после загрузки окружения
        from src.core.quality_metrics import QualityMetrics, QualityLevel
        from src.agents.task_analyzer_agent import TaskAnalyzerAgent, DailyTaskAnalysisResult
        from src.agents.task_analyzer_agent import EmployeeTaskProgress
        from datetime import timedelta
        
        logger.info("=== ДИАГНОСТИКА СИСТЕМЫ КАЧЕСТВА ===")
        
        # 1. Загрузка последнего отчета
        reports_dir = Path("./reports/daily")
        latest_report = None
        latest_date = None
        
        for date_dir in reports_dir.iterdir():
            if date_dir.is_dir():
                task_report = date_dir / "task-analysis_2026-04-03.json"
                if task_report.exists():
                    if latest_date is None or date_dir.name > latest_date:
                        latest_date = date_dir.name
                        latest_report = task_report
        
        if not latest_report:
            logger.error("Отчет не найден")
            return
        
        logger.info(f"Загружаем отчет: {latest_report}")
        
        with open(latest_report, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        logger.info("=== АНАЛИЗ ОТЧЕТА ===")
        logger.info(f"Дата: {report_data.get('analysis_date', 'unknown')}")
        logger.info(f"Сотрудников: {report_data.get('total_employees', 0)}")
        logger.info(f"Задач проанализировано: {report_data.get('total_tasks_analyzed', 0)}")
        logger.info(f"Качество в отчете: {report_data.get('quality_score', 0):.2f}")
        
        # 2. Создаем QualityMetrics и диагностируем
        quality_metrics = QualityMetrics()
        
        # 3. Комплексная оценка качества
        logger.info("\n=== КОМПЛЕКСНАЯ ОЦЕНКА КАЧЕСТВА ===")
        
        # Подготовка контекста для оценки
        context = {
            'required_fields': [
                'analysis_date', 'total_employees', 'employees_progress',
                'team_insights', 'recommendations'
            ],
            'expected_patterns': {
                'has_employee_data': bool(report_data.get('employees_progress')),
                'has_insights': len(report_data.get('team_insights', [])) > 0,
                'has_recommendations': len(report_data.get('recommendations', [])) > 0
            },
            'expected_items': [],
            'max_age_hours': 24
        }
        
        # Выполняем оценку качества
        assessment = quality_metrics.comprehensive_assessment(report_data, context)
        
        logger.info(f"Общий балл качества: {assessment.overall_score:.3f}")
        logger.info(f"Уровень качества: {assessment.level.value}")
        
        logger.info("\n=== ДЕТАЛЬНЫЕ МЕТРИКИ ===")
        for metric in assessment.metrics:
            status = "✅" if metric.is_acceptable() else "❌"
            logger.info(f"{status} {metric.name}: {metric.value:.3f} (порог: {metric.threshold:.3f}) - {metric.description}")
            
            # Дополнительная диагностика для каждой метрики
            if metric.name == "completeness" and not metric.is_acceptable():
                logger.info(f"   Проблема с полнотой данных. Проверьте поля: {context['required_fields']}")
            
            elif metric.name == "accuracy" and not metric.is_acceptable():
                logger.info(f"   Проблема с точностью анализа. Возможные причины:")
                logger.info(f"   - Мало инсайтов: {len(report_data.get('team_insights', []))}")
                logger.info(f"   - Мало рекомендаций: {len(report_data.get('recommendations', []))}")
                logger.info(f"   - Отсутствует employee_analysis в LLM ответе")
            
            elif metric.name == "consistency" and not metric.is_acceptable():
                logger.info(f"   Проблема согласованности данных. Проверьте:")
                logger.info(f"   - Логические связи в данных")
                logger.info(f"   - Числовые значения на разумность")
                logger.info(f"   - Соответствие дат")
            
            elif metric.name == "timeliness" and not metric.is_acceptable():
                logger.info(f"   Проблема со своевременностью. Данные устарели")
            
            elif metric.name == "coverage" and not metric.is_acceptable():
                logger.info(f"   Проблема с покрытием данных. Не все expected_items найдены")
        
        logger.info(f"\n=== ПРОБЛЕМЫ ===")
        if assessment.issues:
            for issue in assessment.issues:
                logger.info(f"❌ {issue}")
        else:
            logger.info("✅ Проблем не обнаружено")
        
        logger.info(f"\n=== РЕКОМЕНДАЦИИ ===")
        if assessment.recommendations:
            for rec in assessment.recommendations:
                logger.info(f"💡 {rec}")
        else:
            logger.info("✅ Рекомендаций нет")
        
        # 4. Критические проблемы
        critical_issues = assessment.get_critical_issues()
        if critical_issues:
            logger.info(f"\n=== КРИТИЧЕСКИЕ ПРОБЛЕМЫ ===")
            for issue in critical_issues:
                logger.info(f"🚨 {issue}")
        
        # 5. Симуляция улучшения качества
        logger.info(f"\n=== СИМУЛЯЦИЯ УЛУЧШЕНИЯ ===")
        
        # Копируем данные и улучшаем их
        improved_data = report_data.copy()
        
        # Добавляем недостающие инсайты
        current_insights = improved_data.get('team_insights', [])
        if len(current_insights) < 3:
            additional_insights = [
                "Команда демонстрирует стабильную производительность",
                "Выявлены возможности для оптимизации процессов",
                "Рекомендуется усилить мониторингdeadline"
            ]
            needed = 3 - len(current_insights)
            improved_data['team_insights'] = current_insights + additional_insights[:needed]
            logger.info(f"➕ Добавлены инсайты: {needed} шт.")
        
        # Добавляем рекомендации
        current_recs = improved_data.get('recommendations', [])
        if len(current_recs) < 3:
            additional_recs = [
                "Провести тренинг по управлению временем",
                "Оптимизировать распределение нагрузки",
                "Внедрить систему раннего предупреждения о просрочках"
            ]
            needed = 3 - len(current_recs)
            improved_data['recommendations'] = current_recs + additional_recs[:needed]
            logger.info(f"➕ Добавлены рекомендации: {needed} шт.")
        
        # Повторная оценка качества
        improved_assessment = quality_metrics.comprehensive_assessment(improved_data, context)
        
        logger.info(f"\n=== РЕЗУЛЬТАТЫ УЛУЧШЕНИЯ ===")
        logger.info(f"Было: {assessment.overall_score:.3f} ({assessment.level.value})")
        logger.info(f"Стало: {improved_assessment.overall_score:.3f} ({improved_assessment.level.value})")
        logger.info(f"Улучшение: +{improved_assessment.overall_score - assessment.overall_score:.3f}")
        
        # 6. Финальные рекомендации
        logger.info(f"\n=== ФИНАЛЬНЫЕ РЕКОМЕНДАЦИИ ===")
        
        if assessment.overall_score < 0.8:
            logger.info("🔧 Для достижения качества > 0.8:")
            
            if len(assessment.issues) > 0:
                logger.info("   1. Решите выявленные проблемы:")
                for issue in assessment.issues:
                    logger.info(f"      - {issue}")
            
            if len(current_insights) < 3:
                logger.info("   2. Сгенерируйте минимум 3 качественных инсайта")
            
            if len(current_recs) < 2:
                logger.info("   3. Добавьте минимум 2 конкретные рекомендации")
            
            logger.info("   4. Убедитесь что LLM возвращает валидный JSON с employee_analysis")
            logger.info("   5. Проверьте согласованность данных в отчете")
        
        logger.info("\n=== ДИАГНОСТИКА ЗАВЕРШЕНА ===")
        
        # Сохраняем диагностику в файл
        diagnostic_report = {
            'timestamp': datetime.now().isoformat(),
            'original_quality': assessment.overall_score,
            'improved_quality': improved_assessment.overall_score,
            'quality_level': assessment.level.value,
            'issues': assessment.issues,
            'recommendations': assessment.recommendations,
            'metrics': [
                {
                    'name': m.name,
                    'value': m.value,
                    'threshold': m.threshold,
                    'acceptable': m.is_acceptable(),
                    'description': m.description
                }
                for m in assessment.metrics
            ],
            'critical_issues': critical_issues
        }
        
        with open('quality_diagnostic_report.json', 'w', encoding='utf-8') as f:
            json.dump(diagnostic_report, f, indent=2, ensure_ascii=False)
        
        logger.info("📄 Отчет диагностики сохранен в quality_diagnostic_report.json")
        
    except Exception as e:
        logger.error(f"Ошибка диагностики: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 ЗАПУСК ДИАГНОСТИКИ КАЧЕСТВА АНАЛИЗА")
    print("=" * 60)
    
    # Проверяем виртуальное окружение
    venv_active = "venv_py311" in sys.executable
    if not venv_active:
        print("⚠️  Виртуальное окружение не активировано")
        print("Выполните: source venv_py311/bin/activate && python3 debug_quality_assessment.py")
        exit(1)
    
    # Запускаем диагностику
    asyncio.run(debug_quality_assessment())
