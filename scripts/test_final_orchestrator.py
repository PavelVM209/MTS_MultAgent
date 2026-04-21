#!/usr/bin/env python3
"""
Тест Final Orchestrator - проверка объединения анализов
"""

import asyncio
import logging
import sys
from pathlib import Path

# Добавляем корень проекта в путь
project_root = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(project_root))

from src.orchestrator.final_orchestrator import FinalOrchestrator

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    print("🚀 ТЕСТ FINAL ORCHESTRATOR")
    print("=" * 60)
    
    try:
        # Создаем orchestrator
        orchestrator = FinalOrchestrator()
        print("✅ Final Orchestrator создан")
        
        # Health check
        health = await orchestrator.get_health_status()
        print(f"📊 Статус здоровья: {health['status']}")
        print(f"🔧 LLM Client: {health['llm_client']}")
        print(f"📁 Директория отчетов: {health['reports_directory']}")
        print(f"🔄 Unified Analysis Ready: {health['unified_analysis_ready']}")
        
        # Выполняем объединенный анализ
        print("\n🔄 ВЫПОЛНЕНИЕ ФИНАЛЬНОГО ОБЪЕДИНЕННОГО АНАЛИЗА")
        print("=" * 60)
        
        result = await orchestrator.execute({})
        
        if result.success:
            print("✅ Объединенный анализ выполнен успешно!")
            print(f"📋 Сообщение: {result.message}")
            
            analysis_data = result.data
            
            print(f"👥 Проанализировано сотрудников: {len(analysis_data.unified_employees)}")
            print(f"🎯 Общее здоровье команды: {analysis_data.overall_team_health:.2f}/10")
            print(f"📊 Качество анализа: {analysis_data.analysis_quality_score:.3f}")
            print(f"🔄 Источников данных: {analysis_data.data_sources_count}")
            
            if analysis_data.strategic_recommendations:
                print(f"📝 Стратегических рекомендаций: {len(analysis_data.strategic_recommendations)}")
                for i, rec in enumerate(analysis_data.strategic_recommendations[:3], 1):
                    print(f"  {i}. {rec[:80]}...")
            
            if analysis_data.risk_factors:
                print(f"⚠️ Факторов риска: {len(analysis_data.risk_factors)}")
                for i, risk in enumerate(analysis_data.risk_factors[:2], 1):
                    print(f"  {i}. {risk[:80]}...")
            
            if analysis_data.growth_opportunities:
                print(f"📈 Возможностей роста: {len(analysis_data.growth_opportunities)}")
                for i, opp in enumerate(analysis_data.growth_opportunities[:2], 1):
                    print(f"  {i}. {opp[:80]}...")
            
            print(f"⏱️ Время выполнения: {result.metadata.get('execution_time', 0):.2f} секунд")
            
            print("\n🎉 FINAL ORCHESTRATOR РАБОТАЕТ ИДЕАЛЬНО!")
            print("=" * 60)
            
            return 0
            
        else:
            print("❌ Объединенный анализ не выполнен!")
            print(f"📋 Ошибка: {result.message}")
            if hasattr(result, 'error') and result.error:
                print(f"💥 Детали ошибки: {result.error}")
            
            return 1
            
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
