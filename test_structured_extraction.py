#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to debug structured data extraction
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from src.agents.meeting_analyzer_agent_improved import ImprovedMeetingAnalyzerAgent

async def test_structured_extraction():
    """Тестирование извлечения структурированных данных"""
    
    print("🔍 ТЕСТИРОВАНИЕ СТРУКТУРИРОВАННОГО ИЗВЛЕЧЕНИЯ")
    print("=" * 60)
    
    # Читаем файл анализа
    with open('reports/daily/comprehensive-analysis_2026-04-04.txt', 'r', encoding='utf-8') as f:
        analysis_text = f.read()
    
    print(f"Размер файла анализа: {len(analysis_text)} символов")
    
    # Создаем агент
    agent = ImprovedMeetingAnalyzerAgent()
    
    # Тестируем извлечение
    print("\n🔄 ИЗВЛЕЧЕНИЕ СТРУКТУРИРОВАННЫХ ДАННЫХ:")
    structured_data = await agent._extract_structured_data(analysis_text)
    
    print(f"Тип данных: {type(structured_data)}")
    
    if isinstance(structured_data, dict):
        print(f"Ключи: {list(structured_data.keys())}")
        
        # Проверяем сотрудников
        employees = structured_data.get('employee_analysis', {})
        print(f"Найдено сотрудников: {len(employees)}")
        
        if employees:
            print("\n👥 СПИСОК СОТРУДНИКОВ:")
            for i, (name, data) in enumerate(employees.items(), 1):
                print(f"  {i}. {name}")
                if isinstance(data, dict):
                    rating = data.get('overall_participation_rating', 'N/A')
                    correlation = data.get('task_meeting_correlation', 'N/A')
                    print(f"     Рейтинг: {rating}, Корреляция: {correlation}")
        else:
            print("❌ СОТРУДНИКИ НЕ НАЙДЕНЫ!")
            
            # Тестируем fallback extraction
            print("\n🔧 ТЕСТИРОВАНИЕ FALLBACK EXTRACTION:")
            fallback_data = agent._fallback_structured_extraction(analysis_text)
            fallback_employees = fallback_data.get('employee_analysis', {})
            print(f"Fallback сотрудников: {len(fallback_employees)}")
            
            if fallback_employees:
                print("👥 FALLBACK СОТРУДНИКИ:")
                for i, name in enumerate(fallback_employees.keys(), 1):
                    print(f"  {i}. {name}")
        
        # Проверяем инсайты
        insights = structured_data.get('team_insights', [])
        print(f"\n💡 Командные инсайты: {len(insights)}")
        for i, insight in enumerate(insights[:3], 1):
            print(f"  {i}. {insight}")
        
        # Проверяем рекомендации
        recommendations = structured_data.get('manager_recommendations', [])
        print(f"\n📝 Рекомендации менеджеру: {len(recommendations)}")
        for i, rec in enumerate(recommendations[:2], 1):
            print(f"  {i}. {rec}")
    
    else:
        print(f"❌ НЕОЖИДАННЫЙ ТИП ДАННЫХ: {type(structured_data)}")
        print(f"Содержимое: {structured_data}")

if __name__ == "__main__":
    asyncio.run(test_structured_extraction())
