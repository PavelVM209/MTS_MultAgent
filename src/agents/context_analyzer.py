"""
LLM-Driven Context Analyzer Agent for MTS MultAgent System

This agent provides 100% LLM-driven context analysis with:
- Zero hardcoded patterns - all intelligence through LLM
- Iterative self-improvement until 85%+ quality
- Intelligent query generation for Excel integration
- Semantic insights and relationship mapping
- Adaptive convergence detection
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.base_agent import BaseAgent, AgentResult
from src.core.models import (
    ContextTask, LLMContextResult, ExtractedEntity, TextSummary, 
    IntelligentQuery, ExcelColumnInfo
)
from src.core.llm_client import LLMClient, get_llm_client, LLMRequest
from src.core.iterative_engine import IterativeEngine, get_iterative_engine
from src.core.quality_metrics import QualityEvaluator, get_quality_evaluator


class ContextAnalyzer(BaseAgent):
    """
    LLM-driven Context Analyzer with Zero hardcoded logic.
    
    Features:
    - 100% LLM-based entity extraction and analysis
    - Iterative improvement until convergence
    - Intelligent query generation
    - Semantic relationship mapping
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize LLM-driven ContextAnalyzer."""
        super().__init__(config, "ContextAnalyzer")
        
        # Initialize LLM components
        self.llm_client = get_llm_client()
        self.iterative_engine = get_iterative_engine()
        self.quality_evaluator = get_quality_evaluator()
        
        # Configuration
        self.max_iterations = self.get_config_value("context.max_iterations", 5)
        self.quality_threshold = self.get_config_value("context.quality_threshold", 85.0)
        
        self.logger.info("LLM-driven ContextAnalyzer initialized")
    
    async def validate(self, task: Dict[str, Any]) -> bool:
        """Validate ContextAnalyzer task parameters."""
        try:
            context_task = ContextTask(**task)
            
            if not context_task.text_content and not context_task.meeting_protocols:
                self.logger.error("Either text_content or meeting_protocols is required")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error("Context task validation failed", error=str(e))
            return False
    
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        """
        Execute LLM-driven context analysis with iterative improvement.
        """
        context_task = ContextTask(**task)
        
        try:
            # Combine all text sources
            combined_text = self._combine_text_sources(context_task)
            
            if not combined_text.strip():
                raise ValueError("No text content to analyze")
            
            # Perform LLM-driven analysis with iterative improvement
            initial_result = await self._initial_llm_analysis(combined_text, context_task)
            
            # Validate and improve iteratively
            final_result = await self.iterative_engine.improve_until_convergence(
                initial_data=initial_result,
                improve_function=self._improve_context_analysis,
                expected_context=combined_text,
                task_requirements=[
                    "Extract comprehensive entities and relationships",
                    "Generate intelligent queries for Excel data extraction",
                    "Provide semantic insights and context understanding",
                    "Create actionable summary with key points"
                ]
            )
            
            # Convert to LLMContextResult
            context_result = LLMContextResult(
                entities=final_result.data.get("entities", []),
                key_phrases=final_result.data.get("key_phrases", []),
                relevant_context=final_result.data.get("relevant_context", []),
                summary=final_result.data.get("summary"),
                language=final_result.data.get("language", "unknown"),
                relevance_scores=final_result.data.get("relevance_scores", {}),
                metadata=final_result.data.get("metadata", {}),
                intelligent_queries=final_result.data.get("intelligent_queries", []),
                semantic_insights=final_result.data.get("semantic_insights", []),
                data_relationships=final_result.data.get("data_relationships", {}),
                quality_metrics=getattr(final_result, 'quality_metrics', None),
                iteration_result=final_result
            )
            
            self.logger.info(
                "LLM-driven context analysis completed",
                quality_score=final_result.quality_score,
                iterations=final_result.iteration,
                entities=len(context_result.entities),
                queries_generated=len(context_result.intelligent_queries)
            )
            
            return AgentResult(
                success=True,
                data=context_result.dict(),
                agent_name=self.name,
                metadata={
                    "quality_score": final_result.quality_score,
                    "iterations": final_result.iteration,
                    "converged": final_result.convergence_detected
                }
            )
            
        except Exception as e:
            self.logger.error("LLM-driven context analysis failed", error=str(e), exc_info=True)
            return AgentResult(
                success=False,
                error=f"Context analysis failed: {str(e)}",
                agent_name=self.name
            )
    
    def _combine_text_sources(self, task: ContextTask) -> str:
        """Combine text from various sources into unified content."""
        text_parts = []
        
        # Add main text content
        if task.text_content:
            text_parts.append(f"## Основной контекст\n{task.text_content}")
        
        # Add meeting protocols
        if task.meeting_protocols:
            text_parts.append("## Протоколы совещаний")
            for i, protocol in enumerate(task.meeting_protocols, 1):
                if isinstance(protocol, dict):
                    title = protocol.get("title", f"Протокол {i}")
                    content = protocol.get("content", "")
                    text_parts.append(f"### {title}\n{content}")
                else:
                    text_parts.append(f"### Протокол {i}\n{protocol}")
        
        # Add additional documents
        if task.additional_documents:
            text_parts.append("## Дополнительные документы")
            for i, doc in enumerate(task.additional_documents, 1):
                if isinstance(doc, dict):
                    content = doc.get("content", "")
                    if content:
                        text_parts.append(f"### Документ {i}\n{content}")
                else:
                    text_parts.append(f"### Документ {i}\n{doc}")
        
        return "\n\n".join(text_parts)
    
    async def _initial_llm_analysis(self, text: str, task: ContextTask) -> Dict[str, Any]:
        """
        Perform initial LLM-driven analysis without hardcoded patterns.
        """
        prompt = f"""
        Проанализируй текстовый контекст и извлеки всю релевантную информацию.
        
        ИСХОДНЫЙ ДАННЫЕ:
        {text}
        
        ЗАДАЧА ОПИСАНИЕ:
        {task.task_description}
        
        КЛЮЧЕВЫЕ СЛОВА ДЛЯ ПОИСКА:
        {', '.join(task.search_keywords) if task.search_keywords else 'Не указаны'}
        
        ВЕРНИ РЕЗУЛЬТАТ В ФОРМАТЕ JSON:
        {{
            "entities": [
                {{
                    "text": "текст сущности",
                    "label": "тип сущности",
                    "start": позиция_в_тексте,
                    "end": позиция_конца,
                    "confidence": 0.95,
                    "context": "контекст вокруг сущности"
                }}
            ],
            "key_phrases": ["ключевая фраза 1", "ключевая фраза 2"],
            "relevant_context": ["релевантный отрывок 1", "релевантный отрывок 2"],
            "summary": {{
                "summary": "краткое содержание",
                "bullet_points": ["• ключевой пункт 1", "• ключевой пункт 2"],
                "key_topics": ["тема 1", "тема 2"],
                "word_count": количество_слов
            }},
            "language": "ru",
            "relevance_scores": {{"ключевое слово": очки_релевантности}},
            "semantic_insights": ["семантический инсайт 1", "семантический инсайт 2"],
            "data_relationships": {{
                "сущность1": ["связанная сущность 1", "связанная сущность 2"]
            }}
        }}
        
        ТРЕБОВАНИЯ:
        - Извлеки ВСЕ релевантные сущности без ограничений по типам
        - Генерируй семантические осмысленные связи между данными
        - Создай глубокий анализ контекста, а не поверхностный
        - Используй естественный язык в summary и insights
        """
        
        try:
            response = await self.llm_client.complete(LLMRequest(
                prompt=prompt,
                temperature=0.1,
                max_tokens=4000,
                cache_key=f"context_analysis_{hash(text)}"
            ))
            
            # Parse JSON response
            result_data = json.loads(response.content)
            
            # Add metadata
            result_data["metadata"] = {
                "analysis_method": "_llm_driven",
                "processing_time": datetime.now().isoformat(),
                "text_length": len(text),
                "llm_provider": response.provider.value
            }
            
            return result_data
            
        except Exception as e:
            self.logger.error(f"Initial LLM analysis failed: {e}")
            # Return minimal structure for fallback
            return {
                "entities": [],
                "key_phrases": [],
                "relevant_context": [],
                "summary": TextSummary(summary="", bullet_points=[], key_topics=[], word_count=0),
                "language": "unknown",
                "relevance_scores": {},
                "semantic_insights": [],
                "data_relationships": {},
                "metadata": {"error": str(e)}
            }
    
    async def _improve_context_analysis(
        self, 
        current_data: Dict[str, Any], 
        improvements_suggestions: str
    ) -> Dict[str, Any]:
        """
        Improve context analysis based on LLM-generated suggestions.
        """
        # Reconstruct original text from metadata or use a placeholder
        original_text = current_data.get("metadata", {}).get("original_text", "")
        
        prompt = f"""
        Улучши анализ контекста на основе обратной связи.
        
        ТЕКУЩИЙ РЕЗУЛЬТАТ АНАЛИЗА:
        {json.dumps(current_data, ensure_ascii=False, indent=2)}
        
        ПРЕДЛОЖЕНИЯ ПО УЛУЧШЕНИЮ:
        {improvements_suggestions}
        
        ОРИГИНАЛЬНЫЙ ТЕКСТ:
        {original_text}
        
        ВЕРНИ УЛУЧШЕННЫЙ РЕЗУЛЬТАТ В ТОМ ЖЕ JSON ФОРМАТЕ.
        
        ФОКУС НА УЛУЧШЕНИЯХ:
        - Добавь пропущенные сущности и связи
        - Улучши качество семантического анализа
        - Расширь релевантные контекстные отрывки
        - Углуби инсайты и выводы
        """
        
        try:
            response = await self.llm_client.complete(LLMRequest(
                prompt=prompt,
                temperature=0.2,
                max_tokens=4000,
                cache_key=f"context_improvement_{hash(str(current_data) + improvements_suggestions)}"
            ))
            
            improved_data = json.loads(response.content)
            
            # Preserve metadata and add improvement info
            improved_data["metadata"] = {
                **current_data.get("metadata", {}),
                "improved": True,
                "improvement_timestamp": datetime.now().isoformat()
            }
            
            return improved_data
            
        except Exception as e:
            self.logger.error(f"Context analysis improvement failed: {e}")
            return current_data  # Return original if improvement fails
    
    async def generate_intelligent_queries(
        self, 
        context_result: LLMContextResult, 
        excel_structure: List[ExcelColumnInfo]
    ) -> List[IntelligentQuery]:
        """
        Generate intelligent queries for Excel data extraction based on context analysis.
        """
        structured_context = self._context_to_structured_format(context_result)
        excel_info = [{"column": col.column_name, "type": col.data_type, "meaning": col.semantic_meaning} 
                     for col in excel_structure]
        
        prompt = f"""
        На основе анализа контекста и структуры Excel данных сгенерируй интеллектуальные запросы для извлечения данных.
        
        АНАЛИЗ КОНТЕКСТА:
        {structured_context}
        
        СТРУКТУРА EXCEL:
        {json.dumps(excel_info, ensure_ascii=False, indent=2)}
        
        СГЕНЕРИРУЙ ЗАПРОСЫ В ФОРМАТЕ JSON МАССИВА:
        [
            {{
                "query_description": "описание запроса на естественном языке",
                "sql_equivalent": "SQL эквивалент если применимо",
                "target_columns": ["колонка1", "колонка2"],
                "expected_output_format": "table",
                "confidence_score": 0.85
            }}
        ]
        
        ТРЕБОВАНИЯ К ЗАПРОСАМ:
        - Запросы должны напрямую соответствовать задачам из анализа контекста
