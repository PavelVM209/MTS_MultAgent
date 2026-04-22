# MTS_MultAgent - Система мониторинга производительности команды

Многоагентная система для комплексного анализа производительности команды на основе данных Jira, протоколов совещаний и еженедельных отчетов с интеграцией в Confluence.

**🎯 Статус проекта: 85% готовности | Production Ready | v2.0.0**

---

## 📋 Последние обновления (Апрель 2026)

### ✅ Проектная очистка завершена
- **Удалено 23 неиспользуемых файла** для улучшения структуры
- **Сохранена 100% функциональность** - все рабочие агенты на месте
- **Оптимизирован memory-bank** - улучшена организация документации
- **Структурированы тесты** - перенесены в соответствующие директории

### 🔄 Улучшенная архитектура
- Чистая структура проекта с актуальными агентами v2.0
- Оптимизированная файловая организация
- Улучшенная документация и банк памяти

---

## 🏗️ Архитектура системы

Система состоит из четырех специализированных агентов, каждый из которых выполняет свою задачу в общей экосистеме мониторинга:

### 🤖 Агенты системы

#### 1. Task Analyzer Agent v2.0.0 ✅
**Задача**: Ежедневный анализ новых задач из Jira

**Возможности**:
- Двухэтапная LLM система для максимального качества анализа
- Инкрементальный анализ только новых задач
- Отслеживание прогресса каждого сотрудника
- Извлечение комментариев и контекста задач
- Автоматическое сохранение в JSON и TXT форматах

**Артефакты**:
- `src/agents/task_analyzer_agent_improved.py` - Улучшенный агент
- `reports/runs/{run_id}/task-analysis/` - артефакты запуска (stage1/stage2/final)
- `reports/latest/task-analysis/` - последние результаты (копии артефактов)
- `stage1_text_analysis.txt` и `stage2_final_json.json` - legacy backward compatibility (выключено по умолчанию; включение: `ENABLE_LEGACY_ROOT_ARTIFACTS=1`)

#### 2. Meeting Analyzer Agent v2.0.0 ✅
**Задача**: Ежедневный анализ новых протоколов совещаний

**Возможности**:
- Трехэтапная система анализа:
  - **Этап 1**: Переработка протоколов в читабельный вид
  - **Этап 2**: Комплексный анализ по протоколу + Task Analyzer данные
  - **Этап 3**: Финальный анализ с инсайтами и JSON для сотрудников
- Анализ корреляции между участием в встречах и выполнением задач
- Оценка эффективности коммуникации
- Создание персональных рекомендаций

**Артефакты**:
- `src/agents/meeting_analyzer_agent_improved.py` - Улучшенный агент
- `data/raw/protocols/` - сырые протоколы (вход)
- `data/processed/protocols_cleaned/` - кэш очищенных протоколов (stage1)
- `reports/runs/{run_id}/meeting-analysis/` - артефакты запуска
- `reports/runs/{run_id}/employee_progression/` - прогресс сотрудников по итогам run
- `reports/latest/meeting-analysis/` - последние результаты

#### 3. Weekly Reports Agent v2.0.0 Complete ✅
**Задача**: Еженедельный комплексный анализ и публикация в Confluence

**Возможности**:
- Комплексный анализ производительности всей команды
- Оценка здоровья команды и индивидуальных метрик
- Автоматическая публикация отчетов в Confluence
- Генерация рекомендаций для менеджмента
- Визуализация进度 и трендов

**Файлы**:
- `src/agents/weekly_reports_agent_complete.py` - Полный агент
- `reports/weekly/weekly_report_YYYY-MM-DD.json` - Еженедельный отчет

#### 4. Quality Orchestrator Agent 🔄
**Задача**: Оркестрация всех агентов и контроль качества

**Возможности**:
- Координация работы всех агентов
- Валидация качества отчетов
- Автоматическое повторное выполнение при необходимости
- Мониторинг состояния системы

**Файлы**:
- `src/agents/quality_orchestrator.py` - Основной оркестратор
- `src/agents/quality_validator_agent.py` - Валидатор качества

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.11+
- Доступ к Jira API
- Доступ к Confluence API
- API ключ для LLM (GLM-4.6-357b)

### Установка

1. **Клонирование репозитория**:
```bash
git clone https://github.com/PavelVM209/MTS_MultAgent.git
cd MTS_MultAgent
```

2. **Создание виртуального окружения**:
```bash
python3 -m venv venv_py311
source venv_py311/bin/activate  # Linux/Mac
# или
venv_py311\Scripts\activate  # Windows
```

