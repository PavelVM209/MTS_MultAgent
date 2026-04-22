---
type: reference
status: active
owner: pavel
updated: 2026-04-23
tags:
  - integrations
  - jira
  - confluence
  - llm
---

# Integrations

## Jira

- основной источник задач и task dynamics
- используется [[ImprovedTaskAnalyzerAgent]]
- snapshots/diff оформлены через [[ADR-0002-jira-snapshots]]
- чувствительная зона: качество полей, comments/worklogs, стабильность auth

## Confluence

- основной канал публикации weekly outputs
- используется [[WeeklyReportsAgentComplete]]
- важно хранить не только публикацию, но и локальный воспроизводимый artifact

## LLM

- участвует в task, meeting и weekly analysis
- даёт качество, но также является bottleneck по latency и стоимости
- особенно чувствителен к объёму протоколов и структуре prompt

## Env Vars / Config

- `.env` и YAML config должны рассматриваться как operational configuration layer
- важно не размазывать настройки по нескольким несогласованным источникам

## Risks

- ручные интеграционные сценарии могут менять filesystem state
- результаты LLM нужно стабилизировать артефактами и fallback extraction
