---
type: decision
status: accepted
owner: pavel
updated: 2026-04-23
tags:
  - adr
  - artifacts
  - runs
---

# ADR-0001 Run Artifacts

Источник: `docs/adr/0001-run-artifacts-and-incremental-processing-index.md`

## Decision

Использовать `reports/runs/{run_id}` как атомарную единицу хранения результатов анализа и `reports/latest/` как слой последних копий.

## Why

- воспроизводимость
- прозрачная отладка
- удобный latest layer для downstream consumers

## Impact

- все workflow должны учитывать run-based модель
- cleanup workflow должен понимать, что `reports/runs/` — runtime storage
