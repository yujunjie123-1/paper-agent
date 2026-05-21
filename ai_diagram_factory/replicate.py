from __future__ import annotations

import math
import shutil
from pathlib import Path
from typing import Any

import click

from .io import abs_path, load_manifest, write_json, write_manifest
from .planner import TOOL_PROFILES, plan_workflow_manifest
from .workflow import render_workflow_manifest


MODULE_LIMIT = 12

BACKEND_TO_KIND: dict[str, str] = {
    "plotneuralnet": "plotneuralnet_cnn",
    "drawio": "drawio_architecture",
    "tikz": "tikz_lstm",
    "graphviz": "graphviz_graph",
    "image_to_image": "drawio_architecture",
    "svg": "svg_module",
}

DEFAULT_CANVAS = {"width": 1600, "height": 900}
REQUIRED_COMPONENT_FIELDS = ("id", "name", "backend", "description")
SUPPORTED_SOURCE_FORMATS: tuple[str, ...] = ("drawio", "svg", "pdf", "vsdx")


class ComponentPlanError(click.ClickException):
    """Raised when a component plan fails validation."""


def validate_component_plan(plan: dict[str, Any]) -> None:
    if not isinstance(plan, dict):
        raise ComponentPlanError("Component plan must be a JSON/YAML object.")
    components = plan.get("components")
    if not isinstance(components, list) or not components:
        raise ComponentPlanError("Component plan must include a non-empty 'components' list.")
    if len(components) > MODULE_LIMIT:
        raise ComponentPlanError(
            f"Component plan has {len(components)} modules; the upper bound is {MODULE_LIMIT}. "
            "Merge adjacent modules before retrying."
        )
    seen_ids: set[str] = set()
    for index, component in enumerate(components):
        if not isinstance(component, dict):
            raise ComponentPlanError(f"Component #{index} must be an object.")
        skip_stage = bool(component.get("skip_stage"))
        required = REQUIRED_COMPONENT_FIELDS if not skip_stage else ("id", "name", "description")
        missing = [field for field in required if not component.get(field)]
        if missing:
            raise ComponentPlanError(
                f"Component #{index} (id={component.get('id', '?')}) is missing required fields: {', '.join(missing)}"
            )
        backend = str(component.get("backend", "drawio")).lower().strip()
        if not skip_stage and backend not in TOOL_PROFILES:
            raise ComponentPlanError(
                f"Component '{component['id']}' has unsupported backend '{component['backend']}'. "
                f"Use one of: {', '.join(sorted(TOOL_PROFILES.keys()))}"
            )
        if component["id"] in seen_ids:
            raise ComponentPlanError(f"Duplicate component id: {component['id']}")
        seen_ids.add(component["id"])
        box = component.get("box_xyxy")
        if box is not None:
            if not (isinstance(box, list) and len(box) == 4 and all(isinstance(v, (int, float)) for v in box)):
                raise ComponentPlanError(
                    f"Component '{component['id']}' has invalid box_xyxy; expected [x1, y1, x2, y2] numbers."
                )
    for connector in plan.get("global_connectors", []) or []:
        if not isinstance(connector, dict):
            raise ComponentPlanError("Each global_connector must be an object.")
        if connector.get("from") not in seen_ids or connector.get("to") not in seen_ids:
            raise ComponentPlanError(
                f"global_connector references unknown component(s): from={connector.get('from')} to={connector.get('to')}"
            )


