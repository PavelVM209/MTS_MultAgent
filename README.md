# MTS_MultAgent

Многоагентная система для автоматизации анализа корпоративных данных и публикации отчетов в Confluence.

## Обзор

Система автоматически обрабатывает данные из Jira, Excel файлов и публикует результаты в Confluence через последовательность из 5 специализированных агентов:

1. **JiraAgent** - чтение задач и протоколов совещаний
2. **ContextAnalyzer** - анализ контента и поиск по ключевым фразам
3. **ExcelAgent** - извлечение данных из Excel файлов
4. **ComparisonAgent** - сравнительный анализ
5. **ConfluenceAgent** - публикация результатов

## Возможности

- ✅ Автоматический сбор данных из корпоративных систем
- ✅ Умный анализ контента с использованием NLP
- ✅ Формирование отчетов в визуальном формате
- ✅ Публикация в Confluence с таблицами и комментариями
- ✅ Сравнительный анализ данных из разных источников
- ✅ Асинхронная обработка для высокой производительности

## Требования

- Python 3.8+ (проверено на 3.8 и выше)
- Доступ к Jira API с персональным токеном
- Доступ к Confluence API с персональным токеном
- Excel файлы с данными для анализа

## Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/mts/MTS_MultAgent.git
cd MTS_MultAgent
```

### 2. Создание и активация виртуального окружения (ОБЯЗАТЕЛЬНО)

**⚠️ ВАЖНО: Всегда используйте виртуальное окружение для работы с проектом!**

#### Сначала проверьте вашу версию Python:
```bash
# Проверка доступных версий Python
python --version
python3 --version
which python
which python3
```

#### Создание виртуального окружения:
```bash
# Если доступен python как python (версия 3.8+)
python -m venv venv

# Если доступен только python3
python3 -m venv venv

# Если у вас несколько версий (например, python3.8, python3.9)
python3.8 -m venv venv
python3.9 -m venv venv
# Выберите доступную версию 3.8+

# Пример для вашей ситуации (Python 3.8):
/Library/Frameworks/Python.framework/Versions/3.8/bin/python3 -m venv venv
```

#### Активация окружения:
```bash
# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

#### Проверка активации:
```bash
# Должно появиться (venv) в начале строки
(venv) $ python --version
(venv) $ which python
# Должен показывать путь к venv/bin/python
```

### 3. Установка зависимостей

```bash
# Убедитесь что виртуальное окружение активно (видите (venv) в начале строки)
pip install -r requirements.txt

# Проверка установки
pip list | grep -E "(aiohttp|pydantic|click|structlog)"
```

### 4. Настройка конфигурации

```bash
cp .env.example .env
# Отредактируйте .env с вашими учетными данными
```

## Конфигурация

Заполните `.env` файл необходимыми переменными:

```bash
# Jira Configuration
# For Test Server:
JIRA_BASE_URL="https://test.jira-clst.mts.ru/rest/scriptrunner/latest/custom"
# For Production Server:
# JIRA_BASE_URL="https://jira.mts.ru/"
JIRA_ACCESS_TOKEN="your-jira-personal-token"
JIRA_USERNAME="your-email@company.com"

# Confluence Configuration
# For Test Server:
CONFLUENCE_BASE_URL="https://test.cnfl-clst.mts.ru/rest/scriptrunner/latest/custom"
# For Production Server:
# CONFLUENCE_BASE_URL="https://confluence.mts.ru/"
CONFLUENCE_ACCESS_TOKEN="your-confluence-personal-token"
CONFLUENCE_SPACE="PROJECTS"
ROOT_PAGE_ID_TO_ADD_NEW_PAGES=897438835

# Project Configuration
PROJECT_NAME="Stroki.Clone.S3.Integration.Api"

# Excel Configuration
EXCEL_FILE_PATH="data/excel/"
```

## Использование

### CLI интерфейс

#### Базовый анализ проекта

```bash
python -m src.cli.main --task "Проанализировать проект PROJECT_NAME"
```

#### Анализ с параметрами

```bash
python -m src.cli.main \
  --task "Анализ проекта по метрикам" \
  --project-key "PROJ" \
  --keywords ["metric", "performance", "deadline"] \
  --output-format "table"
```

