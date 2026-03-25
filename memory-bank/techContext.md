# Technical Context - MTS MultAgent Scheduled Architecture

## 🏗️ **Technical Architecture Overview**

**Phase:** 3 - Scheduled Multi-Agent System  
**Stack:** Python 3.11+, APScheduler, AsyncIO, OpenAI GPT-4, File-based JSON storage  
**Pattern:** Event-driven scheduled workflows with orchestrated agent coordination  

---

## 🔧 **Core Technology Stack**

### **Runtime & Foundation**
```python
# Core Runtime
Python: 3.11.5
AsyncIO: Built-in asyncio for concurrent operations
Type Hints: Full type annotations for code reliability
Environment Management: python-dotenv with .env configuration

# Scheduling & Orchestration
APScheduler: 3.10+ for cron-based scheduling
AsyncIOScheduler: Async-compatible scheduler implementation
Circuit Breaker: Custom implementation for fault tolerance
```

### **LLM & AI Integration**
```python
# OpenAI Integration
OpenAI API: GPT-4-turbo-preview for intelligent analysis
LangChain: 0.1.0+ for LLM orchestration and prompt management
Token Management: tiktoken for efficient API usage
Caching: In-memory LLM response caching with TTL

# Quality Validation
Custom Quality Metrics: Multi-dimensional scoring system
Iterative Improvement: Auto-refinement loops with convergence detection
```

### **Data Processing & Storage**
```python
# Data Processing
Pandas: Data manipulation and analysis
JSON Schema: Data validation and structure enforcement
Pydantic: Type-safe data models with validation

# File Processing
PyPDF2: PDF document parsing
python-docx: DOCX document processing
Pathlib: Advanced file system operations

# Storage Architecture
File-based JSON: Persistent memory store with 365-day retention
Structured Directories: Hierarchical data organization
Backup Systems: Automatic archival and compression
```

### **External APIs & Integration**
```python
# Jira Integration
jira: Python Jira client library
REST API: Direct API calls for advanced features
Rate Limiting: Custom throttling implementation
Authentication: API token-based auth

# Confluence Integration
atlassian-python-api: Confluence REST client
Markdown Processing: Confluence-compatible formatting
Page Management: Hierarchical page creation and updates

# Git Integration
GitPython: Repository interaction and commit analysis
API Integration: GitLab/GitHub API for commit data
Branch Analysis: Development activity tracking
```

---

## 🏛️ **Architecture Patterns**

### **1. Scheduled Agent Architecture**
```python
# Master-Slave Pattern with Orchestration
class ScheduledAgentSystem:
    """
    Scheduled multi-agent system with orchestrated workflows
    """
    
    # Core Components
    scheduler: AsyncIOScheduler          # Time-based execution
    orchestrator: OrchestratorAgent      # Central coordination
    agents: Dict[str, BaseAgent]         # Specialized agents
    memory_store: JSONMemoryStore       # Persistent state
    
    # Execution Patterns
    async def execute_scheduled_workflow(self, workflow_type: str):
        """Orchestrated workflow execution"""
        
    async def coordinate_parallel_execution(self, agent_ids: List[str]):
        """Parallel agent coordination"""
        
    async def validate_quality_gates(self, results: List[AgentResult]):
        """Quality control validation"""
```

### **2. JSON-First Data Architecture**
```python
# Event Sourcing with JSON Persistence
class JSONMemoryStore:
    """
    JSON-based event sourcing and state management
    """
    
    # Data Patterns
    event_stream: List[JSONEvent]        # Immutable event log
    state_snapshots: Dict[str, JSONState] # Periodic state captures
    indexes: Dict[str, JSONIndex]        # Fast lookup indexes
    
    # Operations
    async def append_event(self, event: JSONEvent) -> None:
        """Append new event to stream"""
        
    async def get_state(self, timestamp: datetime) -> JSONState:
        """Reconstruct state at specific time"""
        
    async def query_events(self, filter: EventFilter) -> List[JSONEvent]:
        """Query events with filters"""
```

### **3. Circuit Breaker Resilience Pattern**
```python
# Fault-Tolerant External API Access
class CircuitBreaker:
    """
    Circuit breaker for external service resilience
    """
    
    # States
    CLOSED: "Normal operation"
    OPEN: "Service unavailable, fail fast"
    HALF_OPEN: "Testing service recovery"
    
    # Configuration
    failure_threshold: int = 5          # Failures before opening
    recovery_timeout: int = 300         # Seconds before testing
    success_threshold: int = 2          # Successes to close
    
    # Implementation
    async def execute_with_protection(self, operation: Callable) -> Any:
        """Execute operation with circuit protection"""
```

