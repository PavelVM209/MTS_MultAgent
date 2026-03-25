"""
Quality Metrics System for MTS_MultAgent

This module provides comprehensive quality evaluation system for LLM-driven analysis
including convergence detection, quality scoring, and iterative improvement guidance.
"""

import json
import statistics
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field

import numpy as np
from pydantic import BaseModel

from .llm_client import LLMClient, QualityMetrics, get_llm_client


@dataclass
class ConvergenceCriteria:
    """Criteria for determining convergence in iterative improvement."""
    quality_threshold: float = 85.0  # Minimum quality score to stop
    min_improvement: float = 5.0  # Minimum improvement between iterations
    window_size: int = 3  # Number of iterations to check for convergence
    max_iterations: int = 5  # Maximum iterations regardless of convergence
    
    def should_stop(self, quality_history: List[float]) -> Tuple[bool, str]:
        """
        Determine if iterative improvement should stop.
        
        Returns:
            Tuple of (should_stop, reason)
        """
        if len(quality_history) >= self.max_iterations:
            return True, f"Maximum iterations ({self.max_iterations}) reached"
        
        if len(quality_history) == 0:
            return False, "No quality scores yet"
        
        current_quality = quality_history[-1]
        
        # Check if quality threshold is met
        if current_quality >= self.quality_threshold:
            return True, f"Quality threshold ({self.quality_threshold}) met with score {current_quality}"
        
        # Check for convergence (minimal improvement)
        if len(quality_history) >= self.window_size:
            recent_scores = quality_history[-self.window_size:]
            improvements = [
                recent_scores[i] - recent_scores[i-1]
                for i in range(1, len(recent_scores))
            ]
            
            avg_improvement = statistics.mean(improvements)
            if avg_improvement < self.min_improvement:
                return True, f"Converged with avg improvement {avg_improvement:.2f} < {self.min_improvement}"
        
        # Check for decreasing quality
        if len(quality_history) >= 2:
            last_improvement = quality_history[-1] - quality_history[-2]
            if last_improvement < -1.0:  # Significant decrease
                return True, f"Quality decreased by {abs(last_improvement):.2f}"
        
        return False, "Continue improving"


@dataclass
class QualityDimension:
    """Individual dimension of quality evaluation."""
    name: str
    weight: float = 1.0
    description: str = ""
    
    def evaluate(self, value: float) -> float:
        """Evaluate dimension with weight applied."""
        return value * self.weight


