"""
Excel Agent for MTS MultAgent System

This agent handles Excel file operations:
- Reading Excel files with various formats
- Extracting data from specific sheets and ranges
- Converting Excel data to structured formats
- Handling multiple Excel files
- Data validation and cleaning
"""

import asyncio
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import structlog

from src.core.base_agent import BaseAgent, AgentResult
from src.core.models import ExcelTask, ExcelResult, ExcelData, ExcelSheet

logger = structlog.get_logger()


class ExcelAgent(BaseAgent):
    """
    Agent for processing Excel files.
    
    Handles reading Excel files, extracting data from specific sheets,
    and converting to structured formats for further analysis.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ExcelAgent with configuration.
        
        Args:
            config: Configuration dictionary containing Excel settings
        """
        super().__init__(config, "ExcelAgent")
        
        # Validate required configuration
        required_keys = ["excel.file_path", "excel.supported_formats"]
        if not self.validate_config(required_keys):
            raise ValueError("Missing required Excel configuration")
        
        self.default_file_path = self.get_config_value("excel.file_path")
        self.supported_formats = self.get_config_value("excel.supported_formats", [".xlsx", ".xls", ".xlsm"])
        self.default_sheet = self.get_config_value("excel.default_sheet", 0)
        self.max_rows = self.get_config_value("excel.max_rows", 10000)
        
    async def validate(self, task: Dict[str, Any]) -> bool:
        """
        Validate Excel task parameters.
        
        Args:
            task: Task dictionary with ExcelTask parameters
            
        Returns:
            True if valid, False otherwise
        """
        try:
            excel_task = ExcelTask(**task)
            
            # Additional validation
            if not excel_task.file_paths:
                self.logger.error("At least one file path is required")
                return False
            
            # Check if files exist
            for file_path in excel_task.file_paths:
                path = Path(file_path)
                if not path.exists():
                    self.logger.error(f"File not found: {file_path}")
                    return False
                
                if not path.is_file():
                    self.logger.error(f"Path is not a file: {file_path}")
                    return False
                
                # Check file extension
                if path.suffix.lower() not in self.supported_formats:
                    self.logger.error(
                        f"Unsupported file format: {path.suffix}. Supported: {self.supported_formats}"
                    )
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error("Excel task validation failed", error=str(e))
            return False
    
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        """
        Execute Excel task with data extraction.
        
        Args:
            task: Task dictionary containing Excel parameters
            
        Returns:
            AgentResult with Excel data
        """
        excel_task = ExcelTask(**task)
        
        try:
            extracted_data = []
            sheets_info = []
            total_rows = 0
            total_sheets = 0
            
            # Process each file
            for file_path in excel_task.file_paths:
                self.logger.info(f"Processing Excel file: {file_path}")
                
                # Read Excel file
                file_data = await self._read_excel_file(
                    file_path,
                    excel_task.sheet_names,
                    excel_task.cell_ranges,
                    excel_task.headers_row
                )
                
                extracted_data.extend(file_data["sheets"])
                sheets_info.extend(file_data["sheets_info"])
                total_rows += file_data["total_rows"]
                total_sheets += file_data["total_sheets"]
            
            # Create result
            result = ExcelResult(
                sheets=extracted_data,
                total_rows=total_rows,
                total_sheets=total_sheets,
                file_paths=excel_task.file_paths,
                extraction_timestamp=datetime.now(),
                metadata={
                    "file_count": len(excel_task.file_paths),
                    "extraction_time": datetime.now().isoformat(),
                    "supported_formats": self.supported_formats
                }
            )
            
            self.logger.info(
                "Excel extraction completed",
                file_count=len(excel_task.file_paths),
                sheets=total_sheets,
                rows=total_rows
            )
            
            return AgentResult(
                success=True,
                data=result.dict(),
                agent_name=self.name
            )
            
        except Exception as e:
            self.logger.error("Excel execution failed", error=str(e), exc_info=True)
            return AgentResult(
                success=False,
                error=f"Excel execution failed: {str(e)}",
                agent_name=self.name
            )
    
    async def _read_excel_file(
        self,
        file_path: str,
        sheet_names: Optional[List[str]] = None,
        cell_ranges: Optional[List[str]] = None,
        headers_row: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Read Excel file and extract data from sheets.
        
        Args:
            file_path: Path to Excel file
            sheet_names: List of sheet names to read (None for all)
            cell_ranges: List of cell ranges to extract (optional)
            headers_row: Row number containing headers (optional)
            
        Returns:
            Dictionary with extracted data and metadata
        """
        sheets_data = []
        sheets_info = []
        total_rows = 0
        total_sheets = 0
        
        try:
            # Get all sheet names if not specified
            if not sheet_names:
                excel_file = pd.ExcelFile(file_path)
                sheet_names = excel_file.sheet_names
                excel_file.close()
            
            # Process each sheet
            for sheet_name in sheet_names:
                try:
                    # Read sheet data
                    if cell_ranges:
                        # Read specific ranges
                        sheet_data = await self._read_cell_ranges(file_path, sheet_name, cell_ranges)
                    else:
                        # Read entire sheet
                        sheet_data = await self._read_entire_sheet(file_path, sheet_name, headers_row)
                    
                    # Create sheet info
                    sheet_info = ExcelSheet(
                        name=sheet_name,
                        rows_count=len(sheet_data.get("data", [])),
                        columns_count=len(sheet_data.get("columns", [])),
                        data_type="tabular",
                        extraction_method="pandas"
                    )
                    
                    sheets_data.append(ExcelData(
                        sheet_name=sheet_name,
                        file_path=file_path,
                        data=sheet_data["data"],
                        columns=sheet_data["columns"],
                        metadata=sheet_data.get("metadata", {})
                    ))
                    
                    sheets_info.append(sheet_info)
                    total_rows += sheet_info.rows_count
                    total_sheets += 1
                    
                    self.logger.info(
                        f"Sheet processed: {sheet_name}",
                        rows=sheet_info.rows_count,
                        columns=sheet_info.columns_count
                    )
                    
                except Exception as e:
                    self.logger.error(
                        f"Failed to process sheet {sheet_name}: {str(e)}",
                        exc_info=True
                    )
                    continue
            
            return {
                "sheets": sheets_data,
                "sheets_info": sheets_info,
                "total_rows": total_rows,
                "total_sheets": total_sheets
            }
            
        except Exception as e:
            self.logger.error(f"Failed to read Excel file {file_path}: {str(e)}", exc_info=True)
            raise
    
    async def _read_entire_sheet(
        self,
        file_path: str,
        sheet_name: str,
        headers_row: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Read entire sheet from Excel file.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Name of sheet to read
            headers_row: Row number containing headers
            
        Returns:
            Dictionary with data and columns
        """
        try:
            # Read sheet with pandas
            if headers_row is not None:
                df = pd.read_excel(
                    file_path,
                    sheet_name=sheet_name,
                    header=headers_row,
                    nrows=self.max_rows
                )
            else:
                df = pd.read_excel(
                    file_path,
                    sheet_name=sheet_name,
                    nrows=self.max_rows
                )
            
            # Clean data
            df = df.dropna(how='all')  # Remove empty rows
            df = df.fillna('')  # Fill NaN values
            
            # Convert to records format
            data = df.to_dict('records')
            columns = df.columns.tolist()
            
            return {
                "data": data,
                "columns": columns,
                "metadata": {
                    "shape": df.shape,
                    "dtypes": df.dtypes.to_dict(),
                    "null_counts": df.isnull().sum().to_dict()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to read sheet {sheet_name}: {str(e)}")
            raise
    
    async def _read_cell_ranges(
        self,
        file_path: str,
        sheet_name: str,
        cell_ranges: List[str]
    ) -> Dict[str, Any]:
        """
        Read specific cell ranges from Excel sheet.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Name of sheet to read
            cell_ranges: List of cell ranges (e.g., "A1:C10")
            
        Returns:
            Dictionary with data and columns
        """
        try:
            all_data = []
            all_columns = []
            
            for cell_range in cell_ranges:
                try:
                    # Read specific range
                    df = pd.read_excel(
                        file_path,
                        sheet_name=sheet_name,
                        usecols=cell_range,
                        nrows=self.max_rows
                    )
                    
                    # Clean data
                    df = df.dropna(how='all')
                    df = df.fillna('')
                    
                    # Add range information to data
                    data = df.to_dict('records')
                    for row in data:
                        row['_range'] = cell_range
                    
                    all_data.extend(data)
                    all_columns.extend([f"{col}_{cell_range}" for col in df.columns])
                    
                except Exception as e:
                    self.logger.error(f"Failed to read range {cell_range}: {str(e)}")
                    continue
            
            return {
                "data": all_data,
                "columns": all_columns,
                "metadata": {
                    "ranges_processed": cell_ranges,
                    "total_ranges": len(cell_ranges)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to read cell ranges: {str(e)}")
            raise
    
    async def search_data(
        self,
        file_path: str,
        search_query: str,
        column_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for specific data in Excel file.
        
        Args:
            file_path: Path to Excel file
            search_query: Search query string
            column_name: Specific column to search in (optional)
            
        Returns:
            List of matching rows
        """
        try:
            # Read all sheets
            excel_task = ExcelTask(file_paths=[file_path])
            is_valid = await self.validate(excel_task.dict())
            
            if not is_valid:
                raise ValueError(f"Invalid Excel file: {file_path}")
            
            result = await self.execute(excel_task.dict())
            
            if not result.success:
                raise ValueError(f"Failed to read Excel file: {result.error}")
            
            # Search in extracted data
            matches = []
            search_query_lower = search_query.lower()
            
            for sheet_data in result.data["sheets"]:
                for row in sheet_data["data"]:
                    # Search in all columns or specific column
                    if column_name:
                        if column_name in row and search_query_lower in str(row[column_name]).lower():
                            matches.append({
                                "sheet": sheet_data["sheet_name"],
                                "row": row
                            })
                    else:
                        # Search in all columns
                        for value in row.values():
                            if search_query_lower in str(value).lower():
                                matches.append({
                                    "sheet": sheet_data["sheet_name"],
                                    "row": row
                                })
                                break
            
            self.logger.info(
                f"Search completed in {file_path}",
                query=search_query,
                matches=len(matches)
            )
            
            return matches
            
        except Exception as e:
            self.logger.error(f"Search failed in {file_path}: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for Excel agent.
        
        Returns:
            Health check result
        """
        base_health = await super().health_check()
        
        try:
            # Test pandas functionality
            test_df = pd.DataFrame({'test': [1, 2, 3]})
            pandas_health = {"status": "healthy", "pandas_available": True}
        except Exception as e:
            pandas_health = {"status": "error", "pandas_available": False, "error": str(e)}
        
        # Test file path accessibility
        file_path_accessible = False
        if self.default_file_path:
            default_path = Path(self.default_file_path)
            file_path_accessible = default_path.exists() or default_path.parent.exists()
        
        base_health.update({
            "excel_configured": bool(self.default_file_path),
            "file_path_accessible": file_path_accessible,
            "supported_formats": self.supported_formats,
            "pandas_health": pandas_health
        })
        
        return base_health
