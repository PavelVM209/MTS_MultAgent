"""
LLM-Driven Comparison Agent for MTS MultAgent System

This agent provides intelligent comparison analysis with:
- Zero hardcoded comparison logic - all intelligence through LLM
- Intelligent data alignment and comparison
- Predictive insights and recommendations
- Iterative improvement until convergence
- Contextual relationship mapping
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.base_agent import BaseAgent, AgentResult
from src.core.models import (
    LLMContextResult, LLMExcelResult, LLMComparisonResult, ComparisonItem, Discrepancy
)
from src.core.llm_client import LLMClient, get_llm_client, LLMRequest
from src.core.iterative_engine import IterativeEngine, get_iterative_engine
from src.core.quality_metrics import QualityEvaluator, get_quality_evaluator


class ComparisonAgent(BaseAgent):
    """
    LLM-driven Comparison Agent with intelligent data alignment.
    
    Features:
    - 100% LLM-based comparison logic
    - Intelligent entity matching and alignment
    - Predictive insights and recommendations
    - Iterative improvement of comparison results
    - Contextual relationship analysis
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize LLM-driven ComparisonAgent."""
        super().__init__(config, "ComparisonAgent")
        
        # Initialize LLM components
        self.llm_client = get_llm_client()
        self.iterative_engine = get_iterative_engine()
        self.quality_evaluator = get_quality_evaluator()
        
        # Configuration
        self.max_iterations = self.get_config_value("comparison.max_iterations", 5)
        self.quality_threshold = self.get_config_value("comparison.quality_threshold", 85.0)
        
        self.logger.info("LLM-driven ComparisonAgent initialized")
    
    async def validate(self, task: Dict[str, Any]) -> bool:
        """Validate comparison task parameters."""
        try:
            required_fields = ["context_result", "excel_result"]
            for field in required_fields:
                if field not in task:
                    self.logger.error(f"Missing required field: {field}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error("Comparison task validation failed", error=str(e))
            return False
    
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        """
        Execute LLM-driven comparison with iterative improvement.
        """
        try:
            # Extract input data
            context_result = task["context_result"]
            excel_result = task["excel_result"]
            
            # Step 1: Initial LLM-driven comparison
            initial_comparison = await self._perform_llm_comparison(
                context_result, excel_result
            )
            
            # Step 2: Iterative improvement
            improved_comparison = await self.iterative_engine.improve_until_convergence(
                initial_data=initial_comparison,
                improve_function=self._improve_comparison_analysis,
                expected_context=json.dumps({
                    "context_entities": len(context_result.get("entities", [])),
                    "excel_tables": len(excel_result.get("tables", [])),
                    "excel_rows": excel_result.get("total_rows", 0)
                }),
                task_requirements=[
                    "Accurate entity matching between context and Excel data",
                    "Comprehensive discrepancy detection",
                    "Intelligent insights with predictive recommendations",
                    "Contextual relationship mapping"
                ]
            )
            
            # Step 3: Generate detailed analysis
            detailed_analysis = await self._generate_detailed_analysis(
                improved_comparison.data, context_result, excel_result
            )
            
            # Create LLMComparisonResult
            result = LLMComparisonResult(
                comparisons=detailed_analysis.get("comparisons", []),
                discrepancies=detailed_analysis.get("discrepancies", []),
                insights=detailed_analysis.get("insights", []),
                recommendations=detailed_analysis.get("recommendations", []),
                confidence_scores=detailed_analysis.get("confidence_scores", {}),
                summary_report=detailed_analysis.get("summary_report", ""),
                intelligent_insights=detailed_analysis.get("intelligent_insights", []),
                contextual_analysis=detailed_analysis.get("contextual_analysis", ""),
                predictive_recommendations=detailed_analysis.get("predictive_recommendations", []),
                quality_metrics=getattr(improved_comparison, 'quality_metrics', None),
                iteration_result=improved_comparison
            )
            
            self.logger.info(
                "LLM-driven comparison completed",
                quality_score=improved_comparison.quality_score,
                iterations=improved_comparison.iteration,
                comparisons=len(result.comparisons),
                discrepancies=len(result.discrepancies),
                insights=len(result.intelligent_insights)
            )
            
            return AgentResult(
                success=True,
                data=result.dict(),
                agent_name=self.name,
                metadata={
                    "quality_score": improved_comparison.quality_score,
                    "iterations": improved_comparison.iteration,
                    "alignment_score": detailed_analysis.get("alignment_score", 0)
                }
            )
            
        except Exception as e:
            self.logger.error("LLM-driven comparison failed", error=str(e), exc_info=True)
            return AgentResult(
                success=False,
                error=f"Comparison failed: {str(e)}",
                agent_name=self.name
            )
    
    async def _perform_llm_comparison(
        self, 
        context_result: Dict[str, Any], 
        excel_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform initial LLM-driven comparison analysis."""
        
        # Prepare data for LLM
        context_summary = self._extract_context_summary(context_result)
        excel_summary = self._extract_excel_summary(excel_result)
        
        prompt = f"""
        Проанализируй и сравни данные из контекстного анализа и Excel файлов.
        
        КОНТЕКСТНЫЙ АНАЛИЗ:
        {context_summary}
        
        ДАННЫЕ EXCEL:
        {excel_summary}
        
        ВЫПОЛНИ ИНТЕЛЛЕКТУАЛЬНОЕ СРАВНЕНИЕ И ВЕРНИ РЕЗУЛЬТАТ В ФОРМАТЕ JSON:
        {{
            "alignment_analysis": {{
                "alignment_score": 85.5,
                "matched_entities": ["сущность1", "сущность2"],
                "unmatched_context_entities": ["сущность3"],
                "unmatched_excel_data": ["данные1"],
                "data_consistency": "высокая"
            }},
            "comparisons": [
                {{
                    "criterion": "критерий сравнения",
                    "jira_value": "значение из контекста",
                    "excel_value": "значение из Excel",
                    "match": true,
                    "confidence": 0.85,
                    "notes": "примечания к сравнению"
                }}
            ],
            "discrepancies": [
                {{
                    "type": "тип расхождения",
                    "jira_data": "данные из контекста",
                    "excel_data": "данные из Excel",
                    "description": "описание расхождения",
                    "severity": "medium"
                }}
            ],
            "insights": ["инсайт1", "инсайт2"],
            "recommendations": ["рекомендация1", "рекомендация2"],
            "confidence_scores": {{
                "entities_matching": 0.85,
                "data_consistency": 0.90,
                "overall_quality": 0.87
            }},
            "summary_report": "сводный отчет сравнения"
        }}
        
        ТРЕБОВАНИЯ:
        - Выполни глубокий семантический анализ соответствия данных
        - Выяви ВСЕ значимые расхождения и несоответствия
        - Генерируй интеллектуальные инсайты на основе сравнения
        - Предоставь конкретные рекомендации для улучшения alignment
        - Оцени качество и уверенность каждого аспектра сравнения
        """
        
        try:
            response = await self.llm_client.complete(LLMRequest(
                prompt=prompt,
                temperature=0.1,
                max_tokens=4000,
                cache_key=f"comparison_analysis_{hash(context_summary + excel_summary)}"
            ))
            
            comparison_data = json.loads(response.content)
            
            # Convert to proper objects
            comparison_items = []
            for comp in comparison_data.get("comparisons", []):
                comparison_items.append(ComparisonItem(**comp))
            
            discrepancies = []
            for disc in comparison_data.get("discrepancies", []):
                discrepancies.append(Discrepancy(**disc))
            
            return {
                **comparison_data,
                "comparisons": [comp.dict() for comp in comparison_items],
                "discrepancies": [disc.dict() for disc in discrepancies],
                "raw_analysis": comparison_data
            }
            
        except Exception as e:
            self.logger.error(f"LLM comparison analysis failed: {e}")
            return {
                "comparisons": [],
                "discrepancies": [],
                "insights": [f"Comparison analysis failed: {str(e)}"],
                "recommendations": [],
                "confidence_scores": {"overall_quality": 0.5},
                "summary_report": "Analysis failed"
            }
    
    async def _improve_comparison_analysis(
        self, 
        current_analysis: Dict[str, Any], 
        improvements_suggestions: str
    ) -> Dict[str, Any]:
        """Improve comparison analysis based on LLM suggestions."""
        prompt = f"""
        Улучши анализ сравнения на основе обратной связи.
        
        ТЕКУЩИЙ АНАЛИЗ СРАВНЕНИЯ:
        {json.dumps(current_analysis, ensure_ascii=False, indent=2)}
        
        ПРЕДЛОЖЕНИЯ ПО УЛУЧШЕНИЮ:
        {improvements_suggestions}
        
        ВЕРНИ УЛУЧШЕННЫЙ АНАЛИЗ В ТОМ ЖЕ JSON ФОРМАТЕ.
        
        ФОКУС НА УЛУЧШЕНИЯХ:
        - Повысь точность сопоставления сущностей
        - Добавь пропущенные расхождения
        - Углуби качество инсайтов
        - Расширь рекомендации с учетом контекста
        """
        
        try:
            response = await self.llm_client.complete(LLMRequest(
                prompt=prompt,
                temperature=0.2,
                max_tokens=4000,
                cache_key=f"comparison_improvement_{hash(str(current_analysis) + improvements_suggestions)}"
            ))
            
            improved_data = json.loads(response.content)
            return improved_data
            
        except Exception as e:
            self.logger.error(f"Comparison improvement failed: {e}")
            return current_analysis
    
    async def _generate_detailed_analysis(
        self, 
        comparison_data: Dict[str, Any], 
        context_result: Dict[str, Any], 
        excel_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate detailed analysis with intelligent insights."""
        
        prompt = f"""
        На основе результатов сравнения сгенерируй подробный интеллектуальный анализ.
        
        РЕЗУЛЬТАТЫ СРАВНЕНИЯ:
        {json.dumps(comparison_data, ensure_ascii=False, indent=2)}
        
        КОНТЕКСТНЫЕ ДАННЫЕ:
        {json.dumps(context_result, ensure_ascii=False)[:1500]}
        
        ДАННЫЕ EXCEL:
        {json.dumps(excel_result, ensure_ascii=False)[:1500]}
        
        ВЕРНИ ПОДРОБНЫЙ АНАЛИЗ В ФОРМАТЕ JSON:
        {{
            "alignment_score": 87.5,
            "comparisons": [/* существующие comparisons */],
            "discrepancies": [/* существующие discrepancies */],
            "insights": [/* расширенные инсайты */],
            "recommendations": [/* конкретные рекомендации */],
            "confidence_scores": {{"overall": 0.88}},
            "summary_report": "подробный сводный отчет",
            "intelligent_insights": [
                "интеллектуальный инсайт 1",
                "интеллектуальный инсайт 2"
            ],
            "contextual_analysis": "контекстуальный анализ",
            "predictive_recommendations": [
                "предиктивная рекомендация 1",
                "предиктивная рекомендация 2"
            ]
        }}
        
        ТРЕБОВАНИЯ:
        - Сгенерируй интеллектуальные инсайты на основе паттернов в данных
        - Предоставь предиктивные рекомендации для будущего улучшения
        - Выполни глубокий контекстуальный анализ
        - Обеспечь actionable рекомендации
        """
        
        try:
            response = await self.llm_client.complete(LLMRequest(
                prompt=prompt,
                temperature=0.2,
                max_tokens=3000,
                cache_key=f"detailed_analysis_{hash(str(comparison_data))}"
            ))
            
            detailed_data = json.loads(response.content)
            
            # Merge with original data
            final_analysis = {
                **comparison_data,
                **detailed_data,
                "alignment_score": detailed_data.get("alignment_score", 0)
            }
            
            return final_analysis
            
        except Exception as e:
            self.logger.error(f"Detailed analysis generation failed: {e}")
            return comparison_data
    
    def _extract_context_summary(self, context_result: Dict[str, Any]) -> str:
        """Extract key information from context result."""
        entities = context_result.get("entities", [])[:5]  # Top 5 entities
        key_phrases = context_result.get("key_phrases", [])[:10]  # Top 10 phrases
        semantic_insights = context_result.get("semantic_insights", [])[:5]
        
        summary = {
            "entities": [{"text": e.get("text", ""), "label": e.get("label", ""), "confidence": e.get("confidence", 0)} for e in entities],
            "key_phrases": key_phrases,
            "semantic_insights": semantic_insights,
            "language": context_result.get("language", "unknown"),
            "total_entities": len(context_result.get("entities", []))
        }
        
        return json.dumps(summary, ensure_ascii=False, indent=2)
    
    def _extract_excel_summary(self, excel_result: Dict[str, Any]) -> str:
        """Extract key information from Excel result."""
        tables = excel_result.get("tables", [])[:3]  # Top 3 tables
        column_analysis = excel_result.get("column_analysis", [])[:10]  # Top 10 columns
        data_insights = excel_result.get("data_insights", [])
        
        # Prepare table summary
        tables_summary = []
        for table in tables:
            tables_summary.append({
                "title": table.get("title", ""),
                "row_count": table.get("row_count", 0),
                "columns": table.get("columns", [])[:5]  # First 5 columns
            })
        
        summary = {
            "tables": tables_summary,
            "column_analysis": column_analysis,
            "data_insights": data_insights,
            "total_rows": excel_result.get("total_rows", 0),
            "total_sheets": excel_result.get("total_sheets", 0)
        }
        
        return json.dumps(summary, ensure_ascii=False, indent=2)
    
    async def analyze_alignment_quality(
        self, 
        context_result: LLMContextResult, 
        excel_result: LLMExcelResult
    ) -> Dict[str, Any]:
        """
        Analyze alignment quality between context and Excel data.
        """
        context_summary = self._extract_context_summary(context_result.dict())
        excel_summary = self._extract_excel_summary(excel_result.dict())
        
        prompt = f"""
        Проанализируй качество alignment между контекстным анализом и данными Excel.
        
        КОНТЕКСТ:
        {context_summary}
        
        EXCEL:
        {excel_summary}
        
        ВЕРНИ АНАЛИЗ КАЧЕСТВА В ФОРМАТЕ JSON:
        {{
            "overall_alignment_score": 85.5,
            "entity_alignment_quality": 88.0,
            "data_consistency_score": 82.0,
            "semantic_coherence": 87.5,
            "alignment_issues": [
                {{
                    "type": "missing_entity",
                    "description": "Entity found in context but not in Excel",
                    "severity": "medium"
                }}
            ],
            "improvement_suggestions": [
                "улучшение alignment 1",
                "улучшение alignment 2"
            ]
        }}
        """
        
        try:
            response = await self.llm_client.complete(LLMRequest(
                prompt=prompt,
                temperature=0.1,
                max_tokens=2000,
                cache_key=f"alignment_quality_{hash(context_summary + excel_summary)}"
            ))
            
            return json.loads(response.content)
            
        except Exception as e:
            self.logger.error(f"Alignment quality analysis failed: {e}")
            return {"error": str(e)}
    
    async def generate_predictive_insights(
        self, 
        comparison_result: LLMComparisonResult
    ) -> List[str]:
        """
        Generate predictive insights based on comparison results.
        """
        comparison_data = comparison_result.dict()
        
        prompt = f"""
        На основе результатов сравнения сгенерируй предиктивные инсайты.
        
        РЕЗУЛЬТАТЫ СРАВНЕНИЯ:
        {json.dumps(comparison_data, ensure_ascii=False, indent=2)}
        
        ВЕРНИ ПРЕДИКТИВНЫЕ ИНСАЙТЫ В ФОРМАТЕ JSON МАССИВА:
        [
            "Предиктивный инсайт 1...",
            "Предиктивный инсайт 2..."
        ]
        
        ТРЕБОВАНИЯ:
        - Проанализируй тренды и паттерны в расхождениях
        - Спрогнозируй потенциальные проблемы
        - Предскажи возможности для улучшения
        - Обеспечь actionable предиктивные рекомендации
        """
        
        try:
            response = await self.llm_client.complete(LLMRequest(
                prompt=prompt,
                temperature=0.3,
                max_tokens=1500,
                cache_key=f"predictive_insights_{hash(str(comparison_data))}"
            ))
            
            return json.loads(response.content)
            
        except Exception as e:
            self.logger.error(f"Predictive insights generation failed: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for LLM-driven ComparisonAgent."""
        base_health = await super().health_check()
        
        # Test LLM components
        llm_health = {
            "status": "healthy" if all([
                self.llm_client,
                self.iterative_engine,
                self.quality_evaluator
            ]) else "error",
            "components": {
                "llm_client": bool(self.llm_client),
                "iterative_engine": bool(self.iterative_engine),
                "quality_evaluator": bool(self.quality_evaluator)
            }
        }
        
        base_health.update({
            "analysis_type": "llm_driven",
            "hardcoded_patterns": "none",
            "llm_health": llm_health,
            "supported_features": [
                "intelligent_comparison",
                "entity_alignment",
                "predictive_insights",
                "iterative_improvement",
                "contextual_analysis"
            ]
        })
        
        return base_health


# Factory function for dependency injection
def create_comparison_agent(config: Dict[str, Any]) -> ComparisonAgent:
    """Factory function to create ComparisonAgent instance."""
    return ComparisonAgent(config)
