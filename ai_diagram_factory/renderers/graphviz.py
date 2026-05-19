from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

from ..canvas import draw_arrow, draw_centered_text, load_font, new_canvas, save_png
from ..styles import PALETTE


def render_graphviz_graph(figure: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    fig_dir = out_dir / figure["id"]
    fig_dir.mkdir(parents=True, exist_ok=True)
    dot_path = fig_dir / f"{figure['id']}.dot"
    png_path = fig_dir / f"{figure['id']}.png"
    dot_path.write_text(_build_dot(figure), encoding="utf-8")
    backend = _try_dot(dot_path, png_path)
    if backend["status"] != "graphviz":
        _render_graph_png(figure, png_path)
    return {"id": figure["id"], "kind": "graphviz_graph", "png": str(png_path), "sources": [str(dot_path)], "backend": backend}


def _build_dot(figure: dict[str, Any]) -> str:
    lines = ["digraph G {", "  graph [rankdir=TB, splines=true, overlap=false];", "  node [shape=circle, style=filled, fillcolor=\"#FFF7CC\", color=\"#A68A2D\", fontname=\"Microsoft YaHei\"];"]
    for node in figure.get("nodes", []):
        lines.append(f'  "{node["id"]}" [label="{node.get("label", node["id"])}"];')
    for edge in figure.get("edges", []):
        if len(edge) >= 2:
            lines.append(f'  "{edge[0]}" -> "{edge[1]}";')
    ranks: dict[Any, list[str]] = {}
    for node in figure.get("nodes", []):
        ranks.setdefault(node.get("rank", 0), []).append(node["id"])
    for rank_nodes in ranks.values():
        lines.append("  { rank=same; " + "; ".join(f'"{node_id}"' for node_id in rank_nodes) + "; }")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _try_dot(dot_path: Path, png_path: Path) -> dict[str, Any]:
    dot = shutil.which("dot") or _known_dot_path()
    if not dot:
        return {"status": "fallback", "reason": "dot executable not found"}
    result = subprocess.run([dot, "-Tpng", str(dot_path), "-o", str(png_path)], capture_output=True, text=True, timeout=60)
    if result.returncode == 0 and png_path.exists():
        return {"status": "graphviz", "stdout": result.stdout}
    return {"status": "fallback", "returncode": result.returncode, "stderr": result.stderr}


def _known_dot_path() -> str | None:
    candidates = [
        Path("C:/Program Files/Graphviz/bin/dot.exe"),
        Path("C:/Program Files (x86)/Graphviz/bin/dot.exe"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return None


def _render_graph_png(figure: dict[str, Any], png_path: Path) -> None:
    nodes = figure.get("nodes", [])
    edges = figure.get("edges", [])
    width, height = 900, 680
    img, draw = new_canvas(width, height, "#FFFFFF")
    title_font = load_font(30, bold=True)
    font = load_font(20)
    draw.text((50, 30), figure.get("title", figure["id"]), font=title_font, fill=PALETTE["ink"])
    ranks: dict[int, list[dict[str, Any]]] = {}
    for node in nodes:
        ranks.setdefault(int(node.get("rank", 0)), []).append(node)
    positions = {}
    rank_keys = sorted(ranks)
    for row_index, rank in enumerate(rank_keys):
        row_nodes = ranks[rank]
        y = 140 + row_index * (420 / max(1, len(rank_keys) - 1 if len(rank_keys) > 1 else 1))
        spacing = width / (len(row_nodes) + 1)
        for col, node in enumerate(row_nodes, start=1):
            x = spacing * col
            positions[str(node["id"])] = (x, y)
    for edge in edges:
        if len(edge) >= 2 and str(edge[0]) in positions and str(edge[1]) in positions:
            a, b = positions[str(edge[0])], positions[str(edge[1])]
            angle = math.atan2(b[1] - a[1], b[0] - a[0])
            start = (a[0] + 32 * math.cos(angle), a[1] + 32 * math.sin(angle))
            end = (b[0] - 32 * math.cos(angle), b[1] - 32 * math.sin(angle))
            draw_arrow(draw, start, end, fill="#8B8B6B", width=2)
    for node in nodes:
        x, y = positions[str(node["id"])]
        box = (x - 34, y - 34, x + 34, y + 34)
        draw.ellipse(box, fill="#FFF7CC", outline="#A68A2D", width=3)
        draw_centered_text(draw, box, node.get("label", node["id"]), font, max_chars=6)
    save_png(img, png_path)
