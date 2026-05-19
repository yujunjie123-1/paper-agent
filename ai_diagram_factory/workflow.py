from __future__ import annotations

import base64
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import quote
from xml.sax.saxutils import escape

from .io import abs_path, load_manifest, write_json
from .planner import build_workflow_plan
from .renderers import RENDERERS


def render_workflow_manifest(
    manifest_path: str | Path,
    out_dir: str | Path,
    only_ids: tuple[str, ...] = (),
    source_formats: tuple[str, ...] = (),
) -> dict[str, Any]:
    payload = load_manifest(manifest_path)
    workflows = payload.get("workflows", [])
    if not workflows:
        raise ValueError("Manifest must contain a non-empty workflows list.")
    target_dir = abs_path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    selected = set(only_ids)
    results = []
    for workflow in workflows:
        if selected and workflow.get("id") not in selected:
            continue
        results.append(render_workflow(workflow, target_dir, source_formats=source_formats))
    if not results:
        raise ValueError("No workflows matched the requested ids.")
    index = {
        "manifest": str(abs_path(manifest_path)),
        "output_dir": str(target_dir),
        "results": results,
    }
    write_json(target_dir / "workflow_index.json", index)
    return index


def render_workflow(workflow: dict[str, Any], out_dir: Path, source_formats: tuple[str, ...] = ()) -> dict[str, Any]:
    workflow_id = _required(workflow, "id")
    workflow_dir = out_dir / workflow_id
    stages_dir = workflow_dir / "stages"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    stages_dir.mkdir(parents=True, exist_ok=True)

    tool_plan = build_workflow_plan(workflow)
    tool_plan_path = write_json(workflow_dir / "tool_plan.json", tool_plan)

    stage_results: dict[str, dict[str, Any]] = {}
    for stage in workflow.get("stages", []):
        stage_result = _render_stage(stage, stages_dir)
        stage_results[stage["id"]] = stage_result

    assembly = _render_master_assembly(workflow, stage_results, workflow_dir, source_formats=source_formats)
    report = {
        "id": workflow_id,
        "title": workflow.get("title", workflow_id),
        "objective": workflow.get("objective", ""),
        "stages": list(stage_results.values()),
        "assembly": assembly,
        "workflow": workflow.get("workflow", []),
        "tool_plan": tool_plan,
        "tool_plan_path": str(tool_plan_path),
    }
    report_path = write_json(workflow_dir / "workflow_report.json", report)
    report["report"] = str(report_path)
    return report


def _render_stage(stage: dict[str, Any], stages_dir: Path) -> dict[str, Any]:
    stage_id = _required(stage, "id")
    figure = dict(_required(stage, "figure"))
    figure.setdefault("id", stage_id)
    kind = figure.get("kind", stage.get("kind"))
    if not kind:
        raise ValueError(f"Stage {stage_id} must define figure.kind or kind.")
    renderer = RENDERERS.get(kind)
    if renderer is None:
        raise ValueError(f"Unsupported stage renderer: {kind}")
    stage_out = stages_dir / stage_id
    result = renderer(figure, stage_out)
    return {
        "id": stage_id,
        "tool": stage.get("tool", kind),
        "role": stage.get("role", ""),
        "kind": kind,
        "output": result,
    }