3. **Установка зависимостей**:
```bash
pip install -r requirements.txt
```

4. **Настройка переменных окружения**:
```bash
cp .env.example .env
# Отредактируйте .env с вашими API ключами
```

### Запуск агентов

#### 1. Запуск Task Analyzer
```bash
source venv_py311/bin/activate
python3 src/agents/task_analyzer_agent_improved.py
```

#### 2. Запуск Meeting Analyzer
```bash
source venv_py311/bin/activate
python3 src/agents/meeting_analyzer_agent_improved.py
```

#### 3. Запуск Weekly Reports
```bash
source venv_py311/bin/activate
python3 src/agents/weekly_reports_agent_complete.py
```

#### 4. Запуск Quality Orchestrator
```bash
source venv_py311/bin/activate
python3 src/agents/quality_orchestrator.py
```

### Тестирование

#### Запуск всех тестов
```bash
# Тестирование Task Analyzer
python3 test_improved_task_analyzer.py

# Тестирование Meeting Analyzer
python3 test_improved_meeting_analyzer.py

# Тестирование Weekly Reports
python3 test_weekly_reports_agent.py

# Комплексное тестирование
python3 test_full_system_manual.py

# Тестирование интеграций
python3 test_confluence_integration.py
```

#### 📁 Структура тестов (после очистки)
```
tests/
├── integration/                 # Интеграционные тесты
│   ├── test_confluence_integration.py
│   ├── test_full_system_manual.py
│   ├── test_improved_meeting_analyzer.py
│   └── test_improved_task_analyzer.py
├── unit/                       # Юнит-тесты
│   └── test_json_memory_store.py
└── test_data/                  # Тестовые данные
    ├── meeting_protocol*.txt
    └── jira_task*.txt
```

## 📊 Структура данных

### Формат отчетов

#### Task Analyzer Output
```json
{
  "analysis_date": "2026-04-04T...",
  "total_tasks": 150,
  "employees_analysis": {
    "Имя Сотрудника": {
      "task_count": 15,
      "completion_rate": 0.8,
      "priority_distribution": {...},
      "performance_rating": 8.5
    }
  },
  "insights": ["инсайт 1", "инсайт 2"],
  "recommendations": ["рекомендация 1", "рекомендация 2"]
}
```

#### Meeting Analyzer Output
```json
{
  "analysis_date": "2026-04-04T...",
  "total_employees": 11,
  "team_collaboration_score": 7.8,
  "task_meeting_alignment": 8.2,
  "employees_performance": {
    "Имя Сотрудника": {
      "task_to_meeting_correlation": 0.8,
      "communication_effectiveness": 8.5,
      "performance_rating": 8.0
    }
  },
  "team_insights": ["инсайт 1", "инсайт 2"],
  "recommendations": ["рекомендация 1", "рекомендация 2"]
}
```

## 📁 Структура проекта

```
MTS_MultAgent/
├── src/
│   ├── agents/                    # Агенты системы
│   │   ├── task_analyzer_agent_improved.py
│   │   ├── meeting_analyzer_agent_improved.py
│   │   ├── weekly_reports_agent_complete.py
│   │   └── quality_orchestrator.py
│   ├── core/                     # Базовая архитектура
│   │   ├── base_agent.py
│   │   ├── llm_client.py
│   │   ├── jira_client.py
│   │   └── config.py
│   └── utils/                    # Утилиты
├── config/                       # Конфигурационные файлы
├── data/                         # Data lake (raw/processed/index)
│   ├── raw/                      # Сырые входы
│   ├── processed/                # Обработанные данные/кэши
│   └── index/                    # Индексы обработки (ProcessingIndex)
├── protocols/                    # Legacy (источник для миграции), использовать scripts/migrate_protocols_to_datalake.py
├── reports/                      # Артефакты анализов
│   ├── runs/                     # Запуски (run_id = YYYYMMDD_HHMMSS)
│   ├── latest/                   # Последний запуск (копии артефактов + run_id.txt)
│   └── weekly/                   # Еженедельные отчеты
├── tests/                        # Тесты
├── docs/                        # Документация
└── memory-bank/                 # Банк памяти проекта
```

## 🔧 Конфигурация

