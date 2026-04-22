---
type: dashboard
status: active
owner: pavel
updated: 2026-04-23
tags:
  - dashboard
  - home
  - obsidian
---

# Dashboard

## Start Here

- [[activeContext]]
- [[progress]]
- [[projectbrief]]
- [[Testing Dashboard]]
- [[Artifacts]]
- [[Integrations]]
- [[Open Issues]]
- [[Recent Sessions]]
- [[Workflows Index]]
- [[Decisions Index]]

## Agents

- [[ImprovedTaskAnalyzerAgent]]
- [[ImprovedMeetingAnalyzerAgent]]
- [[WeeklyReportsAgentComplete]]
- [[QualityOrchestrator]]

## Workflows

- [[testing-workflow]]
- [[artifact-cleanup-workflow]]
- [[jira-analysis-workflow]]
- [[meeting-analysis-workflow]]

## Decisions

- [[ADR-0001-run-artifacts]]
- [[ADR-0002-jira-snapshots]]
- [[why-cleanup-script-exists]]

## Open Issues

- [[import-consistency]]
- [[artifact-retention]]
- [[manual-tests-vs-pytest]]

## Sessions

- [[sessions/2026-04-23]]
- [[sessions/2026-04-24]]

## Quick Commands

```bash
./venv_py311/bin/pytest -q
./venv_py311/bin/pytest -q tests/unit/test_json_memory_store.py tests/test_weekly_reports_agent.py
./venv_py311/bin/python scripts/cleanup_test_artifacts.py
./venv_py311/bin/python scripts/cleanup_test_artifacts.py --apply
```
