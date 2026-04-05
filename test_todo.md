# TODO LIST - Комплексное тестирование агентов MTS MultAgent

## Phase 1: Core Infrastructure
- [ ] Активировать виртуальное окружение
- [ ] Проверить .env конфигурацию
- [ ] Настроить DEBUG уровень логирования
- [ ] Тестировать Jira Client подключение
- [ ] Проанализировать ошибки подключения к MTS Jira

## Phase 2: Task Analyzer Agent
- [ ] Создать test_task_analyzer_real.py с DEBUG логами
- [ ] Запустить тест и собрать ошибки из логов
- [ ] Проанализировать stack traces parsing ошибок
- [ ] Исправить "No valid JIRA tasks parsed"
- [ ] Исправить LLM integration проблемы
- [ ] Исправить Memory Store schema ошибки
- [ ] Исправить DateTime formatting проблемы
- [ ] Добиться 95%+ success rate

## Phase 3: Meeting Analyzer Agent
- [ ] Создать test_meeting_analyzer_real.py с DEBUG логами
- [ ] Тестировать с реальными протоколами
- [ ] Проанализировать текст processing ошибки
- [ ] Исправить LLM response parsing проблемы
- [ ] Исправить Employee name matching проблемы
- [ ] Добиться 90%+ success rate

## Phase 4: Quality Validator Agent
- [ ] Создать test_quality_validator_real.py с DEBUG логами
- [ ] Тестировать на реальных данных
- [ ] Проанализировать validation rule ошибки
- [ ] Настроить правильные thresholds
- [ ] Добиться 95%+ validation success

## Phase 5: Weekly Reports Agent
- [ ] Создать test_weekly_reports_real.py с DEBUG логами
- [ ] Тестировать генерацию отчетов
- [ ] Проанализировать datetime calculation ошибки
- [ ] Игнорировать Confluence ошибки, сфокус на данных
- [ ] Добиться 85%+ success

## Phase 6: Integration Testing
- [ ] Создать test_orchestrator_real.py с DEBUG логами
- [ ] Тестировать полный orchestrator workflow
- [ ] Анализировать integration ошибки
- [ ] Добиться 80%+ end-to-end success

## Final Validation
- [ ] Убедиться что все агенты работают стабильно
- [ ] Проверить что нет critical exceptions в логах
- [ ] Валидировать JSON формат отчетов
- [ ] Подготовить summary report
