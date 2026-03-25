# Agent Specifications - MTS MultAgent Scheduled Architecture

## 🤖 **Phase 3 Scheduled Agent System**

**Status:** Architecture Complete, Implementation In Progress  
**Total Agents:** 5 (4 specialized + 1 orchestrator)  
**Execution Model:** Scheduled workflows with JSON persistence  

---

## 🏗️ **ARCHITECTURE OVERVIEW**

### **Agent Hierarchy:**
```
🤖 OrchestratorAgent (Master Coordinator)
    ├── 📊 DailyJiraAnalyzer (Project & Task Analysis)
    ├── 📄 DailyMeetingAnalyzer (Protocol & Meeting Analysis)  
    ├── 📋 DailySummaryAgent (Data Consolidation)
    └── 📈 WeeklyReporter (Analytics & Confluence)
```

### **Execution Schedule:**
- **Daily 19:00 UTC+3:** Parallel: DailyJiraAnalyzer + DailyMeetingAnalyzer
- **Daily 19:30 UTC+3:** Sequential: DailySummaryAgent + Quality Check
- **Friday 19:00 UTC+3:** WeeklyReporter + Confluence Publication

---

## 🤖 **DETAILED AGENT SPECIFICATIONS**

### **1. 📊 DailyJiraAnalyzer**

**Purpose:** Ежедневный анализ задач Jira с отслеживанием прогресса сотрудников  

**Execution:** Daily at 19:00 UTC+3  
**Input Sources:** Jira API (multiple projects)  
**Output:** JSON memory store + structured data  

#### **Core Responsibilities:**
```python
class DailyJiraAnalyzer(BaseAgent):
    """
    Анализ Jira проектов с фокусом на employee analytics
    """
    
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        # 1. Multi-project data collection
        # 2. Employee task assignment tracking
        # 3. Status change monitoring
        # 4. Git commit integration
        # 5. JSON memory store updates
        pass
    
    async def analyze_multiple_projects(self, project_keys: List[str]) -> JSON:
        """Анализ нескольких Jira проектов"""
        pass
    
    async def track_employee_metrics(self, tasks: List[JiraTask]) -> JSON:
        """Отслеживание метрик по сотрудникам"""
        pass
    
    async def integrate_git_commits(self, employees: Dict) -> JSON:
        """Интеграция данных из Git для employee analytics"""
        pass
```

#### **Data Structure:**
```json
{
  "date": "2026-03-25",
  "timestamp": "2026-03-25T19:00:00",
  "projects": {
    "CSI": {
      "total_tasks": 45,
      "completed_tasks": 12,
      "in_progress_tasks": 25,
      "blocked_tasks": 8,
      "employees": {
        "ivanov": {
          "username": "ivanov",
          "full_name": "Иванов Иван",
          "email": "ivanov@company.com",
          "tasks": {
            "total": 15,
            "completed": 5,
            "in_progress": 8,
            "blocked": 2,
            "task_list": [
              {
                "key": "CSI-123",
                "summary": "API разработка",
                "status": "In Progress",
                "assignee": "ivanov",
                "updated": "2026-03-25T14:30:00"
              }
            ]
          },
          "metrics": {
            "completion_rate": 33.3,
            "avg_task_duration": 5.2,
            "status_changes_today": 3,
            "git_commits_today": 2
          }
        }
      }
    }
  },
  "system_metrics": {
    "jira_api_calls": 25,
    "processing_time_seconds": 45,
    "quality_score": 92.5
  }
}
```

#### **Configuration:**
```yaml
daily_jira_analyzer:
  project_keys: ["CSI", "PROJ", "DEV"]
  employee_identification: ["jira_username", "email", "full_name"]
  tracked_metrics: ["tasks", "status_changes", "git_commits", "deadlines"]
  git_integration_enabled: true
  historical_analysis_days: 30
```

---

### **2. 📄 DailyMeetingAnalyzer**

**Purpose:** Ежедневный анализ протоколов совещаний для employee analytics  

