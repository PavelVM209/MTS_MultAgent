#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script for testing employee extraction from comprehensive analysis
"""

import re

def test_employee_extraction():
    """Тестирование извлечения сотрудников из файла анализа"""
    
    # Читаем файл анализа
    with open('reports/daily/comprehensive-analysis_2026-04-04.txt', 'r', encoding='utf-8') as f:
        analysis_text = f.read()
    
    print("🔍 ТЕСТИРОВАНИЕ ИЗВЛЕЧЕНИЯ СОТРУДНИКОВ")
    print("=" * 60)
    
    # Тестируем разные regex patterns
    patterns = [
        (r'\*\*Сотрудник:\*\*([^\n]+)(.*?)(?=\*\*Сотрудник:\*\*|===|\Z)', "**Сотрудник:** формат"),
        (r'Сотрудник:\s*([^\n]+)(.*?)(?=Сотрудник:|===|\Z)', "Сотрудник: формат"),
        (r'\*\*([^*]+)\*\*([^\n]*?)(.*?)(?=\*\*[^*]+\*\*|===|\Z)', "**Любой** формат"),
        (r'Сотрудник[:：]\s*([^\n]+)', "Простой поиск имени"),
    ]
    
    for i, (pattern, description) in enumerate(patterns, 1):
        print(f"\n{i}. Тестирование: {description}")
        print(f"Pattern: {pattern}")
        
        try:
            matches = re.findall(pattern, analysis_text, re.DOTALL)
            print(f"Найдено совпадений: {len(matches)}")
            
            for j, match in enumerate(matches[:3]):  # Показываем первые 3
                if isinstance(match, tuple):
                    name = match[0].strip() if match[0] else "ПУСТО"
                    content = match[1][:100] + "..." if len(match[1]) > 100 else match[1] if len(match) > 1 else "ПУСТО"
                    print(f"  Совпадение {j+1}: '{name}' -> {content}")
                else:
                    name = match.strip() if match else "ПУСТО"
                    print(f"  Совпадение {j+1}: '{name}'")
        
        except Exception as e:
            print(f"  Ошибка: {e}")
    
    # Ищем все строки с **Сотрудник:**
    print(f"\n🔍 ПОИСК СТРОК С **СОТРУДНИК:**")
    employee_lines = []
    for line in analysis_text.split('\n'):
        if '**Сотрудник:' in line:
            employee_lines.append(line.strip())
    
    print(f"Найдено строк: {len(employee_lines)}")
    for i, line in enumerate(employee_lines, 1):
        print(f"  {i}. {line}")
    
    # Показываем фрагмент текста вокруг первого сотрудника
    print(f"\n📄 ФРАГМЕНТ ТЕКСТА ВОКРУГ ПЕРВОГО СОТРУДНИКА:")
    if '**Сотрудник:' in analysis_text:
        first_pos = analysis_text.find('**Сотрудник:')
        start = max(0, first_pos - 50)
        end = min(len(analysis_text), first_pos + 500)
        fragment = analysis_text[start:end]
        print(fragment)
        print("..." * 20)
    
    # Тестируем улучшенный pattern из агента
    print(f"\n🔧 УЛУЧШЕННЫЙ PATTERN ИЗ АГЕНТА:")
    improved_patterns = [
        r'\*\*Сотрудник:\s*([^\n]+)\*\*\s*\n(.*?)(?=\*\*Сотрудник:|===|\Z)',  # **Сотрудник: Имя** формат
        r'Сотрудник:\s*([^\n]+)(.*?)(?=Сотрудник:|===|\Z)'  # Сотрудник: формат
    ]
    
    for i, pattern in enumerate(improved_patterns, 1):
        print(f"\nPattern {i}: {pattern}")
        matches = re.findall(pattern, analysis_text, re.DOTALL)
        print(f"Найдено совпадений: {len(matches)}")
        
        for j, (name, content) in enumerate(matches[:2], 1):
            name = name.strip()
            print(f"  Совпадение {j}: Имя: '{name}'")
            print(f"             Контент: {content[:100]}...")

if __name__ == "__main__":
    test_employee_extraction()
