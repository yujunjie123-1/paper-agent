from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .io import abs_path, load_manifest, write_json


TOOL_PROFILES: dict[str, dict[str, str]] = {
    "plotneuralnet": {
        "tool": "PlotNeuralNet",
        "renderer_kind": "plotneuralnet_cnn",
        "output": "transparent SVG/PNG atomic 3D asset",
        "source": "PlotNeuralNet Python/LaTeX project source",
        "handoff": "Generate the 3D asset first, then import it into Draw.io for final placement.",
    },
    "drawio": {
        "tool": "Draw.io",
        "renderer_kind": "drawio_architecture",
        "output": "editable Draw.io shapes and routed connectors",
        "source": ".drawio or requested Draw.io export format",
        "handoff": "Create or refine directly in the Draw.io master assembly.",
    },
    "tikz": {
        "tool": "TikZ",
        "renderer_kind": "tikz_lstm",
        "output": "crisp vector math/cell inset",
        "source": ".tex source",
        "handoff": "Generate the vector inset first, then import it into Draw.io for final placement.",
    },
    "graphviz": {
        "tool": "Graphviz",
        "renderer_kind": "graphviz_graph",
        "output": "auto-laid-out node-link SVG/PNG asset",
        "source": ".dot source",
        "handoff": "Generate the node layout first, then import it into Draw.io when it is part of the final figure.",
    },
    "image_to_image": {
        "tool": "Image-to-image fallback",
        "renderer_kind": "external_transparent_asset",
        "output": "transparent PNG/SVG-like raster component",
        "source": "prompt plus reference image and generated transparent image",
        "handoff": "Use only when vector/code generation cannot match the reference component, then import into Draw.io.",
    },
    "svg": {
        "tool": "Standalone SVG module",
        "renderer_kind": "svg_module",
        "output": "self-contained editable SVG asset",
        "source": ".svg source",
        "handoff": "Generate the SVG once, then import it into the Draw.io master as a placement; Draw.io only owns cross-module connectors and global labels.",
    },
}


KIND_TO_ROUTE = {
    "plotneuralnet_cnn": "plotneuralnet",
    "drawio_architecture": "drawio",
    "drawio_flow": "drawio",
    "tikz_lstm": "tikz",
    "tikz_attention_gate": "tikz",
    "tikz_module": "tikz",
    "graphviz_graph": "graphviz",
    "svg_module": "svg",
}


DRAWIO_TOKENS = {
    "2d",
    "flat",
    "flow",
    "flowchart",
    "architecture",
    "block",
    "topology",
    "connector",
    "connectors",
    "line",
    "lines",
    "arrow",
    "arrows",
    "label",
    "labels",
    "legend",
    "routing",
    "route",
    "line jump",
    "line jumps",
    "master",
    "assembly",
    "drawio",
    "draw.io",
    "diagrams.net",
    "underlay",
    "trace",
    "reference",
}

THREE_D_TOKENS = {
    "3d",
    "perspective",
    "isometric",
    "feature map",
    "feature-map",
    "stack",
    "stacks",
    "layer stack",
    "conv",
    "convolution",
    "cnn",
    "vgg",
    "alexnet",
    "unet",
    "u-net",
    "plotneuralnet",
}

TIKZ_TOKENS = {
    "tikz",
    "latex",
    "formula",
    "math",
    "gate",
    "gated",
    "lstm",
    "gru",
    "attention gate",
    "cell",
    "notation",
}

GRAPHVIZ_TOKENS = {
    "graphviz",
    "dot",
    "node-link",
    "node link",
    "tree",
    "probabilistic",
    "computation graph",
    "dependency",
    "skeleton",
    "auto-layout",
    "auto layout",
    "circular node",
}

IMAGE_TO_IMAGE_TOKENS = {
    "image-to-image",
    "image2",
    "raster fallback",
    "transparent raster",
    "hard-to-vector",
    "cannot match",
    "non-vector",
}


def plan_workflow_manifest(
    manifest_path: str | Path,
    out_path: str | Path | None = None,
    only_ids: tuple[str, ...] = (),
) -> dict[str, Any]:
    payload = load_manifest(manifest_path)
    plan = build_manifest_plan(payload, only_ids=only_ids)
    if out_path is not None:
        write_json(out_path, plan)
    return plan