**Execution:** Daily at 19:00 UTC+3 (parallel with JiraAnalyzer)  
**Input Sources:** File system (txt, docx, pdf)  
**Output:** JSON memory store + meeting analytics  

#### **Core Responsibilities:**
```python
class DailyMeetingAnalyzer(BaseAgent):
    """
    Анализ протоколов совещаний с фокусом на employee participation
    """
    
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        # 1. Multi-format file parsing
        # 2. Employee action extraction
        # 3. Meeting participation tracking
        # 4. Decision and commitment tracking
        # 5. JSON memory store updates
        pass
    
    async def parse_multiple_formats(self, files: List[Path]) -> JSON:
        """Парсинг файлов txt, docx, pdf"""
        pass
    
    async def extract_employee_actions(self, protocols: List) -> JSON:
        """Извлечение действий сотрудников"""
        pass
```

#### **Data Structure:**
```json
{
  "date": "2026-03-25",
  "processed_files": [
    "/data/meetings/daily_standup_2026-03-25.txt"
  ],
  "meetings": [
    {
      "meeting_type": "daily_standup",
      "date": "2026-03-25",
      "participants": [
        {
          "name": "Иванов Иван",
          "role": "Lead разработчик",
          "participation": {
            "spoke_minutes": 5,
            "action_items": 2,
            "decisions_made": 1
          }
        }
      ],
      "employee_actions": [
        {
          "employee": "Иванов Иван",
          "action": "Завершить API разработку",
          "deadline": "2026-03-26",
          "priority": "high"
        }
      ]
    }
  ],
  "daily_employee_summary": {
    "ivanov": {
      "meetings_attended": 2,
      "action_items_assigned": 3,
      "action_items_completed": 1,
      "participation_score": 8.5
    }
  }
}
```

#### **Configuration:**
```yaml
daily_meeting_analyzer:
  protocols_path: "/data/meetings"
  supported_formats: ["txt", "docx", "pdf"]
  employee_identification: ["full_name", "email", "role"]
  extract_actions: true
  track_participation: true
  deadline_extraction: true
```

---

### **3. 📋 DailySummaryAgent**

**Purpose:** Консолидация данных за день и генерация human-readable отчетов  

**Execution:** Daily at 19:30 UTC+3  
**Input Sources:** JSON memory store (both analyzers)  
**Output:** Human TXT reports + JSON consolidation  

#### **Core Responsibilities:**
```python
class DailySummaryAgent(BaseAgent):
    """
    Консолидация данных и генерация human-readable отчетов
    """
    
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        # 1. Load JSON data from memory store
        # 2. Consolidate employee metrics
        # 3. Generate human-readable TXT report
        # 4. Update JSON memory store
        # 5. Save TXT reports for humans
        pass
    
    async def consolidate_employee_data(self, jira_data: JSON, meeting_data: JSON) -> JSON:
        """Консолидация данных по сотрудникам"""
        pass
    
    async def generate_human_report(self, consolidated_data: JSON) -> str:
        """Генерация human-readable TXT отчета"""
        pass
```

#### **Data Structure:**
```json
{
  "date": "2026-03-25",
  "consolidation_timestamp": "2026-03-25T19:30:00",
  "employee_summary": {
    "ivanov": {
      "full_name": "Иванов Иван",
      "daily_metrics": {
        "tasks_total": 15,
        "tasks_completed": 5,
        "tasks_in_progress": 8,
        "status_changes": 3,
        "git_commits": 2,
        "meetings_attended": 2,
        "action_items_assigned": 3,
        "action_items_completed": 1
      },
      "performance_score": 8.2,
      "trend_analysis": "stable_improvement"
    }
  },
  "project_summary": {
    "CSI": {
      "total_employees": 4,
      "tasks_completed_today": 12,
      "avg_performance_score": 8.0,
      "blocked_items": 2
    }
  },
  "system_health": {
    "data_quality_score": 94.5,
    "missing_data_flags": [],
    "anomaly_detections": []
  }
}
```

