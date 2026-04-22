---
type: dashboard
status: active
owner: pavel
updated: 2026-04-23
tags:
  - testing
  - dashboard
  - pytest
---

# Testing Dashboard

Связанные заметки:
- [[testing-workflow]]
- [[artifact-cleanup-workflow]]
- [[manual-tests-vs-pytest]]

## Smoke Set

```bash
./venv_py311/bin/pytest -q tests/unit/test_json_memory_store.py tests/test_weekly_reports_agent.py
```

## Full Suite

```bash
./venv_py311/bin/pytest -q
```

## Heavier / More Context-Dependent Scenarios

- `tests/test_improved_task_analyzer.py`
- `tests/test_improved_meeting_analyzer.py`
- `tests/test_confluence_integration.py`
- `tests/test_full_system_manual.py`

## Notes

- не все сценарии одинаково “чисты” с точки зрения артефактов
- после тяжёлых прогонов использовать [[artifact-cleanup-workflow]]
- ручные и интеграционные сценарии стоит дальше разводить по маркерам или структуре каталогов
