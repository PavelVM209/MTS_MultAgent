# ADR: Переход на run-based артефакты (reports/runs, reports/latest) и инкрементальную обработку по ProcessingIndex

- Статус: accepted
- Дата: 2026-04-22
- Авторы: DevX Agent

## Контекст

Проект выполняет периодический анализ:
- протоколов встреч (meeting analysis)
- задач Jira (task analysis)
- финальную оркестрацию (unified analysis)

Ранее артефакты складывались в `reports/daily/{YYYY-MM-DD}/...`, а инкрементальность частично обеспечивалась отдельным tracker’ом и “кэшем” по файловой системе. Это создавало проблемы для:
- сравнения “новый запуск vs старый запуск” как инкремента (нет явной сущности run)
- стабильного доступа к “последнему” результату (много `latest` ссылок внутри daily)
- повторного использования LLM-результатов и кэша при смене схемы папок
- подготовки динамики по сотрудникам/команде на основе последовательности запусков

Также требовалось разнести “сырьё” и “обработанные данные” в data lake, чтобы:
- отделить входы (raw) от результатов (processed)
- внедрить инкрементальность по hash без привязки к дням

## Решение

1) Data lake
- Входные данные протоколов храним в `data/raw/protocols/*.txt`
- Очищенные протоколы (stage1 cleaning) кэшируем в `data/processed/protocols_cleaned/*.txt`

2) Инкрементальность по хэшу
- Вводим индекс `ProcessingIndex` (JSON) `data/index/processing_index.json`
- Ключ индекса: `(processing_type, file_hash)`
- Для `meeting_clean`:
  - при наличии записи и существующего `result_path` возвращаем кэш без повторного LLM вызова
  - иначе выполняем очистку и делаем `upsert` записи в индекс

3) Run-based артефакты (результаты запусков)
- Вводим `reports/runs/{run_id}/...` как “атомарную” единицу запуска анализа
- Вводим `reports/latest/` как стабильную точку доступа к последним результатам (копии артефактов + `run_id.txt`)
- Менеджер `RunFileManager` управляет:
  - инициализацией run-структуры
  - записью JSON/TXT
  - обновлением latest (копированием)

4) Миграция агентов и оркестратора
- `ImprovedMeetingAnalyzerAgent`:
  - stage2 comprehensive TXT и final JSON сохраняются в `reports/runs/{run_id}/meeting-analysis/...`
  - employee progression сохраняется в `reports/runs/{run_id}/employee_progression/*.json`
  - latest обновляется в `reports/latest/meeting-analysis/...`
- `ImprovedTaskAnalyzerAgent`:
  - stage1/stage2/final артефакты сохраняются в `reports/runs/{run_id}/task-analysis/...`
  - latest обновляется в `reports/latest/task-analysis/...`
  - backward compatibility: перезапись `stage1_text_analysis.txt` и `stage2_final_json.json` в корне проекта (временно)
- `FinalOrchestrator`:
  - грузит входы из `reports/latest/task-analysis/task-analysis.json` и `reports/latest/meeting-analysis/meeting-analysis.json`
  - сохраняет unified результаты в `reports/runs/{run_id}/unified-analysis/` и копирует в `reports/latest/unified-analysis/`

## Альтернативы

1) Оставить `reports/daily/{date}` и добавить “run_id внутри daily”
- Недостаточно: остаётся жёсткая привязка к дням и сложно сравнивать разные запуски внутри суток.

2) Делать `latest` через symlink
- На некоторых окружениях/FS менее переносимо, сложнее в CI/архивации.
- Выбрано копирование артефактов в `reports/latest`.

3) Инкрементальность по имени файла или mtime
- Ломается при переименованиях/копировании и не гарантирует идентичность контента.
- Выбран hash (MD5) как инвариант контента.

## Последствия

Плюсы:
- явная сущность “запуск” (run) для динамики команды и сравнения инкрементов
- стабильная точка доступа `reports/latest` для API/Confluence/CLI
- меньше повторных LLM вызовов за счёт кэша по hash
- единый data lake слой (raw/processed/index)

Минусы/риски:
- необходима миграция legacy-логики, завязанной на `reports/daily`
- в `reports/latest` теперь копии файлов (занимают место), но объёмы контролируемы retention’ом
- временная backward compatibility в корне проекта — требует последующего удаления

## План внедрения

1) Создать `RunFileManager`, `ProcessingIndex`, `hash_utils`
2) Перевести meeting stage1 cleaning на `data/raw|processed` + `ProcessingIndex`
3) Перевести meeting/task/final orchestrator на `reports/runs|latest`
4) Добавить ops-скрипты миграции/retention (migrate, purge)
5) Обновить документацию и memory-bank
6) После стабилизации удалить legacy `EnhancedFileManager`/`reports/daily`-зависимости (или оставить только для архивных чтений)

## Ссылки

- `src/core/run_file_manager.py`
- `src/core/processing_index.py`
- `src/agents/meeting_analyzer_agent_improved.py`
- `src/agents/task_analyzer_agent_improved.py`
- `src/orchestrator/final_orchestrator.py`
- `scripts/migrate_protocols_to_datalake.py`
- `scripts/purge_old_data.py`
