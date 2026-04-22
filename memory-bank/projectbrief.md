---
type: overview
status: active
owner: pavel
updated: 2026-04-23
tags:
  - overview
  - brief
  - project
---

# Project Brief

Связанные заметки:
- [[Dashboard]]
- [[productContext]]
- [[systemPatterns]]
- [[Testing Dashboard]]

## Summary

`MTS_MultAgent` — это многоагентная система для анализа производительности команды на основе Jira, протоколов совещаний и weekly-данных с публикацией результатов в Confluence.

## Main Components

- [[ImprovedTaskAnalyzerAgent]]
- [[ImprovedMeetingAnalyzerAgent]]
- [[WeeklyReportsAgentComplete]]
- [[QualityOrchestrator]]

## Main Storage and Artifacts

- `data/` — runtime data, indexes, snapshots, processed cache
- `reports/runs/` — артефакты отдельных запусков
- `reports/latest/` — последние копии результатов
- `memory-bank/` — операционная база знаний и Obsidian vault

## Current Project State

- базовый тестовый контур стабилизирован
- run-based artifact model внедрена
- cleanup workflow внедрён
- vault для project memory оформлен

## Current Risks

- performance of meeting analysis
- размытая граница между manual и automated test scenarios
- дисциплина cleanup после тяжёлых прогонов
