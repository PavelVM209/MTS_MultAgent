"""
LLM-Guided Excel Agent for MTS MultAgent System

This agent provides intelligent Excel processing with:
- Zero hardcoded column mappings - all analysis through LLM
- Intelligent structure analysis with semantic meaning
- LLM-generated queries for data extraction
- Real table data validation
- Iterative improvement until convergence
"""

import asyncio
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.core.base_agent import BaseAgent, AgentResult
from src.core.models import (
    ExcelTask, LLMExcelResult, ExcelData, ExcelSheet, ExcelColumnInfo,
    IntelligentQuery
)
from src.core.llm_client import LLMClient, get_llm_client, LLMRequest
from src.core.iterative_engine import IterativeEngine, get_iterative_engine
from src.core.quality_metrics import QualityEvaluator, get_quality_evaluator


class ExcelAgent(BaseAgent):
    """
    LLM-guided Excel Agent with intelligent structure analysis.
    
    Features:
    - 100% LLM-driven column analysis and query generation
    - Semantic meaning extraction for all columns
    - Intelligent query execution and validation
    - Real table data guarantee
    - Iterative improvement of analysis results
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize LLM-guided ExcelAgent."""
        super().__init__(config, "ExcelAgent")
        
        # Initialize LLM components
        self.llm_client = get_llm_client()
        self.iterative_engine = get_iterative_engine()
        self.quality_evaluator = get_quality_evaluator()
        
        # Configuration
        self.supported_formats = self.get_config_value("excel.supported_formats", [".xlsx", ".xls", ".xlsm"])
        self.max_rows = self.get_config_value("excel.max_rows", 10000)
        self.max_iterations = self.get_config_value("excel.max_iterations", 5)
        self.quality_threshold = self.get_config_value("excel.quality_threshold", 85.0)
        
        self.logger.info("LLM-guided ExcelAgent initialized")
    
    async def validate(self, task: Dict[str, Any]) -> bool:
        """Validate Excel task parameters."""
        try:
            excel_task = ExcelTask(**task)
            
            if not excel_task.file_paths:
                self.logger.error("At least one file path is required")
                return False
            
            # Check if files exist
            for file_path in excel_task.file_paths:
                path = Path(file_path)
                if not path.exists():
                    self.logger.error(f"File not found: {file_path}")
                    return False
                
                if path.suffix.lower() not in self.supported_formats:
                    self.logger.error(f"Unsupported format: {path.suffix}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error("Excel task validation failed", error=str(e))
            return False
    
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        """
        Execute LLM-guided Excel processing with iterative improvement.
        """
        excel_task = ExcelTask(**task)
        
        try:
            # Step 1: Basic Excel reading
            basic_data = await self._read_excel_files_basic(excel_task)
            
            # Step 2: LLM-driven structure analysis
            initial_analysis = await self._analyze_structure_with_llm(basic_data)
            
            # Step 3: Iterative improvement of analysis
            improved_analysis = await self.iterative_engine.improve_until_convergence(
                initial_data=initial_analysis,
                improve_function=self._improve_structure_analysis,
                expected_context=json.dumps(basic_data, ensure_ascii=False),
                task_requirements=[
                    "Accurate semantic meaning for all columns",
                    "Comprehensive data insights",
                    "Intelligent query generation",
                    "Real table data extraction"
                ]
            )
            
            # Step 4: Execute intelligent queries
            query_results = await self._execute_intelligent_queries(
                improved_analysis.data, excel_task.file_paths
            )
            
            # Step 5: Validate results
            validated_results = await self._validate_table_results(
                query_results, improved_analysis.data
            )
            
            # Create LLMExcelResult
            result = LLMExcelResult(
                sheets=basic_data["sheets"],
                total_rows=basic_data["total_rows"],
                total_sheets=basic_data["total_sheets"],
                file_paths=excel_task.file_paths,
                extraction_timestamp=datetime.now(),
                metadata={
                    "analysis_method": "llm_guided",
                    "quality_score": improved_analysis.quality_score,
                    "iterations": improved_analysis.iteration
                },
                column_analysis=improved_analysis.data.get("column_analysis", []),
                intelligent_queries=improved_analysis.data.get("intelligent_queries", []),
                query_results=validated_results,
                data_insights=improved_analysis.data.get("data_insights", []),
                tables=validated_results  # CRITICAL: Real table data
            )
            
            self.logger.info(
                "LLM-guided Excel processing completed",
                quality_score=improved_analysis.quality_score,
                iterations=improved_analysis.iteration,
                tables_generated=len(validated_results),
                columns_analyzed=len(result.column_analysis)
            )
            
            return AgentResult(
                success=True,
                data=result.dict(),
                agent_name=self.name,
                metadata={
                    "quality_score": improved_analysis.quality_score,
                    "iterations": improved_analysis.iteration,
                    "real_tables_count": len(validated_results)
                }
            )
            
        except Exception as e:
            self.logger.error("LLM-guided Excel execution failed", error=str(e), exc_info=True)
            return AgentResult(
                success=False,
                error=f"Excel execution failed: {str(e)}",
                agent_name=self.name
            )
    
    async def _read_excel_files_basic(self, task: ExcelTask) -> Dict[str, Any]:
        """Basic Excel reading without hardcoded logic."""
        extracted_data = []
        total_rows = 0
        total_sheets = 0
        
        for file_path in task.file_paths:
            try:
                # Read Excel file
                excel_file = pd.ExcelFile(file_path)
                
                for sheet_name in excel_file.sheet_names:
                    try:
                        # Read sheet with automatic header detection
                        df = pd.read_excel(
                            file_path,
                            sheet_name=sheet_name,
                            nrows=self.max_rows
                        )
                        
                        # Clean data
                        df = df.dropna(how='all')
                        df = df.fillna('')
                        
                        # Convert to records
                        data = df.to_dict('records')
                        columns = df.columns.tolist()
                        
                        # Create ExcelData
                        sheet_data = ExcelData(
                            sheet_name=sheet_name,
                            file_path=file_path,
                            data=data,
                            columns=columns,
                            metadata={
                                "shape": df.shape,
                                "dtypes": df.dtypes.to_dict(),
                                "sample_data": data[:3] if data else []
                            }
                        )
                        
                        extracted_data.append(sheet_data)
                        total_rows += len(data)
                        total_sheets += 1
                        
                    except Exception as e:
                        self.logger.error(f"Failed to read sheet {sheet_name}: {e}")
                        continue
                
                excel_file.close()
                
            except Exception as e:
                self.logger.error(f"Failed to read file {file_path}: {e}")
                continue
        
        return {
            "sheets": extracted_data,
            "total_rows": total_rows,
            "total_sheets": total_sheets
        }
    
    async def _analyze_structure_with_llm(self, basic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Excel structure using LLM without hardcoded patterns."""
        # Prepare structure information for LLM
        structure_info = []
        for sheet in basic_data["sheets"]:
            sheet_info = {
                "sheet_name": sheet.sheet_name,
                "file_path": sheet.file_path,
                "columns": sheet.columns,
                "sample_data": sheet.metadata.get("sample_data", []),
                "shape": sheet.metadata.get("shape", [])
            }
            structure_info.append(sheet_info)
        
        prompt = f"""
        Проанализируй структуру Excel данных и определи семантическое значение всех колонок.
        
        СТРУКТУРА EXCEL:
        {json.dumps(structure_info, ensure_ascii=False, indent=2)}
        
        ВЕРНИ АНАЛИЗ В ФОРМАТЕ JSON:
        {{
            "column_analysis": [
                {{
                    "column_name": "название колонки",
                    "data_type": "тип данных",
                    "sample_values": ["значение1", "значение2"],
                    "null_count": 0,
                    "unique_count": 10,
                    "semantic_meaning": "семантическое значение",
                    "relevance_score": 85.0,
                    "analysis_suggestions": ["рекомендация1", "рекомендация2"]
                }}
            ],
            "intelligent_queries": [
                {{
                    "query_description": "описание запроса",
                    "sql_equivalent": "SQL эквивалент",
                    "target_columns": ["колонка1", "колонка2"],
                    "expected_output_format": "table",
                    "confidence_score": 0.85
                }}
            ],
            "data_insights": ["инсайт1", "инсайт2"]
        }}
        
        ТРЕБОВАНИЯ:
        - Определи семантическое значение КАЖДОЙ колонки на основе названий и данных
        - Генерируй интеллектуальные запросы для извлечения релевантных данных
        - Предоставь глубокие инсайты о структуре и содержании данных
        - Используй только информацию из предоставленной структуры
        """
        
        try:
            response = await self.llm_client.complete(LLMRequest(
                prompt=prompt,
                temperature=0.1,
                max_tokens=4000,
                cache_key=f"structure_analysis_{hash(json.dumps(structure_info))}"
            ))
            
            analysis_data = json.loads(response.content)
            
            # Convert to ExcelColumnInfo objects
            column_objects = []
            for col in analysis_data.get("column_analysis", []):
                column_objects.append(ExcelColumnInfo(**col))
            
            # Convert to IntelligentQuery objects
            query_objects = []
            for query in analysis_data.get("intelligent_queries", []):
                query_objects.append(IntelligentQuery(**query))
            
            return {
                "column_analysis": [col.dict() for col in column_objects],
                "intelligent_queries": [q.dict() for q in query_objects],
                "data_insights": analysis_data.get("data_insights", []),
                "raw_analysis": analysis_data
            }
            
        except Exception as e:
            self.logger.error(f"LLM structure analysis failed: {e}")
            return {
                "column_analysis": [],
                "intelligent_queries": [],
                "data_insights": [f"Analysis failed: {str(e)}"]
            }
    
    async def _improve_structure_analysis(
        self, 
        current_analysis: Dict[str, Any], 
        improvements_suggestions: str
    ) -> Dict[str, Any]:
        """Improve structure analysis based on LLM suggestions."""
        prompt = f"""
        Улучши анализ структуры Excel на основе обратной связи.
        
        ТЕКУЩИЙ АНАЛИЗ:
        {json.dumps(current_analysis, ensure_ascii=False, indent=2)}
        
        ПРЕДЛОЖЕНИЯ ПО УЛУЧШЕНИЮ:
        {improvements_suggestions}
        
        ВЕРНИ УЛУЧШЕННЫЙ АНАЛИЗ В ТОМ ЖЕ JSON ФОРМАТЕ.
        
        ФОКУС НА УЛУЧШЕНИЯХ:
        - Уточни семантическое значение колонок
        - Добавь пропущенные интеллектуальные запросы
        - Расширь инсайты о данных
        - Повысь точность анализа
        """
        
        try:
            response = await self.llm_client.complete(LLMRequest(
                prompt=prompt,
                temperature=0.2,
                max_tokens=4000,
                cache_key=f"structure_improvement_{hash(str(current_analysis) + improvements_suggestions)}"
            ))
            
            improved_data = json.loads(response.content)
            return improved_data
            
        except Exception as e:
            self.logger.error(f"Structure improvement failed: {e}")
            return current_analysis
    
    async def _execute_intelligent_queries(
        self, 
        analysis_data: Dict[str, Any], 
        file_paths: List[str]
    ) -> List[Dict[str, Any]]:
        """Execute intelligent queries on Excel data."""
        query_results = []
        queries = analysis_data.get("intelligent_queries", [])
        
        for query in queries:
            try:
                result = await self._execute_single_query(query, file_paths)
                if result:
                    query_results.append({
                        "query": query,
                        "result": result,
                        "execution_timestamp": datetime.now().isoformat()
                    })
            except Exception as e:
                self.logger.error(f"Query execution failed: {e}")
                continue
        
        return query_results
    
    async def _execute_single_query(
        self, 
        query: Dict[str, Any], 
        file_paths: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Execute a single intelligent query."""
        # Extract data based on target columns
        target_columns = query.get("target_columns", [])
        
        if not target_columns:
            return None
        
        all_data = []
        
        for file_path in file_paths:
            try:
                # Read all sheets
                excel_file = pd.ExcelFile(file_path)
                
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # Filter for target columns that exist
                    available_columns = [col for col in target_columns if col in df.columns]
                    
                    if available_columns:
                        filtered_df = df[available_columns].dropna(how='all')
                        
                        # Convert to dict
                        sheet_result = {
                            "file_path": file_path,
                            "sheet_name": sheet_name,
                            "data": filtered_df.to_dict('records'),
                            "columns": available_columns,
                            "row_count": len(filtered_df)
                        }
                        all_data.append(sheet_result)
                
                excel_file.close()
                
            except Exception as e:
                self.logger.error(f"Failed to execute query on {file_path}: {e}")
                continue
        
        return {
            "query_description": query.get("query_description"),
            "results": all_data,
            "total_rows": sum(len(res.get("data", [])) for res in all_data)
        } if all_data else None
    
    async def _validate_table_results(
        self, 
        query_results: List[Dict[str, Any]], 
        analysis_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Validate and format table results."""
        validated_tables = []
        
        for query_result in query_results:
            result_data = query_result.get("result", {})
            
            if not result_data or not result_data.get("results"):
                continue
            
            # Format each result as a proper table
            for sheet_result in result_data.get("results", []):
                table = {
                    "title": f"{result_data.get('query_description', 'Query Result')} - {sheet_result.get('sheet_name')}",
                    "file_path": sheet_result.get("file_path"),
                    "sheet_name": sheet_result.get("sheet_name"),
                    "columns": sheet_result.get("columns", []),
                    "data": sheet_result.get("data", []),
                    "row_count": sheet_result.get("row_count", 0),
                    "query_description": result_data.get("query_description"),
                    "validation_timestamp": datetime.now().isoformat()
                }
                
                # Only include tables with actual data
                if table["data"] and table["row_count"] > 0:
                    validated_tables.append(table)
        
        self.logger.info(f"Validated {len(validated_tables)} real tables with data")
        return validated_tables
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for LLM-guided ExcelAgent."""
        base_health = await super().health_check()
        
        try:
            # Test pandas functionality
            test_df = pd.DataFrame({'test': [1, 2, 3]})
            pandas_health = {"status": "healthy", "pandas_available": True}
        except Exception as e:
            pandas_health = {"status": "error", "pandas_available": False, "error": str(e)}
        
        # Test LLM components
        llm_health = {
            "status": "healthy" if all([
                self.llm_client,
                self.iterative_engine,
                self.quality_evaluator
            ]) else "error",
            "components": {
                "llm_client": bool(self.llm_client),
                "iterative_engine": bool(self.iterative_engine),
                "quality_evaluator": bool(self.quality_evaluator)
            }
        }
        
        base_health.update({
            "analysis_type": "llm_guided",
            "hardcoded_patterns": "none",
            "supported_formats": self.supported_formats,
            "pandas_health": pandas_health,
            "llm_health": llm_health,
            "supported_features": [
                "llm_structure_analysis",
                "intelligent_queries",
                "semantic_column_analysis",
                "iterative_improvement",
                "real_table_validation"
            ]
        })
        
        return base_health


# Factory function for dependency injection
def create_excel_agent(config: Dict[str, Any]) -> ExcelAgent:
    """Factory function to create ExcelAgent instance."""
    return ExcelAgent(config)
