# Technical Context - MTS MultAgent Technology Stack

## 🛠️ Используемые технологии

### **Core Technology Stack**
- **Language:** Python 3.11+
- **Runtime:** Linux Server (Ubuntu 20.04+ recommended)
- **Package Management:** pip + requirements.txt + pyproject.toml
- **Virtual Environment:** venv_py311/

### **Key Libraries & Frameworks**
```python
# Core dependencies
asyncio                 # Асинхронное выполнение
aiohttp                # HTTP клиент для API запросов
pydantic               # Валидация данных и модели
pyyaml                 # Работа с YAML конфигурацией
python-dotenv          # Управление environment variables
click                  # CLI интерфейс

# LLM Integration
openai                 # OpenAI API клиент
# yandexgpt            # Yandex GPT (опционально)

# Data Processing
pandas                 # Обработка данных
openpyxl               # Excel файлы (legacy support)
python-docx            # Word документы
python-multipart       # Multipart form data

# Web & API
fastapi                # REST API сервер
uvicorn                # ASGI сервер

# Testing
pytest                 # Unit тесты
pytest-asyncio         # Async тесты
pytest-cov             # Coverage отчеты
```

## 🔧 Настройка разработки

### **Development Environment Setup**
```bash
# 1. Создание виртуального окружения
python3.11 -m venv venv_py311

# 2. Активация (ВАЖНО: всегда делать первой командой)
source venv_py311/bin/activate

# 3. Установка зависимостей
pip install -r requirements.txt

# 4. Настройка переменных окружения
cp .env.example .env
# Редактировать .env с реальными токенами
```

### **Configuration Structure**
```yaml
# config/base.yaml - базовая конфигурация
agents:
  task_analyzer:
    enabled: true
    schedule: "0 9 * * *"
  meeting_analyzer:
    enabled: true
    schedule: "0 10 * * *"
  weekly_reports:
    enabled: true
    schedule: "0 17 * * 5"

# config/development.yaml - dev настройки
# config/production.yaml - prod настройки
# config/employee_monitoring.yaml - текущая конфигурация
```

### **Environment Variables**
```bash
# .env файл (не в Git)
JIRA_BASE_URL=https://jira.mts.ru
JIRA_TOKEN=your_personal_token
CONFLUENCE_BASE_URL=https://confluence.mts.ru
CONFLUENCE_TOKEN=your_personal_token
OPENAI_API_KEY=your_openai_key
LOG_LEVEL=INFO
ENVIRONMENT=production
```

## ⚠️ Технические ограничения

### **API Limitations**
- **Jira API:** 1000 requests/hour per token
- **Confluence API:** 1000 requests/hour per token  
- **OpenAI API:** Rate limits по тарифному плану
- **Workers Memory:** 512MB limit в некоторых environments

### **File System Limitations**
- **Protocol Files:** Максимальный размер 50MB
- **Memory Store:** JSON файл до 100MB перед оптимизацией
- **Log Files:** Автоматическая ротация каждые 100MB

### **Network Constraints**
- **VPN Required:** Доступ к MTS сетям через VPN
- **Internal DNS:** jira.mts.ru, confluence.mts.ru
- **Firewall:** HTTPS-only коммуникации

## 📦 Зависимости и их влияние

### **Critical Dependencies**
1. **aiohttp** - Асинхронные HTTP запросы
   - *Почему:* Блокирующие запросы не работают в async среде
   - *Риск:* Connection pooling требует настройки

2. **pydantic** - Валидация данных
   - *Почему:* Type safety и automatic validation
   - *Риск:* Strict typing может ломать backward compatibility

3. **openai** - LLM интеграция
   - *Почему:* Core functionality для анализа
   - *Риск:* Rate limiting и costs

### **Optional Dependencies**
```python
# Для расширенной функциональности
matplotlib             # Графики в отчетах
seaborn                # Statistical visualization
plotly                 # Interactive charts
sentence-transformers  # Alternative embeddings
```

### **Development Dependencies**
```python
# Для разработки и тестирования
black                  # Code formatting
flake8                 # Linting
mypy                   # Type checking
pre-commit             # Git hooks
coverage               # Test coverage
```

## 🔍 Паттерны использования инструментов