def _render_master_assembly(
    workflow: dict[str, Any],
    stage_results: dict[str, dict[str, Any]],
    workflow_dir: Path,
    source_formats: tuple[str, ...] = (),
) -> dict[str, Any]:
    assembly = workflow.get("assembly", {})
    canvas = assembly.get("canvas", {})
    width = int(canvas.get("width", 1600))
    height = int(canvas.get("height", 900))
    name = assembly.get("id", f"{workflow['id']}_master")
    svg_path = workflow_dir / f"{name}.svg"
    drawio_path = workflow_dir / f"{name}.drawio"
    png_path = workflow_dir / f"{name}.png"
    vsdx_path = workflow_dir / f"{name}.vsdx"
    requested_formats = _requested_source_formats(assembly, source_formats)

    svg_text = _build_assembly_svg(workflow, assembly, stage_results, width, height, include_reference=False)
    svg_path.write_text(svg_text, encoding="utf-8")
    _write_png(svg_text, png_path)
    drawio_path.write_text(
        _build_assembly_drawio(workflow, assembly, stage_results, width, height, include_reference=False),
        encoding="utf-8",
    )
    vsdx_export = _try_export_vsdx(drawio_path, vsdx_path) if "vsdx" in requested_formats else {"status": "not_requested"}
    result = {
        "id": name,
        "tool": "drawio_master_assembly",
        "svg": str(svg_path),
        "drawio": str(drawio_path),
        "png": str(png_path),
        "vsdx": str(vsdx_path) if vsdx_path.exists() else None,
        "vsdx_export": vsdx_export,
        "requested_source_formats": requested_formats,
        "notes": assembly.get("notes", ""),
    }
    if assembly.get("reference"):
        trace_svg_path = workflow_dir / f"{name}_trace.svg"
        trace_drawio_path = workflow_dir / f"{name}_trace.drawio"
        trace_png_path = workflow_dir / f"{name}_trace.png"
        trace_vsdx_path = workflow_dir / f"{name}_trace.vsdx"
        trace_svg_text = _build_assembly_svg(workflow, assembly, stage_results, width, height, include_reference=True)
        trace_svg_path.write_text(trace_svg_text, encoding="utf-8")
        _write_png(trace_svg_text, trace_png_path)
        trace_drawio_path.write_text(
            _build_assembly_drawio(workflow, assembly, stage_results, width, height, include_reference=True),
            encoding="utf-8",
        )
        trace_vsdx_export = _try_export_vsdx(trace_drawio_path, trace_vsdx_path) if "vsdx" in requested_formats else {"status": "not_requested"}
        result["trace"] = {
            "svg": str(trace_svg_path),
            "drawio": str(trace_drawio_path),
            "png": str(trace_png_path),
            "vsdx": str(trace_vsdx_path) if trace_vsdx_path.exists() else None,
            "vsdx_export": trace_vsdx_export,
            "reference": str(_reference_path(assembly)),
        }
    result["deliverables"] = _write_deliverables(
        workflow_dir,
        name,
        png_path,
        {
            "drawio": drawio_path,
            "svg": svg_path,
            "vsdx": vsdx_path if vsdx_path.exists() else None,
        },
        requested_formats,
    )
    return result


def _build_assembly_svg(
    workflow: dict[str, Any],
    assembly: dict[str, Any],
    stage_results: dict[str, dict[str, Any]],
    width: int,
    height: int,
    include_reference: bool = False,
) -> str:
    body: list[str] = [
        '<defs>',
        '<marker id="arrow-teal" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#4f8f8a"/></marker>',
        '<marker id="arrow-blue" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#1287cf"/></marker>',
        '<marker id="arrow-red" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#ff2020"/></marker>',
        '<marker id="arrow-black" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#222222"/></marker>',
        '<marker id="arrow-cyan" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#75c5de"/></marker>',
        '</defs>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
    ]
    title = assembly.get("title")
    if title:
        body.append(_svg_text(40, 36, title, size=26, anchor="start", weight="600"))
    if include_reference and assembly.get("reference"):
        body.append(_reference_image_svg(assembly, width, height))
    for placement in assembly.get("placements", []):
        _append_svg_placement(body, placement, stage_results)
    for shape in assembly.get("shapes", []):
        body.extend(_shape_to_svg(shape))
    for connector in assembly.get("connectors", []):
        body.append(_connector_to_svg(connector))
    for label in assembly.get("labels", []):
        body.append(_label_to_svg(label))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        + "\n".join(body)
        + "\n</svg>\n"
    )


def _append_svg_placement(
    body: list[str],
    placement: dict[str, Any],
    stage_results: dict[str, dict[str, Any]],
) -> None:
    asset_path = _placement_image_path(placement, stage_results)
    data_uri = _file_data_uri(asset_path, _mime_for_path(asset_path))
    opacity = float(placement.get("opacity", 1.0))
    body.append(
        f'<image x="{float(placement.get("x", 0)):.2f}" y="{float(placement.get("y", 0)):.2f}" '
        f'width="{float(placement.get("width", 300)):.2f}" height="{float(placement.get("height", 200)):.2f}" '
        f'href="{data_uri}" opacity="{opacity:.3f}" preserveAspectRatio="xMidYMid meet"/>'
    )


