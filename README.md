# MTS MultAgent - Scheduled Multi-Agent System

**Automated Continuous Project & Employee Monitoring System**

🤖 **Phase 3: Scheduled Architecture** | 🕒 **Daily/Weekly Automated Workflows** | 📊 **Employee Analytics & Reporting**

---

## 🎯 **System Overview**

MTS MultAgent - это интеллектуальная система непрерывного мониторинга проектов и сотрудников, которая автоматически анализирует данные из Jira, протоколы совещаний и репозитории кода, генерируя ежедневные и еженедельные отчеты с глубоким анализом производительности.

### **🔄 Key Transformation**
- **❌ Legacy:** Manual one-time analysis → **✅ New:** Automated continuous monitoring
- **❌ Legacy:** Ad-hoc reports → **✅ New:** Scheduled daily/weekly analytics  
- **❌ Legacy:** Simple task tracking → **✅ New:** Comprehensive employee insights
- **❌ Legacy:** Manual reporting → **✅ New:** Auto-published Confluence pages

---

## 🏗️ **Architecture Overview**

### **Scheduled Agent System**
```
🕒 APScheduler (Master Timer)
    ↓
🤖 OrchestratorAgent (Workflow Coordinator)
    ├── 📊 DailyJiraAnalyzer (19:00) → JSON Memory
    ├── 📄 DailyMeetingAnalyzer (19:00) → JSON Memory  
    ├── 📋 DailySummaryAgent (19:30) → TXT Report
    └── 📈 WeeklyReporter (Friday 19:00) → Confluence + TXT
        ↓
💾 JSON Memory Store + Human Reports
```

### **Core Components**
- **🤖 5 Specialized Agents:** Jira, Meeting, Summary, Weekly, Orchestrator
- **⏰ Scheduled Execution:** Daily 19:00, Friday 19:00 (UTC+3)
- **💾 JSON-First Storage:** Persistent state management
- **📈 LLM-Driven Analysis:** Intelligent insights and quality control
- **🔄 Quality Control:** Auto-retry with 90%+ quality threshold

---

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.11+
- OpenAI API key
- Jira API access
- Confluence API access

### **Installation**

```bash
# Clone repository
git clone https://github.com/PavelVM209/MTS_MultAgent.git
cd MTS_MultAgent

# Create virtual environment
python -m venv venv_py311
source venv_py311/bin/activate  # On Windows: venv_py311\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup configuration
cp .env.example .env
# Edit .env with your API keys and settings

# Initialize data directories
mkdir -p data/memory/json
mkdir -p data/reports/human
mkdir -p data/meetings
```

### **Configuration**

Edit `.env` file:

```bash
# OpenAI Configuration
OPENAI_API_KEY="your-openai-api-key"
OPENAI_MODEL="gpt-4-turbo-preview"
OPENAI_TEMPERATURE=0.1

# Jira Configuration
JIRA_URL="https://your-company.atlassian.net"
JIRA_USERNAME="your-jira-email"
JIRA_API_TOKEN="your-jira-token"
JIRA_PROJECT_KEYS="CSI,PROJ,DEV"

# Confluence Configuration  
CONFLUENCE_URL="https://your-company.atlassian.net/wiki"
CONFLUENCE_USERNAME="your-confluence-email"
CONFLUENCE_API_TOKEN="your-confluence-token"
CONFLUENCE_SPACE_KEY="PROJECTS"
CONFLUENCE_PARENT_PAGE_ID="897438835"

# Scheduler Configuration
SCHEDULER_TIMEZONE="Europe/Moscow"
DAILY_JOBS_TIME="19:00"
WEEKLY_REPORT_DAY="friday"
WEEKLY_REPORT_TIME="19:00"

# Data Paths
MEMORY_STORAGE_PATH="/data/memory/json"
REPORTS_OUTPUT_DIR="/data/reports/human"
MEETING_PROTOCOLS_PATH="/data/meetings"

# Quality Control
QUALITY_THRESHOLD="90.0"
MAX_RETRY_ATTEMPTS="3"
ADMIN_EMAIL="admin@company.com"
```