def component_plan_to_workflow_manifest(
    plan: dict[str, Any],
    reference_image: str | None = None,
    project_name: str | None = None,
) -> dict[str, Any]:
    components = plan["components"]
    project = project_name or plan.get("project") or "ai_diagram_replicate"
    workflow_id = _slug(project) + "_replicate"
    canvas = dict(DEFAULT_CANVAS)
    canvas.update(plan.get("canvas", {}) or {})

    reference_size = _reference_size(reference_image) if reference_image else None
    if reference_size and not plan.get("canvas"):
        canvas = {"width": reference_size[0], "height": reference_size[1]}

    stages: list[dict[str, Any]] = []
    placements: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []
    extra_shapes: list[dict[str, Any]] = []
    extra_connectors: list[dict[str, Any]] = []
    extra_labels: list[dict[str, Any]] = []
    box_anchors: dict[str, tuple[float, float, float, float]] = {}

    for index, component in enumerate(components):
        figure_spec = component.get("figure_spec") or {}
        skip_stage = bool(component.get("skip_stage") or figure_spec.get("skip_stage"))
        placement_box = _scaled_box(component.get("box_xyxy"), canvas, reference_size) if component.get("box_xyxy") else None
        if not skip_stage:
            stage = _component_to_stage(component)
            stages.append(stage)
            placement = _component_to_placement(
                component,
                index,
                len(components),
                canvas,
                reference_size,
            )
            placement["asset"] = stage["id"]
            if stage["figure"].get("kind") == "svg_module":
                placement["prefer"] = "svg"
            placements.append(placement)
            anchor = (
                placement["x"],
                placement["y"],
                placement["x"] + placement["width"],
                placement["y"] + placement["height"],
            )
            if not figure_spec.get("hide_label", False):
                labels.append(
                    {
                        "x": placement["x"] + placement["width"] / 2,
                        "y": placement["y"] + placement["height"] + 18,
                        "text": component["name"],
                        "size": 14,
                        "anchor": "middle",
                    }
                )
        else:
            anchor = placement_box if placement_box else _grid_anchor(index, len(components), canvas)
        box_anchors[component["id"]] = anchor

        for shape in figure_spec.get("assembly_shapes", []) or []:
            extra_shapes.append(dict(shape))
        for connector in figure_spec.get("assembly_connectors", []) or []:
            extra_connectors.append(dict(connector))
        for label in figure_spec.get("assembly_labels", []) or []:
            extra_labels.append(dict(label))

    connectors = _build_global_connectors(plan.get("global_connectors", []) or [], placements, box_anchors)
    connectors.extend(extra_connectors)
    labels.extend(extra_labels)
    for label in plan.get("master_labels", []) or []:
        labels.append(dict(label))

    assembly: dict[str, Any] = {
        "id": f"{workflow_id}_master",
        "title": plan.get("master_title", plan.get("summary", project)),
        "canvas": canvas,
        "notes": plan.get("module_count_rationale", ""),
        "placements": placements,
        "shapes": extra_shapes,
        "connectors": connectors,
        "labels": labels,
        "source_formats": list(SUPPORTED_SOURCE_FORMATS),
    }
    if reference_image:
        assembly["reference"] = {
            "path": str(abs_path(reference_image)),
            "x": 0,
            "y": 0,
            "width": canvas["width"],
            "height": canvas["height"],
            "opacity": 0.35,
        }

    planning_components: list[dict[str, Any]] = []
    stage_kind_by_id = {stage["id"]: stage["figure"].get("kind", "") for stage in stages}
    for component in components:
        figure_spec = component.get("figure_spec") or {}
        skip_stage = bool(component.get("skip_stage") or figure_spec.get("skip_stage"))
        backend = str(component.get("backend") or ("drawio" if skip_stage else "drawio")).lower().strip()
        planning_components.append(
            {
                "id": component["id"],
                "name": component["name"],
                "description": component.get("description", ""),
                "backend": backend,
                "kind": stage_kind_by_id.get(component["id"], "assembly_only" if skip_stage else ""),
                "features": component.get("text_inventory", []) or [],
            }
        )

    workflow = {
        "id": workflow_id,
        "title": project,
        "objective": plan.get("summary", ""),
        "planning": {
            "strategy": plan.get(
                "module_count_rationale",
                "Module-by-module replica plan; backend assignment declared per component.",
            ),
            "components": planning_components,
        },
        "workflow": _handoff_steps(planning_components),
        "stages": stages,
        "assembly": assembly,
    }

    return {
        "project": project,
        "description": plan.get("summary", ""),
        "workflows": [workflow],
    }