class QualityEvaluator:
    """
    Comprehensive quality evaluation system for LLM-driven results.
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or get_llm_client()
        self.dimensions = self._initialize_dimensions()
        
    def _initialize_dimensions(self) -> Dict[str, QualityDimension]:
        """Initialize quality evaluation dimensions."""
        return {
            "relevance": QualityDimension(
                name="relevance",
                weight=0.3,
                description="How well results match the original context and requirements"
            ),
            "completeness": QualityDimension(
                name="completeness",
                weight=0.25,
                description="How thoroughly all aspects of the task are addressed"
            ),
            "accuracy": QualityDimension(
                name="accuracy",
                weight=0.25,
                description="Correctness of data extraction and interpretation"
            ),
            "clarity": QualityDimension(
                name="clarity",
                weight=0.1,
                description="How clear and understandable the results are"
            ),
            "actionability": QualityDimension(
                name="actionability",
                weight=0.1,
                description="How actionable and useful the results are"
            )
        }
    
    async def evaluate_comprehensive(
        self,
        result_data: Dict[str, Any],
        expected_context: str,
        task_requirements: Optional[List[str]] = None
    ) -> QualityMetrics:
        """
        Comprehensive quality evaluation using multiple dimensions.
        """
        # Extract specific aspects for evaluation
        evaluation_aspects = self._extract_evaluation_aspects(result_data, expected_context)
        
        # Evaluate each dimension
        dimension_scores = {}
        for name, dimension in self.dimensions.items():
            score = await self._evaluate_dimension(
                dimension, 
                evaluation_aspects, 
                expected_context,
                task_requirements
            )
            dimension_scores[name] = score
        
        # Calculate weighted overall score
        overall_score = sum(
            dimension.evaluate(score)
            for dimension, score in zip(self.dimensions.values(), dimension_scores.values())
        )
        
        # Generate feedback
        feedback = await self._generate_feedback(dimension_scores, evaluation_aspects)
        
        return QualityMetrics(
            relevance_score=dimension_scores.get("relevance", 0),
            completeness_score=dimension_scores.get("completeness", 0),
            accuracy_score=dimension_scores.get("accuracy", 0),
            overall_quality=overall_score,
            feedback=feedback,
            metadata={
                "dimension_scores": dimension_scores,
                "evaluation_aspects": evaluation_aspects,
                "dimensions_count": len(self.dimensions)
            }
        )
    
    async def _evaluate_dimension(
        self,
        dimension: QualityDimension,
        evaluation_aspects: Dict[str, Any],
        expected_context: str,
        task_requirements: Optional[List[str]] = None
    ) -> float:
        """Evaluate a specific quality dimension."""
        
        prompt = f"""
        Оцени качество анализа по измерению "{dimension.name}".
        
        ОПИСАНИЕ ИЗМЕРЕНИЯ:
        {dimension.description}
        
        ИСХОДНЫЙ КОНТЕКСТ:
        {expected_context}
        
        ТРЕБОВАНИЯ К ЗАДАЧЕ:
        {task_requirements or ['Стандартные требования анализа']}
        
        РЕЗУЛЬТАТЫ АНАЛИЗА:
        {json.dumps(evaluation_aspects, ensure_ascii=False, indent=2)}
        
        ОЦЕНИ ПО ШКАЛЕ 0-100:
        - 0-20: Очень плохо - результат完全不 соответствует требованиям
        - 21-40: Плохо - есть существенные проблемы
        - 41-60: Удовлетворительно - базовые требования выполнены
        - 61-80: Хорошо - качественный результат с небольшими недочетами
        - 81-100: Отлично - результат превосходит ожидания
        
        Верни только число от 0 до 100 без объяснений.
        """
        
        try:
            response = await self.llm_client.complete({
                "prompt": prompt,
                "temperature": 0.1,
                "max_tokens": 10,
                "cache_key": f"quality_{dimension.name}_{hash(str(evaluation_aspects))}"
            })
            
            # Extract number from response
            score_text = response.content.strip()
            score = float(score_text.split()[0])  # Take first number
            
            # Ensure score is in valid range
            return max(0, min(100, score))
            
        except Exception as e:
            print(f"Error evaluating dimension {dimension.name}: {e}")
            return 50.0  # Default middle score
    
    def _extract_evaluation_aspects(
        self, 
        result_data: Dict[str, Any], 
        expected_context: str
    ) -> Dict[str, Any]:
        """Extract key aspects for quality evaluation."""
        aspects = {
            "has_summary": bool(result_data.get("summary")),
            "has_entities": bool(result_data.get("entities")),
            "has_key_phrases": bool(result_data.get("key_phrases")),
            "has_insights": bool(result_data.get("insights")),
            "data_completeness": self._calculate_data_completeness(result_data),
            "context_match": self._calculate_context_match(result_data, expected_context),
            "result_structure": self._analyze_result_structure(result_data)
        }
        
        return aspects
    
    def _calculate_data_completeness(self, result_data: Dict[str, Any]) -> float:
        """Calculate how complete the result data is."""
        expected_fields = [
            "summary", "entities", "key_phrases", "insights", 
            "relevant_context", "recommendations"
        ]
        
        present_fields = sum(1 for field in expected_fields if result_data.get(field))
        return (present_fields / len(expected_fields)) * 100
    
    def _calculate_context_match(self, result_data: Dict[str, Any], expected_context: str) -> float:
        """Calculate how well results match the expected context."""
        # Simple keyword overlap calculation (can be enhanced with semantic similarity)
        result_text = str(result_data).lower()
        context_words = set(expected_context.lower().split())
        
        if not context_words:
            return 50.0
        
        matching_words = sum(1 for word in context_words if word in result_text)
        return (matching_words / len(context_words)) * 100
    
    def _analyze_result_structure(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the structure of result data."""
        structure = {
            "total_keys": len(result_data),
            "nested_levels": self._calculate_nesting_level(result_data),
            "data_types": self._analyze_data_types(result_data),
            "list_content": isinstance(result_data.get("data"), list)
        }
        return structure
    
    def _calculate_nesting_level(self, obj: Any, current_level: int = 0) -> int:
        """Calculate maximum nesting level in data structure."""
        if isinstance(obj, dict):
            if not obj:
                return current_level
            return max(
                self._calculate_nesting_level(value, current_level + 1)
                for value in obj.values()
            )
        elif isinstance(obj, list):
            if not obj:
                return current_level
            return max(
                self._calculate_nesting_level(item, current_level + 1)
                for item in obj
            )
        else:
            return current_level
    
    def _analyze_data_types(self, result_data: Dict[str, Any]) -> Dict[str, int]:
        """Analyze distribution of data types."""
        type_counts = {}
        
        for value in result_data.values():
            data_type = type(value).__name__
            type_counts[data_type] = type_counts.get(data_type, 0) + 1
        
        return type_counts
    
    async def _generate_feedback(
        self, 
        dimension_scores: Dict[str, float], 
        evaluation_aspects: Dict[str, Any]
    ) -> str:
        """Generate constructive feedback based on dimension scores."""
        
        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []
        
        for dimension, score in dimension_scores.items():
            if score >= 70:
                strengths.append(f"{dimension} ({score:.0f}%)")
            elif score < 50:
                weaknesses.append(f"{dimension} ({score:.0f}%)")
        
        feedback_parts = []
        
        if strengths:
            feedback_parts.append(f"✅ **Сильные стороны**: {', '.join(strengths)}")
        
        if weaknesses:
            feedback_parts.append(f"⚠️ **Требуют улучшения**: {', '.join(weaknesses)}")
        
        # Add specific recommendations based on aspects
        recommendations = self._generate_recommendations(evaluation_aspects, dimension_scores)
        if recommendations:
            feedback_parts.append(f"💡 **Рекомендации**: {recommendations}")
        
        return " | ".join(feedback_parts) if feedback_parts else "Результат соответствует ожиданиям"
    
    def _generate_recommendations(
        self, 
        aspects: Dict[str, Any], 
        scores: Dict[str, float]
    ) -> str:
        """Generate specific recommendations based on evaluation aspects."""
        recommendations = []
        
        if aspects.get("data_completeness", 0) < 70:
            recommendations.append("дополнить недостающие поля данных")
        
        if scores.get("clarity", 0) < 60:
            recommendations.append("улучшить структуру результатов")
        
        if scores.get("relevance", 0) < 70:
            recommendations.append("лучше учесть контекст задачи")
        
        return ", ".join(recommendations) if recommendations else ""
