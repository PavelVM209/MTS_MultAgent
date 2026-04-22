---
type: workflow
status: active
owner: pavel
updated: 2026-04-23
tags:
  - cleanup
  - workflow
  - runtime-artifacts
---

# Artifact Cleanup Workflow

Связанные заметки:
- [[Artifacts]]
- [[testing-workflow]]
- [[why-cleanup-script-exists]]

## Purpose

Убирать runtime/test artifacts, не затрагивая tracked historical samples.

## Script

`scripts/cleanup_test_artifacts.py`

## Modes

### Dry Run

```bash
./venv_py311/bin/python scripts/cleanup_test_artifacts.py
```

### Apply

```bash
./venv_py311/bin/python scripts/cleanup_test_artifacts.py --apply
```

## What It Cleans

- `reports/runs/`
- `data/index/`
- `data/processed/`
- `data/jira/snapshots/`
- новые untracked weekly summary/report files
- восстанавливает служебный `data/memory/json/.index.json`

## What It Avoids

- tracked historical outputs
- committed reference artifacts
- документы и notes

## Verification

```bash
git status --short
```