def _reference_image_svg(assembly: dict[str, Any], width: int, height: int) -> str:
    reference = assembly.get("reference", {})
    ref_path = _reference_path(assembly)
    data_uri = _file_data_uri(ref_path, _mime_for_path(ref_path))
    x = float(reference.get("x", 0))
    y = float(reference.get("y", 0))
    w = float(reference.get("width", width))
    h = float(reference.get("height", height))
    opacity = float(reference.get("opacity", 0.35))
    return (
        f'<image x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
        f'href="{data_uri}" opacity="{opacity:.3f}" preserveAspectRatio="xMidYMid meet"/>'
    )


def _shape_to_svg(shape: dict[str, Any]) -> list[str]:
    kind = shape.get("type", "rect")
    if kind == "rect":
        dash = _dash_attr(shape)
        return [
            f'<rect x="{shape["x"]}" y="{shape["y"]}" width="{shape["width"]}" height="{shape["height"]}" '
            f'rx="{shape.get("rx", 0)}" fill="{shape.get("fill", "#ffffff")}" stroke="{shape.get("stroke", "#222222")}" '
            f'stroke-width="{shape.get("stroke_width", 1.5)}"{dash} opacity="{shape.get("opacity", 1)}"/>'
        ]
    if kind == "circle":
        return [
            f'<circle cx="{shape["cx"]}" cy="{shape["cy"]}" r="{shape["r"]}" fill="{shape.get("fill", "#ffffff")}" '
            f'stroke="{shape.get("stroke", "#222222")}" stroke-width="{shape.get("stroke_width", 1.8)}"/>'
        ]
    if kind == "iso_block":
        return _iso_block_svg(shape)
    if kind == "feature_stack":
        return _feature_stack_svg(shape)
    if kind == "legend_box":
        return _legend_box_svg(shape)
    if kind == "conv_marker":
        return _conv_marker_svg(shape)
    if kind == "up_marker":
        return _sample_marker_svg(shape, up=True)
    if kind == "pool_marker":
        return _sample_marker_svg(shape, up=False)
    if kind == "attention_input":
        return _attention_input_svg(shape)
    if kind == "attention_circle":
        return _attention_circle_svg(shape)
    if kind == "cswf_module":
        return _cswf_module_svg(shape)
    if kind == "cube":
        return _cube_svg(shape)
    if kind == "line":
        return [
            _svg_line(
                float(shape["x1"]),
                float(shape["y1"]),
                float(shape["x2"]),
                float(shape["y2"]),
                shape.get("stroke", "#222222"),
                float(shape.get("stroke_width", 1.5)),
                marker=shape.get("marker"),
                opacity=float(shape.get("opacity", 1.0)),
            )
        ]
    if kind == "path":
        return [
            f'<path d="{escape(str(shape["d"]))}" fill="{shape.get("fill", "none")}" stroke="{shape.get("stroke", "#222222")}" '
            f'stroke-width="{shape.get("stroke_width", 1.5)}" stroke-linecap="round" stroke-linejoin="round"'
            f'{_dash_attr(shape)} opacity="{shape.get("opacity", 1.0)}"/>'
        ]
    return []


def _iso_block_svg(shape: dict[str, Any]) -> list[str]:
    x = float(shape["x"])
    y = float(shape["y"])
    w = float(shape["width"])
    h = float(shape["height"])
    depth = float(shape.get("depth", 16))
    fill = shape.get("fill", "#f7bf73")
    stroke = shape.get("stroke", "#875f2e")
    dx = depth
    dy = -depth
    top = [(x, y), (x + dx, y + dy), (x + w + dx, y + dy), (x + w, y)]
    side = [(x + w, y), (x + w + dx, y + dy), (x + w + dx, y + h + dy), (x + w, y + h)]
    front = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    polygons = [
        _svg_polygon(top, _adjust_color(fill, 1.12), stroke, shape.get("opacity", 0.9)),
        _svg_polygon(side, _adjust_color(fill, 0.92), stroke, shape.get("opacity", 0.9)),
        _svg_polygon(front, fill, stroke, shape.get("opacity", 0.9)),
    ]
    stripes = int(shape.get("stripes", 0))
    for index in range(1, stripes + 1):
        xx = x + index * w / (stripes + 1)
        polygons.append(_svg_line(xx, y, xx, y + h, stroke, 0.65, opacity=0.32))
        polygons.append(_svg_line(xx, y, xx + dx, y + dy, stroke, 0.65, opacity=0.28))
    return polygons


