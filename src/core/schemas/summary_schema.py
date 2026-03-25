"""
Summary Schemas for Scheduled Architecture

Validates JSON data structure for DailySummaryAgent and WeeklyReporter outputs.
"""

from typing import Dict, Any, List
from datetime import datetime, date
from .base_schema import BaseSchema, ValidationResult, ValidationPatterns, ValidationUtils


class DailySummarySchema(BaseSchema):
    """Schema for validating daily summary data from DailySummaryAgent"""
    
    def __init__(self):
        super().__init__("daily_summary")
    
    async def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate daily summary data structure.
        
        Expected structure:
        {
            "date": "2026-03-25",
            "generated_at": "2026-03-25T19:30:00",
            "data_sources": {
                "jira_data": {...},
                "meeting_data": {...}
            },
            "employee_performance": {...},
            "project_health": {...},
            "insights_and_recommendations": [...],
            "system_metrics": {...},
            "_metadata": {...}
        }
        """
        result = ValidationResult(valid=True, errors=[], warnings=[])
        
        # 🔹 Required top-level fields
        required_fields = [
            "date", "generated_at", "data_sources", 
            "employee_performance", "project_health", "system_metrics"
        ]
        self._validate_required_fields(data, required_fields, result)
        
        # 🔹 Field type validation
        field_types = {
            "date": (str, date),
            "generated_at": (str, datetime),
            "data_sources": dict,
            "employee_performance": dict,
            "project_health": dict,
            "insights_and_recommendations": list,
            "system_metrics": dict
        }
        self._validate_field_types(data, field_types, result)
        
        # 🔹 String pattern validation
        field_patterns = {
            "date": ValidationPatterns.DATE,
            "generated_at": ValidationPatterns.ISO_DATETIME
        }
        self._validate_string_patterns(data, field_patterns, result)
        
        # 🔹 Validate data sources
        if "data_sources" in data:
            self._validate_data_sources(data["data_sources"], result)
        
        # 🔹 Validate employee performance
        if "employee_performance" in data:
            await self._validate_employee_performance(data["employee_performance"], result)
        
        # 🔹 Validate project health
        if "project_health" in data:
            self._validate_project_health(data["project_health"], result)
        
        # 🔹 Validate insights and recommendations
        if "insights_and_recommendations" in data:
            await self._validate_insights(data["insights_and_recommendations"], result)
        
        # 🔹 System metrics validation
        if "system_metrics" in data:
            self._validate_system_metrics(data["system_metrics"], result)
        
        # 🔹 Metadata validation
        if "_metadata" in data:
            self._validate_metadata(data["_metadata"], "daily_summary_data", result)
        
        return result
    
    def _validate_data_sources(self, data_sources: Dict[str, Any], result: ValidationResult):
        """Validate data sources structure"""
        required_sources = ["jira_data", "meeting_data"]
        self._validate_required_fields(data_sources, required_sources, result)
        
        for source_name, source_data in data_sources.items():
            if not isinstance(source_data, dict):
                result.add_error(
                    field=f"data_sources.{source_name}",
                    message="Data source must be dict",
                    value=source_data,
                    expected_type="dict"
                )
                continue
            
            # Check for required source metadata
            required_source_fields = ["last_updated", "quality_score", "record_count"]
            self._validate_required_fields(source_data, required_source_fields, result)
            
            # Validate quality score
            if "quality_score" in source_data:
                score = source_data["quality_score"]
                if not isinstance(score, (int, float)) or not (0 <= score <= 100):
                    result.add_error(
                        field=f"data_sources.{source_name}.quality_score",
                        message="Quality score must be percentage (0-100)",
                        value=score,
                        expected_type="percentage"
                    )
    
    async def _validate_employee_performance(
        self, 
        performance: Dict[str, Any], 
        result: ValidationResult
    ):
        """Validate employee performance structure"""
        if not performance:
            result.add_warning("No employee performance data found")
            return
        
        for username, employee_data in performance.items():
            if not isinstance(employee_data, dict):
                result.add_error(
                    field=f"employee_performance.{username}",
                    message="Employee performance must be dict",
                    value=employee_data,
                    expected_type="dict"
                )
                continue
            
            # Validate overall performance score
            if "overall_score" in employee_data:
                score = employee_data["overall_score"]
                if not ValidationUtils.is_valid_performance_score(score):
                    result.add_error(
                        field=f"employee_performance.{username}.overall_score",
                        message="Overall score must be between 0-10",
                        value=score,
                        expected_type="performance_score"
                    )
            
            # Validate performance dimensions
            dimensions = ["task_performance", "collaboration", "code_contribution"]
            for dimension in dimensions:
                if dimension in employee_data:
                    await self._validate_performance_dimension(
                        employee_data[dimension],
                        f"employee_performance.{username}.{dimension}",
                        result
                    )
            
            # Validate trend data if present
            if "trend_analysis" in employee_data:
                self._validate_trend_analysis(
                    employee_data["trend_analysis"],
                    f"employee_performance.{username}.trend_analysis",
                    result
                )
    
    async def _validate_performance_dimension(
        self, 
        dimension: Dict[str, Any], 
        field_prefix: str, 
        result: ValidationResult
    ):
        """Validate individual performance dimension"""
        if not isinstance(dimension, dict):
            result.add_error(
                field=field_prefix,
                message="Performance dimension must be dict",
                value=dimension,
                expected_type="dict"
            )
            return
        
        # Validate dimension score
        if "score" in dimension:
            score = dimension["score"]
            if not ValidationUtils.is_valid_performance_score(score):
                result.add_error(
                    field=f"{field_prefix}.score",
                    message="Dimension score must be between 0-10",
                    value=score,
                    expected_type="performance_score"
                )
        
        # Validate numeric metrics
        numeric_fields = ["tasks_completed", "meetings_attended", "commits_made"]
        for field in numeric_fields:
            if field in dimension:
                value = dimension[field]
                if not isinstance(value, int) or value < 0:
                    result.add_error(
                        field=f"{field_prefix}.{field}",
                        message=f"Metric must be non-negative integer",
                        value=value,
                        expected_type="int>=0"
                    )
    
    def _validate_trend_analysis(
        self, 
        trend: Dict[str, Any], 
        field_prefix: str, 
        result: ValidationResult
    ):
        """Validate trend analysis structure"""
        if not isinstance(trend, dict):
            result.add_error(
                field=field_prefix,
                message="Trend analysis must be dict",
                value=trend,
                expected_type="dict"
            )
            return
        
        # Validate trend direction
        if "direction" in trend:
            valid_directions = ["improving", "stable", "declining"]
            if trend["direction"] not in valid_directions:
                result.add_error(
                    field=f"{field_prefix}.direction",
                    message="Trend direction must be one of: improving, stable, declining",
                    value=trend["direction"],
                    expected_type="enum"
                )
        
        # Validate trend percentage
        if "change_percentage" in trend:
            change = trend["change_percentage"]
            if not isinstance(change, (int, float)) or not (-100 <= change <= 100):
                result.add_error(
                    field=f"{field_prefix}.change_percentage",
                    message="Change percentage must be between -100 and 100",
                    value=change,
                    expected_type="percentage"
                )
    
    def _validate_project_health(self, project_health: Dict[str, Any], result: ValidationResult):
        """Validate project health structure"""
        if not project_health:
            result.add_warning("No project health data found")
            return
        
        for project_key, health_data in project_health.items():
            if not isinstance(health_data, dict):
                result.add_error(
                    field=f"project_health.{project_key}",
                    message="Project health must be dict",
                    value=health_data,
                    expected_type="dict"
                )
                continue
            
            # Validate overall health score
            if "overall_health" in health_data:
                score = health_data["overall_health"]
                if not ValidationUtils.is_valid_performance_score(score):
                    result.add_error(
                        field=f"project_health.{project_key}.overall_health",
                        message="Project health score must be between 0-10",
                        value=score,
                        expected_type="performance_score"
                    )
            
            # Validate health metrics
            health_metrics = ["velocity", "blocker_count", "team_utilization"]
            for metric in health_metrics:
                if metric in health_data:
                    value = health_data[metric]
                    if metric == "blocker_count":
                        if not isinstance(value, int) or value < 0:
                            result.add_error(
                                field=f"project_health.{project_key}.{metric}",
                                message=f"{metric} must be non-negative integer",
                                value=value,
                                expected_type="int>=0"
                            )
                    else:  # velocity, team_utilization
                        if not isinstance(value, (int, float)) or not (0 <= value <= 100):
                            result.add_error(
                                field=f"project_health.{project_key}.{metric}",
                                message=f"{metric} must be percentage (0-100)",
                                value=value,
                                expected_type="percentage"
                            )
            
            # Validate risk indicators if present
            if "risk_indicators" in health_data:
                self._validate_risk_indicators(
                    health_data["risk_indicators"],
                    f"project_health.{project_key}.risk_indicators",
                    result
                )
    
    def _validate_risk_indicators(
        self, 
        risks: List[Dict[str, Any]], 
        field_prefix: str, 
        result: ValidationResult
    ):
        """Validate risk indicators"""
        for i, risk in enumerate(risks):
            if not isinstance(risk, dict):
                result.add_error(
                    field=f"{field_prefix}[{i}]",
                    message="Risk indicator must be dict",
                    value=risk,
                    expected_type="dict"
                )
                continue
            
            # Validate risk fields
            required_fields = ["type", "severity", "description"]
            self._validate_required_fields(risk, required_fields, result)
            
            # Validate severity
            if "severity" in risk:
                valid_severities = ["low", "medium", "high", "critical"]
                if risk["severity"] not in valid_severities:
                    result.add_error(
                        field=f"{field_prefix}[{i}].severity",
                        message="Severity must be one of: low, medium, high, critical",
                        value=risk["severity"],
                        expected_type="enum"
                    )
    
    async def _validate_insights(
        self, 
        insights: List[Dict[str, Any]], 
        result: ValidationResult
    ):
        """Validate insights and recommendations"""
        for i, insight in enumerate(insights):
            if not isinstance(insight, dict):
                result.add_error(
                    field=f"insights_and_recommendations[{i}]",
                    message="Insight must be dict",
                    value=insight,
                    expected_type="dict"
                )
                continue
            
            # Validate insight fields
            required_fields = ["type", "content", "priority"]
            self._validate_required_fields(insight, required_fields, result)
            
            # Validate type
            if "type" in insight:
                valid_types = [
                    "performance_improvement", "risk_alert", "optimization_opportunity",
                    "collaboration_insight", "productivity_trend"
                ]
                if insight["type"] not in valid_types:
                    result.add_warning(
                        f"Insight type '{insight['type']}' at insights_and_recommendations[{i}].type may not be standard"
                    )
            
            # Validate priority
            if "priority" in insight:
                valid_priorities = ["low", "medium", "high"]
                if insight["priority"] not in valid_priorities:
                    result.add_error(
                        field=f"insights_and_recommendations[{i}].priority",
                        message="Priority must be one of: low, medium, high",
                        value=insight["priority"],
                        expected_type="enum"
                    )
    
    def _validate_system_metrics(self, metrics: Dict[str, Any], result: ValidationResult):
        """Validate system metrics structure"""
        required_metrics = ["data_processing_time", "quality_score", "insights_generated"]
        self._validate_required_fields(metrics, required_metrics, result)
        
        # Validate numeric metrics
        numeric_ranges = {
            "data_processing_time": (0, 3600),  # Max 1 hour
            "quality_score": (0, 100),  # Percentage
            "insights_generated": (0, 50)  # Reasonable max
        }
        self._validate_numeric_ranges(metrics, numeric_ranges, result)
    
    def _validate_metadata(
        self, 
        metadata: Dict[str, Any], 
        expected_type: str, 
        result: ValidationResult
    ):
        """Validate metadata structure"""
        required_metadata = ["data_type", "persisted_at", "persisted_by", "version"]
        self._validate_required_fields(metadata, required_metadata, result)
        
        if "data_type" in metadata:
            if metadata["data_type"] != expected_type:
                result.add_error(
                    field="_metadata.data_type",
                    message=f"Incorrect data type for daily summary",
                    value=metadata["data_type"],
                    expected_type=expected_type
                )


class WeeklySummarySchema(BaseSchema):
    """Schema for validating weekly summary data from WeeklyReporter"""
    
    def __init__(self):
        super().__init__("weekly_summary")
    
    async def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate weekly summary data structure.
        
        Expected structure includes daily summaries aggregation,
        trend analysis, and strategic insights.
        """
        result = ValidationResult(valid=True, errors=[], warnings=[])
        
        # 🔹 Required top-level fields
        required_fields = [
            "week_start", "week_end", "period", "generated_at",
            "aggregated_metrics", "trend_analysis", "strategic_insights", "system_metrics"
        ]
        self._validate_required_fields(data, required_fields, result)
        
        # 🔹 Field type validation
        field_types = {
            "week_start": (str, date),
            "week_end": (str, date),
            "period": str,
            "generated_at": (str, datetime),
            "aggregated_metrics": dict,
            "trend_analysis": dict,
            "strategic_insights": list,
            "system_metrics": dict
        }
        self._validate_field_types(data, field_types, result)
        
        # 🔹 Date validation
        for date_field in ["week_start", "week_end"]:
            if date_field in data and isinstance(data[date_field], str):
                if not ValidationUtils.is_valid_date(data[date_field]):
                    result.add_error(
                        field=date_field,
                        message="Invalid date format (expected YYYY-MM-DD)",
                        value=data[date_field],
                        expected_type="date_string"
                    )
        
        # 🔹 Validate period format
        if "period" in data:
            if not data["period"].startswith("W") or len(data["period"]) < 8:
                result.add_error(
                    field="period",
                    message="Period must be in format like 'W12-2026'",
                    value=data["period"],
                    expected_type="week_period"
                )
        
        # 🔹 Validate aggregated metrics
        if "aggregated_metrics" in data:
            self._validate_aggregated_metrics(data["aggregated_metrics"], result)
        
        # 🔹 Validate trend analysis
        if "trend_analysis" in data:
            await self._validate_weekly_trend_analysis(data["trend_analysis"], result)
        
        # 🔹 Validate strategic insights
        if "strategic_insights" in data:
            await self._validate_strategic_insights(data["strategic_insights"], result)
        
        # 🔹 System metrics validation
        if "system_metrics" in data:
            self._validate_weekly_system_metrics(data["system_metrics"], result)
        
        # 🔹 Metadata validation
        if "_metadata" in data:
            self._validate_metadata(data["_metadata"], "weekly_summary_data", result)
        
        return result
    
    def _validate_aggregated_metrics(self, metrics: Dict[str, Any], result: ValidationResult):
        """Validate aggregated metrics structure"""
        required_categories = ["employee_performance", "project_health", "productivity"]
        self._validate_required_fields(metrics, required_categories, result)
        
        for category, category_data in metrics.items():
            if not isinstance(category_data, dict):
                result.add_error(
                    field=f"aggregated_metrics.{category}",
                    message="Metrics category must be dict",
                    value=category_data,
                    expected_type="dict"
                )
                continue
            
            # Validate summary statistics
            summary_fields = ["average", "min", "max", "trend"]
            for field in summary_fields:
                if field in category_data:
                    if field in ["average", "min", "max"]:
                        value = category_data[field]
                        if not ValidationUtils.is_valid_performance_score(value):
                            result.add_error(
                                field=f"aggregated_metrics.{category}.{field}",
                                message=f"{field} must be score between 0-10",
                                value=value,
                                expected_type="performance_score"
                            )
                    elif field == "trend":
                        valid_trends = ["improving", "stable", "declining"]
                        if category_data[field] not in valid_trends:
                            result.add_error(
                                field=f"aggregated_metrics.{category}.{field}",
                                message="Trend must be one of: improving, stable, declining",
                                value=category_data[field],
                                expected_type="enum"
                            )
    
    async def _validate_weekly_trend_analysis(
        self, 
        trend_analysis: Dict[str, Any], 
        result: ValidationResult
    ):
        """Validate weekly trend analysis structure"""
        trend_categories = ["employee_trends", "project_trends", "productivity_trends"]
        
        for category, category_data in trend_analysis.items():
            if category in trend_analysis:
                if not isinstance(category_data, dict):
                    result.add_error(
                        field=f"trend_analysis.{category}",
                        message="Trend category must be dict",
                        value=category_data,
                        expected_type="dict"
                    )
                    continue
                
                # Validate trend items
                if "trends" in category_data:
                    if not isinstance(category_data["trends"], list):
                        result.add_error(
                            field=f"trend_analysis.{category}.trends",
                            message="Trends must be list",
                            value=category_data["trends"],
                            expected_type="list"
                        )
    
    async def _validate_strategic_insights(
        self, 
        insights: List[Dict[str, Any]], 
        result: ValidationResult
    ):
        """Validate strategic insights structure"""
        for i, insight in enumerate(insights):
            if not isinstance(insight, dict):
                result.add_error(
                    field=f"strategic_insights[{i}]",
                    message="Strategic insight must be dict",
                    value=insight,
                    expected_type="dict"
                )
                continue
            
            # Validate strategic insight fields
            required_fields = ["type", "impact_level", "description", "recommendations"]
            self._validate_required_fields(insight, required_fields, result)
            
            # Validate impact level
            if "impact_level" in insight:
                valid_impacts = ["low", "medium", "high", "strategic"]
                if insight["impact_level"] not in valid_impacts:
                    result.add_error(
                        field=f"strategic_insights[{i}].impact_level",
                        message="Impact level must be one of: low, medium, high, strategic",
                        value=insight["impact_level"],
                        expected_type="enum"
                    )
            
            # Validate recommendations
            if "recommendations" in insight:
                if not isinstance(insight["recommendations"], list):
                    result.add_error(
                        field=f"strategic_insights[{i}].recommendations",
                        message="Recommendations must be list",
                        value=insight["recommendations"],
                        expected_type="list"
                    )
    
    def _validate_weekly_system_metrics(self, metrics: Dict[str, Any], result: ValidationResult):
        """Validate weekly system metrics structure"""
        required_metrics = ["days_processed", "data_processing_time", "quality_score", "insights_generated"]
        self._validate_required_fields(metrics, required_metrics, result)
        
        # Validate numeric metrics
        numeric_ranges = {
            "days_processed": (1, 7),  # Week should have 1-7 days
            "data_processing_time": (0, 7200),  # Max 2 hours for week
            "quality_score": (0, 100),  # Percentage
            "insights_generated": (0, 100)  # Reasonable max for week
        }
        self._validate_numeric_ranges(metrics, numeric_ranges, result)
