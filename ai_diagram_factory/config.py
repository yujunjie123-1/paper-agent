from __future__ import annotations

import os
from pathlib import Path


def _path_from_env(env_name: str, default: Path) -> Path:
    value = os.environ.get(env_name)
    if value:
        return Path(value).expanduser().resolve()
    return default.expanduser().resolve()


ROOT = _path_from_env("AI_DIAGRAM_FACTORY_ROOT", Path(__file__).resolve().parents[1])
DEFAULT_OUTPUT_DIR = _path_from_env("AI_DIAGRAM_FACTORY_OUTPUT_DIR", ROOT / "outputs")
DRAWIO_HARNESS = _path_from_env(
    "AI_DIAGRAM_FACTORY_DRAWIO_HARNESS",
    Path.home() / "Desktop" / "drawio" / "agent-harness",
)
PLOTNEURALNET_SOURCE = _path_from_env(
    "PLOTNEURALNET_SOURCE_ROOT",
    ROOT.parent / "PlotNeuralNet",
)
PLOTNEURALNET_HARNESS = _path_from_env(
    "AI_DIAGRAM_FACTORY_PLOTNEURALNET_HARNESS",
    PLOTNEURALNET_SOURCE / "agent-harness",
)
LATEX_TEMP_DIR = _path_from_env(
    "AI_DIAGRAM_FACTORY_LATEX_TEMP_DIR",
    Path.home() / "Documents" / "ai_diagram_factory_latex_tmp",
)
