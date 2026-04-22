---
type: dashboard
status: active
owner: pavel
updated: 2026-04-23
tags:
  - dashboard
  - dataview
  - workflows
---

# Workflows Index

Связанные заметки:
- [[Dashboard]]
- [[testing-workflow]]
- [[artifact-cleanup-workflow]]

## All Workflows

```dataview
TABLE status, updated, tags
FROM "workflows"
WHERE type = "workflow"
SORT file.name ASC
```
