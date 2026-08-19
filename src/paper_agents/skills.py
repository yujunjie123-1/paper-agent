from __future__ import annotations

from pathlib import Path

from .config import PROJECT_ROOT


class SkillRegistry:
    """Progressively loads only the skills selected by an agent spec."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or PROJECT_ROOT / "skills").resolve()

    def load(self, names: list[str]) -> str:
        sections: list[str] = []
        for name in names:
            skill_file = (self.root / name / "SKILL.md").resolve()
            if self.root not in skill_file.parents:
                raise ValueError(f"Unsafe skill path: {name}")
            if not skill_file.exists():
                raise FileNotFoundError(f"Missing skill: {skill_file}")
            sections.append(skill_file.read_text(encoding="utf-8"))
        return "\n\n".join(sections)

