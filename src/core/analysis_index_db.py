# -*- coding: utf-8 -*-

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


class AnalysisIndexDB:
    """SQLite index over JSON artifacts for fast operational lookups."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.index_dir = self.project_root / "data" / "index"
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.index_dir / "analysis_index.db"
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    analysis_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    artifact_path TEXT,
                    metadata_json TEXT
                );

                CREATE TABLE IF NOT EXISTS jira_issue_versions (
                    issue_key TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    assignee TEXT,
                    status TEXT,
                    artifact_path TEXT,
                    payload_json TEXT,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (issue_key, fingerprint)
                );

                CREATE TABLE IF NOT EXISTS task_evidence_index (
                    run_id TEXT NOT NULL,
                    employee_name TEXT NOT NULL,
                    artifact_path TEXT NOT NULL,
                    source_issue_keys TEXT,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (run_id, employee_name)
                );

                CREATE TABLE IF NOT EXISTS meeting_employee_evidence_index (
                    run_id TEXT NOT NULL,
                    employee_name TEXT NOT NULL,
                    artifact_path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (run_id, employee_name)
                );
                """
            )

    def record_run(self, run_id: str, analysis_type: str, artifact_path: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO runs (run_id, analysis_type, created_at, artifact_path, metadata_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, analysis_type, datetime.now().isoformat(), artifact_path, json.dumps(metadata or {}, ensure_ascii=False)),
            )

    def record_jira_issue_versions(
        self,
        run_id: str,
        tasks: Iterable[Dict[str, Any]],
        *,
        fingerprint_fn,
        artifact_path: str,
    ) -> None:
        created_at = datetime.now().isoformat()
        with self._connect() as conn:
            for task in tasks:
                issue_key = str(task.get("key") or "").strip()
                if not issue_key:
                    continue
                conn.execute(
                    """
                    INSERT OR REPLACE INTO jira_issue_versions
                    (issue_key, fingerprint, run_id, assignee, status, artifact_path, payload_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        issue_key,
                        fingerprint_fn(task),
                        run_id,
                        str(task.get("assignee") or ""),
                        str(task.get("status") or ""),
                        artifact_path,
                        json.dumps(task, ensure_ascii=False, default=str),
                        created_at,
                    ),
                )

    def record_task_evidence(self, run_id: str, employees: Dict[str, Dict[str, Any]], artifact_dir: str) -> None:
        created_at = datetime.now().isoformat()
        with self._connect() as conn:
            for employee_name, evidence in employees.items():
                issue_keys = [item.get("issue") for item in evidence.get("jira_evidence", []) if item.get("issue")]
                conn.execute(
                    """
                    INSERT OR REPLACE INTO task_evidence_index
                    (run_id, employee_name, artifact_path, source_issue_keys, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        employee_name,
                        str(Path(artifact_dir) / f"{employee_name}.json"),
                        json.dumps(issue_keys, ensure_ascii=False),
                        created_at,
                    ),
                )

    def record_meeting_employee_evidence(self, run_id: str, employees: Iterable[str], artifact_dir: str) -> None:
        created_at = datetime.now().isoformat()
        with self._connect() as conn:
            for employee_name in employees:
                safe_name = "".join(ch for ch in employee_name if ch.isalnum() or ch in (" ", "_", "-")).strip()
                safe_name = "_".join(safe_name.split())
                conn.execute(
                    """
                    INSERT OR REPLACE INTO meeting_employee_evidence_index
                    (run_id, employee_name, artifact_path, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        employee_name,
                        str(Path(artifact_dir) / f"{safe_name}.json"),
                        created_at,
                    ),
                )

    def get_runs_in_period(self, analysis_type: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT run_id, analysis_type, created_at, artifact_path, metadata_json
                FROM runs
                WHERE analysis_type = ?
                  AND substr(created_at, 1, 10) >= ?
                  AND substr(created_at, 1, 10) <= ?
                ORDER BY created_at ASC
                """,
                (analysis_type, start_date.date().isoformat(), end_date.date().isoformat()),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_task_evidence_rows(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT tei.run_id, tei.employee_name, tei.artifact_path, tei.source_issue_keys, tei.created_at
                FROM task_evidence_index tei
                JOIN runs r ON r.run_id = tei.run_id
                WHERE r.analysis_type = 'task_analysis'
                  AND substr(r.created_at, 1, 10) >= ?
                  AND substr(r.created_at, 1, 10) <= ?
                ORDER BY tei.created_at ASC
                """,
                (start_date.date().isoformat(), end_date.date().isoformat()),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_meeting_employee_evidence_rows(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT meei.run_id, meei.employee_name, meei.artifact_path, meei.created_at
                FROM meeting_employee_evidence_index meei
                JOIN runs r ON r.run_id = meei.run_id
                WHERE r.analysis_type = 'meeting_analysis'
                  AND substr(r.created_at, 1, 10) >= ?
                  AND substr(r.created_at, 1, 10) <= ?
                ORDER BY meei.created_at ASC
                """,
                (start_date.date().isoformat(), end_date.date().isoformat()),
            ).fetchall()
        return [dict(row) for row in rows]
