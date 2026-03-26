# Employee Monitoring System - Technical Specification

## 🎯 **System Overview**

**MTS MultAgent Employee Monitoring System** - автоматизированная система мониторинга и аналитики производительности сотрудников с использованием LLM для интеллектуального анализа данных.

---

## 🏗️ **System Architecture**

### **Core Agent System**
```
🤖 AgentOrchestrator (Quality Control + Coordination)
    ⏰ Daily Schedule (configurable)
    ├── 📋 TaskAnalyzerAgent (09:00 daily)
    │   ├── 🎯 Анализ задач из Jira projects
    │   ├── 📊 Прогресс по каждому сотруднику
    │   ├── 💾 Сохранение отчета в директорию
    │   └── 🧠 LLM анализ и суммаризация
    │
    └── 📝 MeetingAnalyzerAgent (18:00 daily)
        ├── 🎯 Анализ протоколов собраний
        ├── 📊 Определение прогресса сотрудников
        ├── 💾 Сохранение отчета в директорию
        └── 🧠 LLM анализ активности
        
    🔍 QualityValidatorAgent (after each report)
        ├── 📊 Оценка качества (90% threshold)
        ├── 🔄 Отправка на доработку если нужно
        └── ✅ Утверждение отчетов
        
    ⏰ Weekly Schedule (Friday 17:00)
    └── 📈 WeeklyReportsAgent
        ├── 🎯 Комплексный анализ за неделю
        ├── 📊 Метрики: задачи, коммиты, активность
        ├── 🚀 Публикация в Confluence space
        └── 🧠 LLM генерация выводов и рекомендаций
        ↓
💾 Memory Store (состояние сотрудников) + File System (отчеты)
```

---

## 📋 **Agent Specifications**

### **1. TaskAnalyzerAgent**

**Purpose:** Ежедневный анализ задач из Jira и определение прогресса сотрудников

**Schedule:** Каждый день в `config.employee_monitoring.scheduler.daily_analysis_time`

**Core Functions:**
```python
class TaskAnalyzerAgent(BaseAgent):
    async def execute(self) -> AgentResult:
        # 1. Получение задач из Jira projects
        jira_tasks = await self.fetch_jira_tasks(
            project_keys=config.employee_monitoring.jira.project_keys,
            query_filter=config.employee_monitoring.jira.query_filter
        )
        
        # 2. Группировка задач по сотрудникам
        employee_tasks = self.group_tasks_by_assignee(jira_tasks)
        
        # 3. Анализ прогресса по каждому сотруднику
        employee_progress = {}
        for employee, tasks in employee_tasks.items():
            progress = await self.analyze_employee_progress(tasks)
            employee_progress[employee] = progress
        
        # 4. LLM анализ и суммаризация
        analyzed_data = await self.llm_analyze_progress(employee_progress)
        
        # 5. Сохранение отчета
        await self.save_daily_report(analyzed_data, config.employee_monitoring.reports.daily_reports_dir)
        
        # 6. Обновление состояния в Memory Store
        await self.update_memory_store(employee_progress)
        
        return AgentResult(success=True, data=analyzed_data)
```

**Data Structure:**
```python
EmployeeProgress = {
    "employee_name": str,
    "tasks_total": int,
    "tasks_in_progress": int,
    "tasks_completed": int,
    "tasks_new": int,
    "completion_rate": float,
    "active_projects": List[str],
    "key_achievements": List[str],
    "bottlenecks": List[str],
    "llm_insights": str
}
```

### **2. MeetingAnalyzerAgent**

**Purpose:** Ежедневный анализ протоколов собраний и определение активности сотрудников

**Schedule:** Каждый день в `config.employee_monitoring.scheduler.daily_analysis_time`

