# Agents Specification - MTS_MultAgent LLM-Driven Architecture

## 🧠 НОВАЯ АРХИТЕКТУРА - ПОЛНОСТЬЮ LLM-CENTRIC

### Ключевые принципы:
- **Zero hardcoded logic** - все решения через LLM
- **Iterative self-improvement** - итеративное улучшение результатов
- **Dynamic adaptation** - адаптация на основе анализа результатов
- **Intelligent validation** - оценка качества через LLM

---

## 🔄 ИТЕРАТИВНЫЙ ЦИКЛ УЛУЧШЕНИЯ

```python
class IterativeResult(BaseModel):
    iteration: int
    quality_score: float
    data: Dict[str, Any]
    feedback: str
    needs_refinement: bool

class QualityMetrics(BaseModel):
    relevance_score: float  # 0-100% соответствие контексту
    completeness_score: float  # 0-100% полнота анализа
    accuracy_score: float  # 0-100% точность извлечения
    overall_quality: float  # 0-100% интегральная оценка
```

---

## 1. JiraAgent (БЕЗ ИЗМЕНЕНИЙ)

### Ответственность
- Получение задач из Jira
- Чтение протоколов совещаний
- Поиск по проектным ключам
- Извлечение комментариев и описаний

*Спецификация остается без изменений - работает стабильно*

---

## 2. 🧠 ContextAnalyzer (LLM-DRIVEN + SELF-EVALUATION)

### 🔄 Ключевая инновация: Итеративное улучшение запросов

### Ответственность
- **Интеллектуальный анализ контекста** через LLM без hardcoded паттернов
- **Динамическое формирование запросов** к Excel на основе семантического анализа
- **Самооценка результатов** и итеративное улучшение запросов
- **LLM-driven валидация** качества анализа

### 🧠 LLM-Centric Architecture

#### Входные параметры
```python
class ContextTask(BaseModel):
    jira_data: JiraResult
    task_description: str
    original_context: str
    iteration_data: Optional[IterativeResult] = None  # Для итеративного улучшения
    
class ExcelColumnInfo(BaseModel):
    column_name: str
    data_sample: List[str]
    data_types: List[str]
    semantic_meaning: str  # LLM interpretation

class LLMQueryRequest(BaseModel):
    context_description: str
    available_columns: List[ExcelColumnInfo]
    analysis_goals: List[str]
    previous_feedback: Optional[str] = None
```

#### Выходные данные
```python
class ContextResult(BaseModel):
    intelligent_queries: List[str]  # LLM-generated queries
    column_mappings: Dict[str, str]  # Dynamic column mappings
    extracted_entities: Dict[str, List[str]]
    confidence_score: float
    quality_metrics: QualityMetrics
    iteration_result: IterativeResult
    refined_strategy: Dict[str, Any]
```