- Используй конкретные названия колонок из Excel
        - Создавай запросы для извлечения релевантных метрик и данных
        - Обеспечь логическую связь между контекстом и данными Excel
        - Генерируй 3-5 наиболее релевантных запросов
        """
        
        try:
            response = await self.llm_client.complete(LLMRequest(
                prompt=prompt,
                temperature=0.1,
                max_tokens=2000,
                cache_key=f"queries_generation_{hash(structured_context + str(excel_info))}"
            ))
            
            queries_data = json.loads(response.content)
            
            return [IntelligentQuery(**query) for query in queries_data]
            
        except Exception as e:
            self.logger.error(f"Intelligent queries generation failed: {e}")
            return []
    
    async def analyze_excel_context_alignment(
        self, 
        context_result: LLMContextResult, 
        excel_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze alignment between context analysis and Excel data.
        """
        prompt = f"""
        Проанализируй соответствие между контекстным анализом и данными Excel.
        
        РЕЗУЛЬТАТЫ АНАЛИЗА КОНТЕКСТА:
        {self._context_to_structured_format(context_result)}
        
        ДАННЫЕ EXCEL:
        {json.dumps(excel_data, ensure_ascii=False, indent=2)[:3000]}
        
        ВЕРНИ АНАЛИЗ В ФОРМАТЕ JSON:
        {{
            "alignment_score": 85.5,
            "aligned_entities": ["сущность1", "сущность2"],
            "misaligned_elements": [{"context_item": "элемент1", "issue": "не найден в данных"}],
            "data_validation": {{
                "completeness": 80.0,
                "accuracy": 85.0,
                "relevance": 90.0
            }},
            "recommendations": ["рекомендация1", "рекомендация2"]
        }}
        """
        
        try:
            response = await self.llm_client.complete(LLMRequest(
                prompt=prompt,
                temperature=0.1,
                max_tokens=1500,
                cache_key=f"context_alignment_{hash(str(context_result) + str(excel_data)[:1000])}"
            ))
            
            return json.loads(response.content)
            
        except Exception as e:
            self.logger.error(f"Context alignment analysis failed: {e}")
            return {"error": str(e)}
    
    def _context_to_structured_format(self, context_result: LLMContextResult) -> str:
        """Convert context result to structured format for LLM processing."""
        structured = {
            "summary": context_result.summary.summary if context_result.summary else "",
            "key_topics": context_result.summary.key_topics if context_result.summary else [],
            "entities": [{"text": e.text, "label": e.label, "confidence": e.confidence} 
                        for e in context_result.entities],
            "semantic_insights": context_result.semantic_insights,
            "data_relationships": context_result.data_relationships
        }
        return json.dumps(structured, ensure_ascii=False, indent=2)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for LLM-driven ContextAnalyzer."""
        base_health = await super().health_check()
        
        try:
            # Test LLM functionality
            test_text = "Тестовый текст для проверки LLM анализа контекста."
            test_result = await self._initial_llm_analysis(test_text, ContextTask(
                task_description="Тестовая задача",
                text_content=test_text
            ))
            
            llm_health = {
                "status": "healthy",
                "llm_client_available": bool(self.llm_client),
                "iterative_engine_available": bool(self.iterative_engine),
                "quality_evaluator_available": bool(self.quality_evaluator),
                "test_analysis_successful": bool(test_result.get("entities"))
            }
        except Exception as e:
            llm_health = {"status": "error", "error": str(e)}
        
        base_health.update({
            "analysis_type": "llm_driven",
            "hardcoded_patterns": "none",
            "llm_health": llm_health,
            "supported_features": [
                "llm_entity_extraction",
                "iterative_improvement", 
                "intelligent_queries",
                "semantic_analysis",
                "context_alignment"
            ]
        })
        
        return base_health


# Factory function for dependency injection
def create_context_analyzer(config: Dict[str, Any]) -> ContextAnalyzer:
    """Factory function to create ContextAnalyzer instance."""
    return ContextAnalyzer(config)
