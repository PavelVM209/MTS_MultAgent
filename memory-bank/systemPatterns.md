# System Patterns - MTS MultAgent Scheduled Architecture

## 🏗️ **Design Patterns & Conventions**

**Phase:** 3 - Scheduled Multi-Agent System  
**Approach:** Event-driven architecture with orchestrated workflows  
**Principles:** JSON-first data flow, async-first processing, quality-controlled execution  

---

## 🔄 **Core Architectural Patterns**

### **1. Orchestrator Pattern**
```python
# Centralized Coordination Pattern
class OrchestratorAgent(BaseAgent):
    """
    Master coordinator for scheduled multi-agent workflows
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.quality_controller: QualityController = QualityController()
        self.error_handler: ErrorHandler = ErrorHandler()
    
    async def execute_workflow(self, workflow_name: str) -> WorkflowResult:
        """Execute orchestrated workflow with quality control"""
        
        # 🔹 Workflow Definition Resolution
        workflow = self.workflows[workflow_name]
        
        # 🔹 Phase-Based Execution
        for phase in workflow.phases:
            if phase.execution_type == "parallel":
                results = await self.execute_parallel_phase(phase)
            else:
                results = await self.execute_sequential_phase(phase)
            
            # 🔹 Quality Gate Validation
            if not await self.validate_phase_quality(phase, results):
                await self.handle_quality_gate_failure(phase, results)
                return WorkflowResult(success=False, error="Quality gate failed")
        
        return WorkflowResult(success=True, data=results)
    
    async def execute_parallel_phase(self, phase: WorkflowPhase) -> Dict[str, AgentResult]:
        """Execute multiple agents in parallel"""
        tasks = [
            self.agents[agent_id].execute(phase.agent_configs[agent_id])
            for agent_id in phase.agents
        ]
        
        parallel_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to structured results
        return {
            agent_id: result if not isinstance(result, Exception) 
                      else AgentResult(success=False, error=str(result))
            for agent_id, result in zip(phase.agents, parallel_results)
        }
```

### **2. Scheduled Execution Pattern**
```python
# Time-Based Workflow Scheduling
class ScheduledExecutionPattern:
    """
    Scheduled execution with dependency management and error recovery
    """
    
    async def setup_scheduled_workflows(self):
        """Setup all scheduled workflows with dependencies"""
        
        # Daily Workflow - 19:00 UTC+3
        self.scheduler.add_job(
            func=self.execute_daily_workflow,
            trigger="cron",
            hour=19,
            minute=0,
            timezone="Europe/Moscow",
            id="daily_workflow",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300
        )
        
        # Weekly Workflow - Friday 19:00 UTC+3
        self.scheduler.add_job(
            func=self.execute_weekly_workflow,
            trigger="cron",
            day_of_week="fri",
            hour=19,
            minute=0,
            timezone="Europe/Moscow",
            id="weekly_workflow",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=900
        )
        
        # Health Check - Every hour
        self.scheduler.add_job(
            func=self.health_check,
            trigger="interval",
            hours=1,
            id="health_check",
            max_instances=1
        )
    
    async def execute_daily_workflow(self):
        """Daily workflow with parallel data collection"""
        
        workflow_id = generate_workflow_id("daily")
        
        try:
            # Phase 1: Parallel Data Collection
            await self.log_workflow_start(workflow_id, "daily_workflow", "data_collection")
            
            # Parallel execution of data collection agents
            jira_future = asyncio.create_task(
                self.safe_execute_agent("daily_jira_analyzer", {})
            )
            meeting_future = asyncio.create_task(
                self.safe_execute_agent("daily_meeting_analyzer", {})
            )
            
            jira_result, meeting_result = await asyncio.gather(
                jira_future, meeting_future, return_exceptions=True
            )
            
            # Phase 2: Sequential Consolidation
            if isinstance(jira_result, Exception) or isinstance(meeting_result, Exception):
                await self.handle_parallel_execution_failures([jira_result, meeting_result])
                return
            
            await self.log_workflow_phase(workflow_id, "data_collection", "completed")
            
            # Execute summary consolidation
            summary_result = await self.safe_execute_agent("daily_summary_agent", {})
            
            if summary_result.success:
                await self.log_workflow_complete(workflow_id, "daily_workflow", "success")
            else:
                await self.log_workflow_complete(workflow_id, "daily_workflow", "failed")
                
        except Exception as e:
            await self.log_workflow_complete(workflow_id, "daily_workflow", "critical_error", str(e))
            await self.handle_critical_workflow_error("daily_workflow", e)
```

