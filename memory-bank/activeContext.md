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

Развивать quality-first evidence-based pipeline для мультиагентного анализа: Jira evidence, meeting evidence, employee evidence traces и weekly synthesis по run artifacts.

## Current State

- `pytest` проходит: основной тестовый контур сейчас зелёный
- cleanup workflow оформлен через `scripts/cleanup_test_artifacts.py`
- импортный слой внутри `src` выровнен
- `JSONMemoryStore` доведён до ожидаемого тестами поведения
- `memory-bank/` начинает использоваться как главная project memory
- добавлен evidence-based слой: task evidence, meeting evidence index, employee evidence traces
- Meeting Stage 2 ограничен 10 протоколами для полных supporting texts, но evidence index сохраняет покрытие всех протоколов
- Weekly Reports теперь должен опираться на run artifacts и employee evidence bundle, а не только на file-based memory
- внедрён Jira issue fingerprint cache: при отсутствии изменений Task Analyzer может переиспользовать latest analysis
- внедрён selective employee-level rebuild: при частичных Jira-изменениях Task Analyzer пересчитывает только затронутых сотрудников и переиспользует cached employee analysis для остальных
- добавлен SQLite index layer как operational catalog поверх JSON artifacts
- Weekly Reports начал использовать SQLite-first read-path для run catalog, task evidence и meeting employee evidence с fallback на file scan
- QualityOrchestrator weekly workflow теперь вызывает актуальный SQLite-first weekly path напрямую, без legacy collect-first ветки
- QualityOrchestrator task workflow теперь явно работает по orchestration-driven incremental plan: `reuse / selective / full`
- QualityOrchestrator meeting workflow тоже переведён на orchestration-driven incremental plan: `reuse / selective / full`
- QualityOrchestrator weekly workflow тоже переведён на orchestration-driven incremental plan
- Weekly Reports получил historical trend layer: сравнение текущего периода с предыдущим по сотрудникам и команде
- Weekly Reports начал строить recurring blockers, risks и strengths между периодами на evidence-уровне

## Next 3-5 Steps

1. Проверить selective rebuild на реальном повторном Jira run с частичными изменениями
2. Углубить recurring-pattern synthesis: перейти от keyword heuristics к более содержательному clustering/normalization по evidence themes
3. Добавить selective rebuild не только на employee layer, но и на evidence bundle / weekly pre-aggregation
4. Решить, когда добавлять vector retrieval поверх meeting/task evidence
5. Поддерживать [[testing-workflow]] и [[artifact-cleanup-workflow]] как source of truth

## Open Questions

- Нужен ли `Makefile` для `test`, `test-smoke`, `clean-artifacts`
- Как лучше отделить ручные сценарии от pytest-набора: markers или отдельная директория `tests/manual`
- Когда включать SQL слой: сразу перед следующим большим E2E или после стабилизации JSON evidence artifacts
- Нужна ли vector DB на первом этапе или достаточно SQL + full-text/JSON search

## Current Blockers

- Нет формализованного разделения между `manual`, `integration` и `smoke` сценариями
- Есть риск повторного появления runtime-артефактов, если workflow не соблюдать последовательно
- SQLite слой пока используется как индексный каталог, а не как основной read-path

## Watch Areas

- [[manual-tests-vs-pytest]]
- [[artifact-retention]]
- [[import-consistency]]
- [[jira-incremental-processing-workflow]]
- [[ADR-0004-storage-roadmap-sql-vector]]

## Quick Commands

```bash
./venv_py311/bin/pytest -q
./venv_py311/bin/pytest -q tests/unit/test_json_memory_store.py tests/test_weekly_reports_agent.py
./venv_py311/bin/python scripts/cleanup_test_artifacts.py
./venv_py311/bin/python scripts/cleanup_test_artifacts.py --apply
```
