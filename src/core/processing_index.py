# -*- coding: utf-8 -*-
"""
ProcessingIndex — единый индекс обработок (инкрементальность по hash), без привязки к датам/папкам.

Назначение:
- Хранить реестр "что уже обработано" по ключу (file_hash, processing_type)
- Давать быстрый ответ: нужно ли обрабатывать файл повторно
- Хранить result_path (куда записали результат), processed_at и metadata

Файл индекса по умолчанию:
- data/index/processing_index.json

Формат записи:
{
  "version": 1,
  "updated_at": "...",
  "items": {
    "<processing_type>:<file_hash>": {
      "file_hash": "...",
      "processing_type": "...",
      "source_path": "data/raw/protocols/file.txt",
      "result_path": "data/processed/protocols_cleaned/file_<hash>.txt",
      "processed_at": "...",
      "metadata": {...}
    }
  }
}
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProcessingRecordKey:
    processing_type: str
    file_hash: str

    def to_string(self) -> str:
        return f"{self.processing_type}:{self.file_hash}"


@dataclass
class ProcessingRecord:
    file_hash: str
    processing_type: str
    source_path: str
    result_path: str
    processed_at: str
    metadata: Dict[str, Any]


class ProcessingIndex:
    def __init__(self, index_path: Path):
        self.index_path = index_path
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Any] = {}
        self._load()

    @classmethod
    def default(cls, project_root: Path) -> "ProcessingIndex":
        return cls(project_root / "data" / "index" / "processing_index.json")

    def _load(self) -> None:
        if not self.index_path.exists():
            self._data = {"version": 1, "updated_at": None, "items": {}}
            return
        try:
            self._data = json.loads(self.index_path.read_text(encoding="utf-8"))
            if "items" not in self._data:
                self._data["items"] = {}
        except Exception as e:
            logger.error(f"Не удалось прочитать processing index {self.index_path}: {e}")
            self._data = {"version": 1, "updated_at": None, "items": {}}

    def save(self) -> None:
        self._data["updated_at"] = datetime.now().isoformat()
        self.index_path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get(self, key: ProcessingRecordKey) -> Optional[ProcessingRecord]:
        raw = self._data.get("items", {}).get(key.to_string())
        if not raw:
            return None
        return ProcessingRecord(**raw)

    def upsert(self, record: ProcessingRecord) -> None:
        key = ProcessingRecordKey(record.processing_type, record.file_hash).to_string()
        self._data.setdefault("items", {})[key] = asdict(record)
        self.save()

    def purge_missing_results(self) -> int:
        """Удаляет записи, у которых result_path не существует."""
        items: Dict[str, Any] = self._data.get("items", {})
        to_delete = []
        for k, v in items.items():
            try:
                result_path = Path(v["result_path"])
                if not result_path.exists():
                    to_delete.append(k)
            except Exception:
                to_delete.append(k)

        for k in to_delete:
            items.pop(k, None)

        if to_delete:
            self.save()

        return len(to_delete)
