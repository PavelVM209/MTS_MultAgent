---
type: agent
status: active
owner: pavel
updated: 2026-04-23
tags:
  - agent
  - weekly
  - confluence
---

# WeeklyReportsAgentComplete

Код: `src/agents/weekly_reports_agent_complete.py`

Связанные заметки:
- [[testing-workflow]]
- [[Integrations]]
- [[QualityOrchestrator]]

## Responsibility

- собирать weekly layer из run artifacts
- формировать management-ready weekly output
- публиковать в Confluence

## Inputs

- task stage2 artifacts
- meeting final artifacts
- memory store / weekly summary inputs

## Outputs

- `reports/weekly/weekly_report_YYYY-MM-DD.json`
- публикация в Confluence

## Notes

- агент уже был проверен отдельным pytest-сценарием
- новые generated weekly files нужно учитывать в [[artifact-cleanup-workflow]]
