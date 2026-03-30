# -*- coding: utf-8 -*-
"""
Quality Metrics - Модуль для оценки качества анализа в Employee Monitoring System

Предоставляет инструменты для оценки качества результатов работы агентов,
валидации данных и метрик производительности.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class QualityLevel(Enum):
    """Уровни качества."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class QualityMetric:
    """Метрика качества."""
    name: str
    value: float
    threshold: float
    weight: float = 1.0
    description: str = ""
    
    def is_acceptable(self) -> bool:
        """Проверяет соответствует ли метрика порогу."""
        return self.value >= self.threshold
    
    def get_level(self) -> QualityLevel:
        """Определяет уровень качества."""
        if self.value >= self.threshold * 1.2:
            return QualityLevel.EXCELLENT
        elif self.value >= self.threshold:
            return QualityLevel.GOOD
        elif self.value >= self.threshold * 0.8:
            return QualityLevel.ACCEPTABLE
        elif self.value >= self.threshold * 0.5:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL


@dataclass
class QualityAssessment:
    """Результат оценки качества."""
    overall_score: float
    level: QualityLevel
    metrics: List[QualityMetric] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def is_acceptable(self) -> bool:
        """Проверяет общее качество."""
        return self.level in [QualityLevel.GOOD, QualityLevel.EXCELLENT]
    
    def get_critical_issues(self) -> List[str]:
        """Возвращает критические проблемы."""
        return [
            f"{metric.name}: {metric.value:.2f} < {metric.threshold:.2f}"
            for metric in self.metrics
            if metric.get_level() == QualityLevel.CRITICAL
        ]


