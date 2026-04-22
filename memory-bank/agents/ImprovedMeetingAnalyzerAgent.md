---
type: agent
status: active
owner: pavel
updated: 2026-04-23
tags:
  - agent
  - meeting-analysis
  - protocols
---

# ImprovedMeetingAnalyzerAgent

Код: `src/agents/meeting_analyzer_agent_improved.py`

Связанные заметки:
- [[QualityOrchestrator]]
- [[meeting-analysis-workflow]]
- [[artifact-retention]]

## Responsibility

- очищать и анализировать meeting protocols
- объединять meeting layer с task layer
- сохранять per-run outputs и employee progression

## Inputs

- raw protocols
- task analyzer outputs
- processing index

## Outputs

- `data/processed/protocols_cleaned/...`
- `reports/runs/{run_id}/meeting-analysis/...`
- `reports/runs/{run_id}/employee_progression/...`
- `reports/latest/meeting-analysis/...`

## Main Risk

- heavy runtime / latency
- стоимость и длительность LLM analysis
