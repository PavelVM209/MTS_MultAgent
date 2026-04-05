#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Quality Diagnostic
Анализ качества без сложных импортов
"""

import json
import logging
from datetime import datetime
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def analyze_quality_simple(report_data):
    """Простой анализ качества"""
    quality_factors = {}
    issues = []
    
    # 1. Employee Coverage Factor
    total_employees = report_data.get('total_employees', 0)
    coverage_score = min(1.0, total_employees / 5.0)  # Ожидаем минимум 5 сотрудников
    quality_factors['employee_coverage'] = {
        'value': coverage_score,
        'threshold': 0.8,
        'description': 'Покрытие сотрудников (ожидаем минимум 5)'
    }
    
    # 2. Data Completeness Factor
    employees_progress = report_data.get('employees_progress', {})
    if employees_progress:
        employees_with_data = len([emp for emp, data in employees_progress.items() 
                                 if isinstance(data, dict) and data.get('total_tasks', 0) > 0])
        completeness_score = employees_with_data / len(employees_progress)
    else:
        completeness_score = 0.0
    
    quality_factors['data_completeness'] = {
        'value': completeness_score,
        'threshold': 0.8,
        'description': 'Полнота данных сотрудников'
    }
    
    # 3. Insight Quality Factor
    team_insights = report_data.get('team_insights', [])
    insight_score = min(1.0, len(team_insights) / 3.0)  # Ожидаем минимум 3 инсайта
    quality_factors['insight_quality'] = {
        'value': insight_score,
        'threshold': 0.8,
        'description': f'Качество инсайтов ({len(team_insights)}/3)'
    }
    
    # 4. Recommendation Quality Factor
    recommendations = report_data.get('recommendations', [])
    recommendation_score = min(1.0, len(recommendations) / 2.0)  # Ожидаем минимум 2 рекомендации
    quality_factors['recommendation_quality'] = {
        'value': recommendation_score,
        'threshold': 0.8,
        'description': f'Качество рекомендаций ({len(recommendations)}/2)'
    }
    
    # 5. Task Count Factor
    total_tasks = report_data.get('total_tasks_analyzed', 0)
    task_score = min(1.0, total_tasks / 10.0)  # Ожидаем минимум 10 задач
    quality_factors['task_count'] = {
        'value': task_score,
        'threshold': 0.7,
        'description': f'Количество задач ({total_tasks}/10)'
    }
    
    # 6. Employee Performance Data Factor
    employee_data_quality = 0.0
    if employees_progress:
        total_employee_score = 0.0
        for emp_name, emp_data in employees_progress.items():
            if isinstance(emp_data, dict):
                # Проверяем ключевые поля
                required_fields = ['total_tasks', 'completed_tasks', 'completion_rate', 'performance_rating']
                field_score = sum(1 for field in required_fields if field in emp_data and emp_data[field] is not None)
                employee_score = field_score / len(required_fields)
                total_employee_score += employee_score
        
        employee_data_quality = total_employee_score / len(employees_progress) if employees_progress else 0.0
    
    quality_factors['employee_data_quality'] = {
        'value': employee_data_quality,
        'threshold': 0.9,
        'description': 'Качество данных сотрудников'
    }
    
    # Вычисляем общий балл
    scores = [factor['value'] for factor in quality_factors.values()]
    overall_quality = sum(scores) / len(scores) if scores else 0.0
    
    # Определяем проблемы
    for name, factor in quality_factors.items():
        if factor['value'] < factor['threshold']:
            issues.append(f"{factor['description']}: {factor['value']:.3f} < {factor['threshold']:.3f}")
    
    # Определяем уровень качества
    if overall_quality >= 0.9:
        level = "excellent"
    elif overall_quality >= 0.8:
        level = "good"
    elif overall_quality >= 0.6:
        level = "acceptable"
    elif overall_quality >= 0.4:
        level = "poor"
    else:
        level = "critical"
    
    return {
        'overall_score': overall_quality,
        'level': level,
        'factors': quality_factors,
        'issues': issues,
        'summary': {
            'total_employees': total_employees,
            'total_tasks': total_tasks,
            'insights_count': len(team_insights),
            'recommendations_count': len(recommendations),
            'employees_with_data': employees_with_data if employees_progress else 0
        }
    }

def main():
    """Основная функция"""
    try:
        logger.info("=== ПРОСТАЯ ДИАГНОСТИКА КАЧЕСТВА ===")
        
        # 1. Загрузка последнего отчета
        reports_dir = Path("./reports/daily")
        latest_report = None
        
        for date_dir in reports_dir.iterdir():
            if date_dir.is_dir():
                task_report = date_dir / "task-analysis_2026-04-03.json"
                if task_report.exists():
                    latest_report = task_report
                    break
        
        if not latest_report:
            logger.error("Отчет не найден")
            return
        
        logger.info(f"Загружаем отчет: {latest_report}")
        
        with open(latest_report, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        logger.info("=== АНАЛИЗ ОТЧЕТА ===")
        basic_info = {
            'analysis_date': report_data.get('analysis_date', 'unknown'),
            'total_employees': report_data.get('total_employees', 0),
            'total_tasks_analyzed': report_data.get('total_tasks_analyzed', 0),
            'quality_score_from_report': report_data.get('quality_score', 0),
            'avg_completion_rate': report_data.get('avg_completion_rate', 0),
            'top_performers_count': len(report_data.get('top_performers', [])),
            'employees_need_attention_count': len(report_data.get('employees_needing_attention', [])),
            'team_insights_count': len(report_data.get('team_insights', [])),
            'recommendations_count': len(report_data.get('recommendations', []))
        }
        
        for key, value in basic_info.items():
            if isinstance(value, float):
                logger.info(f"{key}: {value:.3f}")
            else:
                logger.info(f"{key}: {value}")
        
        # 2. Анализ качества
        logger.info("\n=== АНАЛИЗ КАЧЕСТВА ===")
        quality_result = analyze_quality_simple(report_data)
        
        logger.info(f"Общий балл качества: {quality_result['overall_score']:.3f}")
        logger.info(f"Уровень качества: {quality_result['level']}")
        
        logger.info("\n=== ДЕТАЛЬНЫЕ ФАКТОРЫ ===")
        for name, factor in quality_result['factors'].items():
            status = "✅" if factor['value'] >= factor['threshold'] else "❌"
            logger.info(f"{status} {name}: {factor['value']:.3f} (порог: {factor['threshold']:.3f}) - {factor['description']}")
        
        logger.info(f"\n=== ПРОБЛЕМЫ ===")
        if quality_result['issues']:
            for issue in quality_result['issues']:
                logger.info(f"❌ {issue}")
        else:
            logger.info("✅ Проблем не обнаружено")
        
        logger.info(f"\n=== СУММАРНАЯ СТАТИСТИКА ===")
        for key, value in quality_result['summary'].items():
            logger.info(f"{key}: {value}")
        
        # 3. Сравнение с отчетом
        report_quality = report_data.get('quality_score', 0)
        calculated_quality = quality_result['overall_score']
        
        logger.info(f"\n=== СРАВНЕНИЕ КАЧЕСТВА ===")
        logger.info(f"Качество в отчете: {report_quality:.3f}")
        logger.info(f"Рассчитанное качество: {calculated_quality:.3f}")
        logger.info(f"Разница: {abs(report_quality - calculated_quality):.3f}")
        
        # 4. Анализ LLM данных
        logger.info(f"\n=== АНАЛИЗ LLM ДАННЫХ ===")
        employees_progress = report_data.get('employees_progress', {})
        
        if employees_progress:
            logger.info(f"Всего сотрудников в прогрессе: {len(employees_progress)}")
            
            # Проверяем качество данных сотрудников
            good_employee_data = 0
            for emp_name, emp_data in employees_progress.items():
                if isinstance(emp_data, dict):
                    required_fields = ['total_tasks', 'completed_tasks', 'completion_rate', 'performance_rating']
                    has_all_fields = all(field in emp_data and emp_data[field] is not None for field in required_fields)
                    if has_all_fields:
                        good_employee_data += 1
                    else:
                        missing_fields = [field for field in required_fields if field not in emp_data or emp_data[field] is None]
                        logger.info(f"   ❌ {emp_name}: отсутствуют поля {missing_fields}")
            
            logger.info(f"Сотрудников с полными данными: {good_employee_data}/{len(employees_progress)}")
            
            # Проверяем LLM инсайты
            employees_with_insights = sum(1 for emp_data in employees_progress.values() 
                                        if isinstance(emp_data, dict) and emp_data.get('llm_insights'))
            logger.info(f"Сотрудников с LLM инсайтами: {employees_with_insights}/{len(employees_progress)}")
        else:
            logger.info("❌ Данные о прогрессе сотрудников отсутствуют")
        
        # 5. Рекомендации по улучшению
        logger.info(f"\n=== РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ ===")
        
        if quality_result['overall_score'] < 0.8:
            recommendations = []
            
            if len(report_data.get('team_insights', [])) < 3:
                recommendations.append("Добавьте минимум 3 качественных инсайта команды")
            
            if len(report_data.get('recommendations', [])) < 2:
                recommendations.append("Добавьте минимум 2 конкретные рекомендации")
            
            if report_data.get('total_tasks_analyzed', 0) < 10:
                recommendations.append("Увеличьте количество анализируемых задач")
            
            if employees_progress:
                good_data_pct = good_employee_data / len(employees_progress)
                if good_data_pct < 0.9:
                    recommendations.append("Улучшите качество данных сотрудников (заполните все поля)")
            
            if employees_with_insights < len(employees_progress) * 0.8:
                recommendations.append("Добавьте LLM инсайты для всех сотрудников")
            
            if report_quality != calculated_quality:
                recommendations.append("Исправьте расхождение в расчете качества")
            
            for i, rec in enumerate(recommendations, 1):
                logger.info(f"{i}. {rec}")
        else:
            logger.info("✅ Качество удовлетворительное")
        
        # Сохраняем результаты
        diagnostic_report = {
            'timestamp': datetime.now().isoformat(),
            'report_quality': report_quality,
            'calculated_quality': calculated_quality,
            'quality_level': quality_result['level'],
            'factors': quality_result['factors'],
            'issues': quality_result['issues'],
            'basic_info': basic_info,
            'recommendations': recommendations if quality_result['overall_score'] < 0.8 else []
        }
        
        with open('simple_quality_diagnostic.json', 'w', encoding='utf-8') as f:
            json.dump(diagnostic_report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n📄 Отчет диагностики сохранен в simple_quality_diagnostic.json")
        logger.info("=== ДИАГНОСТИКА ЗАВЕРШЕНА ===")
        
    except Exception as e:
        logger.error(f"Ошибка диагностики: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 ЗАПУСК ПРОСТОЙ ДИАГНОСТИКИ КАЧЕСТВА")
    print("=" * 60)
    main()