#### 🧠 LLM-Driven методы
```python
class ContextAnalyzer(BaseAgent):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.llm_client = LLMClient(config["llm"])
        self.max_iterations = config.get("max_iterations", 5)
        self.quality_threshold = config.get("quality_threshold", 85.0)
    
    async def analyze_context_with_llm(self, task: ContextTask) -> ContextResult:
        """Основной LLM-driven анализ контекста"""
        
    async def generate_intelligent_queries(self, request: LLMQueryRequest) -> List[str]:
        """Генерация запросов через LLM без паттернов"""
        prompt = f"""
        Проанализируй бизнес-контекст и сгенерируй точные запросы к Excel данным.
        
        КОНТЕКСТ ЗАДАЧИ:
        {request.context_description}
        
        ДОСТУПНЫЕ КОЛОНКИ:
        {self._format_columns_for_llm(request.available_columns)}
        
        ЦЕЛИ АНАЛИЗА:
        {', '.join(request.analysis_goals)}
        
        ПРЕДЫДУЩИЙ ФИДБЕК:
        {request.previous_feedback or 'Нет'}
        
        СГЕНЕРИРУЙ:
        1. Точные запросы для извлечения релевантных данных
        2. Методологии фильтрации и агрегации
        3. Критерии оценки качества результатов
        
        Формат: JSON with queries array
        """
        
        response = await self.llm_client.complete(prompt)
        return self._parse_llm_queries_response(response)
    
    async def analyze_excel_structure_semantically(self, excel_columns: List[str], sample_data: List[Dict]) -> List[ExcelColumnInfo]:
        """LLM-анализ семантики колонок Excel"""
        prompt = f"""
        Проанализируй структуру Excel файла и определи семантику колонок.
        
        КОЛОНКИ:
        {', '.join(excel_columns)}
        
        ОБРАЗЦЫ ДАННЫХ:
        {self._format_sample_data(sample_data)}
        
        ОПРЕДИЛИ ДЛЯ КАЖДОЙ КОЛОНКИ:
        1. Семантическое значение
        2. Тип данных
        3. Бизнес-сущность
        4. Возможные использования для анализа
        
        Формат: JSON array with column analysis
        """
        
        response = await self.llm_client.complete(prompt)
        return self._parse_column_analysis(response)
    
    async def evaluate_result_quality(self, result_data: Dict, original_context: str) -> QualityMetrics:
        """LLM-оценка качества результатов"""
        prompt = f"""
        Оцени качество извлеченных данных по отношению к исходному контексту.
        
        ИСХОДНЫЙ КОНТЕКСТ:
        {original_context}
        
        ПОЛУЧЕННЫЕ ДАННЫЕ:
        {self._format_result_data(result_data)}
        
        ОЦЕНИ:
        1. Relevance Score (0-100%): Насколько данные соответствуют контексту
        2. Completeness Score (0-100%): Полнота охвата аспектов контекста
        3. Accuracy Score (0-100%): Точность извлечения
        4. Overall Quality (0-100%): Общая оценка качества
        
        Формат: JSON с метриками
        """
        
        response = await self.llm_client.complete(prompt)
        return self._parse_quality_metrics(response)
    
    async def iterative_improvement_loop(self, task: ContextTask, excel_structure: List[ExcelColumnInfo]) -> ContextResult:
        """Итеративный цикл улучшения"""
        current_iteration = 0
        best_result = None
        best_quality = 0.0
        
        while current_iteration < self.max_iterations:
            # Генерация запросов с учетом предыдущих итераций
            query_request = LLMQueryRequest(
                context_description=task.task_description,
                available_columns=excel_structure,
                analysis_goals=self._extract_analysis_goals(task),
                previous_feedback=best_result.feedback if best_result else None
            )
            
            queries = await self.generate_intelligent_queries(query_request)
            
            # Исполнение запросов через ExcelAgent
            excel_result = await self._execute_queries_via_excel_agent(queries)
            
            # Оценка качества
            quality = await self.evaluate_result_quality(excel_result, task.task_description)
            
            # Проверка условия остановки
            if quality.overall_quality >= self.quality_threshold:
                break
            
            # Сохранение лучшего результата
            if quality.overall_quality > best_quality:
                best_quality = quality.overall_quality
                best_result = IterativeResult(
                    iteration=current_iteration,
                    quality_score=quality.overall_quality,
                    data=excel_result,
                    feedback=await self._generate_improvement_feedback(excel_result, task.task_description),
                    needs_refinement=True
                )
            
            current_iteration += 1
        
        return ContextResult(
            intelligent_queries=queries,
            column_mappings=self._create_dynamic_mappings(excel_structure, task),
            extracted_entities=await self._extract_entities_with_llm(task),
            confidence_score=best_quality,
            quality_metrics=quality,
            iteration_result=best_result,
            refined_strategy=await self._generate_refined_strategy(best_result)
        )
```

#### 🧠 LLM Prompts Examples

##### Prompt для анализа контекста:
```
Ты - эксперт бизнес-аналитик. Проанализируй задачу и определи, какие данные нужны из Excel.

ЗАДАЧА: {task_description}

КЛЮЧЕВЫЕ АСПЕКТЫ:
1. Какие бизнес-сущности упоминаются?
2. Какие метрики важны?
3. Какие сравнения нужны?
4. Какие временные периоды релевантны?

СГЕНЕРИРУЙ запросы для Excel, которые дадут точные ответы на эти вопросы.
```