def _feature_stack_svg(shape: dict[str, Any]) -> list[str]:
    items = []
    count = int(shape.get("count", 5))
    step_x = float(shape.get("step_x", 11))
    step_y = float(shape.get("step_y", -8))
    for index in range(count - 1, -1, -1):
        shifted = {
            **shape,
            "type": "rect",
            "x": float(shape["x"]) + index * step_x,
            "y": float(shape["y"]) + index * step_y,
            "opacity": shape.get("opacity", 0.86),
        }
        items.extend(_shape_to_svg(shifted))
    return items


def _legend_box_svg(shape: dict[str, Any]) -> list[str]:
    body = _shape_to_svg({**shape, "type": "rect", "fill": shape.get("fill", "#ffffff"), "rx": 0})
    for item in shape.get("items", []):
        x = float(item["x"])
        y = float(item["y"])
        if item.get("icon") == "arrow":
            body.append(_svg_line(x, y, x + 28, y, item.get("color", "#222222"), 2.0, marker=item.get("marker", "arrow-red")))
        elif item.get("icon") == "square":
            body.extend(_shape_to_svg({"type": "rect", "x": x, "y": y - 6, "width": 12, "height": 12, "fill": item.get("color", "#cccccc")}))
        elif item.get("icon") == "circle":
            body.extend(_shape_to_svg({"type": "circle", "cx": x + 6, "cy": y, "r": 8, "fill": "#ffffff"}))
        elif item.get("icon") == "conv_marker":
            body.extend(_conv_marker_svg({"x": x, "y": y - 6, "fill": item.get("color", "#ff2020")}))
        elif item.get("icon") == "up_marker":
            body.extend(_sample_marker_svg({"x": x, "y": y - 12, "fill": item.get("color", "#f4eb33")}, up=True))
        elif item.get("icon") == "pool_marker":
            body.extend(_sample_marker_svg({"x": x, "y": y + 10, "fill": item.get("color", "#f4eb33")}, up=False))
        elif item.get("icon") == "attention_input":
            body.extend(_attention_input_svg({"x": x, "y": y, "fill": item.get("color", "#96dff0")}))
        elif item.get("icon") == "attention_circle":
            body.extend(_attention_circle_svg({"cx": x + 8, "cy": y, "r": 12}))
        body.append(_svg_text(x + 38, y, item.get("label", ""), size=int(item.get("size", 16)), anchor="start"))
    return body


def _conv_marker_svg(shape: dict[str, Any]) -> list[str]:
    x = float(shape["x"])
    y = float(shape["y"])
    fill = shape.get("fill", "#ff2020")
    stroke = shape.get("stroke", "#222222")
    scale = float(shape.get("scale", 1.0))
    points = [
        (x, y),
        (x + 13 * scale, y + 6 * scale),
        (x, y + 12 * scale),
        (x + 4 * scale, y + 6 * scale),
    ]
    return [_svg_polygon(points, fill, stroke, float(shape.get("opacity", 1.0)))]