#### Сводка совещаний

```bash
python -m src.cli.main \
  --task "Сводка совещаний за неделю" \
  --date-from "2024-01-01" \
  --date-to "2024-01-07"
```

### Программное использование

```python
import asyncio
from src.core.coordinator import Coordinator
from src.core.config import initialize_config

async def main():
    # Инициализация конфигурации
    config_manager = initialize_config()
    
    # Создание координатора
    coordinator = Coordinator(config_manager.config)
    
    # Выполнение анализа
    result = await coordinator.execute_workflow(
        "Проанализировать проект в ручном режиме",
        project_key="PROJECT",
        keywords=["deadline", "budget", "team"]
    )
    
    if result.success:
        print(f"Анализ завершен: {result.data['confluence_url']}")
    else:
        print(f"Ошибка: {result.error}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Архитектура

```
MTS_MultAgent/
├── src/
│   ├── agents/          # Реализация агентов
│   │   ├── jira_agent.py
│   │   ├── context_analyzer.py
│   │   ├── excel_agent.py
│   │   ├── confluence_agent.py
│   │   └── comparison_agent.py
│   ├── core/           # Основные компоненты
│   │   ├── base_agent.py
│   │   ├── config.py
│   │   ├── models.py
│   │   └── coordinator.py
│   ├── cli/            # CLI интерфейс
│   │   └── main.py
│   └── api/            # Web API (Phase 2)
│       └── main.py
├── tests/              # Тесты
├── config/             # Конфигурация
├── memory-bank/        # Банк памяти проекта
└── data/               # Данные (Excel файлы)
```

## Рабочий процесс

1. **Получение задачи** - Система получает описание задачи или проекта
2. **Сбор данных** - Автоматически собирает информацию из Jira и Excel
3. **Анализ** - Находит релевантный контекст и выделяет ключевые метрики
4. **Сравнение** - Выполняет сравнительный анализ данных
5. **Публикация** - Создает отчет в Confluence с таблицами и выводами

## Тестирование

```bash
# Запуск всех тестов
pytest

# Запуск с покрытием
pytest --cov=src

# Запуск конкретных тестов
pytest tests/test_jira_agent.py
pytest tests/test_coordinator.py
```

## Разработка

### Добавление нового агента

1. Создайте класс наследующий `BaseAgent`
2. Реализуйте методы `execute()` и `validate()`
3. Добавьте агент в координатор

```python
from src.core.base_agent import BaseAgent, AgentResult

class CustomAgent(BaseAgent):
    async def validate(self, task: Dict[str, Any]) -> bool:
        return "required_field" in task
    
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        # Ваша логика
        return AgentResult(
            success=True,
            data={"result": "custom_result"},
            agent_name=self.name
        )
```

### Форматирование кода

```bash
# Форматирование
black src/ tests/

# Проверка типов
mypy src/

# Линтинг
flake8 src/
```

## Структура банка памяти

Проект использует систему "банка памяти" для документации:

- `memory-bank/projectbrief.md` - Основной краткий проект
- `memory-bank/productContext.md` - Бизнес-контекст и проблемы
- `memory-bank/systemPatterns.md` - Архитектура и паттерны
- `memory-bank/techContext.md` - Технологический стек
- `memory-bank/agentsSpec.md` - Спецификация агентов
- `memory-bank/activeContext.md` - Текущий фокус работы
- `memory-bank/progress.md` - Отслеживание прогресса

## Веб-интерфейс (Phase 2)

На втором этапе будет доступен веб-интерфейс:

```bash
# Запуск веб-сервера
uvicorn src.api.main:app --reload --port 8000

# Доступ к интерфейсу
open http://localhost:8000
```

## Мониторинг и логирование

```bash
# Просмотр логов
tail -f logs/mts_agent.log

# Структурированные логи
python -c "
import structlog
logger = structlog.get_logger()
logger.info('Test message', project='demo', status='running')
"
```

## Устранение проблем

### Частые проблемы

1. **Ошибка аутентификации**
   - Проверьте токены в `.env`
   - Убедитесь что токены имеют необходимые права

2. **Timeout ошиб