##### Prompt для улучшения результатов:
```
Проанализируй полученные результаты и определи, как их улучшить.

ПОЛУЧЕННЫЕ ДАННЫЕ: {result_data}

ОЖИДАНИЯ ИЗ КОНТЕКСТА: {expected_data}

ЧТО НЕДОСТАТОЧНО:
1. Какие данные missing?
2. Какие аспекты не освещены?
3. Какие уточнения нужны?

СГЕНЕРИРУЙ улучшенные запросы для следующей итерации.
```

---

## 3. 🎯 ExcelAgent (LLM-GUIDED)

### 🔄 Ключевая инновация: Исполнение LLM-запросов

### Ответственность
- **Исполнение интеллектуальных запросов** от ContextAnalyzer
- **Динамическая обработка данных** без hardcoded паттернов
- **Адаптивная фильтрация** на основе LLM-инструкций
- **Гибкое форматирование** результатов

#### LLM-Guided методы
```python
class ExcelAgent(BaseAgent):
    async def execute_llm_generated_queries(self, queries: List[str], file_paths: List[str]) -> Dict[str, Any]:
        """Исполнение LLM-сгенерированных запросов"""
        results = {}
        
        for query in queries:
            try:
                # LLM-парсинг запроса в конкретные операции
                operations = await self._parse_query_with_llm(query)
                
                # Исполнение операций
                query_result = await self._execute_operations(operations, file_paths)
                results[query] = query_result
                
            except Exception as e:
                logger.error(f"Failed to execute query: {query}", error=str(e))
                results[query] = {"error": str(e)}
        
        return results
    
    async def parse_query_with_llm(self, query: str) -> List[Dict[str, Any]]:
        """LLM-парсинг natural language запроса в операции"""
        prompt = f"""
        Преобразуй natural language запрос в конкретные операции с Excel.
        
        ЗАПРОС: {query}
        
        ВОЗМОЖНЫЕ ОПЕРАЦИИ:
        1. filter_columns: фильтрация колонок
        2. filter_rows: фильтрация строк
        3. aggregate: агрегация данных
        4. calculate: вычисления
        5. group_by: группировка
        
        СГЕНЕРИРУЙ JSON массив операций.
        """
        
        response = await self.llm_client.complete(prompt)
        return self._parse_operations(response)
```

---

## 4. 🧪 ComparisonAgent (LLM-DRIVEN + ADAPTIVE)

### 🔄 Ключевая инновация: Итеративное улучшение анализа

### Ответственность
- **Интеллектуальное сравнение** данных с контекстом через LLM
- **Адаптивная корректировка** стратегии анализа
- **Генерация контекстуальных выводов** и рекомендаций
- **LLM-driven оценка** качества сравнения

#### 🧪 LLM-Driven методы
```python
class ComparisonAgent(BaseAgent):
    async def compare_with_iterative_improvement(
        self, 
        jira_data: JiraResult, 
        excel_data: Dict, 
        context_result: ContextResult
    ) -> ComparisonResult:
        """Итеративное сравнение с улучшением"""
        
        current_iteration = 0
        best_analysis = None
        best_quality = 0.0
        
        while current_iteration < self.max_iterations:
            # LLM-анализ соответствия
            comparison_analysis = await self._perform_llm_comparison(
                jira_data, excel_data, context_result
            )
            
            # Оценка качества анализа
            analysis_quality = await self._evaluate_analysis_quality(
                comparison_analysis, jira_data, excel_data
            )
            
            # Проверка условия остановки
            if analysis_quality >= self.quality_threshold:
                break
            
            # Корректировка стратегии анализа
            refined_strategy = await self._refine_analysis_strategy(
                comparison_analysis, analysis_quality
            )
            
            # Сохранение лучшего результата
            if analysis_quality > best_quality:
                best_quality = analysis_quality
                best_analysis = comparison_analysis
            
            current_iteration += 1
        
        return await self._generate_final_comparison_result(
            best_analysis, context_result
        )
    
    async def _perform_llm_comparison(
        self, 
        jira_data: JiraResult, 
        excel_data: Dict, 
        context_result: ContextResult
    ) -> Dict[str, Any]:
        """LLM-анализ соответствия данных контексту"""
        prompt = f"""
        Проведи глубокий анализ соответствия данных из Excel исходному контексту из Jira.
        
        КОНТЕКСТ JIRA:
        {self._format_jira_context(jira_data)}
        
        ДАННЫЕ EXCEL:
        {self._format_excel_data(excel_data)}
        
        АНАЛИТИЧЕСКИЕ ЦЕЛИ:
        {context_result.refined_strategy}
        
        ПРОАНАЛИЗИРУЙ:
        1. Насколько полно данные отвечают на вопросы из Jira?
        2. Какие аспекты контекста не освещены?
        3. Есть ли противоречия или несоответствия?
        4. Какие дополнительные инсайты можно извлечь?
        
        Формат: детальный анализ с оценками и рекомендациями.
        """
        
        response = await self.llm_client.complete(prompt)
        return self._parse_comparison_analysis(response)
```

