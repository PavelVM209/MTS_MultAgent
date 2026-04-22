---
type: reference
status: active
owner: pavel
updated: 2026-04-23
tags:
  - artifacts
  - storage
  - cleanup
---

# Artifacts

Связанные заметки:
- [[systemPatterns]]
- [[artifact-cleanup-workflow]]
- [[ADR-0001-run-artifacts]]
- [[ADR-0002-jira-snapshots]]

## Main Artifact Areas

### `reports/runs/`

- полный набор артефактов отдельного запуска
- можно удалять как runtime artifacts, если они не нужны для анализа или не закоммичены

### `reports/latest/`

- последний валидный слой артефактов
- удобен для потребителей, которым не нужен `run_id`
- не считать это историческим архивом

### `data/processed/`

- кэш stage1/cleaned protocol outputs
- можно пересобрать
- считается временным runtime storage

### `data/index/`

- processing index
- служебное состояние инкрементальной обработки
- очищается cleanup workflow при локальном шуме

### `data/jira/snapshots/`

- snapshots Jira на момент конкретного запуска
- полезны для диффов и анализа инкремента
- в локальном workflow считаются runtime artifacts

## Can Be Deleted By Cleanup Workflow

- `reports/runs/`
- `data/index/`
- `data/processed/`
- `data/jira/snapshots/`
- новые untracked weekly output files

## Should Not Be Deleted Blindly

- tracked historical sample outputs
- committed baseline artifacts
- documents, ADR, notes

## Rule of Thumb

Если артефакт нужен только для локальной проверки текущего запуска и не зафиксирован в git как sample/reference, его должен убирать [[artifact-cleanup-workflow]].