### **4. Quality Control Pipeline Pattern**
```python
# Multi-Stage Quality Validation
class QualityController:
    """
    LLM-based quality control with iterative improvement
    """
    
    # Validation Stages
    completeness_check: CompletenessValidator
    accuracy_check: AccuracyValidator
    format_check: FormatValidator
    
    # Improvement Loop
    async def validate_and_improve(self, data: Any) -> QualityValidated:
        """Validate quality and auto-improve if needed"""
        
    async def llm_quality_assessment(self, data: Any) -> QualityMetrics:
        """LLM-based quality scoring"""
        
    async def apply_improvements(self, data: Any, feedback: str) -> Any:
        """Apply LLM-suggested improvements"""
```

---

## 🔌 **Integration Architecture**

### **External API Integration Strategy**
```python
# Unified API Client Pattern
class APIClient:
    """
    Unified client for all external API integrations
    """
    
    # Common Features
    rate_limiter: RateLimiter            # API rate limiting
    retry_handler: RetryHandler          # Exponential backoff
    auth_manager: AuthenticationManager  # Token management
    logger: StructuredLogger            # Request/response logging
    
    # Service-Specific Clients
    jira_client: JiraAPIClient
    confluence_client: ConfluenceAPIClient
    git_client: GitAPIClient
    
    # Implementation
    async def make_request(self, service: str, endpoint: str, **kwargs) -> Response:
        """Unified request handling with all cross-cutting concerns"""
```

### **Data Flow Integration Pattern**
```python
# Pipeline-Based Data Processing
class DataPipeline:
    """
    Configurable data processing pipeline
    """
    
    # Pipeline Stages
    stages: List[StageInterface]         # Processing stages
    transformers: List[Transformer]      # Data transformers
    validators: List[Validator]          # Data validation
    
    # Execution Patterns
    async def execute_pipeline(self, input_data: Any) -> ProcessedData:
        """Execute complete data pipeline"""
        
    async def execute_stage(self, stage: StageInterface, data: Any) -> Any:
        """Execute individual pipeline stage"""
        
    async def handle_stage_failure(self, stage: StageInterface, error: Exception):
        """Handle processing failures with recovery"""
```

---

## 📊 **Data Architecture**

### **JSON Schema Design**
```python
# Unified Data Models
class JiraAnalysisResult(BaseModel):
    """Jira analysis data structure"""
    date: datetime
    timestamp: datetime
    projects: Dict[str, ProjectData]
    employees: Dict[str, EmployeeData]
    system_metrics: SystemMetrics
    
    # Validation
    @validator('projects')
    def validate_project_keys(cls, v):
        return {k: ProjectData(**data) for k, data in v.items()}

class MeetingAnalysisResult(BaseModel):
    """Meeting protocol analysis data structure"""
    date: datetime
    processed_files: List[str]
    meetings: List[MeetingData]
    employee_actions: List[EmployeeAction]
    participation_metrics: ParticipationMetrics

class DailySummaryResult(BaseModel):
    """Daily consolidated summary data structure"""
    date: datetime
    consolidation_timestamp: datetime
    employee_summary: Dict[str, EmployeeSummary]
    project_summary: Dict[str, ProjectSummary]
    performance_scores: Dict[str, PerformanceScore]
    trend_analysis: TrendAnalysis
```

### **File System Organization**
```
/data/
├── memory/json/                    # JSON Memory Store
│   ├── daily_jira_data_YYYY-MM-DD.json
│   ├── daily_meeting_data_YYYY-MM-DD.json
│   ├── daily_summary_data_YYYY-MM-DD.json
│   ├── weekly_summary_data_YYYY-MM-DD.json
│   ├── employee_metrics_YYYY-MM-DD.json
│   ├── system_state.json
│   └── history/                   # 365-day archive
│       ├── 2025/
│       ├── 2024/
│       └── archived/
├── reports/human/                 # Human-Readable Reports
│   ├── YYYY/
│   │   ├── MM/
│   │   │   ├── DD/
│   │   │   │   ├── daily_summary_YYYY-MM-DD.txt
│   │   │   │   ├── employees_analysis_YYYY-MM-DD.txt
│   │   │   │   └── weekly_summary_YYYY-MM-DD.txt
│   │   │   └── archived/
│   │   └── archived/
│   └── archived/
├── meetings/                      # Meeting Protocol File Store
│   ├── daily_standup/
│   ├── sprint_planning/
│   ├── retrospectives/
│   └── archived/
└── system/                        # System Runtime Data
    ├── logs/
    ├── cache/
    ├── temp/
    └── backups/
```

