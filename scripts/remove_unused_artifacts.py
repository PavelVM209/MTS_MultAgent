#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Удаление неиспользуемых (legacy/одноразовых) артефактов проекта.

ВАЖНО:
- Скрипт по умолчанию работает в режиме dry-run (ничего не удаляет).
- Удаляет только то, что подтверждено поиском по репозиторию как неиспользуемое runtime-алгоритмом:
  1) reports/daily/stages/ (legacy структура)
  2) scripts/migrate_cleaned_protocols.py (одноразовая миграция под дату)
  3) scripts/test_role_context_integration.py (ручной тест/демо)
- НЕ трогает:
  - reports/daily/.processing_tracker.json
  - reports/daily/YYYY-MM-DD/* (история анализа)
  - stage1_text_analysis.txt / stage2_final_json.json (backward-compat)

Примеры:
  source venv_py311/bin/activate
  python scripts/remove_unused_artifacts.py --dry-run
  python scripts/remove_unused_artifacts.py --apply
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import List


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _rm_path(path: Path, apply: bool) -> str:
    if not path.exists():
        return f"SKIP (not found): {path}"

    if not apply:
        return f"DRY-RUN: would remove {path}"

    try:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        return f"REMOVED: {path}"
    except Exception as e:
        return f"ERROR: failed to remove {path}: {e}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Удаление неиспользуемых файлов/папок (legacy artifacts).")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Только показать что будет удалено (по умолчанию).")
    mode.add_argument("--apply", action="store_true", help="Фактически удалить найденные артефакты.")
    args = parser.parse_args()

    apply = bool(args.apply)

    targets: List[Path] = [
        PROJECT_ROOT / "reports" / "daily" / "stages",
        PROJECT_ROOT / "scripts" / "migrate_cleaned_protocols.py",
        PROJECT_ROOT / "scripts" / "test_role_context_integration.py",
    ]

    print(f"Project root: {PROJECT_ROOT}")
    print("Mode:", "APPLY (delete)" if apply else "DRY-RUN (no delete)")
    print("-" * 80)

    for t in targets:
        print(_rm_path(t, apply=apply))

    print("-" * 80)
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