**Core Functions:**
```python
class MeetingAnalyzerAgent(BaseAgent):
    async def execute(self) -> AgentResult:
        # 1. Чтение протоколов из директории
        protocol_files = await self.scan_protocols_directory(
            config.employee_monitoring.protocols.directory_path
        )
        
        # 2. Парсинг протоколов (TXT/PDF/DOCX)
        parsed_protocols = []
        for file_path in protocol_files:
            content = await self.parse_protocol_file(file_path)
            parsed_protocols.append({"file": file_path, "content": content})
        
        # 3. Извлечение упоминаний сотрудников
        employee_mentions = await self.extract_employee_mentions(parsed_protocols)
        
        # 4. Анализ вклада и активности
        employee_activity = {}
        for employee, mentions in employee_mentions.items():
            activity = await self.analyze_employee_activity(mentions)
            employee_activity[employee] = activity
        
        # 5. LLM анализ протоколов
        analyzed_data = await self.llm_analyze_meetings(employee_activity)
        
        # 6. Сохранение отчета
        await self.save_daily_report(analyzed_data, config.employee_monitoring.reports.daily_reports_dir)
        
        return AgentResult(success=True, data=analyzed_data)
```

**Data Structure:**
```python
EmployeeActivity = {
    "employee_name": str,
    "meeting_participations": int,
    "speaking_turns": int,
    "action_items_assigned": int,
    "action_items_completed": int,
    "topics_initiated": int,
    "decisions_influenced": int,
    "engagement_score": float,
    "leadership_indicators": List[str],
    "llm_insights": str
}
```

### **3. WeeklyReportsAgent**

**Purpose:** Еженедельный комплексный анализ с публикацией в Confluence

**Schedule:** Пятница в `config.employee_monitoring.scheduler.weekly_report_time`

**Core Functions:**
```python
class WeeklyReportsAgent(BaseAgent):
    async def execute(self) -> AgentResult:
        # 1. Агрегация данных за неделю из Memory Store
        weekly_data = await self.aggregate_weekly_data()
        
        # 2. Получение данных из Git репозиториев
        git_data = await self.fetch_git_metrics()
        
        # 3. Комплексный анализ по сотрудникам
        employee_analytics = {}
        for employee in weekly_data['employees']:
            analytics = await self.generate_comprehensive_analysis(
                employee,
                weekly_data['tasks'][employee],
                weekly_data['meetings'][employee],
                git_data.get(employee, {})
            )
            employee_analytics[employee] = analytics
        
        # 4. LLM генерация отчета с выводами и комментариями
        weekly_report = await self.llm_generate_weekly_report(employee_analytics)
        
        # 5. Публикация в Confluence
        confluence_page = await self.publish_to_confluence(
            weekly_report,
            config.employee_monitoring.confluence.weekly_reports_space
        )
        
        return AgentResult(success=True, data={"confluence_url": confluence_page})
```

**Report Structure:**
```markdown
# Еженедельный отчет по команде - [Дата]

## 📊 Сводные метрики команды
- Общее количество задач: X
- Выполнено задач: Y
- Средняя производительность: Z%
- Количество коммитов: N

## 👥 Анализ по сотрудникам

### [Имя сотрудника]
**📋 Задачи:**
- Всего задач: X
- В работе: Y  
- Выполнено: Z
- Завершенность: N%

**💬 Активность в встречах:**
- Участий: X
- Выступлений: Y
- Action items: Z
- Engagement score: N%

**🔧 Техническая активность:**
- Коммиты: X
- Pull requests: Y
- Code reviews: Z

**🎯 Ключевые достижения:**
- [Список достижений]

**🔍 зоны улучшения:**
- [Список рекомендаций]

## 📈 Общие выводы и рекомендации
[LLM сгенерированные инсайты]
```

### **4. QualityValidatorAgent**

**Purpose:** LLM-проверка качества отчетов с возможностью доработки

**Trigger:** После каждого сгенерированного отчета

