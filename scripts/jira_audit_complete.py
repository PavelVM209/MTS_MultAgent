#!/usr/bin/env python3
"""
Comprehensive Jira Integration Audit Script - Complete Version
Analyzes available tasks, API limits, and creates detailed integration specification
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

# Add project root to path
project_root = Path(__file__).parents[1]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))
os.chdir(project_root)

from dotenv import load_dotenv
load_dotenv()

from src.core.jira_client import JiraClient

@dataclass
class JiraTaskSummary:
    """Summary of Jira task analysis."""
    task_id: str
    key: str
    summary: str
    status: str
    assignee: str
    created: str
    updated: str
    priority: str
    project: str
    story_points: Optional[float] = None
    labels: List[str] = None
    components: List[str] = None

@dataclass
class JiraAuditResults:
    """Complete audit results for Jira integration."""
    audit_date: datetime
    connection_status: bool
    total_tasks_found: int
    date_range_analyzed: str
    
    # Task distribution
    tasks_by_status: Dict[str, int]
    tasks_by_assignee: Dict[str, int]
    tasks_by_project: Dict[str, int]
    tasks_by_priority: Dict[str, int]
    
    # Employee coverage
    unique_employees: List[str]
    employees_with_tasks: Dict[str, int]
    
    # Time analysis
    tasks_updated_last_7_days: int
    tasks_updated_last_30_days: int
    tasks_created_last_30_days: int
    
    # API performance
    api_response_time: float
    max_results_per_query: int
    total_api_calls: int
    
    # Sample tasks
    sample_tasks: List[JiraTaskSummary]
    
    # Issues and limitations
    api_limitations: List[str]
    data_quality_issues: List[str]
    recommendations: List[str]

class JiraAuditor:
    """Comprehensive Jira integration auditor."""
    
    def __init__(self):
        self.jira_client = JiraClient()
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    async def test_api_limits(self) -> Dict[str, Any]:
        """Test API rate limits and performance."""
        self.logger.info("🔍 Testing API limits and performance...")
        
        results = {
            'max_results_test': None,
            'response_times': [],
            'rate_limit_info': {},
            'pagination_info': {}
        }
        
        try:
            # Test different result limits
            test_limits = [10, 50, 100]
            
            for limit in test_limits:
                start_time = datetime.now()
                tasks = await self.jira_client.search_issues(
                    jql=f'project = "OPENBD" ORDER BY updated DESC',
                    fields=['key', 'summary', 'status', 'assignee'],
                    max_results=limit
                )
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                results['response_times'].append({
                    'limit': limit,
                    'response_time': response_time,
                    'actual_count': len(tasks) if tasks else 0
                })
                
                self.logger.info(f"Query limit {limit}: {response_time:.2f}s, returned {len(tasks) if tasks else 0} tasks")
            
            # Test pagination
            start_time = datetime.now()
            tasks = await self.jira_client.search_issues(
                jql='project = "OPENBD" ORDER BY updated DESC',
                fields=['key', 'summary'],
                max_results=50,
                start_at=0
            )
            end_time = datetime.now()
            
            results['pagination_info'] = {
                'first_page_response': (end_time - start_time).total_seconds(),
                'tasks_returned': len(tasks) if tasks else 0
            }
            
        except Exception as e:
            self.logger.error(f"API limits test failed: {e}")
            results['error'] = str(e)
        
        return results
    
    async def analyze_task_distribution(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze task distribution across various dimensions."""
        self.logger.info("📊 Analyzing task distribution...")
        
        distribution = {
            'by_status': {},
            'by_assignee': {},
            'by_project': {},
            'by_priority': {},
            'by_creation_month': {},
            'by_update_month': {}
        }
        
        for task in tasks:
            fields = task.get('fields', {})
            
            # Status distribution
            status = fields.get('status', {}).get('name', 'Unknown')
            distribution['by_status'][status] = distribution['by_status'].get(status, 0) + 1
            
            # Assignee distribution
            assignee = self._extract_assignee_name(fields.get('assignee'))
            distribution['by_assignee'][assignee] = distribution['by_assignee'].get(assignee, 0) + 1
            
            # Project distribution
            project = fields.get('project', {}).get('key', 'Unknown')
            distribution['by_project'][project] = distribution['by_project'].get(project, 0) + 1
            
            # Priority distribution
            priority = fields.get('priority', {}).get('name', 'Unknown')
            distribution['by_priority'][priority] = distribution['by_priority'].get(priority, 0) + 1
            
            # Time-based distribution
            created = fields.get('created')
            updated = fields.get('updated')
            
            if created:
                try:
                    created_date = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    month_key = created_date.strftime('%Y-%m')
                    distribution['by_creation_month'][month_key] = distribution['by_creation_month'].get(month_key, 0) + 1
                except:
                    pass
            
            if updated:
                try:
                    updated_date = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                    month_key = updated_date.strftime('%Y-%m')
                    distribution['by_update_month'][month_key] = distribution['by_update_month'].get(month_key, 0) + 1
                except:
                    pass
        
        return distribution
    
    def _extract_assignee_name(self, assignee_field: Any) -> str:
        """Extract assignee name from Jira field."""
        if not assignee_field:
            return 'Unassigned'
        
        if isinstance(assignee_field, dict):
            return (
                assignee_field.get('displayName') or 
                assignee_field.get('name') or 
                assignee_field.get('emailAddress') or 
                'Unknown'
            )
        
        return str(assignee_field)
    
    async def analyze_employee_coverage(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze employee coverage and task distribution."""
        self.logger.info("👥 Analyzing employee coverage...")
        
        employees = {}
        
        for task in tasks:
            fields = task.get('fields', {})
            assignee_name = self._extract_assignee_name(fields.get('assignee'))
            
            if assignee_name not in employees:
                employees[assignee_name] = {
                    'total_tasks': 0,
                    'by_status': {},
                    'by_project': {},
                    'recent_activity': [],
                    'story_points_total': 0,
                    'first_seen': fields.get('created'),
                    'last_seen': fields.get('updated')
                }
            
            employee = employees[assignee_name]
            employee['total_tasks'] += 1
            
            # Status breakdown
            status = fields.get('status', {}).get('name', 'Unknown')
            employee['by_status'][status] = employee['by_status'].get(status, 0) + 1
            
            # Project breakdown
            project = fields.get('project', {}).get('key', 'Unknown')
            employee['by_project'][project] = employee['by_project'].get(project, 0) + 1
            
            # Story points
            story_points = self._extract_story_points(fields)
            if story_points:
                employee['story_points_total'] += story_points
            
            # Track recent activity
            updated = fields.get('updated')
            if updated:
                employee['recent_activity'].append({
                    'task_key': task.get('key'),
                    'updated': updated,
                    'status': status
                })
            
            # Update first/last seen
            created = fields.get('created')
            if created and (not employee['first_seen'] or created < employee['first_seen']):
                employee['first_seen'] = created
            
            if updated and (not employee['last_seen'] or updated > employee['last_seen']):
                employee['last_seen'] = updated
        
        # Sort employees by activity
        sorted_employees = dict(sorted(
            employees.items(), 
            key=lambda x: x[1]['total_tasks'], 
            reverse=True
        ))
        
        return {
            'total_employees': len(employees),
            'employees': sorted_employees,
            'most_active': list(sorted_employees.keys())[:5],
            'employees_with_recent_activity': len([
                emp for emp in sorted_employees.values() 
                if emp.get('last_seen') and 
                datetime.fromisoformat(emp['last_seen'].replace('Z', '+00:00')) > 
                datetime.now() - timedelta(days=7)
            ])
        }
    
    def _extract_story_points(self, fields: Dict[str, Any]) -> Optional[float]:
        """Extract story points from task fields."""
        # Try common story point field names
        story_point_fields = [
            'customfield_10002',  # Common Jira story point field
            'storyPoints', 
            'story points'
        ]
        
        for field_name in story_point_fields:
            if field_name in fields:
                try:
                    return float(fields[field_name])
                except (ValueError, TypeError):
                    continue
        
        # Check if it's in a custom field substructure
        for field_value in fields.values():
            if isinstance(field_value, dict) and 'value' in field_value:
                try:
                    return float(field_value['value'])
                except (ValueError, TypeError):
                    continue
        
        return None
    
    async def create_task_samples(self, tasks: List[Dict[str, Any]], count: int = 10) -> List[JiraTaskSummary]:
        """Create sample task summaries."""
        self.logger.info(f"📋 Creating {count} task samples...")
        
        samples = []
        for task in tasks[:count]:
            fields = task.get('fields', {})
            
            sample = JiraTaskSummary(
                task_id=task.get('id'),
                key=task.get('key'),
                summary=fields.get('summary', ''),
                status=fields.get('status', {}).get('name', 'Unknown'),
                assignee=self._extract_assignee_name(fields.get('assignee')),
                created=fields.get('created', ''),
                updated=fields.get('updated', ''),
                priority=fields.get('priority', {}).get('name', 'Unknown'),
                project=fields.get('project', {}).get('key', 'Unknown'),
                story_points=self._extract_story_points(fields),
                labels=fields.get('labels', []),
                components=[comp.get('name') for comp in fields.get('components', [])]
            )
            
            samples.append(sample)
        
        return samples
    
    async def comprehensive_audit(self) -> JiraAuditResults:
        """Perform comprehensive Jira audit."""
        self.logger.info("🚀 Starting comprehensive Jira audit...")
        
        start_time = datetime.now()
        
        # Test connection first
        connection_status = await self.jira_client.test_connection()
        
        if not connection_status:
            raise Exception("Jira connection failed")
        
        # Get tasks for different time periods
        last_7_days = await self.jira_client.search_issues(
            jql='project = "OPENBD" AND updated >= -7d ORDER BY updated DESC',
            fields=['summary', 'status', 'assignee', 'created', 'updated', 'priority', 'project', 'components', 'labels'],
            max_results=1000
        )
        
        last_30_days = await self.jira_client.search_issues(
            jql='project = "OPENBD" AND updated >= -30d ORDER BY updated DESC',
            fields=['summary', 'status', 'assignee', 'created', 'updated', 'priority', 'project'],
            max_results=1000
        )
        
        all_tasks = await self.jira_client.search_issues(
            jql='project = "OPENBD" ORDER BY updated DESC',
            fields=['summary', 'status', 'assignee', 'created', 'updated', 'priority', 'project', 'components', 'labels'],
            max_results=1000
        )
        
        # Analyze data
        distribution = await self.analyze_task_distribution(all_tasks)
        employee_coverage = await self.analyze_employee_coverage(all_tasks)
        api_limits = await self.test_api_limits()
        task_samples = await self.create_task_samples(all_tasks)
        
        # Calculate时间-based metrics
        now = datetime.now()
        
        tasks_updated_7d = len([
            t for t in all_tasks 
            if t.get('fields', {}).get('updated') and
            datetime.fromisoformat(t['fields']['updated'].replace('Z', '+00:00')) > now - timedelta(days=7)
        ])
        
        tasks_updated_30d = len([
            t for t in all_tasks 
            if t.get('fields', {}).get('updated') and
            datetime.fromisoformat(t['fields']['updated'].replace('Z', '+00:00')) > now - timedelta(days=30)
        ])
        
        tasks_created_30d = len([
            t for t in all_tasks 
            if t.get('fields', {}).get('created') and
            datetime.fromisoformat(t['fields']['created'].replace('Z', '+00:00')) > now - timedelta(days=30)
        ])
        
        # Identify issues and recommendations
        api_limitations = []
        data_quality_issues = []
        recommendations = []
        
        # API limitations
        if len(all_tasks) >= 1000:
            api_limitations.append("API limit reached (1000 tasks) - may not have complete dataset")
        
        if api_limits.get('response_times') and max(rt['response_time'] for rt in api_limits['response_times']) > 10:
            api_limitations.append("Slow API response times detected")
        
        # Data quality issues
        if 'Unassigned' in distribution['by_assignee'] and distribution['by_assignee']['Unassigned'] > len(all_tasks) * 0.1:
            data_quality_issues.append(f"High number of unassigned tasks: {distribution['by_assignee']['Unassigned']}")
        
        # Recommendations
        if tasks_updated_30d < len(all_tasks) * 0.5:
            recommendations.append("Consider archiving old inactive tasks to improve performance")
        
        if employee_coverage['employees_with_recent_activity'] < employee_coverage['total_employees'] * 0.8:
            recommendations.append("Follow up with employees showing no recent activity")
        
        audit_end_time = datetime.now()
        total_time = (audit_end_time - start_time).total_seconds()
        
        results = JiraAuditResults(
            audit_date=start_time,
            connection_status=connection_status,
            total_tasks_found=len(all_tasks),
            date_range_analyzed="Last available tasks up to 1000",
            
            tasks_by_status=distribution['by_status'],
            tasks_by_assignee=distribution['by_assignee'],
            tasks_by_project=distribution['by_project'],
            tasks_by_priority=distribution['by_priority'],
            
            unique_employees=list(employee_coverage['employees'].keys()),
            employees_with_tasks={emp: data['total_tasks'] for emp, data in employee_coverage['employees'].items()},
            
            tasks_updated_last_7_days=tasks_updated_7d,
            tasks_updated_last_30_days=tasks_updated_30d,
            tasks_created_last_30_days=tasks_created_30d,
            
            api_response_time=total_time,
            max_results_per_query=1000,
            total_api_calls=5,  # Number of queries we made
            
            sample_tasks=task_samples,
            
            api_limitations=api_limitations,
            data_quality_issues=data_quality_issues,
            recommendations=recommendations
        )
        
        self.logger.info(f"✅ Jira audit completed in {total_time:.2f}s")
        return results
    
    def generate_specification(self, audit_results: JiraAuditResults) -> Dict[str, Any]:
        """Generate comprehensive Jira integration specification."""
        spec = {
            'integration_overview': {
                'system': 'MTS Jira',
                'endpoint': os.getenv('JIRA_BASE_URL'),
                'authentication': 'Bearer Token',
                'project_scope': 'OPENBD',
                'last_audit': audit_results.audit_date.isoformat(),
                'connection_status': 'operational' if audit_results.connection_status else 'failed'
            },
            
            'data_catalog': {
                'total_tasks_available': audit_results.total_tasks_found,
                'unique_employees': len(audit_results.unique_employees),
                'date_coverage': audit_results.date_range_analyzed,
                'task_fields_available': [
                    'id', 'key', 'summary', 'description', 'status', 'assignee',
                    'reporter', 'priority', 'project', 'components', 'labels',
                    'created', 'updated', 'duedate', 'resolution',
                    'customfield_10002 (story points)'
                ],
                'employee_mapping': audit_results.employees_with_tasks
            },
            
            'task_status_catalog': {
                'active_statuses': [status for status, count in audit_results.tasks_by_status.items() 
                                  if status.lower() not in ['done', 'closed', 'resolved']],
                'completed_statuses': [status for status, count in audit_results.tasks_by_status.items() 
                                     if status.lower() in ['done', 'closed', 'resolved']],
                'status_distribution': audit_results.tasks_by_status
            },
            
            'performance_characteristics': {
                'api_response_time': f"{audit_results.api_response_time:.2f} seconds",
                'max_results_per_query': audit_results.max_results_per_query,
                'estimated_full_sync_time': f"{audit_results.api_response_time * 2:.2f} seconds",
                'recommended_query_intervals': {
                    'realtime': '5 minutes',
                    'hourly': '1 hour',
                    'daily': '24 hours'
                }
            },
            
            'query_patterns': {
                'all_active_tasks': 'project = "OPENBD" AND status IN (In Progress, To Do, Backlog
