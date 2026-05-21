from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from ai_diagram_factory.cli import cli
from ai_diagram_factory.io import write_manifest, write_json
from ai_diagram_factory.replicate import MODULE_LIMIT
from ai_diagram_factory.renderers.tikz import render_tikz_module
from ai_diagram_factory.templates import reference_workflow_manifest


@pytest.fixture(autouse=True)
def skip_external_desktop_exports(monkeypatch) -> None:
    monkeypatch.setenv("AI_DIAGRAM_FACTORY_SKIP_EXTERNAL_EXPORTS", "1")
    monkeypatch.setenv("AI_DIAGRAM_FACTORY_SKIP_LATEX", "1")


def test_init_creates_gallery_manifest(tmp_path: Path) -> None:
    manifest_path = tmp_path / "gallery.yaml"
    result = CliRunner().invoke(
        cli,
        ["init", "--preset", "deep-learning-gallery", "-o", str(manifest_path.resolve())],
    )

    assert result.exit_code == 0, result.output
    assert manifest_path.is_file()
    assert "vgg_style_cnn" in manifest_path.read_text(encoding="utf-8")


def test_render_drawio_flow_manifest(tmp_path: Path) -> None:
    manifest_path = tmp_path / "single_flow.yaml"
    out_dir = tmp_path / "out"
    write_manifest(
        manifest_path,
        {
            "project": "smoke",
            "figures": [
                {
                    "id": "smoke_flow",
                    "kind": "drawio_flow",
                    "title": "Smoke Flow",
                    "nodes": [
                        {"id": "start", "label": "Start"},
                        {"id": "finish", "label": "Finish"},
                    ],
                    "edges": [["start", "finish"]],
                }
            ],
        },
    )

    result = CliRunner().invoke(
        cli,
        ["render", str(manifest_path.resolve()), "--out-dir", str(out_dir.resolve())],
    )

    assert result.exit_code == 0, result.output
    assert (out_dir / "smoke_flow" / "smoke_flow.drawio").is_file()
    assert (out_dir / "smoke_flow" / "smoke_flow.png").is_file()
    index = json.loads((out_dir / "index.json").read_text(encoding="utf-8"))
    assert index["results"][0]["id"] == "smoke_flow"


def test_workflow_plan_writes_expected_summary(tmp_path: Path) -> None:
    manifest_path = tmp_path / "reference_workflow.yaml"
    plan_path = tmp_path / "tool_plan.json"
    write_manifest(manifest_path, reference_workflow_manifest())

    result = CliRunner().invoke(
        cli,
        ["workflow", "plan", str(manifest_path.resolve()), "-o", str(plan_path.resolve())],
    )

    assert result.exit_code == 0, result.output
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert len(plan["workflows"]) == 2
    assert plan["workflows"][0]["summary"]["drawio_tasks"] >= 1
    assert plan["workflows"][1]["summary"]["tikz_assets"] >= 1


def _minimal_component_plan() -> dict:
    return {
        "project": "smoke_replicate",
        "source_kind": "text",
        "summary": "Two-module smoke run.",
        "module_count_rationale": "One flow panel and one graph panel; merging them would erase the routing semantics.",
        "components": [
            {
                "id": "panel_a",
                "name": "Training flow",
                "backend": "drawio",
                "description": "Left-to-right training loop.",
                "figure_spec": {
                    "kind": "drawio_flow",
                    "nodes": [
                        {"id": "start", "label": "Start"},
                        {"id": "finish", "label": "Finish"},
                    ],
                    "edges": [["start", "finish"]],
                },
            },
            {
                "id": "panel_b",
                "name": "Dependency skeleton",
                "backend": "graphviz",
                "description": "Two-node dependency stub.",
                "figure_spec": {
                    "nodes": [
                        {"id": "a", "label": "A", "rank": 0},
                        {"id": "b", "label": "B", "rank": 1},
                    ],
                    "edges": [["a", "b"]],
                },
            },
        ],
        "global_connectors": [
            {"from": "panel_a", "to": "panel_b", "style": "dashed", "label": "feeds"},
        ],
    }