**Core Functions:**
```python
class QualityValidatorAgent(BaseAgent):
    async def validate_report(self, report: Dict) -> ValidationResult:
        # 1. Проверка полноты данных
        completeness = await self.check_completeness(report)
        
        # 2. Проверка логической связности
        coherence = await self.check_coherence(report)
        
        # 3. Проверка соответствия стандартам
        standards_compliance = await self.check_standards(report)
        
        # 4. LLM оценка качества
        llm_quality_score = await self.llm_evaluate_quality(report)
        
        # 5. Расчет общего качества
        overall_quality = self.calculate_overall_quality(
            completeness, coherence, standards_compliance, llm_quality_score
        )
        
        # 6. Проверка порога качества
        threshold = config.employee_monitoring.quality.threshold
        if overall_quality >= threshold:
            return ValidationResult(approved=True, score=overall_quality)
        else:
            # 7. Генерация рекомендаций по доработке
            improvement_suggestions = await self.llm_generate_improvements(report)
            return ValidationResult(
                approved=False, 
                score=overall_quality,
                suggestions=improvement_suggestions
            )
```

---

## ⚙️ **Configuration System**

### **Configuration Structure**
```yaml
# config/base.yaml
employee_monitoring:
  jira:
    project_keys: "ROOBY,0BF,DEV"
    query_filter: "status in (In Progress, Done, To Do) AND updated >= -7d"
    fields: ["assignee", "status", "summary", "description", "created", "updated"]
    
  protocols:
    directory_path: "/data/meeting-protocols"
    file_formats: ["txt", "pdf", "docx"]
    scan_subdirectories: true
    
  reports:
    daily_reports_dir: "./reports/daily"
    weekly_reports_dir: "./reports/weekly"
    report_format: "json"
    
  confluence:
    weekly_reports_space: "TEAM"
    parent_page_id: "123456"
    template_name: "weekly-report-template"
    
  scheduler:
    daily_analysis_time: "09:00"
    weekly_report_time: "17:00"
    weekly_report_day: "friday"
    timezone: "Europe/Moscow"
    
  quality:
    threshold: 0.9
    max_retries: 3
    validation_timeout: 300
    
  git:
    repositories: [
        "https://github.com/company/repo1.git",
        "https://github.com/company/repo2.git"
    ]
    commit_analysis_days: 7
    
  employees:
    tracking_enabled: true
    excluded_users: ["bot", "system"]
    department_mapping:
      "ROOBY": "CloudBilling"
      "0BF": "B2B"
```

### **Environment Variables**
```bash
# .env
# Employee Monitoring Configuration
JIRA_PROJECT_KEYS="ROOBY,0BF,DEV"
PROTOCOLS_DIRECTORY_PATH="/data/meeting-protocols"
DAILY_REPORTS_DIR="./reports/daily"
WEEKLY_REPORTS_SPACE="TEAM"
DAILY_ANALYSIS_TIME="09:00"
WEEKLY_REPORT_TIME="17:00"
QUALITY_THRESHOLD="0.9"
```

---

## 🗄️ **Data Storage & Management**

### **Memory Store Schema**
```python
# Employee State Tracking
EmployeeState = {
    "employee_id": str,
    "name": str,
    "department": str,
    "last_updated": datetime,
    "daily_metrics": {
        "YYYY-MM-DD": {
            "tasks": EmployeeProgress,
            "meetings": EmployeeActivity,
            "git_metrics": GitMetrics
        }
    },
    "weekly_metrics": {
        "YYYY-WW": WeeklyMetrics
    },
    "trends": {
        "task_completion_rate": List[float],
        "meeting_engagement": List[float],
        "productivity_score": List[float]
    }
}
```

### **File System Structure**
```
reports/
├── daily/
│   ├── 2026-03-26/
│   │   ├── task-analysis_2026-03-26.json
│   │   └── meeting-analysis_2026-03-26.json
│   └── 2026-03-27/
├── weekly/
│   ├── 2026-W12/
│   │   └── weekly-report_2026-W12.html
│   └── 2026-W13/
└── quality/
    ├── validation_2026-03-26.json
    └── improvement_suggestions_2026-03-26.json
```

---

## 🔧 **Implementation Details**

