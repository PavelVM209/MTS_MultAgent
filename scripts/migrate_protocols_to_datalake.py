#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Миграция протоколов из legacy `protocols/` в новый data lake `data/raw/protocols/`.

По умолчанию dry-run (ничего не копирует/не удаляет).
Режимы:
- --dry-run (default): показать план действий
- --copy: копировать файлы
- --move: переместить файлы (удалит из `protocols/`)

Пример:
  source venv_py311/bin/activate
  python scripts/migrate_protocols_to_datalake.py --dry-run
  python scripts/migrate_protocols_to_datalake.py --copy
  python scripts/migrate_protocols_to_datalake.py --move
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEGACY_PROTOCOLS_DIR = PROJECT_ROOT / "protocols"
TARGET_DIR = PROJECT_ROOT / "data" / "raw" / "protocols"


def _collect_txt_files(src: Path) -> List[Path]:
    if not src.exists():
        return []
    return sorted([p for p in src.glob("*.txt") if p.is_file()])


def main() -> int:
    parser = argparse.ArgumentParser(description="Миграция protocols/*.txt → data/raw/protocols/")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Показать действия (default).")
    mode.add_argument("--copy", action="store_true", help="Копировать файлы.")
    mode.add_argument("--move", action="store_true", help="Переместить файлы (удалит из protocols/).")
    args = parser.parse_args()

    do_copy = bool(args.copy)
    do_move = bool(args.move)
    apply = do_copy or do_move

    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    files = _collect_txt_files(LEGACY_PROTOCOLS_DIR)

    print(f"Project root: {PROJECT_ROOT}")
    print(f"Legacy protocols dir: {LEGACY_PROTOCOLS_DIR}")
    print(f"Target dir: {TARGET_DIR}")
    print("Mode:", "MOVE" if do_move else "COPY" if do_copy else "DRY-RUN")
    print("-" * 80)

    if not files:
        print("Нет файлов для миграции.")
        return 0

    for src_file in files:
        dst_file = TARGET_DIR / src_file.name
        if dst_file.exists():
            print(f"SKIP (exists): {dst_file}")
            continue

        if not apply:
            print(f"DRY-RUN: would {'move' if do_move else 'copy'} {src_file} -> {dst_file}")
            continue

        if do_move:
            shutil.move(str(src_file), str(dst_file))
            print(f"MOVED: {src_file} -> {dst_file}")
        else:
            shutil.copy2(str(src_file), str(dst_file))
            print(f"COPIED: {src_file} -> {dst_file}")

    print("-" * 80)
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
