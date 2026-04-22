---
type: agent
status: active
owner: pavel
updated: 2026-04-23
tags:
  - agent
  - jira
  - task-analysis
---

# ImprovedTaskAnalyzerAgent

Код: `src/agents/task_analyzer_agent_improved.py`

Связанные заметки:
- [[QualityOrchestrator]]
- [[jira-analysis-workflow]]
- [[ADR-0002-jira-snapshots]]

## Responsibility

- получать задачи из Jira
- выполнять task analysis
- сохранять run artifacts
- формировать Jira snapshot и diff

## Inputs

- Jira tasks
- config/env
- role context

## Outputs

- `reports/runs/{run_id}/task-analysis/...`
- `reports/latest/task-analysis/...`
- `data/jira/snapshots/{run_id}.json`
- `reports/runs/{run_id}/jira-diff/jira-diff.json`

## Watch Areas

- import consistency
- устойчивость parsing/extraction
- корректность snapshot/diff
