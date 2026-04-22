---
type: workflow
status: active
owner: pavel
updated: 2026-04-23
tags:
  - testing
  - workflow
  - pytest
---

# Testing Workflow

Связанные заметки:
- [[Testing Dashboard]]
- [[artifact-cleanup-workflow]]
- [[manual-tests-vs-pytest]]

## Purpose

Дать повторяемый тестовый цикл без засорения рабочего дерева.

## Default Flow

1. Открыть [[activeContext]]
2. Проверить [[progress]]
3. Запустить нужный тестовый набор
4. Посмотреть `git status --short`
5. Запустить cleanup workflow
6. Зафиксировать результат в `sessions/`

## Recommended Commands

### Smoke

```bash
./venv_py311/bin/pytest -q tests/unit/test_json_memory_store.py tests/test_weekly_reports_agent.py
```

### Full

```bash
./venv_py311/bin/pytest -q
```

### Cleanup

```bash
./venv_py311/bin/python scripts/cleanup_test_artifacts.py
./venv_py311/bin/python scripts/cleanup_test_artifacts.py --apply
```

## Rules

- если запуск генерирует артефакты, cleanup не опционален
- если меняется test workflow, обновить эту заметку
- ручные сценарии и pytest suite не смешивать без явной причины
