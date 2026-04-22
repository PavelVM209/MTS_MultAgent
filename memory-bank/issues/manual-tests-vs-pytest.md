---
type: issue
status: open
owner: pavel
updated: 2026-04-23
tags:
  - issue
  - tests
  - pytest
  - manual
---

# Manual Tests vs Pytest

## Problem

Часть сценариев выглядит как pytest tests, но по сути является ручными или integration-heavy scripts.

## Risks

- непредсказуемый runtime
- лишние generated artifacts
- сложность понимания, что должно идти в smoke/full suite

## Desired End State

- smoke tests
- stable automated pytest suite
- manual/integration scenarios, явно отделённые по маркерам или расположению
