---
type: context
status: active
owner: pavel
updated: 2026-04-23
tags:
  - product-context
  - business
  - team-analytics
---

# Product Context

Связанные заметки:
- [[projectbrief]]
- [[ImprovedTaskAnalyzerAgent]]
- [[ImprovedMeetingAnalyzerAgent]]
- [[WeeklyReportsAgentComplete]]

## Product Goal

Система должна автоматически собирать и интерпретировать сигналы о работе команды из Jira, протоколов встреч и еженедельных отчётов, чтобы руководитель видел:

- что реально происходит с командой
- кто перегружен, кто буксует, кто тянет критичные зоны
- где есть организационные и коммуникационные риски
- какие управленческие действия стоит предпринять

## Primary Users

- team lead / engineering manager
- product owner
- руководитель направления
- аналитик или операционный координатор, который собирает weekly/status слой

## Valuable Outputs

- daily task analysis
- meeting analysis with employee progression
- weekly consolidated report
- management recommendations
- Confluence-ready weekly publication

## Why This Is Valuable

- снижает ручной труд на разбор Jira и встреч
- ускоряет weekly/status ритм
- помогает выявлять тренды, а не только разовые события
- создаёт машинно-обрабатываемый слой поверх неструктурированных командных сигналов

## Quality Criteria

Результат ценен, если он:

- воспроизводим
- понятен менеджеру без чтения кода
- основан на реальных данных, а не только на LLM-summary
- может быть проверен через артефакты запуска