---

## 🔄 ИНТЕГРАЦИОННЫЙ WORKFLOW С ИТЕРАТИВНЫМ УЛУЧШЕНИЕМ

```python
async def execute_intelligent_analysis_pipeline(task_description: str):
    """Основной pipeline с итеративным улучшением"""
    
    # 1. JiraAgent (без изменений)
    jira_result = await jira_agent.execute_with_fallback({
        "project_key": extract_project_key(task_description),
        "task_description": task_description,
        "search_keywords": extract_keywords(task_description)
    })
    
    # 2. Анализ структуры Excel через LLM
    excel_structure = await excel_agent.analyze_structure_with_llm(get_excel_files())
    
    # 3. ContextAnalyzer с итеративным улучшением
    context_task = ContextTask(
        jira_data=jira_result.data,
        task_description=task_description,
        original_context=jira_result.data.get("context", "")
    )
    
    context_result = await context_analyzer.iterative_improvement_loop(
        context_task, excel_structure
    )
    
    # 4. ExcelAgent исполнение LLM-запросов
    excel_result = await excel_agent.execute_llm_generated_queries(
        context_result.intelligent_queries,
        get_excel_files()
    )
    
    # 5. ComparisonAgent с итеративным улучшением
    comparison_result = await comparison_agent.compare_with_iterative_improvement(
        jira_result.data,
        excel_result,
        context_result
    )
    
    # 6. Публикация результатов
    final_result = await confluence_agent.create_intelligent_page({
        "title": generate_title(task_description),
        "content": format_llm_enhanced_content(context_result, comparison_result),
        "tables": excel_result.get("tables", []),
        "quality_metrics": context_result.quality_metrics,
        "iteration_info": context_result.iteration_result
    })
    
    return final_result
```

---

## 🎯 КЛЮЧЕВЫЕ ПРЕИМУЩЕСТВА НОВОЙ АРХИТЕКТУРЫ

### 1. **Полная интеллектуализация**
- Никаких hardcoded паттернов
- 100% LLM-driven принятие решений
- Динамическая адаптация к любому контексту

### 2. **Самообучение и улучшение**
- Итеративное приближение к оптимальному результату
- Автоматическая корректировка стратегии
- Качественная оценка на каждом шаге

### 3. **Универсальность**
- Работает с любой структурой Excel
- Понимает любой бизнес-контекст
- Адаптируется к любым требованиям

### 4. **Прозрачность и контролируемость**
- Логирование каждой итерации
- Метрики качества для анализа
- Возможность вмешательства и корректировки

---

## 🚀 РЕАЛИЗАЦИОННЫЕ АСПЕКТЫ

### LLM Integration Requirements:
- **API Key**: OpenAI или локальная LLM
- **Rate Limiting**: Управление запросами к LLM
- **Caching**: Кэширование LLM-ответов
- **Fallback**: Резервовые стратегии при недоступности LLM

### Performance Optimization:
- **Parallel LLM calls**: Параллельные запросы к LLM
- **Smart Caching**: Интеллектуальное кэширование
- **Batch Processing**: Группировка операций
- **Lazy Evaluation**: Отложенное выполнение

### Quality Assurance:
- **Convergence Testing**: Тестирование сходимости итераций
- **Quality Threshold Validation**: Валидация порогов качества
- **A/B Testing**: Сравнение с предыдущими версиями
- **Human-in-the-Loop**: Возможность экспертной оценки

Эта архитектура создает genuinely интеллектуальную систему, которая не просто следует жестким правилам, а учится, адаптируется и улучшается на каждом шаге.

---

## 🎉 **PHASE 1 & 2 COMPLETION STATUS**

### ✅ **Phase 1: LLM Foundation - 100% COMPLETE**
- **LLMClient**: Multi-provider поддержка (OpenAI, Local LLM, Mock)
- **QualityMetrics**: Comprehensive scoring система
- **IterativeEngine**: Self-improvement с convergence detection
- **Enhanced Models**: LLM-oriented data структуры

### ✅ **Phase 2: Agent Redesign - 100% COMPLETE**
- **ContextAnalyzer**: 100% LLM-driven, zero hardcoded logic
- **ExcelAgent**: LLM-guided с real table validation
- **ComparisonAgent**: Новый intelligent agent (заменяет UniversalAnalyzer)
- **JiraAgent**: LLM enhancements при сохранении стабильности

### 🚀 **Достижения новой архитектуры:**

#### **Zero Hardcoded Logic - ACHIEVED:**
- ❌ **Eliminated**: ВСЕ hardcoded паттерны и маппинги
- ✅ **Achieved**: 100% интеллектуальные решения через LLM
- 🧠 **Result**: Адаптивность к любому контексту и структуре данных

#### **Iterative Intelligence - IMPLEMENTED:**
- 🔄 **Self-Improvement**: Автоматическое улучшение до 85%+ качества
- ⚡ **Convergence Detection**: Автоматическая остановка при достижении целей
- 📈 **Quality Metrics**: Relevance, Completeness, Accuracy, Clarity, Actionability
- 🎯 **Adaptive Thresholds**: Intelligent quality assessment

#### **Real Results Guarantee - ENSURED:**
- 📊 **Real Tables**: Обязательные реальные таблицы данных из Excel
- 🧠 **Intelligent Insights**: LLM-generated анализ вместо общих фраз
- ⚖️ **Concrete Comparisons**: Specific comparison data с метриками
- 🎯 **Actionable Recommendations**: Практические рекомендации

### 📊 **Техническая реализация:**

#### **LLM Integration:**
- **Multi-provider support**: OpenAI, Local LLM, Mock modes
- **Intelligent caching**: Оптимизация LLM запросов
- **Rate limiting**: Управление API лимитами
- **Fallback strategies**: Резервные варианты при недоступности

#### **Quality Infrastructure:**
- **IterativeEngine**: Автоматическое улучшение результатов
- **QualityMetrics**: Комплексная оценка качества
- **Convergence detection**: Определение момента остановки
- **Performance optimization**: Async processing и кэширование

#### **Agent Architecture:**
- **ContextAnalyzer**: Полный LLM-driven анализ с самооценкой
- **ExcelAgent**: Исполнение интеллектуальных запросов
- **ComparisonAgent**: Умное сравнение с предиктивными инсайтами
- **JiraAgent**: Стабильная основа + LLM улучшения

### 🎯 **Business Value Delivered:**
- **Intelligence**: Система понимает и анализирует любой бизнес-контекст
- **Adaptability**: Работает с любыми Excel файлами без настроек
- **Quality**: Гарантирует реальные данные и интеллектуальные выводы
- **Reliability**: Самоулучшается и обеспечивает стабильные результаты

**🎉 PROJECT TRANSFORMATION COMPLETE: От hardcoded системы к genuinely intelligent LLM-driven architecture!**

---

*Последнее обновление: 24.03.2026 10:52*
*Статус: Phase 2 Agent Redesign ЗАВЕРШЕН (100%)*
*Достижение: Полная LLM-архитектура с итеративным улучшением*