def build_manifest_plan(payload: dict[str, Any], only_ids: tuple[str, ...] = ()) -> dict[str, Any]:
    workflows = payload.get("workflows", [])
    if not workflows:
        raise ValueError("Manifest must contain workflows for workflow planning.")
    selected = set(only_ids)
    planned_workflows = []
    for workflow in workflows:
        if selected and workflow.get("id") not in selected:
            continue
        planned_workflows.append(build_workflow_plan(workflow))
    if not planned_workflows:
        raise ValueError("No workflows matched the requested ids.")
    return {
        "manifest": payload.get("_manifest_path", ""),
        "project": payload.get("project", ""),
        "planning_policy": {
            "rule": "Classify components before rendering; generate specialist assets first; assemble and route in Draw.io last.",
            "drawio_owns": "2D topology, labels, legends, connector routing, line jumps, final alignment, and final export.",
            "specialist_assets": "3D stacks use PlotNeuralNet; math/cell insets use TikZ; dense node-link layouts use Graphviz.",
            "fallback": "Image-to-image is allowed only for transparent component assets when vector generation cannot match the reference.",
        },
        "workflows": planned_workflows,
    }


def build_workflow_plan(workflow: dict[str, Any]) -> dict[str, Any]:
    declared = workflow.get("planning", {})
    components = list(declared.get("components", [])) or _infer_components(workflow)
    planned_components = [classify_component(component) for component in components]
    counts = Counter(component["assignment"]["route"] for component in planned_components)
    return {
        "workflow_id": workflow.get("id", ""),
        "title": workflow.get("title", workflow.get("id", "")),
        "objective": workflow.get("objective", ""),
        "strategy": declared.get(
            "strategy",
            "Plan first, generate specialist atomic assets, then assemble and route the final figure in Draw.io.",
        ),
        "components": planned_components,
        "summary": {
            "plotneuralnet_assets": counts.get("plotneuralnet", 0),
            "drawio_tasks": counts.get("drawio", 0),
            "tikz_assets": counts.get("tikz", 0),
            "graphviz_assets": counts.get("graphviz", 0),
            "image_to_image_fallbacks": counts.get("image_to_image", 0),
        },
        "handoff_order": _handoff_order(planned_components),
        "quality_gate": [
            "Do not render the full figure as one hard-coded SVG when multiple tools are assigned.",
            "All connector-heavy or label-heavy work must remain editable in Draw.io.",
            "Compare every generated 3D asset against the reference before final Draw.io assembly.",
            "If the vector asset remains visibly off after tuning, replace only that component with a transparent image-to-image asset.",
        ],
    }


def classify_component(component: dict[str, Any]) -> dict[str, Any]:
    route, confidence, reason = _choose_route(component)
    profile = TOOL_PROFILES[route]
    component_kind = str(component.get("kind", "") or component.get("figure_kind", "")).lower()
    renderer_kind = component.get("renderer_kind") or (component_kind if component_kind in KIND_TO_ROUTE else profile["renderer_kind"])
    result = dict(component)
    result["assignment"] = {
        "route": route,
        "tool": profile["tool"],
        "renderer_kind": renderer_kind,
        "output": profile["output"],
        "editable_source": profile["source"],
        "handoff": profile["handoff"],
        "confidence": confidence,
        "reason": reason,
        "final_assembly": "Draw.io",
    }
    return result


def _choose_route(component: dict[str, Any]) -> tuple[str, str, str]:
    declared_backend = str(component.get("backend", "")).lower().strip()
    if declared_backend in TOOL_PROFILES:
        return declared_backend, "declared", "Component plan explicitly assigned this backend."

    explicit = str(component.get("preferred_route", "") or component.get("route", "")).lower().strip()
    if explicit in TOOL_PROFILES:
        return explicit, "declared", "The component declares an explicit route."

    kind = str(component.get("kind", "") or component.get("figure_kind", "") or component.get("renderer_kind", "")).lower()
    if kind in KIND_TO_ROUTE:
        return KIND_TO_ROUTE[kind], "high", f"The renderer kind is {kind}."

    text = _component_text(component)
    features = _feature_set(component)
    if features & {"drawio", "master", "assembly", "connector", "connectors", "routing", "legend", "labels", "2d", "topology"} and not (
        features & {"3d", "plotneuralnet", "feature map", "feature-map"}
    ):
        return "drawio", "high", "The declared component features make this a Draw.io assembly or editable 2D task."
    if features & {"3d", "plotneuralnet", "feature map", "feature-map", "stack", "stacks"}:
        return "plotneuralnet", "high", "The declared component features identify a 3D feature-map asset."
    if _contains_any(text, IMAGE_TO_IMAGE_TOKENS):
        return "image_to_image", "medium", "The component is marked as a transparent raster fallback."
    if _contains_any(text, THREE_D_TOKENS) and not _contains_any(text, {"master", "assembly", "connector", "connectors", "routing", "line jump", "line jumps"}):
        return "plotneuralnet", "high", "The component is a 3D convolutional or feature-map stack."
    if _contains_any(text, DRAWIO_TOKENS):
        return "drawio", "high", "The component is connector-, label-, layout-, or 2D-topology-heavy."
    if _contains_any(text, TIKZ_TOKENS):
        return "tikz", "high", "The component is math-, notation-, or gated-cell-heavy."
    if _contains_any(text, GRAPHVIZ_TOKENS):
        return "graphviz", "high", "The component is a node-link graph or auto-layout dependency structure."
    return "drawio", "low", "No specialist feature was detected, so Draw.io is the safest editable default."


