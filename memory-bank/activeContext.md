# Active Context - MTS_MultAgent

## Текущий фокус работы

**Дата**: 23.03.2026
**Статус**: Реализация агентов и CLI интерфейса
**Следующий этап**: Создание JiraAgent и базовой CLI

### Что делаем сейчас
- ✅ Создана структура проекта с основными директориями
- ✅ Создан банк памяти со спецификацией проекта
- ✅ Настроена конфигурация и переменные окружения
- ✅ Реализован базовый класс BaseAgent
- 🔄 Реализуем JiraAgent - первый специализированный агент
- ⏭️ Создаем CLI интерфейс
- ⏭️ Реализуем остальные агенты

### Последние изменения
1. **Инфраструктура**: Полностью готова к разработке
2. **BaseAgent**: Базовый класс с обработкой ошибок и валидацией
3. **Config**: Продвинутая система конфигурации с Pydantic
4. **План**: Определены следующие шаги реализации

## Активные решения

### Текущие задачи
1. **JiraAgent**: Интеграция с Jira API для получения задач и протоколов ✅
2. **CLI Interface**: Командная строка с основными командами ✅
3. **ContextAnalyzer**: Анализ текстового контента
4. **ExcelAgent**: Работа с Excel файлами
5. **ConfluenceAgent**: Публикация результатов

### Приоритеты
1. **High Priority**: JiraAgent + CLI (MVP для демонстрации) ✅
2. **Medium Priority**: ContextAnalyzer + ExcelAgent
3. **Low Priority**: ConfluenceAgent + ComparisonAgent

## 🚨 КРИТИЧЕСКИ ВАЖНО: Виртуальное окружение

### Обязательное требование для работы с проектом
**ВСЕГДА используйте виртуальное окружение при работе с MTS_MultAgent!**

```bash
# Создание (если еще не создано)
python -m venv venv

# Активация ОБЯЗАТЕЛЬНА перед любой работой
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Проверка активации - должно быть (venv) в начале строки
(venv) $ python --version
```

### Почему это критически важно
- 🔒 **Изоляция**: Предотвращает конфликты с системными пакетами
- 🛡️ **Безопасность**: Защищает системный Python
- 🔄 **Воспроизводимость**: Гарантирует одинаковое окружение
- 📦 **Зависимости**: Изолирует пакеты проекта

### Проверка перед работой
```bash
# Всегда проверяйте активацию
echo $VIRTUAL_ENV  # Должен показывать путь к venv
which python      # Должен показывать путь к venv/bin/python
```

## Следующие шаги (немедленные)

### 1. JiraAgent Реализация
```python
# Создать src/agents/jira_agent.py
class JiraAgent(BaseAgent):
    async def search_issues(self, project_key, keywords)
    async def get_meeting_protocols(self, project_key)
    async def extract_comments(self, issue_id)
```

### 2. CLI Interface
```python
# Создать src/cli/main.py
@click.command()
@click.option('--task', required=True)
@click.option('--project-key')
async def analyze(task, project_key)
```

### 3. Models и Types
```python
# Создать src/core/models.py
class JiraTask(BaseModel)
class JiraResult(BaseModel)
class ContextTask(BaseModel)
```

## Технические детали для реализации

### Jira API Интеграция
- **Endpoint**: `/rest/api/3/search`
- **Authentication**: Basic Auth + Token
- **JQL Queries**: Динамическое построение запросов
- **Rate Limiting**: Обработка ограничений

### CLI Команды
```bash
# Базовая команда
python -m src.cli.main --task "анализ проекта"

# С параметрами
python -m src.cli.main \
  --task "анализ проекта" \
  --project-key "PROJ" \
  --keywords ["deadline", "budget"]

# Датафильтры
python -m src.cli.main \
  --task "сводка совещаний" \
  --date-from "2024-01-01" \
  --date-to "2024-01-07"
```

## Проблемы для решения

### Технические вызовы
1. **Authentication**: Корректная обработка токенов Jira
2. **Rate Limiting**: Предотвращение превышения лимитов
3. **Error Handling**: Graceful degradation при ошибках API
4. **Data Parsing**: Обработка различных форматов ответов

### Архитектурные решения
1. **Async Context**: Правильное использование async/await
2. **Configuration**: Интеграция с существующей конфигурацией
3. **Logging**: Структурированное логирование операций
4. **Testing**: Подготовка к юнит-тестам

## Критерии успеха

### JiraAgent
- ✅ Подключение к Jira API
- ✅ Поиск задач по ключевым словам
- ✅ Получение протоколов совещаний
- ✅ Обработка ошибок API

### CLI Interface
- ✅ Базовая команда работает
- ✅ Опциональные параметры
- ✅ Валидация входных данных
- ✅ Читаемый вывод результатов

### Интеграция
- ✅ JiraAgent интегрируется с BaseAgent
- ✅ CLI вызывает JiraAgent корректно
- ✅ Конфигурация используется
- ✅ Логирование работает

## Прогресс реализации

### Текущий статус: 35% complete
- ✅ Architecture & Planning: 100%
- ✅ Core Infrastructure: 100%
- 🔄 Agent Implementation: 20% (BaseAgent готов)
- ⏳ CLI Interface: 0%
- ⏳ Testing: 0%

### Ближайшие цели
1. **Завершить JiraAgent** к концу дня
2. **Создать базовый CLI** завтра
3. **Тестирование интеграции** послезавтра

## Ресурсы и зависимости

### Внешние API
- **Jira API Documentation**: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
- **Authentication**: Personal Access Tokens
- **Rate Limits**: 1000 requests/hour per token

### Библиотеки
- **aiohttp**: HTTP клиент
- **pydantic**: Валидация данных
- **click**: CLI framework
- **structlog**: Логирование

## Мониторинг и отладка

### Логирование
```python
logger.info("Jira API request", 
           endpoint="/rest/api/3/search",
           project_key=project_key,
           keywords=keywords)
```

### Метрики
- **Request Count**: Количество запросов к API
- **Response Time**: Время ответа
- **Success Rate**: Процент успешных запросов
- **Error Types**: Типы ошибок

## Риски и митигация

### Технические риски
1. **API Changes**: Jira может изменить API
   - *Митигация*: Version pinning, fallback strategies
2. **Authentication Issues**: Проблемы с токенами
   - *Митигация*: Clear error messages, token validation
3. **Performance**: Медленные ответы API
   - *Митигация*: Async requests, timeouts

### Бизнес риски
1. **User Adoption**: Сложность использования
   - *Mитигация*: Simple CLI, good documentation
2. **Data Privacy**: Уязвимые данные
   - *Mитигация*: Data sanitization, secure storage

---
*Последнее обновление: 23.03.2026 14:05*
*Статус: Implementing JiraAgent*
*Следующий шаг: Create src/agents/jira_agent.py*