class QualityMetrics:
    """
    Класс для оценки качества данных и результатов анализа.
    
    Оценивает:
    - Полноту данных
    - Точность анализа
    - Согласованность результатов
    - Временные метрики
    """
    
    def __init__(self):
        """Инициализация модуля качества."""
        self.default_thresholds = {
            'completeness': 0.8,
            'accuracy': 0.85,
            'consistency': 0.9,
            'timeliness': 0.7,
            'coverage': 0.75
        }
        
        logger.info("QualityMetrics initialized")
    
    def assess_data_completeness(self, data: Dict[str, Any], required_fields: List[str]) -> QualityMetric:
        """
        Оценивает полноту данных.
        
        Args:
            data: Данные для оценки
            required_fields: Список обязательных полей
            
        Returns:
            QualityMetric: Метрика полноты
        """
        if not required_fields:
            return QualityMetric(
                name="completeness",
                value=1.0,
                threshold=self.default_thresholds['completeness'],
                description="Data completeness"
            )
        
        present_fields = sum(1 for field in required_fields if self._field_exists(data, field))
        completeness = present_fields / len(required_fields)
        
        return QualityMetric(
            name="completeness",
            value=completeness,
            threshold=self.default_thresholds['completeness'],
            description="Data completeness"
        )
    
    def assess_analysis_accuracy(self, analysis_data: Dict[str, Any], 
                                expected_patterns: Dict[str, Any]) -> QualityMetric:
        """
        Оценивает точность анализа.
        
        Args:
            analysis_data: Результаты анализа
            expected_patterns: Ожидаемые паттерны
            
        Returns:
            QualityMetric: Метрика точности
        """
        accuracy_factors = []
        
        # Проверяем наличие ключевых секций
        key_sections = ['employees', 'summary', 'insights', 'recommendations']
        for section in key_sections:
            if section in analysis_data and analysis_data[section]:
                accuracy_factors.append(1.0)
            else:
                accuracy_factors.append(0.0)
        
        # Проверяем качество инсайтов
        if 'insights' in analysis_data:
            insights = analysis_data['insights']
            if isinstance(insights, list) and len(insights) >= 3:
                accuracy_factors.append(1.0)
            else:
                accuracy_factors.append(0.5)
        
        # Проверяем рекомендации
        if 'recommendations' in analysis_data:
            recommendations = analysis_data['recommendations']
            if isinstance(recommendations, list) and len(recommendations) >= 2:
                accuracy_factors.append(1.0)
            else:
                accuracy_factors.append(0.5)
        
        accuracy = sum(accuracy_factors) / len(accuracy_factors) if accuracy_factors else 0.0
        
        return QualityMetric(
            name="accuracy",
            value=accuracy,
            threshold=self.default_thresholds['accuracy'],
            description="Analysis accuracy"
        )
    
    def assess_data_consistency(self, data: Dict[str, Any]) -> QualityMetric:
        """
        Оценивает согласованность данных.
        
        Args:
            data: Данные для оценки
            
        Returns:
            QualityMetric: Метрика согласованности
        """
        consistency_factors = []
        
        # Проверяем числовые значения на разумность
        numeric_checks = self._check_numeric_consistency(data)
        consistency_factors.extend(numeric_checks)
        
        # Проверяем даты
        date_checks = self._check_date_consistency(data)
        consistency_factors.extend(date_checks)
        
        # Проверяем связи между данными
        relationship_checks = self._check_relationship_consistency(data)
        consistency_factors.extend(relationship_checks)
        
        consistency = sum(consistency_factors) / len(consistency_factors) if consistency_factors else 0.5
        
        return QualityMetric(
            name="consistency",
            value=consistency,
            threshold=self.default_thresholds['consistency'],
            description="Data consistency"
        )
    
    def assess_timeliness(self, timestamp: datetime, max_age_hours: int = 24) -> QualityMetric:
        """
        Оценивает своевременность данных.
        
        Args:
            timestamp: Временная метка данных
            max_age_hours: Максимальный возраст данных в часах
            
        Returns:
            QualityMetric: Метрика своевременности
        """
        now = datetime.now()
        age_hours = (now - timestamp).total_seconds() / 3600
        
        if age_hours <= max_age_hours:
            timeliness = 1.0
        elif age_hours <= max_age_hours * 2:
            timeliness = 0.7
        elif age_hours <= max_age_hours * 4:
            timeliness = 0.4
        else:
            timeliness = 0.1
        
        return QualityMetric(
            name="timeliness",
            value=timeliness,
            threshold=self.default_thresholds['timeliness'],
            description="Data timeliness"
        )
    
    def assess_coverage(self, data: Dict[str, Any], expected_items: List[str]) -> QualityMetric:
        """
        Оценивает покрытие данных.
        
        Args:
            data: Данные для оценки
            expected_items: Ожидаемые элементы
            
        Returns:
            QualityMetric: Метрика покрытия
        """
        if not expected_items:
            return QualityMetric(
                name="coverage",
                value=1.0,
                threshold=self.default_thresholds['coverage'],
                description="Data coverage"
            )
        
        found_items = 0
        for item in expected_items:
            if self._item_exists_in_data(data, item):
                found_items += 1
        
        coverage = found_items / len(expected_items)
        
        return QualityMetric(
            name="coverage",
            value=coverage,
            threshold=self.default_thresholds['coverage'],
            description="Data coverage"
        )
    
    def comprehensive_assessment(self, data: Dict[str, Any], 
                               context: Dict[str, Any]) -> QualityAssessment:
        """
        Комплексная оценка качества данных.
        
        Args:
            data: Данные для оценки
            context: Контекст оценки
            
        Returns:
            QualityAssessment: Комплексная оценка
        """
        metrics = []
        issues = []
        recommendations = []
        
        # Оценка полноты
        required_fields = context.get('required_fields', [])
        completeness_metric = self.assess_data_completeness(data, required_fields)
        metrics.append(completeness_metric)
        
        if not completeness_metric.is_acceptable():
            issues.append("Неполные данные - отсутствуют обязательные поля")
            recommendations.append("Добавить отсутствующие данные")
        
        # Оценка точности
        expected_patterns = context.get('expected_patterns', {})
        accuracy_metric = self.assess_analysis_accuracy(data, expected_patterns)
        metrics.append(accuracy_metric)
        
        if not accuracy_metric.is_acceptable():
            issues.append("Низкая точность анализа")
            recommendations.append("Улучшить алгоритмы анализа")
        
        # Оценка согласованности
        consistency_metric = self.assess_data_consistency(data)
        metrics.append(consistency_metric)
        
        if not consistency_metric.is_acceptable():
            issues.append("Проблемы согласованности данных")
            recommendations.append("Проверить логические связи в данных")
        
        # Оценка своевременности
        timestamp = data.get('timestamp', datetime.now())
        max_age = context.get('max_age_hours', 24)
        timeliness_metric = self.assess_timeliness(timestamp, max_age)
        metrics.append(timeliness_metric)
        
        if not timeliness_metric.is_acceptable():
            issues.append("Устаревшие данные")
            recommendations.append("Обновить данные")
        
        # Оценка покрытия
        expected_items = context.get('expected_items', [])
        coverage_metric = self.assess_coverage(data, expected_items)
        metrics.append(coverage_metric)
        
        if not coverage_metric.is_acceptable():
            issues.append("Неполное покрытие данных")
            recommendations.append("Расширить охват анализа")
        
        # Расчет общего качества
        overall_score = self._calculate_weighted_score(metrics)
        level = self._determine_quality_level(overall_score)
        
        return QualityAssessment(
            overall_score=overall_score,
            level=level,
            metrics=metrics,
            issues=issues,
            recommendations=recommendations
        )
    
    def _field_exists(self, data: Dict[str, Any], field_path: str) -> bool:
        """Проверяет существование поля в данных."""
        keys = field_path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return False
        
        return True
    
    def _check_numeric_consistency(self, data: Dict[str, Any]) -> List[float]:
        """Проверяет согласованность числовых данных."""
        consistency_factors = []
        
        # Проверяем проценты (должны быть 0-100 или 0-1)
        percentage_fields = ['completion_rate', 'attendance_rate', 'engagement_score']
        for field in percentage_fields:
            if field in data:
                value = data[field]
                if isinstance(value, (int, float)):
                    if 0 <= value <= 1 or 0 <= value <= 100:
                        consistency_factors.append(1.0)
                    else:
                        consistency_factors.append(0.0)
        
        # Проверяем счетчики (должны быть неотрицательными)
        counter_fields = ['total_tasks', 'completed_tasks', 'meetings_attended']
        for field in counter_fields:
            if field in data:
                value = data[field]
                if isinstance(value, (int, float)) and value >= 0:
                    consistency_factors.append(1.0)
                else:
                    consistency_factors.append(0.0)
        
        return consistency_factors
    
    def _check_date_consistency(self, data: Dict[str, Any]) -> List[float]:
        """Проверяет согласованность дат."""
        consistency_factors = []
        
        date_fields = ['created_date', 'updated_date', 'analysis_date']
        dates = []
        
        for field in date_fields:
            if field in data:
                value = data[field]
                if isinstance(value, datetime):
                    dates.append(value)
                elif isinstance(value, str):
                    try:
                        from datetime import datetime
                        # Пробуем различные форматы
                        for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                            try:
                                dates.append(datetime.strptime(value, fmt))
                                break
                            except ValueError:
                                continue
                    except Exception:
                        consistency_factors.append(0.0)
        
        # Проверяем логическую последовательность дат
        if len(dates) >= 2:
            dates.sort()
            # created_date должна быть раньше updated_date
            consistency_factors.append(1.0)
        elif dates:
            consistency_factors.append(1.0)
        
        return consistency_factors
    
    def _check_relationship_consistency(self, data: Dict[str, Any]) -> List[float]:
        """Проверяет согласованность связей между данными."""
        consistency_factors = []
        
        # Проверяем логические отношения
        if 'total_tasks' in data and 'completed_tasks' in data:
            total = data['total_tasks']
            completed = data['completed_tasks']
            if isinstance(total, (int, float)) and isinstance(completed, (int, float)):
                if completed <= total:
                    consistency_factors.append(1.0)
                else:
                    consistency_factors.append(0.0)
        
        if 'total_meetings' in data and 'meetings_attended' in data:
            total = data['total_meetings']
            attended = data['meetings_attended']
            if isinstance(total, (int, float)) and isinstance(attended, (int, float)):
                if attended <= total:
                    consistency_factors.append(1.0)
                else:
                    consistency_factors.append(0.0)
        
        return consistency_factors
    
    def _item_exists_in_data(self, data: Dict[str, Any], item: str) -> bool:
        """Проверяет наличие элемента в данных."""
        # Простой поиск по строкам в значениях
        for key, value in data.items():
            if isinstance(value, str) and item.lower() in value.lower():
                return True
            elif isinstance(value, list) and any(item.lower() in str(v).lower() for v in value):
                return True
            elif isinstance(value, dict):
                if self._item_exists_in_data(value, item):
                    return True
        
        return False
    
    def _calculate_weighted_score(self, metrics: List[QualityMetric]) -> float:
        """Рассчитывает взвешенный показатель качества."""
        if not metrics:
            return 0.0
        
        total_weight = sum(metric.weight for metric in metrics)
        if total_weight == 0:
            return sum(metric.value for metric in metrics) / len(metrics)
        
        weighted_sum = sum(metric.value * metric.weight for metric in metrics)
        return weighted_sum / total_weight
    
    def _determine_quality_level(self, score: float) -> QualityLevel:
        """Определяет уровень качества по показателю."""
        if score >= 0.9:
            return QualityLevel.EXCELLENT
        elif score >= 0.8:
            return QualityLevel.GOOD
        elif score >= 0.6:
            return QualityLevel.ACCEPTABLE
        elif score >= 0.4:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL
