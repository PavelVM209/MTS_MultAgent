"""
Meeting Analysis Schema for Scheduled Architecture

Validates JSON data structure for DailyMeetingAgent outputs from protocol analysis.
"""

from typing import Dict, Any, List
from datetime import datetime, date
from .base_schema import BaseSchema, ValidationResult, ValidationPatterns, ValidationUtils


class MeetingAnalysisSchema(BaseSchema):
    """Schema for validating meeting analysis data from DailyMeetingAgent"""
    
    def __init__(self):
        super().__init__("meeting_analysis")
    
    async def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate meeting analysis data structure.
        
        Expected structure:
        {
            "date": "2026-03-25",
            "processed_files": ["/path/to/protocol1.txt"],
            "meetings": [
                {
                    "meeting_type": "daily_standup",
                    "date": "2026-03-25",
                    "participants": [...],
                    "employee_actions": [...]
                }
            ],
            "daily_employee_summary": {...},
            "system_metrics": {...},
            "_metadata": {...}
        }
        """
        result = ValidationResult(valid=True, errors=[], warnings=[])
        
        # 🔹 Required top-level fields
        required_fields = ["date", "processed_files", "meetings", "system_metrics"]
        self._validate_required_fields(data, required_fields, result)
        
        # 🔹 Field type validation
        field_types = {
            "date": (str, date),
            "processed_files": list,
            "meetings": list,
            "system_metrics": dict
        }
        self._validate_field_types(data, field_types, result)
        
        # 🔹 String pattern validation
        field_patterns = {
            "date": ValidationPatterns.DATE
        }
        self._validate_string_patterns(data, field_patterns, result)
        
        # 🔹 Validate processed files
        if "processed_files" in data:
            self._validate_processed_files(data["processed_files"], result)
        
        # 🔹 Validate meetings
        if "meetings" in data:
            await self._validate_meetings(data["meetings"], result)
        
        # 🔹 Validate daily employee summary if present
        if "daily_employee_summary" in data:
            self._validate_daily_employee_summary(data["daily_employee_summary"], result)
        
        # 🔹 System metrics validation
        if "system_metrics" in data:
            self._validate_system_metrics(data["system_metrics"], result)
        
        # 🔹 Metadata validation
        if "_metadata" in data:
            self._validate_metadata(data["_metadata"], "daily_meeting_data", result)
        
        return result
    
    def _validate_processed_files(self, files: List[str], result: ValidationResult):
        """Validate processed files list"""
        for i, file_path in enumerate(files):
            if not isinstance(file_path, str):
                result.add_error(
                    field=f"processed_files[{i}]",
                    message="File path must be string",
                    value=file_path,
                    expected_type="string"
                )
            elif not file_path.strip():
                result.add_error(
                    field=f"processed_files[{i}]",
                    message="File path cannot be empty",
                    value=file_path,
                    expected_type="non_empty_string"
                )
    
    async def _validate_meetings(self, meetings: List[Dict[str, Any]], result: ValidationResult):
        """Validate meetings array"""
        if not meetings:
            result.add_warning("No meetings found in processed data")
            return
        
        for i, meeting in enumerate(meetings):
            if not isinstance(meeting, dict):
                result.add_error(
                    field=f"meetings[{i}]",
                    message="Meeting entry must be dict",
                    value=meeting,
                    expected_type="dict"
                )
                continue
            
            await self._validate_single_meeting(meeting, f"meetings[{i}]", result)
    
    async def _validate_single_meeting(
        self, 
        meeting: Dict[str, Any], 
        field_prefix: str, 
        result: ValidationResult
    ):
        """Validate individual meeting entry"""
        # Required meeting fields
        required_fields = ["meeting_type", "date", "participants", "employee_actions"]
        self._validate_required_fields(meeting, required_fields, result)
        
        # Field type validation
        field_types = {
            "meeting_type": str,
            "date": (str, date),
            "participants": list,
            "employee_actions": list
        }
        self._validate_field_types(meeting, field_types, result)
        
        # Validate meeting type
        if "meeting_type" in meeting:
            valid_types = [
                "daily_standup", "sprint_planning", "sprint_review", 
                "retrospective", "technical_sync", "client_meeting"
            ]
            if meeting["meeting_type"] not in valid_types:
                result.add_warning(
                    f"Meeting type '{meeting['meeting_type']}' at {field_prefix}.meeting_type may not be standard"
                )
        
        # Validate date format
        if "date" in meeting and isinstance(meeting["date"], str):
            if not ValidationUtils.is_valid_date(meeting["date"]):
                result.add_error(
                    field=f"{field_prefix}.date",
                    message="Invalid date format (expected YYYY-MM-DD)",
                    value=meeting["date"],
                    expected_type="date_string"
                )
        
        # Validate participants
        if "participants" in meeting:
            await self._validate_participants(meeting["participants"], f"{field_prefix}.participants", result)
        
        # Validate employee actions
        if "employee_actions" in meeting:
            await self._validate_employee_actions(meeting["employee_actions"], f"{field_prefix}.employee_actions", result)
        
        # Validate optional fields
        if "decisions_made" in meeting:
            self._validate_decisions_made(meeting["decisions_made"], f"{field_prefix}.decisions_made", result)
    
    async def _validate_participants(
        self, 
        participants: List[Dict[str, Any]], 
        field_prefix: str, 
        result: ValidationResult
    ):
        """Validate participants list"""
        for i, participant in enumerate(participants):
            if not isinstance(participant, dict):
                result.add_error(
                    field=f"{field_prefix}[{i}]",
                    message="Participant must be dict",
                    value=participant,
                    expected_type="dict"
                )
                continue
            
            # Required participant fields
            required_fields = ["name"]
            self._validate_required_fields(participant, required_fields, result)
            
            # Validate name
            if "name" in participant:
                name = participant["name"]
                if not isinstance(name, str) or len(name.strip()) < 2:
                    result.add_error(
                        field=f"{field_prefix}[{i}].name",
                        message="Participant name must be non-empty string (min 2 chars)",
                        value=name,
                        expected_type="string"
                    )
            
            # Validate role if present
            if "role" in participant:
                role = participant["role"]
                if not isinstance(role, str) or len(role.strip()) < 2:
                    result.add_error(
                        field=f"{field_prefix}[{i}].role",
                        message="Participant role must be non-empty string (min 2 chars)",
                        value=role,
                        expected_type="string"
                    )
            
            # Validate participation metrics if present
            if "participation" in participant:
                self._validate_participation_metrics(
                    participant["participation"],
                    f"{field_prefix}[{i}].participation",
                    result
                )
    
    def _validate_participation_metrics(
        self, 
        participation: Dict[str, Any], 
        field_prefix: str, 
        result: ValidationResult
    ):
        """Validate participation metrics"""
        if not isinstance(participation, dict):
            result.add_error(
                field=field_prefix,
                message="Participation metrics must be dict",
                value=participation,
                expected_type="dict"
            )
            return
        
        # Validate numeric participation metrics
        numeric_fields = ["spoke_minutes", "action_items", "decisions_made"]
        for field in numeric_fields:
            if field in participation:
                value = participation[field]
                if not isinstance(value, (int, float)) or value < 0:
                    result.add_error(
                        field=f"{field_prefix}.{field}",
                        message=f"Participation metric must be non-negative number",
                        value=value,
                        expected_type="number>=0"
                    )
        
        # Validate reasonable ranges
        if "spoke_minutes" in participation:
            minutes = participation["spoke_minutes"]
            if minutes > 60:  # Reasonable limit for meeting participation
                result.add_warning(
                    f"High speaking time ({minutes} minutes) at {field_prefix}.spoke_minutes"
                )
    
    async def _validate_employee_actions(
        self, 
        actions: List[Dict[str, Any]], 
        field_prefix: str, 
        result: ValidationResult
    ):
        """Validate employee actions list"""
        for i, action in enumerate(actions):
            if not isinstance(action, dict):
                result.add_error(
                    field=f"{field_prefix}[{i}]",
                    message="Employee action must be dict",
                    value=action,
                    expected_type="dict"
                )
                continue
            
            # Required action fields
            required_fields = ["employee", "action"]
            self._validate_required_fields(action, required_fields, result)
            
            # Validate employee name
            if "employee" in action:
                employee = action["employee"]
                if not isinstance(employee, str) or len(employee.strip()) < 2:
                    result.add_error(
                        field=f"{field_prefix}[{i}].employee",
                        message="Employee name must be non-empty string (min 2 chars)",
                        value=employee,
                        expected_type="string"
                    )
            
            # Validate action description
            if "action" in action:
                action_text = action["action"]
                if not isinstance(action_text, str) or len(action_text.strip()) < 5:
                    result.add_error(
                        field=f"{field_prefix}[{i}].action",
                        message="Action description must be non-empty string (min 5 chars)",
                        value=action_text,
                        expected_type="string"
                    )
            
            # Validate deadline if present
            if "deadline" in action:
                deadline = action["deadline"]
                if isinstance(deadline, str):
                    if not ValidationUtils.is_valid_date(deadline):
                        result.add_error(
                            field=f"{field_prefix}[{i}].deadline",
                            message="Deadline must be valid date (YYYY-MM-DD)",
                            value=deadline,
                            expected_type="date_string"
                        )
                elif not isinstance(deadline, (date, datetime)):
                    result.add_error(
                        field=f"{field_prefix}[{i}].deadline",
                        message="Deadline must be date or date string",
                        value=deadline,
                        expected_type="date"
                    )
            
            # Validate priority if present
            if "priority" in action:
                valid_priorities = ["low", "medium", "high", "critical"]
                if action["priority"] not in valid_priorities:
                    result.add_warning(
                        f"Priority '{action['priority']}' at {field_prefix}[{i}].priority may not be standard"
                    )
    
    def _validate_decisions_made(
        self, 
        decisions: List[Dict[str, Any]], 
        field_prefix: str, 
        result: ValidationResult
    ):
        """Validate decisions made list"""
        for i, decision in enumerate(decisions):
            if not isinstance(decision, dict):
                result.add_error(
                    field=f"{field_prefix}[{i}]",
                    message="Decision must be dict",
                    value=decision,
                    expected_type="dict"
                )
                continue
            
            # Required decision fields
            required_fields = ["decision", "made_by"]
            self._validate_required_fields(decision, required_fields, result)
            
            # Validate decision text
            if "decision" in decision:
                decision_text = decision["decision"]
                if not isinstance(decision_text, str) or len(decision_text.strip()) < 5:
                    result.add_error(
                        field=f"{field_prefix}[{i}].decision",
                        message="Decision must be non-empty string (min 5 chars)",
                        value=decision_text,
                        expected_type="string"
                    )
            
            # Validate made_by
            if "made_by" in decision:
                made_by = decision["made_by"]
                if not isinstance(made_by, str) or len(made_by.strip()) < 2:
                    result.add_error(
                        field=f"{field_prefix}[{i}].made_by",
                        message="Decision maker must be non-empty string (min 2 chars)",
                        value=made_by,
                        expected_type="string"
                    )
    
    def _validate_daily_employee_summary(
        self, 
        summary: Dict[str, Any], 
        result: ValidationResult
    ):
        """Validate daily employee summary structure"""
        if not isinstance(summary, dict):
            result.add_error(
                field="daily_employee_summary",
                message="Daily employee summary must be dict",
                value=summary,
                expected_type="dict"
            )
            return
        
        for username, employee_summary in summary.items():
            if not isinstance(employee_summary, dict):
                result.add_error(
                    field=f"daily_employee_summary.{username}",
                    message="Employee summary must be dict",
                    value=employee_summary,
                    expected_type="dict"
                )
                continue
            
            # Validate employee summary fields
            numeric_fields = ["meetings_attended", "action_items_assigned", "action_items_completed"]
            for field in numeric_fields:
                if field in employee_summary:
                    value = employee_summary[field]
                    if not isinstance(value, int) or value < 0:
                        result.add_error(
                            field=f"daily_employee_summary.{username}.{field}",
                            message=f"Summary metric must be non-negative integer",
                            value=value,
                            expected_type="int>=0"
                        )
            
            # Validate participation score if present
            if "participation_score" in employee_summary:
                score = employee_summary["participation_score"]
                if not ValidationUtils.is_valid_performance_score(score):
                    result.add_error(
                        field=f"daily_employee_summary.{username}.participation_score",
                        message="Participation score must be between 0-10",
                        value=score,
                        expected_type="performance_score"
                    )
    
    def _validate_system_metrics(self, metrics: Dict[str, Any], result: ValidationResult):
        """Validate system metrics structure"""
        required_metrics = ["files_processed", "processing_time_seconds", "quality_score"]
        self._validate_required_fields(metrics, required_metrics, result)
        
        # Validate numeric metrics
        numeric_ranges = {
            "files_processed": (0, 100),  # Reasonable range for daily files
            "processing_time_seconds": (0, 1800),  # Max 30 minutes processing
            "quality_score": (0, 100)  # Percentage
        }
        self._validate_numeric_ranges(metrics, numeric_ranges, result)
    
    def _validate_metadata(
        self, 
        metadata: Dict[str, Any], 
        expected_type: str, 
        result: ValidationResult
    ):
        """Validate metadata structure"""
        # Check for required metadata fields
        required_metadata = ["data_type", "persisted_at", "persisted_by", "version"]
        self._validate_required_fields(metadata, required_metadata, result)
        
        # Validate data type
        if "data_type" in metadata:
            if metadata["data_type"] != expected_type:
                result.add_error(
                    field="_metadata.data_type",
                    message=f"Incorrect data type for meeting analysis",
                    value=metadata["data_type"],
                    expected_type=expected_type
                )
        
        # Validate timestamps
        if "persisted_at" in metadata:
            if not ValidationUtils.is_valid_datetime(metadata["persisted_at"]):
                result.add_error(
                    field="_metadata.persisted_at",
                    message="Invalid datetime format",
                    value=metadata["persisted_at"],
                    expected_type="iso_datetime"
                )


# Additional validation functions for meeting-specific scenarios
def validate_meeting_coverage(meetings: List[Dict[str, Any]]) -> List[str]:
    """
    Validate meeting coverage and patterns.
    Returns list of warnings about unusual meeting patterns.
    """
    warnings = []
    
    if not meetings:
        return warnings
    
    # Count meeting types
    meeting_types = {}
    for meeting in meetings:
        meeting_type = meeting.get("meeting_type", "unknown")
        meeting_types[meeting_type] = meeting_types.get(meeting_type, 0) + 1
    
    # Check for missing daily standup (usually expected)
    if meeting_types.get("daily_standup", 0) == 0:
        warnings.append("No daily standup meetings found - may be unusual pattern")
    
    # Check for too many meetings in one day
    total_meetings = len(meetings)
    if total_meetings > 8:
        warnings.append(f"High meeting count: {total_meetings} meetings in single day")
    
    # Check for meetings without participants or actions
    for i, meeting in enumerate(meetings):
        participants = len(meeting.get("participants", []))
        actions = len(meeting.get("employee_actions", []))
        
        if participants == 0:
            warnings.append(f"Meeting {i+1} has no participants")
        
        if actions == 0 and meeting.get("meeting_type") in ["daily_standup", "sprint_planning"]:
            warnings.append(f"Meeting {i+1} ({meeting.get('meeting_type')}) has no action items")
    
    return warnings


def validate_employee_action_balance(actions: List[Dict[str, Any]]) -> List[str]:
    """
    Validate balance of employee actions across meetings.
    Returns list of warnings about imbalance.
    """
    warnings = []
    
    # Count actions per employee
    action_counts = {}
    for action in actions:
        employee = action.get("employee", "unknown")
        action_counts[employee] = action_counts.get(employee, 0) + 1
    
    # Check for imbalance
    if action_counts:
        max_actions = max(action_counts.values())
        min_actions = min(action_counts.values())
        
        if max_actions > min_actions * 3:  # More than 3x difference
            warnings.append(
                f"Significant action imbalance: most employee has {max_actions} actions, least has {min_actions}"
            )
    
    # Check for overdue actions
    current_date = date.today()
    for action in actions:
        if "deadline" in action and "completed" not in action:
            try:
                deadline = date.fromisoformat(action["deadline"])
                if deadline < current_date:
                    warnings.append(f"Overdue action: {action.get('action', 'Unknown')}")
            except (ValueError, TypeError):
                pass
    
    return warnings