#### **Human TXT Report Format:**
```txt
# ЕЖЕДНЕВНЫЙ ОТЧЕТ ПО ПРОЕКТАМ И СОТРУДНИКАМ
============================================
Дата: 25.03.2026

## 📊 СВОДКА ПО ПРОЕКТАМ

### CSI CloudStorageIntegration
- Всего задач: 45
- Выполнено сегодня: 12
- В работе: 25
- Заблокировано: 8
- Средний performance score: 8.0

## 👥 АНАЛИТИКА ПО СОТРУДНИКАМ

### Иванов Иванов (Lead разработчик)
**Daily Performance Score: 8.2** 📈

📋 Задачи:
- Всего: 15 | Завершено: 5 | В работе: 8
- Статус изменений за день: 3
- Git коммиты: 2

🤝 Совещания:
- Посещено: 2 из 2
- Action items: назначено 3, выполнено 1

## 🔍 КЛЮЧЕВЫЕ НАБЛЮДЕНИЯ

1. **Высокая активность** у Иванова - 8.2 performance score
2. **Блокирующие задачи** требуют внимания (2Critical items)
3. **Git активность** коррелирует с выполнением задач

## ⚠️ ТРЕБУЕТ ВНИМАНИЯ

- **Петров Пётр**: Низкое выполнение action items (0/2)
- **CSI-156**: Заблокирована 3 дня, нужен escalation

---
*Сгенерировано: 2026-03-25 19:30*
*Источник: Jira + Meeting Protocols*
```

---

### **4. 📈 WeeklyReporter**

**Purpose:** Комплексный недельный анализ с публикацией в Confluence  

**Execution:** Friday 19:00 UTC+3  
**Input Sources:** JSON memory store (7 days)  
**Output:** Confluence pages + TXT reports + analytics  

#### **Core Responsibilities:**
```python
class WeeklyReporter(BaseAgent):
    """
    Недельный аналитический отчет с публикацией в Confluence
    """
    
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        # 1. Load 7-day JSON data from memory
        # 2. Generate comprehensive analytics
        # 3. Create trend analysis
        # 4. Generate human-readable reports
        # 5. Publish to Confluence
        # 6. Save local TXT backup
        pass
    
    async def analyze_weekly_trends(self, daily_data: List[JSON]) -> JSON:
        """Анализ трендов за неделю"""
        pass
    
    async def generate_employee_insights(self, employee_data: JSON) -> JSON:
        """Генерация инсайтов по сотрудникам"""
        pass
```

#### **Data Structure:**
```json
{
  "week_start": "2026-03-25",
  "week_end": "2026-03-31",
  "analysis_timestamp": "2026-03-31T19:00:00",
  "week_summary": {
    "total_tasks_processed": 315,
    "total_employees_analyzed": 8,
    "avg_daily_performance": 8.1,
    "completion_rate": 78.5,
    "meeting_participation_rate": 92.3
  },
  "employee_weekly_performance": {
    "ivanov": {
      "tasks_completed": 35,
      "avg_daily_score": 8.5,
      "trend": "improving",
      "top_achievements": [
        "CSI-123 API разработка завершена",
        "Git commits: 14 за неделю"
      ],
      "areas_for_improvement": [
        "Время ответа на comments: 48h avg"
      ]
    }
  },
  "project_insights": {
    "CSI": {
      "week_velocity": 45,
      "blockers_resolved": 8,
      "new_blockers": 3,
      "team_performance_trend": "stable"
    }
  },
  "confluence_publication": {
    "page_id": "987654321",
    "url": "https://confluence.company.com/display/PROJECTS/Weekly-Report-2026-03-31"
  }
}
```

#### **Configuration:**
```yaml
weekly_reporter:
  confluence_space_key: "PROJECTS"
  parent_page_id: "897438835"
  include_trend_analysis: true
  include_employee_insights: true
  include_predictions: false  # Future feature
  backup_local_reports: true
```

---

### **5. 🤖 OrchestratorAgent**

**Purpose:** Центральная оркестрация всех scheduled операций  

**Execution:** Continuous monitoring + scheduled triggers  
**Input Sources:** System clock + configuration + health monitoring  
**Output:** Coordinated execution + error handling + notifications  