### **LLM Integration Patterns**
```python
# Wrapper pattern для LLM провайдеров
class LLMClient:
    def __init__(self, provider: str, api_key: str):
        self.provider = provider
        self.api_key = api_key
    
    async def analyze(self, prompt: str) -> str:
        if self.provider == "openai":
            return await self._openai_analyze(prompt)
        elif self.provider == "yandex":
            return await self._yandex_analyze(prompt)

# Prompt engineering pattern
TASK_ANALYSIS_PROMPT = """
Проанализируй следующие задачи Jira:
{tasks}

Оцени по метрикам:
1. Completion rate (0-100%)
2. Productivity score (1-10)
3. Performance rating (1-10)

Формат ответа: JSON
"""
```

### **API Client Patterns**
```python
# Retry pattern с exponential backoff
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(ConnectionError)
)
async def get_jira_tasks(self, jql: str) -> List[JiraTask]:
    # API call logic

# Circuit breaker pattern
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5):
        self.failure_threshold = failure_threshold
        self.failure_count = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
```

### **Configuration Management Patterns**
```python
# Hierarchical configuration with overrides
@dataclass
class AgentConfig:
    enabled: bool = True
    schedule: str = ""
    timeout: int = 300
    retry_attempts: int = 3

def load_config(env: str = "development") -> Config:
    base_config = load_yaml("config/base.yaml")
    env_config = load_yaml(f"config/{env}.yaml")
    runtime_overrides = load_env_overrides()
    
    return merge_configs([base_config, env_config, runtime_overrides])
```

### **Error Handling Patterns**
```python
# Structured error handling
class EmployeeMonitoringError(Exception):
    def __init__(self, message: str, agent: str, context: Dict = None):
        self.message = message
        self.agent = agent
        self.context = context or {}
        super().__init__(f"{agent}: {message}")

# Logging pattern for debugging
logger = logging.getLogger(__name__)
logger.info(
    "Agent execution started",
    extra={
        "agent": "TaskAnalyzer",
        "execution_id": execution_id,
        "employee_count": len(employees),
        "timestamp": datetime.utcnow().isoformat()
    }
)
```

### **Testing Patterns**
```python
# Async testing pattern
@pytest.mark.asyncio
async def test_task_analyzer_success():
    # Arrange
    mock_jira_client = AsyncMock()
    mock_llm_client = AsyncMock()
    
    # Act
    analyzer = TaskAnalyzerAgent(
        jira_client=mock_jira_client,
        llm_client=mock_llm_client,
        config=test_config
    )
    result = await analyzer.analyze_tasks()
    
    # Assert
    assert result.success is True
    assert len(result.analyzed_employees) > 0

# Integration testing pattern
@pytest.mark.integration
async def test_full_workflow():
    # Test real API integration
    pass
```

## 🚀 Performance Considerations

### **Memory Management**
```python
# Context manager for memory cleanup
class MemoryAwareAgent:
    async def __aenter__(self):
        # Resource allocation
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Resource cleanup
        await self.cleanup()

# Generator pattern for large datasets
def process_large_dataset(data_stream):
    for batch in chunked(data_stream, size=1000):
        yield process_batch(batch)
```

### **Async Best Practices**
```python
# Proper async context management
async def analyze_with_timeout(agent: BaseAgent, data: Dict, timeout: int = 300):
    try:
        return await asyncio.wait_for(agent.analyze(data), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"Agent {agent.__class__.__name__} timed out")
        raise

# Concurrent execution with semaphore
async def run_concurrent_agents(agents: List[BaseAgent], max_concurrent: int = 5):
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def run_with_semaphore(agent):
        async with semaphore:
            return await agent.execute()
    
    return await asyncio.gather(*[run_with_semaphore(agent) for agent in agents])
```

## 📊 Monitoring и Observability

### **Logging Configuration**
```python
# Structured JSON logging
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": "logs/employee_monitoring.log",
            "maxBytes": 104857600,  # 100MB
            "backupCount": 5
        }
    }
}
```

### **Health Checks**
```python
# Health check endpoints
async def health_check():
    checks = {
        "jira_api": await check_jira_connection(),
        "confluence_api": await check_confluence_connection(),
        "llm_service": await check_llm_service(),
        "memory_store": await check_memory_store(),
        "disk_space": check_disk_space()
    }
    
    return {
        "status": "healthy" if all(checks.values()) else "unhealthy",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

*Этот технический контекст обеспечивает понимание всех участников проекта о технологическом стеке, ограничениях и паттернах использования инструментов*
