---
type: context
status: active
owner: pavel
updated: 2026-04-23
tags:
  - technical-context
  - runtime
  - testing
---

# Tech Context

Связанные заметки:
- [[systemPatterns]]
- [[testing-workflow]]
- [[artifact-cleanup-workflow]]
- [[Integrations]]
- [[Artifacts]]

## Stack

- Python 3.11
- pytest
- asyncio
- aiofiles / aiohttp
- YAML config
- markdown/json file artifacts

## Project Layout

- `src/` — основной код
- `tests/` — pytest и сценарные тесты
- `config/` — YAML-конфигурация
- `data/` — data lake, индексы, snapshots, processed cache
- `reports/` — run artifacts, latest copies, weekly outputs
- `memory-bank/` — Obsidian vault / project memory

## Current Testing Commands

```bash
./venv_py311/bin/pytest -q
./venv_py311/bin/pytest -q tests/unit/test_json_memory_store.py tests/test_weekly_reports_agent.py
./venv_py311/bin/python scripts/cleanup_test_artifacts.py
./venv_py311/bin/python scripts/cleanup_test_artifacts.py --apply
```

## What Counts As Temporary

- `reports/runs/`
- `data/index/`
- `data/processed/`
- `data/jira/snapshots/`
- новые untracked weekly summary files
- новые untracked weekly report files

## What Is Not Temporary By Default

- tracked historical fixtures and samples in `reports/`
- committed baseline outputs
- documentation and ADRs
- `memory-bank/` notes

## Runtime Constraints

- часть сценариев зависит от реальных внешних интеграций
- ручные тесты могут генерировать артефакты даже при “просто посмотреть”
- cleanup лучше считать обязательным шагом после тяжёлых прогонов

## Environment Notes

- важные переменные обычно загружаются из `.env`
- интеграции: Jira, Confluence, LLM
- не все тесты должны выполняться без внешних данных; это нужно явно документировать в workflow
