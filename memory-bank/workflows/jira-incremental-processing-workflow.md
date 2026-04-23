---
type: workflow
status: proposed
owner: pavel
updated: 2026-04-23
tags:
  - workflow
  - jira
  - incremental
  - cache
---

# Jira Incremental Processing Workflow

Связанные заметки:
- [[ADR-0002-jira-snapshots]]
- [[ADR-0004-storage-roadmap-sql-vector]]
- [[ImprovedTaskAnalyzerAgent]]

## Problem

Snapshot/diff уже показывает изменения между Jira runs, но этого недостаточно, чтобы гарантированно не гонять повторный LLM-анализ по неизменившимся задачам.

## Current Status

Частично внедрено:

- issue fingerprint cache в JSON
- fingerprint diff artifact на каждый run
- Task Analyzer умеет reuse latest task analysis, если fingerprints не изменились
- Task Analyzer умеет selective employee-level rebuild, если changed issues затрагивают только часть сотрудников
- SQLite index сохраняет run catalog, issue versions и task evidence index

## Target Behavior

- неизменившаяся Jira issue не отправляется повторно в expensive analysis
- изменившаяся issue анализируется заново
- сотрудник пересобирается только если изменился его task evidence или role context
- weekly использует уже сохранённый evidence, а не повторяет извлечение

## Issue Fingerprint

Для каждой Jira issue нужно считать fingerprint по стабильным полям:

```text
issue_key
summary
status
assignee
priority
updated
description
comments ids/body/update timestamps
project
```

Минимальный вариант:

```text
sha256(json.dumps(normalized_issue_payload, sort_keys=True))
```

## Cache Contract

Хранить:

- `issue_key`
- `fingerprint`
- `last_seen_run_id`
- `last_analyzed_run_id`
- `task_evidence_path`
- `analysis_status`
- `updated_at`

## Processing Rules

- если `issue_key + fingerprint` уже есть: reuse existing task evidence
- если `issue_key` есть, но fingerprint изменился: generate new task evidence
- если issue исчезла из текущего JQL: пометить `not_seen_in_current_run`, но не удалять историю
- если assignee изменился: пересобрать employee evidence для старого и нового assignee

## Recommended Implementation

Этап 1:

- оставить JSON artifacts как есть
- использовать file-based `data/index/jira_issue_fingerprints.json`
- использовать его в Task Analyzer перед LLM stage

Этап 2:

- расширить SQLite index как основной read-path для incremental logic
- связать tables: `runs`, `jira_issues`, `jira_issue_versions`, `task_evidence`, `employee_evidence`

## Why This Matters

- снижает стоимость и время повторных прогонов
- повышает стабильность выводов
- делает изменения explainable: можно показать, почему сотрудник был переоценён именно в этом run
