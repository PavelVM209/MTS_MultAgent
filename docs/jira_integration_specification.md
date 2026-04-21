# Спецификация Jira Интеграции

**Дата аудита:** 13.04.2026  
**Версия спецификации:** 1.0  
**Статус:** ✅ ГОТОВА К ПРОИЗВОДСТВУ

## Обзор интеграции

### Система
- **Платформа:** MTS Jira
- **Эндпоинт:** https://jira.mts.ru
- **Аутентификация:** Bearer Token (sa0000openbdrnd)
- **Проект:** OPENBD
- **Статус подключения:** ✅ Операционно

### Характеристики производительности
- **Время ответа API:** 0.25 секунд для 50 задач
- **Максимальный лимит запросов:** 1000 задач
- **Оценочное время полной синхронизации:** 0.5 секунд
- **Статус:** ✅ Высокая производительность

## Каталог данных

### Доступные задачи
- **Всего задач:** 1000 (лимит API)
- **За последние 7 дней:** 91 задач
- **За последние 30 дней:** 203 задач
- **Уникальных сотрудников:** 21
- **Охват данных:** Высокий

### Доступные поля задач
```json
{
  "id": "ID задачи",
  "key": "Ключ задачи (например, OPENBD-123)",
  "summary": "Название задачи",
  "description": "Описание задачи",
  "status": {
    "name": "Статус задачи",
    "id": "ID статуса"
  },
  "assignee": {
    "displayName": "Полное имя исполнителя",
    "name": "Имя пользователя Jira",
    "emailAddress": "Email исполнителя"
  },
  "reporter": {
    "displayName": "Полное имя автора",
    "name": "Имя пользователя автора"
  },
  "priority": {
    "name": "Приоритет",
    "id": "ID приоритета"
  },
  "project": {
    "key": "Ключ проекта",
    "name": "Название проекта"
  },
  "components": [
    {
      "name": "Название компонента",
      "id": "ID компонента"
    }
  ],
  "labels": ["Метки задачи"],
  "created": "Дата создания (ISO 8601)",
  "updated": "Дата обновления (ISO 8601)",
  "duedate": "Срок выполнения (YYYY-MM-DD)",
  "resolution": {
    "name": "Резолюция",
    "date": "Дата резолюции"
  },
  "customfield_10002": "Story Points (если настроено)",
  "comment": {
    "comments": [
      {
        "id": "ID комментария",
        "author": {
          "displayName": "Автор комментария",
          "name": "Имя пользователя автора"
        },
        "body": "Текст комментария",
        "created": "Дата создания комментария",
        "updated": "Дата обновления комментария",
        "visibility": {
          "type": "Тип видимости",
          "value": "Значение видимости"
        }
      }
    ],
    "maxResults": 100,
    "total": 25,
    "startAt": 0
  },
  "worklog": {
    "worklogs": [
      {
        "id": "ID записи времени",
        "author": {
          "displayName": "Автор записи",
          "name": "Имя пользователя"
        },
        "timeSpent": "5h",
        "timeSpentSeconds": 18000,
        "started": "Дата начала работы",
        "comment": "Комментарий к записи времени"
      }
    ],
    "maxResults": 50,
    "total": 10,
    "startAt": 0
  },
  "attachment": [
    {
      "id": "ID вложения",
      "filename": "Имя файла",
      "author": {
        "displayName": "Автор вложения"
      },
      "created": "Дата создания",
      "size": 1024000,
      "mimeType": "application/pdf",
      "content": "URL для скачивания"
    }
  ],
  "subtasks": [
    {
      "id": "ID подзадачи",
      "key": "Ключ подзадачи",
      "summary": "Название подзадачи",
      "status": {
        "name": "Статус подзадачи"
      }
    }
  ],
  "issuelinks": [
    {
      "id": "ID связи",
      "type": {
        "name": "Тип связи",
        "inward": "Внутреннее название",
        "outward": "Внешнее название"
      },
      "inwardIssue": {
        "key": "Ключ связанной задачи",
        "summary": "Название связанной задачи"
      },
      "outwardIssue": {
        "key": "Ключ связанной задачи",
        "summary": "Название связанной задачи"
      }
    }
  ]
}
```

