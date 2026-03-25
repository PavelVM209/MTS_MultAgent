# MTS_MultAgent - LLM-Driven Intelligence System

🚀 **Интеллектуальная многоагентная система** для автоматизации анализа корпоративных данных с **100% LLM-архитектурой** и **итеративным самоулучшением**.

## 🎯 Обзор

Система автоматически обрабатывает данные из Jira, Excel файлов и публикует результаты в Confluence через последовательность из **LLM-драйверенных агентов**:

1. **JiraAgent** - интеллектуальный сбор данных с LLM-улучшениями
2. **ContextAnalyzer** - 100% LLM-driven анализ контента
3. **ExcelAgent** - LLM-guided извлечение с реальными таблицами
4. **ComparisonAgent** - интеллектуальное сравнение с предиктивными инсайтами
5. **ConfluenceAgent** - публикация результатов

## ✨ Ключевые возможности

### 🧠 **Интеллектуальный анализ**
- ✅ **Zero hardcoded logic** - 100% интеллектуальные решения через LLM
- ✅ **Итеративное самоулучшение** до качества 85%+
- ✅ **Адаптивность к любому контексту** и структуре данных
- ✅ **Предиктивные инсайты** и рекомендации

### 📊 **Реальные результаты**
- ✅ **Реальные таблицы данных** из Excel (без фейковых отчетов)
- ✅ **Интеллектуальные выводы** через LLM интерпретацию
- ✅ **Семантический анализ** контекста и отношений
- ✅ **Quality metrics** с автоматической оценкой качества

### 🔄 **Автоматическое улучшение**
- ✅ **Convergence detection** - автоматическая стоп при достижении качества
- ✅ **Self-improvement loops** - итеративное совершенствование результатов
- ✅ **Multi-provider LLM support** - OpenAI, Local LLM, Mock
- ✅ **Intelligent caching** и performance optimization

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

# 🧠 LLM Configuration (NEW!)
OPENAI_API_KEY="your-openai-api-key"
OPENAI_MODEL="gpt-4-turbo-preview"
OPENAI_TEMPERATURE=0.1
OPENAI_MAX_TOKENS=4000

# 🔄 Iterative Improvement Configuration
MAX_ITERATIONS=5
QUALITY_THRESHOLD=85.0
CONVERGENCE_MIN_IMPROVEMENT=5.0

# 🚀 Performance & Caching
CACHE_ENABLED=true
CACHE_TTL=3600
MAX_CONCURRENT_LLM_REQUESTS=3

