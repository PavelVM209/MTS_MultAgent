# Agents Specification - MTS_MultAgent

## Общая структура агентов

### Базовый интерфейс
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel

class AgentResult(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float

class BaseAgent(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        """Основной метод выполнения задачи"""
        pass
    
    @abstractmethod
    async def validate(self, task: Dict[str, Any]) -> bool:
        """Валидация входных данных"""
        pass
    
    async def execute_with_fallback(self, task: Dict[str, Any]) -> AgentResult:
        """Выполнение с обработкой ошибок"""
        try:
            if not await self.validate(task):
                return AgentResult(
                    success=False,
                    error=f"Validation failed for {self.name}"
                )
            
            start_time = time.time()
            result = await self.execute(task)
            result.execution_time = time.time() - start_time
            
            return result
        except Exception as e:
            return AgentResult(
                success=False,
                error=f"{self.name} error: {str(e)}",
                execution_time=0.0
            )
```

## 1. JiraAgent

### Ответственность
- Получение задач из Jira
- Чтение протоколов совещаний
- Поиск по проектным ключам
- Извлечение комментариев и описаний

### Входные параметры
```python
class JiraTask(BaseModel):
    project_key: str  # "PROJ"
    task_description: str
    search_keywords: List[str]
    date_range: Optional[Dict[str, str]] = None
    jql_query: Optional[str] = None
```

### Выходные данные
```python
class JiraResult(BaseModel):
    issues: List[Dict[str, Any]]
    meeting_protocols: List[Dict[str, Any]]
    comments: List[Dict[str, Any]]
    total_count: int
    extracted_context: str
```

### Основные методы
```python
class JiraAgent(BaseAgent):
    async def search_issues(self, project_key: str, keywords: List[str]) -> List[Dict]:
        """Поиск задач по ключевым словам"""
        
    async def get_meeting_protocols(self, project_key: str) -> List[Dict]:
        """Получение протоколов совещаний"""
        
    async def extract_comments(self, issue_id: str) -> List[Dict]:
        """Извлечение комментариев к задаче"""
        
    async def build_jql_query(self, task: JiraTask) -> str:
        """Построение JQL запроса"""
```

### API интеграция
- **Test Server**: `https://test.jira-clst.mts.ru/rest/scriptrunner/latest/custom`
- **Production Server**: `https://jira.mts.ru/`
- **Endpoint**: `/rest/api/3/search`
- **Authentication**: Basic Auth + Token
- **Query parameters**: `jql`, `fields`, `expand`
- **Rate limiting**: 1000 requests/hour

### Обработка ошибок
- **Network issues**: Retry exponential backoff
- **Authentication errors**: Immediate failure
- **Rate limiting**: Automatic retry with delay
- **Invalid JQL**: Validation before request

## 2. ContextAnalyzer

### Ответственность
- Анализ текстового контента
- Поиск по ключевым фразам
- Извлечение релевантной информации
- Формирование контекста для Excel запросов

### Входные параметры
```python
class ContextTask(BaseModel):
    jira_data: JiraResult
    task_description: str
    search_patterns: List[str]
    entities_to_extract: List[str]
```

### Выходные данные
```python
class ContextResult(BaseModel):
    relevant_context: str
    extracted_entities: Dict[str, List[str]]
    search_queries_for_excel: List[str]
    confidence_score: float
    summary: str
```

### Алгоритмы анализа
```python
class ContextAnalyzer(BaseAgent):
    async def extract_key_phrases(self, text: str) -> List[str]:
        """Извлечение ключевых фраз с NLP"""
        
    async def find_project_references(self, text: str, patterns: List[str]) -> List[str]:
        """Поиск упоминаний проектов"""
        
    async def build_excel_queries(self, context: str) -> List[str]:
        """Формирование запросов для Excel"""
        
    async def calculate_relevance_score(self, text: str, keywords: List[str]) -> float:
        """Расчет релевантности"""
```

### Технологии
- **NLP**: spaCy или NLTK для обработки текста
- **Pattern matching**: Регулярные выражения
- **Scoring**: TF-IDF или косинусное сходство
- **Entity extraction**: Распознавание сущностей

## 3. ExcelAgent

### Ответственность
- Чтение Excel файлов
- Поиск данных по запросам
- Извлечение таблиц и данных
- Форматирование результатов

### Входные параметры
```python
class ExcelTask(BaseModel):
    file_paths: List[str]
    search_queries: List[str]
    sheet_names: Optional[List[str]] = None
    data_types: List[str] = ["numeric", "text", "date"]
```

### Выходные данные
```python
class ExcelResult(BaseModel):
    extracted_tables: List[Dict[str, Any]]
    matched_data: List[Dict[str, Any]]
    summary_statistics: Dict[str, Any]
    file_metadata: List[Dict[str, str]]
```

### Основные методы
```python
class ExcelAgent(BaseAgent):
    async def read_excel_file(self, file_path: str, sheet_name: str) -> pd.DataFrame:
        """Чтение Excel файла"""
        
    async def search_in_data(self, df: pd.DataFrame, queries: List[str]) -> List[Dict]:
        """Поиск данных в DataFrame"""
        
    async def extract_tables(self, df: pd.DataFrame) -> List[Dict]:
        """Извлечение структурированных таблиц"""
        
    async def format_for_confluence(self, data: List[Dict]) -> str:
        """Форматирование для Confluence"""
```

### Производительность
- **Memory management**: Chunked reading for large files
- **Caching**: Cache results for repeated queries
- **Parallel processing**: Async file operations
- **Data validation**: Type checking and validation

## 4. ConfluenceAgent

### Ответственность
- Создание страниц в Confluence
- Форматирование контента
- Публикация таблиц
- Добавление комментариев

### Входные параметры
```python
class ConfluenceTask(BaseModel):
    space_key: str
    parent_page_id: int
    title: str
    content: str
    tables: List[Dict[str, Any]]
    comments: List[str]
```

### Выходные данные
```python
class ConfluenceResult(BaseModel):
    page_id: str
    page_url: str
    success: bool
    created_at: str
    version: int
```

### API интеграция
- **Test Server**: `https://test.cnfl-clst.mts.ru/rest/scriptrunner/latest/custom`
- **Production Server**: `https://confluence.mts.ru/`
- **Endpoint**: `/rest/api/content`
- **Authentication**: Basic Auth + Token
- **Rate limiting**: 1000 requests/hour

### API методы
```python
class ConfluenceAgent(BaseAgent):
    async def create_page(self, task: ConfluenceTask) -> ConfluenceResult:
        """Создание новой страницы"""
        
    async def format_table(self, data: List[Dict]) -> str:
        """Форматирование таблицы в Confluence format"""
        
    async def add_comment(self, page_id: str, comment: str) -> bool:
        """Добавление комментария к странице"""
        
    async def get_parent_page(self, page_id: int) -> Dict:
        """Получение информации о родительской странице"""
```

### Confluence разметка
```html
<!-- Таблица в Confluence format -->
<table>
  <tr><th>Header 1</th><th>Header 2</th></tr>
  <tr><td>Data 1</td><td>Data 2</td></tr>
</table>

<!-- Форматированный текст -->
<h2>Анализ проекта</h2>
<p>Описание анализа...</p>
<ac:structured-macro ac:name="code">
  <ac:parameter ac:name="language">python</ac:parameter>
  <ac:plain-text-body><![CDATA[code here]]></ac:plain-text-body>
</ac:structured-macro>
```

## 5. ComparisonAgent

### Ответственность
- Сравнительный анализ данных
- Выявление расхождений
- Формирование выводов
- Генерация рекомендаций

### Входные параметры
```python
class ComparisonTask(BaseModel):
    jira_data: JiraResult
    excel_data: ExcelResult
    context_data: ContextResult
    comparison_criteria: List[str]
```

### Выходные данные
```python
class ComparisonResult(BaseModel):
    comparisons: List[Dict[str, Any]]
    discrepancies: List[Dict[str, Any]]
    insights: List[str]
    recommendations: List[str]
    confidence_scores: Dict[str, float]
    summary_report: str
```

### Алгоритмы сравнения
```python
class ComparisonAgent(BaseAgent):
    async def compare_numeric_data(self, jira_values: List[float], excel_values: List[float]) -> Dict:
        """Сравнение числовых данных"""
        
    async def find_text_discrepancies(self, text1: str, text2: str) -> List[str]:
        """Поиск текстовых расхождений"""
        
    async def validate_dates_consistency(self, jira_dates: List[str], excel_dates: List[str]) -> bool:
        """Проверка консистентности дат"""
        
    async def generate_insights(self, comparison_data: Dict) -> List[str]:
        """Генерация инсайтов на основе сравнения"""
        
    async def create_summary_report(self, all_comparisons: Dict) -> str:
        """Создание сводного отчета"""
```

### Метрики сравнения
- **Точность**: Percentage of matching data
- **Полнота**: Coverage of expected data points
- **Согласованность**: Consistency across sources
- **Актуальность**: Recency of data

## Взаимодействие агентов

### Sequential Workflow
```python
async def execute_analysis_pipeline(task_description: str):
    # 1. JiraAgent
    jira_result = await jira_agent.execute_with_fallback({
        "project_key": extract_project_key(task_description),
        "task_description": task_description,
        "search_keywords": extract_keywords(task_description)
    })
    
    # 2. ContextAnalyzer
    context_result = await context_analyzer.execute_with_fallback({
        "jira_data": jira_result.data,
        "task_description": task_description,
        "search_patterns": get_project_patterns(),
        "entities_to_extract": get_target_entities()
    })
    
    # 3. ExcelAgent
    excel_result = await excel_agent.execute_with_fallback({
        "file_paths": get_excel_files(),
        "search_queries": context_result.data["search_queries_for_excel"]
    })
    
    # 4. ComparisonAgent
    comparison_result = await comparison_agent.execute_with_fallback({
        "jira_data": jira_result.data,
        "excel_data": excel_result.data,
        "context_data": context_result.data,
        "comparison_criteria": get_comparison_criteria()
    })
    
    # 5. ConfluenceAgent
    final_result = await confluence_agent.execute_with_fallback({
        "space_key": os.getenv("CONFLUENCE_SPACE"),
        "parent_page_id": int(os.getenv("ROOT_PAGE_ID_TO_ADD_NEW_PAGES")),
        "title": generate_title(task_description),
        "content": format_content(context_result, comparison_result),
        "tables": excel_result.data["extracted_tables"],
        "comments": comparison_result.data["recommendations"]
    })
    
    return final_result
```

### Error Handling Across Agents
- **Cascading failures**: Остановка при критической ошибке
- **Partial success**: Продолжение с доступными данными
- **Retry logic**: Повторные попытки для временных ошибок
- **Fallback strategies**: Альтернативные методы выполнения

### Performance Optimization
- **Parallel execution**: Независимые агенты могут работать параллельно
- **Caching**: Кэширование результатов между запусками
- **Batch processing**: Группировка запросов
- **Resource pooling**: Переиспользование соединений и сессий

## Тестирование агентов

### Unit Tests
```python
@pytest.mark.asyncio
async def test_jira_agent_search():
    agent = JiraAgent(test_config)
    result = await agent.execute_with_fallback({
        "project_key": "TEST",
        "task_description": "test task",
        "search_keywords": ["test"]
    })
    assert result.success == True
    assert "issues" in result.data

@pytest.mark.asyncio
async def test_context_analyzer():
    agent = ContextAnalyzer(test_config)
    result = await agent.execute_with_fallback({
        "jira_data": mock_jira_result,
        "task_description": "test",
        "search_patterns": ["pattern1"],
        "entities_to_extract": ["project", "date"]
    })
    assert result.success == True
    assert len(result.data["search_queries_for_excel"]) > 0
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_full_pipeline():
    coordinator = Coordinator(config)
    result = await coordinator.execute_workflow("Test project analysis")
    assert result.success == True
    assert "confluence_url" in result.data
```

## Мониторинг и логирование

### Метрики для каждого агента
- **Execution time**: Время выполнения
- **Success rate**: Процент успешных операций
- **Error types**: Типы ошибок
- **Data volume**: Объем обработанных данных

### Логирование событий
```python
logger.info("Agent execution started", 
           agent="JiraAgent",
           task_id=task["id"],
           project_key=task["project_key"])

logger.error("Agent execution failed",
             agent="ExcelAgent",
             error=str(e),
             file_path=task["file_paths"][0])
```
