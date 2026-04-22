---
type: template
status: active
owner: pavel
updated: 2026-04-23
tags:
  - template
  - agent
  - workflow
---

# Agent Task Template

## Goal

Что именно нужно изменить и какой результат считается успешным.

## Constraints

- не трогать tracked historical artifacts без явного решения
- не ломать `reports/runs` / `reports/latest` модель без обновления документации
- после тестов запускать cleanup workflow
- держать изменения воспроизводимыми и проверяемыми

## Verify

```bash
./venv_py311/bin/pytest -q
./venv_py311/bin/python scripts/cleanup_test_artifacts.py
git status --short
```

## Notes

- если меняется архитектурный паттерн, обновить [[systemPatterns]]
- если меняется процесс, обновить соответствующий workflow note
- если принято новое устойчивое решение, добавить note в `decisions/`
