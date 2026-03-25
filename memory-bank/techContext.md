# Tech Context - MTS_MultAgent LLM-Driven Architecture

## 🧠 НОВЫЙ ТЕХНОЛОГИЧЕСКИЙ СТЕК - LLM-CENTRIC

### Основные технологии
- **Python 3.11+**: Основной язык разработки (LLM-оптимизированный)
- **asyncio**: Асинхронное программирование для параллельных LLM запросов
- **aiohttp**: HTTP клиент для API запросов
- **pandas**: Обработка данных Excel
- **openpyxl**: Работа с Excel файлами больших размеров (2-3 ГБ)
- **click**: CLI интерфейс
- **python-dotenv**: Управление переменными окружения
- **pydantic**: Валидация данных с LLM-моделями
- **FastAPI**: Веб-интерфейс (второй этап)

### 🚀 LLM Integration Stack
- **OpenAI API**: Primary LLM provider
- **Local LLM Support**: Ollama, Llama 2, и другие
- **LangChain**: LLM orchestration и prompt management
- **Vector Databases**: ChromaDB для кэширования LLM ответов
- **Prompt Templates**: Jinja2 для динамических промптов
- **Rate Limiting**: Управление LLM API запросами

### Итеративные алгоритмы
- **Quality Convergence**: Алгоритмы сходимости итераций
- **Adaptive Strategies**: Динамическая корректировка стратегий
- **Bayesian Optimization**: Оптимизация гиперпараметров LLM
- **Reinforcement Learning**: Обучение на основе обратной связи

## Настройка разработки

### Требования к окружению
```bash
# Проверка доступных версий Python - требуется 3.11+ для LLM оптимизации
python --version
python3 --version

# Виртуальное окружение (ОБЯЗАТЕЛЬНО)
python3.11 -m venv venv_py311  # Рекомендуемая версия
source venv_py311/bin/activate

# Проверка активации
(venv_py311) $ python --version
# Python 3.11.x
```

### ⚠️ КРИТИЧЕСКИ ВАЖНО: LLM окружение

**Особенности для LLM разработки:**
- **Python 3.11+**: Оптимизация производительности для LLM
- **Дополнительная память**: Минимум 4GB RAM для LLM операций
- **网络稳定性**: Стабильное соединение для LLM API
- **GPU поддержка**: Опционально для локальных LLM

### Обновленная структура requirements.txt
```txt
# Core dependencies
aiohttp>=3.8.0
pandas>=1.5.0
openpyxl>=3.0.0
click>=8.0.0
python-dotenv>=0.19.0
pydantic>=2.0.0  # Версия 2+ для LLM моделей

# LLM Integration
openai>=1.0.0
langchain>=0.1.0
langchain-openai>=0.0.5
chromadb>=0.4.0
tiktoken>=0.5.0
jinja2>=3.1.0

# Итеративные алгоритмы
numpy>=1.24.0
scipy>=1.10.0
scikit-learn>=1.3.0
matplotlib>=3.7.0
seaborn>=0.12.0

# Big Data обработки
dask>=2023.1.0
modin[pandas]>=0.20.0  # Для больших Excel файлов
memory-profiler>=0.60.0

# Web interface (Phase 2)
fastapi>=0.100.0
uvicorn>=0.23.0

# Development с LLM тестами
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-mock>=3.11.0
black>=23.0.0
mypy>=1.5.0
pre-commit>=3.3.0
```

## 🧠 LLM Конфигурация