def _sample_marker_svg(shape: dict[str, Any], up: bool) -> list[str]:
    x = float(shape["x"])
    y = float(shape["y"])
    fill = shape.get("fill", "#f4eb33")
    stroke = shape.get("stroke", "#222222")
    scale = float(shape.get("scale", 1.0))
    if up:
        points = [
            (x + 6 * scale, y),
            (x + 12 * scale, y + 12 * scale),
            (x + 8 * scale, y + 12 * scale),
            (x + 8 * scale, y + 24 * scale),
            (x + 4 * scale, y + 24 * scale),
            (x + 4 * scale, y + 12 * scale),
            (x, y + 12 * scale),
        ]
    else:
        points = [
            (x, y),
            (x + 6 * scale, y + 12 * scale),
            (x + 12 * scale, y),
            (x + 8 * scale, y),
            (x + 8 * scale, y - 12 * scale),
            (x + 4 * scale, y - 12 * scale),
            (x + 4 * scale, y),
        ]
    return [_svg_polygon(points, fill, stroke, float(shape.get("opacity", 1.0)))]


def _attention_input_svg(shape: dict[str, Any]) -> list[str]:
    x = float(shape["x"])
    y = float(shape["y"])
    fill = shape.get("fill", "#96dff0")
    stroke = shape.get("stroke", "#222222")
    scale = float(shape.get("scale", 1.0))
    points = [
        (x, y),
        (x + 8 * scale, y - 12 * scale),
        (x + 16 * scale, y),
        (x + 8 * scale, y - 4 * scale),
    ]
    return [_svg_polygon(points, fill, stroke, float(shape.get("opacity", 1.0)))]


def _attention_circle_svg(shape: dict[str, Any]) -> list[str]:
    cx = float(shape["cx"])
    cy = float(shape["cy"])
    r = float(shape.get("r", 24))
    stroke = shape.get("stroke", "#555555")
    items = [
        f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{shape.get("fill", "#ffffff")}" '
        f'stroke="{stroke}" stroke-width="{shape.get("stroke_width", 2.0)}"/>'
    ]
    items.append(
        f'<path d="M {cx - r * 0.65:.2f} {cy + r * 0.08:.2f} '
        f'C {cx - r * 0.25:.2f} {cy - r * 0.62:.2f}, {cx + r * 0.22:.2f} {cy + r * 0.62:.2f}, {cx + r * 0.65:.2f} {cy - r * 0.08:.2f}" '
        f'fill="none" stroke="{stroke}" stroke-width="{shape.get("wave_width", 2.0)}" stroke-linecap="round"/>'
    )
    return items


def _cswf_module_svg(shape: dict[str, Any]) -> list[str]:
    x = float(shape["x"])
    y = float(shape["y"])
    scale = float(shape.get("scale", 1.0))
    width = float(shape.get("width", 178 * scale))
    height = float(shape.get("height", 76 * scale))
    items = _shape_to_svg(
        {
            "type": "rect",
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "fill": shape.get("fill", "#ffd8bf"),
            "stroke": shape.get("stroke", "#222222"),
            "stroke_width": shape.get("stroke_width", 1.6),
        }
    )
    for index in range(int(shape.get("stack_count", 5))):
        items.extend(
            _cube_svg(
                {
                    "x": x + (24 + index * 8) * scale,
                    "y": y + (48 - index * 6) * scale,
                    "size": 25 * scale,
                    "fill": shape.get("cube_fill", "#b7a4f5"),
                    "stroke": shape.get("cube_stroke", "#7350d8"),
                    "opacity": 0.76,
                }
            )
        )
    brace_x = x + width * 0.52
    items.append(
        f'<path d="M {brace_x:.2f} {y + height * 0.18:.2f} C {brace_x + 18 * scale:.2f} {y + height * 0.18:.2f}, '
        f'{brace_x + 18 * scale:.2f} {y + height * 0.82:.2f}, {brace_x:.2f} {y + height * 0.82:.2f}" '
        f'fill="none" stroke="#22aa66" stroke-width="{2.0 * scale:.2f}"/>'
    )
    items.extend(
        _cube_svg(
            {
                "x": x + width * 0.66,
                "y": y + height * 0.61,
                "size": 32 * scale,
                "fill": shape.get("cube_fill", "#c9b7f5"),
                "stroke": shape.get("cube_stroke", "#7350d8"),
                "opacity": 0.80,
            }
        )
    )
    return items


