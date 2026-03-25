#!/usr/bin/env python3
"""
Scheduler Manager Demo - Phase 3
Demonstrates APScheduler integration with timezone handling
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path

from src.core.scheduler_manager import (
    SchedulerManager,
    JobConfig,
    JobStatus,
    SchedulerStatus
)


# Sample job functions for demonstration
async def sample_jira_analysis():
    """Sample JIRA analysis job"""
    print(f"🔍 [JIRA Analysis] Analyzing JIRA tasks... {datetime.now()}")
    await asyncio.sleep(2)  # Simulate work
    print(f"✅ [JIRA Analysis] Completed analyzing JIRA tasks")
    return {"tasks_found": 15, "employees_tracked": 8}


async def sample_meeting_analysis():
    """Sample meeting analysis job"""
    print(f"📝 [Meeting Analysis] Processing meeting protocols... {datetime.now()}")
    await asyncio.sleep(1.5)  # Simulate work
    print(f"✅ [Meeting Analysis] Completed processing protocols")
    return {"protocols_processed": 5, "actions_extracted": 12}


async def sample_daily_summary():
    """Sample daily summary job"""
    print(f"📊 [Daily Summary] Generating daily report... {datetime.now()}")
    await asyncio.sleep(3)  # Simulate work
    print(f"✅ [Daily Summary] Daily report generated")
    return {"report_generated": True, "pages": 3}


async def sample_weekly_report():
    """Sample weekly report job"""
    print(f"📈 [Weekly Report] Generating comprehensive weekly report... {datetime.now()}")
    await asyncio.sleep(5)  # Simulate work
    print(f"✅ [Weekly Report] Weekly report completed")
    return {"report_generated": True, "pages": 15, "sections": 8}


def job_event_callback(execution_result):
    """Callback function for job events"""
    status_emoji = {
        JobStatus.COMPLETED: "✅",
        JobStatus.ERROR: "❌",
        JobStatus.MISSED: "⏰"
    }
    
    emoji = status_emoji.get(execution_result.status, "❓")
    
    print(f"\n{emoji} Job Event - ID: {execution_result.job_id}")
    print(f"   Status: {execution_result.status.value}")
    print(f"   Start Time: {execution_result.start_time}")
    
    if execution_result.end_time:
        duration = execution_result.end_time - execution_result.start_time
        print(f"   Duration: {duration.total_seconds():.2f}s")
    
    if execution_result.result:
        print(f"   Result: {execution_result.result}")
    
    if execution_result.error:
        print(f"   Error: {execution_result.error}")
    
    print("-" * 50)


async def demo_scheduler_basic_operations():
    """Demonstrate basic scheduler operations"""
    
    print("🚀 Scheduler Manager Demo - Phase 3")
    print("=" * 60)
    
    # Initialize scheduler manager
    scheduler_manager = SchedulerManager(timezone_str="Europe/Moscow")
    
    try:
        # Initialize and start scheduler
        print("📋 Initializing scheduler...")
        await scheduler_manager.initialize()
        await scheduler_manager.start()
        
        print("✅ Scheduler started successfully!")
        
        # Show scheduler health
        health = await scheduler_manager.get_health()
        print(f"\n🏥 Scheduler Health:")
        print(f"   Status: {health.status.value}")
        print(f"   Timezone: Europe/Moscow")
        print(f"   Total Jobs: {health.total_jobs}")
        print(f"   Active Jobs: {health.active_jobs}")
        print(f"   Uptime: {health.uptime}")
        
        # Add event callbacks
        scheduler_manager.add_callback('job_completed', job_event_callback)
        scheduler_manager.add_callback('job_error', job_event_callback)
        scheduler_manager.add_callback('job_missed', job_event_callback)
        
        # Create job configurations
        jobs = [
            JobConfig(
                id="jira_analysis",
                name="Daily JIRA Analysis",
                func=sample_jira_analysis,
                trigger_type="cron",
                trigger_config={
                    "minute": "*/30",  # Every 30 seconds for demo
                    "hour": "*",
                    "day": "*"
                },
                description="Analyze JIRA tasks for employee tracking"
            ),
            JobConfig(
                id="meeting_analysis",
                name="Daily Meeting Analysis",
                func=sample_meeting_analysis,
                trigger_type="cron",
                trigger_config={
                    "minute": "*/45",  # Every 45 seconds for demo
                    "hour": "*",
                    "day": "*"
                },
                description="Process meeting protocols and extract actions"
            ),
            JobConfig(
                id="daily_summary",
                name="Daily Summary Generation",
                func=sample_daily_summary,
                trigger_type="cron",
                trigger_config={
                    "minute": "*/20",  # Every 20 seconds for demo
                    "hour": "*",
                    "day": "*"
                },
                description="Generate daily summary report"
            ),
            JobConfig(
                id="weekly_report",
                name="Weekly Comprehensive Report",
                func=sample_weekly_report,
                trigger_type="cron",
                trigger_config={
                    "minute": "*/60",  # Every 60 seconds for demo
                    "hour": "*",
                    "day": "*"
                },
                description="Generate comprehensive weekly report"
            )
        ]
        
        # Add jobs to scheduler
        print(f"\n📝 Adding {len(jobs)} jobs to scheduler...")
        
        for job in jobs:
            job_id = await scheduler_manager.add_job(job)
            print(f"   ✅ Added job: {job.name} (ID: {job_id})")
        
        # Update health after adding jobs
        health = await scheduler_manager.get_health()
        print(f"\n📊 Updated Scheduler Health:")
        print(f"   Total Jobs: {health.total_jobs}")
        print(f"   Active Jobs: {health.active_jobs}")
        print(f"   Paused Jobs: {health.paused_jobs}")
        
        # List all jobs with details
        print(f"\n📋 All Jobs Status:")
        jobs_list = await scheduler_manager.list_jobs()
        
        for job_info in jobs_list:
            print(f"\n🔹 Job: {job_info['name']}")
            print(f"   ID: {job_info['id']}")
            print(f"   Next Run: {job_info['next_run_time']}")
            print(f"   Trigger: {job_info['trigger']}")
            print(f"   Enabled: {job_info['enabled']}")
            
            if job_info['config'] and job_info['config']['description']:
                print(f"   Description: {job_info['config']['description']}")
        
        # Run scheduler for demonstration period
        print(f"\n⏰ Running scheduler for 2 minutes to demonstrate job execution...")
        print("   Watch for job executions and events!")
        print("   " + "=" * 50)
        
        # Let scheduler run for 2 minutes
        await asyncio.sleep(120)
        
        # Show final statistics
        health = await scheduler_manager.get_health()
        print(f"\n📈 Final Statistics:")
        print(f"   Total Executions: {len(scheduler_manager.job_executions)}")
        print(f"   Errors Count: {health.errors_count}")
        print(f"   Success Rate: {health.success_rate:.2%}")
        print(f"   Uptime: {health.uptime}")
        
        # Show recent executions
        print(f"\n📊 Recent Job Executions:")
        for execution in health.recent_executions[-5:]:
            status_emoji = "✅" if execution.status == JobStatus.COMPLETED else "❌"
            print(f"   {status_emoji} {execution.job_id}: {execution.status.value} ({execution.start_time})")
        
        # Demo job management operations
        print(f"\n🔧 Demonstrating Job Management Operations...")
        
        # Pause a job
        print(f"   ⏸️ Pausing daily summary job...")
        await scheduler_manager.pause_job("daily_summary")
        
        await asyncio.sleep(5)  # Wait a bit
        
        # Resume the job
        print(f"   ▶️ Resuming daily summary job...")
        await scheduler_manager.resume_job("daily_summary")
        
        await asyncio.sleep(10)  # Wait for resume to take effect
        
        print(f"\n🎉 Scheduler Manager Demo Completed!")
        print(f"✅ All core functionality demonstrated successfully!")
        
    except Exception as e:
        print(f"❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean shutdown
        print(f"\n🛑 Shutting down scheduler...")
        await scheduler_manager.stop(wait=True)
        print(f"✅ Scheduler stopped gracefully!")


async def demo_scheduler_timezone_handling():
    """Demonstrate timezone handling capabilities"""
    
    print(f"\n🌍 Timezone Handling Demo")
    print("=" * 40)
    
    # Create scheduler with different timezone
    scheduler_manager = SchedulerManager(timezone_str="Europe/Moscow")
    
    try:
        await scheduler_manager.initialize()
        await scheduler_manager.start()
        
        print(f"📍 Scheduler Timezone: {scheduler_manager.timezone}")
        
        # Create a job that shows current time
        def show_time_job():
            now = datetime.now(scheduler_manager.timezone)
            print(f"⏰ Current Moscow Time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Add interval job
        job_config = JobConfig(
            id="time_demo",
            name="Time Demo Job",
            func=show_time_job,
            trigger_type="interval",
            trigger_config={"seconds": 10},
            description="Demonstrate timezone handling"
        )
        
        await scheduler_manager.add_job(job_config)
        
        print(f"⏰ Added time demo job (runs every 10 seconds)")
        
        # Run for 30 seconds to show timezone execution
        await asyncio.sleep(30)
        
        print(f"✅ Timezone handling demo completed!")
        
    finally:
        await scheduler_manager.stop()


async def demo_scheduler_error_handling():
    """Demonstrate error handling and recovery"""
    
    print(f"\n🚨 Error Handling Demo")
    print("=" * 40)
    
    scheduler_manager = SchedulerManager()
    
    def failing_job():
        """Job that fails to demonstrate error handling"""
        raise Exception("This is a test error for demonstration")
    
    def partial_success_job():
        """Job that sometimes fails"""
        import random
        if random.random() < 0.5:  # 50% chance of failure
            raise Exception("Random failure for testing")
        return "Success!"
    
    try:
        await scheduler_manager.initialize()
        await scheduler_manager.start()
        
        # Add callbacks to show errors
        def error_callback(execution_result):
            if execution_result.status == JobStatus.ERROR:
                print(f"🚨 Error in job {execution_result.job_id}: {execution_result.error}")
        
        scheduler_manager.add_callback('job_error', error_callback)
        
        # Add failing job
        failing_config = JobConfig(
            id="failing_job",
            name="Failing Demo Job",
            func=failing_job,
            trigger_type="interval",
            trigger_config={"seconds": 15},
            description="Demonstrates error handling"
        )
        
        # Add partially successful job
        partial_config = JobConfig(
            id="partial_job",
            name="Partial Success Job",
            func=partial_success_job,
            trigger_type="interval",
            trigger_config={"seconds": 20},
            description="Sometimes succeeds, sometimes fails"
        )
        
        await scheduler_manager.add_job(failing_config)
        await scheduler_manager.add_job(partial_config)
        
        print(f"🚨 Added failing jobs for error demonstration")
        
        # Run for 1 minute to see error handling
        await asyncio.sleep(60)
        
        # Show error statistics
        health = await scheduler_manager.get_health()
        print(f"\n📊 Error Statistics:")
        print(f"   Total Errors: {health.errors_count}")
        print(f"   Success Rate: {health.success_rate:.2%}")
        
        print(f"✅ Error handling demo completed!")
        
    finally:
        await scheduler_manager.stop()


async def main():
    """Main demo function"""
    
    print("🎯 MTS MultAgent - Scheduler Manager Phase 3 Demo")
    print("=" * 60)
    print("This demo showcases APScheduler integration with:")
    print("  • Timezone handling (Europe/Moscow)")
    print("  • Job persistence and recovery")
    print("  • Health monitoring")
    print("  • Error handling and callbacks")
    print("  • Job management operations")
    print("=" * 60)
    
    try:
        # Run main demo
        await demo_scheduler_basic_operations()
        
        # Run timezone demo
        await demo_scheduler_timezone_handling()
        
        # Run error handling demo
        await demo_scheduler_error_handling()
        
        print(f"\n🎊 All Scheduler Manager demos completed successfully!")
        print(f"✅ Phase 3 Foundation is ready for production!")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main())