### Переменные окружения
```bash
# LLM Configuration
OPENAI_API_KEY="your-openai-api-key"
OPENAI_MODEL="gpt-4-turbo-preview"
OPENAI_TEMPERATURE=0.1
OPENAI_MAX_TOKENS=4000
OPENAI_TIMEOUT=60

# Local LLM Support
LOCAL_LLM_ENABLED=false
LOCAL_LLM_MODEL="llama2"
LOCAL_LLM_BASE_URL="http://localhost:11434"

# Vector Database
CHROMA_PERSIST_DIRECTORY="./chroma_db"
CHROMA_COLLECTION_NAME="mts_analysis"

# Итеративное улучшение
MAX_ITERATIONS=5
QUALITY_THRESHOLD=85.0
CONVERGENCE_MIN_IMPROVEMENT=5.0

# Caching и Performance
CACHE_ENABLED=true
CACHE_TTL=3600
LLM_REQUEST_TIMEOUT=60
MAX_CONCURRENT_LLM_REQUESTS=3

# Jira Configuration (без изменений)
JIRA_BASE_URL="https://your-company.atlassian.net"
JIRA_ACCESS_TOKEN="your-jira-token"
JIRA_USERNAME="your-email@company.com"

# Confluence Configuration
CONFLUENCE_BASE_URL="https://your-company.atlassian.net/wiki"
CONFLUENCE_ACCESS_TOKEN="your-confluence-token"
CONFLUENCE_SPACE="your-space"
ROOT_PAGE_ID_TO_ADD_NEW_PAGES=897438835

# Project Configuration
PROJECT_NAME="Stroki.Clone.S3.Integration.Api"
WEB_REQUEST_TIMEOUT_IN_SECONDS=30

# Logging для LLM
LOG_LEVEL="INFO"
LLM_LOG_LEVEL="DEBUG"
LOG_FILE="logs/mts_agent.log"
PROMPT_LOG_FILE="logs/prompts.log"
```

## 🔄 LLM API интеграции

### OpenAI API Configuration
```python
# LLM Client Configuration
class LLMConfig:
    api_key: str
    model: str = "gpt-4-turbo-preview"
    temperature: float = 0.1
    max_tokens: int = 4000
    timeout: int = 60
    max_retries: int = 3
    rate_limit: int = 100  # requests per minute

# Prompt Templates
PROMPT_TEMPLATES = {
    "context_analysis": """
    Ты - эксперт бизнес-аналитик с глубоким пониманием корпоративных данных.
    
    ЗАДАЧА: {task_description}
    КОНТЕКСТ JIRA: {jira_context}
    ДОСТУПНЫЕ КОЛОНКИ EXCEL: {excel_columns}
    
    Проанализируй и сгенерируй точные запросы для извлечения релевантных данных.
    """,
    
    "quality_evaluation": """
    Оцени качество анализа по шкале 0-100%:
    
    ИСХОДНЫЙ КОНТЕКСТ: {original_context}
    ПОЛУЧЕННЫЕ ДАННЫЕ: {result_data}
    
    Оцени: relevance, completeness, accuracy, overall_quality
    """,
    
    "improvement_suggestions": """
    Проанализируй результаты и предложи улучшения:
    
    ТЕКУЩИЕ РЕЗУЛЬТАТЫ: {current_results}
    ОЖИДАЕМЫЕ ДАННЫЕ: {expected_data}
    ПРЕДЫДУЩИЙ ФИДБЕК: {previous_feedback}
    
    Сгенерируй улучшенные запросы для следующей итерации.
    """
}
```

### Local LLM Support
```python
# Local LLM Configuration (Ollama)
class LocalLLMConfig:
    enabled: bool = False
    model: str = "llama2"
    base_url: str = "http://localhost:11434"
    timeout: int = 120
    temperature: float = 0.1
    
# Fallback Strategy
class LLMFallbackConfig:
    primary_provider: str = "openai"
    fallback_provider: str = "local"
    failover_threshold: int = 3  # consecutive failures
    auto_switch: bool = True
```

## 🔄 Архитектурные паттерны для LLM

