---
type: workflow
status: active
owner: pavel
updated: 2026-04-23
tags:
  - workflow
  - evidence
  - quality
  - agents
---

# Evidence-Based Pipeline Workflow

Связанные заметки:
- [[ADR-0003-evidence-based-pipeline]]
- [[jira-incremental-processing-workflow]]
- [[ImprovedTaskAnalyzerAgent]]
- [[ImprovedMeetingAnalyzerAgent]]
- [[WeeklyReportsAgentComplete]]

## Purpose

Цель workflow - повысить качество и проверяемость анализа по всей цепочке, не жертвуя полнотой данных ради скорости.

## Flow

```text
Jira Fetch
  -> Task Evidence Extraction
  -> Task Employee Analysis
  -> Task Final JSON

Meeting Protocols
  -> Per-Protocol Cleaning
  -> Per-Protocol Evidence Extraction
  -> Employee Meeting Evidence Index
  -> Meeting/Task Correlation Analysis
  -> Meeting Final JSON

Quality Validator
  -> Validate Analysis Content
  -> Save Quality Report
  -> Do not fail workflow on memory schema mismatch

Weekly Reports
  -> Aggregate run artifacts
  -> Build Employee Evidence Bundle
  -> Per-Employee LLM Insight
  -> JSON Repair if needed
  -> Team Synthesis
  -> Final Weekly Report
```

## Artifacts

- `reports/runs/{run_id}/task-analysis/evidence/task_evidence.json`
- `reports/runs/{run_id}/meeting-analysis/evidence/meeting_evidence_index.json`
- `reports/runs/{run_id}/employee_evidence/{employee}.json`
- `reports/runs/{run_id}/meeting-analysis/final/meeting-analysis.json`
- `reports/weekly/weekly_report_*.json`

## Quality Rules

- не заменять полный анализ агрессивными summaries
- сохранять evidence отдельно от итоговой интерпретации
- weekly выводы должны строиться на employee evidence bundle
- LLM parse failure должен идти через JSON repair, а не просто терять инсайт
- validation persistence в memory store не должна ломать analysis workflow

## Current Limit

Meeting Stage 2 использует evidence по всем протоколам и полные supporting texts максимум по 10 протоколам.
