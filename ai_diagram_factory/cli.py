from __future__ import annotations

import json
import shutil
from pathlib import Path

import click

from . import __version__
from .config import DEFAULT_OUTPUT_DIR, DRAWIO_HARNESS, PLOTNEURALNET_HARNESS
from .io import abs_path, load_manifest, write_json, write_manifest
from .planner import plan_workflow_manifest
from .renderers import RENDERERS
from .replicate import MODULE_LIMIT, replicate_from_plan
from .templates import blank_manifest, deep_learning_gallery_manifest, reference_workflow_manifest
from .workflow import render_workflow_manifest


@click.group()
@click.version_option(__version__)
def cli() -> None:
    """Batch-create AI architecture diagrams from manifests."""


@cli.command()
def catalog() -> None:
    """List supported diagram kinds and backend status."""
    rows = [
        ("plotneuralnet_cnn", "3D CNN / VGG / AlexNet / stacked feature maps", "cli-anything-plotneuralnet + Pillow preview"),
        ("drawio_flow", "Algorithm flowchart / training pipeline", "cli-anything-drawio + Pillow preview"),
        ("drawio_architecture", "Complex block topology / multi-branch system architecture", "cli-anything-drawio + Pillow preview"),
        ("graphviz_graph", "Probabilistic graph model / computation graph / tree-net", "Graphviz dot if installed + Pillow preview"),
        ("tikz_lstm", "LSTM / gated cell / math-heavy unit structure", "TikZ source + Pillow preview"),
        ("tikz_attention_gate", "Attention gate / math-heavy local module inset", "TikZ source + Pillow preview"),
        ("workflow", "Multi-software staged workflow with Draw.io master assembly", "PlotNeuralNet / TikZ / Graphviz / Draw.io stages"),
    ]
    click.echo("Supported kinds:")
    for kind, desc, backend in rows:
        click.echo(f"  {kind:<22} {desc}")
        click.echo(f"  {'':<22} backend: {backend}")
    click.echo()
    click.echo("Backend status:")
    click.echo(f"  cli-anything-plotneuralnet: {shutil.which('cli-anything-plotneuralnet') or 'not found'}")
    click.echo(f"  cli-anything-drawio:       {shutil.which('cli-anything-drawio') or 'not found'}")
    click.echo(f"  graphviz dot:             {shutil.which('dot') or 'not found'}")
    click.echo(f"  plotneuralnet harness:    {PLOTNEURALNET_HARNESS}")
    click.echo(f"  drawio harness:           {DRAWIO_HARNESS}")


@cli.command()
@click.option("--preset", default="deep-learning-gallery", show_default=True, type=click.Choice(["deep-learning-gallery", "blank"]))
@click.option("-o", "--output", required=True, type=click.Path(), help="Absolute output manifest path.")
@click.option("--project", default="diagram_batch", show_default=True)
def init(preset: str, output: str, project: str) -> None:
    """Create a starter YAML manifest."""
    payload = deep_learning_gallery_manifest() if preset == "deep-learning-gallery" else blank_manifest(project)
    if preset == "blank":
        payload["project"] = project
    target = write_manifest(output, payload)
    click.echo(f"Created manifest: {target}")


@cli.group()
def workflow() -> None:
    """Run multi-software staged diagram workflows."""


@workflow.command("init-reference")
@click.option("-o", "--output", required=True, type=click.Path(), help="Absolute output workflow manifest path.")
@click.option("--reference-1", default="", type=click.Path(), help="Original reference image for the first figure. Used as a locked Draw.io tracing underlay.")
@click.option("--reference-2", default="", type=click.Path(), help="Original reference image for the second figure. Used as a locked Draw.io tracing underlay.")
def workflow_init_reference(output: str, reference_1: str, reference_2: str) -> None:
    """Create the reference-replica multi-software workflow manifest."""
    ref1_path = abs_path(reference_1) if reference_1 else None
    ref2_path = abs_path(reference_2) if reference_2 else None
    if ref1_path and not ref1_path.is_file():
        raise click.ClickException(f"Reference 1 image not found: {ref1_path}")
    if ref2_path and not ref2_path.is_file():
        raise click.ClickException(f"Reference 2 image not found: {ref2_path}")
    ref1 = str(ref1_path) if ref1_path else None
    ref2 = str(ref2_path) if ref2_path else None
    target = write_manifest(output, reference_workflow_manifest(ref1, ref2))
    click.echo(f"Created workflow manifest: {target}")


@workflow.command("plan")
@click.argument("manifest", type=click.Path(exists=True))
@click.option("-o", "--output", default="", type=click.Path(), help="Absolute output JSON path for the tool plan.")
@click.option("--only", "only_ids", multiple=True, help="Plan only matching workflow id. Can be repeated.")
def workflow_plan(manifest: str, output: str, only_ids: tuple[str, ...]) -> None:
    """Classify figure components and assign each one to the right tool before rendering."""
    out_path = abs_path(output) if output else abs_path(manifest).with_suffix(".tool_plan.json")
    plan = plan_workflow_manifest(manifest, out_path, only_ids=only_ids)
    click.echo(f"Planned {len(plan['workflows'])} workflow(s). Tool plan: {out_path}")