# 🔧 LLM Features Configuration
JIRA_ENABLE_LLM_ENHANCEMENTS=true
CONTEXT_MAX_ITERATIONS=5
EXCEL_QUALITY_THRESHOLD=85.0
COMPARISON_MAX_ITERATIONS=5
```

## 🧠 LLM Архитектура

### **Phase 1 & 2 Completion Status**: ✅ **100% ЗАВЕРШЕНЫ**

#### **🏗️ LLM Foundation (Phase 1)**
- ✅ **LLMClient** - Multi-provider поддержка (OpenAI, Local, Mock)
- ✅ **QualityMetrics** - Комплексная система оценки качества
- ✅ **IterativeEngine** - Движок итеративного улучшения
- ✅ **Enhanced Models** - LLM-ориентированные модели данных

#### **🤖 Agent Redesign (Phase 2)**
- ✅ **ContextAnalyzer** - 100% LLM-driven, zero hardcoded logic
- ✅ **ExcelAgent** - LLM-guided анализ с real table validation
- ✅ **ComparisonAgent** - Новый intelligent agent с predictive insights
- ✅ **JiraAgent** - LLM enhancements при сохранении стабильности

### **Ключевые достижения:**
- 🎯 **Zero Hardcoded Logic**: 100% интеллектуальные решения через LLM
- 📊 **Real Results**: Обязательные реальные таблицы данных
- 🔄 **Iterative Improvement**: Автоулучшение до 85%+ качества
- 🧠 **Semantic Intelligence**: Глубокое понимание контекста

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

## 🔄 Рабочий процесс (LLM-Enhanced)

1. **📥 Получение задачи** - Система получает описание задачи или проекта
2. **🧠 LL-Enhanced Сбор данных** - Интеллектуальный сбор из Jira и Excel
3. **🎯 Итеративный анализ** - LLM-driven анализ с автоулучшением до 85%+
4. **⚖️ Умное сравнение** - Сравнение с предиктивными инсайтами
5. **📊 Публикация** - Создание отчета с реальными таблицами и выводами

### **Ключевые преимущества нового workflow:**
- 🔄 **Self-Improving**: Каждый цикл улучшает качество результатов
- 🧠 **Context-Aware**: Понимание семантики и бизнес-контекста
- 📊 **Real Data**: Только реальные таблицы и конкретные данные
- ⚡ **Convergence**: Автоматическая остановка при достижении качества

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

## 🎉 **Результаты проекта**

### **✅ Phase 1 & 2 COMPLETION**

#### **🏗️ Phase 1: LLM Foundation (100% Complete)**
- ✅ **LLMClient** - Multi-provider поддержка (OpenAI, Local LLM, Mock)
- ✅ **QualityMetrics** - Comprehensive scoring (relevance, completeness, accuracy, clarity, actionability)
- ✅ **IterativeEngine** - Self-improvement с convergence detection
- ✅ **Enhanced Models** - LLM-oriented data structures

#### **🤖 Phase 2: Agent Redesign (100% Complete)**
- ✅ **ContextAnalyzer** - 100% LLM-driven, zero hardcoded logic eliminated
- ✅ **ExcelAgent** - LLM-guided с обязательной real table validation
- ✅ **ComparisonAgent** - Новый intelligent agent с predictive insights
- ✅ **JiraAgent** - LLM enhancements при сохранении стабильной основы

### **🚀 Ключевые достижения**

#### **Zero Hardcoded Logic Achievement:**
- ❌ **Eliminated**: ВСЕ hardcoded паттерны и маппинги
- ✅ **Achieved**: 100% интеллектуальные решения через LLM
- 🧠 **Result**: Адаптивность к любому контекту и структуре данных

#### **Real Results Guarantee:**
- 📊 **Real Tables**: Обязательные реальные таблицы данных из Excel
- 🧠 **Intelligent Insights**: LLM-generated анализ вместо общих фраз
- ⚖️ **Concrete Comparisons**: Specific comparison data с метриками
- 🎯 **Actionable Recommendations**: Практические рекомендации

#### **Iterative Intelligence:**
- 🔄 **Self-Improvement**: Автоматическое улучшение до 85%+ качества
- ⚡ **Convergence Detection**: Автоматическая остановка при достижении целей
- 📈 **Quality Metrics**: Relevance, Completeness, Accuracy, Clarity, Actionability
- 🎯 **Adaptive Thresholds**: Intelligent quality assessment

### **📊 Технические метрики**

#### **Architecture Metrics:**
- **4 агента** полностью переработаны под LLM-архитектуру
- **100% elimination** hardcoded логики
- **85%+ quality threshold** achieved через iterative improvement
- **Multi-provider LLM support** реализован
- **Real data validation** обязательна для всех результатов

#### **Performance Metrics:**
- **Convergence detection** оптимальное количество итераций
- **Caching system** для LLM запросов
- **Async processing** для высокой производительности
- **Error resilience** с fallback стратегиями

### **🎯 Business Value**

#### **Immediate Impact:**
- 📊 **Real Reports**: Только реальные данные и таблицы
- 🧠 **Intelligent Analysis**: Глубокое понимание бизнес-контекста
- ⚡ **Automated Insights**: Самостоятельное генерирование выводов
- 🔄 **Continuous Improvement**: Система учится и улучшается

#### **Long-term Value:**
- 🚀 **Scalability**: Работа с любыми Excel файлами и проектами
- 🧠 **Adaptability**: Понимание любого бизнес-контекста
- 🎯 **Reliability**: Стабильные результаты с гарантией качества
- 💡 **Innovation**: Foundation для будущих AI-функций

---

## Устранение проблем

### Частые проблемы

1. **Ошибка аутентификации**
   - Проверьте токены в `.env`
   - Убедитесь что токены имеют необходимые права

2. **Timeout ошиб
