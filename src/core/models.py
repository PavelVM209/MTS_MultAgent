"""
Data Models for MTS_MultAgent

This module contains Pydantic models for data validation and serialization
across all agents in the system.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator


# Jira Models
class JiraTask(BaseModel):
    """Task model for Jira operations."""
    project_key: str = Field(..., description="Jira project key")
    task_description: str = Field(..., description="Task description")
    search_keywords: List[str] = Field(default_factory=list, description="Keywords to search")
    date_range: Optional[Dict[str, str]] = Field(None, description="Date range filter")
    jql_query: Optional[str] = Field(None, description="Custom JQL query")
    max_results: int = Field(default=50, description="Maximum results to return")

    @validator('project_key')
    def validate_project_key(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Project key cannot be empty')
        return v.upper().strip()


class JiraIssue(BaseModel):
    """Jira issue model."""
    id: str = Field(..., description="Issue ID")
    key: str = Field(..., description="Issue key")
    summary: str = Field(..., description="Issue summary")
    description: Optional[str] = Field(None, description="Issue description")
    status: str = Field(..., description="Issue status")
    assignee: Optional[str] = Field(None, description="Assignee display name")
    reporter: Optional[str] = Field(None, description="Reporter display name")
    created: datetime = Field(..., description="Creation date")
    updated: datetime = Field(..., description="Last update date")
    issue_type: str = Field(..., description="Issue type")
    priority: Optional[str] = Field(None, description="Issue priority")
    labels: List[str] = Field(default_factory=list, description="Issue labels")
    components: List[str] = Field(default_factory=list, description="Issue components")


class JiraComment(BaseModel):
    """Jira comment model."""
    id: str = Field(..., description="Comment ID")
    author: str = Field(..., description="Comment author")
    body: str = Field(..., description="Comment body")
    created: datetime = Field(..., description="Creation date")
    updated: Optional[datetime] = Field(None, description="Last update date")


class JiraMeetingProtocol(BaseModel):
    """Meeting protocol extracted from Jira."""
    issue_id: str = Field(..., description="Related issue ID")
    title: str = Field(..., description="Protocol title")
    content: str = Field(..., description="Protocol content")
    date: datetime = Field(..., description="Protocol date")
    attendees: List[str] = Field(default_factory=list, description="Meeting attendees")
    action_items: List[str] = Field(default_factory=list, description="Action items")


class JiraResult(BaseModel):
    """Result model for Jira operations."""
    issues: List[JiraIssue] = Field(default_factory=list, description="Found issues")
    meeting_protocols: List[JiraMeetingProtocol] = Field(default_factory=list, description="Meeting protocols")
    comments: List[JiraComment] = Field(default_factory=list, description="Extracted comments")
    total_count: int = Field(default=0, description="Total count of items found")
    extracted_context: str = Field(default="", description="Extracted text context")
    search_summary: Dict[str, Any] = Field(default_factory=dict, description="Search summary")


# Context Analysis Models
class ContextTask(BaseModel):
    """Task model for context analysis."""
    text_content: Optional[str] = Field(None, description="Main text content")
    task_description: str = Field(..., description="Original task description")
    search_keywords: List[str] = Field(default_factory=list, description="Keywords to search for")
    meeting_protocols: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Meeting protocols")
    additional_documents: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Additional documents")


class ExtractedEntity(BaseModel):
    """Extracted entity model."""
    text: str = Field(..., description="Entity text")
    label: str = Field(..., description="Entity label/type")
    start: int = Field(..., description="Start position in text")
    end: int = Field(..., description="End position in text")
    confidence: float = Field(..., description="Confidence score")
    context: str = Field(..., description="Context where entity was found")


class TextSummary(BaseModel):
    """Text summary model."""
    summary: str = Field(..., description="Generated summary")
    bullet_points: List[str] = Field(default_factory=list, description="Key bullet points")
    key_topics: List[str] = Field(default_factory=list, description="Key topics")
    word_count: int = Field(default=0, description="Total word count")


class ContextResult(BaseModel):
    """Result model for context analysis."""
    entities: List[ExtractedEntity] = Field(default_factory=list, description="Extracted entities")
    key_phrases: List[str] = Field(default_factory=list, description="Key phrases")
    relevant_context: List[str] = Field(default_factory=list, description="Relevant context sections")
    summary: TextSummary = Field(..., description="Text summary")
    language: str = Field(..., description="Detected language")
    relevance_scores: Dict[str, float] = Field(default_factory=dict, description="Relevance scores")
    analysis_timestamp: datetime = Field(..., description="Analysis timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# Excel Models
class ExcelTask(BaseModel):
    """Task model for Excel operations."""
    file_paths: List[str] = Field(..., description="Paths to Excel files")
    sheet_names: Optional[List[str]] = Field(None, description="Sheet names to process")
    cell_ranges: Optional[List[str]] = Field(None, description="Cell ranges to extract")
    headers_row: Optional[int] = Field(None, description="Row number containing headers")

    @validator('file_paths')
    def validate_file_paths(cls, v):
        if not v:
            raise ValueError('At least one file path must be provided')
        return v


class ExcelData(BaseModel):
    """Excel data model."""
    sheet_name: str = Field(..., description="Sheet name")
    file_path: str = Field(..., description="Source file path")
    data: List[Dict[str, Any]] = Field(..., description="Row data")
    columns: List[str] = Field(..., description="Column names")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ExcelSheet(BaseModel):
    """Excel sheet information model."""
    name: str = Field(..., description="Sheet name")
    rows_count: int = Field(..., description="Number of rows")
    columns_count: int = Field(..., description="Number of columns")
    data_type: str = Field(default="tabular", description="Type of data")
    extraction_method: str = Field(default="pandas", description="Extraction method used")


class ExcelTable(BaseModel):
    """Excel table model."""
    name: str = Field(..., description="Table name")
    headers: List[str] = Field(..., description="Column headers")
    rows: List[List[Any]] = Field(..., description="Table rows")
    sheet_name: str = Field(..., description="Source sheet name")
    row_count: int = Field(..., description="Number of rows")
    column_count: int = Field(..., description="Number of columns")


class ExcelMatch(BaseModel):
    """Excel search match model."""
    file_path: str = Field(..., description="Source file path")
    sheet_name: str = Field(..., description="Sheet name")
    cell_address: str = Field(..., description="Cell address (e.g., 'A1')")
    value: Any = Field(..., description="Cell value")
    query: str = Field(..., description="Query that matched")
    context: List[str] = Field(default_factory=list, description="Surrounding context")


class ExcelResult(BaseModel):
    """Result model for Excel operations."""
    sheets: List[ExcelData] = Field(default_factory=list, description="Extracted sheet data")
    total_rows: int = Field(default=0, description="Total rows extracted")
    total_sheets: int = Field(default=0, description="Total sheets processed")
    file_paths: List[str] = Field(default_factory=list, description="Processed file paths")
    extraction_timestamp: datetime = Field(..., description="Extraction timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# Comparison Models
class ComparisonTask(BaseModel):
    """Task model for comparison operations."""
    jira_data: JiraResult = Field(..., description="Data from Jira")
    excel_data: ExcelResult = Field(..., description="Data from Excel")
    context_data: ContextResult = Field(..., description="Data from context analysis")
    comparison_criteria: List[str] = Field(default_factory=list, description="Criteria to compare")


class ComparisonItem(BaseModel):
    """Individual comparison item."""
    criterion: str = Field(..., description="Comparison criterion")
    jira_value: Any = Field(..., description="Value from Jira")
    excel_value: Any = Field(..., description="Value from Excel")
    match: bool = Field(..., description="Whether values match")
    confidence: float = Field(..., description="Match confidence")
    notes: str = Field(default="", description="Additional notes")


class Discrepancy(BaseModel):
    """Discrepancy model."""
    type: str = Field(..., description="Discrepancy type")
    jira_data: Any = Field(..., description="Jira data")
    excel_data: Any = Field(..., description="Excel data")
    description: str = Field(..., description="Discrepancy description")
    severity: str = Field(default="medium", description="Severity level")


class ComparisonResult(BaseModel):
    """Result model for comparison operations."""
    comparisons: List[ComparisonItem] = Field(default_factory=list, description="Comparison items")
    discrepancies: List[Discrepancy] = Field(default_factory=list, description="Found discrepancies")
    insights: List[str] = Field(default_factory=list, description="Generated insights")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="Confidence scores")
    summary_report: str = Field(default="", description="Summary report")


# Confluence Models
class ConfluenceTask(BaseModel):
    """Task model for Confluence operations."""
    space_key: str = Field(..., description="Confluence space key")
    parent_page_id: int = Field(..., description="Parent page ID")
    title: str = Field(..., description="Page title")
    content: str = Field(..., description="Page content")
    tables: List[ExcelTable] = Field(default_factory=list, description="Tables to include")
    comments: List[str] = Field(default_factory=list, description="Comments to add")

    @validator('title')
    def validate_title(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Page title cannot be empty')
        return v.strip()


class ConfluencePage(BaseModel):
    """Confluence page model."""
    id: str = Field(..., description="Page ID")
    title: str = Field(..., description="Page title")
    url: str = Field(..., description="Page URL")
    space_key: str = Field(..., description="Space key")
    version: int = Field(..., description="Page version")


class ConfluenceResult(BaseModel):
    """Result model for Confluence operations."""
    page_id: str = Field(..., description="Created page ID")
    page_url: str = Field(..., description="Page URL")
    success: bool = Field(..., description="Operation success")
    created_at: datetime = Field(..., description="Creation timestamp")
    version: int = Field(..., description="Page version")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# Workflow Models
class WorkflowTask(BaseModel):
    """Complete workflow task model."""
    description: str = Field(..., description="Task description")
    project_key: Optional[str] = Field(None, description="Project key")
    keywords: List[str] = Field(default_factory=list, description="Keywords")
    date_range: Optional[Dict[str, str]] = Field(None, description="Date range")
    excel_files: List[str] = Field(default_factory=list, description="Excel file paths")


class WorkflowResult(BaseModel):
    """Complete workflow result model."""
    success: bool = Field(..., description="Overall success")
    jira_result: Optional[JiraResult] = Field(None, description="Jira operation result")
    context_result: Optional[ContextResult] = Field(None, description="Context analysis result")
    excel_result: Optional[ExcelResult] = Field(None, description="Excel operation result")
    comparison_result: Optional[ComparisonResult] = Field(None, description="Comparison result")
    confluence_result: Optional[ConfluenceResult] = Field(None, description="Confluence result")
    execution_summary: Dict[str, Any] = Field(default_factory=dict, description="Execution summary")
    errors: List[str] = Field(default_factory=list, description="Errors encountered")


# Error Models
class ErrorDetail(BaseModel):
    """Error detail model."""
    agent_name: str = Field(..., description="Agent that generated error")
    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    context: Dict[str, Any] = Field(default_factory=dict, description="Error context")


# Validation Models
class ValidationResult(BaseModel):
    """Validation result model."""
    is_valid: bool = Field(..., description="Whether validation passed")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")


# LLM-Enhanced Models for New Architecture

class ExcelColumnInfo(BaseModel):
    """Information about Excel column for LLM analysis."""
    column_name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="Data type")
    sample_values: List[Any] = Field(default_factory=list, description="Sample values")
    null_count: int = Field(default=0, description="Number of null values")
    unique_count: int = Field(default=0, description="Number of unique values")
    semantic_meaning: Optional[str] = Field(None, description="LLM-derived semantic meaning")
    relevance_score: float = Field(default=0.0, description="Relevance to analysis (0-100)")
    analysis_suggestions: List[str] = Field(default_factory=list, description="Analysis suggestions")


class IntelligentQuery(BaseModel):
    """LLM-generated intelligent query for Excel data."""
    query_description: str = Field(..., description="Natural language description")
    sql_equivalent: Optional[str] = Field(None, description="SQL equivalent if applicable")
    target_columns: List[str] = Field(default_factory=list, description="Target columns")
    expected_output_format: str = Field(default="table", description="Expected output format")
    confidence_score: float = Field(default=0.0, description="Confidence in query correctness")


class LLMContextResult(BaseModel):
    """Enhanced context result with LLM insights."""
    entities: List[ExtractedEntity] = Field(default_factory=list, description="Extracted entities")
    key_phrases: List[str] = Field(default_factory=list, description="Key phrases")
    relevant_context: List[str] = Field(default_factory=list, description="Relevant context sections")
    summary: TextSummary = Field(..., description="Text summary")
    language: str = Field(..., description="Detected language")
    relevance_scores: Dict[str, float] = Field(default_factory=dict, description="Relevance scores")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # LLM-enhanced fields
    intelligent_queries: List[IntelligentQuery] = Field(default_factory=list, description="Generated queries")
    semantic_insights: List[str] = Field(default_factory=list, description="LLM semantic insights")
    data_relationships: Dict[str, List[str]] = Field(default_factory=dict, description="Data relationships")
    
    # Iterative improvement fields
    quality_metrics: Optional['QualityMetrics'] = Field(None, description="Quality evaluation")
    iteration_result: Optional['IterationResult'] = Field(None, description="Iteration data")


class LLMExcelResult(BaseModel):
    """Enhanced Excel result with LLM insights."""
    sheets: List[ExcelData] = Field(default_factory=list, description="Extracted sheet data")
    total_rows: int = Field(default=0, description="Total rows extracted")
    total_sheets: int = Field(default=0, description="Total sheets processed")
    file_paths: List[str] = Field(default_factory=list, description="Processed file paths")
    extraction_timestamp: datetime = Field(default_factory=datetime.now, description="Extraction timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # LLM-enhanced fields
    column_analysis: List[ExcelColumnInfo] = Field(default_factory=list, description="Column analysis")
    intelligent_queries: List[IntelligentQuery] = Field(default_factory=list, description="Generated queries")
    query_results: List[Dict[str, Any]] = Field(default_factory=list, description="Query execution results")
    data_insights: List[str] = Field(default_factory=list, description="Data insights")
    
    # Real table data - CRITICAL requirement
    tables: List[Dict[str, Any]] = Field(default_factory=list, description="Real table results")


class LLMComparisonResult(BaseModel):
    """Enhanced comparison result with LLM insights."""
    comparisons: List[ComparisonItem] = Field(default_factory=list, description="Comparison items")
    discrepancies: List[Discrepancy] = Field(default_factory=list, description="Found discrepancies")
    insights: List[str] = Field(default_factory=list, description="Generated insights")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="Confidence scores")
    summary_report: str = Field(default="", description="Summary report")
    
    # LLM-enhanced fields
    intelligent_insights: List[str] = Field(default_factory=list, description="LLM-generated insights")
    contextual_analysis: str = Field(default="", description="Contextual analysis")
    predictive_recommendations: List[str] = Field(default_factory=list, description="Predictive recommendations")
    
    # Quality and iteration fields
    quality_metrics: Optional['QualityMetrics'] = Field(None, description="Quality evaluation")
    iteration_result: Optional['IterationResult'] = Field(None, description="Iteration data")


class LLMWorkflowResult(BaseModel):
    """Enhanced workflow result with LLM insights."""
    success: bool = Field(..., description="Overall success")
    jira_result: Optional[JiraResult] = Field(None, description="Jira operation result")
    context_result: Optional[LLMContextResult] = Field(None, description="Context analysis result")
    excel_result: Optional[LLMExcelResult] = Field(None, description="Excel operation result")
    comparison_result: Optional[LLMComparisonResult] = Field(None, description="Comparison result")
    confluence_result: Optional[ConfluenceResult] = Field(None, description="Confluence result")
    execution_summary: Dict[str, Any] = Field(default_factory=dict, description="Execution summary")
    errors: List[str] = Field(default_factory=list, description="Errors encountered")
    
    # Quality and performance metrics
    overall_quality_score: float = Field(default=0.0, description="Overall quality score")
    pipeline_efficiency: Dict[str, float] = Field(default_factory=dict, description="Pipeline efficiency metrics")
    llm_performance: Dict[str, Any] = Field(default_factory=dict, description="LLM performance data")


# Forward declarations for circular imports
from .llm_client import QualityMetrics, IterationResult