### **3. JSON-First Data Pattern**
```python
# JSON-Centric Data Management
class JSONFirstDataPattern:
    """
    JSON-first data persistence with schema validation
    """
    
    def __init__(self):
        self.schemas: Dict[str, Schema] = self._load_schemas()
        self.storage_path: Path = Path("/data/memory/json")
        self.index_manager: IndexManager = IndexManager()
    
    async def persist_json_data(self, data_type: str, data: dict) -> str:
        """Persist data with JSON schema validation"""
        
        # 🔹 Schema Validation
        schema = self.schemas.get(data_type)
        if schema:
            validation_result = schema.validate(data)
            if not validation_result.valid:
                raise ValidationError(f"Schema validation failed: {validation_result.errors}")
        
        # 🔹 Data Enrichment
        enriched_data = self._enrich_with_metadata(data, data_type)
        
        # 🔹 File Path Generation
        timestamp = datetime.now().strftime("%Y-%m-%d")
        filename = f"{data_type}_{timestamp}.json"
        file_path = self.storage_path / filename
        
        # 🔹 Atomic Write
        await self._atomic_json_write(file_path, enriched_data)
        
        # 🔹 Index Update
        await self.index_manager.update_index(data_type, file_path, enriched_data)
        
        return str(file_path)
    
    async def load_json_data(self, data_type: str, date: str = None) -> dict:
        """Load JSON data with date-based resolution"""
        
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        filename = f"{data_type}_{date}.json"
        file_path = self.storage_path / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"JSON data file not found: {file_path}")
        
        # 🔹 Schema Validation on Load
        data = await self._load_json_file(file_path)
        schema = self.schemas.get(data_type)
        
        if schema:
            validation_result = schema.validate(data)
            if not validation_result.valid:
                raise ValidationError(f"Loaded data validation failed: {validation_result.errors}")
        
        return data
    
    async def query_json_data(self, query: JSONQuery) -> List[dict]:
        """Query JSON data using file-based indexes"""
        
        # 🔹 Index-Based Query Resolution
        candidate_files = await self.index_manager.query_files(query)
        
        results = []
        for file_path in candidate_files:
            data = await self._load_json_file(file_path)
            
            # 🔹 In-Memory Query Filtering
            if self._matches_query(data, query):
                results.append(data)
        
        return results
```

### **4. Quality Control Pipeline Pattern**
```python
# Multi-Stage Quality Validation Pipeline
class QualityControlPipeline:
    """
    LLM-driven quality control with iterative improvement
    """
    
    def __init__(self):
        self.llm_client: LLMClient = LLMClient()
        self.validators: Dict[str, Validator] = {
            "completeness": CompletenessValidator(),
            "accuracy": AccuracyValidator(),
            "format": FormatValidator(),
            "consistency": ConsistencyValidator()
        }
        self.improver: DataImprover = DataImprover()
    
    async def validate_and_improve(
        self, 
        data: Any, 
        data_type: str, 
        quality_threshold: float = 90.0
    ) -> QualityControlledResult:
        """Multi-stage quality validation with auto-improvement"""
        
        current_data = data
        best_quality = 0.0
        iterations = 0
        max_iterations = 3
        
        while iterations < max_iterations:
            # 🔹 Multi-Stage Validation
            validation_results = {}
            overall_quality = 0.0
            
            for validator_name, validator in self.validators.items():
                result = await validator.validate(current_data)
                validation_results[validator_name] = result
                overall_quality += result.score * result.weight
            
            overall_quality = min(overall_quality, 100.0)
            
            # 🔹 Quality Threshold Check
            if overall_quality >= quality_threshold:
                return QualityControlledResult(
                    data=current_data,
                    quality_score=overall_quality,
                    validation_results=validation_results,
                    iterations=iterations,
                    success=True
                )
            
            # 🔹 Iterative Improvement
            if iterations < max_iterations - 1:
                feedback = await self._generate_improvement_feedback(
                    current_data, validation_results, data_type
                )
                
                improved_data = await self.improver.improve_data(current_data, feedback)
                
                # Only accept improvement if it increases quality
                if improved_data != current_data:
                    current_data = improved_data
                    best_quality = overall_quality
            
            iterations += 1
        
        # Return best effort result
        return QualityControlledResult(
            data=current_data,
            quality_score=best_quality,
            validation_results=validation_results,
            iterations=iterations,
            success=False,
            reason=f"Failed to achieve quality threshold {quality_threshold}"
        )
    
    async def _generate_improvement_feedback(
        self, 
        data: Any, 
        validation_results: Dict[str, ValidationResult], 
        data_type: str
    ) -> str:
        """Generate LLM-based improvement feedback"""
        
        validation_summary = "\n".join([
            f"- {name}: {result.score}% - {result.feedback}"
            for name, result in validation_results.items()
        ])
        
        prompt = f"""
        Analyze the following {data_type} data and provide specific improvement suggestions:
        
        Current Data:
        {json.dumps(data, indent=2, default=str)}
        
        Validation Results:
        {validation_summary}
        
        Provide specific, actionable feedback to improve:
        1. Data completeness
        2. Accuracy of information
        3. Format consistency
        4. Logical consistency
        
        Focus on the lowest scoring areas first.
        """
        
        return await self.llm_client.complete(prompt)
```

