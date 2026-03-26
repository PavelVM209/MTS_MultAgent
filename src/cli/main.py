"""
Main CLI Interface for MTS MultAgent System

This module provides command-line interface for running the multi-agent system
with various commands for analysis, configuration, and monitoring.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from dateutil.parser import parse as parse_date

from src.core.config import initialize_config, get_config
from core.models import WorkflowTask, WorkflowResult
from src.agents.jira_agent import JiraAgent

import structlog

logger = structlog.get_logger()


class MTSCLI:
    """Main CLI class for MTS MultAgent System."""
    
    def __init__(self):
        """Initialize CLI with configuration."""
        self.config_manager = None
        self.config = None
        
    def initialize(self, env_file: Optional[str] = None):
        """Initialize configuration and logging."""
        try:
            self.config_manager = initialize_config(env_file)
            self.config = self.config_manager.config
            
            # Setup structured logging
            self._setup_logging()
            
            click.echo(f"✅ MTS MultAgent System initialized")
            click.echo(f"📋 Project: {self.config.project_name}")
            click.echo(f"🔧 Debug mode: {self.config.debug}")
            
        except Exception as e:
            click.echo(f"❌ Failed to initialize: {e}", err=True)
            sys.exit(1)
    
    def _setup_logging(self):
        """Setup structured logging."""
        import structlog
        import logging
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.processors.add_log_level,
                structlog.processors.add_logger_name,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer() if self.config.debug 
                else structlog.processors.JSONRenderer()
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, self.config.logging.level)
            ),
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )


cli_instance = MTSCLI()


@click.group()
@click.option('--env-file', '-e', help='Path to environment file')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.pass_context
def cli(ctx, env_file, debug):
    """MTS MultAgent System - Automated corporate data analysis."""
    ctx.ensure_object(dict)
    
    # Initialize CLI
    cli_instance.initialize(env_file)
    
    if debug:
        cli_instance.config.debug = True
        cli_instance._setup_logging()


@cli.command()
@click.option('--task', '-t', required=True, help='Task description to analyze')
@click.option('--project-key', '-p', help='Jira project key')
@click.option('--keywords', '-k', multiple=True, help='Search keywords (can be used multiple times)')
@click.option('--date-from', help='Start date for filtering (YYYY-MM-DD)')
@click.option('--date-to', help='End date for filtering (YYYY-MM-DD)')
@click.option('--output', '-o', help='Output file for results (JSON)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def analyze(task, project_key, keywords, date_from, date_to, output, verbose):
    """Analyze project task using multi-agent system."""
    
    async def run_analysis():
        try:
            # Prepare task
            workflow_task = WorkflowTask(
                description=task,
                project_key=project_key,
                keywords=list(keywords) if keywords else [],
                date_range={"from": date_from, "to": date_to} if date_from or date_to else None
            )
            
            if verbose:
                click.echo("🚀 Starting analysis...")
                click.echo(f"📝 Task: {task}")
                click.echo(f"🔑 Project: {project_key or 'Auto-detect'}")
                click.echo(f" Keywords: {workflow_task.keywords}")
            
            # Execute analysis
            result = await execute_workflow(workflow_task, verbose)
            
            # Output results
            if result.success:
                click.echo("✅ Analysis completed successfully!")
                
                if verbose:
                    _print_detailed_results(result)
                else:
                    _print_summary_results(result)
                
                # Save to file if requested
                if output:
                    with open(output, 'w', encoding='utf-8') as f:
                        json.dump(result.dict(), f, indent=2, ensure_ascii=False, default=str)
                    click.echo(f"💾 Results saved to: {output}")
                
            else:
                click.echo("❌ Analysis failed!")
                click.echo(f"Error: {'; '.join(result.errors)}")
                sys.exit(1)
                
        except KeyboardInterrupt:
            click.echo("\n⏹️  Analysis cancelled by user")
            sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Unexpected error: {e}")
            if cli_instance.config.debug:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    # Run async analysis
    asyncio.run(run_analysis())


@cli.command()
@click.option('--project-key', '-p', required=True, help='Jira project key')
@click.option('--keywords', '-k', multiple=True, help='Search keywords')
@click.option('--limit', '-l', default=20, help='Maximum number of issues')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json', 'summary']), 
              default='summary', help='Output format')
def jira(project_key, keywords, limit, output_format):
    """Search and display Jira issues."""
    
    async def run_jira_search():
        try:
            # Create Jira agent
            agent_config = cli_instance.config_manager.get_agent_config("JiraAgent")
            async with JiraAgent(agent_config) as agent:
                
                if keywords:
                    click.echo(f"🔍 Searching Jira for project {project_key} with keywords: {list(keywords)}")
                else:
                    click.echo(f"🔍 Searching Jira for project {project_key}")
                
                # Execute search
                task_data = {
                    "project_key": project_key,
                    "task_description": f"Search for issues in {project_key}",
                    "search_keywords": list(keywords) if keywords else [],
                    "max_results": limit
                }
                
                result = await agent.execute_with_fallback(task_data)
                
                if result.success:
                    data = result.data
                    
                    if output_format == 'table':
                        _print_jira_table(data['issues'])
                    elif output_format == 'json':
                        click.echo(json.dumps(data, indent=2, ensure_ascii=False, default=str))
                    else:  # summary
                        _print_jira_summary(data)
                        
                else:
                    click.echo(f"❌ Jira search failed: {result.error}")
                    sys.exit(1)
                    
        except Exception as e:
            click.echo(f"❌ Error: {e}")
            sys.exit(1)
    
    asyncio.run(run_jira_search())


@cli.command()
@click.option('--agent', '-a', help='Check specific agent (jira, excel, confluence, etc.)')
def health(agent):
    """Check system health and agent status."""
    
    async def run_health_check():
        try:
            click.echo("🏥 System Health Check")
            click.echo("=" * 50)
            
            # Check configuration
            click.echo("📋 Configuration:")
            click.echo(f"  Project: {cli_instance.config.project_name}")
            click.echo(f"  Jira URL: {cli_instance.config.jira.base_url}")
            click.echo(f"  Confluence URL: {cli_instance.config.confluence.base_url}")
            click.echo(f"  Debug mode: {cli_instance.config.debug}")
            
            if agent and agent.lower() == 'jira':
                await _check_jira_health()
            elif agent and agent.lower() == 'all':
                await _check_all_agents_health()
            else:
                click.echo(f"\n💡 Use --agent jira to check specific agent health")
            
        except Exception as e:
            click.echo(f"❌ Health check failed: {e}")
            sys.exit(1)
    
    asyncio.run(run_health_check())


@cli.command()
def config():
    """Display current configuration."""
    click.echo("⚙️  Current Configuration")
    click.echo("=" * 50)
    
    click.echo(f"Project: {cli_instance.config.project_name}")
    click.echo(f"Debug: {cli_instance.config.debug}")
    click.echo(f"Test Mode: {cli_instance.config.test_mode}")
    
    click.echo("\n🔗 Jira Configuration:")
    click.echo(f"  Base URL: {cli_instance.config.jira.base_url}")
    click.echo(f"  Username: {cli_instance.config.jira.username}")
    click.echo(f"  Timeout: {cli_instance.config.jira.timeout}s")
    
    click.echo("\n📝 Confluence Configuration:")
    click.echo(f"  Base URL: {cli_instance.config.confluence.base_url}")
    click.echo(f"  Space: {cli_instance.config.confluence.space}")
    click.echo(f"  Root Page ID: {cli_instance.config.confluence.root_page_id}")
    
    click.echo("\n⚡ Performance Configuration:")
    click.echo(f"  Max Concurrent: {cli_instance.config.performance.max_concurrent_requests}")
    click.echo(f"  Cache TTL: {cli_instance.config.performance.cache_ttl_seconds}s")
    click.echo(f"  Retry Attempts: {cli_instance.config.performance.retry_max_attempts}")


async def execute_workflow(task: WorkflowTask, verbose: bool = False) -> WorkflowResult:
    """
    Execute complete workflow with all agents.
    
    Currently implements JiraAgent only. Other agents will be added.
    """
    result = WorkflowResult(success=False, errors=[])
    
    try:
        # Phase 1: Jira Analysis
        if verbose:
            click.echo("📡 Phase 1: Jira Analysis...")
        
        agent_config = cli_instance.config_manager.get_agent_config("JiraAgent")
        async with JiraAgent(agent_config) as jira_agent:
            jira_task = {
                "project_key": task.project_key or cli_instance.config.project_name,
                "task_description": task.description,
                "search_keywords": task.keywords,
                "max_results": 50
            }
            
            jira_result = await jira_agent.execute_with_fallback(jira_task)
            if jira_result.success:
                result.jira_result = type('JiraResult', (), jira_result.data)()
                if verbose:
                    click.echo(f"  ✅ Found {len(jira_result.data['issues'])} issues")
            else:
                result.errors.append(f"Jira analysis failed: {jira_result.error}")
                if verbose:
                    click.echo(f"  ❌ Jira analysis failed")
                return result
        
        # TODO: Phase 2: Context Analysis
        # TODO: Phase 3: Excel Processing
        # TODO: Phase 4: Comparison
        # TODO: Phase 5: Confluence Publishing
        
        result.success = True
        result.execution_summary = {
            "phases_completed": ["jira"],
            "total_issues": len(result.jira_result.issues) if result.jira_result else 0,
            "execution_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        result.errors.append(f"Workflow execution failed: {str(e)}")
        result.success = False
    
    return result


def _print_summary_results(result: WorkflowResult):
    """Print summary of workflow results."""
    click.echo("\n📊 Analysis Summary:")
    click.echo("=" * 30)
    
    if result.jira_result:
        click.echo(f"📋 Issues found: {len(result.jira_result.issues)}")
        click.echo(f"📝 Meeting protocols: {len(result.jira_result.meeting_protocols)}")
        click.echo(f"💬 Comments extracted: {len(result.jira_result.comments)}")
    
    if result.execution_summary:
        click.echo(f"⏱️  Execution time: {result.execution_summary.get('execution_time', 'N/A')}")


def _print_detailed_results(result: WorkflowResult):
    """Print detailed workflow results."""
    if result.jira_result:
        click.echo(f"\n📋 Jira Results ({len(result.jira_result.issues)} issues):")
        for issue in result.jira_result.issues[:5]:  # Show first 5
            click.echo(f"  • {issue['key']}: {issue['summary']}")
            click.echo(f"    Status: {issue['status']}, Assignee: {issue['assignee'] or 'Unassigned'}")
        
        if len(result.jira_result.issues) > 5:
            click.echo(f"  ... and {len(result.jira_result.issues) - 5} more issues")
    
    if result.jira_result and result.jira_result.meeting_protocols:
        click.echo(f"\n📝 Meeting Protocols ({len(result.jira_result.meeting_protocols)}):")
        for protocol in result.jira_result.meeting_protocols:
            click.echo(f"  • {protocol['title']}")
            click.echo(f"    Date: {protocol['date']}, Attendees: {len(protocol['attendees'])}")


def _print_jira_table(issues: List[Dict]):
    """Print Jira issues in table format."""
    if not issues:
        click.echo("No issues found.")
        return
    
    click.echo(f"\n📋 Found {len(issues)} issues:")
    click.echo("-" * 80)
    click.echo(f"{'Key':<10} {'Status':<15} {'Assignee':<20} {'Summary':<35}")
    click.echo("-" * 80)
    
    for issue in issues[:20]:  # Limit to 20 for readability
        key = issue['key']
        status = issue['status'][:14]
        assignee = (issue['assignee'] or 'Unassigned')[:19]
        summary = issue['summary'][:34]
        click.echo(f"{key:<10} {status:<15} {assignee:<20} {summary:<35}")


def _print_jira_summary(data: Dict):
    """Print Jira results summary."""
    issues = data['issues']
    search_summary = data.get('search_summary', {})
    
    click.echo(f"\n📊 Jira Search Summary:")
    click.echo(f"  Project: {search_summary.get('project_key', 'N/A')}")
    click.echo(f"  Keywords: {', '.join(search_summary.get('keywords', []))}")
    click.echo(f"  Issues found: {len(issues)}")
    
    if issues:
        # Status breakdown
        status_counts = {}
        for issue in issues:
            status = issue['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        click.echo(f"\n📈 Status Breakdown:")
        for status, count in status_counts.items():
            click.echo(f"  {status}: {count}")
        
        # Recent issues
        click.echo(f"\n🕐 Recent Issues:")
        for issue in issues[:5]:
            click.echo(f"  • {issue['key']}: {issue['summary']}")


async def _check_jira_health():
    """Check Jira agent health."""
    try:
        click.echo("\n🔍 Checking Jira Agent Health...")
        
        agent_config = cli_instance.config_manager.get_agent_config("JiraAgent")
        async with JiraAgent(agent_config) as agent:
            health = await agent.health_check()
            
            click.echo(f"  Status: {health['status']}")
            click.echo(f"  Configured: {health['jira_configured']}")
            
            jira_health = health.get('jira_health', {})
            click.echo(f"  API Connected: {jira_health.get('api_connected', False)}")
            
            if jira_health.get('error'):
                click.echo(f"  Error: {jira_health['error']}")
                
    except Exception as e:
        click.echo(f"  Health check failed: {e}")


async def _check_all_agents_health():
    """Health check for all agents."""
    await _check_jira_health()
    
    # TODO: Add health checks for other agents
    click.echo("\n📝 Context Analyzer: Not implemented yet")
    click.echo("🔗 Confluence Agent: Not implemented yet")
    click.echo("⚖️ Comparison Agent: Not implemented yet")


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == '__main__':
    main()
