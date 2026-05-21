"""Generate a high-fidelity LeNet-5 replica plan.

The plan targets the 1428x762 reference image
``a8793e5d285acb2b03230165418da744.png``. The high-density figure is split into
specialist atomic assets: PlotNeuralNet compact stacks for the 3D feature maps,
Graphviz for the full-connection node network, and standalone SVG modules for
strict pixel-grid insets. The Draw.io master only imports those placements,
owns the cross-module connectors, and carries the global operation labels.

Run::

    python examples/build_lenet_hifi_plan.py
    python -m ai_diagram_factory.cli replicate \
        --plan examples/lenet5_hifi_plan.json \
        --reference C:/Users/86180/Desktop/a8793e5d285acb2b03230165418da744.png \
        --out-dir E:/多软件协作/ai-diagram-factory/outputs/lenet5_hifi
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CANVAS_W = 1428
CANVAS_H = 762
PLAN_PATH = Path(__file__).resolve().parent / "lenet5_hifi_plan.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def grid_outline(x: float, y: float, cell: float, cols: int, rows: int, stroke: str = "#222222", stroke_width: float = 1.2, fill: str = "#ffffff") -> list[dict[str, Any]]:
    width = cell * cols
    height = cell * rows
    shapes: list[dict[str, Any]] = [
        {"type": "rect", "x": x, "y": y, "width": width, "height": height, "fill": fill, "stroke": stroke, "stroke_width": stroke_width},
    ]
    for c in range(1, cols):
        cx = x + c * cell
        shapes.append({"type": "line", "x1": cx, "y1": y, "x2": cx, "y2": y + height, "stroke": stroke, "stroke_width": stroke_width})
    for r in range(1, rows):
        cy = y + r * cell
        shapes.append({"type": "line", "x1": x, "y1": cy, "x2": x + width, "y2": cy, "stroke": stroke, "stroke_width": stroke_width})
    return shapes


def cell_fill(grid_x: float, grid_y: float, cell: float, col: int, row: int, fill: str, opacity: float = 1.0) -> dict[str, Any]:
    return {
        "type": "rect",
        "x": grid_x + col * cell,
        "y": grid_y + row * cell,
        "width": cell,
        "height": cell,
        "fill": fill,
        "stroke": "#222222",
        "stroke_width": 1.0,
        "opacity": opacity,
    }


def dashed_path(x1: float, y1: float, x2: float, y2: float, color: str, width: float = 1.6) -> dict[str, Any]:
    return {
        "type": "path",
        "d": f"M {x1} {y1} L {x2} {y2}",
        "fill": "none",
        "stroke": color,
        "stroke_width": width,
        "dash": "5,4",
        "opacity": 1.0,
    }


def label(x: float, y: float, text: str, size: int = 16, weight: str = "400", anchor: str = "middle", fill: str = "#222222", rotate: float | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"x": x, "y": y, "text": text, "size": size, "weight": weight, "anchor": anchor, "fill": fill}
    if rotate is not None:
        payload["rotate"] = rotate
    return payload


def feature_stack_shape(x: float, y: float, width: float, height: float, count: int, step_x: float, step_y: float, fill: str = "#a8a8a8", stroke: str = "#444444") -> dict[str, Any]:
    return {
        "type": "feature_stack",
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "count": count,
        "step_x": step_x,
        "step_y": step_y,
        "fill": fill,
        "stroke": stroke,
        "stroke_width": 1.0,
        "opacity": 1.0,
        "rx": 0,
    }


def svg_component(*, id: str, name: str, description: str, box_xyxy: list[float], shapes: list[dict[str, Any]], labels: list[dict[str, Any]] | None = None, connectors: list[dict[str, Any]] | None = None, text_inventory: list[str] | None = None) -> dict[str, Any]:
    return {
        "id": id,
        "name": name,
        "backend": "svg",
        "description": description,
        "box_xyxy": box_xyxy,
        "text_inventory": text_inventory or [],
        "figure_spec": {
            "shapes": shapes,
            "labels": labels or [],
            "connectors": connectors or [],
            "hide_label": True,
        },
    }


def plot_stack_component(
    *,
    id: str,
    name: str,
    description: str,
    box_xyxy: list[float],
    count: int,
    face_width_mm: float,
    face_height_mm: float,
    step_mm: float,
    overlays: list[dict[str, Any]] | None = None,
    text_inventory: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": id,
        "name": name,
        "backend": "plotneuralnet",
        "description": description,
        "box_xyxy": box_xyxy,
        "text_inventory": text_inventory or [],
        "features": ["3d", "feature map", "stack", "plotneuralnet"],
        "figure_spec": {
            "compact": True,
            "count": count,
            "face_width_mm": face_width_mm,
            "face_height_mm": face_height_mm,
            "step_mm": step_mm,
            "depth_x_mm": step_mm * 0.9,
            "depth_y_mm": step_mm * 0.65,
            "fill": "black!34",
            "top_fill": "black!20",
            "side_fill": "black!45",
            "stroke": "black!80",
            "line_width_mm": 0.22,
            "overlays": overlays or [],
            "hide_label": True,
        },
    }


# ---------------------------------------------------------------------------
# Module builders (all coordinates are LOCAL to the module bounding box)
# ---------------------------------------------------------------------------


def build_input_module() -> dict[str, Any]:
    # Canvas box: (40, 100) -> (280, 380). Local size: 240 x 280.
    box = [40, 100, 280, 380]
    shapes: list[dict[str, Any]] = [
        {"type": "rect", "x": 10, "y": 10, "width": 220, "height": 240, "fill": "#cccccc", "stroke": "#444", "stroke_width": 1.6},
        {"type": "path", "d": "M 60 220 L 120 45 L 180 220 M 80 160 L 160 160", "fill": "none", "stroke": "#111", "stroke_width": 14},
        {"type": "rect", "x": 18, "y": 190, "width": 42, "height": 42, "fill": "#ff2020", "stroke": "#ff2020", "stroke_width": 2.6, "opacity": 0.25},
        {"type": "rect", "x": 18, "y": 190, "width": 42, "height": 42, "fill": "none", "stroke": "#ff2020", "stroke_width": 2.6},
    ]
    return svg_component(
        id="01_input_32x32",
        name="INPUT 32x32",
        description="Gray 32x32 input plane with handwritten A and red source-pixel box.",
        box_xyxy=box,
        shapes=shapes,
        text_inventory=["INPUT", "32x32"],
    )


def build_c1_module() -> dict[str, Any]:
    # Canvas box: (275, 30) -> (540, 350). Local size: 265 x 320.
    box = [275, 30, 540, 350]
    overlays = [
        {"x": 7.0, "y": 13.0, "width": 2.6, "height": 2.6, "color": "green!70!black", "mode": "outline", "line_width_mm": 0.34},
        {"x": 18.5, "y": 1.8, "width": 1.4, "height": 1.4, "color": "red", "mode": "filled", "line_width_mm": 0.18},
    ]
    return plot_stack_component(
        id="02_c1_feature_maps",
        name="C1: feature maps 6@28x28",
        description="Stack of 6 28x28 feature maps after a 5x5 convolution, with green selected and red output cells.",
        box_xyxy=box,
        count=6,
        face_width_mm=30,
        face_height_mm=30,
        step_mm=1.65,
        overlays=overlays,
        text_inventory=["C1: feature maps", "6@28x28"],
    )


def build_s2_module() -> dict[str, Any]:
    # Canvas box: (470, 80) -> (700, 350). Local size: 230 x 270.
    box = [470, 80, 700, 350]
    overlays = [
        {"x": 16.5, "y": 8.5, "width": 3.6, "height": 3.6, "color": "blue", "mode": "translucent", "opacity": 0.24, "line_width_mm": 0.32},
        {"x": 10.0, "y": 4.4, "width": 1.0, "height": 1.0, "color": "green!70!black", "mode": "filled", "line_width_mm": 0.16},
    ]
    return plot_stack_component(
        id="03_s2_feature_maps",
        name="S2: f. maps 6@14x14",
        description="Stack of 6 14x14 maps after 2x2 subsampling, with green output cell and blue C3 receptive-field square.",
        box_xyxy=box,
        count=6,
        face_width_mm=25,
        face_height_mm=25,
        step_mm=1.45,
        overlays=overlays,
        text_inventory=["S2: f. maps", "6@14x14"],
    )


def build_c3_module() -> dict[str, Any]:
    # Canvas box: (650, 8) -> (920, 360). Local size: 270 x 352.
    box = [650, 8, 920, 360]
    overlays = [
        {"x": 12.6, "y": 12.8, "width": 1.1, "height": 1.1, "color": "blue", "mode": "filled", "line_width_mm": 0.16},
    ]
    return plot_stack_component(
        id="04_c3_feature_maps",
        name="C3: f. maps 16@10x10",
        description="Stack of 16 10x10 maps after 3x3 convolution, with a small blue target cell.",
        box_xyxy=box,
        count=16,
        face_width_mm=26,
        face_height_mm=26,
        step_mm=0.92,
        overlays=overlays,
        text_inventory=["C3: f. maps 16@10x10"],
    )


def build_s4_module() -> dict[str, Any]:
    # Canvas box: (880, 75) -> (1090, 360). Local size: 210 x 285.
    box = [880, 75, 1090, 360]
    overlays = [
        {"x": 8.3, "y": 11.0, "width": 1.1, "height": 1.1, "color": "green!70!black", "mode": "outline", "line_width_mm": 0.24},
        {"x": 14.3, "y": 6.0, "width": 3.0, "height": 3.0, "color": "magenta", "mode": "translucent", "opacity": 0.24, "line_width_mm": 0.28},
    ]
    return plot_stack_component(
        id="05_s4_feature_maps",
        name="S4: f. maps 16@5x5",
        description="Stack of 16 5x5 maps after 2x2 subsampling, with green inner and magenta source-cell markers.",
        box_xyxy=box,
        count=16,
        face_width_mm=22,
        face_height_mm=22,
        step_mm=0.75,
        overlays=overlays,
        text_inventory=["S4: f. maps 16@5x5"],
    )


def slant_band(top_x: float, top_y: float, width: float, height: float, skew: float, fill: str = "#5e5e5e", stroke: str = "#222") -> dict[str, Any]:
    points = [
        (top_x, top_y),
        (top_x + width, top_y),
        (top_x + width - skew, top_y + height),
        (top_x - skew, top_y + height),
    ]
    d = "M " + " L ".join(f"{px:.2f} {py:.2f}" for px, py in points) + " Z"
    return {"type": "path", "d": d, "fill": fill, "stroke": stroke, "stroke_width": 1.4, "opacity": 1.0}


def build_c5_f6_output_module() -> dict[str, Any]:
    # Canvas box: (1070, 80) -> (1335, 380). Local size: 265 x 300.
    box = [1070, 80, 1335, 380]
    skew = 55
    band_y = 50
    band_h = 230
    band_w = 38
    bands = [
        slant_band(80, band_y, band_w, band_h, skew),  # C5 layer
        slant_band(160, band_y, band_w, band_h, skew),  # F6 layer
        slant_band(240, band_y, band_w, band_h, skew),  # OUTPUT
    ]
    top_line = {
        "type": "path",
        "d": f"M 80 {band_y} L 240 {band_y - 14}",
        "fill": "none",
        "stroke": "#111",
        "stroke_width": 1.2,
        "opacity": 0.85,
    }
    shapes: list[dict[str, Any]] = bands + [top_line]
    digit_labels: list[dict[str, Any]] = []
    digits = list("0123456789")
    base_x = 230
    base_y = 90
    for index, digit in enumerate(digits):
        digit_labels.append(label(base_x + index * 4, base_y + index * 12, digit, size=18, weight="600", fill="#cc1111"))
    labels = [
        label(78, 18, "C5: layer", size=16, weight="500"),
        label(78, 38, "120", size=17, weight="500"),
        label(158, 18, "F6: layer", size=16, weight="500"),
        label(158, 38, "84", size=17, weight="500"),
        label(228, 18, "OUTPUT", size=16, weight="500"),
        label(228, 38, "10", size=17, weight="500"),
        *digit_labels,
    ]
    return svg_component(
        id="06_c5_f6_output_bands",
        name="C5/F6/OUTPUT bands",
        description="Three slanted gray bands C5(120), F6(84), OUTPUT(10) with thin top connection line and red diagonal class digits 0..9.",
        box_xyxy=box,
        shapes=shapes,
        labels=labels,
        text_inventory=["C5: layer", "120", "F6: layer", "84", "OUTPUT", "10", *digits],
    )


def build_conv_5x5_inset() -> dict[str, Any]:
    # Canvas box: (20, 460) -> (400, 750). Local size: 380 x 290.
    box = [20, 460, 400, 750]
    cell = 31
    grid_x = 0
    grid_y = 20
    shapes = grid_outline(grid_x, grid_y, cell, 7, 7, stroke="#222", stroke_width=1.2)
    shapes.append({"type": "rect", "x": grid_x, "y": grid_y, "width": cell * 5, "height": cell * 5, "fill": "#1287cf", "stroke": "#1287cf", "stroke_width": 3.0, "opacity": 0.18})
    shapes.append({"type": "rect", "x": grid_x, "y": grid_y, "width": cell * 5, "height": cell * 5, "fill": "none", "stroke": "#1287cf", "stroke_width": 3.0})
    shapes.append({"type": "rect", "x": grid_x + cell, "y": grid_y + cell, "width": cell * 5, "height": cell * 5, "fill": "#ff2020", "stroke": "#ff2020", "stroke_width": 3.0, "opacity": 0.20})
    shapes.append({"type": "rect", "x": grid_x + cell, "y": grid_y + cell, "width": cell * 5, "height": cell * 5, "fill": "none", "stroke": "#ff2020", "stroke_width": 3.0})

    out_x = 280
    out_y = 105
    out_cell = 22
    shapes.extend(grid_outline(out_x, out_y, out_cell, 3, 3, stroke="#222"))
    shapes.append(cell_fill(out_x, out_y, out_cell, 2, 1, "#ee2020"))
    shapes.append(cell_fill(out_x, out_y, out_cell, 0, 0, "#1287cf"))
    shapes.append(dashed_path(grid_x + 5 * cell, grid_y + cell * 2, out_x + out_cell * 0.5, out_y + out_cell * 0.5, "#1287cf", width=1.8))
    shapes.append(dashed_path(grid_x + cell + 5 * cell, grid_y + cell + cell * 2.5, out_x + out_cell * 2.5, out_y + out_cell * 1.5, "#ee2020", width=1.8))
    return svg_component(
        id="07_conv_5x5_inset",
        name="5x5 convolution inset",
        description="7x7 input grid with overlapping blue/red 5x5 windows; dashed guides to a 3x3 output grid with red and blue output cells.",
        box_xyxy=box,
        shapes=shapes,
        text_inventory=["Convolutions", "5x5"],
    )


def build_subsampling_2x2_inset() -> dict[str, Any]:
    # Canvas box: (400, 530) -> (645, 740). Local size: 245 x 210.
    box = [400, 530, 645, 740]
    cell = 32
    grid_x = 15
    grid_y = 25
    shapes = grid_outline(grid_x, grid_y, cell, 3, 3, stroke="#222")
    shapes.append({"type": "rect", "x": grid_x, "y": grid_y, "width": cell * 2, "height": cell * 2, "fill": "#22aa44", "stroke": "#22aa44", "stroke_width": 2.6, "opacity": 0.22})
    shapes.append({"type": "rect", "x": grid_x, "y": grid_y, "width": cell * 2, "height": cell * 2, "fill": "none", "stroke": "#22aa44", "stroke_width": 2.6})

    out_x = 155
    out_y = 70
    out_cell = 22
    shapes.extend(grid_outline(out_x, out_y, out_cell, 3, 3, stroke="#222"))
    shapes.append(cell_fill(out_x, out_y, out_cell, 0, 0, "#22aa44"))
    shapes.append(dashed_path(grid_x + cell * 2, grid_y, out_x + out_cell * 0.5, out_y + out_cell * 0.5, "#22aa44", width=1.8))
    shapes.append(dashed_path(grid_x + cell * 2, grid_y + cell * 2, out_x + out_cell * 0.5, out_y + out_cell * 0.5, "#22aa44", width=1.8))
    return svg_component(
        id="08_subsampling_2x2_inset",
        name="2x2 subsampling inset",
        description="3x3 input grid with green 2x2 window; dashed guides to a 3x3 output grid with a single green cell.",
        box_xyxy=box,
        shapes=shapes,
        text_inventory=["Subsampling", "2x2"],
    )


def build_conv_3x3_inset() -> dict[str, Any]:
    # Canvas box: (640, 510) -> (950, 760). Local size: 310 x 250.
    box = [640, 510, 950, 760]
    cell = 30
    grid_x = 15
    grid_y = 35
    shapes = grid_outline(grid_x, grid_y, cell, 5, 5, stroke="#222")
    shapes.append({"type": "rect", "x": grid_x, "y": grid_y, "width": cell * 3, "height": cell * 3, "fill": "#f4d72a", "stroke": "#f4d72a", "stroke_width": 3.0, "opacity": 0.32})
    shapes.append({"type": "rect", "x": grid_x, "y": grid_y, "width": cell * 3, "height": cell * 3, "fill": "none", "stroke": "#f4d72a", "stroke_width": 3.0})
    shapes.append({"type": "rect", "x": grid_x + cell, "y": grid_y + cell, "width": cell * 3, "height": cell * 3, "fill": "#1287cf", "stroke": "#1287cf", "stroke_width": 3.0, "opacity": 0.22})
    shapes.append({"type": "rect", "x": grid_x + cell, "y": grid_y + cell, "width": cell * 3, "height": cell * 3, "fill": "none", "stroke": "#1287cf", "stroke_width": 3.0})

    out_x = 205
    out_y = 90
    out_cell = 22
    shapes.extend(grid_outline(out_x, out_y, out_cell, 3, 3, stroke="#222"))
    shapes.append(cell_fill(out_x, out_y, out_cell, 0, 0, "#f4d72a"))
    shapes.append(cell_fill(out_x, out_y, out_cell, 1, 1, "#1287cf"))
    shapes.append(dashed_path(grid_x + cell * 3, grid_y, out_x + out_cell * 0.5, out_y + out_cell * 0.5, "#d4ba1e", width=1.8))
    shapes.append(dashed_path(grid_x + cell + cell * 3, grid_y + cell + cell * 1.5, out_x + out_cell * 1.5, out_y + out_cell * 1.5, "#1287cf", width=1.8))
    return svg_component(
        id="09_conv_3x3_inset",
        name="3x3 convolution inset",
        description="5x5 input grid with overlapping yellow/blue 3x3 windows; dashed guides to a 3x3 output grid with yellow and blue cells.",
        box_xyxy=box,
        shapes=shapes,
        text_inventory=["Convolutions", "3x3"],
    )


def build_c5_source_grid() -> dict[str, Any]:
    # Canvas box: (950, 540) -> (1120, 740). Local size: 170 x 200.
    box = [950, 540, 1120, 740]
    cell = 28
    shapes = grid_outline(30, 30, cell, 5, 5, stroke="#cc33cc", stroke_width=2.4, fill="#f7d6f7")
    return svg_component(
        id="10_c5_source_grid",
        name="C5 source 5x5 grid",
        description="Magenta-bordered 5x5 cell grid representing the C5 source patch on S4. The 'Full connection' caption is on the Draw.io master, not inside this SVG.",
        box_xyxy=box,
        shapes=shapes,
        text_inventory=[],
    )


def build_fc_network_module() -> dict[str, Any]:
    # Canvas box: (1100, 440) -> (1428, 762). Local size: 328 x 322.
    # Auto-laid-out by Graphviz (specialist tool for dense node networks). The
    # external "120 / 84 / 10" blue captions and the "0..9" red class digits
    # are master_labels on the Draw.io master, not inside the Graphviz SVG.
    box = [1100, 440, 1428, 762]
    col_sizes = [12, 12, 10]
    nodes: list[dict[str, Any]] = []
    for col, size in enumerate(col_sizes):
        for row in range(size):
            nodes.append({"id": f"L{col}_{row}", "rank": col, "label": ""})
    edges: list[list[str]] = []
    for s in range(col_sizes[0]):
        for t in range(col_sizes[1]):
            edges.append([f"L0_{s}", f"L1_{t}"])
    for s in range(col_sizes[1]):
        for t in range(col_sizes[2]):
            edges.append([f"L1_{s}", f"L2_{t}"])

    return {
        "id": "11_fc_network",
        "name": "FC 120 -> 84 -> 10",
        "backend": "graphviz",
        "description": "Dense three-rank fully connected node network laid out by Graphviz; the blue layer labels (120/84/10) and the red class digits 0..9 are added on the Draw.io master, not inside this Graphviz SVG.",
        "box_xyxy": box,
        "text_inventory": ["120", "84", "10", *list("0123456789")],
        "figure_spec": {
            "rankdir": "LR",
            "splines": "line",
            "overlap": "false",
            "node_attrs": {
                "shape": "circle",
                "style": "filled",
                "fillcolor": "white",
                "color": "#222222",
                "fixedsize": "true",
                "width": "0.22",
                "height": "0.22",
                "label": "",
                "penwidth": "1.0",
            },
            "edge_attrs": {
                "arrowhead": "none",
                "color": "#444444",
                "penwidth": "0.35",
            },
            "nodes": nodes,
            "edges": edges,
            "hide_label": True,
        },
    }


# ---------------------------------------------------------------------------
# Top-level master labels (operation captions between top row and insets)
# ---------------------------------------------------------------------------


def build_master_labels() -> list[dict[str, Any]]:
    # Draw.io master owns all labels: operation captions between top row and
    # insets, the module titles above each top-row module, FC layer captions,
    # and the red class digits next to the FC right column.
    labels: list[dict[str, Any]] = [
        # Module titles for the top-row CNN skeleton
        label(160, 80, "INPUT", size=18, weight="500"),
        label(160, 100, "32x32", size=18, weight="500"),
        label(405, 20, "C1: feature maps", size=16, weight="500"),
        label(405, 40, "6@28x28", size=16, weight="500"),
        label(585, 60, "S2: f. maps", size=16, weight="500"),
        label(585, 80, "6@14x14", size=16, weight="500"),
        label(800, 15, "C3: f. maps 16@10x10", size=16, weight="500"),
        label(985, 60, "S4: f. maps 16@5x5", size=16, weight="500"),
        # Operation labels between top row and bottom row
        label(395, 410, "Convolutions", size=20, weight="500"),
        label(395, 436, "5x5", size=22, weight="600", fill="#1287cf"),
        label(560, 410, "Subsampling", size=20, weight="500"),
        label(560, 436, "2x2", size=22, weight="600", fill="#1287cf"),
        label(770, 410, "Convolutions", size=20, weight="500"),
        label(770, 436, "3x3", size=22, weight="600", fill="#1287cf"),
        label(975, 410, "Subsampling", size=20, weight="500"),
        label(975, 436, "2x2", size=22, weight="600", fill="#1287cf"),
        label(1175, 392, "Full connection", size=18, weight="500"),
        label(1330, 422, "Gaussian connections", size=18, weight="500"),
        # FC layer captions below the Graphviz-laid network (positions match
        # the actual column centers in the Graphviz SVG: cx=8/60/112 in a
        # 103-wide content area, centered inside the 328-wide placement).
        label(1220, 752, "120", size=20, weight="600", fill="#1287cf"),
        label(1272, 752, "84", size=20, weight="600", fill="#1287cf"),
        label(1324, 752, "10", size=20, weight="600", fill="#1287cf"),
    ]
    # Red class digits 0..9 just right of the rightmost Graphviz column
    fc_top_y = 460
    fc_step = 30
    digit_x = 1385
    for index, digit in enumerate("0123456789"):
        labels.append(label(digit_x, fc_top_y + index * fc_step, digit, size=22, weight="600", fill="#cc1111"))
    return labels


# ---------------------------------------------------------------------------
# Plan assembly
# ---------------------------------------------------------------------------


def main() -> None:
    components = [
        build_input_module(),
        build_c1_module(),
        build_s2_module(),
        build_c3_module(),
        build_s4_module(),
        build_c5_f6_output_module(),
        build_conv_5x5_inset(),
        build_subsampling_2x2_inset(),
        build_conv_3x3_inset(),
        build_c5_source_grid(),
        build_fc_network_module(),
    ]

    plan: dict[str, Any] = {
        "project": "lenet5_hifi",
        "source_kind": "image",
        "summary": "High-fidelity LeNet-5 replica: per-module specialist assets (SVG / Graphviz) imported into Draw.io; Draw.io only owns cross-module arrows and global labels.",
        "module_count_rationale": "11 semantic modules: INPUT + four 3D stacks (C1/S2/C3/S4) + C5/F6/OUTPUT bands + four lower insets (5x5 conv, 2x2 sub, 3x3 conv, magenta C5 source) + FC network. Each contains a distinct visual unit; merging any neighboring pair would lose either a colored cross-anchor cell (red/green/blue/magenta) or an operation visualization.",
        "master_title": "",
        "components": components,
        "global_connectors": [
            {"from": "01_input_32x32",      "to": "07_conv_5x5_inset",        "style": "solid", "color": "#ff2020", "width": 2.6},
            {"from": "02_c1_feature_maps",  "to": "08_subsampling_2x2_inset", "style": "solid", "color": "#22aa44", "width": 2.4},
            {"from": "04_c3_feature_maps",  "to": "09_conv_3x3_inset",        "style": "solid", "color": "#1287cf", "width": 2.4},
            {"from": "05_s4_feature_maps",  "to": "10_c5_source_grid",        "style": "solid", "color": "#cc33cc", "width": 2.4},
        ],
        "master_labels": build_master_labels(),
    }
    PLAN_PATH.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {PLAN_PATH}")


if __name__ == "__main__":
    main()
