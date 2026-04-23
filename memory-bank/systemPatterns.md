---
type: architecture
status: active
owner: pavel
updated: 2026-04-23
tags:
  - architecture
  - patterns
  - run-artifacts
---

# System Patterns

Связанные заметки:
- [[projectbrief]]
- [[techContext]]
- [[ADR-0001-run-artifacts]]
- [[ADR-0002-jira-snapshots]]
- [[ADR-0003-evidence-based-pipeline]]
- [[ADR-0004-storage-roadmap-sql-vector]]
- [[Artifacts]]

## Core Architecture

Проект использует иерархическую многоагентную схему:

- orchestration layer: `EmployeeMonitoringOrchestratorFixed`, scheduler, quality coordination
- agent layer: [[ImprovedTaskAnalyzerAgent]], [[ImprovedMeetingAnalyzerAgent]], [[WeeklyReportsAgentComplete]], `QualityValidatorAgent`
- core layer: config, llm client, jira client, memory store, processing index
- storage/artifact layer: `data/*`, `reports/runs/*`, `reports/latest/*`

## Primary Patterns

### Run-Based Artifacts

- каждый значимый запуск сохраняется в `reports/runs/{run_id}/...`
- это делает запуск атомарной единицей анализа
- последние результаты дублируются в `reports/latest/...`
- это основной паттерн для воспроизводимости и отладки

См. [[ADR-0001-run-artifacts]].

### Latest Copies

- `reports/latest/` нужен как удобная ссылка на последний валидный результат
- потребители не обязаны знать `run_id`
- диагностика и история всё равно идут через `reports/runs/`

### Processing Index

- `data/index/processing_index.json` хранит состояние инкрементальной обработки
- нужен для определения, какие протоколы уже были очищены/обработаны
- помогает не гонять повторно один и тот же expensive pipeline

### Cleaned Protocol Cache

- `data/processed/protocols_cleaned/` хранит очищенные stage1-версии протоколов
- это кэш, а не источник истины
- его можно пересобрать из входных данных

### Jira Snapshot / Diff

- snapshot хранится в `data/jira/snapshots/{run_id}.json`
- diff хранится в `reports/runs/{run_id}/jira-diff/jira-diff.json`
- это даёт формализованный инкремент между запусками

См. [[ADR-0002-jira-snapshots]].

### Jira Issue Fingerprint Cache

- поверх snapshot/diff добавлен issue-level fingerprint cache
- fingerprint считается по нормализованным полям Jira issue: summary, status, assignee, priority, updated, description, comments и related counters
- если набор issue fingerprints не изменился, Task Analyzer может переиспользовать latest task analysis вместо повторного LLM run
- на каждый run сохраняется отдельный `issue-fingerprint-diff.json`

Это уже не просто исторический diff между runs, а operational decision layer для `analyze vs reuse`.

См. [[jira-incremental-processing-workflow]].

### SQLite Operational Index

- `data/index/analysis_index.db` хранит быстрый operational index поверх JSON artifacts
- JSON artifacts остаются audit/source-of-truth layer
- SQLite слой нужен для быстрых выборок по `run_id`, `issue_key`, `fingerprint`, `employee_name`
- текущие таблицы: `runs`, `jira_issue_versions`, `task_evidence_index`, `meeting_employee_evidence_index`

Паттерн: `JSON for audit + SQLite for lookup/read-path`.

### SQLite-First Orchestration

- orchestration layer постепенно переводится на прямой вызов актуальных read-path, а не legacy collect-first веток
- Weekly workflow уже использует SQLite-first pipeline напрямую
- Task workflow уже принимает явное orchestration-решение `reuse / selective / full` перед запуском Task Analyzer
- это снижает риск расхождения между тем, что умеет агент, и тем, что реально вызывает оркестратор

### Evidence-Based Pipeline

- Task Analyzer создаёт `task_evidence` поверх Jira tasks
- Meeting Analyzer создаёт per-protocol evidence, meeting evidence index и employee evidence traces
- Meeting Stage 2 анализирует evidence по всем протоколам и использует полные тексты только как supporting context для 10 наиболее релевантных протоколов
- Weekly Reports собирает employee evidence bundle из run artifacts и генерирует персональные инсайты с JSON repair
- цель паттерна: максимальное качество и проверяемость выводов, а не ускорение любой ценой

См. [[ADR-0003-evidence-based-pipeline]] и [[evidence-based-pipeline-workflow]].

### Storage Roadmap

- JSON artifacts остаются audit/source-of-truth layer для воспроизводимости
- SQL база рекомендуется как operational index для runs, issues, evidence, employees, validation reports
- vector DB имеет смысл как retrieval layer для semantic search по протоколам, комментариям и historical evidence
- vector DB не должна заменять SQL и JSON artifacts

См. [[ADR-0004-storage-roadmap-sql-vector]].

### Memory Store as Operational State

- `JSONMemoryStore` хранит сериализованные состояния/результаты
- это не полноценная БД, а file-based store
- он подходит для текущего масштаба и делает данные прозрачными для отладки

### Cleanup as Part of Development Loop

- runtime/test-артефакты считаются частью рабочего цикла, а не случайным побочным эффектом
- после тестов/ручных прогонов используется [[artifact-cleanup-workflow]]
- tracked historical samples не удаляются cleanup-скриптом

## Design Preferences

- `async/await` для orchestration и I/O
- dataclass-based structured results
- file-based прозрачные артефакты
- явные workflow-заметки как часть engineering process
- минимум “магии”, максимум воспроизводимых шагов

## Known Tensions

- ручные сценарии и pytest-сценарии пока недостаточно строго отделены
- runtime-артефакты полезны для анализа, но загрязняют worktree без cleanup discipline
- Meeting Analyzer даёт полезный результат, но performance profile всё ещё тяжёлый
- повторный анализ Jira нужно перевести с run-level snapshot/diff на issue-level fingerprint cache
