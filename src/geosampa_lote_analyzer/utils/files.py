import json
from pathlib import Path
from typing import Any


def ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, data: Any) -> Path:
    ensure_parent(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def safe_filename(value: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in value)

