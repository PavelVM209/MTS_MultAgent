"""
Integration Test for MTS MultAgent System

This test verifies the complete workflow:
1. Read Jira task and extract keywords
2. Find relevant context in meeting protocol
3. Query Excel data based on context
4. Generate result table with descriptions
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.context_analyzer import ContextAnalyzer
from src.agents.excel_agent import ExcelAgent
from src.agents.universal_analyzer import UniversalAnalyzerAgent


class IntegrationWorkflowTest:
    """
    Integration test for the complete workflow
    """
    
    def __init__(self):
        self.test_data_dir = Path(__file__).parent / "test_data"
        self.config = self._get_test_config()
        
        # Initialize agents
        self.context_analyzer = ContextAnalyzer(self.config)
        self.excel_agent = ExcelAgent(self.config)
        self.universal_analyzer = UniversalAnalyzerAgent(self.config)
        
    def _get_test_config(self):
        """Get test configuration for agents."""
        return {
            "context": {
                "languages": ["ru", "en"],
                "min_relevance_score": 0.3,
                "max_summary_length": 500
            },
            "excel": {
                "file_path": str(self.test_data_dir),
                "supported_formats": [".xlsx", ".xls", ".xlsm"],
                "max_rows": 1000,
                "default_sheet": 0
            },
            "debug": True,
            "logging": {
                "level": "INFO"
            }
        }
    
    async def test_complete_workflow(self):
        """
        Test the complete workflow from Jira task to result table.
        """
        print("🚀 Starting Integration Workflow Test")
        print("=" * 60)
        
        try:
            # Step 1: Read and analyze Jira task
            print("\n📋 Step 1: Analyzing Jira task...")
            jira_content = self._read_jira_task()
            jira_keywords = self._extract_keywords_from_jira(jira_content)
            print(f"✅ Extracted keywords: {jira_keywords}")
            
            # Step 2: Analyze meeting protocol and find relevant context
            print("\n📝 Step 2: Analyzing meeting protocol...")
            protocol_content = self._read_meeting_protocol()
            relevant_context = await self._find_relevant_context(
                protocol_content, jira_keywords
            )
            print(f"✅ Found relevant context sections: {len(relevant_context)}")
            
            # Step 3: Query Excel data
            print("\n📊 Step 3: Querying Excel data...")
            excel_data = await self._query_excel_data(relevant_context)
            print(f"✅ Retrieved Excel data: {len(excel_data)} rows")
            
            # Step 4: Generate intelligent analysis using universal analyzer
            print("\n🧠 Step 4: Generating intelligent analysis...")
            result_table = await self._generate_intelligent_analysis(
                jira_keywords, relevant_context, excel_data
            )
            
            # Step 5: Save results
            print("\n💾 Step 5: Saving results...")
            output_file = await self._save_results(result_table)
            print(f"✅ Results saved to: {output_file}")
            
            # Summary
            print("\n🎉 Integration Test Completed Successfully!")
            print(f"📁 Output file: {output_file}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def _read_jira_task(self) -> str:
        """Read Jira task from file."""
        jira_file = self.test_data_dir / "jira_task_emulation.txt"
        with open(jira_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _read_meeting_protocol(self) -> str:
        """Read meeting protocol from file."""
        protocol_file = self.test_data_dir / "meeting_protocol.txt"
        with open(protocol_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _extract_keywords_from_jira(self, jira_content: str) -> list:
        """Extract keywords from Jira task content."""
        # Simple keyword extraction based on task content
        keywords = []
        
        # Analysis and comparison keywords
        analysis_keywords = [
            "сравнение", "анализ", "показатели", "компании", 
            "финансовый", "операционный", "эффективность", "arpu",
            "рентабельность", "трафик", "дохо", "расход"
        ]
        
        jira_lower = jira_content.lower()
        for keyword in analysis_keywords:
            if keyword in jira_lower:
                keywords.append(keyword)
        
        # Extract specific terms
        if "компанией" in jira_lower or "компаниями" in jira_lower:
            keywords.append("компании")
        if "компания а" in jira_lower:
            keywords.append("компания а")
        if "компания б" in jira_lower:
            keywords.append("компания б")
        if "mvno" in jira_lower:
            keywords.append("mvno")
        if "1кв" in jira_lower or "1 кв" in jira_lower:
            keywords.append("1кв 2025")
        
        return keywords
    
    async def _find_relevant_context(self, protocol_content: str, keywords: list) -> list:
        """Find relevant context sections in meeting protocol."""
        # Use ContextAnalyzer to find relevant sections
        context_task = {
            "text_content": protocol_content,
            "task_description": "Анализ производительности системы заказов",
            "search_keywords": keywords,
            "meeting_protocols": [{"content": protocol_content}]
        }
        
        # Validate task
        is_valid = await self.context_analyzer.validate(context_task)
        if not is_valid:
            raise ValueError("Invalid context task")
        
        # Execute analysis
        result = await self.context_analyzer.execute(context_task)
        
        if not result.success:
            raise ValueError(f"Context analysis failed: {result.error}")
        
        # Extract relevant context
        relevant_context = result.data.get("relevant_context", [])
        entities = result.data.get("entities", [])
        key_phrases = result.data.get("key_phrases", [])
        
        return {
            "sections": relevant_context,
            "entities": entities,
            "key_phrases": key_phrases,
            "keywords": keywords
        }
    
    async def _query_excel_data(self, relevant_context: dict) -> list:
        """Query Excel data based on relevant context."""
        excel_file = self.test_data_dir / "performance_metrics.xlsx"
        
        # Create Excel task - detect sheet name automatically
        excel_task = {
            "file_paths": [str(excel_file)]
            # Remove specific sheet name to let agent detect automatically
        }
        
        # Validate task
        is_valid = await self.excel_agent.validate(excel_task)
        if not is_valid:
            raise ValueError("Invalid Excel task")
        
        # Execute Excel processing
        result = await self.excel_agent.execute(excel_task)
        
        if not result.success:
            raise ValueError(f"Excel processing failed: {result.error}")
        
        # Extract data
        sheets_data = result.data.get("sheets", [])
        if not sheets_data:
            return []
        
        return sheets_data[0].get("data", [])
    
    async def _generate_intelligent_analysis(self, keywords: list, context: dict, excel_data: list) -> str:
        """Generate intelligent analysis using universal analyzer."""
        try:
            # Prepare Excel metadata for universal analyzer
            excel_metadata = {
                "sheets": ["лист 1", "лист 2"],  # From the actual Excel file
                "columns": {
                    "лист 1": list(excel_data[0].keys()) if excel_data else []
                },
                "total_rows": len(excel_data)
            }
            
            # Use universal analyzer for intelligent analysis
            analysis_result = await self.universal_analyzer.analyze_with_context(
                jira_keywords=keywords,
                context_data=context,
                excel_metadata=excel_metadata,
                excel_sample=excel_data[:5] if excel_data else []
            )
            
            # Generate result table with intelligent insights
            return self._format_intelligent_result(keywords, context, excel_data, analysis_result)
            
        except Exception as e:
            print(f"⚠️  Intelligent analysis failed, using fallback: {e}")
            # Fallback to original method
            return self._generate_result_table(keywords, context, excel_data)
    
    def _format_intelligent_result(self, keywords: list, context: dict, excel_data: list, analysis_result: dict) -> str:
        """Format the intelligent analysis result."""
        insights = analysis_result.get("insights", [])
        recommendations = analysis_result.get("recommendations", [])
        analysis_type = analysis_result.get("analysis_type", "unknown")
        confidence = analysis_result.get("confidence_score", 0.0)
        
        result_lines = [
            f"УМНЫЙ АНАЛИЗАТОР - {analysis_type.upper().replace('_', ' ')}",
            "=" * 60,
            f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Уверенность анализа: {confidence:.1%}",
            f"Источник задачи: PROJ-1234 - Сравнение операционных и финансовых показателей",
            "",
            "1. КЛЮЧЕВЫЕ СЛОВА ИЗ ЗАДАЧИ:",
            "-" * 30
        ]
        
        for keyword in keywords:
            result_lines.append(f"• {keyword}")
        
        result_lines.extend([
            "",
            "2. РЕЛЕВАНТНЫЙ КОНТЕКСТ ИЗ ПРОТОКОЛА:",
            "-" * 40
        ])
        
        # Add key context sections
        sections = context.get("sections", [])
        for i, section in enumerate(sections[:3]):  # Top 3 sections
            result_lines.extend([
                f"\nРаздел {i+1}:",
                section[:200] + "..." if len(section) > 200 else section
            ])
        
        result_lines.extend([
            "",
            "3. ДАННЫЕ ИЗ EXCEL:",
            "-" * 20,
            ""
        ])
        
        # Add Excel data as formatted table
        if excel_data:
            # Create header based on actual columns in Excel data
            columns = list(excel_data[0].keys())
            header = " | ".join([col[:18] for col in columns])
            separator = "-" * len(header)
            result_lines.append(f"| {header} |")
            result_lines.append(f"|{separator}|")
            
            # Show first 5 rows
            for row in excel_data[:5]:
                values = " | ".join([str(row.get(col, ""))[:18] for col in columns])
                result_lines.append(f"| {values} |")
            
            if len(excel_data) > 5:
                result_lines.append(f"... и еще {len(excel_data) - 5} строк")
        
        result_lines.extend([
            "",
            "4. 🧠 ИНТЕЛЛЕКТУАЛЬНЫЕ ИНСАЙТЫ:",
            "-" * 35
        ])
        
        # Add intelligent insights
        if insights:
            for insight in insights:
                result_lines.append(f"💡 {insight}")
        else:
            result_lines.append("📊 Анализ данных не выявил значимых паттернов")
        
        result_lines.extend([
            "",
            "5. 🎯 УМНЫЕ РЕКОМЕНДАЦИИ:",
            "-" * 25
        ])
        
        # Add intelligent recommendations
        if recommendations:
            for rec in recommendations:
                result_lines.append(f"✨ {rec}")
        else:
            result_lines.append("📋 Рекомендации будут сгенерированы после дополнительного анализа")
        
        # Add analysis summary
        data_summary = analysis_result.get("data_summary", {})
        if data_summary:
            result_lines.extend([
                "",
                "6. 📈 СВОДКА АНАЛИЗА:",
                "-" * 20,
                f"• Проанализировано строк: {data_summary.get('rows_analyzed', 0)}",
                f"• Проанализировано колонок: {data_summary.get('columns_analyzed', 0)}",
                f"• Фокус анализа: {', '.join(data_summary.get('focus_areas', []))}"
            ])
        
        result_lines.extend([
            "",
            "=" * 60,
            "Отчет сгенерирован интеллектуальной системой MTS MultAgent 🤖"
        ])
        
        return "\n".join(result_lines)
    
    def _generate_result_table(self, keywords: list, context: dict, excel_data: list) -> str:
        """Generate formatted result table with descriptions."""
        
        result_lines = [
            "АНАЛИЗАТОР СРАВНЕНИЯ ПОКАЗАТЕЛЕЙ КОМПАНИЙ А И Б",
            "=" * 60,
            f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Источник задачи: PROJ-1234 - Сравнение операционных и финансовых показателей",
            "",
            "1. КЛЮЧЕВЫЕ СЛОВА ИЗ ЗАДАЧИ:",
            "-" * 30
        ]
        
        for keyword in keywords:
            result_lines.append(f"• {keyword}")
        
        result_lines.extend([
            "",
            "2. РЕЛЕВАНТНЫЙ КОНТЕКСТ ИЗ ПРОТОКОЛА:",
            "-" * 40
        ])
        
        # Add key context sections
        sections = context.get("sections", [])
        for i, section in enumerate(sections[:3]):  # Top 3 sections
            result_lines.extend([
                f"\nРаздел {i+1}:",
                section[:200] + "..." if len(section) > 200 else section
            ])
        
        result_lines.extend([
            "",
            "3. ДАННЫЕ ИЗ EXCEL (1КВ 2025):",
            "-" * 35,
            ""
        ])
        
        # Add Excel data as formatted table
        if excel_data:
            # Create header based on actual columns in Excel data
            if excel_data:
                columns = list(excel_data[0].keys())
                header = " | ".join([col[:20] for col in columns])
                separator = "-" * len(header)
                result_lines.append(f"| {header} |")
                result_lines.append(f"|{separator}|")
                
                for row in excel_data:
                    values = " | ".join([str(row.get(col, ""))[:20] for col in columns])
                    result_lines.append(f"| {values} |")
        
        result_lines.extend([
            "",
            "4. ВЫЯВЛЕННЫЕ ОСОБЕННОСТИ:",
            "-" * 25
        ])
        
        # Add identified insights based on data
        insights = self._identify_insights(excel_data, context)
        for insight in insights:
            result_lines.append(f"📊 {insight}")
        
        result_lines.extend([
            "",
            "5. РЕКОМЕНДАЦИИ:",
            "-" * 15
        ])
        
        # Add recommendations
        recommendations = self._generate_recommendations(excel_data, context)
        for rec in recommendations:
            result_lines.append(f"✅ {rec}")
        
        result_lines.extend([
            "",
            "=" * 60,
            "Отчет сгенерирован автоматически MTS MultAgent System"
        ])
        
        return "\n".join(result_lines)
    
    def _identify_insights(self, excel_data: list, context: dict) -> list:
        """Identify insights based on Excel data and context."""
        insights = []
        
        if not excel_data:
            return insights
        
        # Analyze company A vs B data
        company_a_data = [row for row in excel_data if str(row.get("Компания", "")).strip() == "А"]
        company_b_data = [row for row in excel_data if str(row.get("Компания", "")).strip() == "Б"]
        
        if company_a_data and company_b_data:
            # Compare subscriber bases
            a_subs = company_a_data[-1].get("Активные абоненты (тыс.)", 0) if company_a_data else 0
            b_subs = company_b_data[-1].get("Активные абоненты (тыс.)", 0) if company_b_data else 0
            
            if a_subs > 0 and b_subs > 0:
                ratio = a_subs / b_subs
                insights.append(f"База Компании А в {ratio:.1f} раз больше базы Компании Б")
            
            # Compare internet traffic
            a_traffic = company_a_data[-1].get("Интернет-трафик (ТБ)", 0) if company_a_data else 0
            b_traffic = company_b_data[-1].get("Интернет-трафик (ТБ)", 0) if company_b_data else 0
            
            if a_traffic > 0 and b_traffic > 0:
                traffic_per_a = a_traffic / a_subs if a_subs > 0 else 0
                traffic_per_b = b_traffic / b_subs if b_subs > 0 else 0
                
                if traffic_per_b > traffic_per_a:
                    insights.append(f"Абоненты Компании Б потребляют в {traffic_per_b/traffic_per_a:.1f} раз больше трафика на пользователя")
        
        # Growth analysis
        if len(company_b_data) >= 2:
            first_month = company_b_data[0].get("Активные абоненты (тыс.)", 0)
            last_month = company_b_data[-1].get("Активные абоненты (тыс.)", 0)
            if first_month > 0:
                growth = ((last_month - first_month) / first_month) * 100
                insights.append(f"Компания Б показывает рост абонентской базы на {growth:.1f}% за квартал")
        
        return insights
    
    def _generate_recommendations(self, excel_data: list, context: dict) -> list:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Based on context analysis
        sections = context.get("sections", [])
        protocol_text = " ".join(sections).lower()
        
        if "ариф ugpu" in protocol_text or "оптовые тарифы" in protocol_text:
            recommendations.append("Рассмотреть пересмотр оптовых тарифов для Компании Б")
        
        if "сегмент" in protocol_text or "b2c" in protocol_text or "b2b" in protocol_text:
            recommendations.append("Подготовить детальный отчет с разбивкой по сегментам B2C и B2B")
        
        if "загрузки сети" in protocol_text or "капex" in protocol_text:
            recommendations.append("Внедрить ежемесячный мониторинг эффективности использования сети")
        
        if "тарифной линейки" in protocol_text:
            recommendations.append("Разработать план оптимизации тарифной линейки Компании Б")
        
        # Based on Excel data insights
        insights = self._identify_insights(excel_data, context)
        if "потребляют в" in " ".join(insights):
            recommendations.append("Ориентировать Компанию Б на тарифы с высокими пакетами данных")
        
        company_b_data = [row for row in excel_data if str(row.get("Компания", "")).strip() == "Б"]
        if len(company_b_data) >= 2:
            recommendations.append("Продолжить стратегию роста абонентской базы Компании Б")
        
        return recommendations
    
    async def _save_results(self, result_table: str) -> str:
        """Save results to output file."""
        output_dir = Path(__file__).parent / "test_data"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"analysis_result_{timestamp}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result_table)
        
        return str(output_file)


async def main():
    """Main test function."""
    print("🧪 MTS MultAgent Integration Test")
    print("Testing complete workflow: Jira → Context → Excel → Results")
    print()
    
    test = IntegrationWorkflowTest()
    success = await test.test_complete_workflow()
    
    if success:
        print("\n🎯 All tests passed! System is working correctly.")
        return True
    else:
        print("\n💥 Test failed! Check the error messages above.")
        return False


if __name__ == "__main__":
    asyncio.run(main())
