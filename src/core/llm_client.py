"""
LLM Client for MTS_MultAgent

This module provides a unified interface for interacting with various LLM providers
including OpenAI, local models, and fallback strategies with caching and quality monitoring.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from enum import Enum

import aiohttp
import tiktoken
from pydantic import BaseModel, Field

from .config import get_settings
from .base_agent import BaseAgent


class LLMProvider(Enum):
    """Available LLM providers."""
    OPENAI = "openai"
    LOCAL = "local"
    MOCK = "mock"


class LLMRequest(BaseModel):
    """LLM request model."""
    prompt: str = Field(..., description="The prompt to send to LLM")
    max_tokens: int = Field(default=4000, description="Maximum tokens in response")
    temperature: float = Field(default=0.1, description="Temperature for sampling")
    model: Optional[str] = Field(None, description="Model to use")
    provider: Optional[LLMProvider] = Field(None, description="LLM provider")
    cache_key: Optional[str] = Field(None, description="Cache key for response")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class LLMResponse(BaseModel):
    """LLM response model."""
    content: str = Field(..., description="Response content")
    model: str = Field(..., description="Model used")
    provider: LLMProvider = Field(..., description="Provider used")
    tokens_used: int = Field(default=0, description="Tokens used")
    response_time: float = Field(..., description="Response time in seconds")
    cache_hit: bool = Field(default=False, description="Whether response was from cache")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @property
    def is_valid(self) -> bool:
        """Check if response is valid."""
        return bool(self.content.strip())


class QualityMetrics(BaseModel):
    """Quality metrics for LLM responses."""
    relevance_score: float = Field(..., description="Relevance score (0-100)")
    completeness_score: float = Field(..., description="Completeness score (0-100)")
    accuracy_score: float = Field(..., description="Accuracy score (0-100)")
    overall_quality: float = Field(..., description="Overall quality score (0-100)")
    feedback: str = Field(default="", description="Feedback for improvement")
    timestamp: datetime = Field(default_factory=datetime.now, description="Evaluation timestamp")


class IterationResult(BaseModel):
    """Result of iterative improvement."""
    iteration: int = Field(..., description="Current iteration number")
    quality_score: float = Field(..., description="Quality score for this iteration")
    data: Dict[str, Any] = Field(..., description="Result data")
    feedback: str = Field(default="", description="Feedback for next iteration")
    needs_refinement: bool = Field(..., description="Whether further refinement is needed")
    improvements_made: List[str] = Field(default_factory=list, description="Improvements made")
    convergence_detected: bool = Field(default=False, description="Whether convergence is detected")


class LLMClient(BaseAgent):
    """
    Unified LLM client with multiple providers, caching, and quality monitoring.
    """
    
    def __init__(self):
        super().__init__("LLMClient")
        self.settings = get_settings()
        self.providers = self._initialize_providers()
        self.cache = {}  # Simple in-memory cache (upgrade to Redis/ChromaDB later)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.metrics = {
            "requests_total": 0,
            "cache_hits": 0,
            "tokens_total": 0,
            "response_times": [],
            "errors": 0
        }
        
    def _initialize_providers(self) -> List[LLMProvider]:
        """Initialize available LLM providers based on configuration."""
        providers = []
        
        if self.settings.OPENAI_API_KEY:
            providers.append(LLMProvider.OPENAI)
        
        # Always include mock as fallback
        providers.append(LLMProvider.MOCK)
        
        self.logger.info(f"Initialized LLM providers: {[p.value for p in providers]}")
        return providers
    
    async def complete(
        self, 
        request: LLMRequest,
        cache_enabled: bool = True
    ) -> LLMResponse:
        """
        Complete an LLM request with caching and fallback.
        """
        start_time = time.time()
        
        # Check cache first
        if cache_enabled and request.cache_key:
            cached_response = self._get_from_cache(request.cache_key)
            if cached_response:
                self.metrics["cache_hits"] += 1
                self.logger.debug(f"Cache hit for key: {request.cache_key}")
                return cached_response
        
        # Try providers in order
        for provider in self.providers:
            try:
                response = await self._call_provider(provider, request)
                
                # Update metrics
                self.metrics["requests_total"] += 1
                self.metrics["tokens_total"] += response.tokens_used
                self.metrics["response_times"].append(response.response_time)
                
                # Cache response if valid
                if cache_enabled and response.is_valid and request.cache_key:
                    self._cache_response(request.cache_key, response)
                
                return response
                
            except Exception as e:
                self.logger.error(f"Provider {provider.value} failed: {e}")
                self.metrics["errors"] += 1
                continue
        
        raise RuntimeError("All LLM providers failed")
    
    async def _call_provider(self, provider: LLMProvider, request: LLMRequest) -> LLMResponse:
        """Call a specific LLM provider."""
        if provider == LLMProvider.OPENAI:
            return await self._call_openai(request)
        elif provider == LLMProvider.LOCAL:
            return await self._call_local(request)
        elif provider == LLMProvider.MOCK:
            return await self._call_mock(request)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def _call_openai(self, request: LLMRequest) -> LLMResponse:
        """Call OpenAI API."""
        start_time = time.time()
        
        headers = {
            "Authorization": f"Bearer {self.settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": request.model or self.settings.OPENAI_MODEL,
            "messages": [{"role": "user", "content": request.prompt}],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"OpenAI API error: {response.status} - {error_text}")
                
                data = await response.json()
                content = data["choices"][0]["message"]["content"]
                tokens_used = data.get("usage", {}).get("total_tokens", 0)
                model = data["model"]
                
                response_time = time.time() - start_time
                
                return LLMResponse(
                    content=content,
                    model=model,
                    provider=LLMProvider.OPENAI,
                    tokens_used=tokens_used,
                    response_time=response_time,
                    cache_hit=False
                )
    
    async def _call_local(self, request: LLMRequest) -> LLMResponse:
        """Call local LLM implementation."""
        # Placeholder for local LLM integration
        # Could be Ollama, Llama.cpp, or other local models
        start_time = time.time()
        
        # Simulate local LLM call
        await asyncio.sleep(0.5)  # Simulate processing time
        
        response_time = time.time() - start_time
        
        return LLMResponse(
            content="[LOCAL LLM] This is a mock response from local LLM implementation.",
            model="local-llm",
            provider=LLMProvider.LOCAL,
            tokens_used=100,
            response_time=response_time,
            cache_hit=False
        )
    
    async def _call_mock(self, request: LLMRequest) -> LLMResponse:
        """Mock LLM provider for testing and fallback."""
        start_time = time.time()
        
        # Generate a realistic mock response based on prompt
        if "анализ" in request.prompt.lower() or "analysis" in request.prompt.lower():
            mock_content = """
            На основе анализа предоставленных данных, я могу выделить следующие ключевые аспекты:

            1. **Структура данных**: Данные организованы в табличном формате с четкими заголовками
            2. **Ключевые показатели**: Наблюдаются определенные тенденции в метриках
            3. **Корреляции**: Присутствуют связи между различными параметрами
            4. **Рекомендации**: Предлагается уделить внимание аномальным значениям

            Для более детального анализа требуется дополнительная информация о контексте и целях исследования.
            """
        elif "сравнение" in request.prompt.lower() or "compare" in request.prompt.lower():
            mock_content = """
            Результаты сравнения показывают следующие различия:

            **Сходства:**
            - Общая структура данных совпадает
            - Основные метрики имеют схожую динамику

            **Различия:**
            - Наблюдаются расхождения в количественных показателях
            - Временные паттерны имеют отличия

            **Выводы:**
            Различия могут быть объяснены различными методами сбора данных или временными факторами.
            """
        else:
            mock_content = "Я проанализировал ваш запрос и готов предоставить рекомендации по дальнейшим действиям."
        
        response_time = time.time() - start_time
        
        return LLMResponse(
            content=mock_content,
            model="mock-gpt-4",
            provider=LLMProvider.MOCK,
            tokens_used=len(self.tokenizer.encode(mock_content)),
            response_time=response_time,
            cache_hit=False
        )
    
    async def evaluate_quality(
        self, 
        result_data: Dict[str, Any], 
        expected_context: str,
        evaluation_criteria: Optional[List[str]] = None
    ) -> QualityMetrics:
        """
        Evaluate the quality of analysis results using LLM.
        """
        if not evaluation_criteria:
            evaluation_criteria = ["relevance", "completeness", "accuracy"]
        
        prompt = f"""
        Оцени качество анализа данных по отношению к исходному контексту.
        
        ИСХОДНЫЙ КОНТЕКСТ:
        {expected_context}
        
        ПОЛУЧЕННЫЕ ДАННЫЕ:
        {self._format_data_for_evaluation(result_data)}
        
        КРИТЕРИИ ОЦЕНКИ:
        {', '.join(evaluation_criteria)}
        
        ОЦЕНИ ПО ШКАЛЕ 0-100%:
        1. Relevance Score: Насколько данные соответствуют контексту
        2. Completeness Score: Полнота охвата аспектов контекста
        3. Accuracy Score: Точность извлечения и интерпретации
        4. Overall Quality: Интегральная оценка качества
        
        Формат ответа: JSON с метриками и объяснением
        """
        
        request = LLMRequest(
            prompt=prompt,
            temperature=0.1,
            max_tokens=1000,
            cache_key=f"quality_eval_{hash(expected_context + str(result_data))}"
        )
        
        response = await self.complete(request)
        
        try:
            # Parse JSON response
            metrics_data = json.loads(response.content)
            
            return QualityMetrics(
                relevance_score=metrics_data.get("relevance_score", 0),
                completeness_score=metrics_data.get("completeness_score", 0),
                accuracy_score=metrics_data.get("accuracy_score", 0),
                overall_quality=metrics_data.get("overall_quality", 0),
                feedback=metrics_data.get("feedback", ""),
                metadata={"raw_response": response.content}
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to parse quality evaluation: {e}")
            
            # Fallback metrics
            return QualityMetrics(
                relevance_score=70.0,
                completeness_score=70.0,
                accuracy_score=70.0,
                overall_quality=70.0,
                feedback="Failed to parse evaluation result"
            )
    
    async def generate_improvements(
        self, 
        current_result: Dict[str, Any], 
        feedback: str,
        iteration: int
    ) -> str:
        """
        Generate improvements suggestions based on current result and feedback.
        """
        prompt = f"""
        Проанализируй текущий результат和建议 улучшения для итерации #{iteration + 1}.
        
        ТЕКУЩИЙ РЕЗУЛЬТАТ:
        {self._format_data_for_evaluation(current_result)}
        
        ОБРАТНАЯ СВЯЗЬ:
        {feedback}
        
        ПРЕДЛОЖИ КОНКРЕТНЫЕ УЛУЧШЕНИЯ:
        1. Что нужно исправить в анализе?
        2. Какие данные еще нужно извлечь?
        3. Как улучшить интерпретацию?
        4. Какие дополнительные métriques добавить?
        
        Формат: Структурированные предложения для улучшения
        """
        
        request = LLMRequest(
            prompt=prompt,
            temperature=0.2,
            max_tokens=800,
            cache_key=f"improvements_{hash(str(current_result) + feedback)}_{iteration}"
        )
        
        response = await self.complete(request)
        return response.content
    
    def _format_data_for_evaluation(self, data: Dict[str, Any]) -> str:
        """Format data for LLM evaluation."""
        if isinstance(data, dict):
            formatted = []
            for key, value in data.items():
                if isinstance(value, (list, dict)):
                    formatted.append(f"{key}: {json.dumps(value, ensure_ascii=False, indent=2)}")
                else:
                    formatted.append(f"{key}: {value}")
            return "\n".join(formatted)
        else:
            return str(data)
    
    def _get_from_cache(self, cache_key: str) -> Optional[LLMResponse]:
        """Get response from cache if valid."""
        if cache_key in self.cache:
            cached_item = self.cache[cache_key]
            
            # Check TTL (30 minutes)
            if datetime.now() - cached_item["timestamp"] < timedelta(minutes=30):
                return cached_item["response"]
            else:
                # Remove expired cache entry
                del self.cache[cache_key]
        
        return None
    
    def _cache_response(self, cache_key: str, response: LLMResponse):
        """Cache a response."""
        self.cache[cache_key] = {
            "response": response,
            "timestamp": datetime.now()
        }
        
        # Limit cache size
        if len(self.cache) > 1000:
            # Remove oldest entries
            oldest_keys = sorted(
                self.cache.keys(),
                key=lambda k: self.cache[k]["timestamp"]
            )[:100]
            
            for key in oldest_keys:
                del self.cache[key]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        cache_hit_rate = (
            self.metrics["cache_hits"] / max(self.metrics["requests_total"], 1) * 100
        )
        
        avg_response_time = (
            sum(self.metrics["response_times"]) / len(self.metrics["response_times"])
            if self.metrics["response_times"] else 0
        )
        
        return {
            **self.metrics,
            "cache_hit_rate": cache_hit_rate,
            "avg_response_time": avg_response_time,
            "cache_size": len(self.cache)
        }


# Global LLM client instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get global LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


async def complete_llm_request(
    prompt: str,
    **kwargs
) -> LLMResponse:
    """Convenience function to complete an LLM request."""
    client = get_llm_client()
    request = LLMRequest(prompt=prompt, **kwargs)
    return await client.complete(request)
