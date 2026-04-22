---
type: dashboard
status: active
owner: pavel
updated: 2026-04-23
tags:
  - dashboard
  - dataview
  - decisions
---

# Decisions Index

Связанные заметки:
- [[Dashboard]]
- [[ADR-0001-run-artifacts]]
- [[ADR-0002-jira-snapshots]]
- [[why-cleanup-script-exists]]

## Accepted / Proposed Decisions

```dataview
TABLE status, updated, tags
FROM "decisions"
WHERE type = "decision"
SORT file.name ASC
```
