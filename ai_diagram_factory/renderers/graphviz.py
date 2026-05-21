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
    svg_path = fig_dir / f"{figure['id']}.svg"
    dot_path.write_text(_build_dot(figure), encoding="utf-8")
    backend = _try_dot(dot_path, png_path, svg_path)
    sources = [str(dot_path)]
    result: dict[str, Any] = {"id": figure["id"], "kind": "graphviz_graph", "png": str(png_path), "sources": sources, "backend": backend}
    if backend["status"] == "graphviz" and svg_path.is_file():
        result["svg"] = str(svg_path)
        sources.append(str(svg_path))
    if backend["status"] != "graphviz":
        _render_graph_png(figure, png_path)
    return result


def _build_dot(figure: dict[str, Any]) -> str:
    rankdir = figure.get("rankdir", "TB")
    splines = figure.get("splines", "true")
    overlap = figure.get("overlap", "false")
    graph_attr_overrides = dict(figure.get("graph_attrs") or {})
    node_attrs = figure.get(
        "node_attrs",
        {"shape": "circle", "style": "filled", "fillcolor": "#FFF7CC", "color": "#A68A2D", "fontname": "Microsoft YaHei"},
    )
    edge_attrs = figure.get("edge_attrs", {})
    box = figure.get("box_xyxy")
    graph_attrs: dict[str, Any] = {
        "rankdir": rankdir,
        "splines": splines,
        "overlap": overlap,
        "outputorder": figure.get("outputorder", "edgesfirst"),
        "margin": figure.get("margin", "0"),
        "nodesep": figure.get("nodesep", "0.12"),
        "ranksep": figure.get("ranksep", "0.35"),
    }
    if box and len(box) == 4:
        width_in = max(0.5, (float(box[2]) - float(box[0])) / 72.0)
        height_in = max(0.5, (float(box[3]) - float(box[1])) / 72.0)
        graph_attrs["size"] = f"{width_in:.2f},{height_in:.2f}!"
        graph_attrs["dpi"] = "72"
        graph_attrs["bgcolor"] = "transparent"
    graph_attrs.update(graph_attr_overrides)
    lines = ["digraph G {", f"  graph [{_attr_string(graph_attrs)}];", f"  node [{_attr_string(node_attrs)}];"]
    if edge_attrs:
        lines.append(f"  edge [{_attr_string(edge_attrs)}];")
    for node in figure.get("nodes", []):
        attrs = dict(node.get("attrs") or {})
        if "label" in node:
            attrs["label"] = node["label"]
        attr_string = _attr_string(attrs) if attrs else ""
        if attr_string:
            lines.append(f'  "{node["id"]}" [{attr_string}];')
        else:
            lines.append(f'  "{node["id"]}";')
    for edge in figure.get("edges", []):
        if len(edge) >= 2:
            if isinstance(edge, dict):
                source = edge.get("from") or edge.get("source")
                target = edge.get("to") or edge.get("target")
                attrs = dict(edge.get("attrs") or {})
            else:
                source = edge[0]
                target = edge[1]
                attrs = dict(edge[2]) if len(edge) > 2 and isinstance(edge[2], dict) else {}
            if source is None or target is None:
                continue
            attr_string = f" [{_attr_string(attrs)}]" if attrs else ""
            lines.append(f'  "{source}" -> "{target}"{attr_string};')
    ranks: dict[Any, list[str]] = {}
    for node in figure.get("nodes", []):
        ranks.setdefault(node.get("rank", 0), []).append(node["id"])
    for rank_nodes in ranks.values():
        lines.append("  { rank=same; " + "; ".join(f'"{node_id}"' for node_id in rank_nodes) + "; }")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _attr_string(attrs: dict[str, Any]) -> str:
    return ", ".join(f'{key}="{_escape_attr(value)}"' for key, value in attrs.items())


def _escape_attr(value: Any) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def _try_dot(dot_path: Path, png_path: Path, svg_path: Path | None = None) -> dict[str, Any]:
    dot = shutil.which("dot") or _known_dot_path()
    if not dot:
        return {"status": "fallback", "reason": "dot executable not found"}
    result = subprocess.run([dot, "-Tpng", str(dot_path), "-o", str(png_path)], capture_output=True, text=True, timeout=60)
    if result.returncode != 0 or not png_path.exists():
        return {"status": "fallback", "returncode": result.returncode, "stderr": result.stderr}
    if svg_path is not None:
        svg_result = subprocess.run([dot, "-Tsvg", str(dot_path), "-o", str(svg_path)], capture_output=True, text=True, timeout=60)
        if svg_result.returncode != 0:
            return {"status": "graphviz", "stdout": result.stdout, "svg_warning": svg_result.stderr}
    return {"status": "graphviz", "stdout": result.stdout}


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
