# -*- coding: utf-8 -*-
"""
RunFileManager — менеджер артефактов запусков в структуре:

reports/
  runs/{run_id}/
    meeting-analysis/
      stage1/
      stage2/
      final/
    employee_progression/
    inputs/
    _metadata.json
  latest/  -> ссылки/копии на последний run (минимально: текстовые отчёты + json)

Принципы:
- Никаких папок по дням
- run_id задаётся снаружи (обычно YYYYMMDD_HHMMSS)
- LLM входы (briefs) храним как TXT в inputs/
- Финальные отчёты для Confluence — TXT/MD
- Структурные результаты и метрики — JSON
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunPaths:
    run_dir: Path
    meeting_dir: Path
    meeting_stage1_dir: Path
    meeting_stage2_dir: Path
    meeting_final_dir: Path
    employee_progression_dir: Path
    inputs_dir: Path
    metadata_path: Path


class RunFileManager:
    def __init__(self, project_root: Path, reports_root: Optional[Path] = None):
        self.project_root = project_root
        self.reports_root = reports_root or (project_root / "reports")
        self.runs_root = self.reports_root / "runs"
        self.latest_root = self.reports_root / "latest"
        self.runs_root.mkdir(parents=True, exist_ok=True)
        self.latest_root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def generate_run_id(now: Optional[datetime] = None) -> str:
        dt = now or datetime.now()
        return dt.strftime("%Y%m%d_%H%M%S")

    def init_run(self, run_id: str) -> RunPaths:
        run_dir = self.runs_root / run_id
        meeting_dir = run_dir / "meeting-analysis"
        meeting_stage1_dir = meeting_dir / "stage1"
        meeting_stage2_dir = meeting_dir / "stage2"
        meeting_final_dir = meeting_dir / "final"
        employee_progression_dir = run_dir / "employee_progression"
        inputs_dir = run_dir / "inputs"
        metadata_path = run_dir / "_metadata.json"

        for d in (
            meeting_stage1_dir,
            meeting_stage2_dir,
            meeting_final_dir,
            employee_progression_dir,
            inputs_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)

        if not metadata_path.exists():
            metadata_path.write_text(
                json.dumps({"run_id": run_id, "created_at": datetime.now().isoformat()}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        return RunPaths(
            run_dir=run_dir,
            meeting_dir=meeting_dir,
            meeting_stage1_dir=meeting_stage1_dir,
            meeting_stage2_dir=meeting_stage2_dir,
            meeting_final_dir=meeting_final_dir,
            employee_progression_dir=employee_progression_dir,
            inputs_dir=inputs_dir,
            metadata_path=metadata_path,
        )

    def save_text(self, path: Path, content: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def save_json(self, path: Path, data: Dict[str, Any]) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def set_latest(self, run_id: str) -> None:
        """
        Обновляет reports/latest на указанный run_id.

        Реализация: создаём/пересоздаём файл latest/run_id.txt.
        Ссылки на конкретные артефакты будем добавлять по мере миграции остальных частей.
        """
        (self.latest_root / "run_id.txt").write_text(run_id, encoding="utf-8")

    def copy_to_latest(self, src: Path, rel_dst: Path) -> Path:
        """
        Копирует файл в reports/latest/<rel_dst>.
        Используем копию вместо symlink, чтобы не зависеть от особенностей FS/переносимости.
        """
        dst = self.latest_root / rel_dst
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return dst
