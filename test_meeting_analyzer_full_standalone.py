#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест MeetingAnalyzerAgentFull с анализом ПОЛНЫХ протоколов собраний
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.meeting_analyzer_agent_full import MeetingAnalyzerAgentFull

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_meeting_analyzer_full():
    """Тест MeetingAnalyzerAgentFull."""
    print("=" * 80)
    print("TESTING MeetingAnalyzerAgentFull - FULL PROTOCOL TEXT ANALYSIS")
    print("=" * 80)
    
    try:
        # Инициализируем агент
        agent = MeetingAnalyzerAgentFull()
        print(f"✅ Agent initialized: {agent.config.name}")
        print(f"📝 Description: {agent.config.description}")
        print(f"🔢 Version: {agent.config.version}")
        
        # Проверяем состояние
        print("\n📊 Checking agent health...")
        health = await agent.get_health_status()
        print(f"Status: {health['status']}")
        print(f"LLM Client: {health['llm_client']}")
        print(f"Memory Store: {health['memory_store']}")
        print(f"Protocols Directory: {health['protocols_directory']}")
        print(f"Full Text Analysis: {health.get('full_text_analysis', 'unknown')}")
        
        if health['status'] != 'healthy':
            print("⚠️  Agent health is not optimal, continuing test anyway...")
        
        # Сканируем директорию с протоколами
        print("\n🔍 Scanning protocols directory...")
        protocols = await agent.scan_protocols_directory()
        
        if not protocols:
            print("❌ No protocols found for testing")
            return
        
        print(f"✅ Found {len(protocols)} protocol files:")
        for i, protocol in enumerate(protocols[:3]):  # Показываем первые 3
            print(f"  {i+1}. {protocol['filename']} ({protocol['content_length']} chars)")
        
        if len(protocols) > 3:
            print(f"  ... and {len(protocols) - 3} more files")
        
        # Выбираем один протокол для теста
        test_protocol = protocols[0]
        print(f"\n🎯 Testing with protocol: {test_protocol['filename']}")
        print(f"📄 Protocol type: {test_protocol['meeting_type']}")
        print(f"📝 Text length: {test_protocol['content_length']} characters")
        print(f"📋 Text preview: {test_protocol['full_text'][:200]}...")
        
        # Тестируем анализ полного текста
        print("\n🚀 Starting full protocol text analysis...")
        start_time = datetime.now()
        
        result = await agent.execute({'meeting_protocols': [test_protocol]})
        
        execution_time = datetime.now() - start_time
        print(f"⏱️  Analysis completed in {execution_time.total_seconds():.2f} seconds")
        
        if result.success:
            print("✅ Analysis completed successfully!")
            print(f"📊 Message: {result.message}")
            
            # Показываем метаданные
            metadata = result.metadata
            print(f"\n📈 Execution metadata:")
            print(f"  - Execution time: {metadata.get('execution_time', 'N/A'):.2f}s")
            print(f"  - Protocols analyzed: {metadata.get('protocols_analyzed', 'N/A')}")
            print(f"  - Employees analyzed: {metadata.get('employees_analyzed', 'N/A')}")
            print(f"  - Quality score: {metadata.get('quality_score', 'N/A'):.2f}")
            
            # Анализируем результаты
            analysis_data = result.data
            if analysis_data:
                print(f"\n📊 Analysis Results:")
                print(f"  - Total employees: {analysis_data.total_employees}")
                print(f"  - Total meetings: {analysis_data.total_meetings_analyzed}")
                print(f"  - Avg attendance: {analysis_data.avg_attendance_rate:.1%}")
                print(f"  - Total action items: {analysis_data.total_action_items}")
                print(f"  - Team insights: {len(analysis_data.team_collaboration_insights)}")
                print(f"  - Recommendations: {len(analysis_data.recommendations)}")
                
                # Показываем детали по сотрудникам
                if analysis_data.employees_participation:
                    print(f"\n👥 Employee Participation Details:")
                    for name, participation in analysis_data.employees_participation.items():
                        print(f"  👤 {name}:")
                        print(f"    - Speaking turns: {participation.speaking_turns}")
                        print(f"    - Questions: {participation.questions_asked}")
                        print(f"    - Suggestions: {participation.suggestions_made}")
                        print(f"    - Action items: {participation.action_items_assigned}")
                        print(f"    - Engagement: {participation.engagement_score:.2f}")
                        print(f"    - Rating: {participation.participation_rating:.1f}/10")
                        
                        if participation.leadership_indicators:
                            print(f"    - Leadership: {', '.join(participation.leadership_indicators[:2])}")
                        
                        if participation.concerns:
                            print(f"    - Concerns: {', '.join(participation.concerns[:2])}")
                
                # Показываем team insights
                if analysis_data.team_collaboration_insights:
                    print(f"\n💡 Team Insights:")
                    for insight in analysis_data.team_collaboration_insights[:3]:
                        print(f"  • {insight}")
                
                # Показываем рекомендации
                if analysis_data.recommendations:
                    print(f"\n🎯 Recommendations:")
                    for rec in analysis_data.recommendations[:3]:
                        print(f"  • {rec}")
                
                print(f"\n🎉 FULL PROTOCOL TEXT ANALYSIS TEST COMPLETED SUCCESSFULLY!")
                print("✅ MeetingAnalyzerAgentFull is working correctly with full text analysis")
                
            else:
                print("⚠️  No detailed analysis data returned")
        
        else:
            print("❌ Analysis failed!")
            print(f"Error: {result.message}")
            if result.error:
                print(f"Details: {result.error}")
        
        # Проверяем сохраненные отчеты
        print(f"\n📁 Checking saved reports...")
        reports_dir = Path("reports/daily")
        if reports_dir.exists():
            today = datetime.now().strftime("%Y-%m-%d")
            today_reports = list(reports_dir.glob(f"*/meeting-analysis_{today}.json"))
            if today_reports:
                print(f"✅ Found {len(today_reports)} reports for today")
                for report in today_reports:
                    print(f"  📄 {report}")
            else:
                print("⚠️  No reports found for today")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Главная функция теста."""
    await test_meeting_analyzer_full()


if __name__ == "__main__":
    asyncio.run(main())
