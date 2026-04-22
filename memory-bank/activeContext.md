---
type: context
status: active
owner: pavel
updated: 2026-04-23
tags:
  - active-context
  - planning
  - obsidian
---

# Active Context

Основные точки входа:
- [[Dashboard]]
- [[projectbrief]]
- [[progress]]
- [[Testing Dashboard]]
- [[Artifacts]]

## Current Goal

Превратить `memory-bank/` в рабочий Obsidian vault и использовать его как операционную базу знаний проекта, а не как архив длинных заметок.

## Current State

- `pytest` проходит: основной тестовый контур сейчас зелёный
- cleanup workflow оформлен через `scripts/cleanup_test_artifacts.py`
- импортный слой внутри `src` выровнен
- `JSONMemoryStore` доведён до ожидаемого тестами поведения
- `memory-bank/` начинает использоваться как главная project memory

## Next 3-5 Steps

1. Поддерживать [[testing-workflow]] и [[artifact-cleanup-workflow]] как source of truth
2. Обновлять [[progress]] после каждой существенной сессии
3. Обновлять [[systemPatterns]] при изменении архитектуры run-артефактов, snapshot/diff или retention
4. Вести рабочие заметки в [[sessions/2026-04-23]] и следующих daily/session notes
5. Решить, нужен ли `Makefile` или другой тонкий CLI-слой поверх тестового workflow

## Open Questions

- Нужен ли `Makefile` для `test`, `test-smoke`, `clean-artifacts`
- Как лучше отделить ручные сценарии от pytest-набора: markers или отдельная директория `tests/manual`
- Хотим ли расширять vault шаблонами для issue/release/session через Templater

## Current Blockers

- Нет формализованного разделения между `manual`, `integration` и `smoke` сценариями
- Есть риск повторного появления runtime-артефактов, если workflow не соблюдать последовательно

## Watch Areas

- [[manual-tests-vs-pytest]]
- [[artifact-retention]]
- [[import-consistency]]

## Quick Commands

```bash
./venv_py311/bin/pytest -q
./venv_py311/bin/pytest -q tests/unit/test_json_memory_store.py tests/test_weekly_reports_agent.py
./venv_py311/bin/python scripts/cleanup_test_artifacts.py
./venv_py311/bin/python scripts/cleanup_test_artifacts.py --apply
```
