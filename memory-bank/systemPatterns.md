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
