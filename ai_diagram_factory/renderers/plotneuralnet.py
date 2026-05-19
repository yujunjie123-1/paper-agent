from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from PIL import ImageDraw

from ..canvas import draw_arrow, draw_centered_text, load_font, new_canvas, save_png
from ..config import PLOTNEURALNET_HARNESS, PLOTNEURALNET_SOURCE
from ..io import write_json
from ..styles import KIND_COLORS, PALETTE


def render_plotneuralnet_cnn(figure: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    fig_dir = out_dir / figure["id"]
    fig_dir.mkdir(parents=True, exist_ok=True)
    source_json = fig_dir / f"{figure['id']}.plotneuralnet.json"
    tex_path = fig_dir / f"{figure['id']}.tex"
    png_path = fig_dir / f"{figure['id']}.png"

    project = {
        "schema_version": 1,
        "name": figure.get("title", figure["id"]),
        "source_root": str(PLOTNEURALNET_SOURCE),
        "items": _to_plotneuralnet_items(figure.get("layers", [])),
        "history": [],
        "future": [],
        "metadata": {"factory_kind": "plotneuralnet_cnn"},
        "created_at": "generated",
        "updated_at": "generated",
    }
    write_json(source_json, project)

    cli_result = _run_plotneuralnet_cli(source_json, tex_path)
    _render_cnn_png(figure, png_path)
    return {
        "id": figure["id"],
        "kind": "plotneuralnet_cnn",
        "png": str(png_path),
        "sources": [str(source_json), str(tex_path)],
        "backend": cli_result,
    }


def _to_plotneuralnet_items(layers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    previous_name = None
    x_offset = 0
    for index, layer in enumerate(layers):
        kind = layer.get("type", "conv")
        name = layer.get("name", f"{kind}{index}")
        if kind == "input":
            continue
        to = "(0,0,0)" if previous_name is None else f"({previous_name}-east)"
        offset = "(0,0,0)" if previous_name is None else "(1,0,0)"
        if kind in {"conv", "dense"}:
            item = {
                "type": "conv",
                "name": name,
                "s_filer": _shape_depth(layer.get("shape"), default=64),
                "n_filer": _shape_channels(layer.get("shape"), default=64),
                "offset": offset,
                "to": to,
                "height": max(10, 48 - x_offset * 3),
                "depth": max(10, 48 - x_offset * 3),
                "width": 2 if kind == "conv" else 4,
                "caption": layer.get("label", name),
            }
        elif kind == "pool":
            item = {"type": "pool", "name": name, "offset": offset, "to": to, "height": 36, "depth": 36, "width": 1}
        elif kind == "softmax":
            item = {"type": "softmax", "name": name, "offset": offset, "to": to, "s_filer": layer.get("classes", 10), "caption": layer.get("label", name)}
        else:
            item = {"type": "conv", "name": name, "offset": offset, "to": to, "caption": layer.get("label", name)}
        if previous_name is not None:
            items.append({"type": "connection", "of": previous_name, "to": name})
        items.append(item)
        previous_name = name
        x_offset += 1
    return items


def _shape_channels(shape: str | None, default: int) -> int:
    if not shape:
        return default
    parts = [part for part in str(shape).replace("×", "x").split("x") if part.strip()]
    try:
        return int(parts[-1])
    except (ValueError, IndexError):
        return default


def _shape_depth(shape: str | None, default: int) -> int:
    if not shape:
        return default
    parts = [part for part in str(shape).replace("×", "x").split("x") if part.strip()]
    try:
        return int(parts[0])
    except (ValueError, IndexError):
        return default


def _run_plotneuralnet_cli(source_json: Path, tex_path: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PLOTNEURALNET_HARNESS)
    env["PLOTNEURALNET_SOURCE_ROOT"] = str(PLOTNEURALNET_SOURCE)
    env["CLI_ANYTHING_PLOTNEURALNET_SESSION_DIR"] = str(source_json.parent / ".session")
    cmd = [
        "cli-anything-plotneuralnet",
        "--json",
        "--project",
        str(source_json),
        "render",
        "tex",
        "-o",
        str(tex_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=60)
    except Exception as exc:
        tex_path.write_text("% PlotNeuralNet CLI unavailable\n", encoding="utf-8")
        return {"status": "fallback", "reason": str(exc)}
    if result.returncode != 0:
        tex_path.write_text("% PlotNeuralNet CLI failed\n" + result.stderr + result.stdout, encoding="utf-8")
        return {"status": "fallback", "returncode": result.returncode, "stderr": result.stderr, "stdout": result.stdout}
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"stdout": result.stdout}
    return {"status": "plotneuralnet", "payload": payload}


def _render_cnn_png(figure: dict[str, Any], png_path: Path) -> None:
    layers = figure.get("layers", [])
    width = max(1200, 180 + len(layers) * 145)
    height = 520
    img, draw = new_canvas(width, height, "#FFFFFF")
    title_font = load_font(30, bold=True)
    label_font = load_font(20)
    small_font = load_font(16)
    draw.text((50, 30), figure.get("title", figure["id"]), font=title_font, fill=PALETTE["ink"])
    x = 80
    y = 200
    prev = None
    for index, layer in enumerate(layers):
        kind = layer.get("type", "conv")
        fill, edge = KIND_COLORS.get(kind, KIND_COLORS["conv"])
        h = 190 if kind in {"input", "conv"} else 145
        w = 44 if kind in {"pool", "softmax"} else 70
        depth = 28
        top = y + (190 - h) / 2
        _draw_iso_block(draw, x, top, w, h, depth, fill, edge)
        draw_centered_text(draw, (x - 8, top + h + 18, x + w + 42, top + h + 74), layer.get("name", kind), small_font, max_chars=12)
        if layer.get("shape"):
            draw_centered_text(draw, (x - 20, top - 44, x + w + 52, top - 10), str(layer["shape"]), small_font, fill=PALETTE["muted"], max_chars=16)
        if prev:
            draw_arrow(draw, (prev[0] + prev[1] + 40, y + 95), (x - 12, y + 95), fill="#4B5563", width=3)
        prev = (x, w)
        x += 135
    save_png(img, png_path)


def _draw_iso_block(draw: ImageDraw.ImageDraw, x: float, y: float, w: float, h: float, d: float, fill: str, edge: str) -> None:
    front = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    top = [(x, y), (x + d, y - d), (x + w + d, y - d), (x + w, y)]
    side = [(x + w, y), (x + w + d, y - d), (x + w + d, y + h - d), (x + w, y + h)]
    draw.polygon(top, fill=_lighten(fill, 1.08), outline=edge)
    draw.polygon(side, fill=_lighten(fill, 0.9), outline=edge)
    draw.polygon(front, fill=fill, outline=edge)
    for i in range(1, 5):
        xx = x + i * w / 5
        draw.line([(xx, y), (xx, y + h)], fill=edge, width=1)


def _lighten(hex_color: str, factor: float) -> str:
    hex_color = hex_color.lstrip("#")
    values = [int(hex_color[i : i + 2], 16) for i in (0, 2, 4)]
    values = [max(0, min(255, int(value * factor))) for value in values]
    return "#" + "".join(f"{value:02x}" for value in values)
