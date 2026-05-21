from __future__ import annotations

import base64
import json
import math
import os
import subprocess
from argparse import ArgumentParser, Namespace
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = (PROJECT_ROOT / "outputs" / "lenet5_divide_conquer").resolve()
STAGES_DIR = (OUTPUT_ROOT / "stages").resolve()
DELIVERABLES_DIR = (OUTPUT_ROOT / "deliverables").resolve()
REFERENCE_IMAGE = Path(r"C:\Users\86180\Desktop\a8793e5d285acb2b03230165418da744.png")
PYTHON312 = Path(r"C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe")
NEATO_EXE = Path(r"C:\Program Files\Graphviz\bin\neato.exe")
DEFAULT_COMPONENT_PLAN = PROJECT_ROOT / "examples" / "lenet5_component_plan.json"
COMPONENT_PLAN_PATH = DEFAULT_COMPONENT_PLAN


def main() -> None:
    configure_from_args(parse_args())
    STAGES_DIR.mkdir(parents=True, exist_ok=True)
    DELIVERABLES_DIR.mkdir(parents=True, exist_ok=True)

    top_dir = STAGES_DIR / "top_skeleton_plotneuralnet"
    grid_dir = STAGES_DIR / "micro_grid_drawio_table"
    fc_dir = STAGES_DIR / "full_connection_graphviz"
    slices_dir = STAGES_DIR / "reference_slices"
    declarations_dir = STAGES_DIR / "structured_declarations"
    for folder in (top_dir, grid_dir, fc_dir, slices_dir, declarations_dir):
        folder.mkdir(parents=True, exist_ok=True)

    top_svg = top_dir / "lenet5_top_skeleton.svg"
    top_project = top_dir / "lenet5_top_skeleton.plotneuralnet.json"
    top_tex = top_dir / "lenet5_top_skeleton.tex"
    top_png = top_dir / "lenet5_top_skeleton.png"
    grid_svg = grid_dir / "lenet5_micro_grid.svg"
    grid_png = grid_dir / "lenet5_micro_grid.png"
    fc_dot = fc_dir / "lenet5_full_connection.dot"
    fc_svg = fc_dir / "lenet5_full_connection.svg"
    fc_png = fc_dir / "lenet5_full_connection.png"
    declarations_json = declarations_dir / "lenet5_structured_declarations.json"
    prompts_md = declarations_dir / "lenet5_local_ai_prompts.md"
    review_checklist_md = declarations_dir / "lenet5_detail_review_checklist.md"
    master_drawio = DELIVERABLES_DIR / "lenet5_divide_conquer_master.drawio"
    master_png = DELIVERABLES_DIR / "lenet5_divide_conquer_master.png"

    component_plan = load_component_plan(COMPONENT_PLAN_PATH)
    write_planner_prompt(declarations_dir / "dynamic_component_planner_prompt.md")
    slices = write_reference_slices(slices_dir, component_plan)
    write_structured_declarations(declarations_json, prompts_md, review_checklist_md, slices, component_plan)
    write_plotneuralnet_source(top_project)
    render_plotneuralnet_tex(top_project, top_tex)
    write_top_skeleton_svg(top_svg)
    write_micro_grid_svg(grid_svg)
    write_full_connection_dot(fc_dot)
    render_graphviz_svg(fc_dot, fc_svg)
    write_full_connection_svg(fc_svg)
    svg_to_png(top_svg, top_png)
    svg_to_png(grid_svg, grid_png)
    svg_to_png(fc_svg, fc_png)
    write_master_drawio(master_drawio, top_png, grid_png, fc_png)
    write_master_preview_png(master_png, top_png, grid_png, fc_png)
    drawio_export = export_drawio_png(master_drawio, master_png)

    report = {
        "reference_slices": slices,
        "structured_declarations": {
            "json": str(declarations_json),
            "prompts": str(prompts_md),
            "review_checklist": str(review_checklist_md),
            "component_plan": str(COMPONENT_PLAN_PATH),
            "planner_prompt": str(declarations_dir / "dynamic_component_planner_prompt.md"),
        },
        "top_skeleton": {
            "svg": str(top_svg),
            "png": str(top_png),
            "plotneuralnet_json": str(top_project),
            "plotneuralnet_tex": str(top_tex),
        },
        "micro_grid": {"svg": str(grid_svg), "png": str(grid_png)},
        "full_connection": {"dot": str(fc_dot), "svg": str(fc_svg), "png": str(fc_png)},
        "master": {"drawio": str(master_drawio), "png": str(master_png), "drawio_export": drawio_export},
    }
    (OUTPUT_ROOT / "divide_conquer_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


def parse_args() -> Namespace:
    parser = ArgumentParser(description="Build the high-density LeNet-5 divide-and-conquer replica.")
    parser.add_argument("--reference-image", default=str(REFERENCE_IMAGE), help="Absolute path to the original LeNet-5 reference image.")
    parser.add_argument("--out-dir", default=str(OUTPUT_ROOT), help="Absolute output directory for all generated artifacts.")
    parser.add_argument(
        "--component-plan",
        default=str(DEFAULT_COMPONENT_PLAN),
        help="Absolute JSON plan whose components decide how many regions to crop. Create a new plan per reference image.",
    )
    return parser.parse_args()


def configure_from_args(args: Namespace) -> None:
    global REFERENCE_IMAGE, OUTPUT_ROOT, STAGES_DIR, DELIVERABLES_DIR, COMPONENT_PLAN_PATH
    REFERENCE_IMAGE = Path(args.reference_image).expanduser().resolve()
    OUTPUT_ROOT = Path(args.out_dir).expanduser().resolve()
    STAGES_DIR = (OUTPUT_ROOT / "stages").resolve()
    DELIVERABLES_DIR = (OUTPUT_ROOT / "deliverables").resolve()
    COMPONENT_PLAN_PATH = Path(args.component_plan).expanduser().resolve()


def load_component_plan(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(
            f"Component plan not found: {path}. Create one from dynamic_component_planner_prompt.md or pass --component-plan."
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("components"), list):
        raise ValueError("Component plan must be a JSON object with a components list.")
    return payload


def write_planner_prompt(path: Path) -> None:
    path.write_text(
        """# Dynamic Component Planner Prompt

Use this before rendering any dense reference image. The number of regions must be decided from the image content, not from a fixed template.

Return JSON only:

```json
{
  "strategy": "Short explanation of how the image was divided.",
  "overview_regions": [
    {
      "id": "optional_large_region_id",
      "name": "Optional broad region for context",
      "box_xyxy": [0, 0, 100, 100]
    }
  ],
  "components": [
    {
      "id": "stable_slug",
      "name": "Human-readable component name",
      "box_xyxy": [x1, y1, x2, y2],
      "text": ["all words/numbers/symbols visible inside this component"],
      "must_notice": ["colored boxes", "arrows", "dashed lines", "connector endpoints", "small symbols"],
      "relationships": ["how this component connects to neighboring components"]
    }
  ]
}
```

Rules:

- Start with OCR: list all visible text in the whole image.
- Then choose crops around semantic components: layer stack, local inset, legend, connector cluster, dense node group, small label cluster, etc.
- Crops may overlap when a connector crosses component boundaries.
- Use as many or as few components as the image requires.
- Each component should be small enough that no text, colored marker, arrow endpoint, or tiny inset is likely to be skipped.
- Do not merge unrelated details just to reduce the component count.
""",
        encoding="utf-8",
    )


def write_reference_slices(out_dir: Path, component_plan: dict[str, object]) -> dict[str, dict[str, object]]:
    if not REFERENCE_IMAGE.is_file():
        return {}
    image = Image.open(REFERENCE_IMAGE).convert("RGB")
    regions: list[dict[str, object]] = []
    for key in ("overview_regions", "components"):
        for region in component_plan.get(key, []):
            if not isinstance(region, dict):
                continue
            regions.append(region)
    result: dict[str, dict[str, object]] = {}
    for region in regions:
        name = str(region["id"])
        box = tuple(int(value) for value in region["box_xyxy"])
        crop = image.crop(box)
        crop_path = out_dir / f"{name}.png"
        crop.save(crop_path, dpi=(300, 300))
        scale = max(1.0, 2048 / crop.width)
        hi_res = crop.resize((round(crop.width * scale), round(crop.height * scale)), Image.Resampling.LANCZOS)
        hi_res_path = out_dir / f"{name}_2048w_300dpi.png"
        hi_res.save(hi_res_path, dpi=(300, 300))
        result[name] = {
            "box_xyxy": box,
            "crop_png": str(crop_path),
            "ai_working_png": str(hi_res_path),
        }
        for source_key, result_key in (
            ("name", "name"),
            ("text", "expected_text"),
            ("must_notice", "must_notice"),
            ("relationships", "relationships"),
        ):
            if source_key in region:
                result[name][result_key] = region[source_key]
    return result


def write_structured_declarations(
    declarations_json: Path,
    prompts_md: Path,
    review_checklist_md: Path,
    slices: dict[str, dict[str, object]],
    component_plan: dict[str, object],
) -> None:
    components = [component for component in component_plan.get("components", []) if isinstance(component, dict)]
    payload = {
        "principle": "Divide the dense LeNet-5 figure into content-defined local components, declare each component, then assemble components in Draw.io.",
        "component_planning": {
            "strategy": component_plan.get(
                "strategy",
                "The component count is determined by the reference image content, not by a fixed grid or fixed region count.",
            ),
            "component_count": len(components),
            "rule": "Each component is a semantic detail unit: text cluster, layer stack, local inset, connector cluster, legend, or dense node group.",
        },
        "rendering_settings": {
            "minimum_ai_working_width_px": 2048,
            "dpi": 300,
            "line_policy": "constant weight black lines; do not fade cross-layer connectors into background texture",
            "text_policy": "use vector text in Draw.io master whenever possible; use Arial for English labels",
        },
        "ocr_first_text_inventory": [
            "INPUT",
            "32x32",
            "C1: feature maps",
            "6@28x28",
            "S2: f. maps",
            "6@14x14",
            "C3: f. maps 16@10x10",
            "S4: f. maps 16@5x5",
            "C5: layer",
            "120",
            "F6: layer",
            "84",
            "OUTPUT",
            "10",
            "Convolutions",
            "5x5",
            "Subsampling",
            "2x2",
            "Convolutions",
            "3x3",
            "Subsampling",
            "2x2",
            "Full connection",
            "Full connection",
            "Gaussian connections",
            "0 1 2 3 4 5 6 7 8 9",
        ],
        "region_reading_protocol": [
            "First list all visible text in the crop before drawing anything.",
            "Then list every colored box, arrow, dashed guide, and connector line with start/end anchors.",
            "Only after the element inventory is complete should the component be rendered.",
            "After rendering, compare against the inventory and mark missing, shifted, or simplified elements.",
        ],
        "fine_components": [
            {
                "id": component.get("id", ""),
                "name": component.get("name", ""),
                "source_crop": slices.get(str(component.get("id", "")), {}),
                "expected_text": component.get("text", []),
                "must_notice": component.get("must_notice", []),
                "relationships": component.get("relationships", []),
            }
            for component in components
        ],
        "regions": [
            {
                "id": "A",
                "name": "CNN skeleton",
                "source_crop": slices.get("A_cnn_skeleton", {}),
                "tool": "PlotNeuralNet-style vector skeleton, then Draw.io assembly",
                "declaration": {
                    "layers": [
                        {"id": "input", "label": "INPUT 32x32", "kind": "input_plane"},
                        {"id": "c1", "label": "C1: feature maps 6@28x28", "kind": "feature_stack", "maps": 6},
                        {"id": "s2", "label": "S2: f. maps 6@14x14", "kind": "feature_stack", "maps": 6},
                        {"id": "c3", "label": "C3: f. maps 16@10x10", "kind": "feature_stack", "maps": 16},
                        {"id": "s4", "label": "S4: f. maps 16@5x5", "kind": "feature_stack", "maps": 16},
                        {"id": "c5", "label": "C5: layer 120", "kind": "diagonal_band"},
                        {"id": "f6", "label": "F6: layer 84", "kind": "diagonal_band"},
                        {"id": "out", "label": "OUTPUT 10", "kind": "diagonal_band"},
                    ],
                    "cross_layer_connectors": [
                        {
                            "id": "red_input_to_c1",
                            "meaning": "input 1x1 red pixel projects to corresponding C1 feature-map point",
                            "start": "input.right-lower red 1x1 pixel",
                            "end": "C1 front feature-map red output pixel",
                        },
                        {
                            "id": "c1_green_kernel_to_s2",
                            "meaning": "C1 selected local activation is subsampled to S2 green activation",
                            "start": "C1 green window center",
                            "end": "S2 green activation pixel",
                        },
                        {
                            "id": "c3_blue_kernel_to_micro_grid",
                            "meaning": "C3 blue receptive-field window expands into lower convolution grid",
                            "start": "C3 blue square window",
                            "end": "lower micro-grid blue window",
                        },
                    ],
                },
            },
            {
                "id": "B",
                "name": "Micro grid alignment",
                "source_crop": slices.get("B_micro_grid_alignment", {}),
                "tool": "Draw.io table or deterministic SVG grid",
                "declaration": {
                    "grid_groups": [
                        {
                            "id": "conv_5x5",
                            "grid": "7x7 white table",
                            "blue_window": "5x5 outline from row 1 col 1",
                            "red_window": "5x5 outline offset by +1 row and +1 col",
                            "pink_overlap": "overlap cells between blue and red windows",
                        },
                        {
                            "id": "pool_2x2",
                            "grid": "2x2 green table connected to 4x4 table",
                            "selected_output": "green cell at local row 2 col 2 in the 4x4 table",
                        },
                        {
                            "id": "conv_3x3",
                            "grid": "5x5 table with yellow and blue receptive-field outlines",
                            "selected_output": "3x3 output table with yellow upper-left and blue center cells",
                        },
                    ],
                    "connector_policy": "dashed local projection lines connect corresponding grid corners and selected pixels only",
                },
            },
            {
                "id": "C",
                "name": "Full connection network",
                "source_crop": slices.get("C_full_connection_network", {}),
                "tool": "Graphviz/structured coordinate generator",
                "declaration": {
                    "layers": [
                        {"id": "fc_in", "logical_nodes": 16, "visible_nodes": 9},
                        {"id": "fc_120", "logical_nodes": 120, "visible_nodes": 11},
                        {"id": "fc_84", "logical_nodes": 84, "visible_nodes": 7},
                        {"id": "fc_out", "logical_nodes": 10, "visible_nodes": 10},
                    ],
                    "edges": "complete bipartite connections between adjacent visible columns",
                    "node_policy": "equal radius circles; equal vertical spacing; bottom labels centered under each column",
                    "line_policy": "constant thin gray stroke for every edge",
                },
            },
        ],
        "assembly_detail_gate": [
            "The final master must contain the operation labels under the upper network: Convolutions 5x5, Subsampling 2x2, Convolutions 3x3, Subsampling 2x2, Full connection, Full connection, Gaussian connections.",
            "The lower-right fully connected inset must show three logical output columns labeled 120, 84, and 10, plus red class digits 0-9 on the right.",
            "Every long colored arrow from the top skeleton to the lower insets must end at the exact corresponding inset, not merely near the region.",
            "Run an omission pass after rendering and list missing text, missing colored boxes, and line endpoints that do not touch their target objects.",
        ],
    }
    declarations_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    prompts_md.write_text(local_prompt_markdown(payload), encoding="utf-8")
    review_checklist_md.write_text(review_checklist_markdown(payload), encoding="utf-8")


def local_prompt_markdown(payload: dict) -> str:
    return f"""# LeNet-5 Local AI Prompts

## Mandatory High-Density Reading Protocol

Do not summarize the whole image first. Work in this order:

1. OCR first: list every visible word, number, and symbol in the crop.
2. Element inventory: list every module, colored square, grid, arrow, dashed guide, connector line, node column, and digit label.
3. Anchor mapping: for every arrow or line, name the exact start object and end object.
4. Render only after the inventory is complete.
5. Omission pass: compare the rendered component against the inventory and report missing or shifted details.

## Required Text Inventory

INPUT; 32x32; C1: feature maps; 6@28x28; S2: f. maps; 6@14x14; C3: f. maps 16@10x10; S4: f. maps 16@5x5; C5: layer; 120; F6: layer; 84; OUTPUT; 10; Convolutions; 5x5; Subsampling; 2x2; Convolutions; 3x3; Subsampling; 2x2; Full connection; Full connection; Gaussian connections; 0 1 2 3 4 5 6 7 8 9.

## Content-Defined Component Prompts

The list below comes from the component plan for this specific reference image. For a different image, generate a new component plan first; do not reuse this count or these boxes.

{component_prompt_sections(payload)}

## Region A: CNN Skeleton

Use the Region A crop only. Recreate the LeNet-5 top skeleton as crisp vector-like technical graphics. Draw gray feature-map stacks in this exact order: INPUT 32x32, C1 feature maps 6@28x28, S2 f. maps 6@14x14, C3 f. maps 16@10x10, S4 f. maps 16@5x5, C5 layer 120, F6 layer 84, OUTPUT 10. Use constant-weight black cross-layer lines. Add the operation labels below the top skeleton: Convolutions 5x5, Subsampling 2x2, Convolutions 3x3, Subsampling 2x2, Full connection, Full connection, Gaussian connections. Do not invent extra connectors.

## Region B: Micro Grid Alignment

Use the Region B crop only. Create deterministic white table grids with straight black grid lines. In the large 7x7 grid, draw a blue 5x5 outline starting at row 1 col 1 and a red 5x5 outline offset by +1 row and +1 col. Fill the overlap area translucent pink. Preserve the mathematical alignment of cells; do not shift the red or blue windows for aesthetics.

## Region C: Full Connection Network

Use the Region C crop only. Draw three vertical node columns representing 120, 84, and 10 logical nodes. Use equal-size circles, equal vertical spacing within each visible column, and complete bipartite thin gray connections between adjacent columns. Place the blue labels 120, 84, 10 centered under the columns. Place the red class digits 0 through 9 to the right of the output column. Do not vary line thickness.

## Assembly Rule

Do not ask the image model to assemble the whole figure. Import the finished local components into Draw.io, align them over the reference underlay, and draw cross-component connector lines as editable vector lines. Before final export, run the omission pass again and check text labels, colored boxes, dashed guide lines, and arrow endpoints.
"""


def component_prompt_sections(payload: dict) -> str:
    sections = []
    for component in payload.get("fine_components", []):
        crop = component.get("source_crop", {})
        expected_text = "; ".join(component.get("expected_text", [])) or "No text expected; focus on shapes and line endpoints."
        must_notice = "; ".join(component.get("must_notice", []))
        relationships = "; ".join(component.get("relationships", []))
        sections.append(
            "\n".join(
                [
                    f"### {component.get('id', '')}: {component.get('name', '')}",
                    f"- Crop: {crop.get('ai_working_png', crop.get('crop_png', ''))}",
                    f"- Expected text: {expected_text}",
                    f"- Must notice: {must_notice}",
                    f"- Relationships: {relationships}",
                    "- Instruction: analyze this crop alone first, then compare it with adjacent crops only for connector continuity.",
                ]
            )
        )
    return "\n\n".join(sections)


def review_checklist_markdown(payload: dict) -> str:
    items = "\n".join(f"- [ ] {item}" for item in payload["ocr_first_text_inventory"])
    gates = "\n".join(f"- [ ] {item}" for item in payload["assembly_detail_gate"])
    components = "\n".join(
        f"- [ ] {component.get('id', '')}: {component.get('name', '')} includes "
        f"{'; '.join(component.get('expected_text', [])) or 'all declared non-text details'} and "
        f"{'; '.join(component.get('must_notice', []))}"
        for component in payload.get("fine_components", [])
    )
    return f"""# LeNet-5 Detail Review Checklist

## Text Must Appear

{items}

## Content-Defined Component Pass

{components}

## Alignment And Detail Gates

{gates}

## Region Pass

- [ ] Left/top INPUT box includes the black handwritten A-like stroke and the red source pixel marker.
- [ ] C1, S2, C3, S4 stacks keep their intended layer counts and do not collapse into a generic gray block.
- [ ] Lower convolution 5x5 grid has both blue and red windows plus pink overlap and dashed projection lines.
- [ ] Lower pooling 2x2 inset has green source and target cells with dashed green projection lines.
- [ ] Lower convolution 3x3 inset has yellow and blue windows plus matching yellow/blue output cells.
- [ ] Fully connected inset uses three labeled columns 120, 84, 10 with red class digits 0-9 at the right.
- [ ] Cyan arrows from top C5/F6/OUTPUT bands point to the corresponding fully connected columns.
"""


def write_plotneuralnet_source(path: Path) -> None:
    payload = {
        "schema_version": 1,
        "name": "LeNet-5 top skeleton",
        "source_root": str(PROJECT_ROOT.parent / "PlotNeuralNet"),
        "items": [
            {"type": "conv", "name": "C1", "s_filer": 28, "n_filer": 6, "height": 28, "depth": 28, "width": 3, "caption": "C1 6@28x28"},
            {"type": "connection", "of": "C1", "to": "S2"},
            {"type": "pool", "name": "S2", "height": 14, "depth": 14, "width": 1, "caption": "S2 6@14x14"},
            {"type": "connection", "of": "S2", "to": "C3"},
            {"type": "conv", "name": "C3", "s_filer": 10, "n_filer": 16, "height": 10, "depth": 10, "width": 5, "caption": "C3 16@10x10"},
            {"type": "connection", "of": "C3", "to": "S4"},
            {"type": "pool", "name": "S4", "height": 5, "depth": 5, "width": 2, "caption": "S4 16@5x5"},
            {"type": "connection", "of": "S4", "to": "C5"},
            {"type": "conv", "name": "C5", "s_filer": 1, "n_filer": 120, "height": 6, "depth": 6, "width": 9, "caption": "C5 120"},
            {"type": "connection", "of": "C5", "to": "F6"},
            {"type": "conv", "name": "F6", "s_filer": 1, "n_filer": 84, "height": 5, "depth": 5, "width": 7, "caption": "F6 84"},
            {"type": "connection", "of": "F6", "to": "Output"},
            {"type": "softmax", "name": "Output", "s_filer": 10, "caption": "Output 10"},
        ],
        "history": [],
        "future": [],
        "metadata": {"factory_kind": "plotneuralnet_lenet5_top_skeleton"},
        "created_at": "generated",
        "updated_at": "generated",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def render_plotneuralnet_tex(project_path: Path, tex_path: Path) -> None:
    command = [
        "cli-anything-plotneuralnet",
        "--json",
        "--project",
        str(project_path),
        "render",
        "tex",
        "-o",
        str(tex_path),
    ]
    result = subprocess.run(command, cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=90)
    if result.returncode != 0:
        tex_path.write_text("% PlotNeuralNet render failed\n" + result.stdout + result.stderr, encoding="utf-8")


def write_top_skeleton_svg(path: Path) -> None:
    svg = SvgBuilder(1250, 430)
    svg.rect(0, 0, 1250, 430, "#ffffff", "#ffffff", 0)
    svg.rect(8, 82, 132, 132, "#cfcfcf", "#cfcfcf", 1)
    svg.text(42, 26, "INPUT", 22)
    svg.text(42, 50, "32x32", 20)
    svg.polyline([(32, 180), (63, 112), (103, 182)], "#111111", 7)
    svg.polyline([(47, 144), (99, 157)], "#111111", 7)

    svg.feature_stack(185, 54, 108, 125, 6, 13, 10, "#8d8d8d")
    svg.text(213, 18, "C1: feature maps", 20)
    svg.text(229, 42, "6@28x28", 19)
    svg.feature_stack(400, 106, 74, 78, 6, 10, 8, "#929292")
    svg.text(385, 74, "S2: f. maps", 18)
    svg.text(390, 96, "6@14x14", 18)
    svg.feature_stack(510, 36, 66, 88, 16, 13, 10, "#878787")
    svg.text(505, 18, "C3: f. maps 16@10x10", 20)
    svg.feature_stack(705, 56, 31, 31, 12, 22, 20, "#858585")
    svg.text(682, 50, "S4: f. maps 16@5x5", 19)

    svg.line(734, 65, 856, 132, "#222222", 1.6)
    svg.line(856, 132, 985, 140, "#222222", 1.4)
    svg.line(985, 140, 1090, 136, "#222222", 1.4)
    svg.slanted_band(875, 130, 30, 174, -42, "#777777")
    svg.slanted_band(1002, 133, 29, 164, -42, "#777777")
    svg.slanted_band(1117, 127, 30, 174, -42, "#777777")
    svg.text(840, 90, "C5: layer", 20)
    svg.text(857, 114, "120", 20)
    svg.text(970, 91, "F6: layer", 20)
    svg.text(988, 115, "84", 20)
    svg.text(1078, 84, "OUTPUT", 20)
    svg.text(1096, 108, "10", 20)
    for digit in range(10):
        svg.text(1129 + digit * 12.3, 82 + digit * 9.3, str(digit), 22, "#8a4b4b", rotate=28)

    svg.rect(91, 171, 25, 25, "none", "#d92525", 4)
    svg.rect(300, 133, 16, 16, "none", "#22d833", 3)
    svg.rect(548, 157, 38, 38, "none", "#1730d3", 4)
    svg.rect(760, 223, 17, 17, "none", "#22d833", 3)
    svg.rect(885, 205, 38, 38, "none", "#d52bd5", 5)
    svg.line(105, 184, 370, 197, "#222222", 2)
    svg.line(305, 141, 875, 210, "#222222", 1.5)
    svg.line(310, 145, 760, 230, "#222222", 1.3)
    svg.line(775, 232, 913, 224, "#222222", 1.7)
    svg.text(223, 324, "Convolutions", 20)
    svg.text(223, 354, "5x5", 21, "#1731d5")
    svg.text(445, 324, "Subsampling", 20)
    svg.text(445, 354, "2x2", 21, "#1731d5")
    svg.text(615, 324, "Convolutions", 20)
    svg.text(615, 354, "3x3", 21, "#1731d5")
    svg.text(790, 324, "Subsampling", 20)
    svg.text(790, 354, "2x2", 21, "#1731d5")
    svg.text(965, 324, "Full connection", 15)
    svg.text(1080, 324, "Full connection", 15)
    svg.text(1138, 312, "Gaussian connections", 14)
    path.write_text(svg.finish(), encoding="utf-8")


def write_micro_grid_svg(path: Path) -> None:
    svg = SvgBuilder(960, 250)
    svg.rect(0, 0, 960, 250, "#ffffff", "#ffffff", 0)
    svg.grid(16, 24, 7, 7, 24)
    svg.rect(16, 24, 120, 120, "none", "#1131d8", 5)
    svg.rect(40, 48, 120, 120, "none", "#e51c23", 5)
    for row in range(1, 5):
        for col in range(1, 6):
            svg.rect(16 + col * 24, 24 + row * 24, 24, 24, "#efb6dc", "#222222", 1, opacity=0.45)
    svg.grid(235, 78, 3, 3, 24)
    svg.rect(235, 78, 24, 24, "#1131d8", "#222222", 1)
    svg.rect(259, 102, 24, 24, "#e51c23", "#222222", 1)
    svg.line(160, 72, 235, 91, "#a75a5a", 1.6, dashed=True)
    svg.line(160, 145, 235, 126, "#a75a5a", 1.6, dashed=True)

    svg.grid(355, 50, 2, 2, 28)
    svg.rect(355, 50, 56, 56, "none", "#20df2b", 5)
    svg.grid(485, 42, 4, 4, 18)
    svg.rect(503, 60, 18, 18, "#20e820", "#222222", 1)
    svg.line(411, 73, 485, 60, "#34c84a", 1.6, dashed=True)
    svg.line(411, 102, 485, 121, "#34c84a", 1.6, dashed=True)

    svg.grid(610, 32, 5, 5, 25)
    svg.rect(610, 32, 50, 50, "none", "#f2e932", 6, opacity=0.6)
    svg.rect(635, 32, 75, 75, "none", "#1d33da", 5)
    svg.grid(820, 57, 3, 3, 24)
    svg.rect(820, 57, 24, 24, "#fff21c", "#222222", 1)
    svg.rect(844, 81, 24, 24, "#1731d4", "#222222", 1)
    svg.line(710, 71, 820, 70, "#2c2a79", 1.5, dashed=True)
    svg.line(710, 106, 820, 104, "#2c2a79", 1.5, dashed=True)
    path.write_text(svg.finish(), encoding="utf-8")


def write_full_connection_dot(path: Path) -> None:
    layers = [
        ("h1", 120, 11, 0),
        ("h2", 84, 7, 1.6),
        ("o", 10, 10, 3.2),
    ]
    lines = [
        "graph G {",
        '  graph [layout=neato, splines=line, overlap=false, outputorder=edgesfirst, bgcolor="transparent", margin=0, pad=0];',
        '  node [shape=circle, label="", fixedsize=true, width=0.14, height=0.14, style=filled, fillcolor="white", color="black", penwidth=1.7];',
        '  edge [color="#55555533", penwidth=0.55];',
    ]
    visible_nodes: dict[str, list[str]] = {}
    for prefix, total, shown, x in layers:
        ys = visible_y_positions(shown)
        visible_nodes[prefix] = []
        for idx, y in enumerate(ys):
            name = f"{prefix}{idx}"
            visible_nodes[prefix].append(name)
            lines.append(f'  {name} [pos="{x},{y}!", tooltip="{prefix} visible node {idx + 1} of {total}"];')
        lines.append(
            f'  {prefix}_label [shape=plaintext, label="{total}", fontsize=18, fontcolor="#1731b5", '
            f'fixedsize=false, width=0.45, height=0.2, pos="{x},-0.55!"];'
        )
    for a, b in [("h1", "h2"), ("h2", "o")]:
        for source in visible_nodes[a]:
            for target in visible_nodes[b]:
                lines.append(f"  {source} -- {target};")
    lines.append("}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_full_connection_svg(path: Path) -> None:
    svg = SvgBuilder(430, 330)
    svg.rect(0, 0, 430, 330, "#ffffff", "#ffffff", 0)
    layers = [
        (70, [22, 48, 74, 100, 126, 152, 178, 204, 230, 256, 282], "120"),
        (215, [28, 70, 112, 154, 196, 238, 280], "84"),
        (360, [22 + idx * 29 for idx in range(10)], "10"),
    ]
    for (x1, ys1, _), (x2, ys2, _) in zip(layers, layers[1:]):
        for y1 in ys1:
            for y2 in ys2:
                svg.line(x1, y1, x2, y2, "#555555", 0.55)
    for x, ys, label in layers:
        for y in ys:
            svg.circle(x, y, 9, "#ffffff", "#111111", 2)
        svg.text(x, 315, label, 22, "#1731b5")
    svg.text(70, 294, "...", 20)
    svg.text(215, 294, "...", 20)
    for idx, y in enumerate(layers[-1][1]):
        svg.text(413, y + 6, str(idx), 22, "#8a4b4b")
    path.write_text(svg.finish(), encoding="utf-8")


def visible_y_positions(count: int) -> list[float]:
    if count == 7:
        return [2.8, 2.35, 1.9, 1.45, 1.0, 0.15, -0.3]
    if count == 9:
        return [2.8, 2.45, 2.1, 1.75, 1.4, 0.55, 0.2, -0.15, -0.5]
    return [2.8 - index * (3.3 / max(1, count - 1)) for index in range(count)]


def render_graphviz_svg(dot_path: Path, svg_path: Path) -> None:
    command = [str(NEATO_EXE), "-n2", "-Tsvg", str(dot_path), "-o", str(svg_path)]
    subprocess.run(command, cwd=str(PROJECT_ROOT), check=True, timeout=120)


def svg_to_png(svg_path: Path, png_path: Path) -> None:
    import cairosvg

    cairosvg.svg2png(url=str(svg_path), write_to=str(png_path))


def write_master_drawio(path: Path, top_png: Path, grid_png: Path, fc_png: Path) -> None:
    cells = [
        '<mxCell id="0"/>',
        '<mxCell id="component_layer" value="Component SVG layers" parent="0"/>',
        '<mxCell id="connector_layer" value="Editable connectors" parent="0"/>',
        '<mxCell id="label_layer" value="Assembly labels" parent="0"/>',
    ]
    next_id = 1

    def image_cell(image_path: Path, x: int, y: int, w: int, h: int) -> None:
        nonlocal next_id
        next_id += 1
        data_uri = quote("data:image/png;base64," + base64.b64encode(image_path.read_bytes()).decode("ascii"), safe=":/,+=@#")
        cells.append(
            f'<mxCell id="n{next_id}" value="" style="shape=image;imageAspect=0;aspect=fixed;image={data_uri};" vertex="1" parent="component_layer">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
        )

    def line(points: list[tuple[int, int]], color: str, width: float, dashed: bool = False) -> None:
        nonlocal next_id
        next_id += 1
        start, end = points[0], points[-1]
        mids = "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in points[1:-1])
        dash = "dashed=1;dashPattern=8 7;" if dashed else ""
        cells.append(
            f'<mxCell id="e{next_id}" value="" style="edgeStyle=none;html=1;rounded=0;strokeColor={color};strokeWidth={width};endArrow=classic;endFill=1;endSize=6;{dash}" edge="1" parent="connector_layer">'
            f'<mxGeometry relative="1" as="geometry"><mxPoint x="{start[0]}" y="{start[1]}" as="sourcePoint"/><mxPoint x="{end[0]}" y="{end[1]}" as="targetPoint"/><Array as="points">{mids}</Array></mxGeometry></mxCell>'
        )

    image_cell(top_png, 10, 18, 1290, 430)
    image_cell(grid_png, 40, 480, 920, 230)
    image_cell(fc_png, 1000, 398, 395, 330)
    line([(112, 205), (147, 485)], "#d52525", 2.0)
    line([(332, 160), (405, 478)], "#23cc38", 3.0)
    line([(585, 214), (685, 480)], "#2033d7", 2.4)
    line([(945, 260), (960, 490)], "#d52bd5", 3.0)
    line([(1085, 356), (1065, 408)], "#24aaca", 3.0)
    line([(1198, 356), (1198, 408)], "#24aaca", 3.0)
    line([(1290, 356), (1332, 408)], "#24aaca", 3.0)

    xml = f'''<mxfile host="ai-diagram-factory" agent="codex" version="0.5.0">
  <diagram id="lenet5-divide-conquer" name="LeNet-5 divide-conquer assembly">
    <mxGraphModel dx="1428" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1428" pageHeight="762" math="0" shadow="0">
      <root>
        {"".join(cells)}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
'''
    path.write_text(xml, encoding="utf-8")


def write_master_preview_png(png_path: Path, top_png: Path, grid_png: Path, fc_png: Path) -> None:
    canvas = Image.new("RGB", (1428, 762), "white")
    top = Image.open(top_png).convert("RGBA").resize((1290, 430), Image.Resampling.LANCZOS)
    grid = Image.open(grid_png).convert("RGBA").resize((920, 230), Image.Resampling.LANCZOS)
    fc = Image.open(fc_png).convert("RGBA").resize((395, 330), Image.Resampling.LANCZOS)
    canvas.paste(top, (10, 18), top)
    canvas.paste(grid, (40, 480), grid)
    canvas.paste(fc, (1000, 398), fc)
    draw = ImageDraw.Draw(canvas)
    draw_arrow(draw, (112, 205), (147, 485), "#d52525", 2.0)
    draw_arrow(draw, (332, 160), (405, 478), "#23cc38", 3.0)
    draw_arrow(draw, (585, 214), (685, 480), "#2033d7", 2.4)
    draw_arrow(draw, (945, 260), (960, 490), "#d52bd5", 3.0)
    draw_arrow(draw, (1085, 356), (1065, 408), "#24aaca", 3.0)
    draw_arrow(draw, (1198, 356), (1198, 408), "#24aaca", 3.0)
    draw_arrow(draw, (1290, 356), (1332, 408), "#24aaca", 3.0)
    canvas.save(png_path, dpi=(300, 300))


def draw_arrow(draw: ImageDraw.ImageDraw, start: tuple[float, float], end: tuple[float, float], color: str, width: float) -> None:
    draw.line([start, end], fill=color, width=round(width))
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    length = 12
    spread = 0.46
    p1 = end
    p2 = (end[0] - length * math.cos(angle - spread), end[1] - length * math.sin(angle - spread))
    p3 = (end[0] - length * math.cos(angle + spread), end[1] - length * math.sin(angle + spread))
    draw.polygon([p1, p2, p3], fill=color)


def export_drawio_png(drawio_path: Path, png_path: Path) -> dict[str, str | int | bool]:
    command = [
        "cli-anything-drawio",
        "--project",
        str(drawio_path),
        "export",
        "render",
        str(png_path),
        "--format",
        "png",
        "--overwrite",
    ]
    env = os.environ.copy()
    try:
        result = subprocess.run(command, cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=180, env=env)
    except Exception as exc:
        return {"ok": False, "fallback_preview_kept": True, "reason": str(exc)}
    if result.returncode == 0:
        return {"ok": True, "fallback_preview_kept": False}
    return {
        "ok": False,
        "fallback_preview_kept": True,
        "returncode": result.returncode,
        "stderr_tail": (result.stderr or "")[-800:],
    }


class SvgBuilder:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.parts: list[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        ]

    def rect(self, x: float, y: float, w: float, h: float, fill: str, stroke: str, width: float, opacity: float = 1.0) -> None:
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}"/>'
        )

    def circle(self, cx: float, cy: float, r: float, fill: str, stroke: str, width: float) -> None:
        self.parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'
        )

    def text(self, x: float, y: float, content: str, size: int, fill: str = "#111111", rotate: float | None = None) -> None:
        transform = f' transform="rotate({rotate} {x} {y})"' if rotate is not None else ""
        self.parts.append(
            f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" font-size="{size}" fill="{fill}" text-anchor="middle"{transform}>{escape(content)}</text>'
        )

    def line(self, x1: float, y1: float, x2: float, y2: float, color: str, width: float, arrow: bool = False, dashed: bool = False) -> None:
        dash = ' stroke-dasharray="8 7"' if dashed else ""
        self.parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}" stroke-linecap="round"{dash}/>'
        )
        if arrow:
            self.arrowhead(x1, y1, x2, y2, color)

    def polyline(self, points: list[tuple[float, float]], color: str, width: float, arrow: bool = False) -> None:
        pts = " ".join(f"{x},{y}" for x, y in points)
        self.parts.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')
        if arrow and len(points) >= 2:
            (x1, y1), (x2, y2) = points[-2], points[-1]
            self.arrowhead(x1, y1, x2, y2, color)

    def arrowhead(self, x1: float, y1: float, x2: float, y2: float, color: str) -> None:
        angle = math.atan2(y2 - y1, x2 - x1)
        length = 12
        spread = 0.46
        p1 = (x2, y2)
        p2 = (x2 - length * math.cos(angle - spread), y2 - length * math.sin(angle - spread))
        p3 = (x2 - length * math.cos(angle + spread), y2 - length * math.sin(angle + spread))
        pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in (p1, p2, p3))
        self.parts.append(f'<polygon points="{pts}" fill="{color}" stroke="{color}" stroke-width="0.5"/>')

    def grid(self, x: float, y: float, cols: int, rows: int, size: float) -> None:
        for row in range(rows):
            for col in range(cols):
                self.rect(x + col * size, y + row * size, size, size, "#ffffff", "#222222", 1)

    def feature_stack(self, x: float, y: float, w: float, h: float, count: int, dx: float, dy: float, fill: str) -> None:
        for idx in range(count):
            self.rect(x + idx * dx, y + idx * dy, w, h, fill, "#d0d0d0", 1)

    def slanted_band(self, x: float, y: float, w: float, h: float, angle: float, fill: str) -> None:
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{fill}" transform="rotate({angle} {x} {y})"/>')

    def finish(self) -> str:
        return "\n".join(self.parts + ["</svg>\n"])


if __name__ == "__main__":
    main()