def _cube_svg(shape: dict[str, Any]) -> list[str]:
    return _iso_block_svg(
        {
            "x": shape["x"],
            "y": shape["y"],
            "width": shape.get("size", 24),
            "height": shape.get("size", 24),
            "depth": float(shape.get("size", 24)) * 0.34,
            "fill": shape.get("fill", "#c9b7f5"),
            "stroke": shape.get("stroke", "#7350d8"),
            "opacity": shape.get("opacity", 0.82),
            "stripes": shape.get("stripes", 0),
        }
    )


def _connector_to_svg(connector: dict[str, Any]) -> str:
    points = connector.get("points", [])
    if len(points) < 2:
        return ""
    color = connector.get("color", "#4f8f8a")
    width = connector.get("width", 2.0)
    marker = connector.get("marker", "arrow-teal")
    dash = _dash_attr(connector)
    opacity = connector.get("opacity", 1)
    if connector.get("curve"):
        d = connector["curve"]
        return (
            f'<path d="{escape(d)}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'stroke-linecap="round" stroke-linejoin="round" marker-end="url(#{marker})"{dash} opacity="{opacity}"/>'
        )
    path_points = " ".join(f'{float(x):.2f},{float(y):.2f}' for x, y in points)
    return (
        f'<polyline points="{path_points}" fill="none" stroke="{color}" stroke-width="{width}" '
        f'stroke-linecap="round" stroke-linejoin="round" marker-end="url(#{marker})"{dash} opacity="{opacity}"/>'
    )


def _label_to_svg(label: dict[str, Any]) -> str:
    return _svg_text(
        float(label["x"]),
        float(label["y"]),
        str(label.get("text", "")),
        size=int(label.get("size", 16)),
        anchor=label.get("anchor", "middle"),
        weight=label.get("weight", "400"),
        rotate=label.get("rotate"),
        fill=label.get("fill", "#222222"),
    )