### **Running the System**

```bash
# Start scheduled system
python -m src.cli.main --mode scheduled

# Run manual daily workflow
python -m src.cli.main --mode daily

# Run manual weekly report
python -m src.cli.main --mode weekly

# System health check
python -m src.cli.main --mode health-check
```

---

## 📊 **Features & Capabilities**

### **🔄 Automated Workflows**

#### **Daily Workflow (19:00 UTC+3)**
```
19:00 - Parallel Data Collection:
├── Jira Analysis (multi-project employee tracking)
└── Meeting Protocol Analysis (multi-format parsing)

19:30 - Consolidation & Reporting:
├── Employee Metrics Consolidation
├── Performance Score Calculation  
├── Human-Readable Report Generation
└── Quality Validation & Persistence
```

#### **Weekly Workflow (Friday 19:00 UTC+3)**
```
19:00 - Comprehensive Analysis:
├── 7-Day Data Aggregation
├── Trend Analysis & Insights
├── Employee Performance Review
├── Project Velocity Analysis
├── Confluence Publication
└── Local Report Backup
```

### **📈 Employee Analytics**

#### **Comprehensive Metrics**
- **Task Tracking:** Total, in progress, completed per employee
- **Activity Monitoring:** Status changes, git commits, meeting participation
- **Performance Scoring:** 0-10 scale with trend analysis
- **Deadline Tracking:** Performance against timelines
- **Historical Trends:** 365-day retention with pattern analysis

#### **Smart Insights**
- **Performance Patterns:** Identification of high/low performers
- **Blocking Issues:** Automatic detection and escalation
- **Predictive Indicators:** Early warning signs for project risks
- **Team Dynamics:** Collaboration and participation metrics

### **📋 Multi-Format Support**

#### **Input Sources**
- **Jira API:** Multi-project task and issue tracking
- **Git API:** Commit integration and code activity
- **File System:** Meeting protocols (TXT, PDF, DOCX)
- **Historical Data:** 365-day trend analysis

#### **Output Formats**
- **JSON Memory Store:** Machine-readable persistent data
- **Human-Readable TXT:** Daily and weekly reports for stakeholders
- **Confluence Pages:** Published weekly analytics for organization
- **Admin Notifications:** Email alerts for system issues

---

## 🎯 **Business Value**

### **📊 Continuous Visibility**
- **Real-time Project Status:** Always current project health monitoring
- **Employee Performance:** Objective data-driven performance analytics
- **Trend Identification:** Early detection of positive/negative patterns
- **Risk Prevention:** Proactive identification of blocking issues

### **🤖 Automation Benefits**
- **Zero Manual Effort:** Fully automated data collection and analysis
- **Consistent Quality:** LLM-validated reports with 90%+ quality threshold
- **Timely Insights:** Daily reports at 19:30, weekly comprehensive analysis
- **Scalable Coverage:** Monitor multiple projects and employees simultaneously

### **📈 Data-Driven Decisions**
- **Performance Management:** Objective metrics for employee evaluation
- **Resource Allocation:** Data-driven team and project assignments
- **Process Optimization:** Identification of bottlenecks and inefficiencies
- **Strategic Planning:** Long-term trend analysis for organizational insights

---

## 🏗️ **Technical Architecture**

### **🤖 Agent System**

#### **DailyJiraAnalyzer**
```python
# Multi-project Jira analysis with employee tracking
- Project status across CSI, PROJ, DEV
- Employee task assignment and progress
- Status change monitoring
- Git commit integration
- Historical trend analysis
```

#### **DailyMeetingAnalyzer**  
```python
# Multi-format meeting protocol parsing
- TXT, PDF, DOCX file processing
- Employee action extraction
- Meeting participation tracking
- Decision and commitment monitoring
- Participation score calculation
```

