---
type: log
status: active
owner: pavel
updated: 2026-04-23
tags:
  - progress
  - changelog
  - project-memory
---

# Progress

Связанные заметки:
- [[activeContext]]
- [[systemPatterns]]
- [[testing-workflow]]
- [[artifact-cleanup-workflow]]
- [[sessions/2026-04-23]]

## 2026-04-23

### Done

- выровнен пакетный импорт внутри `src`
- исправлены старые тесты, которые импортировали модули из неправильного корня
- восстановлены `src/core/jira_snapshot_store.py` и `src/core/jira_diff.py`
- стабилизирован `src/core/json_memory_store.py`
- добавлен `tests/conftest.py` для единого import-path
- добавлен `scripts/cleanup_test_artifacts.py`
- обновлён `.gitignore` для runtime/test-артефактов
- обновлён `README.md` с новым тестовым и cleanup workflow
- `memory-bank/` преобразован в структуру Obsidian vault

### Verified

- `./venv_py311/bin/pytest -q` проходил зелёным
- повторный smoke run:
  - `./venv_py311/bin/pytest -q tests/unit/test_json_memory_store.py tests/test_weekly_reports_agent.py`
  - результат: зелёный
- cleanup workflow проверен в `dry-run` и `--apply`

### Outcome

- проект стал заметно чище с точки зрения runtime-артефактов
- кодовая база лучше переносит обычный `pytest`
- появился повторяемый operational workflow для разработки и тестов

## 2026-04-20 to 2026-04-22

### Done

- оформлен переход на run-based артефакты
- добавлен `ProcessingIndex`
- введён подход `reports/runs/{run_id}` + `reports/latest`
- Weekly Reports переведён на чтение из run-артефактов
- внедрён Jira snapshot/diff как инкремент между запусками

### Architecture Notes

- ключевые решения зафиксированы в [[ADR-0001-run-artifacts]] и [[ADR-0002-jira-snapshots]]

## Earlier Stable Achievements

- Jira интеграция подтверждена на реальных данных
- Task Analyzer работает как основной агент извлечения Jira-аналитики
- Meeting Analyzer работает, но требует внимания к производительности
- Weekly Reports Agent собирает недельный слой и публикует в Confluence

## What To Update Next

- пополнять эту заметку после каждого крупного изменения
- не превращать её в длинный архив логов; детали выносить в `sessions/`