### **LLM Integration**
```python
# OpenAI GPT-4 Integration for analysis
class LLMEmployeeAnalyzer:
    def __init__(self):
        self.client = OpenAI(api_key=config.llm.api_key)
        self.model = config.llm.model  # gpt-4
    
    async def analyze_employee_performance(self, employee_data: Dict) -> str:
        prompt = f"""
        Проанализируй производительность сотрудника на основе следующих данных:
        
        Задачи: {employee_data.get('tasks', {})}
        Активность на встречах: {employee_data.get('meetings', {})}
        Техническая активность: {employee_data.get('git_metrics', {})}
        
        Определи:
        1. Ключевые достижения за период
        2. Потенциальные проблемы или бутылочные горлышки
        3. Рекомендации по улучшению производительности
        4. Общую оценку производительности (шкала 1-10)
        
        Ответ в структурированном формате.
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        return response.choices[0].message.content
```

### **Quality Control Loop**
```python
async def quality_control_workflow(report: Dict, agent: BaseAgent) -> Dict:
    validator = QualityValidatorAgent()
    
    for attempt in range(config.employee_monitoring.quality.max_retries + 1):
        validation = await validator.validate_report(report)
        
        if validation.approved:
            return report
        
        if attempt < config.employee_monitoring.quality.max_retries:
            # Send for revision
            print(f"Report quality {validation.score:.2f} < threshold. Improving...")
            report = await agent.improve_report(report, validation.suggestions)
        else:
            # Max retries reached, log and use as-is
            logger.warning(f"Max retries reached for report quality improvement")
            break
    
    return report
```

---

## 📊 **Success Metrics & KPIs**

### **System Performance Metrics**
- **API Response Time:** <2s for Jira, <1s for Confluence
- **Report Generation Time:** <5 minutes for daily, <15 minutes for weekly
- **Quality Score:** >=90% for all reports
- **System Uptime:** >99.5%
- **Error Rate:** <1%

### **Business Value Metrics**
- **Employee Coverage:** 100% of tracked employees
- **Data Completeness:** >95% complete reports
- **Insight Quality:** Actionable recommendations in >80% of reports
- **Time Savings:** >10 hours/week manual analysis time
- **Decision Support:** Data available for management decisions

---

## 🚀 **Implementation Roadmap**

### **Phase 1: Foundation (Week 1)**
- [ ] Update configuration system with employee monitoring parameters
- [ ] Adapt DailyJiraAnalyzer → TaskAnalyzerAgent
- [ ] Adapt DailyMeetingAnalyzer → MeetingAnalyzerAgent
- [ ] Setup basic Memory Store schema

### **Phase 2: Advanced Features (Week 2)**
- [ ] Create WeeklyReportsAgent with Confluence integration
- [ ] Implement QualityValidatorAgent
- [ ] Add Git repository integration
- [ ] Setup file system for reports storage

### **Phase 3: Integration & Testing (Week 3)**
- [ ] Enhance AgentOrchestrator for new workflow
- [ ] Implement scheduler configuration
- [ ] Test end-to-end workflow
- [ ] Performance optimization and monitoring

### **Phase 4: Production Deployment (Week 4)**
- [ ] Production configuration setup
- [ ] User training and documentation
- [ ] Go-live and monitoring
- [ ] Feedback collection and improvements

---

## 🛠️ **Development Guidelines**

### **Code Standards**
- **Type Hints:** Required for all functions
- **Async/Await:** All I/O operations must be async
- **Error Handling:** Comprehensive try-catch with logging
- **Testing:** 95%+ coverage required
- **Documentation:** All public methods must have docstrings

### **Security Considerations**
- **PII Protection:** Employee personal information must be protected
- **Access Control:** Role-based access to reports
- **Audit Logging:** All access to employee data logged
- **Data Retention:** Configurable retention policies
- **Encryption:** Sensitive data encrypted at rest

---

*Last Updated: 2026-03-26*  
*Status: Ready for Implementation*  
*Next Phase: Development Start*