---

## 🔌 **Integration Patterns**

### **1. Circuit Breaker Resilience Pattern**
```python
# Fault-Tolerant External Service Integration
class CircuitBreakerResilience:
    """
    Circuit breaker pattern for external service resilience
    """
    
    def __init__(self, service_name: str, config: CircuitBreakerConfig):
        self.service_name = service_name
        self.failure_threshold = config.failure_threshold
        self.recovery_timeout = config.recovery_timeout
        self.success_threshold = config.success_threshold
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        
        self.metrics_collector = MetricsCollector()
        self.logger = StructuredLogger()
    
    async def execute_with_protection(self, operation: Callable) -> Any:
        """Execute operation with circuit breaker protection"""
        
        start_time = time.time()
        
        try:
            # 🔹 Circuit State Validation
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    await self.logger.info(f"Circuit breaker for {self.service_name} attempting reset")
                else:
                    raise CircuitBreakerOpenException(f"Circuit breaker for {self.service_name} is OPEN")
            
            # 🔹 Operation Execution
            result = await operation()
            
            # 🔹 Success Handling
            self.on_success()
            
            await self.metrics_collector.record_circuit_breaker_success(
                self.service_name, time.time() - start_time
            )
            
            return result
            
        except Exception as e:
            # 🔹 Failure Handling
            self.on_failure()
            
            await self.metrics_collector.record_circuit_breaker_failure(
                self.service_name, time.time() - start_time, type(e).__name__
            )
            
            await self.logger.error(f"Circuit breaker execution failed for {self.service_name}: {str(e)}")
            
            raise e
    
    def on_success(self):
        """Handle successful operation execution"""
        if self.state == CircuitState.HALF_OPEN:
            if hasattr(self, 'consecutive_successes'):
                self.consecutive_successes += 1
            else:
                self.consecutive_successes = 1
            
            if self.consecutive_successes >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                del self.consecutive_successes
        else:
            self.failure_count = 0
    
    def on_failure(self):
        """Handle operation execution failure"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        return (
            self.state == CircuitState.OPEN and
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
```

