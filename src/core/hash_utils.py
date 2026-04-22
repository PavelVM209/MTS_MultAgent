# -*- coding: utf-8 -*-
"""
Минимальные утилиты для хэширования файлов и контента.

Нужны для инкрементальной обработки:
- определять изменился ли файл по содержимому (а не по имени/дате)
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def md5_text(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()
