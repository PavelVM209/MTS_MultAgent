# Employee Monitoring System - TODO List

## 🎯 Phase: ARCHITECTURE FIXES FOR ORIGINAL REQUIREMENTS

### Критические исправления для соответствия первоначальной задаче

**Дата:** 2026-03-27  
**Основание:** Анализ несоответствий с требованиями (см. architecture-fixes.md)  
**Статус:** Готов к реализации  
**Приоритет:** КРИТИЧЕСКИЙ

---

## 📋 ИСПОЛНИТЕЛЬНЫЙ ПЛАН

### **TASK 1: Создание QualityOrchestrator как главного компонента** 🔴
- [ ] **Расширить QualityValidatorAgent до роли главного оркестратора**
  - [ ] Создать новый класс QualityOrchestrator на базе QualityValidatorAgent
  - [ ] Реализовать методы `execute_daily_task_workflow()`, `execute_daily_meeting_workflow()`, `execute_weekly_workflow()`
  - [ ] Интегрировать вызовы TaskAnalyzerAgent, MeetingAnalyzerAgent, WeeklyReportsAgent
  
- [ ] **Реализовать контроль качества на каждом этапе**
  - [ ] Добавить логику проверки качества после каждого анализа
  - [ ] Реализовать LLM-валидацию результатов
  - [ ] Настроить порог качества 90%
  
- [ ] **Добавить логику отправки на доработку**
  - [ ] Реализовать функцию `_request_improvement()` для доработки отчетов
  - [ ] Настроить до 3 попыток улучшения с использованием LLM
  - [ ] Добавить логирование процесса доработки
  
- [ ] **Интегрировать сохранение и публикацию**
  - [ ] Реализовать `_save_approved_report()` для качественных отчетов
  - [ ] Реализовать `_save_with_warning()` для отчетов с низким качеством
  - [ ] Интегрировать Confluence публикацию для еженедельных отчетов

### **TASK 2: TaskAnalyzerAgent интеграция с Jira API** 🔴
- [ ] **Добавить метод fetch_jira_tasks()**
  - [ ] Реализовать прямое подключение к Jira API
  - [ ] Обработать ошибки API и retry логику
  - [ ] Добавить парсинг Jira полей для коммитов и PR
  - [ ] Добавить логирование количества полученных задач
  
- [ ] **Обновить execute() метод**
  - [ ] Изменить сигнатуру для работы без обязательного input_data
  - [ ] Добавить авто-вызов `fetch_jira_tasks()` если данные не предоставлены
  - [ ] Интегрировать обработку коммитов и PR из Jira
  
- [ ] **Тестирование Jira интеграции**
  - [ ] Проверить подключение к API
  - [ ] Валидировать обработку разных статусов задач
  - [ ] Проверить извлечение кастомных полей (коммиты, PR)

### **TASK 3: MeetingAnalyzerAgent авто-сканирование директории** 🔴
- [ ] **Реализовать метод scan_protocols_directory()**
  - [ ] Добавить сканирование директории по конфигурации
  - [ ] Реализовать фильтрацию по форматам (TXT, PDF, DOCX)
  - [ ] Добавить проверку файлов-маркеров `.processed`
  - [ ] Реализовать фильтрацию пустых файлов
  
- [ ] **Обновить execute() метод**
  - [ ] Изменить сигнатуру для работы без обязательного input_data
  - [ ] Добавить авто-вызов `scan_protocols_directory()` если данные не предоставлены
  - [ ] Интегрировать обработку разных форматов файлов
  
- [ ] **Улучшить обработка протоколов**
  - [ ] Добавить поддержку PDF (библиотека PyPDF2/pdfplumber)
  - [ ] Добавить поддержку DOCX (библиотека python-docx)
  - [ ] Реализовать извлечение дат из имен файлов

### **TASK 4: WeeklyReportsAgent обновление (без Git интеграции)** 🟡
- [ ] **Удалить зависимости от Git интеграции**
  - [ ] Убрать заглушки `fetch_git_metrics()`
  - [ ] Обновить документацию (коммиты и PR из Jira)
  
- [ ] **Обновить сбор данных**
  - [ ] Модифицировать `generate_employee_summaries()` для учета коммитов/PR из Jira
  - [ ] Обновить структуру employee_summaries
  - [ ] Оптимизировать агрегацию данных за неделю
  
- [ ] **Улучшить генерацию отчетов**
  - [ ] Обновить шаблоны Confluence контента
  - [ ] Добавить метрики коммитов и PR в отчеты
  - [ ] Оптимизировать форматирование markdown

### **TASK 5: Обновление orchestration системы** 🟡
- [ ] **Перенастроить EmployeeMonitoringOrchestrator**
  - [ ] Обновить для работы с QualityOrchestrator
  - [ ] Изменить методы вызова
  - [ ] Адаптировать логику обработки результатов
  
- [ ] **Обновить EmployeeMonitoringScheduler**
  - [ ] Перенастроить расписания для новых workflow
  - [ ] Интегрировать вызовы QualityOrchestrator
  - [ ] Обновить логику обработки ошибок
  
