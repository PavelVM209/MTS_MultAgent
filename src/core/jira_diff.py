# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class JiraIssueKey:
    key: str


def _task_identity(task: Dict[str, Any]) -> Optional[str]:
    key = task.get("key")
    return str(key) if key else None


def _task_fingerprint(task: Dict[str, Any]) -> Tuple[Any, ...]:
    """Minimal fingerprint for detecting changes between snapshots."""
    return (
        task.get("status"),
        task.get("assignee"),
        task.get("priority"),
        task.get("summary"),
        task.get("updated"),
    )


def diff_jira_snapshots(
    prev_tasks: List[Dict[str, Any]],
    curr_tasks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    prev_by_key: Dict[str, Dict[str, Any]] = {}
    for task in prev_tasks:
        key = _task_identity(task)
        if key:
            prev_by_key[key] = task

    curr_by_key: Dict[str, Dict[str, Any]] = {}
    for task in curr_tasks:
        key = _task_identity(task)
        if key:
            curr_by_key[key] = task

    added_keys = sorted(set(curr_by_key.keys()) - set(prev_by_key.keys()))
    removed_keys = sorted(set(prev_by_key.keys()) - set(curr_by_key.keys()))

    changed: List[Dict[str, Any]] = []
    for key in sorted(set(curr_by_key.keys()) & set(prev_by_key.keys())):
        prev_fp = _task_fingerprint(prev_by_key[key])
        curr_fp = _task_fingerprint(curr_by_key[key])
        if prev_fp != curr_fp:
            changed.append(
                {
                    "key": key,
                    "prev": {
                        "status": prev_by_key[key].get("status"),
                        "assignee": prev_by_key[key].get("assignee"),
                        "priority": prev_by_key[key].get("priority"),
                        "updated": prev_by_key[key].get("updated"),
                    },
                    "curr": {
                        "status": curr_by_key[key].get("status"),
                        "assignee": curr_by_key[key].get("assignee"),
                        "priority": curr_by_key[key].get("priority"),
                        "updated": curr_by_key[key].get("updated"),
                    },
                }
            )

    return {
        "added": [curr_by_key[key] for key in added_keys],
        "removed": [prev_by_key[key] for key in removed_keys],
        "changed": changed,
        "stats": {
            "added": len(added_keys),
            "removed": len(removed_keys),
            "changed": len(changed),
            "prev_total": len(prev_by_key),
            "curr_total": len(curr_by_key),
        },
    }