### **Data Retention Policy**
```python
class DataRetentionPolicy:
    """
    Automated data lifecycle management
    """
    
    # Retention Periods
    json_data_retention_days: int = 365      # JSON memory store
    human_reports_retention_days: int = 90   # Human-readable reports
    meeting_files_retention_days: int = 180  # Meeting protocols
    logs_retention_days: int = 30            # System logs
    
    # Archival Strategy
    async def archive_old_data(self, older_than_days: int) -> None:
        """Compress and archive old data"""
        
    async def cleanup_expired_data(self, older_than_days: int) -> None:
        """Permanently delete expired data"""
        
    async def optimize_storage(self) -> None:
        """Optimize file system storage"""
```

---

## 🔄 **Execution Architecture**

### **Scheduled Execution Pattern**
```python
# Time-Based Workflow Orchestration
class ScheduledWorkflow:
    """
    Time-based workflow execution with dependencies
    """
    
    # Workflow Definition
    workflow_id: str
    schedule: ScheduleDefinition
    agents: List[AgentDefinition]
    dependencies: Dict[str, List[str]]    # Agent dependencies
    quality_gates: List[QualityGate]      # Quality checkpoints
    
    # Execution Logic
    async def execute_workflow(self) -> WorkflowResult:
        """Execute complete scheduled workflow"""
        
    async def execute_parallel_phase(self, phase: List[str]) -> Dict[str, AgentResult]:
        """Execute agents in parallel"""
        
    async def execute_sequential_phase(self, phase: List[str]) -> Dict[str, AgentResult]:
        """Execute agents sequentially"""
        
    async def validate_phase_quality(self, phase_results: Dict[str, AgentResult]) -> bool:
        """Validate quality phase results"""
```

### **AsyncIO Concurrency Pattern**
```python
# High-Performance Async Processing
class AsyncProcessor:
    """
    Async processing with controlled concurrency
    """
    
    # Concurrency Control
    semaphore: asyncio.Semaphore          # Concurrency limiting
    task_queue: asyncio.Queue            # Task queue management
    worker_pool: List[asyncio.Task]      # Worker tasks
    
    # Execution Patterns
    async def process_with_concurrency(self, tasks: List[Task], max_workers: int) -> List[Result]:
        """Process tasks with controlled concurrency"""
        
    async def worker_loop(self, worker_id: int) -> None:
        """Worker processing loop"""
        
    async def graceful_shutdown(self) -> None:
        """Graceful shutdown of processing"""
```

---

## 🛡️ **Security Architecture**

### **API Security Management**
```python
# Secure Credential Management
class SecurityManager:
    """
    Centralized security and credential management
    """
    
    # Credential Storage
    encrypted_secrets: Dict[str, str]     # Encrypted API keys
    token_cache: Dict[str, Token]         # OAuth token cache
    certificate_store: Certificates       # SSL certificates
    
    # Security Features
    async def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        
    async def rotate_api_credentials(self) -> None:
        """Rotate API credentials"""
        
    async def validate_api_permissions(self, service: str, required_scopes: List[str]) -> bool:
        """Validate API token permissions"""
```

### **Data Privacy & Compliance**
```python
# Privacy-First Data Handling
class PrivacyManager:
    """
    Data privacy and compliance management
    """
    
    # Privacy Features
    data_anonymization: bool = True       # Anonymize personal data
    audit_logging: bool = True            # Audit all data access
    retention_compliance: bool = True     # Compliance retention
    
    # Implementation
    async def anonymize_employee_data(self, employee_data: dict) -> dict:
        """Anonymize sensitive employee information"""
        
    async def log_data_access(self, user: str, data_type: str, operation: str) -> None:
        """Log data access for audit"""
        
    async def validate_gdpr_compliance(self, data: dict) -> bool:
        """Validate GDPR compliance"""
```

---

## 🔍 **Monitoring & Observability**