### Важность полей для анализа
```yaml
analysis_priority:
  critical_fields:
    - "assignee.displayName"        # Идентификация сотрудника
    - "status.name"                 # Текущий статус работы
    - "summary"                     # Тематики задач
    - "description"                 # Детальное описание работы
    - "comment.comments[].body"    # 💬 КОММЕНТАРИИ - ключевые для анализа коммуникаций
    - "created/updated"            # Временная динамика
    
  important_fields:
    - "reporter.displayName"        # Кто поставил задачу
    - "priority.name"               # Срочность и важность
    - "components[].name"           # Компоненты/направления
    - "labels"                      # Дополнительная классификация
    - "worklog.worklogs"            # Затраченное время
    - "duedate"                     # Сроки выполнения
    
  optional_fields:
    - "attachment"                  # Вложенные файлы
    - "subtasks"                    # Иерархия задач
    - "issuelinks"                  # Связи между задачами
    - "customfield_*"               # Кастомные поля
```

## Каталог статусов задач

### Активные статусы
```yaml
active_statuses:
  - "В работе"
  - "Бэклог"
  - "Запланировано"
  - "Открыто"
  - "В ожидании"
  - "Готово к проверке"
  - "Готово к тестированию"
  - "Готово для ревью"
```

### Завершенные статусы
```yaml
completed_statuses:
  - "Закрыт"
  - "Released"
  - "Установлено"
```

### Распределение по статусам (текущие данные)
```yaml
status_distribution:
  "Закрыт": 793          # 79.3% завершенных
  "Бэклог": 122          # 12.2% запланированных
  "В работе": 30         # 3.0% в процессе
  "Запланировано": 24    # 2.4% запланированных
  "Открыто": 9           # 0.9% открытых
  "Готово к проверке": 8  # 0.8% на проверке
  "Released": 5          # 0.5% релизнутых
  "В ожидании": 4        # 0.4% ожидающих
  "Готово к тестированию": 2  # 0.2% на тестировании
  "Готово для ревью": 2  # 0.2% на ревью
  "Установлено": 1       # 0.1% установленных
```

## Каталог сотрудников

### Картирование сотрудников (Task Count Mapping)
```yaml
employee_mapping:
  Болотин Андрей: 160          # Самый активный
  Мурзаков Павел: 115          # Второй по активности
  Колобаев Никита: 86          # Высокая активность
  Стрельченко Святослав: 86    # Высокая активность
  Савенкова Надежда: 72        # Средняя активность
  Степанов Тимофей: 42         # Средняя активность
  Кроткова Наталья Олеговна: 31 # Средняя активность
  Вощилов Егор: 29             # Средняя активность
  Мангурсузян Рафаэль Варушанович: 29  # Средняя активность
  Сабадаш Алина: 26            # Средняя активность
  Найденов Иван Владимирович: 23  # Средняя активность
  Березин Константин: 17       # Низкая активность
  Покинен Андрей Эдуардович: 16  # Низкая активность
  Анзоров Азрет [X]: 16       # Низкая активность
  Жданов Андрей: 13           # Низкая активность
  Кузьмин Вячеслав: 12        # Низкая активность
  Алешаев Александр: 6        # Очень низкая активность
  Пугаева Ксения [X]: 5       # Очень низкая активность
  Котов Илья: 9               # Очень низкая активность
  Кроткова Наталья: 1         # Минимальная активность
  Unassigned: 206             # 20.6% задач без исполнителя
```

### Категоризация сотрудников по активности
```yaml
activity_categories:
  high_activity: &high_activity
    - "Болотин Андрей"           # 160+ задач
    - "Мурзаков Павел"           # 115+ задач
  
  medium_high_activity: &medium_high
    - "Колобаев Никита"          # 80-100 задач
    - "Стрельченко Святослав"    # 80-100 задач
    - "Савенкова Надежда"        # 70-80 задач
  
  medium_activity: &medium
    - "Степанов Тимофей"         # 40-50 задач
    - "Кроткова Наталья Олеговна" # 30-40 задач
    - "Вощилов Егор"             # 25-35 задач
    - "Мангурсузян Рафаэль Варушанович" # 25-35 задач
    - "Сабадаш Алина"            # 25-35 задач
    - "Найденов Иван Владимирович" # 20-30 задач
  
  low_activity: &low
    - "Березин Константин"       # 15-20 задач
    - "Покинен Андрей Эдуардович" # 15-20 задач
    - "Анзоров Азрет [X]"       # 15-20 задач
    - "Жданов Андрей"            # 10-15 задач
    - "Кузьмин Вячеслав"         # 10-15 задач
  
  minimal_activity: &minimal
    - "Котов Илья"               # <10 задач
    - "Алешаев Александр"        # <10 задач
    - "Пугаева Ксения [X]"       # <10 задач
    - "Кроткова Наталья"         # <5 задач
```

