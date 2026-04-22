---
type: dashboard
status: active
owner: pavel
updated: 2026-04-23
tags:
  - dashboard
  - dataview
  - sessions
---

# Recent Sessions

Связанные заметки:
- [[Dashboard]]
- [[activeContext]]
- [[progress]]

## Latest Session Notes

```dataview
TABLE status, updated, tags
FROM "sessions"
WHERE type = "session"
SORT file.name DESC
```

## Planned / Active Sessions

```dataview
LIST
FROM "sessions"
WHERE type = "session" AND (status = "planned" OR status = "active")
SORT file.name DESC
```
