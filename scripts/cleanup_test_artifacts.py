#!/usr/bin/env python3
"""
Cleanup runtime/test artifacts that should not pollute the git worktree.

Default mode is dry-run.

Targets:
- restore tracked generated index files to HEAD
- remove untracked run artifacts and caches produced during local tests

This script intentionally avoids deleting tracked historical fixtures/samples.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RESTORE_EXACT = {
    "data/memory/json/.index.json",
}

UNTRACKED_PREFIXES = (
    "reports/runs/",
    "data/index/",
    "data/processed/",
    "data/jira/snapshots/",
)

UNTRACKED_FILE_PREFIXES = (
    "reports/weekly/weekly_report_",
    "data/memory/json/weekly_summary_data_",
)

DIRECT_PATH_TARGETS = (
    "reports/runs",
    "data/index",
    "data/processed",
    "data/jira/snapshots",
)

GLOB_TARGETS = (
    "reports/weekly/weekly_report_*.json",
    "data/memory/json/weekly_summary_data_*.json",
)


@dataclass(frozen=True)
class CleanupAction:
    kind: str
    path: str


def _git_status_lines() -> List[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def _is_tracked(path: str) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", path],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _parse_path(raw_line: str) -> tuple[str, str]:
    status = raw_line[:2]
    path = raw_line[3:]
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return status, path


def _matches_untracked_target(path: str) -> bool:
    if any(path.startswith(prefix) for prefix in UNTRACKED_PREFIXES):
        return True
    if any(path.startswith(prefix) and path.endswith(".json") for prefix in UNTRACKED_FILE_PREFIXES):
        return True
    return False


def collect_actions() -> List[CleanupAction]:
    actions: List[CleanupAction] = []
    for line in _git_status_lines():
        status, path = _parse_path(line)

        if path in RESTORE_EXACT and "?" not in status:
            actions.append(CleanupAction(kind="restore", path=path))
            continue

        if status == "??" and _matches_untracked_target(path):
            actions.append(CleanupAction(kind="remove", path=path))

    for rel_path in DIRECT_PATH_TARGETS:
        full_path = PROJECT_ROOT / rel_path
        if full_path.exists():
            actions.append(CleanupAction(kind="remove", path=rel_path))

    for pattern in GLOB_TARGETS:
        for full_path in PROJECT_ROOT.glob(pattern):
            rel_path = str(full_path.relative_to(PROJECT_ROOT))
            if full_path.exists() and not _is_tracked(rel_path):
                actions.append(
                    CleanupAction(
                        kind="remove",
                        path=rel_path,
                    )
                )

    deduped: List[CleanupAction] = []
    seen = set()
    for action in actions:
        key = (action.kind, action.path)
        if key not in seen:
            seen.add(key)
            deduped.append(action)
    return deduped


def _remove_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def apply_actions(actions: Iterable[CleanupAction]) -> None:
    restore_paths = [action.path for action in actions if action.kind == "restore"]
    remove_paths = [action.path for action in actions if action.kind == "remove"]

    for rel_path in restore_paths:
        result = subprocess.run(
            ["git", "show", f"HEAD:{rel_path}"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        target_path = PROJECT_ROOT / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(result.stdout, encoding="utf-8")

    for rel_path in remove_paths:
        _remove_path(PROJECT_ROOT / rel_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Cleanup generated test/runtime artifacts.")
    parser.add_argument("--apply", action="store_true", help="Apply cleanup actions.")
    args = parser.parse_args()

    actions = collect_actions()

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Mode: {mode}")
    print("-" * 80)

    if not actions:
        print("No generated test artifacts found.")
        return 0

    for action in actions:
        print(f"{action.kind.upper():7} {action.path}")

    if args.apply:
        apply_actions(actions)
        print("-" * 80)
        print("Cleanup completed.")
    else:
        print("-" * 80)
        print("Dry-run only. Re-run with --apply to perform cleanup.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