def _build_assembly_drawio(
    workflow: dict[str, Any],
    assembly: dict[str, Any],
    stage_results: dict[str, dict[str, Any]],
    width: int,
    height: int,
    include_reference: bool = False,
) -> str:
    cells = [
        '<mxCell id="0"/>',
        '<mxCell id="reference_layer" value="Reference underlay" parent="0"/>',
        '<mxCell id="asset_layer" value="Generated assets" parent="0"/>',
        '<mxCell id="shape_layer" value="Editable assembly shapes" parent="0"/>',
        '<mxCell id="connector_layer" value="Editable routed connectors" parent="0"/>',
        '<mxCell id="label_layer" value="Labels" parent="0"/>',
    ]
    next_id = 2
    if include_reference and assembly.get("reference"):
        reference = assembly.get("reference", {})
        ref_path = _reference_path(assembly)
        data_uri = quote(_file_data_uri(ref_path, _mime_for_path(ref_path)), safe=":/,+=@#")
        cells.append(
            f'<mxCell id="reference_image" value="locked reference image" '
            f'style="shape=image;imageAspect=0;aspect=fixed;locked=1;image={data_uri};opacity={int(float(reference.get("opacity", 35)) * 100) if float(reference.get("opacity", 0.35)) <= 1 else int(reference.get("opacity", 35))};" '
            f'vertex="1" parent="reference_layer"><mxGeometry x="{reference.get("x", 0)}" y="{reference.get("y", 0)}" '
            f'width="{reference.get("width", width)}" height="{reference.get("height", height)}" as="geometry"/></mxCell>'
        )
    for placement in assembly.get("placements", []):
        asset_path = _placement_image_path(placement, stage_results)
        data_uri = quote(_file_data_uri(asset_path, _mime_for_path(asset_path)), safe=":/,+=@#")
        cells.append(
            f'<mxCell id="n{next_id}" value="{escape(placement.get("label", ""))}" '
            f'style="shape=image;imageAspect=0;aspect=fixed;verticalLabelPosition=bottom;verticalAlign=top;image={data_uri};" '
            f'vertex="1" parent="asset_layer"><mxGeometry x="{placement.get("x", 0)}" y="{placement.get("y", 0)}" '
            f'width="{placement.get("width", 300)}" height="{placement.get("height", 200)}" as="geometry"/></mxCell>'
        )
        next_id += 1
    for shape in assembly.get("shapes", []):
        if shape.get("type") not in {"rect", "circle"}:
            continue
        style = _shape_drawio_style(shape)
        x = shape.get("x", shape.get("cx", 0) - shape.get("r", 0))
        y = shape.get("y", shape.get("cy", 0) - shape.get("r", 0))
        w = shape.get("width", shape.get("r", 20) * 2)
        h = shape.get("height", shape.get("r", 20) * 2)
        cells.append(
            f'<mxCell id="n{next_id}" value="{escape(shape.get("label", ""))}" style="{style}" vertex="1" parent="shape_layer">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
        )
        next_id += 1
    for label in assembly.get("labels", []):
        cells.append(
            f'<mxCell id="n{next_id}" value="{escape(str(label.get("text", "")))}" '
            f'style="text;html=1;strokeColor=none;fillColor=none;align={label.get("align", "center")};verticalAlign=middle;fontSize={label.get("size", 16)};" '
            f'vertex="1" parent="label_layer"><mxGeometry x="{float(label["x"]) - 80}" y="{float(label["y"]) - 16}" width="160" height="32" as="geometry"/></mxCell>'
        )
        next_id += 1
    for connector in assembly.get("connectors", []):
        points = connector.get("points", [])
        if len(points) < 2:
            continue
        start = points[0]
        end = points[-1]
        mx_points = "".join(f'<mxPoint x="{p[0]}" y="{p[1]}"/>' for p in points[1:-1])
        color = connector.get("color", "#4f8f8a")
        style = f'edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor={color};strokeWidth={connector.get("width", 2)};endArrow=block;endFill=1;'
        cells.append(
            f'<mxCell id="e{next_id}" value="{escape(connector.get("label", ""))}" style="{style}" edge="1" parent="connector_layer">'
            f'<mxGeometry relative="1" as="geometry"><mxPoint x="{start[0]}" y="{start[1]}" as="sourcePoint"/>'
            f'<mxPoint x="{end[0]}" y="{end[1]}" as="targetPoint"/><Array as="points">{mx_points}</Array></mxGeometry></mxCell>'
        )
        next_id += 1
    content = "\n".join(cells)
    title = escape(assembly.get("title", workflow.get("title", workflow["id"])))
    return f'''<mxfile host="ai-diagram-factory" agent="ai-diagram-factory" version="0.2.0">
  <diagram id="master" name="{title}">
    <mxGraphModel dx="{width}" dy="{height}" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{width}" pageHeight="{height}" math="1" shadow="0">
      <root>
        {content}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
'''


def _shape_drawio_style(shape: dict[str, Any]) -> str:
    fill = shape.get("fill", "#ffffff")
    stroke = shape.get("stroke", "#222222")
    if shape.get("type") == "circle":
        return f"ellipse;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};"
    return f"rounded={1 if shape.get('rx') else 0};whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};"


def _write_png(svg_text: str, png_path: Path) -> None:
    try:
        import cairosvg

        cairosvg.svg2png(bytestring=svg_text.encode("utf-8"), write_to=str(png_path))
    except Exception as exc:
        png_path.with_suffix(".render-error.txt").write_text(str(exc), encoding="utf-8")