### Итеративный цикл улучшения
```python
class IterativeImprovementPattern:
    """Базовый паттерн для итеративного улучшения через LLM"""
    
    async def improve_until_convergence(
        self,
        initial_input: Any,
        quality_threshold: float = 85.0,
        max_iterations: int = 5
    ) -> IterationResult:
        
        current_iteration = 0
        best_result = None
        best_quality = 0.0
        
        while current_iteration < max_iterations:
            # LLM анализ и улучшение
            improved_result = await self.llm_improve(
                initial_input, 
                previous_result=best_result,
                iteration=current_iteration
            )
            
            # LLM оценка качества
            quality_score = await self.llm_evaluate_quality(
                improved_result, 
                initial_input
            )
            
            # Проверка сходимости
            if quality_score >= quality_threshold:
                break
            
            # Сохранение лучшего результата
            if quality_score > best_quality:
                best_quality = quality_score
                best_result = improved_result
            
            current_iteration += 1
        
        return IterationResult(
            final_result=best_result,
            quality_score=best_quality,
            iterations=current_iteration,
            converged=quality_score >= quality_threshold
        )
```

### LLM Caching Strategy
```python
class LLMCacheManager:
    """Интеллектуальное кэширование LLM запросов"""
    
    def __init__(self):
        self.vector_db = ChromaDB()
        self.cache_ttl = 3600  # 1 hour
        
    async def get_cached_response(
        self, 
        prompt: str, 
        context_hash: str
    ) -> Optional[str]:
        """Получение кэшированного LLM ответа"""
        
    async def cache_response(
        self, 
        prompt: str, 
        response: str, 
        context_hash: str
    ) -> None:
        """Кэширование LLM ответа"""
        
    async def find_similar_prompts(
        self, 
        prompt: str, 
        similarity_threshold: float = 0.85
    ) -> List[str]:
        """Поиск похожих промптов в кэше"""
```

### Quality Convergence Algorithm
```python
class QualityConvergenceDetector:
    """Алгоритм определения сходимости качества"""
    
    def __init__(self, min_improvement: float = 5.0, window_size: int = 3):
        self.min_improvement = min_improvement
        self.window_size = window_size
        self.quality_history = []
        
    def has_converged(self, current_quality: float) -> bool:
        """Определение сходимости на основе истории качества"""
        self.quality_history.append(current_quality)
        
        if len(self.quality_history) < self.window_size:
            return False
        
        recent_qualities = self.quality_history[-self.window_size:]
        improvements = [
            recent_qualities[i] - recent_qualities[i-1]
            for i in range(1, len(recent_qualities))
        ]
        
        avg_improvement = sum(improvements) / len(improvements)
        return avg_improvement < self.min_improvement
```

## 🚀 Performance оптимизация для LLM

### Параллельные LLM запросы
```python
import asyncio
from asyncio import Semaphore

class ConcurrentLLMProcessor:
    def __init__(self, max_concurrent: int = 3):
        self.semaphore = Semaphore(max_concurrent)
        
    async def process_batch_requests(
        self, 
        requests: List[LLMRequest]
    ) -> List[LLMResponse]:
        """Параллельная обработка LLM запросов"""
        
        async def process_single_request(request):
            async with self.semaphore:
                return await self.llm_client.complete(request.prompt)
        
        tasks = [process_single_request(req) for req in requests]
        return await asyncio.gather(*tasks)
```

### Memory оптимизация для больших Excel файлов
```python
class MemoryOptimizedExcelProcessor:
    def __init__(self, chunk_size: int = 10000):
        self.chunk_size = chunk_size
        
    async def process_large_excel(
        self, 
        file_path: str, 
        llm_processor: LLMProcessor
    ) -> Iterator[ChunkResult]:
        """Построчная обработка больших Excel файлов"""
        
        for chunk in pd.read_excel(file_path, chunksize=self.chunk_size):
            # LLM анализ чанка
            chunk_analysis = await llm_processor.analyze_chunk(chunk)
            yield ChunkResult(data=chunk, analysis=chunk_analysis)
            
            # Очистка памяти
            del chunk
            gc.collect()
```

## 🔄 Мониторинг и отладка LLM

