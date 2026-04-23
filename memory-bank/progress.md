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
- добавлен quality-first evidence-based pipeline:
  - Task Analyzer сохраняет structured task evidence
  - Meeting Analyzer сохраняет per-protocol evidence и employee evidence traces
  - Meeting Stage 2 использует evidence-first prompt и 10 supporting protocols
  - Weekly Reports читает run artifacts и employee evidence bundle
  - Quality Validator больше не считает schema mismatch в memory store ошибкой анализа
- добавлен Jira incremental layer:
  - issue fingerprint cache в `data/index/jira_issue_fingerprints.json`
  - fingerprint diff artifact на каждый run
  - re-use latest task analysis при отсутствии изменений в Jira issues
  - selective employee-level rebuild при частичных изменениях Jira issues
- добавлен SQLite operational index:
  - `data/index/analysis_index.db`
  - таблицы для `runs`, `jira_issue_versions`, `task_evidence_index`
  - SQLite-first read-path в Weekly Reports для `runs`, `task_evidence`, `meeting_employee_evidence`

### Verified

- `./venv_py311/bin/pytest -q` проходил зелёным
- повторный smoke run:
  - `./venv_py311/bin/pytest -q tests/unit/test_json_memory_store.py tests/test_weekly_reports_agent.py`
  - результат: зелёный
- cleanup workflow проверен в `dry-run` и `--apply`
- после evidence-pipeline изменений:
  - `./venv_py311/bin/python -m py_compile src/agents/task_analyzer_agent_improved.py src/agents/meeting_analyzer_agent_improved.py src/agents/weekly_reports_agent_complete.py src/agents/quality_validator_agent.py src/agents/quality_orchestrator.py`
  - `./venv_py311/bin/pytest -q`
  - результат: `26 passed`
- runtime/test-артефакты очищены через `scripts/cleanup_test_artifacts.py --apply`
- после incremental Jira + SQLite index изменений:
  - `./venv_py311/bin/python -m py_compile src/core/jira_issue_fingerprint_store.py src/core/analysis_index_db.py src/agents/task_analyzer_agent_improved.py`
  - `./venv_py311/bin/pytest -q`
  - результат: `26 passed`

### Outcome

- проект стал заметно чище с точки зрения runtime-артефактов
- кодовая база лучше переносит обычный `pytest`
- появился повторяемый operational workflow для разработки и тестов
- появилась основа для проверяемых выводов: каждый weekly/meeting insight можно связывать с task evidence, meeting evidence и employee trace
- появился базовый механизм, чтобы не тратить повторный expensive analysis на неизменившиеся Jira issues
- появился следующий слой оптимизации качества/стоимости: частичный rebuild только по затронутым сотрудникам, а не полный task pipeline
- SQLite слой перестал быть только write-side каталогом и начал реально использоваться в read-path weekly aggregation
- оркестратор weekly workflow переведён на актуальный SQLite-first weekly path
- оркестратор task workflow переведён на явный incremental decision path с режимами `reuse`, `selective`, `full`

## 2026-04-20 to 2026-04-22

### Done

- оформлен переход на run-based артефакты
- добавлен `ProcessingIndex`
- введён подход `reports/runs/{run_id}` + `reports/latest`
- Weekly Reports переведён на чтение из run-артефактов
- внедрён Jira snapshot/diff как инкремент между запусками

### Architecture Notes

- ключевые решения зафиксированы в [[ADR-0001-run-artifacts]] и [[ADR-0002-jira-snapshots]]
- evidence-based pipeline зафиксирован в [[ADR-0003-evidence-based-pipeline]]
- storage roadmap зафиксирован в [[ADR-0004-storage-roadmap-sql-vector]]

## Earlier Stable Achievements

- Jira интеграция подтверждена на реальных данных
- Task Analyzer работает как основной агент извлечения Jira-аналитики
- Meeting Analyzer работает, но требует внимания к производительности
- Weekly Reports Agent собирает недельный слой и публикует в Confluence

## What To Update Next

- пополнять эту заметку после каждого крупного изменения
- не превращать её в длинный архив логов; детали выносить в `sessions/`
