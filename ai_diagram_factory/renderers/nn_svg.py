from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any


def render_nn_svg_network(figure: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    """Render a small NN-SVG-style neural-network schematic.

    This is a local, dependency-free renderer inspired by NN-SVG's public
    modes: FCNN, LeNet-style CNN, and AlexNet-style deep CNN schematics. The
    generated SVG owns all intra-network links; Draw.io should only place the
    asset or add cross-module/missing arrows.
    """

    fig_dir = out_dir / figure["id"]
    fig_dir.mkdir(parents=True, exist_ok=True)
    svg_path = fig_dir / f"{figure['id']}.svg"
    png_path = fig_dir / f"{figure['id']}.png"

    mode = str(figure.get("mode", "fcnn")).lower().replace("-", "_")
    if mode in {"cnn", "lenet", "lenet_style"}:
        svg_text = _render_cnn_svg(figure, perspective=False)
    elif mode in {"deep", "alexnet", "alexnet_style", "3d"}:
        svg_text = _render_cnn_svg(figure, perspective=True)
    else:
        svg_text = _render_fcnn_svg(figure)

    svg_path.write_text(svg_text, encoding="utf-8")
    _write_png_from_svg(svg_text, png_path)
    return {
        "id": figure["id"],
        "kind": "nn_svg_network",
        "svg": str(svg_path),
        "png": str(png_path),
        "sources": [str(svg_path)],
        "backend": {
            "status": "nn_svg_style",
            "mode": mode,
            "line_ownership": "internal links are owned by nn_svg_network",
        },
    }


def _render_fcnn_svg(figure: dict[str, Any]) -> str:
    layers = _normalise_fcnn_layers(figure.get("layers", []))
    max_nodes = max(layer["size"] for layer in layers)
    width = float(figure.get("width", 220 + 150 * max(0, len(layers) - 1)))
    height = float(figure.get("height", max(260, 90 + max_nodes * 46)))
    margin_x = float(figure.get("margin_x", 80))
    margin_y = float(figure.get("margin_y", 58))
    node_r = float(figure.get("node_radius", 13))
    stroke = figure.get("stroke", "#46515c")
    fill = figure.get("fill", "#f7fbff")
    edge_color = figure.get("edge_color", "#9aa7b2")

    positions: list[list[tuple[float, float]]] = []
    for index, layer in enumerate(layers):
        x = margin_x if len(layers) == 1 else margin_x + index * ((width - margin_x * 2) / (len(layers) - 1))
        gap = (height - margin_y * 2) / max(1, layer["size"] - 1)
        if layer["size"] == 1:
            ys = [height / 2]
        else:
            ys = [margin_y + i * gap for i in range(layer["size"])]
        positions.append([(x, y) for y in ys])

    body = [_defs(), f'<rect width="{width:.2f}" height="{height:.2f}" fill="{figure.get("background", "transparent")}"/>']
    for left, right in zip(positions, positions[1:]):
        for sx, sy in left:
            for tx, ty in right:
                body.append(
                    f'<line x1="{sx:.2f}" y1="{sy:.2f}" x2="{tx:.2f}" y2="{ty:.2f}" '
                    f'stroke="{edge_color}" stroke-width="{figure.get("edge_width", 1.0)}" opacity="{figure.get("edge_opacity", 0.62)}"/>'
                )
    for layer_index, layer in enumerate(layers):
        for x, y in positions[layer_index]:
            body.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{node_r:.2f}" fill="{fill}" '
                f'stroke="{stroke}" stroke-width="1.5"/>'
            )
        if layer.get("label"):
            body.append(_text(positions[layer_index][0][0], height - 22, layer["label"], 14))
    if figure.get("title"):
        body.append(_text(width / 2, 28, figure["title"], 18, weight="600"))
    return _svg(width, height, body)


def _render_cnn_svg(figure: dict[str, Any], *, perspective: bool) -> str:
    layers = _normalise_cnn_layers(figure.get("layers", []))
    width = float(figure.get("width", max(520, 130 + len(layers) * 120)))
    height = float(figure.get("height", 320 if perspective else 260))
    base_y = float(figure.get("base_y", height * 0.48))
    x = float(figure.get("start_x", 70))
    gap = float(figure.get("gap", 112))
    edge_color = figure.get("edge_color", "#506d84")

    body = [_defs(), f'<rect width="{width:.2f}" height="{height:.2f}" fill="{figure.get("background", "transparent")}"/>']
    centers: list[tuple[float, float]] = []
    for index, layer in enumerate(layers):
        layer_x = x + index * gap
        block_w = float(layer.get("width", max(28, min(84, 18 + float(layer.get("channels", 8)) * 2.4))))
        block_h = float(layer.get("height", max(42, min(150, 34 + float(layer.get("size", 28)) * 2.2))))
        fill = layer.get("fill", _layer_fill(index))
        stroke = layer.get("stroke", "#405060")
        if perspective:
            depth = float(layer.get("depth", max(8, min(24, block_w * 0.28))))
            y = base_y - block_h / 2
            body.extend(_iso_block(layer_x, y, block_w, block_h, depth, fill, stroke))
            center = (layer_x + block_w + depth / 2, y + block_h / 2 - depth / 2)
            label_y = y + block_h + 32
        else:
            maps = max(1, int(layer.get("maps", 1)))
            stack_step = min(8.0, max(2.0, maps / 2))
            y = base_y - block_h / 2
            for offset in range(min(maps, 6) - 1, -1, -1):
                body.append(
                    f'<rect x="{layer_x + offset * stack_step:.2f}" y="{y - offset * stack_step:.2f}" '
                    f'width="{block_w:.2f}" height="{block_h:.2f}" fill="{fill}" stroke="{stroke}" '
                    f'stroke-width="1.2" opacity="0.94"/>'
                )
            center = (layer_x + block_w + stack_step * min(maps, 6) / 2, y + block_h / 2)
            label_y = y + block_h + 26
        centers.append(center)
        label = layer.get("label") or layer.get("name") or f"L{index + 1}"
        body.append(_text(center[0], label_y, label, int(layer.get("font_size", 13))))
    for start, end in zip(centers, centers[1:]):
        body.append(
            f'<line x1="{start[0]:.2f}" y1="{start[1]:.2f}" x2="{end[0]:.2f}" y2="{end[1]:.2f}" '
            f'stroke="{edge_color}" stroke-width="{figure.get("edge_width", 1.8)}" marker-end="url(#nn-svg-arrow)"/>'
        )
    if figure.get("title"):
        body.append(_text(width / 2, 28, figure["title"], 18, weight="600"))
    return _svg(width, height, body)


