# -*- coding: utf-8 -*-

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class JiraSnapshotMeta:
    run_id: str
    generated_at: str
    jql: str
    project_key: str
    analysis_depth_days: int


class JiraSnapshotStore:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.snapshots_dir = self.project_root / "data" / "jira" / "snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def snapshot_path(self, run_id: str) -> Path:
        return self.snapshots_dir / f"{run_id}.json"

    def save_snapshot(
        self,
        run_id: str,
        tasks: List[Dict[str, Any]],
        *,
        jql: str,
        project_key: str,
        analysis_depth_days: int,
    ) -> Path:
        meta = JiraSnapshotMeta(
            run_id=run_id,
            generated_at=datetime.now().isoformat(),
            jql=jql,
            project_key=project_key,
            analysis_depth_days=analysis_depth_days,
        )
        payload = {
            "meta": meta.__dict__,
            "tasks": tasks,
        }

        path = self.snapshot_path(run_id)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def list_snapshots(self) -> List[Tuple[str, Path]]:
        items: List[Tuple[str, Path]] = []
        for path in sorted(self.snapshots_dir.glob("*.json")):
            items.append((path.stem, path))
        return items

    def find_previous_snapshot_path(self, run_id: str) -> Optional[Path]:
        """Find the newest snapshot whose run_id is strictly older than the current one."""
        snapshots = [snapshot_run_id for snapshot_run_id, _ in self.list_snapshots()]
        previous = [snapshot_run_id for snapshot_run_id in snapshots if snapshot_run_id < run_id]
        if not previous:
            return None
        return self.snapshot_path(sorted(previous)[-1])

    def load_snapshot(self, path: Path) -> Dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))