@workflow.command("render")
@click.argument("manifest", type=click.Path(exists=True))
@click.option("--out-dir", default=str(DEFAULT_OUTPUT_DIR), show_default=True, type=click.Path(), help="Absolute output directory.")
@click.option("--only", "only_ids", multiple=True, help="Render only matching workflow id. Can be repeated.")
@click.option(
    "--source-format",
    "source_formats",
    multiple=True,
    type=click.Choice(["drawio", "svg", "pdf", "vsdx"], case_sensitive=False),
    help="Final source format to place in deliverables. Repeat for multiple formats. PNG is always included.",
)
def workflow_render(manifest: str, out_dir: str, only_ids: tuple[str, ...], source_formats: tuple[str, ...]) -> None:
    """Execute staged backends and compose a Draw.io master assembly."""
    index = render_workflow_manifest(manifest, out_dir, only_ids, source_formats=source_formats)
    click.echo(f"Rendered {len(index['results'])} workflow(s). Index: {index['output_dir']}\\workflow_index.json")


@cli.command("brief")
@click.option("--text", default="", help="Text brief. Use this to create a starter manifest from a rough request.")
@click.option("--image", "image_path", default="", type=click.Path(), help="Reference image path recorded in the manifest.")
@click.option("-o", "--output", required=True, type=click.Path(), help="Absolute output manifest path.")
def brief(text: str, image_path: str, output: str) -> None:
    """Create an editable starter manifest from text/image references."""
    lower = text.lower()
    payload = blank_manifest("brief_diagram_batch")
    payload["brief"] = text
    if image_path:
        payload["reference_image"] = str(abs_path(image_path))
    if any(token in lower for token in ["cnn", "vgg", "alexnet", "卷积", "3d"]):
        payload["figures"].append(deep_learning_gallery_manifest()["figures"][0])
    if any(token in lower for token in ["flow", "流程", "pipeline", "训练"]):
        payload["figures"].append(deep_learning_gallery_manifest()["figures"][2])
    if any(token in lower for token in ["architecture", "架构", "系统", "branch", "fusion"]):
        payload["figures"].append(deep_learning_gallery_manifest()["figures"][1])
    if any(token in lower for token in ["lstm", "门控", "gate"]):
        payload["figures"].append(deep_learning_gallery_manifest()["figures"][3])
    if any(token in lower for token in ["graph", "概率", "节点", "tree", "计算图"]):
        payload["figures"].append(deep_learning_gallery_manifest()["figures"][4])
    if not payload["figures"]:
        payload["figures"] = deep_learning_gallery_manifest()["figures"][:2]
    target = write_manifest(output, payload)
    click.echo(f"Created starter manifest: {target}")


@cli.command()
@click.option(
    "--plan",
    "plan_path",
    required=True,
    type=click.Path(exists=True),
    help=f"Absolute path to a component plan JSON/YAML (at most {MODULE_LIMIT} modules).",
)
@click.option(
    "--reference",
    "reference_image",
    default="",
    type=click.Path(),
    help="Optional absolute path to a reference image used as a locked Draw.io trace underlay.",
)
@click.option(
    "--out-dir",
    "out_dir",
    default=str(DEFAULT_OUTPUT_DIR),
    show_default=True,
    type=click.Path(),
    help="Absolute output directory.",
)
@click.option("--project", "project_name", default="", help="Optional project name override.")
def replicate(plan_path: str, reference_image: str, out_dir: str, project_name: str) -> None:
    """End-to-end replicate: component plan -> per-module backend rendering -> Draw.io master assembly.

    Always writes PNG plus .drawio, .svg, and .vsdx (when draw.io Desktop is available) into deliverables/.
    """
    summary = replicate_from_plan(
        plan_path,
        out_dir,
        reference_image=reference_image or None,
        project_name=project_name or None,
    )
    click.echo(f"Modules: {summary['module_count']} / {summary['module_limit']}")
    click.echo(f"Tool plan: {summary['tool_plan_path']}")
    click.echo(f"Workflow dir: {summary['workflow_dir']}")
    click.echo(f"Deliverables: {summary['deliverables_dir']}")
    click.echo(f"VSDX export status: {summary['vsdx_status']}")
    for warning in summary["warnings"]:
        click.echo(f"WARNING: {warning}")


@cli.command()
@click.argument("manifest", type=click.Path(exists=True))
@click.option("--out-dir", default=str(DEFAULT_OUTPUT_DIR), show_default=True, type=click.Path(), help="Absolute output directory.")
@click.option("--only", "only_ids", multiple=True, help="Render only matching figure id. Can be repeated.")
def render(manifest: str, out_dir: str, only_ids: tuple[str, ...]) -> None:
    """Render every figure in a manifest."""
    payload = load_manifest(manifest)
    target_dir = abs_path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    figures = payload.get("figures", [])
    if only_ids:
        figures = [figure for figure in figures if figure.get("id") in set(only_ids)]
    if not figures:
        raise click.ClickException("No figures to render.")
    results = []
    for figure in figures:
        kind = figure.get("kind")
        renderer = RENDERERS.get(kind)
        if renderer is None:
            raise click.ClickException(f"Unsupported figure kind: {kind}")
        if not figure.get("id"):
            raise click.ClickException("Every figure must include an id.")
        click.echo(f"Rendering {figure['id']} ({kind})...")
        result = renderer(figure, target_dir)
        write_json(target_dir / figure["id"] / "metadata.json", result)
        results.append(result)
    index = {"manifest": str(abs_path(manifest)), "output_dir": str(target_dir), "results": results}
    write_json(target_dir / "index.json", index)
    click.echo(f"Rendered {len(results)} figure(s). Index: {target_dir / 'index.json'}")


if __name__ == "__main__":
    cli()
