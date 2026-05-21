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
from ..latex_utils import compile_tikz_body_to_svg
from ..styles import KIND_COLORS, PALETTE


def render_plotneuralnet_cnn(figure: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    fig_dir = out_dir / figure["id"]
    fig_dir.mkdir(parents=True, exist_ok=True)
    if figure.get("compact") or figure.get("stack"):
        return _render_compact_stack(figure, fig_dir)

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


def _render_compact_stack(figure: dict[str, Any], fig_dir: Path) -> dict[str, Any]:
    """Render a single 3D feature-map stack as a tight-bbox SVG via standalone TikZ.

    The figure dict accepts:
        count           (int)   number of visible slices in the stack
        face_width_mm   (float) front-face width in mm
        face_height_mm  (float) front-face height in mm
        step_mm         (float) per-slice perspective offset in mm
        depth_x_mm      (float) top/side-face x offset in mm
        depth_y_mm      (float) top/side-face y offset in mm
        fill            (str)   TikZ color for the stack faces (default 'black!28')
        top_fill        (str)   optional TikZ color for top faces
        side_fill       (str)   optional TikZ color for side faces
        stroke          (str)   TikZ color for stack outlines (default 'black')
        overlays        (list)  selected cells / receptive-field markers (see below)

    Each overlay item is::

        {
            "x": <mm>, "y": <mm>, "width": <mm>, "height": <mm>,
            "color": "<tikz color>",
            "mode": "outline" | "filled" | "translucent",
            "line_width": <mm>,
        }
    """
    png_path = fig_dir / f"{figure['id']}.png"
    body = _compact_stack_body(figure)
    latex_result = compile_tikz_body_to_svg(
        body,
        fig_dir,
        figure["id"],
        engine=figure.get("engine", "auto"),
        text_mode=figure.get("text_mode", "paths"),
    )
    sources = [latex_result["tex"]]
    if latex_result.get("pdf"):
        sources.append(latex_result["pdf"])
    if latex_result.get("svg"):
        sources.append(latex_result["svg"])
        _rasterize_svg_to_png(latex_result["svg"], png_path)
    if not png_path.exists():
        _render_compact_stack_png(figure, png_path)
    backend_status = "tikz_compact_svg" if latex_result.get("svg") else "pillow_preview"
    result: dict[str, Any] = {
        "id": figure["id"],
        "kind": "plotneuralnet_cnn",
        "png": str(png_path),
        "sources": sources,
        "backend": {"status": backend_status, "pdf_status": latex_result.get("pdf_status"), "svg_status": latex_result.get("svg_status")},
    }
    if latex_result.get("svg"):
        result["svg"] = latex_result["svg"]
    return result


def _compact_stack_body(figure: dict[str, Any]) -> str:
    count = max(1, int(figure.get("count", 6)))
    face_w = float(figure.get("face_width_mm", 24.0))
    face_h = float(figure.get("face_height_mm", 24.0))
    step = float(figure.get("step_mm", 1.4))
    depth_x = float(figure.get("depth_x_mm", max(0.8, step * 0.85)))
    depth_y = float(figure.get("depth_y_mm", max(0.6, step * 0.65)))
    fill = str(figure.get("fill", "black!28"))
    top_fill = str(figure.get("top_fill", fill))
    side_fill = str(figure.get("side_fill", fill))
    stroke = str(figure.get("stroke", "black"))
    line_width = float(figure.get("line_width_mm", 0.25))
    overlays = figure.get("overlays", []) or []

    lines: list[str] = ["\\begin{tikzpicture}[x=1mm, y=1mm]"]
    for i in range(count - 1, -1, -1):
        ox = i * step
        oy = i * step
        x0 = ox
        y0 = oy
        x1 = ox + face_w
        y1 = oy + face_h
        lines.extend(
            [
                f"  \\fill[{top_fill}, draw={stroke}, line width={line_width:.2f}mm] "
                f"({x0:.2f},{y1:.2f}) -- ({x0 + depth_x:.2f},{y1 + depth_y:.2f}) -- "
                f"({x1 + depth_x:.2f},{y1 + depth_y:.2f}) -- ({x1:.2f},{y1:.2f}) -- cycle;",
                f"  \\fill[{side_fill}, draw={stroke}, line width={line_width:.2f}mm] "
                f"({x1:.2f},{y0:.2f}) -- ({x1 + depth_x:.2f},{y0 + depth_y:.2f}) -- "
                f"({x1 + depth_x:.2f},{y1 + depth_y:.2f}) -- ({x1:.2f},{y1:.2f}) -- cycle;",
                f"  \\fill[{fill}, draw={stroke}, line width={line_width:.2f}mm] "
                f"({x0:.2f},{y0:.2f}) rectangle ({x1:.2f},{y1:.2f});",
            ]
        )
    for overlay in overlays:
        kind = str(overlay.get("type", "rect"))
        ox = float(overlay.get("x", 0))
        oy = float(overlay.get("y", 0))
        ow = float(overlay.get("width", 4))
        oh = float(overlay.get("height", 4))
        color = str(overlay.get("color", "red"))
        mode = str(overlay.get("mode", "outline"))
        lw = float(overlay.get("line_width_mm", 0.45))
        if kind == "rect":
            if mode == "filled":
                lines.append(
                    f"  \\fill[{color}, draw={color}, line width={lw:.2f}mm] "
                    f"({ox:.2f},{oy:.2f}) rectangle ++({ow:.2f},{oh:.2f});"
                )
            elif mode == "translucent":
                opacity = float(overlay.get("opacity", 0.28))
                lines.append(
                    f"  \\fill[{color}, opacity={opacity:.2f}] "
                    f"({ox:.2f},{oy:.2f}) rectangle ++({ow:.2f},{oh:.2f});"
                )
                lines.append(
                    f"  \\draw[{color}, line width={lw:.2f}mm] "
                    f"({ox:.2f},{oy:.2f}) rectangle ++({ow:.2f},{oh:.2f});"
                )
            else:
                lines.append(
                    f"  \\draw[{color}, line width={lw:.2f}mm] "
                    f"({ox:.2f},{oy:.2f}) rectangle ++({ow:.2f},{oh:.2f});"
                )
    lines.append("\\end{tikzpicture}")
    return "\n".join(lines)


def _rasterize_svg_to_png(svg_path: str, png_path: Path) -> None:
    try:
        import cairosvg

        cairosvg.svg2png(url=svg_path, write_to=str(png_path), output_width=600)
    except Exception as exc:
        png_path.with_suffix(".render-error.txt").write_text(str(exc), encoding="utf-8")


def _render_compact_stack_png(figure: dict[str, Any], png_path: Path) -> None:
    count = int(figure.get("count", 6))
    scale = 6
    face_w = int(float(figure.get("face_width_mm", 24.0)) * scale)
    face_h = int(float(figure.get("face_height_mm", 24.0)) * scale)
    step = max(2, int(float(figure.get("step_mm", 1.4)) * scale))
    depth_x = max(1, int(float(figure.get("depth_x_mm", max(0.8, float(figure.get("step_mm", 1.4)) * 0.85))) * scale))
    depth_y = max(1, int(float(figure.get("depth_y_mm", max(0.6, float(figure.get("step_mm", 1.4)) * 0.65))) * scale))
    margin = 14
    total_w = face_w + step * (count - 1) + depth_x + margin * 2
    total_h = face_h + step * (count - 1) + depth_y + margin * 2
    img, draw = new_canvas(total_w, total_h, "#FFFFFF")
    for i in range(count - 1, -1, -1):
        x0 = margin + i * step
        y0 = total_h - margin - face_h - depth_y - i * step
        top = [(x0, y0), (x0 + depth_x, y0 - depth_y), (x0 + face_w + depth_x, y0 - depth_y), (x0 + face_w, y0)]
        side = [
            (x0 + face_w, y0),
            (x0 + face_w + depth_x, y0 - depth_y),
            (x0 + face_w + depth_x, y0 + face_h - depth_y),
            (x0 + face_w, y0 + face_h),
        ]
        draw.polygon(top, fill="#b8b8b8", outline="#222222")
        draw.polygon(side, fill="#929292", outline="#222222")
        draw.rectangle((x0, y0, x0 + face_w, y0 + face_h), fill="#a8a8a8", outline="#222222", width=1)
    for overlay in figure.get("overlays", []) or []:
        ox = margin + int(float(overlay.get("x", 0)) * scale)
        oy = total_h - margin - face_h - depth_y + face_h - int((float(overlay.get("y", 0)) + float(overlay.get("height", 4))) * scale)
        ow = int(float(overlay.get("width", 4)) * scale)
        oh = int(float(overlay.get("height", 4)) * scale)
        color = _fallback_overlay_color(str(overlay.get("color", "red")))
        if overlay.get("mode") in {"filled", "translucent"}:
            draw.rectangle((ox, oy, ox + ow, oy + oh), fill=color, outline=color, width=2)
        else:
            draw.rectangle((ox, oy, ox + ow, oy + oh), outline=color, width=2)
    save_png(img, png_path)


def _fallback_overlay_color(color: str) -> str:
    lower = color.lower()
    if "red" in lower or "ff" in lower or "ee" in lower:
        return "#ee2020"
    if "blue" in lower or "1287" in lower:
        return "#1287cf"
    if "green" in lower or "22aa" in lower:
        return "#22aa44"
    if "magenta" in lower or "cc33" in lower:
        return "#cc33cc"
    if "yellow" in lower or "f4" in lower:
        return "#d4ba1e"
    return "#222222"


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