## Паттерны запросов (Query Patterns)

### Основные JQL запросы
```yaml
query_patterns:
  all_active_tasks: >
    project = "OPENBD" AND status IN ("В работе", "Бэклог", "Запланировано", "Открыто", "В ожидании") 
    ORDER BY updated DESC
  
  recently_updated: >
    project = "OPENBD" AND updated >= -7d ORDER BY updated DESC
  
  tasks_by_assignee: >
    project = "OPENBD" AND assignee = "{employee_name}" ORDER BY updated DESC
  
  completed_tasks: >
    project = "OPENBD" AND status IN ("Закрыт", "Released", "Установлено") 
    AND updated >= -30d ORDER BY updated DESC
  
  high_priority_tasks: >
    project = "OPENBD" AND priority IN ("Highest", "High") 
    AND status IN ("В работе", "Бэклог", "Запланировано") 
    ORDER BY priority DESC, updated DESC
  
  unassigned_tasks: >
    project = "OPENBD" AND assignee is EMPTY 
    AND status IN ("В работе", "Бэклог", "Запланировано") 
    ORDER BY created DESC
  
  overdue_tasks: >
    project = "OPENBD" AND duedate <= now() 
    AND status NOT IN ("Закрыт", "Released", "Установлено") 
    ORDER BY duedate ASC
  
  tasks_by_component: >
    project = "OPENBD" AND component = "{component_name}" 
    ORDER BY updated DESC
```

## Лимиты и ограничения

### API ограничения
```yaml
api_limitations:
  max_results_per_request: 1000    # Jira API лимит
  recommended_batch_size: 50-100   # Оптимальный размер пакета
  rate_limit: "Не документирован, но ~100 запросов/минуту"
  timeout: 30 секунд                # Тайм-аут запроса
  
pagination_notes: >
  При запросах >1000 задач требуется пагинация.
  Рекомендуется использовать start_at параметр для постраничной загрузки.
```

### Ограничения данных
```yaml
data_limitations:
  historical_data: "Доступны все задачи (лимит 1000 за запрос)"
  field_access: "Все стандартные поля доступны"
  custom_fields: "customfield_10002 (Story Points) доступен"
  user_data: "displayName, name, emailAddress доступны"
  attachment_access: "Требует отдельных запросов"
  comment_access: "Требует отдельных запросов на каждую задачу"
  worklog_access: "Требует отдельных запросов на каждую задачу"

# 💬 ВАЖНО: Комментарии доступны только через отдельные API вызовы
# GET /rest/api/2/issue/{issueIdOrKey}/comment
# Параметры: expand=renderedBody, возвращает все комментарии задачи
comment_api_details:
  endpoint: "/rest/api/2/issue/{issueIdOrKey}/comment"
  method: "GET"
  parameters:
    - "expand=renderedBody"  # Для отформатированного текста
    - "maxResults=100"       # Максимум комментариев
  performance_impact: "Один дополнительный API вызов на задачу"
  recommendation: "Использовать 选择性地 для активных задач"
  
# Работа со временем (worklog) также требует отдельных вызовов
worklog_api_details:
  endpoint: "/rest/api/2/issue/{issueIdOrKey}/worklog"
  method: "GET"
  performance_impact: "Один дополнительный API вызов на задачу"
  recommendation: "Использовать для анализа продуктивности"
```

### Стратегии получения комментариев
```yaml
comment_strategies:
  selective_approach:
    description: "Получать комментарии только для активных задач"
    jql_filter: >
      project = "OPENBD" AND status IN ("В работе", "Готово к проверке", "В ожидании")
    performance_impact: "Низкий"
    analysis_value: "Высокий"
  
  recent_activity_approach:
    description: "Получать комментарии для задач с недавними обновлениями"
    jql_filter: >
      project = "OPENBD" AND updated >= -7d
    performance_impact: "Средний"
    analysis_value: "Высокий"
  
  comprehensive_approach:
    description: "Получать комментарии для всех задач"
    performance_impact: "Высокий"
    analysis_value: "Максимальный"
    recommendation: "Только для офлайн-анализа"
  
  batch_approach:
    description: "Пакетная обработка по 50 задач за раз"
    batch_size: 50
    delay_between_batches: "1 секунда"
    performance_impact: "Умеренный"
    analysis_value: "Комплексный"
```

## Оптимизация производительности

### Рекомендуемые интервалы запросов
```yaml
recommended_intervals:
  realtime_sync: "5 минут"      # для критически важных данных
  hourly_sync: "1 час"          # для регулярных обновлений
  daily_sync: "24 часа"         # для полной синхронизации
  weekly_reports: "7 дней"      # для еженедельных отчетов
```

### Стратегии кэширования
```yaml
caching_strategies:
  user_data_cache: "24 часа"    # Данные о сотрудниках меняются редко
  status_cache: "1 час"         # Статусы задач меняются регулярно
  project_data_cache: "7 дней"  # Данные проекта стабильны
  
conditional_cache_refresh:
  high_activity_employees: "30 минут"
  medium_activity_employees: "2 часа"
  low_activity_employees: "6 часов"
```

## Картирование полей (Field Mapping)

### Маппинг для анализа сотрудников
```yaml
employee_analysis_mapping:
  primary_identifier: "assignee.displayName"
  secondary_identifier: "assignee.name"
  fallback_identifier: "Unassigned"
  
performance_metrics:
  task_count: "count of issues"
  completion_rate: "completed_issues / total_issues"
  avg_completion_time: "avg(updated - created for completed)"
  current_workload: "count of issues in 'В работе'"
  overdue_count: "count of issues where duedate < now()"
  
quality_metrics:
  rejection_rate: "count of issues returning from 'Готово к проверке'"
  rework_count: "count of status transitions backward"
  first_time_approval: "issues completed without 'Готово для ревью'"
```

### Маппинг статусов для анализа
```yaml
status_analysis_mapping:
  work_in_progress: ["В работе", "Готово к проверке", "Готово к тестированию", "Готово для ревью"]
  planning_phase: ["Бэклог", "Запланировано", "Открыто"]
  blocked: ["В ожидании"]
  completed: ["Закрыт", "Released", "Установлено"]
  
flow_indicators:
  efficient_flow: "Запланировано → В работе → Готово к проверке → Закрыт"
  review_needed: "В работе → Готово для ревью → В работе → ..."
  blocked_flow: "В работе → В ожидании → В работе"
  quality_issues: "Готово к проверке → В работе → ..."
```

## Конфигурация интеграции

### Рекомендуемые настройки
```yaml
integration_config:
  api_settings:
    base_url: "https://jira.mts.ru"
    auth_type: "Bearer Token"
    timeout: 30
    max_retries: 3
    retry_delay: 1
    
  query_settings:
    default_fields: [
      "summary", "status", "assignee", "created", "updated", 
      "priority", "project", "components", "labels"
    ]
    detailed_fields: [
      "summary", "description", "status", "assignee", "reporter",
      "created", "updated", "duedate", "priority", "project",
      "components", "labels", "customfield_10002"
    ]
    
  scheduling:
    incremental_sync: "*/5 * * * *"     # каждые 5 минут
    full_sync: "0 2 * * *"              # каждый день в 2:00
    weekly_report: "0 6 * * 1"          # каждый понедельник в 6:00
```

## Мониторинг и метрики

### Ключевые метрики интеграции
```yaml
key_metrics:
  availability:
    - api_uptime_percentage
    - connection_success_rate
    - average_response_time
    
  data_quality:
    - tasks_with_assignee_percentage
    - tasks_with_valid_status_percentage
    - duplicate_task_count
    
  performance:
    - tasks_processed_per_second
    - api_call_success_rate
    - cache_hit_ratio
    
  business:
    - active_task_count
    - completion_rate_trend
    - employee_workload_balance
```

### Оповещения (Alerts)
```yaml
alerts:
  critical:
    - api_connection_failure
    - authentication_failure
    - data corruption_detected
    
  warning:
    - high_api_response_time (>5 секунд)
    - low_task_assignment_rate (<80%)
    - unusual_status_distribution_changes
    
  informational:
    - new_employee_detected
    - high_volume_task_creation
    - workflow_bottleneck_detected
```

## Процедуры развертывания

### Шаги для production развертывания
1. **Валидация конфигурации**
   - Проверить учетные данные API
   - Валидировать поля проекта
   - Тестировать базовые запросы

2. **Инициализация данных**
   - Выполнить полную синхронизацию задач
   - Построить кэш сотрудников
   - Валидировать маппинг полей

3. **Настройка мониторинга**
   - Настроить метрики производительности
   - Конфигурировать оповещения
   - Установить дашборды

4. **Тестирование загрузки**
   - Симулировать пиковые нагрузки
   - Проверить обработку ошибок
   - Валидировать отказоустойчивость

## Рекомендации по использованию

### Для анализа сотрудников
```yaml
employee_anal
