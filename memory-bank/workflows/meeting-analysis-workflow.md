---
type: workflow
status: active
owner: pavel
updated: 2026-04-23
tags:
  - meetings
  - workflow
  - protocols
---

# Meeting Analysis Workflow

Связанные заметки:
- [[ImprovedMeetingAnalyzerAgent]]
- [[Artifacts]]

## Flow

1. Найти новые или релевантные протоколы
2. Очистить протоколы и положить cleaned outputs в processed cache
3. Соединить meeting layer с task layer
4. Сохранить final meeting analysis в `reports/runs/{run_id}`
5. Обновить `reports/latest`

## Watch Areas

- длительность обработки
- рост processed cache
- согласованность employee progression