def _infer_components(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    components: list[dict[str, Any]] = []
    for stage in workflow.get("stages", []):
        figure = stage.get("figure", {})
        components.append(
            {
                "id": stage.get("id", figure.get("id", "stage")),
                "name": figure.get("title", stage.get("role", stage.get("id", "stage"))),
                "source": "stage",
                "role": stage.get("role", ""),
                "tool_hint": stage.get("tool", ""),
                "kind": figure.get("kind", stage.get("kind", "")),
                "description": f"{stage.get('tool', '')} {stage.get('role', '')} {figure.get('title', '')}",
            }
        )
    assembly = workflow.get("assembly", {})
    if assembly.get("reference"):
        components.append(
            {
                "id": "reference_underlay",
                "name": "Locked reference underlay",
                "source": "assembly",
                "description": "Reference image trace underlay locked in Draw.io.",
            }
        )
    if assembly.get("shapes"):
        components.append(
            {
                "id": "editable_shapes",
                "name": "Editable 2D assembly shapes",
                "source": "assembly",
                "description": "Flat modules, legends, labels, and manually aligned layout shapes.",
            }
        )
    if assembly.get("connectors"):
        components.append(
            {
                "id": "routed_connectors",
                "name": "Final routed connectors",
                "source": "assembly",
                "description": "Arrow direction, line routing, line jumps, and connector cleanup.",
            }
        )
    components.append(
        {
            "id": "drawio_master_assembly",
            "name": "Draw.io master assembly",
            "source": "assembly",
            "description": "Final assembly imports specialist assets and owns final export.",
        }
    )
    return components


def _handoff_order(components: list[dict[str, Any]]) -> list[str]:
    active = {component["assignment"]["route"] for component in components}
    order = []
    if "plotneuralnet" in active:
        order.append("1. Generate and tune PlotNeuralNet 3D assets as transparent SVG/PNG components.")
    if "tikz" in active:
        order.append("2. Generate TikZ math/cell insets as vector assets.")
    if "graphviz" in active:
        order.append("3. Generate Graphviz node-link or dependency skeleton assets when needed.")
    if "image_to_image" in active:
        order.append("4. Generate transparent image-to-image fallback components only for shapes that cannot be matched as vectors.")
    order.append("5. Import all specialist assets into the Draw.io master canvas.")
    order.append("6. Build 2D modules, labels, legends, connector routing, line jumps, and final alignment in Draw.io.")
    order.append("7. Export PNG plus only the source format requested by the user.")
    return order


def _component_text(component: dict[str, Any]) -> str:
    values: list[str] = []
    for key in ("id", "name", "title", "source", "role", "tool", "tool_hint", "kind", "figure_kind", "renderer_kind", "description", "visual_family"):
        value = component.get(key)
        if value:
            values.append(str(value))
    for key in ("features", "tags", "contains"):
        value = component.get(key, [])
        if isinstance(value, list):
            values.extend(str(item) for item in value)
        elif value:
            values.append(str(value))
    return " ".join(values).lower()


def _feature_set(component: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for key in ("features", "tags", "contains"):
        value = component.get(key, [])
        if isinstance(value, list):
            result.update(str(item).lower().strip() for item in value)
        elif value:
            result.add(str(value).lower().strip())
    return result


def _contains_any(text: str, tokens: set[str]) -> bool:
    return any(token in text for token in tokens)