def _normalise_fcnn_layers(raw_layers: Any) -> list[dict[str, Any]]:
    if not raw_layers:
        return [{"size": 3, "label": "Input"}, {"size": 5, "label": "Hidden"}, {"size": 2, "label": "Output"}]
    layers: list[dict[str, Any]] = []
    for index, layer in enumerate(raw_layers):
        if isinstance(layer, int):
            layers.append({"size": max(1, layer), "label": f"Layer {index + 1}"})
        else:
            layers.append({"size": max(1, int(layer.get("size", layer.get("nodes", 3)))), "label": layer.get("label", "")})
    return layers


def _normalise_cnn_layers(raw_layers: Any) -> list[dict[str, Any]]:
    if raw_layers:
        return [dict(layer) for layer in raw_layers]
    return [
        {"label": "Input", "size": 64, "channels": 3, "maps": 1, "fill": "#e8eef7"},
        {"label": "Conv", "size": 48, "channels": 16, "maps": 4, "fill": "#cbe7ff"},
        {"label": "Pool", "size": 34, "channels": 16, "maps": 4, "fill": "#f8d6a8"},
        {"label": "Dense", "size": 18, "channels": 32, "maps": 1, "fill": "#d8c8f1"},
    ]


def _iso_block(x: float, y: float, width: float, height: float, depth: float, fill: str, stroke: str) -> list[str]:
    dx = depth
    dy = -depth
    top = f'{x:.2f},{y:.2f} {x + dx:.2f},{y + dy:.2f} {x + width + dx:.2f},{y + dy:.2f} {x + width:.2f},{y:.2f}'
    side = f'{x + width:.2f},{y:.2f} {x + width + dx:.2f},{y + dy:.2f} {x + width + dx:.2f},{y + height + dy:.2f} {x + width:.2f},{y + height:.2f}'
    front = f'{x:.2f},{y:.2f} {x + width:.2f},{y:.2f} {x + width:.2f},{y + height:.2f} {x:.2f},{y + height:.2f}'
    return [
        f'<polygon points="{top}" fill="{_shade(fill, 1.12)}" stroke="{stroke}" stroke-width="1.2"/>',
        f'<polygon points="{side}" fill="{_shade(fill, 0.88)}" stroke="{stroke}" stroke-width="1.2"/>',
        f'<polygon points="{front}" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>',
    ]


def _defs() -> str:
    return (
        '<defs><marker id="nn-svg-arrow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" '
        'orient="auto" markerUnits="userSpaceOnUse"><path d="M 0 0 L 9 4.5 L 0 9 z" fill="#506d84"/></marker></defs>'
    )


def _svg(width: float, height: float, body: list[str]) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.2f}" height="{height:.2f}" '
        f'viewBox="0 0 {width:.2f} {height:.2f}">\n'
        + "\n".join(body)
        + "\n</svg>\n"
    )


def _text(x: float, y: float, text: Any, size: int, *, weight: str = "400") -> str:
    return (
        f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="middle" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="#222222">{escape(str(text))}</text>'
    )


def _layer_fill(index: int) -> str:
    colors = ["#cbe7ff", "#f8d6a8", "#d8f0ce", "#f4c9d8", "#d8c8f1"]
    return colors[index % len(colors)]


def _shade(hex_color: str, factor: float) -> str:
    color = hex_color.lstrip("#")
    if len(color) != 6:
        return hex_color
    channels = [int(color[i : i + 2], 16) for i in (0, 2, 4)]
    shaded = [max(0, min(255, int(channel * factor))) for channel in channels]
    return "#" + "".join(f"{channel:02x}" for channel in shaded)


def _write_png_from_svg(svg_text: str, png_path: Path) -> None:
    try:
        import cairosvg

        cairosvg.svg2png(bytestring=svg_text.encode("utf-8"), write_to=str(png_path))
    except Exception as exc:
        png_path.with_suffix(".render-error.txt").write_text(str(exc), encoding="utf-8")