def test_replicate_with_minimal_plan(tmp_path: Path) -> None:
    plan_path = tmp_path / "component_plan.json"
    out_dir = tmp_path / "out"
    write_json(plan_path, _minimal_component_plan())

    result = CliRunner().invoke(
        cli,
        [
            "replicate",
            "--plan",
            str(plan_path.resolve()),
            "--out-dir",
            str(out_dir.resolve()),
        ],
    )

    assert result.exit_code == 0, result.output

    summary_path = out_dir / "replicate_summary.json"
    assert summary_path.is_file(), result.output
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["module_count"] == 2

    tool_plan = json.loads((out_dir / "tool_plan.json").read_text(encoding="utf-8"))
    confidences = {c["assignment"]["confidence"] for c in tool_plan["workflows"][0]["components"]}
    assert confidences == {"declared"}, tool_plan

    workflow_dir = Path(summary["workflow_dir"])
    deliverable_dir = workflow_dir / "deliverables"
    assert deliverable_dir.is_dir()
    assert "pdf" in summary["workflow_result"]["assembly"]["requested_source_formats"]
    pngs = list(deliverable_dir.glob("*.png"))
    drawios = list(deliverable_dir.glob("*.drawio"))
    svgs = list(deliverable_dir.glob("*.svg"))
    assert pngs, list(deliverable_dir.iterdir())
    assert drawios, list(deliverable_dir.iterdir())
    assert svgs, list(deliverable_dir.iterdir())

    report = json.loads((workflow_dir / "workflow_report.json").read_text(encoding="utf-8"))
    vsdx_status = report["assembly"]["vsdx_export"]["status"]
    assert vsdx_status in {"exported", "unavailable", "skipped"}, vsdx_status


def test_tikz_module_writes_source_and_preview(tmp_path: Path) -> None:
    result = render_tikz_module(
        {
            "id": "tiny_tikz",
            "kind": "tikz_module",
            "title": "Tiny TikZ",
            "body": (
                "\\begin{tikzpicture}[>=Stealth]\n"
                "  \\node[draw, rounded corners, fill=cyan!8] (a) {A};\n"
                "  \\node[draw, rounded corners, fill=orange!12, right=1cm of a] (b) {B};\n"
                "  \\draw[->] (a) -- (b);\n"
                "\\end{tikzpicture}\n"
            ),
        },
        tmp_path,
    )

    assert Path(result["png"]).is_file()
    assert any(Path(source).suffix == ".tex" for source in result["sources"])
    if result["backend"]["status"] == "tikz_svg":
        assert Path(result["svg"]).is_file()


def test_lenet_hifi_plan_uses_specialist_backends() -> None:
    plan_path = Path(__file__).resolve().parents[1] / "examples" / "lenet5_hifi_plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    components = {component["id"]: component for component in plan["components"]}

    for component_id in ["02_c1_feature_maps", "03_s2_feature_maps", "04_c3_feature_maps", "05_s4_feature_maps"]:
        component = components[component_id]
        assert component["backend"] == "plotneuralnet"
        assert component["figure_spec"]["compact"] is True

    assert components["11_fc_network"]["backend"] == "graphviz"


def test_replicate_rejects_more_than_12_modules(tmp_path: Path) -> None:
    plan = _minimal_component_plan()
    plan["components"] = [
        {
            "id": f"m{i:02d}",
            "name": f"Module {i}",
            "backend": "drawio",
            "description": "filler",
        }
        for i in range(MODULE_LIMIT + 1)
    ]
    plan["global_connectors"] = []
    plan_path = tmp_path / "too_many.json"
    write_json(plan_path, plan)

    result = CliRunner().invoke(
        cli,
        [
            "replicate",
            "--plan",
            str(plan_path.resolve()),
            "--out-dir",
            str((tmp_path / "out").resolve()),
        ],
    )

    assert result.exit_code != 0
    assert "12" in result.output or "module" in result.output.lower()