### **Structured Logging Architecture**
```python
# Comprehensive Logging System
class StructuredLogger:
    """
    Structured logging with correlation and context
    """
    
    # Log Structure
    log_entry: LogEntryTemplate
    correlation_id: str                   # Request correlation
    context: Dict[str, Any]              # Additional context
    severity: LogSeverity                 # Log level
    
    # Log Destinations
    file_logger: FileBasedLogger
    syslog_logger: SyslogLogger
    external_logger: ExternalLogService
    
    # Implementation
    async def log_structured(self, event: str, level: LogSeverity, **kwargs) -> None:
        """Log structured event with context"""
        
    async def log_workflow_execution(self, workflow_id: str, phase: str, status: str) -> None:
        """Log workflow execution events"""
        
    async def log_quality_metrics(self, agent: str, quality_score: float) -> None:
        """Log quality metrics"""
```

### **Metrics Collection System**
```python
# Performance & Health Metrics
class MetricsCollector:
    """
    Comprehensive metrics collection and reporting
    """
    
    # Metric Types
    counter_metrics: Dict[str, Counter]   # Event counters
    gauge_metrics: Dict[str, Gauge]       # Current values
    histogram_metrics: Dict[str, Histogram] # Value distributions
    timer_metrics: Dict[str, Timer]       # Duration measurements
    
    # Collection Points
    agent_execution_times: Timer
    api_response_times: Histogram
    quality_scores: Gauge
    error_rates: Counter
    
    # Implementation
    async def record_agent_execution(self, agent: str, duration: float, success: bool) -> None:
        """Record agent execution metrics"""
        
    async def get_system_health_snapshot(self) -> HealthSnapshot:
        """Get current system health metrics"""
        
    async def export_metrics(self, format: str) -> str:
        """Export metrics in specified format"""
```

---

## 🚀 **Performance Optimization**

### **Caching Strategy**
```python
# Multi-Level Caching System
class CacheManager:
    """
    Multi-tier caching with TTL and invalidation
    """
    
    # Cache Tiers
    l1_cache: Dict[str, CacheEntry]      # In-memory L1 cache
    l2_cache: FileBasedCache             # File-based L2 cache
    l3_cache: RedisCache                  # External L3 cache (optional)
    
    # Cache Policies
    default_ttl: int = 3600              # 1 hour default TTL
    max_memory_usage: int = 100 * 1024 * 1024  # 100MB max
    invalidation_strategy: InvalidationStrategy
    
    # Implementation
    async def get_cached(self, key: str) -> Optional[Any]:
        """Get value from cache hierarchy"""
        
    async def set_cached(self, key: str, value: Any, ttl: int = None) -> None:
        """Set value in cache hierarchy"""
        
    async def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate cache entries matching pattern"""
```

### **Resource Management**
```python
# Efficient Resource Utilization
class ResourceManager:
    """
    System resource management and optimization
    """
    
    # Resource Pools
    connection_pool: ConnectionPool        # Database/API connections
    thread_pool: ThreadPoolExecutor       # Thread management
    memory_pool: MemoryPool              # Memory allocation
    
    # Optimization Strategies
    connection_scaling: bool = True       # Auto-scale connections
    memory_gc_threshold: float = 0.8     # GC trigger threshold
    cpu_utilization_target: float = 0.7  # Target CPU usage
    
    # Implementation
    async def optimize_resource_usage(self) -> OptimizationReport:
        """Optimize system resource usage"""
        
    async def handle_memory_pressure(self) -> None:
        """Handle memory pressure scenarios"""
        
    async def scale_connection_pool(self, demand: int) -> None:
        """Dynamically scale connection pool"""
```

---

## 🔧 **Development & Deployment**

### **Development Environment Setup**
```bash
# Python Environment
python -m venv venv_py311
source venv_py311/bin/activate
pip install -r requirements.txt

# Development Dependencies
pip install -r requirements-dev.txt  # Testing, linting, profiling
pip install pre-commit                 # Git hooks
pip install black isort mypy          # Code formatting and type checking

# Development Tools
poetry install                         # Alternative dependency management
docker-compose up -d                  # Local development environment
```

### **Code Quality Standards**
```python
# Type Safety & Code Quality
typing: Full type hints for all functions
pydantic: Data validation and models
mypy: Static type checking
black: Code formatting
isort: Import organization
flake8: Linting
pytest: Testing framework
coverage: Coverage reporting

# Development Patterns
async/await: All I/O operations must be async
error_handling: Comprehensive exception management
logging: Structured logging with context
documentation: Comprehensive docstrings
testing: 80%+ code coverage requirement
```

### **Deployment Architecture**
```dockerfile
# Docker Multi-stage Build
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM
