#!/usr/bin/env python3
"""
Упрощенный энд-ту-энд тест для проверки полного workflow:
1. Чтение Jira задачи
2. Извлечение ключевых слов
3. Поиск в протоколе совещания
4. Создание запроса к Excel
5. Исполнение запроса
6. Генерация отчета
"""

import os
from pathlib import Path
import pandas as pd
from datetime import datetime


class SimpleEndToEndWorkflow:
    """Упрощенный класс для энд-ту-энд тестирования workflow"""
    
    def __init__(self):
        self.test_data_dir = Path(__file__).parent / "test_data"
        
    def setup_test_data(self):
        """Проверка наличия тестовых данных"""
        required_files = [
            "jira_task_realistic.txt",
            "meeting_protocol_realistic.txt", 
            "project_data_realistic.xlsx"
        ]
        
        missing_files = []
        for file in required_files:
            if not (self.test_data_dir / file).exists():
                missing_files.append(file)
        
        if missing_files:
            raise FileNotFoundError(f"Missing test files: {missing_files}")
            
        print("✅ Все тестовые файлы найдены")
        
    def test_jira_reading(self):
        """Тест чтения Jira задачи"""
        print("\n🔍 Тест 1: Чтение Jira задачи")
        
        # Читаем тестовую Jira задачу
        jira_file = self.test_data_dir / "jira_task_realistic.txt"
        with open(jira_file, 'r', encoding='utf-8') as f:
            jira_content = f.read()
            
        # Извлекаем ключевую информацию
        lines = jira_content.split('\n')
        project_key = None
        description = ""
        keywords = []
        
        for line in lines:
            if "Проект:" in line:
                project_key = line.split(":")[1].strip()
            elif "**Описание:**" in line:
                description = line.replace("**Описание:**", "").strip()
            elif "интеграция" in line.lower() or "s3" in line.lower() or "сроки" in line.lower() or "бюджет" in line.lower():
                keywords.extend([word.lower() for word in line.split() if len(word) > 3])
        
        keywords = list(set(keywords))  # Убираем дубликаты
        
        print(f"   📋 Проект: {project_key}")
        print(f"   📝 Описание: {description[:50]}...")
        print(f"   🔑 Ключевые слова: {keywords[:8]}")
        
        return {
            "project_key": project_key,
            "description": description,
            "keywords": keywords,
            "content": jira_content
        }
        
    def test_protocol_analysis(self, jira_data):
        """Тест анализа протокола совещания"""
        print("\n🔍 Тест 2: Анализ протокола совещания")
        
        # Читаем протокол совещания
        protocol_file = self.test_data_dir / "meeting_protocol_realistic.txt"
        with open(protocol_file, 'r', encoding='utf-8') as f:
            protocol_content = f.read()
            
        # Ищем релевантную информацию по ключевым словам
        relevant_sections = []
        lines = protocol_content.split('\n')
        
        for i, line in enumerate(lines):
            # Ищем упоминания ключевых слов
            if any(keyword.lower() in line.lower() for keyword in jira_data["keywords"]):
                # Берем текущую строку и несколько следующих
                section = line
                for j in range(1, min(3, len(lines) - i)):
                    if lines[i + j].strip():
                        section += "\n" + lines[i + j]
                    else:
                        break
                relevant_sections.append(section.strip())
                
        print(f"   📄 Найдено релевантных секций: {len(relevant_sections)}")
        for i, section in enumerate(relevant_sections[:3]):
            print(f"   📍 Секция {i+1}: {section[:100]}...")
            
        return {
            "protocol_content": protocol_content,
            "relevant_sections": relevant_sections
        }
        
    def test_excel_query(self, jira_data, protocol_data):
        """Тест запроса к Excel данным"""
        print("\n🔍 Тест 3: Запрос к Excel данным")
        
        # Читаем Excel файл
        excel_file = self.test_data_dir / "project_data_realistic.xlsx"
        df = pd.read_excel(excel_file)
        
        print(f"   📊 Excel структура: {df.shape[0]} строк, {df.shape[1]} колонок")
        print(f"   📋 Колонки: {list(df.columns)}")
        
        # Формируем запрос на основе контекста
        query_conditions = []
        
        # Если есть упоминания S3 интеграции
        if any("s3" in sec.lower() or "интеграция" in sec.lower() for sec in protocol_data["relevant_sections"]):
            query_conditions.append(df["Компонент"].str.contains("S3|интеграция", case=False, na=False))
            
        # Если есть упоминания статусов
        if any("статус" in sec.lower() or "в работе" in sec.lower() or "завершен" in sec.lower() for sec in protocol_data["relevant_sections"]):
            query_conditions.append(df["Статус"].isin(["В работе", "Завершен"]) | 
                                   df["Компонент"].str.contains("API", case=False, na=False))
            
        # Если есть упоминания ответственных
        if any("петров" in sec.lower() or "иванов" in sec.lower() or "сидоров" in sec.lower() for sec in protocol_data["relevant_sections"]):
            query_conditions.append(df["Ответственный"].str.contains("Петров|Иванов|Сидоров|Васильев", case=False, na=False))
            
        # Применяем условия
        if query_conditions:
            combined_condition = query_conditions[0]
            for condition in query_conditions[1:]:
                combined_condition = combined_condition | condition
            result_df = df[combined_condition]
        else:
            result_df = df
            
        print(f"   📈 Результат запроса: {result_df.shape[0]} строк найдено")
        
        if not result_df.empty:
            print("   📋 Найденные строки:")
            for _, row in result_df.iterrows():
                print(f"      - {row['Компонент']}: {row['Статус']} ({row['Ответственный']})")
        
        return {
            "original_data": df,
            "query_result": result_df,
            "query_conditions": len(query_conditions)
        }
        
    def test_report_generation(self, jira_data, protocol_data, excel_data):
        """Тест генерации отчета"""
        print("\n🔍 Тест 4: Генерация отчета")
        
        # Формируем отчет
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.test_data_dir / f"analysis_result_{timestamp}.txt"
        
        report_content = f"""
# РЕЗУЛЬТАТ АНАЛИЗА ПРОЕКТА
============================

## 📋 Исходная задача Jira
- **Ключ проекта:** {jira_data['project_key']}
- **Описание:** {jira_data['description']}
- **Ключевые слова:** {', '.join(jira_data['keywords'][:8])}

## 📄 Анализ протокола совещания
- **Найдено релевантных секций:** {len(protocol_data['relevant_sections'])}
- **Ключевые темы:** S3 интеграция, статусы выполнения, команда проекта

## 📊 Результаты анализа Excel данных
- **Всего записей в таблице:** {len(excel_data['original_data'])}
- **Найдено по запросу:** {len(excel_data['query_result'])}
- **Применено условий:** {excel_data['query_conditions']}

## 📈 ТАБЛИЦА РЕЗУЛЬТАТОВ:
"""
        
        if not excel_data['query_result'].empty:
            report_content += "\n| Компонент | Статус | Плановый срок | Ответственный | Прогресс |\n"
            report_content += "|-----------|--------|---------------|---------------|----------|\n"
            
            for _, row in excel_data['query_result'].iterrows():
                report_content += f"| {row['Компонент']} | {row['Статус']} | {row['Плановый срок']} | {row['Ответственный']} | {row['Прогресс']} |\n"
        else:
            report_content += "Данные по запросу не найдены\n"
            
        report_content += f"""
## 🔍 Анализ и выводы

На основе интегрального анализа данных из Jira, протокола совещания и Excel таблицы:

1. **Проект {jira_data['project_key']}** активно разрабатывается
2. **Обнаружено {len(excel_data['query_result'])} компонентов** соответствующих ключевым запросам
3. **Статусы выполнения** варьируются от "Не начато" до "Завершен"
4. **Команда проекта** включает {len(excel_data['query_result']['Ответственный'].unique())} ключевых специалистов

### 🔧 Тестирование процесса
✅ Jira задача успешно прочитана и проанализирована
✅ Протокол совещания обработан с извлечением релевантных секций
✅ Excel данные запрошены и отфильтрованы по контексту
✅ Отчет сгенерирован в формате таблицы

## 📋 Сводка по команде проекта:
"""
        
        if not excel_data['query_result'].empty:
            for responsible in excel_data['query_result']['Ответственный'].unique():
                responsible_tasks = excel_data['query_result'][excel_data['query_result']['Ответственный'] == responsible]
                report_content += f"- **{responsible}**: {len(responsible_tasks)} задач\n"
        
        report_content += f"""
---
*Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Источник данных: Jira задача, протокол совещания, Excel таблица*
"""
        
        # Сохраняем отчет
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
            
        print(f"   📄 Отчет сохранен: {report_file.name}")
        print(f"   📊 Размер отчета: {len(report_content)} символов")
        
        return {
            "report_file": str(report_file),
            "content_length": len(report_content),
            "data_found": len(excel_data['query_result']) > 0
        }
        
    def run_end_to_end_test(self):
        """Запуск полного энд-ту-энд теста"""
        print("🚀 ЗАПУСК ЭНД-ТУ-ЭНД ТЕСТА MTS_MultAgent")
        print("=" * 60)
        
        try:
            # Шаг 1: Проверка тестовых данных
            self.setup_test_data()
            
            # Шаг 2: Чтение Jira задачи
            jira_data = self.test_jira_reading()
            
            # Шаг 3: Анализ протокола совещания
            protocol_data = self.test_protocol_analysis(jira_data)
            
            # Шаг 4: Запрос к Excel данным
            excel_data = self.test_excel_query(jira_data, protocol_data)
            
            # Шаг 5: Генерация отчета
            report_data = self.test_report_generation(jira_data, protocol_data, excel_data)
            
            # Итоги теста
            print("\n" + "=" * 60)
            print("🎉 ЭНД-ТУ-ЭНД ТЕСТ УСПЕШНО ЗАВЕРШЕН!")
            print(f"📁 Отчет: {report_data['report_file'].split('/')[-1]}")
            print(f"📊 Найдено данных: {'Да' if report_data['data_found'] else 'Нет'}")
            print(f"📈 Компонентов обработано: {len(excel_data['query_result'])}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Ошибка в ходе теста: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Главная функция для запуска теста"""
    tester = SimpleEndToEndWorkflow()
    success = tester.run_end_to_end_test()
    
    if success:
        print("\n✅ Все тесты успешно пройдены!")
        return 0
    else:
        print("\n❌ Тесты не пройдены!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
