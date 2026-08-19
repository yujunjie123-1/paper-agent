from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from .models import AgentSpec


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected YAML object in {path}")
    return value


def load_agent_specs(path: Path | None = None) -> dict[str, AgentSpec]:
    config = _load_yaml(path or PROJECT_ROOT / "config" / "agents.yaml")
    specs = [AgentSpec.model_validate(item) for item in config["agents"]]
    by_id = {spec.id: spec for spec in specs}
    if len(by_id) != len(specs):
        raise ValueError("Duplicate agent id in config/agents.yaml")
    return by_id


def load_workflow(path: Path | None = None) -> dict[str, Any]:
    return _load_yaml(path or PROJECT_ROOT / "config" / "workflow.yaml")


class Settings:
    def __init__(self) -> None:
        self.provider = os.getenv("PAPER_AGENTS_PROVIDER", "mock").lower()
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-5.6-terra")
        self.db_path = Path(
            os.getenv("PAPER_AGENTS_DB", str(PROJECT_ROOT / "data" / "paper_agents.db"))
        )
        self.auto_approve = os.getenv("PAPER_AGENTS_AUTO_APPROVE", "false").lower() == "true"
        self.max_revisions = int(os.getenv("PAPER_AGENTS_MAX_REVISIONS", "2"))
        self.review_threshold = float(os.getenv("PAPER_AGENTS_REVIEW_THRESHOLD", "0.78"))

