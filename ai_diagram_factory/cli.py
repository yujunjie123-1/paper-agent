from __future__ import annotations

import json
import shutil
from pathlib import Path

import click

from . import __version__
from .config import DEFAULT_OUTPUT_DIR, DRAWIO_HARNESS, PLOTNEURALNET_HARNESS
from .io import abs_path, load_manifest, write_json, write_manifest
from .renderers import RENDERERS
from .templates import blank_manifest, deep_learning_gallery_manifest


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