#### **Core Responsibilities:**
```python
class OrchestratorAgent(BaseAgent):
    """
    Мастер-координатор всей scheduled системы
    """
    
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        # 1. Schedule management
        # 2. Agent coordination
        # 3. Quality control oversight
        # 4. Error handling and recovery
        # 5. Admin notifications
        # 6. Health monitoring
        pass
    
    async def execute_daily_workflow(self) -> JSON:
        """Оркестрация ежедневного workflow"""
        pass
    
    async def execute_weekly_workflow(self) -> JSON:
        """Оркестрация недельного workflow"""
        pass
    
    async def validate_workflow_quality(self, results: List[AgentResult]) -> bool:
        """Валидация качества выполнения workflow"""
        pass
```

#### **Orchestration Logic:**
```python
async def execute_daily_workflow(self):
    try:
        # 19:00 - Parallel execution
        jira_task = asyncio.create_task(self.daily_jira_analyzer.execute({}))
        meeting_task = asyncio.create_task(self.daily_meeting_analyzer.execute({}))
        
        jira_result, meeting_result = await asyncio.gather(
            jira_task, meeting_task, return_exceptions=True
        )
        
        # 19:30 - Sequential execution
        if isinstance(jira_result, Exception) or isinstance(meeting_result, Exception):
            await self.handle_execution_errors([jira_result, meeting_result])
            return
            
        # Quality check for individual agents
        jira_quality = await self.quality_controller.validate_agent_result(jira_result)
        meeting_quality = await self.quality_controller.validate_agent_result(meeting_result)
        
        if jira_quality.score < 90 or meeting_quality.score < 90:
            await self.retry_failed_agents(jira_result, meeting_result)
            return
            
        # Execute summary agent
        summary_result = await self.daily_summary_agent.execute({})
        
        # Final quality check
        summary_quality = await self.quality_controller.validate_agent_result(summary_result)
        
        if summary_quality.score < 90:
            await self.notify_admin_quality_issue(summary_result)
        else:
            await self.notify_success("Daily workflow completed successfully")
            
    except Exception as e:
        await self.handle_critical_error(e)
```

#### **Configuration:**
```yaml
orchestrator_agent:
  scheduler_timezone: "Europe/Moscow"
  daily_workflow_time: "19:00"
  weekly_workflow_day: "friday"
  weekly_workflow_time: "19:00"
  max_retry_attempts: 3
  retry_delay_seconds: 300
  admin_notification_email: "admin@company.com"
  health_check_interval: 3600
```

---

## 🔄 **QUALITY CONTROL SYSTEM**

### **LLM-Based Validation:**
```python
class ReportQualityController:
    async def validate_agent_result(self, result: AgentResult) -> QualityMetrics:
        prompt = f"""
        Оцени качество результата агента {result.agent_type}:
        
        Данные: {result.data}
        
        Критерии оценки:
        1. Полнота данных (completeness) - все ли типы данных присутствуют
        2. Точность данных (accuracy) - корректность значений
        3. Формат данных (format) - соответствие JSON схеме
        
        Вери балл от 0 до 100 для каждого критерия и общий балл.
        """
        
        llm_response = await self.llm_client.complete(prompt)
        return self.parse_quality_response(llm_response)
```

### **Quality Metrics:**
```typescript
interface QualityMetrics {
  completeness_score: number;    // 0-100
  accuracy_score: number;        // 0-100  
  format_score: number;          // 0-100
  overall_quality: number;       // 0-100
  needs_retry: boolean;          // Auto-retry decision
  feedback: string;              // LLM feedback for improvement
}
```

---

## 📂 **MEMORY STORE ARCHITECTURE**

### **JSON File Structure:**
```
/data/memory/json/
├── daily_jira_data_2026-03-25.json
├── daily_meeting_data_2026-03-25.json  
├── daily_summary_data_2026-03-25.json
├── employee_metrics_2026-03-25.json
├── weekly_summary_data_2026-03-31.json
├── system_state.json              # Current system status
├── agent_health.json             # Health monitoring
└── history/                      # 365-day retention
