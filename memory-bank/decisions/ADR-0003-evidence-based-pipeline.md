---
type: decision
status: accepted
owner: pavel
updated: 2026-04-23
tags:
  - adr
  - evidence
  - quality
  - architecture
---

# ADR-0003 Evidence-Based Pipeline

## Context

Для проекта важнее максимальное качество анализа, чем минимальное время выполнения. Агрессивные summaries и smoke/offline подходы могут потерять нюансы: кто что сказал, какие есть blockers, где проявляется лидерство, какие задачи подтверждаются обсуждениями.

## Decision

Строим evidence-based pipeline:

- Task Analyzer сохраняет structured task evidence
- Meeting Analyzer сохраняет per-protocol evidence и employee evidence traces
- Stage 2 Meeting Analysis получает evidence index по всем протоколам
- полные тексты протоколов остаются supporting context и ограничиваются 10 протоколами
- Weekly Reports строит employee evidence bundle из run artifacts
- LLM employee insights используют строгий JSON contract и repair-pass

## Consequences

Плюсы:

- выводы становятся проверяемыми
- weekly analysis может ссылаться на evidence, а не только на финальные summary
- меньше риска потерять важные blockers/action items
- легче объяснять менеджеру, почему сделан конкретный вывод

Минусы:

- больше артефактов
- больше объём данных в run directories
- нужен storage roadmap, иначе JSON-only слой станет неудобным при росте истории

## Current Implementation

- `task-analysis/evidence/task_evidence.json`
- `meeting-analysis/evidence/meeting_evidence_index.json`
- `employee_evidence/{employee}.json`
- weekly aggregation from run artifacts
- validation persistence is best-effort
