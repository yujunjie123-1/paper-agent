from __future__ import annotations

from pathlib import Path
from typing import Any


def render_svg_module(figure: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    from ..workflow import _connector_to_svg, _label_to_svg, _shape_to_svg
    """Render a self-contained editable SVG asset for one module.

    The module owns all of its own shapes/connectors/labels in *local*
    coordinates (origin at 0, 0; width/height matching the module bounding
    box). Draw.io master imports the SVG as an ``<image>`` placement and
    only owns cross-module connectors and global labels.
    """
    fig_dir = out_dir / figure["id"]
    fig_dir.mkdir(parents=True, exist_ok=True)
    svg_path = fig_dir / f"{figure['id']}.svg"
    png_path = fig_dir / f"{figure['id']}.png"

    shapes = figure.get("shapes", []) or []
    connectors = figure.get("connectors", []) or []
    labels = figure.get("labels", []) or []
    width, height = _module_size(figure)
    background = figure.get("background", "transparent")

    body: list[str] = []
    if background and background != "transparent":
        body.append(
            f'<rect x="0" y="0" width="{width}" height="{height}" fill="{background}"/>'
        )
    for shape in shapes:
        body.extend(_shape_to_svg(shape))
    for connector in connectors:
        body.append(_connector_to_svg(connector))
    for label in labels:
        body.append(_label_to_svg(label))

    svg_text = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.2f}" height="{height:.2f}" '
        f'viewBox="0 0 {width:.2f} {height:.2f}">\n'
        + "\n".join(body)
        + "\n</svg>\n"
    )
    svg_path.write_text(svg_text, encoding="utf-8")
    _write_png_from_svg(svg_text, png_path)

    return {
        "id": figure["id"],
        "kind": "svg_module",
        "svg": str(svg_path),
        "png": str(png_path),
        "sources": [str(svg_path)],
        "backend": {"status": "svg_module"},
    }


def _module_size(figure: dict[str, Any]) -> tuple[float, float]:
    if "width" in figure and "height" in figure:
        return float(figure["width"]), float(figure["height"])
    box = figure.get("box_xyxy")
    if box and len(box) == 4:
        width = max(1.0, float(box[2]) - float(box[0]))
        height = max(1.0, float(box[3]) - float(box[1]))
        return width, height
    return 200.0, 200.0


def _write_png_from_svg(svg_text: str, png_path: Path) -> None:
    try:
        import cairosvg

        cairosvg.svg2png(bytestring=svg_text.encode("utf-8"), write_to=str(png_path))
    except Exception as exc:
        png_path.with_suffix(".render-error.txt").write_text(str(exc), encoding="utf-8")
