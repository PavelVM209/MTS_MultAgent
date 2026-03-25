"""
Universal Analyzer Agent for MTS MultAgent System

This agent provides intelligent analysis using LLM:
- Extracts and refines keywords from Jira tasks
- Enriches context with meeting protocols
- Sends structured context + Excel metadata to LLM for analysis
- Generates high-quality insights and recommendations
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import structlog

logger = structlog.get_logger()


class UniversalAnalyzerAgent:
    """
    Universal analyzer that uses LLM for intelligent data analysis.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the universal analyzer."""
        self.config = config
        self.name = "UniversalAnalyzer"
        
    async def analyze_with_context(
        self,
        jira_keywords: List[str],
        context_data: Dict[str, Any],
        excel_metadata: Dict[str, Any],
        excel_sample: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform intelligent analysis using context and Excel data.
        
        Args:
            jira_keywords: Keywords extracted from Jira task
            context_data: Refined context from meeting protocols
            excel_metadata: Excel structure information (columns, sheets, etc.)
            excel_sample: Sample data rows from Excel
            
        Returns:
            Dictionary with insights and recommendations
        """
        try:
            # Prepare comprehensive analysis request
            analysis_request = self._prepare_analysis_request(
                jira_keywords, context_data, excel_metadata, excel_sample
            )
            
            # Here we would send to LLM service
            # For now, simulate intelligent analysis
            analysis_result = await self._simulate_llm_analysis(analysis_request)
            
            logger.info("Universal analysis completed", insights_count=len(analysis_result.get("insights", [])))
            
            return analysis_result
            
        except Exception as e:
            logger.error("Universal analysis failed", error=str(e))
            return {
                "insights": [],
                "recommendations": [],
                "error": str(e)
            }
    
    def _prepare_analysis_request(
        self,
        jira_keywords: List[str],
        context_data: Dict[str, Any],
        excel_metadata: Dict[str, Any],
        excel_sample: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Prepare structured analysis request for LLM.
        """
        return {
            "task_context": {
                "keywords": jira_keywords,
                "analysis_type": self._determine_analysis_type(jira_keywords),
                "priority_areas": self._identify_priority_areas(jira_keywords, context_data)
            },
            "business_context": {
                "relevant_sections": context_data.get("sections", [])[:3],  # Top 3 sections
                "entities": context_data.get("entities", []),
                "key_topics": context_data.get("key_phrases", [])[:10]  # Top 10 phrases
            },
            "data_structure": {
                "available_sheets": excel_metadata.get("sheets", []),
                "columns_by_sheet": excel_metadata.get("columns", {}),
                "data_types": self._identify_column_types(excel_sample),
                "data_volume": {
                    "total_rows": excel_metadata.get("total_rows", 0),
                    "sample_size": len(excel_sample)
                }
            },
            "sample_data": excel_sample[:5],  # First 5 rows for context
            "analysis_requirements": {
                "focus_on": self._determine_focus_areas(jira_keywords, context_data),
                "comparison_needs": self._identify_comparison_needs(excel_metadata),
                "trend_analysis": self._needs_trend_analysis(excel_metadata, context_data)
            }
        }
    
    def _determine_analysis_type(self, keywords: List[str]) -> str:
        """Determine the type of analysis based on keywords."""
        keyword_text = " ".join(keywords).lower()
        
        if any(word in keyword_text for word in ["финансов", "прибыл", "доход", "рентабельность", "ebitda"]):
            return "financial_analysis"
        elif any(word in keyword_text for word in ["производител", "эффективност", "оптимизаци"]):
            return "performance_analysis"
        elif any(word in keyword_text for word in ["сравнен", "анализ", "компани"]):
            return "comparative_analysis"
        elif any(word in keyword_text for word in ["продаж", "выручк", "сбыт"]):
            return "sales_analysis"
        else:
            return "general_analysis"
    
    def _identify_priority_areas(self, keywords: List[str], context: Dict[str, Any]) -> List[str]:
        """Identify priority areas for analysis."""
        areas = []
        keyword_text = " ".join(keywords).lower()
        context_text = " ".join(context.get("sections", [])).lower()
        combined_text = keyword_text + " " + context_text
        
        if "рентабельност" in combined_text:
            areas.append("profitability_analysis")
        if "эффективност" in combined_text:
            areas.append("efficiency_metrics")
        if "рост" in combined_text or "динамик" in combined_text:
            areas.append("growth_trends")
        if "сравнен" in combined_text:
            areas.append("comparative_metrics")
        if "оптимизац" in combined_text:
            areas.append("optimization_opportunities")
        
        return areas or ["general_insights"]
    
    def _identify_column_types(self, sample_data: List[Dict[str, Any]]) -> Dict[str, str]:
        """Identify the types of columns in the data."""
        if not sample_data:
            return {}
        
        column_types = {}
        first_row = sample_data[0]
        
        for col_name, value in first_row.items():
            if isinstance(value, str):
                if any(word in col_name.lower() for word in ["дата", "период", "время"]):
                    column_types[col_name] = "date"
                elif any(word in col_name.lower() for word in ["компани", "стран", "регион"]):
                    column_types[col_name] = "categorical"
                else:
                    column_types[col_name] = "text"
            elif isinstance(value, (int, float)):
                if any(word in col_name.lower() for word in ["руб", "долл", "$", "€"]):
                    column_types[col_name] = "currency"
                elif any(word in col_name.lower() for word in ["%", "процент"]):
                    column_types[col_name] = "percentage"
                else:
                    column_types[col_name] = "numeric"
        
        return column_types
    
    def _determine_focus_areas(self, keywords: List[str], context: Dict[str, Any]) -> List[str]:
        """Determine what to focus on in the analysis."""
        focus_areas = []
        
        # Extract business focus from keywords
        if "рентабельност" in " ".join(keywords).lower():
            focus_areas.append("profitability_drivers")
        if "затрат" in " ".join(keywords).lower():
            focus_areas.append("cost_structure")
        if "эффективност" in " ".join(keywords).lower():
            focus_areas.append("efficiency_metrics")
        
        # Extract from context
        context_text = " ".join(context.get("key_phrases", [])).lower()
        if "рост" in context_text:
            focus_areas.append("growth_factors")
        if "проблем" in context_text:
            focus_areas.append("problem_areas")
        
        return focus_areas or ["key_metrics"]
    
    def _identify_comparison_needs(self, excel_metadata: Dict[str, Any]) -> bool:
        """Check if comparative analysis is needed."""
        columns = []
        for sheet_cols in excel_metadata.get("columns", {}).values():
            columns.extend(sheet_cols)
        
        return any("компани" in col.lower() for col in columns)
    
    def _needs_trend_analysis(self, excel_metadata: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if trend analysis is needed."""
        columns = []
        for sheet_cols in excel_metadata.get("columns", {}).values():
            columns.extend(sheet_cols)
        
        has_time = any(word in col.lower() for word in ["период", "дата", "месяц", "квартал"] for col in columns)
        context_mentions_growth = any("рост" in section.lower() or "динамик" in section.lower() 
                                   for section in context.get("sections", []))
        
        return has_time or context_mentions_growth
    
    async def _simulate_llm_analysis(self, analysis_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate LLM analysis. In production, this would call actual LLM service.
        """
        # Extract key information
        task_type = analysis_request["task_context"]["analysis_type"]
        focus_areas = analysis_request["analysis_requirements"]["focus_on"]
        data_structure = analysis_request["data_structure"]
        sample_data = analysis_request["sample_data"]
        
        insights = []
        recommendations = []
        
        # Generate insights based on analysis type and data
        if task_type == "financial_analysis" and sample_data:
            insights.extend(self._generate_financial_insights(sample_data, focus_areas))
            recommendations.extend(self._generate_financial_recommendations(sample_data, focus_areas))
        
        elif task_type == "comparative_analysis" and sample_data:
            insights.extend(self._generate_comparative_insights(sample_data, data_structure))
            recommendations.extend(self._generate_comparative_recommendations(sample_data))
        
        elif task_type == "performance_analysis":
            insights.extend(self._generate_performance_insights(sample_data, focus_areas))
            recommendations.extend(self._generate_performance_recommendations(sample_data))
        
        else:
            insights.extend(self._generate_general_insights(sample_data, focus_areas))
            recommendations.extend(self._generate_general_recommendations())
        
        return {
            "insights": insights,
            "recommendations": recommendations,
            "analysis_type": task_type,
            "confidence_score": 0.85,
            "data_summary": {
                "rows_analyzed": len(sample_data),
                "columns_analyzed": len(data_structure.get("columns", {})),
                "focus_areas": focus_areas
            }
        }
    
    def _generate_financial_insights(self, sample_data: List[Dict], focus_areas: List[str]) -> List[str]:
        """Generate financial insights."""
        insights = []
        
        if sample_data:
            # Look for financial metrics
            for row in sample_data:
                for col, val in row.items():
                    if "прибыл" in col.lower() and isinstance(val, (int, float)):
                        insights.append(f"Найдены данные по прибыли: {val}")
                    elif "выручк" in col.lower() and isinstance(val, (int, float)):
                        insights.append(f"Найдены данные по выручке: {val}")
        
        if "profitability_drivers" in focus_areas:
            insights.append("Анализ выявляет факторы рентабельности")
        
        return insights[:5]  # Return top 5 insights
    
    def _generate_financial_recommendations(self, sample_data: List[Dict], focus_areas: List[str]) -> List[str]:
        """Generate financial recommendations."""
        recommendations = []
        
        if "cost_structure" in focus_areas:
            recommendations.append("Проанализировать структуру затрат для оптимизации")
        
        if "profitability_drivers" in focus_areas:
            recommendations.append("Выявить драйверы рентабельности для увеличения прибыли")
        
        recommendations.append("Разработать план по улучшению финансовых показателей")
        
        return recommendations
    
    def _generate_comparative_insights(self, sample_data: List[Dict], data_structure: Dict) -> List[str]:
        """Generate comparative insights."""
        insights = []
        
        # Check for company comparisons
        if sample_data:
            companies = set()
            for row in sample_data:
                for col, val in row.items():
                    if "компани" in col.lower():
                        companies.add(str(val))
            
            if len(companies) > 1:
                insights.append(f"Данные позволяют сравнить {len(companies)} компании")
        
        return insights
    
    def _generate_comparative_recommendations(self, sample_data: List[Dict]) -> List[str]:
        """Generate comparative recommendations."""
        return [
            "Провести детальное сравнение показателей",
            "Выявить лучшие практики и области для улучшения",
            "Разработать стратегии на основе сравнительного анализа"
        ]
    
    def _generate_performance_insights(self, sample_data: List[Dict], focus_areas: List[str]) -> List[str]:
        """Generate performance insights."""
        insights = []
        
        if "efficiency_metrics" in focus_areas:
            insights.append("Выявлены метрики эффективности для анализа")
        
        if sample_data:
            insights.append("Данные содержат показатели производительности")
        
        return insights
    
    def _generate_performance_recommendations(self, sample_data: List[Dict]) -> List[str]:
        """Generate performance recommendations."""
        return [
            "Оптимизировать ключевые показатели эффективности",
            "Внедрить мониторинг производительности",
            "Разработать план по улучшению метрик"
        ]
    
    def _generate_general_insights(self, sample_data: List[Dict], focus_areas: List[str]) -> List[str]:
        """Generate general insights."""
        insights = []
        
        if sample_data:
            insights.append("Данные структурированы и готовы для анализа")
            insights.append(f"Найдено {len(sample_data)} записей для анализа")
        
        if focus_areas:
            insights.append(f"Акцент на анализе: {', '.join(focus_areas)}")
        
        return insights
    
    def _generate_general_recommendations(self) -> List[str]:
        """Generate general recommendations."""
        return [
            "Провести углубленный анализ данных",
            "Разработать план действий на основе результатов",
            "Внедрить регулярный мониторинг ключевых показателей"
        ]