- [ ] **Обновить основной запуск**
  - [ ] Модифицировать `main_employee_monitoring.py`
  - [ ] Обновить CLI интерфейс
  - [ ] Адаптировать конфигурацию

### **TASK 6: Тестирование и валидация** 🟡
- [ ] **Е2E тест полного workflow**
  - [ ] Тест ежедневного анализа задач
  - [ ] Тест ежедневного анализа протоколов
  - [ ] Тест еженедельного отчета
  
- [ ] **Тест контроля качества**
  - [ ] Валидация quality score < 90% и доработки
  - [ ] Тест LLM улучшения отчетов
  - [ ] Проверка максимального количества попыток
  
- [ ] **Интеграционное тестирование**
  - [ ] Тест Jira API подключения
  - [ ] Тест обработки протоколов
  - [ ] Тест публикации в Confluence

### **TASK 7: Документация и развертывание** 🟢
- [ ] **Обновить архитектурную документацию**
  - [ ] Обновить `employee-monitoring-spec.md`
  - [ ] Обновить `progress.md`
  - [ ] Создать API documentation
  
- [ ] **Полностью переработать README.md**
  - [ ] современная структура документа
  - [ ] описание новой архитектуры
  - [ ] инструкции по установке и использованию
  - [ ] troubleshooting guide
  
- [ ] **Подготовить к развертыванию**
  - [ ] Обновить конфигурацию если необходимо
  - [ ] Проверить deployment скрипты
  - [ ] Обновить systemctl service

---

## 🎯 КЛЮЧЕВЫЕ ЦЕЛИ

### **Соответствие первоначальным требованиям:**
- ✅ **QualityOrchestrator** оркестрирует всё + контроль качества на каждом этапе
- ✅ **TaskAnalyzer** автоматически получает данные из Jira (включая коммиты/PR)
- ✅ **MeetingAnalyzer** автоматически сканирует протоколы по заданному пути
- ✅ **WeeklyReports** делает комплексный анализ + публикация в Confluence
- ✅ **Качество** проверяется на каждом этапе с отправкой на доработку

### **Технические цели:**
- 🎯 Автономная работа всех компонентов (без input_data)
- 🎯 Quality score >= 90% для финальных отчетов
- 🎯 Устойчивость к ошибкам внешних API
- 🎯 Полное соответствие TRL (_original requirements)
- 🎯 Production-ready статус

---

## 📊 METRICS УСПЕХА

### **Functional Metrics:**
- [ ] System automatically fetches Jira data without input_data
- [ ] System automatically scans protocols without input_data  
- [ ] QualityOrchestrator controls quality at every step
- [ ] Revision workflow works for quality < 90%
- [ ] Weekly reports include commits and PR (from Jira)

### **Technical Metrics:**
- [ ] All components work autonomously
- [ ] Quality score >= 90% for final reports
- [ ] Daily analysis execution time < 5 minutes
- [ ] Weekly report generation time < 15 minutes
- [ ] System is resilient to API errors

---

## 🚀 СТАТУС РЕАЛИЗАЦИИ

### **Overall Progress:**
- **Phase 1 (QualityOrchestrator):** 0/4 completed
- **Phase 2 (TaskAnalyzer):** 0/3 completed  
- **Phase 3 (MeetingAnalyzer):** 0/3 completed
- **Phase 4 (WeeklyReports):** 0/3 completed
- **Phase 5 (Orchestration):** 0/3 completed
- **Phase 6 (Testing):** 0/3 completed
- **Phase 7 (Documentation):** 0/3 completed

### **Current Focus:**
- **Priority:** Создание QualityOrchestrator как главного компонента
- **Timeline:** 2026-03-27 (один день)
- **Risk:** Высокий (архитектурные изменения)
- **Dependencies:** Jira API доступность, LLM сервис

---

## 📝 ЗАМЕТКИ

### **Critical Dependencies:**
- Jira API credentials и доступность
- LLM сервис для контроля качества
- Файловая система с протоколами собраний
- Confluence API для публикации

### **Known Issues:**
- ⚠️ QualityValidatorAgent needs to become main orchestrator
- ⚠️ TaskAnalyzerAgent needs direct Jira API integration
- ⚠️ MeetingAnalyzerAgent needs auto-scanning capability
- ⚠️ Git integration not needed (commits/PR in Jira)

### **Risks & Mitigation:**
- 🔴 **Risk:** Architectural changes may break existing functionality  
  **Mitigation:** Comprehensive testing before deployment
- 🟡 **Risk:** Jira API rate limits or downtime  
  **Mitigation**: Retry logic and error handling
- 🟡 **Risk:** LLM service availability for quality control  
  **Mitigation**: Fallback validation methods

---

**Last Updated:** 2026-03-27  
**Responsible:** AI Assistant  
**Status:** READY FOR IMPLEMENTATION  
**Next Action:** Start with QualityOrchestrator implementation

---
*"The goal is 100% compliance with original requirements through architectural fixes"*
