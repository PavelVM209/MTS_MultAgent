#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Удаление сырых и обработанных данных старше N дней (по умолчанию 60).

Чистим только data lake:
- data/raw/**
- data/processed/**

Режимы:
- --dry-run (default): только показать что будет удалено
- --apply: фактически удалить

Опционально:
- --days N (default 60)

Пример:
  source venv_py311/bin/activate
  python scripts/purge_old_data.py --dry-run
  python scripts/purge_old_data.py --apply --days 60
"""

from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
INDEX_PATH = PROJECT_ROOT / "data" / "index" / "processing_index.json"


@dataclass
class Candidate:
    path: Path
    mtime: float


def _iter_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return [p for p in root.rglob("*") if p.is_file()]


def _collect_candidates(days: int) -> List[Candidate]:
    threshold = datetime.now() - timedelta(days=days)
    threshold_ts = threshold.timestamp()

    candidates: List[Candidate] = []
    for base in (RAW_DIR, PROCESSED_DIR):
        for p in _iter_files(base):
            try:
                st = p.stat()
                if st.st_mtime < threshold_ts:
                    candidates.append(Candidate(path=p, mtime=st.st_mtime))
            except FileNotFoundError:
                continue
    candidates.sort(key=lambda c: c.mtime)
    return candidates


def _delete_file(path: Path) -> None:
    path.unlink(missing_ok=True)


def _cleanup_empty_dirs(base: Path) -> None:
    if not base.exists():
        return
    for d in sorted([p for p in base.rglob("*") if p.is_dir()], reverse=True):
        try:
            if not any(d.iterdir()):
                d.rmdir()
        except Exception:
            continue


def _purge_index_missing_results() -> Tuple[bool, str]:
    if not INDEX_PATH.exists():
        return False, "SKIP: processing_index.json not found"

    try:
        # локальный импорт, чтобы скрипт работал без установки пакета
        from src.core.processing_index import ProcessingIndex  # type: ignore

        idx = ProcessingIndex(INDEX_PATH)
        removed = idx.purge_missing_results()
        return True, f"Index purge: removed {removed} missing result_path records"
    except Exception as e:
        return False, f"Index purge ERROR: {e}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Purge old data in data/raw and data/processed")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Показать что будет удалено (default).")
    mode.add_argument("--apply", action="store_true", help="Фактически удалить.")
    parser.add_argument("--days", type=int, default=60, help="Удалять файлы старше N дней (default 60).")
    args = parser.parse_args()

    apply = bool(args.apply)
    days = int(args.days)

    candidates = _collect_candidates(days=days)

    print(f"Project root: {PROJECT_ROOT}")
    print(f"Mode: {'APPLY' if apply else 'DRY-RUN'}; days={days}")
    print(f"Targets: {RAW_DIR} ; {PROCESSED_DIR}")
    print("-" * 80)

    if not candidates:
        print("Нет файлов для удаления.")
    else:
        for c in candidates:
            dt = datetime.fromtimestamp(c.mtime).isoformat(timespec="seconds")
            if apply:
                _delete_file(c.path)
                print(f"REMOVED: {c.path} (mtime={dt})")
            else:
                print(f"DRY-RUN: would remove {c.path} (mtime={dt})")

    if apply:
        _cleanup_empty_dirs(RAW_DIR)
        _cleanup_empty_dirs(PROCESSED_DIR)
        ok, msg = _purge_index_missing_results()
        print(msg if ok else msg)

    print("-" * 80)
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