#### **DailySummaryAgent**
```python
# Data consolidation and human report generation
- JSON data consolidation
- Employee performance scoring
- Trend analysis and insights
- Human-readable TXT reports
- Quality validation
```

#### **WeeklyReporter**
```python
# Comprehensive weekly analytics
- 7-day data aggregation
- Trend and pattern analysis
- Employee performance insights
- Confluence publication
- Local backup generation
```

#### **OrchestratorAgent**
```python
# Master workflow coordination
- Schedule management
- Agent coordination
- Quality control oversight
- Error handling and recovery
- Admin notifications
```

### **💾 Data Architecture**

#### **JSON Memory Store**
```
/data/memory/json/
├── daily_jira_data_2026-03-25.json
├── daily_meeting_data_2026-03-25.json
├── daily_summary_data_2026-03-25.json
├── weekly_summary_data_2026-03-31.json
├── employee_metrics_2026-03-25.json
├── system_state.json
└── history/ (365-day retention)
```

#### **Human Reports**
```
/data/reports/human/
├── 2026/03/25/
│   ├── daily_summary_2026-03-25.txt
│   └── employees_analysis_2026-03-25.txt
└── 2026/03/31/
    └── weekly_summary_2026-03-25_to_2026-03-31.txt
```

### **🔄 Quality Control**

#### **LLM Validation Pipeline**
```python
# Multi-dimensional quality assessment
- Completeness Score: Data coverage analysis
- Accuracy Score: Data correctness validation  
- Format Score: JSON schema compliance
- Overall Quality: Weighted composite score (90%+ threshold)
- Auto-Retry Logic: 3 attempts with exponential backoff
```

---

## 📊 **Monitoring & observability**

### **🔍 Health Monitoring**
- **System Health:** Hourly comprehensive health checks
- **Job Status:** Real-time job execution monitoring
- **Quality Metrics:** Continuous report quality assessment
- **Resource Usage:** CPU, memory, disk space monitoring
- **External Services:** Jira, Confluence, Git API availability

### **📈 Performance Metrics**
- **Execution Success Rate:** 99.9% target for scheduled jobs
- **Report Quality:** 90%+ average LLM validation score
- **Processing Time:** <5 minutes for daily workflows
- **Data Retention:** 365-day historical data availability
- **API Response:** <2 seconds average external API latency

### **🚨 Alerting System**
- **Job Failures:** Immediate email notifications
- **Quality Issues:** Auto-retry with admin escalation
- **System Health:** Critical alert on service degradation
- **External Services:** Notifications for API unavailability
- **Resource Limits:** Warnings for disk space/memory usage

---

## 🧪 **Testing**

### **Unit Tests**
```bash
# Run all unit tests
python -m pytest tests/unit/

# Run specific agent tests
python -m pytest tests/unit/test_daily_jira_analyzer.py
python -m pytest tests/unit/test_daily_meeting_analyzer.py
```

### **Integration Tests**
```bash
# Run end-to-end workflow tests
python -m pytest tests/integration/test_scheduled_workflows.py

# Run data flow tests
python -m pytest tests/integration/test_data_pipeline.py
```

### **Performance Tests**
```bash
# Run performance benchmarks
python -m pytest tests/performance/test_scheduler_performance.py

# Load testing
python tests/load/test_concurrent_workflows.py
```

---

## 📚 **Documentation**

### **Memory Bank**
- **[activeContext.md](memory-bank/activeContext.md)** - Current development focus
- **[progress.md](memory-bank/progress.md)** - Project progress tracking
- **[agentsSpec.md](memory-bank/agentsSpec.md)** - Detailed agent specifications
- **[schedulerSpec.md](memory-bank/schedulerSpec.md)** - Scheduler architecture
- **[dataFlowDesign.md](memory-bank/dataFlowDesign.md)** - Data flow specifications

