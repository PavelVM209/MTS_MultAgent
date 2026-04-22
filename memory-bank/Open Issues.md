---
type: dashboard
status: active
owner: pavel
updated: 2026-04-23
tags:
  - dashboard
  - dataview
  - issues
---

# Open Issues

Связанные заметки:
- [[Dashboard]]
- [[import-consistency]]
- [[artifact-retention]]
- [[manual-tests-vs-pytest]]

## Dataview Table

```dataview
TABLE status, updated, tags
FROM "issues"
WHERE type = "issue"
SORT updated DESC
```

## Dataview Task View

```dataview
LIST
FROM "issues"
WHERE type = "issue" AND status = "open"
SORT file.name ASC
```