### Основные параметры (.env)
```bash
# Jira Configuration
JIRA_URL=https://jira.mts.ru
JIRA_USERNAME=sa0000openbdrnd
JIRA_API_TOKEN=your_api_token
JIRA_PROJECT_KEYS=OPENBD

# Confluence Configuration
CONFLUENCE_URL=https://confluence.mts.ru
CONFLUENCE_API_TOKEN=your_api_token
CONFLUENCE_PARENT_PAGE_ID=2282162313

# LLM Configuration
LLM_API_KEY=your_llm_api_key
LLM_MODEL=glm-4.6-357b
LLM_API_BASE_URL=https://devx-copilot.tech/v1
```

### Конфигурация агентов (config/)
- `base.yaml` - Базовая конфигурация
- `development.yaml` - Настройки для разработки
- `production.yaml` - Настройки для продакшена
- `employee-monitoring.yaml` - Специфичные настройки мониторинга

## 📈 Метрики и KPI

### Отслеживаемые метрики

#### Уровень сотрудника
- Количество задач (всего/в работе/выполнено)
- Рейтинг эффективности (1-10)
- Корреляция задач и участия в встречах
- Эффективность коммуникации
- Прогресс во времени

#### Уровень команды
- Общее здоровье команды (1-10)
- Скорость командной работы
- Согласование задач и встреч
- Распределение нагрузки
- Выявление лидеров и проблемных зон

#### Уровня качества
- Успешность выполнения (95%)
- Восстановление после ошибок (90%)
- Целостность данных (98%)
- Покрытие тестами (85%)

## 🔄 Инкрементальный анализ и запуск (run) как единица сравнения

Система поддерживает инкрементальность и сравнение изменений через два механизма:

1) **Инкрементальность по контенту (hash) для протоколов**
- `ProcessingIndex`: `data/index/processing_index.json`
- ключ: `(processing_type, file_hash)`
- кэш очищенных протоколов: `data/processed/protocols_cleaned/`
- позволяет не дергать LLM повторно при неизменном протоколе

2) **Run-based артефакты для сравнения динамики**
- каждый запуск сохраняется в `reports/runs/{run_id}/...`
- последняя версия результатов доступна в `reports/latest/...`
- `reports/latest/run_id.txt` хранит id последнего запуска

3) **Инкремент по Jira через Snapshot + Diff**
- snapshot входных данных Jira: `data/jira/snapshots/{run_id}.json`
- diff изменений между текущим и предыдущим snapshot:
  - run: `reports/runs/{run_id}/jira-diff/jira-diff.json`
  - latest: `reports/latest/jira-diff/jira-diff.json`
- diff используется как \"инкремент\" для сравнения нового состояния с предыдущим и построения динамики по сотрудникам/команде

### Ops-скрипты
- Миграция legacy протоколов в data lake:
  - `python scripts/migrate_protocols_to_datalake.py --dry-run`
  - `python scripts/migrate_protocols_to_datalake.py --copy` или `--move`
- Retention/cleanup data lake (по умолчанию 60 дней):
  - `python scripts/purge_old_data.py --dry-run --days 60`
  - `python scripts/purge_old_data.py --apply --days 60`

Подробнее: `docs/adr/0001-run-artifacts-and-incremental-processing-index.md`

## 🚨 Обработка ошибок

### Механизмы восстановления
- **Retry logic**: автоматические повторы при временных сбоях
- **Fallback mechanisms**: резервные методы извлечения данных
- **Graceful degradation**: понижение функциональности вместо полного отказа
- **Comprehensive logging**: детальное логирование для диагностики

### Known Issues
1. **LLM client reliability** - требует стабильного интернет-соединения
2. **API rate limits** - обработано через retry logic
3. **Data consistency** - контролируется через quality metrics

## 📚 Документация

- [API Documentation](docs/API.md) - Детальная документация API
- [Deployment Guide](docs/DEPLOYMENT.md) - Инструкции по развертыванию
- [Memory Bank](memory-bank/) - Банк памяти проекта с техническими решениями

## 🤝 Участие в проекте

### Статус проекта
- **Current Version**: v2.0.0
- **Completion**: 85%
- **Production Ready**: Да (с настройкой)

### Todo по приоритетам
1. [ ] Финальное интеграционное тестирование
2. [ ] Оптимизация производительности
3. [ ] Дополнительное мониторинг
4. [ ] Расширение функциональности

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи в соответствующих директориях
2. Убедитесь что все API ключи корректно настроены
3. Запустите тесты для диагностики
4. Проверьте [Memory Bank](memory-bank/) для известных решений

---

**Проект разработан с ❤️ для MTS Digital Team**
