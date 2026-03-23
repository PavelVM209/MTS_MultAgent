# Tech Context - MTS_MultAgent

## Технологический стек

### Основные технологии
- **Python 3.8+**: Основной язык разработки (проверено на 3.8 и выше)
- **asyncio**: Асинхронное программирование
- **aiohttp**: HTTP клиент для API запросов
- **pandas**: Обработка данных
- **openpyxl**: Работа с Excel файлами
- **click**: CLI интерфейс
- **python-dotenv**: Управление переменными окружения
- **pydantic**: Валидация данных
- **FastAPI**: Веб-интерфейс (второй этап)

### Зависимости для разработки
- **pytest**: Тестирование
- **black**: Форматирование кода
- **mypy**: Статическая типизация
- **pre-commit**: Git hooks

## Настройка разработки

### Требования к окружению
```bash
# Проверка доступных версий Python
python --version
python3 --version
which python
which python3
# Требуется Python 3.8+

# Виртуальное окружение (ОБЯЗАТЕЛЬНО)
# Выберите подходящую команду для вашей системы:

# Если доступен python как python (версия 3.8+)
python -m venv venv

# Если доступен только python3
python3 -m venv venv

# Если у вас несколько версий Python
python3.8 -m venv venv  # Для Python 3.8
python3.9 -m venv venv  # Для Python 3.9
python3.10 -m venv venv # Для Python 3.10

# Для конкретного пути (как в вашем примере с macOS)
/Library/Frameworks/Python.framework/Versions/3.8/bin/python3 -m venv venv

# Активация
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Проверка активации - должно появиться (venv) в начале строки
(venv) $ python --version
(venv) $ which python  # Должен показывать путь к venv/bin/python
```

### ⚠️ ВАЖНО: Обязательное использование виртуального окружения

**Почему это критически важно:**
- Изоляция зависимостей проекта от системных
- Предотвращение конфликтов версий
- Гарантия воспроизводимости окружения
- Безопасность системного Python

**Проверка активации:**
```bash
# Должно быть видно (venv) в начале строки
(venv) $ python --version
(venv) $ which python
# /path/to/project/venv/bin/python

# Если активации нет, повторите:
source venv/bin/activate
```

### Установка зависимостей
```bash
pip install -r requirements.txt
```

### Структура requirements.txt
```
# Core dependencies
aiohttp>=3.8.0
pandas>=1.5.0
openpyxl>=3.0.0
click>=8.0.0
python-dotenv>=0.19.0
pydantic>=1.10.0

# Web interface (Phase 2)
fastapi>=0.85.0
uvicorn>=0.18.0

# Development
pytest>=7.0.0
pytest-asyncio>=0.20.0
black>=22.0.0
mypy>=0.991
pre-commit>=2.20.0
```

## Конфигурация

### Переменные окружения
```bash
# Jira Configuration
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

# Excel Configuration
EXCEL_FILE_PATH="path/to/excel/files"
EXCEL_SHEET_NAME="Sheet1"

# Logging
LOG_LEVEL="INFO"
LOG_FILE="logs/mts_agent.log"
```

### Файл .env.example
```bash
# Copy this to .env and fill with your values
cp .env.example .env
```

## API интеграции

### Jira API
- **Test Server**: `https://test.jira-clst.mts.ru/rest/scriptrunner/latest/custom`
- **Production Server**: `https://jira.mts.ru/`
- **Endpoint**: `/rest/api/3/search`
- **Authentication**: Basic Auth + Token
- **Rate Limit**: 1000 requests/hour
- **Timeout**: 30 seconds

```python
# Пример запроса
headers = {
    "Authorization": f"Basic {base64_token}",
    "Content-Type": "application/json"
}

# Test URL
JIRA_TEST_URL = "https://test.jira-clst.mts.ru/rest/scriptrunner/latest/custom"
# Production URL  
JIRA_PROD_URL = "https://jira.mts.ru/"
```

### Confluence API
- **Test Server**: `https://test.cnfl-clst.mts.ru/rest/scriptrunner/latest/custom`
- **Production Server**: `https://confluence.mts.ru/`
- **Endpoint**: `/rest/api/content`
- **Authentication**: Basic Auth + Token
- **Rate Limit**: 1000 requests/hour
- **Timeout**: 30 seconds

```python
# Пример создания страницы
payload = {
    "type": "page",
    "title": "Analysis Report",
    "space": {"key": "SPACE"},
    "body": {"storage": {"value": content, "representation": "storage"}}
}

# Test URL
CONFLUENCE_TEST_URL = "https://test.cnfl-clst.mts.ru/rest/scriptrunner/latest/custom"
# Production URL
CONFLUENCE_PROD_URL = "https://confluence.mts.ru/"
```

## Архитектурные ограничения

### Производительность
- **Максимальный размер Excel файла**: 100MB
- **Количество concurrent запросов**: 10
- **Memory limit**: 1GB per process
- **Timeout для API**: 30 секунд

### Безопасность
- **Токены**: Хранятся только в переменных окружения
- **HTTPS**: Обязательное использование
- **No hardcoded credentials**: Запрет на хранение в коде
- **Sanitization**: Очистка входных данных

### Доступность
- **Python 3.8+**: Минимальная версия (проверено на 3.8 и выше)
- **Linux/Mac/Windows**: Кроссплатформенность
- **Docker**: Контейнеризация опционально

## Паттерны использования инструментов

### Виртуальное окружение
```bash
# Активация перед работой
source venv/bin/activate

# Деактивация после работы
deactivate
```

### Запуск приложения
```bash
# CLI режим
python -m src.cli.main --task "project analysis"

# Web режим (Phase 2)
uvicorn src.api.main:app --reload --port 8000
```

### Тестирование
```bash
# Все тесты
pytest

# С覆盖率
pytest --cov=src

# Асинхронные тесты
pytest -k "async" --asyncio-mode=auto
```

### Логирование
```python
# Структурированное логирование
import structlog
logger = structlog.get_logger()

logger.info("Agent execution started", 
           agent="JiraAgent", 
           task_id="123",
           project="MyProject")
```

## Мониторинг и отладка

### Логи
- **Уровень**: INFO по умолчанию
- **Формат**: JSON structured logs
- **Rotation**: Ежедневная ротация
- **Местоположение**: `logs/`

### Метрики
- **Performance**: Время выполнения агентов
- **Success Rate**: Успешность операций
- **Error Tracking**: Мониторинг ошибок
- **Resource Usage**: Память и CPU

### Отладка
```bash
# Включение debug режима
export LOG_LEVEL=DEBUG
python -m src.cli.main --debug --task "test"

# Profiling
python -m cProfile -o profile.stats src/cli/main.py
```

## Развертывание

### Локальное развертывание
```bash
# Клонирование и настройка
git clone <repo>
cd MTS_MultAgent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
```

### Docker развертывание (опционально)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "src.cli.main"]
