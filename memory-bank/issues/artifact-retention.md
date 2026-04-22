---
type: issue
status: open
owner: pavel
updated: 2026-04-23
tags:
  - issue
  - retention
  - artifacts
---

# Artifact Retention

## Problem

Пока не до конца формализовано:

- сколько хранить `reports/runs`
- когда очищать `data/processed`
- как долго хранить Jira snapshots локально

## Tension

С одной стороны, артефакты нужны для анализа и отладки. С другой, они быстро загрязняют локальное дерево и разрастаются по объёму.

## Next Step

Сформулировать retention policy по типам артефактов и отдельно описать:

- local dev retention
- CI/runtime retention
- historical sample retention
