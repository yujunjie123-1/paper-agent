from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def abs_path(path: str | Path, base: str | Path | None = None) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute() and base is not None:
        candidate = Path(base).expanduser() / candidate
    return candidate.resolve()


def load_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path = abs_path(path)
    text = manifest_path.read_text(encoding="utf-8")
    if manifest_path.suffix.lower() == ".json":
        payload = json.loads(text)
    else:
        payload = yaml.safe_load(text)
    if not isinstance(payload, dict):
        raise ValueError(f"Manifest must be an object: {manifest_path}")
    payload["_manifest_path"] = str(manifest_path)
    return payload


def write_manifest(path: str | Path, payload: dict[str, Any]) -> Path:
    target = abs_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.suffix.lower() == ".json":
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        target.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return target


def write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    target = abs_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target
