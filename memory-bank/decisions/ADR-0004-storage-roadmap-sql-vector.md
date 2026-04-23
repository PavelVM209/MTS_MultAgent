---
type: decision
status: proposed
owner: pavel
updated: 2026-04-23
tags:
  - adr
  - storage
  - sql
  - vector-db
  - roadmap
---

# ADR-0004 Storage Roadmap: SQL And Vector DB

## Context

Сейчас проект использует JSON artifacts, `JSONMemoryStore`, processing index и run directories. Это прозрачно и удобно для отладки, но при росте истории появятся проблемы:

- сложно быстро искать по сотруднику, issue, run, risk, blocker
- сложно делать инкрементальный Jira cache
- сложно строить cross-run аналитику
- vector retrieval по протоколам и комментариям невозможен без отдельного индекса

## Decision Direction

Не заменять JSON artifacts. Добавить два дополнительных слоя:

- SQL как operational/index database
- vector DB как semantic retrieval layer

## SQL Layer

Рекомендуемый первый выбор: SQLite.

Почему:

- минимальная сложность внедрения
- не требует сервера
- хорошо подходит для локальной разработки
- можно мигрировать на Postgres позже

Что хранить:

- `runs`
- `jira_issues`
- `jira_issue_versions`
- `task_evidence`
- `meeting_protocols`
- `meeting_evidence`
- `employee_evidence`
- `weekly_reports`
- `validation_reports`

Сложность: средняя.

Оценка внедрения:

- базовая SQLite-схема и DAO: 1-2 дня
- миграция чтения weekly на SQL + fallback JSON: 1-2 дня
- тесты и cleanup/migrations: 1 день

## Vector Layer

Рекомендуемый первый выбор: Chroma или LanceDB.

Что индексировать:

- cleaned protocol chunks
- meeting evidence excerpts
- Jira comments/descriptions
- employee evidence traces
- weekly insights

Зачем:

- semantic search по прошлым обсуждениям
- retrieval для LLM перед weekly/manager report
- поиск похожих blockers и recurring risks

Сложность: средняя-высокая.

Оценка внедрения:

- chunking + embeddings + local vector store: 1-2 дня
- retrieval API для агентов: 1-2 дня
- качество retrieval/eval: 2+ дня

## Recommended Order

1. Сначала SQL для инкрементальности Jira и cross-run evidence index
2. Затем vector DB для semantic retrieval
3. JSON artifacts оставить как audit/source-of-truth layer

## Current Status

Частично реализовано:

- SQLite index уже ведётся в коде
- Weekly Reports использует SQLite-first read-path с fallback на file-based artifacts
- JSON artifacts остаются основным audit layer

## Why Not Vector First

Vector DB хорошо ищет похожий смысл, но плохо заменяет точные связи:

- какой run создал evidence
- какой issue fingerprint был актуален
- какой сотрудник связан с каким blocker
- какой validation report относится к какому artifact

Поэтому vector DB должна дополнять SQL, а не заменять его.
