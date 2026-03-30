# -*- coding: utf-8 -*-
"""
Core Models - Data models for Employee Monitoring System

Defines basic data structures and models used throughout the system.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events."""
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    MEETING_STARTED = "meeting_started"
    MEETING_ENDED = "meeting_ended"
    EMPLOYEE_ADDED = "employee_added"
    EMPLOYEE_UPDATED = "employee_updated"
    REPORT_GENERATED = "report_generated"


@dataclass
class JSONEvent:
    """Represents an event in the system."""
    id: str
    timestamp: datetime
    event_type: EventType
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type.value,
            'source': self.source,
            'data': self.data,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JSONEvent':
        """Create from dictionary."""
        return cls(
            id=data['id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            event_type=EventType(data['event_type']),
            source=data['source'],
            data=data.get('data', {}),
            metadata=data.get('metadata', {})
        )


@dataclass
class JSONState:
    """Represents a state snapshot."""
    id: str
    timestamp: datetime
    entity_type: str
    entity_id: str
    state_data: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'state_data': self.state_data,
            'version': self.version,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JSONState':
        """Create from dictionary."""
        return cls(
            id=data['id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            entity_type=data['entity_type'],
            entity_id=data['entity_id'],
            state_data=data.get('state_data', {}),
            version=data.get('version', 1),
            metadata=data.get('metadata', {})
        )


@dataclass
class JSONIndex:
    """Represents an index entry."""
    id: str
    key: str
    value: str
    entity_type: str
    entity_id: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JSONIndex':
        """Create from dictionary."""
        return cls(
            id=data['id'],
            key=data['key'],
            value=data['value'],
            entity_type=data['entity_type'],
            entity_id=data['entity_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {})
        )


@dataclass
class TaskModel:
    """Task model for JIRA integration."""
    id: str
    key: str
    summary: str
    status: str
    assignee: str
    project: str
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    due_date: Optional[datetime] = None
    priority: str = "Medium"
    story_points: Optional[float] = None
    description: str = ""
    labels: List[str] = field(default_factory=list)
    commits_count: int = 0
    pull_requests_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'key': self.key,
            'summary': self.summary,
            'status': self.status,
            'assignee': self.assignee,
            'project': self.project,
            'created': self.created.isoformat() if self.created else None,
            'updated': self.updated.isoformat() if self.updated else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'priority': self.priority,
            'story_points': self.story_points,
            'description': self.description,
            'labels': self.labels,
            'commits_count': self.commits_count,
            'pull_requests_count': self.pull_requests_count
        }


@dataclass
class EmployeeModel:
    """Employee model."""
    id: str
    name: str
    email: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'department': self.department,
            'position': self.position,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class MeetingModel:
    """Meeting model."""
    id: str
    title: str
    date: datetime
    duration_minutes: int
    participants: List[str] = field(default_factory=list)
    meeting_type: str = "general"
    protocol_content: str = ""
    action_items: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'date': self.date.isoformat(),
            'duration_minutes': self.duration_minutes,
            'participants': self.participants,
            'meeting_type': self.meeting_type,
            'protocol_content': self.protocol_content,
            'action_items': self.action_items,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class ReportModel:
    """Report model."""
    id: str
    report_type: str
    title: str
    content: Dict[str, Any]
    generated_at: datetime = field(default_factory=datetime.now)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    employees: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'report_type': self.report_type,
            'title': self.title,
            'content': self.content,
            'generated_at': self.generated_at.isoformat(),
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'employees': self.employees,
            'quality_score': self.quality_score,
            'metadata': self.metadata
        }


# Utility functions
def generate_id() -> str:
    """Generate unique ID."""
    import uuid
    return str(uuid.uuid4())


def serialize_model(model) -> str:
    """Serialize model to JSON string."""
    if hasattr(model, 'to_dict'):
        return json.dumps(model.to_dict(), ensure_ascii=False, indent=2)
    else:
        return json.dumps(asdict(model), ensure_ascii=False, indent=2)


def deserialize_model(json_str: str, model_class):
    """Deserialize JSON string to model."""
    data = json.loads(json_str)
    if hasattr(model_class, 'from_dict'):
        return model_class.from_dict(data)
    else:
        return model_class(**data)