def _try_export_vsdx(drawio_path: Path, vsdx_path: Path) -> dict[str, Any]:
    cmd = [
        "cli-anything-drawio",
        "--project",
        str(drawio_path),
        "export",
        "render",
        str(vsdx_path),
        "--format",
        "vsdx",
        "--overwrite",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except Exception as exc:
        return {"status": "skipped", "reason": str(exc), "command": cmd}
    if result.returncode == 0 and vsdx_path.exists():
        return {"status": "exported", "path": str(vsdx_path), "stdout": result.stdout}
    return {
        "status": "unavailable",
        "returncode": result.returncode,
        "stdout": result.stdout[-2000:],
        "stderr": result.stderr[-2000:],
        "command": cmd,
    }


def _requested_source_formats(assembly: dict[str, Any], override: tuple[str, ...]) -> list[str]:
    raw = list(override) if override else list(assembly.get("source_formats", ["drawio"]))
    allowed = {"drawio", "svg", "vsdx"}
    result = []
    for item in raw:
        fmt = str(item).lower().lstrip(".")
        if fmt == "png":
            continue
        if fmt not in allowed:
            raise ValueError(f"Unsupported source format: {item}. Supported: {', '.join(sorted(allowed))}")
        if fmt not in result:
            result.append(fmt)
    return result or ["drawio"]


def _write_deliverables(
    workflow_dir: Path,
    name: str,
    png_path: Path,
    source_paths: dict[str, Path | None],
    requested_formats: list[str],
) -> dict[str, Any]:
    deliverable_dir = workflow_dir / "deliverables"
    deliverable_dir.mkdir(parents=True, exist_ok=True)
    final_png = deliverable_dir / f"{name}.png"
    shutil.copy2(png_path, final_png)
    sources: dict[str, str | None] = {}
    missing = []
    for fmt in requested_formats:
        source = source_paths.get(fmt)
        if source and source.exists():
            target = deliverable_dir / f"{name}.{fmt}"
            shutil.copy2(source, target)
            sources[fmt] = str(target)
        else:
            sources[fmt] = None
            missing.append(fmt)
    return {"png": str(final_png), "sources": sources, "missing": missing}


def _stage_png(stage_results: dict[str, dict[str, Any]], asset_id: str) -> Path:
    if asset_id not in stage_results:
        raise ValueError(f"Unknown assembly asset: {asset_id}")
    png = stage_results[asset_id].get("output", {}).get("png")
    if not png:
        raise ValueError(f"Stage does not expose a PNG asset: {asset_id}")
    return Path(png)


def _placement_image_path(placement: dict[str, Any], stage_results: dict[str, dict[str, Any]]) -> Path:
    if placement.get("path"):
        path = abs_path(placement["path"])
        if not path.is_file():
            raise ValueError(f"Placement image file not found: {path}")
        return path
    asset_id = _required(placement, "asset")
    return _stage_png(stage_results, asset_id)


def _reference_path(assembly: dict[str, Any]) -> Path:
    reference = assembly.get("reference", {})
    path = reference.get("path")
    if not path:
        raise ValueError("Assembly reference requires a path.")
    ref_path = abs_path(path)
    if not ref_path.is_file():
        raise ValueError(f"Reference image file not found: {ref_path}")
    return ref_path


def _file_data_uri(path: Path, mime: str) -> str:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def _mime_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".svg":
        return "image/svg+xml"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    return "image/png"


def _required(data: dict[str, Any], key: str) -> Any:
    if key not in data:
        raise ValueError(f"Missing required key: {key}")
    return data[key]


def _dash_attr(shape: dict[str, Any]) -> str:
    dash = shape.get("dash")
    return f' stroke-dasharray="{escape(str(dash))}"' if dash else ""


def _svg_polygon(points: list[tuple[float, float]], fill: str, stroke: str, opacity: float) -> str:
    pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="1.2" opacity="{opacity}"/>'


def _svg_line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    stroke: str,
    width: float,
    marker: str | None = None,
    opacity: float = 1.0,
) -> str:
    marker_attr = f' marker-end="url(#{marker})"' if marker else ""
    return (
        f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
        f'stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" opacity="{opacity}"{marker_attr}/>'
    )


def _svg_text(
    x: float,
    y: float,
    text: str,
    size: int,
    anchor: str = "middle",
    weight: str = "400",
    fill: str = "#222222",
    rotate: float | None = None,
) -> str:
    transform = f' transform="rotate({rotate:.2f} {x:.2f} {y:.2f})"' if rotate is not None else ""
    return (
        f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="{anchor}" dominant-baseline="middle" '
        f'font-family="Microsoft YaHei, SimSun, Times New Roman, serif" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}"{transform}>{escape(text)}</text>'
    )


def _adjust_color(hex_color: str, factor: float) -> str:
    value = hex_color.lstrip("#")
    rgb = []
    for idx in (0, 2, 4):
        channel = int(value[idx : idx + 2], 16)
        rgb.append(max(0, min(255, int(channel * factor))))
    return "#" + "".join(f"{channel:02x}" for channel in rgb)
