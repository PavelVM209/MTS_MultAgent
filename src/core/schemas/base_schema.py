"""
Base Schema Classes for JSON Validation

Provides foundation schema validation functionality for scheduled architecture.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime, date
import json
import re


@dataclass
class ValidationError:
    """Individual validation error"""
    field: str
    message: str
    value: Any
    expected_type: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of schema validation"""
    valid: bool
    errors: List[ValidationError]
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
    
    @property
    def error_count(self) -> int:
        return len(self.errors)
    
    @property
    def warning_count(self) -> int:
        return len(self.warnings)
    
    def add_error(self, field: str, message: str, value: Any, expected_type: str = None):
        """Add a validation error"""
        self.errors.append(ValidationError(
            field=field,
            message=message,
            value=value,
            expected_type=expected_type
        ))
        self.valid = False
    
    def add_warning(self, message: str):
        """Add a validation warning"""
        self.warnings.append(message)


class BaseSchema(ABC):
    """Base schema class with common validation functionality"""
    
    def __init__(self, schema_name: str):
        self.schema_name = schema_name
    
    @abstractmethod
    async def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate data against schema"""
        pass
    
    def _validate_required_fields(
        self, 
        data: Dict[str, Any], 
        required_fields: List[str],
        result: ValidationResult
    ):
        """Validate required fields are present"""
        for field in required_fields:
            if field not in data or data[field] is None:
                result.add_error(
                    field=field,
                    message=f"Required field '{field}' is missing or null",
                    value=data.get(field)
                )
    
    def _validate_field_types(
        self, 
        data: Dict[str, Any], 
        field_types: Dict[str, type],
        result: ValidationResult
    ):
        """Validate field types"""
        for field, expected_type in field_types.items():
            if field in data and data[field] is not None:
                value = data[field]
                
                # Handle special cases
                if expected_type == datetime:
                    if not isinstance(value, (str, datetime)):
                        result.add_error(
                            field=field,
                            message=f"Field '{field}' must be datetime or ISO string",
                            value=value,
                            expected_type="datetime|string"
                        )
                    elif isinstance(value, str):
                        try:
                            datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except ValueError:
                            result.add_error(
                                field=field,
                                message=f"Field '{field}' must be valid ISO datetime string",
                                value=value,
                                expected_type="datetime|string"
                            )
                
                elif expected_type == date:
                    if not isinstance(value, (str, date)):
                        result.add_error(
                            field=field,
                            message=f"Field '{field}' must be date or YYYY-MM-DD string",
                            value=value,
                            expected_type="date|string"
                        )
                    elif isinstance(value, str):
                        try:
                            date.fromisoformat(value)
                        except ValueError:
                            result.add_error(
                                field=field,
                                message=f"Field '{field}' must be valid YYYY-MM-DD date string",
                                value=value,
                                expected_type="date|string"
                            )
                
                elif not isinstance(value, expected_type):
                    result.add_error(
                        field=field,
                        message=f"Field '{field}' must be {expected_type.__name__}",
                        value=value,
                        expected_type=expected_type.__name__
                    )
    
    def _validate_numeric_ranges(
        self, 
        data: Dict[str, Any], 
        field_ranges: Dict[str, tuple],
        result: ValidationResult
    ):
        """Validate numeric field ranges"""
        for field, (min_val, max_val) in field_ranges.items():
            if field in data and data[field] is not None:
                value = data[field]
                if not isinstance(value, (int, float)):
                    continue
                
                if value < min_val or value > max_val:
                    result.add_error(
                        field=field,
                        message=f"Field '{field}' must be between {min_val} and {max_val}",
                        value=value,
                        expected_type=f"number[{min_val}-{max_val}]"
                    )
    
    def _validate_string_patterns(
        self, 
        data: Dict[str, Any], 
        field_patterns: Dict[str, str],
        result: ValidationResult
    ):
        """Validate string field patterns"""
        for field, pattern in field_patterns.items():
            if field in data and data[field] is not None:
                value = data[field]
                if not isinstance(value, str):
                    continue
                
                if not re.match(pattern, value):
                    result.add_error(
                        field=field,
                        message=f"Field '{field}' does not match required pattern",
                        value=value,
                        expected_type=f"string[{pattern}]"
                    )
    
    def _validate_enum_values(
        self, 
        data: Dict[str, Any], 
        field_enums: Dict[str, List[Any]],
        result: ValidationResult
    ):
        """Validate enum field values"""
        for field, allowed_values in field_enums.items():
            if field in data and data[field] is not None:
                value = data[field]
                if value not in allowed_values:
                    result.add_error(
                        field=field,
                        message=f"Field '{field}' must be one of: {allowed_values}",
                        value=value,
                        expected_type=f"enum[{', '.join(map(str, allowed_values))}]"
                    )
    
    def _validate_array_items(
        self, 
        data: Dict[str, Any], 
        array_schemas: Dict[str, dict],
        result: ValidationResult
    ):
        """Validate array items against schemas"""
        for field, item_schema in array_schemas.items():
            if field in data and data[field] is not None:
                value = data[field]
                if not isinstance(value, list):
                    continue
                
                for i, item in enumerate(value):
                    # Basic type validation for array items
                    if 'type' in item_schema:
                        expected_type = item_schema['type']
                        if expected_type == 'string' and not isinstance(item, str):
                            result.add_error(
                                field=f"{field}[{i}]",
                                message=f"Array item must be string",
                                value=item,
                                expected_type="string"
                            )
                        elif expected_type == 'dict' and not isinstance(item, dict):
                            result.add_error(
                                field=f"{field}[{i}]",
                                message=f"Array item must be dict",
                                value=item,
                                expected_type="dict"
                            )
    
    def _validate_nested_objects(
        self, 
        data: Dict[str, Any], 
        nested_schemas: Dict[str, dict],
        result: ValidationResult
    ):
        """Validate nested object structures"""
        for field, schema in nested_schemas.items():
            if field in data and data[field] is not None:
                value = data[field]
                if not isinstance(value, dict):
                    result.add_error(
                        field=field,
                        message=f"Field '{field}' must be object/dict",
                        value=value,
                        expected_type="dict"
                    )
                    continue
                
                # Validate nested object fields
                nested_result = ValidationResult(valid=True, errors=[], warnings=[])
                
                if 'required' in schema:
                    self._validate_required_fields(value, schema['required'], nested_result)
                
                if 'types' in schema:
                    self._validate_field_types(value, schema['types'], nested_result)
                
                # Add nested errors to main result with field prefix
                for error in nested_result.errors:
                    result.add_error(
                        field=f"{field}.{error.field}",
                        message=error.message,
                        value=error.value,
                        expected_type=error.expected_type
                    )
    
    @staticmethod
    def _get_field_path(data: Dict[str, Any], path: str, default: Any = None) -> Any:
        """Get nested field value by path (e.g., 'user.profile.name')"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current


