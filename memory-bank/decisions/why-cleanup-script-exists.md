---
type: decision
status: accepted
owner: pavel
updated: 2026-04-23
tags:
  - cleanup
  - decision
  - workflow
---

# Why Cleanup Script Exists

## Problem

Тесты и ручные сценарии генерируют filesystem artifacts, которые:

- засоряют `git status`
- мешают видеть реальные изменения в коде
- провоцируют случайные коммиты runtime-мусора

## Decision

Добавить `scripts/cleanup_test_artifacts.py` и считать cleanup частью обычного engineering workflow.

## Important Constraint

Скрипт не должен удалять tracked historical samples и reference artifacts.