### **Technical Documentation**
- **[systemPatterns.md](memory-bank/systemPatterns.md)** - Design patterns and conventions
- **[techContext.md](memory-bank/techContext.md)** - Technical architecture context
- **[productContext.md](memory-bank/productContext.md)** - Product vision and requirements

---

## 🔧 **Development**

### **Adding New Agents**

```python
# 1. Create agent class
class NewAgent(BaseAgent):
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        # Implementation
        pass

# 2. Add to scheduler
scheduler.add_job(
    func=new_agent.execute,
    trigger="cron",
    hour=20,
    minute=0,
    timezone="Europe/Moscow"
)

# 3. Update orchestrator
await orchestrator.register_agent("new_agent", new_agent)
```

### **Configuration Extensions**

```yaml
# config/scheduler.yaml - Add new agent config
agents:
  new_agent:
    enabled: true
    schedule: "20:00"
    config_param: value
```

### **Quality Control Extensions**

```python
# Add custom quality validation
class CustomQualityController(QualityController):
    async def custom_validation(self, data: dict) -> float:
        # Custom validation logic
        return quality_score
```

---

## 🚀 **Deployment**

### **Production Setup**

```bash
# Using Docker
docker build -t mts-multagent .
docker run -d --name mts-multagent \
  -v $(pwd)/data:/data \
  -v $(pwd)/config:/config \
  --env-file .env \
  mts-multagent

# Using Docker Compose
docker-compose up -d
```

### **Environment Configuration**
```yaml
# docker-compose.yml
version: '3.8'
services:
  mts-multagent:
    build: .
    volumes:
      - ./data:/data
      - ./config:/config
    environment:
      - PYTHONPATH=/app
      - TZ=Europe/Moscow
    restart: unless-stopped
```

### **Monitoring Setup**
```yaml
# monitoring/prometheus.yml
scrape_configs:
  - job_name: 'mts-multagent'
    static_configs:
      - targets: ['localhost:8080']
```

---

## 🤝 **Contributing**

### **Development Workflow**
1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and add tests
4. Run test suite (`python -m pytest`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Create Pull Request

### **Code Standards**
- **Python 3.11+** compliance
- **Type hints** required for all functions
- **Async/await** patterns for I/O operations
- **Error handling** with comprehensive exception management
- **Documentation** for all public APIs
- **Testing** minimum 80% code coverage

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 **Support**

### **Getting Help**
- **Documentation:** Check memory bank for detailed specs
- **Issues:** [GitHub Issues](https://github.com/PavelVM209/MTS_MultAgent/issues)
- **Email:** admin@company.com for production support

### **Troubleshooting**

#### **Common Issues**
```bash
# Scheduler not starting
python -c "from apscheduler.schedulers.asyncio import AsyncIOScheduler; print('APScheduler OK')"

# Memory store permissions
ls -la /data/memory/json/
chmod 755 /data/memory/json/

# API connectivity
curl -H "Authorization: Bearer $JIRA_API_TOKEN" "$JIRA_URL/rest/api/3/myself"
```

#### **Debug Mode**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python -m src.cli.main --mode scheduled --debug
```

---

## 🗺️ **Roadmap**

### **Phase 4 (April 2026)**
- **Predictive Analytics:** AI-driven trend prediction
- **Mobile Interface:** Real-time dashboards and alerts
- **Advanced Integrations:** Slack, email, calendar integration
- **Multi-tenant Support:** Scalable enterprise architecture

### **Phase 5 (May 2026)**
- **Machine Learning:** Custom performance prediction models
- **Voice Interfaces:** Natural language reporting
- **Blockchain Integration:** Immutable audit trails
- **Global Deployment:** Multi-region support

---

**🚀 Current Status: Phase 3 Implementation (48% Complete)**  

**📊 Next Milestone: Scheduled Agent Deployment (March 29, 2026)**

---

*Built with ❤️ for intelligent project automation*
