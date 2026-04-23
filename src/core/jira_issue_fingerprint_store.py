# -*- coding: utf-8 -*-

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class JiraIssueFingerprintRecord:
    issue_key: str
    fingerprint: str
    last_seen_run_id: str
    last_analyzed_run_id: str
    task_evidence_path: str
    updated_at: str
    assignee: str
    status: str


class JiraIssueFingerprintStore:
    """File-based issue fingerprint cache for incremental Jira processing."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.index_dir = self.project_root / "data" / "index"
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.index_dir / "jira_issue_fingerprints.json"

    def load(self) -> Dict[str, Dict[str, Any]]:
        if not self.index_path.exists():
            return {}
        return json.loads(self.index_path.read_text(encoding="utf-8"))

    def save(self, records: Dict[str, Dict[str, Any]]) -> None:
        payload = {
            "updated_at": datetime.now().isoformat(),
            "issues": records,
        }
        self.index_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_issues(self) -> Dict[str, Dict[str, Any]]:
        payload = self.load()
        if "issues" in payload:
            return payload["issues"]
        return payload if isinstance(payload, dict) else {}

    def compute_fingerprint(self, task: Dict[str, Any]) -> str:
        normalized = {
            "key": task.get("key"),
            "summary": task.get("summary"),
            "status": task.get("status"),
            "assignee": task.get("assignee"),
            "priority": task.get("priority"),
            "updated": task.get("updated"),
            "project": task.get("project"),
            "description": task.get("description"),
            "comments": task.get("comments"),
            "commits_count": task.get("commits_count"),
            "pull_requests_count": task.get("pull_requests_count"),
        }
        body = json.dumps(normalized, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    def diff_tasks(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        existing = self.load_issues()
        current: Dict[str, Dict[str, Any]] = {}
        unchanged: List[str] = []
        changed: List[str] = []
        added: List[str] = []

        for task in tasks:
            issue_key = str(task.get("key") or "").strip()
            if not issue_key:
                continue
            fingerprint = self.compute_fingerprint(task)
            current[issue_key] = {
                "fingerprint": fingerprint,
                "assignee": task.get("assignee", ""),
                "status": task.get("status", ""),
            }
            previous = existing.get(issue_key)
            if not previous:
                added.append(issue_key)
            elif previous.get("fingerprint") == fingerprint:
                unchanged.append(issue_key)
            else:
                changed.append(issue_key)

        removed = sorted(set(existing.keys()) - set(current.keys()))

        return {
            "current": current,
            "added": sorted(added),
            "changed": sorted(changed),
            "unchanged": sorted(unchanged),
            "removed": removed,
            "previous": existing,
        }

    def update_from_tasks(
        self,
        tasks: List[Dict[str, Any]],
        *,
        run_id: str,
        task_evidence_path: str,
        analyzed_keys: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        existing = self.load_issues()
        analyzed_keys = set(analyzed_keys or [])

        for task in tasks:
            issue_key = str(task.get("key") or "").strip()
            if not issue_key:
                continue
            fingerprint = self.compute_fingerprint(task)
            previous = existing.get(issue_key, {})
            existing[issue_key] = JiraIssueFingerprintRecord(
                issue_key=issue_key,
                fingerprint=fingerprint,
                last_seen_run_id=run_id,
                last_analyzed_run_id=run_id if issue_key in analyzed_keys else previous.get("last_analyzed_run_id", ""),
                task_evidence_path=task_evidence_path,
                updated_at=datetime.now().isoformat(),
                assignee=str(task.get("assignee") or ""),
                status=str(task.get("status") or ""),
            ).__dict__

        self.save(existing)
        return existing