def replicate_from_plan(
    plan_path: str | Path,
    out_dir: str | Path,
    reference_image: str | Path | None = None,
    project_name: str | None = None,
) -> dict[str, Any]:
    plan = load_manifest(plan_path)
    plan.pop("_manifest_path", None)
    validate_component_plan(plan)

    ref_path = abs_path(reference_image) if reference_image else None
    if ref_path and not ref_path.is_file():
        raise click.ClickException(f"Reference image not found: {ref_path}")
    if not ref_path and plan.get("reference_image"):
        ref_path = abs_path(plan["reference_image"])
        if not ref_path.is_file():
            raise click.ClickException(f"Reference image declared in plan not found: {ref_path}")

    out_root = abs_path(out_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    manifest_payload = component_plan_to_workflow_manifest(
        plan,
        reference_image=str(ref_path) if ref_path else None,
        project_name=project_name,
    )
    manifest_path = out_root / "replicate_manifest.yaml"
    write_manifest(manifest_path, manifest_payload)

    tool_plan_path = out_root / "tool_plan.json"
    tool_plan = plan_workflow_manifest(manifest_path, tool_plan_path)

    index = render_workflow_manifest(
        manifest_path,
        out_root,
        source_formats=SUPPORTED_SOURCE_FORMATS,
    )

    workflow_result = index["results"][0]
    workflow_dir = out_root / workflow_result["id"]
    deliverable_dir = workflow_dir / "deliverables"
    assembly_result = workflow_result.get("assembly", {})
    vsdx_status = (assembly_result.get("vsdx_export") or {}).get("status", "not_requested")

    summary = {
        "plan_path": str(abs_path(plan_path)),
        "manifest_path": str(manifest_path),
        "tool_plan_path": str(tool_plan_path),
        "output_dir": str(out_root),
        "workflow_dir": str(workflow_dir),
        "deliverables_dir": str(deliverable_dir),
        "module_count": len(plan["components"]),
        "module_limit": MODULE_LIMIT,
        "reference_image": str(ref_path) if ref_path else None,
        "tool_plan": tool_plan,
        "workflow_result": workflow_result,
        "vsdx_status": vsdx_status,
        "warnings": _collect_warnings(workflow_result),
    }
    write_json(out_root / "replicate_summary.json", summary)
    return summary


def _component_to_stage(component: dict[str, Any]) -> dict[str, Any]:
    backend = str(component["backend"]).lower().strip()
    figure_spec = dict(component.get("figure_spec") or {})
    explicit_kind = str(figure_spec.pop("kind", "")).lower().strip() if figure_spec else ""
    figure_kind = explicit_kind or BACKEND_TO_KIND[backend]
    figure = _default_figure_for_kind(figure_kind, component)
    figure.update(figure_spec)
    figure["id"] = component["id"]
    figure["kind"] = figure_kind
    figure.setdefault("title", component["name"])
    if component.get("box_xyxy") and "box_xyxy" not in figure:
        figure["box_xyxy"] = list(component["box_xyxy"])
    if figure_kind == "svg_module":
        figure.setdefault("shapes", [])
        figure.setdefault("labels", [])
        figure.setdefault("connectors", [])

    return {
        "id": component["id"],
        "tool": TOOL_PROFILES[backend]["tool"],
        "role": component.get("description", ""),
        "figure": figure,
    }


def _default_figure_for_kind(kind: str, component: dict[str, Any]) -> dict[str, Any]:
    name = component.get("name", component["id"])
    inventory = [str(item) for item in component.get("text_inventory", []) or []]
    description = component.get("description", "")

    if kind == "plotneuralnet_cnn":
        return {
            "layers": [
                {"type": "input", "name": "Input", "shape": "K"},
                {"type": "conv", "name": name[:20] or "Block", "shape": "64x64x64"},
                {"type": "conv", "name": "Out", "shape": "32x32x128"},
            ],
        }
    if kind in {"drawio_architecture", "drawio_flow"}:
        nodes = inventory or [name]
        if kind == "drawio_architecture":
            return {
                "lanes": [{"name": name, "nodes": nodes}],
                "edges": [],
            }
        return {
            "nodes": [{"id": _slug(label), "label": label} for label in nodes],
            "edges": [[_slug(a), _slug(b)] for a, b in zip(nodes, nodes[1:])],
        }
    if kind in {"tikz_lstm", "tikz_attention_gate"}:
        return {
            "inputs": ["x_t", "h_{t-1}", "c_{t-1}"],
            "gates": ["f_t", "i_t", "o_t", "\\tilde{c}_t"],
            "outputs": ["h_t", "c_t"],
            "caption": description[:60],
        }
    if kind == "graphviz_graph":
        return {
            "layout": "layered",
            "nodes": [{"id": _slug(name), "label": name, "rank": 0}],
            "edges": [],
        }
    if kind == "svg_module":
        box = component.get("box_xyxy") or [0, 0, 200, 200]
        return {
            "shapes": [],
            "labels": [],
            "connectors": [],
            "box_xyxy": list(box),
        }
    return {}


def _component_to_placement(
    component: dict[str, Any],
    index: int,
    total: int,
    canvas: dict[str, Any],
    reference_size: tuple[int, int] | None,
) -> dict[str, Any]:
    box = component.get("box_xyxy")
    if box and reference_size:
        ref_w, ref_h = reference_size
        cw = canvas["width"] / ref_w
        ch = canvas["height"] / ref_h
        x = box[0] * cw
        y = box[1] * ch
        width = max(40.0, (box[2] - box[0]) * cw)
        height = max(40.0, (box[3] - box[1]) * ch)
    elif box:
        x, y = float(box[0]), float(box[1])
        width = max(40.0, float(box[2] - box[0]))
        height = max(40.0, float(box[3] - box[1]))
    else:
        x, y, width, height = _grid_placement(index, total, canvas)

    return {
        "x": round(x, 2),
        "y": round(y, 2),
        "width": round(width, 2),
        "height": round(height, 2),
        "opacity": 0.98,
        "label": component.get("name", component["id"]),
    }


def _scaled_box(
    box: list | None,
    canvas: dict[str, Any],
    reference_size: tuple[int, int] | None,
) -> tuple[float, float, float, float] | None:
    if box is None:
        return None
    if reference_size:
        ref_w, ref_h = reference_size
        cw = canvas["width"] / ref_w
        ch = canvas["height"] / ref_h
        return (box[0] * cw, box[1] * ch, box[2] * cw, box[3] * ch)
    return (float(box[0]), float(box[1]), float(box[2]), float(box[3]))


def _grid_anchor(index: int, total: int, canvas: dict[str, Any]) -> tuple[float, float, float, float]:
    x, y, w, h = _grid_placement(index, total, canvas)
    return (x, y, x + w, y + h)


def _grid_placement(index: int, total: int, canvas: dict[str, Any]) -> tuple[float, float, float, float]:
    cols = max(1, math.ceil(math.sqrt(total)))
    rows = max(1, math.ceil(total / cols))
    pad_x = 60
    pad_y = 80
    cell_w = (canvas["width"] - pad_x * (cols + 1)) / cols
    cell_h = (canvas["height"] - pad_y * (rows + 1)) / rows
    col = index % cols
    row = index // cols
    x = pad_x + col * (cell_w + pad_x)
    y = pad_y + row * (cell_h + pad_y)
    return x, y, cell_w, cell_h


def _build_global_connectors(
    connectors: list[dict[str, Any]],
    placements: list[dict[str, Any]],
    box_anchors: dict[str, tuple[float, float, float, float]] | None = None,
) -> list[dict[str, Any]]:
    if not connectors:
        return []
    placement_index = {placement["asset"]: placement for placement in placements}
    box_anchors = box_anchors or {}
    rendered: list[dict[str, Any]] = []
    for connector in connectors:
        src_id = connector.get("from")
        tgt_id = connector.get("to")
        source_anchor = _resolve_anchor(src_id, placement_index, box_anchors)
        target_anchor = _resolve_anchor(tgt_id, placement_index, box_anchors)
        if not source_anchor or not target_anchor:
            continue
        sx, sy, tx, ty = _edge_to_edge_points(source_anchor, target_anchor)
        marker = connector.get("marker") or _marker_for_color(connector.get("color", ""))
        rendered.append(
            {
                "points": [[sx, sy], [tx, ty]],
                "color": connector.get("color", "#4f8f8a"),
                "width": float(connector.get("width", 2.0)),
                "dash": "6,4" if str(connector.get("style", "")).lower() == "dashed" else None,
                "label": connector.get("label", ""),
                "marker": marker,
                "opacity": float(connector.get("opacity", 1.0)),
            }
        )
    return rendered


def _resolve_anchor(
    component_id: str | None,
    placement_index: dict[str, dict[str, Any]],
    box_anchors: dict[str, tuple[float, float, float, float]],
) -> tuple[float, float, float, float] | None:
    if not component_id:
        return None
    if component_id in placement_index:
        placement = placement_index[component_id]
        return (
            placement["x"],
            placement["y"],
            placement["x"] + placement["width"],
            placement["y"] + placement["height"],
        )
    return box_anchors.get(component_id)


def _edge_to_edge_points(
    source: tuple[float, float, float, float],
    target: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    scx = (source[0] + source[2]) / 2
    scy = (source[1] + source[3]) / 2
    tcx = (target[0] + target[2]) / 2
    tcy = (target[1] + target[3]) / 2
    if tcy > source[3]:
        sx, sy = scx, source[3]
    elif tcy < source[1]:
        sx, sy = scx, source[1]
    elif tcx > source[2]:
        sx, sy = source[2], scy
    else:
        sx, sy = source[0], scy
    if scy < target[1]:
        tx, ty = tcx, target[1]
    elif scy > target[3]:
        tx, ty = tcx, target[3]
    elif scx < target[0]:
        tx, ty = target[0], tcy
    else:
        tx, ty = target[2], tcy
    return sx, sy, tx, ty


def _marker_for_color(color: str) -> str:
    color = (color or "").lower()
    if color.startswith("#ff") or "ff20" in color or color in {"red", "#ff0000"}:
        return "arrow-red"
    if color.startswith("#12") or color in {"blue", "#1287cf"} or color.startswith("#22") and "aa" not in color:
        return "arrow-blue"
    if color.startswith("#75") or color in {"cyan", "#75c5de"}:
        return "arrow-cyan"
    if color.startswith("#4f") or color.startswith("#22aa") or color in {"green", "#22aa44"}:
        return "arrow-teal"
    if color.startswith("#cc") or color.startswith("#aa") or "magenta" in color or "pink" in color:
        return "arrow-black"
    return "arrow-black"


def _handoff_steps(components: list[dict[str, Any]]) -> list[str]:
    backends = {component["backend"] for component in components}
    steps: list[str] = []
    if "plotneuralnet" in backends:
        steps.append("Stage A: PlotNeuralNet generates 3D feature-map assets.")
    if "tikz" in backends:
        steps.append("Stage B: TikZ generates math/cell insets.")
    if "graphviz" in backends:
        steps.append("Stage C: Graphviz lays out node-link skeletons.")
    if "image_to_image" in backends:
        steps.append("Stage D: Image-to-image fallback for transparent raster assets that cannot be vectorized.")
    steps.append("Stage E: Draw.io master assembly imports each asset and owns final layout, connectors, and export.")
    return steps


def _reference_size(path: str | Path) -> tuple[int, int] | None:
    try:
        from PIL import Image
    except Exception:
        return None
    try:
        with Image.open(path) as image:
            return image.size
    except Exception:
        return None


def _collect_warnings(workflow_result: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    assembly = workflow_result.get("assembly", {}) or {}
    vsdx_export = assembly.get("vsdx_export") or {}
    if vsdx_export.get("status") in {"unavailable", "skipped"}:
        warnings.append(
            "VSDX export unavailable; install draw.io Desktop and ensure `cli-anything-drawio` is on PATH to enable .vsdx."
        )
    deliverables = assembly.get("deliverables", {}) or {}
    for missing in deliverables.get("missing", []) or []:
        warnings.append(f"Requested source format '{missing}' is missing from deliverables.")
    return warnings


def _slug(value: str) -> str:
    cleaned = []
    for ch in str(value).lower().strip():
        if ch.isalnum():
            cleaned.append(ch)
        elif ch in {" ", "-", "_", "/"}:
            cleaned.append("_")
    slug = "".join(cleaned).strip("_")
    return slug or "component"