### LLM-специфичные метрики
```python
class LLMMetrics:
    """Метрики для мониторинга LLM производительности"""
    
    def __init__(self):
        self.request_count = 0
        self.token_usage = 0
        self.response_times = []
        self.error_rates = {}
        self.quality_scores = []
        
    def track_request(
        self, 
        tokens_used: int, 
        response_time: float, 
        quality_score: float
    ):
        """Трекинг LLM запроса"""
        self.request_count += 1
        self.token_usage += tokens_used
        self.response_times.append(response_time)
        self.quality_scores.append(quality_score)
        
    def get_performance_stats(self) -> Dict[str, float]:
        """Получение статистики производительности"""
        return {
            "avg_response_time": sum(self.response_times) / len(self.response_times),
            "avg_quality_score": sum(self.quality_scores) / len(self.quality_scores),
            "total_tokens": self.token_usage,
            "tokens_per_request": self.token_usage / self.request_count
        }
```

### LLM Logging
```python
class LLMPromptLogger:
    """Логирование промптов и ответов для анализа"""
    
    def __init__(self, log_file: str = "logs/prompts.log"):
        self.log_file = log_file
        
    async def log_interaction(
        self, 
        prompt: str, 
        response: str, 
        metadata: Dict[str, Any]
    ):
        """Логирование LLM взаимодействия"""
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "prompt": prompt,
            "response": response,
            "metadata": metadata,
            "prompt_tokens": len(prompt.split()),
            "response_tokens": len(response.split())
        }
        
        async with aiofiles.open(self.log_file, "a") as f:
            await f.write(json.dumps(log_entry) + "\n")
```

## 🧪 Тестирование LLM-систем

### LLM-интеграционные тесты
```python
class LLMIntegrationTests:
    """Тесты для LLM-интеграции"""
    
    async def test_iterative_improvement_convergence(self):
        """Тест сходимости итеративного улучшения"""
        
    async def test_quality_evaluation_consistency(self):
        """Тест консистентности оценки качества"""
        
    async def test_prompt_robustness(self):
        """Тест устойчивости к variation в промптах"""
        
    async def test_fallback_mechanism(self):
        """Тест механизма fallback при недоступности LLM"""
```

### Mock LLM для тестирования
```python
class MockLLMClient:
    """Mock LLM клиент для тестирования"""
    
    def __init__(self, response_delay: float = 0.1):
        self.response_delay = response_delay
        self.predetermined_responses = {}
        
    async def complete(self, prompt: str) -> str:
        """Mock LLM completion с детерминированными ответами"""
        await asyncio.sleep(self.response_delay)
        
        prompt_hash = hash(prompt)
        if prompt_hash in self.predetermined_responses:
            return self.predetermined_responses[prompt_hash]
            
        # Генерация осмысленного mock ответа
        return self._generate_mock_response(prompt)
```

## 🚀 Развертывание LLM-систем

### Production LLM конфигурация
```bash
# Production оптимизации
export OPENAI_MODEL="gpt-4-turbo-preview"
export OPENAI_TEMPERATURE=0.0  # Для консистентности
export MAX_CONCURRENT_LLM_REQUESTS=5
export CACHE_ENABLED=true
export CACHE_TTL=7200  # 2 часа

# Мониторинг
export PROMETHEUS_ENABLED=true
export LLM_METRICS_EXPORT=true
export QUALITY_TRACKING=true
```

### Docker для LLM-систем
```dockerfile
FROM python:3.11-slim

# GPU поддержка для локальных LLM
RUN apt-get update && apt-get install -y \
    nvidia-cuda-toolkit \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes конфигурация
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mts-multagent-llm
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mts-multagent-llm
  template:
    spec:
      containers:
      - name: mts-multagent
        image: mts-multagent:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: mts-secrets
              key: openai-api-key
```

Новая архитектура обеспечивает полную интеллектуализацию системы с итеративным улучшением результатов через LLM.