### **2. Async Resource Pool Pattern**
```python
# Efficient Resource Management for External APIs
class AsyncResourcePool:
    """
    Async resource pool for external service connections
    """
    
    def __init__(self, create_resource: Callable, max_size: int = 10):
        self.create_resource = create_resource
        self.max_size = max_size
        self.pool: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self.active_resources: Set = set()
        self.resource_counter = 0
        self.stats = PoolStatistics()
    
    async def acquire(self, timeout: float = 30.0) -> Any:
        """Acquire resource from pool"""
        
        start_time = time.time()
        
        try:
            # 🔹 Try to get existing resource
            resource = await asyncio.wait_for(
                self.pool.get(), 
                timeout=timeout
            )
            
            # Validate resource health
            if await self._is_resource_healthy(resource):
                self.active_resources.add(resource)
                await self.stats.record_acquisition(time.time() - start_time, "existing")
                return resource
            else:
                # Resource unhealthy, dispose and create new
                await self._dispose_resource(resource)
                return await self._create_and_acquire(timeout)
                
        except asyncio.TimeoutError:
            # Pool empty, try to create new resource
            return await self._create_and_acquire(timeout)
    
    async def release(self, resource: Any):
        """Release resource back to pool"""
        
        if resource in self.active_resources:
            self.active_resources.remove(resource)
            
            # Validate resource before returning to pool
            if await self._is_resource_healthy(resource):
                await self.pool.put(resource)
                await self.stats记录_release("healthy")
            else:
                await self._dispose_resource(resource)
                await self.stats.record_release("unhealthy")
    
    async def _create_and_acquire(self, timeout: float) -> Any:
        """Create new resource if under limit"""
        
        if len(self.active_resources) + self.pool.qsize() >= self.max_size:
            raise ResourcePoolExhaustedException("Resource pool exhausted")
        
        resource = await self.create_resource()
        self.resource_counter += 1
        self.active_resources.add(resource)
        
        await self.stats.record_acquisition(time.time() - timeout, "created")
        
        return resource
    
    async def health_check(self) -> PoolHealthStatus:
        """Check pool health"""
        
        total_resources = len(self.active_resources) + self.pool.qsize()
        healthy_resources = 0
        
        # Check active resources health
        for resource in list(self.active_resources):
            if await self._is_resource_healthy(resource):
                healthy_resources += 1
            else:
                await self._dispose_resource(resource)
                self.active_resources.discard(resource)
        
        # Check pool resources health
        pool_resources = []
        while not self.pool.empty():
            resource = await self.pool.get()
            if await self._is_resource_healthy(resource):
                pool_resources.append(resource)
                healthy_resources += 1
            else:
                await self._dispose_resource(resource)
        
        # Return healthy resources to pool
        for resource in pool_resources:
            await self.pool.put(resource)
        
        return PoolHealthStatus(
            total_resources=len(self.active_resources) + self.pool.qsize(),
            healthy_resources=healthy_resources,
            active_resources=len(self.active_resources),
            pool_size=self.pool.qsize()
        )
```

---

## 📊 **Data Processing Patterns**

### **1. Pipeline Processing Pattern**
```python
# Configurable Data Processing Pipeline
class PipelineProcessingPattern:
    """
    Configurable pipeline for data processing with error recovery
    """
    
    def __init__(self):
        self.stages: List[StageInterface] = []
        self.error_handlers: Dict[str, ErrorHandler] = {}
        self.middleware: List[Middleware] = []
    
    def add_stage(self, stage: StageInterface, name: str):
        """Add processing stage to pipeline"""
        self.stages.append(stage)
        self.error_handlers[name] = DefaultErrorHandler()
    
    def add_middleware(self, middleware: Middleware):
        """Add middleware to pipeline"""
        self.middleware.append(middleware)
    
    async def execute_pipeline(self, input_data: Any, context: PipelineContext) -> PipelineResult:
        """Execute complete pipeline with middleware and error handling"""
        
        current_data = input_data
        
        try:
            # 🔹 Pre-processing Middleware
            for middleware in self.middleware:
                current_data = await middleware.before_pipeline(current_data, context)
            
            # 🔹 Stage-by-Stage Processing
            stage_results = {}
            
            for i, stage in enumerate(self.stages):
                stage_name = f"stage_{i}"
                
                try:
                    # Pre-stage middleware
                    for middleware in self.middleware:
                        current_data = await middleware.before_stage(
                            current_data, context, stage_name
                        )
                    
                    # Stage execution
                    stage_result = await stage.execute(current_data, context)
                    stage_results[stage_name] = stage_result
                    
                    # Validate stage output
                    if not await self._validate_stage_output(stage_result, stage):
                        raise StageValidationError(f"Stage {stage_name} output validation failed")
                    
                    current_data = stage_result.data
                    
                    # Post-stage middleware
                    for middleware in self.middleware:
                        current_data = await middleware.after_stage(
                            current_data, context, stage_name
                        )
                
                except Exception as e:
                    #
