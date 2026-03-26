"""
LLM Client Module

Provides integration with OpenAI API for analysis and insights generation.
Includes retry logic, error handling, and response validation.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

try:
    import openai
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

from .config import get_config
from .quality_metrics import QualityMetrics

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Available LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


@dataclass
class LLMRequest:
    """LLM request configuration."""
    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    model: Optional[str] = None
    provider: LLMProvider = LLMProvider.OPENAI
    response_format: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """LLM response with metadata."""
    content: str
    model: str
    usage: Dict[str, int]
    response_time: float
    quality_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMClientError(Exception):
    """Base exception for LLM client errors."""
    pass


class LLMQuotaExceededError(LLMClientError):
    """Raised when API quota is exceeded."""
    pass


class LLMRateLimitError(LLMClientError):
    """Raised when rate limit is exceeded."""
    pass


class LLMClient:
    """
    LLM Client for OpenAI API integration.
    
    Provides:
    - OpenAI API client with async support
    - Retry logic and error handling
    - Response validation and quality scoring
    - Token usage tracking
    - Model selection and configuration
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLM client.
        
        Args:
            config: Client configuration dictionary
        """
        self.config = config or {}
        self._client = None
        self._quality_metrics = QualityMetrics()
        self._setup_client()
        
    def _setup_client(self) -> None:
        """Setup OpenAI client."""
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI library not available. Install with: pip install openai")
            return
            
        try:
            # Get configuration
            app_config = get_config()
            llm_config = self.config.get('llm', app_config.get('llm', {}))
            
            # Initialize client
            api_key = llm_config.get('api_key')
            base_url = llm_config.get('base_url')
            organization = llm_config.get('organization')
            
            self._client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
                organization=organization
            )
            
            # Set default model
            self.default_model = llm_config.get('model', 'gpt-3.5-turbo')
            self.max_tokens = llm_config.get('max_tokens', 2000)
            self.temperature = llm_config.get('temperature', 0.7)
            
            # Retry configuration
            self.max_retries = llm_config.get('max_retries', 3)
            self.retry_delay = llm_config.get('retry_delay', 1.0)
            
            logger.info(f"LLM client initialized with model: {self.default_model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            self._client = None
    
    async def is_available(self) -> bool:
        """Check if LLM client is available."""
        if not OPENAI_AVAILABLE or not self._client:
            return False
            
        try:
            # Test with a simple request
            response = await self._client.chat.completions.create(
                model=self.default_model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.warning(f"LLM client not available: {e}")
            return False
    
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """
        Generate response from LLM.
        
        Args:
            request: LLM request configuration
            
        Returns:
            LLM response with metadata
            
        Raises:
            LLMClientError: If request fails
        """
        if not self._client:
            raise LLMClientError("LLM client not initialized")
        
        # Set defaults
        model = request.model or self.default_model
        max_tokens = request.max_tokens or self.max_tokens
        
        # Prepare messages
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        
        # Prepare request parameters
        kwargs = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": request.temperature
        }
        
        if request.response_format:
            kwargs["response_format"] = request.response_format
        
        # Execute with retries
        last_error = None
        start_time = time.time()
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"LLM request attempt {attempt + 1}/{self.max_retries + 1}")
                
                response = await self._client.chat.completions.create(**kwargs)
                
                # Calculate response time
                response_time = time.time() - start_time
                
                # Extract content and metadata
                content = response.choices[0].message.content
                
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
                
                # Create response object
                llm_response = LLMResponse(
                    content=content,
                    model=model,
                    usage=usage,
                    response_time=response_time,
                    metadata={
                        "attempt": attempt + 1,
                        "provider": request.provider.value
                    }
                )
                
                # Quality assessment
                llm_response.quality_score = await self._assess_quality(llm_response)
                
                logger.info(f"LLM response generated in {response_time:.2f}s, "
                           f"tokens: {usage['total_tokens']}, "
                           f"quality: {llm_response.quality_score:.2f}")
                
                return llm_response
                
            except openai.RateLimitError as e:
                last_error = LLMRateLimitError(f"Rate limit exceeded: {e}")
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Rate limit hit, waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                continue
                
            except openai.APIError as e:
                last_error = LLMClientError(f"API error: {e}")
                if attempt < self.max_retries:
                    wait_time = self.retry_delay
                    logger.warning(f"API error, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                continue
                
            except Exception as e:
                last_error = LLMClientError(f"Unexpected error: {e}")
                if attempt < self.max_retries:
                    wait_time = self.retry_delay
                    logger.warning(f"Unexpected error, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                continue
        
        # All retries failed
        logger.error(f"LLM request failed after {self.max_retries + 1} attempts: {last_error}")
        raise last_error
    
    async def _assess_quality(self, response: LLMResponse) -> float:
        """
        Assess response quality.
        
        Args:
            response: LLM response to assess
            
        Returns:
            Quality score (0.0-1.0)
        """
        try:
            # Basic quality metrics
            content_length = len(response.content.strip())
            
            # Length score (too short or too long is bad)
            length_score = 1.0
            if content_length < 50:  # Too short
                length_score = 0.5
            elif content_length > 4000:  # Too long
                length_score = 0.8
            
            # Response time score (faster is better)
            time_score = max(0.1, 1.0 - (response.response_time / 10.0))
            
            # Token efficiency score
            total_tokens = response.usage.get('total_tokens', 0)
            efficiency_score = min(1.0, 1000.0 / max(total_tokens, 1))
            
            # Combined score
            quality_score = (length_score * 0.4 + time_score * 0.3 + efficiency_score * 0.3)
            
            return min(1.0, max(0.0, quality_score))
            
        except Exception as e:
            logger.warning(f"Failed to assess quality: {e}")
            return 0.5  # Default score
    
    async def generate_structured_response(
        self, 
        prompt: str, 
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response.
        
        Args:
            prompt: User prompt
            schema: JSON schema for response format
            system_prompt: Optional system prompt
            
        Returns:
            Parsed JSON response
        """
        request = LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format={"type": "json_object"}
        )
        
        response = await self.generate_response(request)
        
        try:
            # Parse JSON response
            parsed_response = json.loads(response.content)
            
            # Basic validation against schema
            if not self._validate_schema(parsed_response, schema):
                logger.warning("Response doesn't match expected schema")
                
            return parsed_response
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise LLMClientError(f"Invalid JSON response: {e}")
    
    def _validate_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Basic schema validation."""
        try:
            required_keys = schema.get('required', [])
            return all(key in data for key in required_keys)
        except Exception:
            return False
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "client_available": await self.is_available(),
            "default_model": getattr(self, 'default_model', None),
            "max_tokens": getattr(self, 'max_tokens', None),
            "quality_metrics": self._quality_metrics.get_summary()
        }


# Global client instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get global LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


async def initialize_llm_client(config: Optional[Dict[str, Any]] = None) -> LLMClient:
    """Initialize LLM client with configuration."""
    global _llm_client
    _llm_client = LLMClient(config)
    
    # Test availability
    if await _llm_client.is_available():
        logger.info("LLM client initialized and available")
    else:
        logger.warning("LLM client initialized but not available")
    
    return _llm_client


# Utility functions
async def analyze_jira_data(jira_data: str, context: str = "") -> Dict[str, Any]:
    """
    Analyze JIRA data using LLM.
    
    Args:
        jira_data: Raw JIRA data
        context: Additional context for analysis
        
    Returns:
        Analysis results
    """
    client = get_llm_client()
    
    prompt = f"""
    Analyze the following JIRA data and extract key insights:
    
    JIRA Data:
    {jira_data}
    
    Context: {context}
    
    Please provide analysis in JSON format with the following structure:
    {{
        "tasks_analysis": {{
            "total_tasks": number,
            "completed_tasks": number,
            "in_progress_tasks": number,
            "blocked_tasks": number
        }},
        "employees_analysis": {{
            "total_employees": number,
            "active_employees": number,
            "workload_distribution": [{{"employee": "name", "task_count": number}}]
        }},
        "projects_analysis": {{
            "total_projects": number,
            "active_projects": number,
            "project_progress": [{{"project": "name", "completion_percentage": number}}]
        }},
        "insights": ["key insight 1", "key insight 2"],
        "recommendations": ["recommendation 1", "recommendation 2"]
    }}
    """
    
    schema = {
        "required": ["tasks_analysis", "employees_analysis", "projects_analysis", "insights", "recommendations"]
    }
    
    return await client.generate_structured_response(prompt, schema)


async def analyze_meeting_protocol(protocol_text: str) -> Dict[str, Any]:
    """
    Analyze meeting protocol using LLM.
    
    Args:
        protocol_text: Meeting protocol text
        
    Returns:
        Analysis results
    """
    client = get_llm_client()
    
    prompt = f"""
    Analyze the following meeting protocol and extract key information:
    
    Protocol Text:
    {protocol_text}
    
    Please provide analysis in JSON format with the following structure:
    {{
        "meeting_info": {{
            "date": "YYYY-MM-DD",
            "participants": ["name1", "name2"],
            "duration": "X hours Y minutes"
        }},
        "action_items": [
            {{
                "description": "Task description",
                "responsible": "Person name",
                "deadline": "YYYY-MM-DD",
                "status": "pending/in_progress/completed"
            }}
        ],
        "decisions": ["decision 1", "decision 2"],
        "key_topics": ["topic 1", "topic 2"],
        "next_steps": ["step 1", "step 2"]
    }}
    """
    
    schema = {
        "required": ["meeting_info", "action_items", "decisions", "key_topics", "next_steps"]
    }
    
    return await client.generate_structured_response(prompt, schema)
