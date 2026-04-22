---
type: agent
status: active
owner: pavel
updated: 2026-04-23
tags:
  - agent
  - orchestrator
  - quality
---

# QualityOrchestrator

Код: `src/agents/quality_orchestrator.py`

Связанные заметки:
- [[ImprovedTaskAnalyzerAgent]]
- [[ImprovedMeetingAnalyzerAgent]]
- [[WeeklyReportsAgentComplete]]
- [[artifact-cleanup-workflow]]
- [[ADR-0001-run-artifacts]]

## Responsibility

- координировать запуск агентов
- применять quality loop
- сохранять одобренные результаты

## Why It Matters

- это точка, где бизнесовый pipeline становится управляемым процессом
- если orchestration неустойчив, весь downstream workflow становится хрупким

## Current Notes

- импорты были выровнены под единый пакетный стиль
- orchestration logic нужно держать согласованной с run-based artifact model
