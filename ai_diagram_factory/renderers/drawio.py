from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from ..canvas import draw_arrow, draw_centered_text, draw_round_rect, load_font, new_canvas, save_png
from ..config import DRAWIO_HARNESS
from ..styles import PALETTE


def render_drawio_flow(figure: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    nodes = figure.get("nodes", [])
    positioned = _flow_positions(nodes)
    return _render_drawio_common(figure, out_dir, positioned, figure.get("edges", []), mode="flow")


def render_drawio_architecture(figure: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges = list(figure.get("edges", []))
    lanes = figure.get("lanes", [])
    for lane_index, lane in enumerate(lanes):
        for node_index, label in enumerate(lane.get("nodes", [])):
            nodes.append(
                {
                    "id": str(label),
                    "label": str(label),
                    "lane": lane.get("name", f"Lane {lane_index + 1}"),
                    "x": 110 + node_index * 240,
                    "y": 140 + lane_index * 170,
                    "fill": ["#D9F2E6", "#DCEBFF", "#FFE0EA", "#F8EDC0"][lane_index % 4],
                }
            )
    if not edges:
        for lane in lanes:
            lane_nodes = [str(node) for node in lane.get("nodes", [])]
            edges.extend([[lane_nodes[i], lane_nodes[i + 1]] for i in range(len(lane_nodes) - 1)])
    return _render_drawio_common(figure, out_dir, nodes, edges, mode="architecture")


def _render_drawio_common(
    figure: dict[str, Any],
    out_dir: Path,
    nodes: list[dict[str, Any]],
    edges: list[list[str]],
    mode: str,
) -> dict[str, Any]:
    fig_dir = out_dir / figure["id"]
    fig_dir.mkdir(parents=True, exist_ok=True)
    drawio_path = fig_dir / f"{figure['id']}.drawio"
    png_path = fig_dir / f"{figure['id']}.png"
    _write_drawio_source(drawio_path, figure.get("title", figure["id"]), nodes, edges)
    backend = _try_drawio_export(drawio_path, png_path)
    if backend["status"] != "drawio":
        _render_drawio_preview(figure, nodes, edges, png_path, mode=mode)
    return {"id": figure["id"], "kind": f"drawio_{mode}", "png": str(png_path), "sources": [str(drawio_path)], "backend": backend}


def _flow_positions(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    positioned = []
    for index, node in enumerate(nodes):
        positioned.append(
            {
                **node,
                "x": 120 + (index % 3) * 270,
                "y": 160 + (index // 3) * 170,
                "fill": ["#DCEBFF", "#D9F2E6", "#FFE0EA"][index % 3],
            }
        )
    return positioned


def _write_drawio_source(path: Path, title: str, nodes: list[dict[str, Any]], edges: list[list[str]]) -> None:
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    id_map: dict[str, str] = {}
    for idx, node in enumerate(nodes, start=2):
        cell_id = f"n{idx}"
        id_map[str(node.get("id", node.get("label", idx)))] = cell_id
        label = escape(str(node.get("label", node.get("id", ""))))
        style = "rounded=1;whiteSpace=wrap;html=1;fillColor={};strokeColor=#5B6B7A;".format(node.get("fill", "#DCEBFF"))
        cells.append(
            f'<mxCell id="{cell_id}" value="{label}" style="{style}" vertex="1" parent="1">'
            f'<mxGeometry x="{node["x"]}" y="{node["y"]}" width="170" height="70" as="geometry"/>'
            "</mxCell>"
        )
    edge_start = len(nodes) + 10
    for idx, edge in enumerate(edges, start=edge_start):
        if len(edge) < 2:
            continue
        source, target = str(edge[0]), str(edge[1])
        if source not in id_map or target not in id_map:
            continue
        label = escape(str(edge[2])) if len(edge) > 2 else ""
        cells.append(
            f'<mxCell id="e{idx}" value="{label}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" '
            f'edge="1" parent="1" source="{id_map[source]}" target="{id_map[target]}">'
            '<mxGeometry relative="1" as="geometry"/>'
            "</mxCell>"
        )
    content = "\n".join(cells)
    xml = f'''<mxfile host="ai-diagram-factory" agent="ai-diagram-factory" version="0.1.0">
  <diagram id="page-1" name="{escape(title)}">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1200" pageHeight="800" math="0" shadow="0">
      <root>
        {content}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
'''
    path.write_text(xml, encoding="utf-8")


def _try_drawio_export(drawio_path: Path, png_path: Path) -> dict[str, Any]:
    if os.environ.get("AI_DIAGRAM_FACTORY_SKIP_EXTERNAL_EXPORTS") == "1":
        return {"status": "fallback", "reason": "disabled by AI_DIAGRAM_FACTORY_SKIP_EXTERNAL_EXPORTS"}
    env = os.environ.copy()
    env["PYTHONPATH"] = str(DRAWIO_HARNESS)
    cmd = ["cli-anything-drawio", "--project", str(drawio_path), "export", "render", str(png_path), "--format", "png", "--overwrite"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=90)
    except Exception as exc:
        return {"status": "fallback", "reason": str(exc)}
    if result.returncode == 0 and png_path.exists():
        return {"status": "drawio", "stdout": result.stdout}
    return {"status": "fallback", "returncode": result.returncode, "stderr": result.stderr, "stdout": result.stdout}


def _render_drawio_preview(figure: dict[str, Any], nodes: list[dict[str, Any]], edges: list[list[str]], png_path: Path, mode: str) -> None:
    width = 1160
    height = max(640, max((int(node["y"]) for node in nodes), default=120) + 190)
    img, draw = new_canvas(width, height, "#FFFFFF")
    title_font = load_font(30, bold=True)
    font = load_font(20)
    small = load_font(16)
    draw.text((50, 32), figure.get("title", figure["id"]), font=title_font, fill=PALETTE["ink"])
    positions = {}
    if mode == "architecture":
        lane_names = []
        for node in nodes:
            if node.get("lane") and node["lane"] not in lane_names:
                lane_names.append(node["lane"])
        for lane_index, lane in enumerate(lane_names):
            y = 120 + lane_index * 170
            draw.rounded_rectangle((45, y, width - 45, y + 130), radius=18, fill="#FAFAFA", outline="#D1D5DB", width=2)
            draw.text((64, y + 12), lane, font=small, fill=PALETTE["muted"])
    for node in nodes:
        x, y = float(node["x"]), float(node["y"])
        box = (x, y, x + 170, y + 70)
        draw_round_rect(draw, box, node.get("fill", "#DCEBFF"), "#5B6B7A")
        draw_centered_text(draw, box, node.get("label", node.get("id", "")), font)
        positions[str(node.get("id", node.get("label", "")))] = box
    for edge in edges:
        if len(edge) < 2 or str(edge[0]) not in positions or str(edge[1]) not in positions:
            continue
        a = positions[str(edge[0])]
        b = positions[str(edge[1])]
        start = (a[2], (a[1] + a[3]) / 2)
        end = (b[0], (b[1] + b[3]) / 2)
        if end[0] < start[0]:
            start = ((a[0] + a[2]) / 2, a[3])
            end = ((b[0] + b[2]) / 2, b[1])
        draw_arrow(draw, start, end, fill="#4B5563")
    save_png(img, png_path)
