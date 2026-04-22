---
type: workflow
status: active
owner: pavel
updated: 2026-04-23
tags:
  - jira
  - workflow
  - task-analysis
---

# Jira Analysis Workflow

Связанные заметки:
- [[ImprovedTaskAnalyzerAgent]]
- [[ADR-0002-jira-snapshots]]

## Flow

1. Получить задачи из Jira
2. Нормализовать task payload
3. Выполнить task analysis
4. Сохранить snapshot
5. Построить diff к предыдущему snapshot
6. Сохранить run artifacts и latest copies

## Key Outputs

- task-analysis outputs
- jira snapshot
- jira diff