class JsonSchemaValidator:
    """JSON Schema validation utility"""
    
    @staticmethod
    def create_simple_schema(schema_def: Dict[str, Any]) -> Dict[str, Any]:
        """Create simple JSON schema from definition"""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": schema_def.get("properties", {}),
            "required": schema_def.get("required", []),
            "additionalProperties": schema_def.get("additionalProperties", False)
        }
    
    @staticmethod
    def validate_with_jsonschema(data: Dict[str, Any], schema: Dict[str, Any]) -> ValidationResult:
        """Validate using JSON Schema (if available)"""
        try:
            import jsonschema
            
            result = ValidationResult(valid=True, errors=[], warnings=[])
            
            try:
                jsonschema.validate(data, schema)
            except jsonschema.ValidationError as e:
                result.add_error(
                    field=".".join(str(p) for p in e.absolute_path) if e.absolute_path else "root",
                    message=e.message,
                    value=e.instance,
                    expected_type=str(e.schema.get('type', 'unknown'))
                )
            except jsonschema.SchemaError as e:
                result.add_error(
                    field="schema",
                    message=f"Schema error: {e.message}",
                    value=schema,
                    expected_type="valid_schema"
                )
            
            return result
            
        except ImportError:
            # Fallback to basic validation
            return ValidationResult(
                valid=False,
                errors=[ValidationError(
                    field="validator",
                    message="jsonschema library not available for validation",
                    value=None
                )],
                warnings=["Basic validation only - install jsonschema for full validation"]
            )


# Common validation patterns and utilities
class ValidationPatterns:
    """Common validation patterns for scheduled architecture"""
    
    # Email pattern
    EMAIL = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Jira project key pattern
    JIRA_PROJECT_KEY = r'^[A-Z][A-Z0-9]*$'
    
    # Jira issue key pattern
    JIRA_ISSUE_KEY = r'^[A-Z][A-Z0-9]*-\d+$'
    
    # Username pattern (alphanumeric with underscore, hyphen)
    USERNAME = r'^[a-zA-Z0-9_-]+$'
    
    # Date pattern (YYYY-MM-DD)
    DATE = r'^\d{4}-\d{2}-\d{2}$'
    
    # ISO datetime pattern
    ISO_DATETIME = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
    
    # Performance score (0-10 with optional decimal)
    PERFORMANCE_SCORE = r'^[0-9](\.[0-9])?$|^10(\.0)?$'
    
    # File path pattern
    FILE_PATH = r'^[a-zA-Z0-9_\-/\\.]+$'


class ValidationUtils:
    """Utility functions for validation"""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Check if email is valid"""
        return bool(re.match(ValidationPatterns.EMAIL, email))
    
    @staticmethod
    def is_valid_jira_key(key: str) -> bool:
        """Check if Jira key is valid"""
        return bool(re.match(ValidationPatterns.JIRA_ISSUE_KEY, key))
    
    @staticmethod
    def is_valid_date(date_str: str) -> bool:
        """Check if date string is valid YYYY-MM-DD"""
        if not re.match(ValidationPatterns.DATE, date_str):
            return False
        try:
            date.fromisoformat(date_str)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_valid_datetime(datetime_str: str) -> bool:
        """Check if datetime string is valid ISO format"""
        if not re.match(ValidationPatterns.ISO_DATETIME, datetime_str):
            return False
        try:
            datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_valid_performance_score(score: Any) -> bool:
        """Check if performance score is valid (0-10)"""
        if isinstance(score, str):
            return bool(re.match(ValidationPatterns.PERFORMANCE_SCORE, score))
        elif isinstance(score, (int, float)):
            return 0 <= score <= 10
        return False
    
    @staticmethod
    def normalize_score(score: Any) -> float:
        """Normalize score to float between 0-10"""
        if isinstance(score, str):
            try:
                return float(score)
            except ValueError:
                return 0.0
        elif isinstance(score, (int, float)):
            return float(score)
        return 0.0
    
    @staticmethod
    def safe_get_dict(data: Any, default: Dict = None) -> Dict:
        """Safely get dictionary from any value"""
        if isinstance(data, dict):
            return data
        elif isinstance(data, str):
            try:
                return json.loads(data)
            except (json.JSONDecodeError, TypeError):
                pass
        return default or {}
    
    @staticmethod
    def safe_get_list(data: Any, default: List = None) -> List:
        """Safely get list from any value"""
        if isinstance(data, list):
            return data
        elif isinstance(data, (str, dict)):
            # Don't try to parse strings or dicts as lists
            return default or []
        elif data is not None:
            return [data]
        return default or []
