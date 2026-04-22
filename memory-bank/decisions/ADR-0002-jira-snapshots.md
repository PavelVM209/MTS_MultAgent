---
type: decision
status: accepted
owner: pavel
updated: 2026-04-23
tags:
  - adr
  - jira
  - snapshots
---

# ADR-0002 Jira Snapshots

Источник: `docs/adr/0002-jira-snapshots-and-diff-increment.md`

## Decision

Фиксировать Jira snapshot на каждый run и строить machine-readable diff между соседними запусками.

## Why

- даёт формализованный инкремент
- уменьшает зависимость от сравнения только LLM outputs
- помогает weekly и trend analysis

## Impact

- нужен отдельный runtime слой для snapshot artifacts
- snapshot/diff должны быть документированы и учитываться в cleanup workflow
