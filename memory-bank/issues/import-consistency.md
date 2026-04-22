---
type: issue
status: open
owner: pavel
updated: 2026-04-23
tags:
  - issue
  - imports
  - packaging
---

# Import Consistency

## Problem

Исторически в проекте смешивались:

- импорты через `src.*`
- “плоские” импорты вроде `agents.*`
- относительные импорты внутри пакета

## Why It Matters

- ломается test collection
- появляются fragile path hacks в тестах
- становится трудно предсказать, из какого корня должен импортироваться модуль

## Current Direction

- внутри `src` использовать пакетно-согласованный стиль
- в тестах поднимать корень проекта единообразно
