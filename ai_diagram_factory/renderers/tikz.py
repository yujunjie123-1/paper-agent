from __future__ import annotations

from pathlib import Path
from typing import Any

from ..canvas import draw_arrow, draw_centered_text, draw_round_rect, load_font, new_canvas, save_png
from ..latex_utils import compile_tikz_body_to_svg
from ..styles import PALETTE


def render_tikz_lstm(figure: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    fig_dir = out_dir / figure["id"]
    fig_dir.mkdir(parents=True, exist_ok=True)
    png_path = fig_dir / f"{figure['id']}.png"
    body = _lstm_body(figure)
    latex_result = compile_tikz_body_to_svg(body, fig_dir, figure["id"])
    sources = [latex_result["tex"]]
    if latex_result.get("pdf"):
        sources.append(latex_result["pdf"])
    if latex_result.get("svg"):
        sources.append(latex_result["svg"])
        _rasterize_svg_to_png(latex_result["svg"], png_path)
    else:
        _render_lstm_png(figure, png_path)
    if not png_path.exists():
        _render_lstm_png(figure, png_path)
    result: dict[str, Any] = {
        "id": figure["id"],
        "kind": "tikz_lstm",
        "png": str(png_path),
        "sources": sources,
        "backend": _latex_backend_status(latex_result),
    }
    if latex_result.get("svg"):
        result["svg"] = latex_result["svg"]
    return result


def render_tikz_attention_gate(figure: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    fig_dir = out_dir / figure["id"]
    fig_dir.mkdir(parents=True, exist_ok=True)
    png_path = fig_dir / f"{figure['id']}.png"
    body = _attention_gate_body(figure)
    latex_result = compile_tikz_body_to_svg(body, fig_dir, figure["id"])
    sources = [latex_result["tex"]]
    if latex_result.get("pdf"):
        sources.append(latex_result["pdf"])
    if latex_result.get("svg"):
        sources.append(latex_result["svg"])
        _rasterize_svg_to_png(latex_result["svg"], png_path)
    else:
        _render_attention_gate_png(figure, png_path)
    if not png_path.exists():
        _render_attention_gate_png(figure, png_path)
    result: dict[str, Any] = {
        "id": figure["id"],
        "kind": "tikz_attention_gate",
        "png": str(png_path),
        "sources": sources,
        "backend": _latex_backend_status(latex_result),
    }
    if latex_result.get("svg"):
        result["svg"] = latex_result["svg"]
    return result


def render_tikz_module(figure: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    """Generic TikZ module renderer.

    The figure must provide a ``body`` field containing a complete
    ``\\begin{tikzpicture}...\\end{tikzpicture}`` block. Optional fields:
    ``libraries`` (list of TikZ library names), ``packages`` (list of extra
    LaTeX packages), ``preamble`` (raw LaTeX before \\begin{document}),
    ``border_pt`` (standalone border in pt).
    """
    fig_dir = out_dir / figure["id"]
    fig_dir.mkdir(parents=True, exist_ok=True)
    png_path = fig_dir / f"{figure['id']}.png"
    body = figure.get("body") or _placeholder_body(figure)
    latex_result = compile_tikz_body_to_svg(
        body,
        fig_dir,
        figure["id"],
        libraries=figure.get("libraries"),
        extra_packages=figure.get("packages"),
        preamble=figure.get("preamble", ""),
        border_pt=int(figure.get("border_pt", 2)),
        engine=figure.get("engine", "auto"),
        text_mode=figure.get("text_mode", "paths"),
    )
    sources = [latex_result["tex"]]
    if latex_result.get("pdf"):
        sources.append(latex_result["pdf"])
    if latex_result.get("svg"):
        sources.append(latex_result["svg"])
        _rasterize_svg_to_png(latex_result["svg"], png_path)
    if not png_path.exists():
        _render_module_fallback_png(figure, png_path)
    result: dict[str, Any] = {
        "id": figure["id"],
        "kind": "tikz_module",
        "png": str(png_path),
        "sources": sources,
        "backend": _latex_backend_status(latex_result),
    }
    if latex_result.get("svg"):
        result["svg"] = latex_result["svg"]
    return result


def _latex_backend_status(latex_result: dict[str, Any]) -> dict[str, Any]:
    pdf_status = latex_result.get("pdf_status", {}).get("status")
    svg_status = latex_result.get("svg_status", {}).get("status")
    engine = latex_result.get("engine", "auto")
    if pdf_status == "ok" and svg_status == "ok":
        return {"status": "tikz_svg", "engine": engine}
    if pdf_status == "ok":
        return {"status": "latex_pdf_only", "engine": engine, "svg_status": svg_status}
    return {"status": "pillow_preview", "engine": engine, "pdf_status": pdf_status}


def _rasterize_svg_to_png(svg_path: str, png_path: Path) -> None:
    try:
        import cairosvg

        cairosvg.svg2png(url=svg_path, write_to=str(png_path))
    except Exception as exc:
        png_path.with_suffix(".render-error.txt").write_text(str(exc), encoding="utf-8")


def _placeholder_body(figure: dict[str, Any]) -> str:
    title = figure.get("title", figure.get("id", ""))
    return (
        "\\begin{tikzpicture}[>=Stealth]\n"
        f"  \\node[draw, rounded corners, fill=cyan!8, minimum width=4cm, minimum height=2cm] (n) {{{title}}};\n"
        "\\end{tikzpicture}\n"
    )


def _lstm_body(figure: dict[str, Any]) -> str:
    title = figure.get("title", "LSTM Cell")
    return (
        "\\begin{tikzpicture}[>=Stealth, every node/.style={font=\\small}]\n"
        f"  \\node[draw, rounded corners, fill=cyan!8, minimum width=10cm, minimum height=4.6cm] (cell) {{{title}}};\n"
        "  \\node[draw, circle, fill=white] (mul1) at (-3,0.8) {$\\times$};\n"
        "  \\node[draw, circle, fill=white] (add) at (-1,0.8) {$+$};\n"
        "  \\node[draw, circle, fill=white] (mul2) at (1.2,0.8) {$\\times$};\n"
        "  \\node[draw, rounded corners, fill=red!12] (f) at (-3,-0.8) {$f_t$};\n"
        "  \\node[draw, rounded corners, fill=red!12] (i) at (-1.5,-0.8) {$i_t$};\n"
        "  \\node[draw, rounded corners, fill=red!12] (c) at (0,-0.8) {$\\tilde{c}_t$};\n"
        "  \\node[draw, rounded corners, fill=red!12] (o) at (1.5,-0.8) {$o_t$};\n"
        "  \\draw[->] (-5,0.8) -- (mul1);\n"
        "  \\draw[->] (mul1) -- (add);\n"
        "  \\draw[->] (add) -- (mul2);\n"
        "  \\draw[->] (mul2) -- (5,0.8);\n"
        "  \\draw[->] (-4,-2.2) -- (f);\n"
        "  \\draw[->] (-4,-2.2) -- (i);\n"
        "  \\draw[->] (-4,-2.2) -- (c);\n"
        "  \\draw[->] (-4,-2.2) -- (o);\n"
        "  \\draw[->] (f) -- (mul1);\n"
        "  \\draw[->] (i) -- (add);\n"
        "  \\draw[->] (c) -- (add);\n"
        "  \\draw[->] (o) -- (mul2);\n"
        "\\end{tikzpicture}\n"
    )


def _attention_gate_body(figure: dict[str, Any]) -> str:
    title = figure.get("title", "Attention Gate")
    return (
        "\\begin{tikzpicture}[>=Stealth, every node/.style={font=\\small}]\n"
        "  \\node[draw, dashed, rounded corners, fill=cyan!4, minimum width=3.0cm, minimum height=4.6cm] (x) at (0,0) {$N\\times H\\times W\\times C$};\n"
        "  \\node[draw, rounded corners, fill=cyan!18, minimum width=1.2cm, minimum height=0.8cm] (conv) at (3.0,0.8) {$1\\times1$ conv};\n"
        "  \\node[draw, dashed, rounded corners, fill=violet!5, minimum width=1.3cm, minimum height=2.4cm] (a) at (5.2,0.2) {$H\\times W\\times1\\times N$};\n"
        "  \\node[draw, rounded corners, fill=blue!18, minimum width=1.4cm, minimum height=0.8cm] (ca) at (7.3,1.2) {channel};\n"
        "  \\node[draw, rounded corners, fill=blue!18, minimum width=1.4cm, minimum height=0.8cm] (sa) at (7.3,-0.7) {spatial};\n"
        "  \\node[draw, circle, fill=white] (mul) at (9.0,0.2) {$\\otimes$};\n"
        "  \\node[draw, rounded corners, fill=red!12, minimum width=1.4cm, minimum height=0.9cm] (out) at (10.8,0.2) {$H\\times W\\times C$};\n"
        "  \\draw[->] (x) -- node[above] {conv} (conv);\n"
        "  \\draw[->] (conv) -- node[above] {concat} (a);\n"
        "  \\draw[->] (a) -- (ca);\n"
        "  \\draw[->] (a) -- (sa);\n"
        "  \\draw[->] (ca) -| (mul);\n"
        "  \\draw[->] (sa) -| (mul);\n"
        "  \\draw[->] (mul) -- (out);\n"
        f"  \\node at (5.4,2.5) {{{title}}};\n"
        "\\end{tikzpicture}\n"
    )


def _render_module_fallback_png(figure: dict[str, Any], png_path: Path) -> None:
    width, height = 600, 320
    img, draw = new_canvas(width, height, "#FFFFFF")
    title_font = load_font(22, bold=True)
    body_font = load_font(16)
    draw.text((30, 24), figure.get("title", figure.get("id", "TikZ module")), font=title_font, fill=PALETTE["ink"])
    box = (40, 90, width - 40, height - 40)
    draw_round_rect(draw, box, "#EFFBFF", "#638A9C", width=3, radius=18)
    description = figure.get("description", "TikZ source available; LaTeX/dvisvgm not run.")
    draw_centered_text(draw, box, description[:120], body_font, max_chars=18)
    save_png(img, png_path)


def _render_lstm_png(figure: dict[str, Any], png_path: Path) -> None:
    width, height = 980, 520
    img, draw = new_canvas(width, height, "#FFFFFF")
    title_font = load_font(32, bold=True)
    font = load_font(22)
    small = load_font(18)
    draw.text((55, 30), figure.get("title", "LSTM Cell"), font=title_font, fill=PALETTE["ink"])
    outer = (80, 110, 900, 420)
    draw_round_rect(draw, outer, "#EFFBFF", "#638A9C", width=4, radius=28)
    gates = [
        ("f_t", 210, 300, "#FFE0EA"),
        ("i_t", 370, 300, "#FFE0EA"),
        ("tanh", 530, 300, "#FFE0EA"),
        ("o_t", 690, 300, "#FFE0EA"),
    ]
    ops = [
        ("x", 230, 190),
        ("+", 450, 190),
        ("x", 690, 190),
    ]
    for label, x, y, fill in gates:
        box = (x - 58, y - 34, x + 58, y + 34)
        draw_round_rect(draw, box, fill, "#B4667A", width=3, radius=14)
        draw_centered_text(draw, box, label, font)
    for label, x, y in ops:
        box = (x - 32, y - 32, x + 32, y + 32)
        draw.ellipse(box, fill="#FFFFFF", outline="#333333", width=3)
        draw_centered_text(draw, box, label, font)
    draw_arrow(draw, (90, 190), (198, 190), width=3)
    draw_arrow(draw, (262, 190), (418, 190), width=3)
    draw_arrow(draw, (482, 190), (658, 190), width=3)
    draw_arrow(draw, (722, 190), (900, 190), width=3)
    draw.text((30, 180), "c_{t-1}", font=small, fill=PALETTE["muted"])
    draw.text((910, 180), "c_t", font=small, fill=PALETTE["muted"])
    draw.text((30, 365), "x_t, h_{t-1}", font=small, fill=PALETTE["muted"])
    draw.text((910, 365), "h_t", font=small, fill=PALETTE["muted"])
    for _, x, y, _ in gates:
        draw_arrow(draw, (x, y - 34), (x, 220), width=2)
    draw_arrow(draw, (80, 370), (180, 330), width=2)
    draw_arrow(draw, (80, 370), (340, 330), width=2)
    draw_arrow(draw, (80, 370), (500, 330), width=2)
    draw_arrow(draw, (80, 370), (660, 330), width=2)
    draw_arrow(draw, (690, 222), (900, 370), width=2)
    save_png(img, png_path)


def _render_attention_gate_png(figure: dict[str, Any], png_path: Path) -> None:
    width, height = 760, 300
    img, draw = new_canvas(width, height, "#FFFFFF")
    title_font = load_font(24, bold=True)
    font = load_font(17)
    small = load_font(14)
    draw.text((30, 18), figure.get("title", "Attention Gate"), font=title_font, fill=PALETTE["ink"])
    draw.rounded_rectangle((40, 70, 150, 240), radius=10, fill="#F0FBFF", outline="#0B9CE5", width=2)
    draw_centered_text(draw, (40, 70, 150, 240), "N×H×W×C", small, max_chars=10)
    draw_arrow(draw, (150, 155), (230, 155), fill="#222222", width=2)
    draw_round_rect(draw, (230, 118, 330, 192), "#E7F7FF", "#4F85A8", width=2, radius=10)
    draw_centered_text(draw, (230, 118, 330, 192), "1×1 conv\nC→1", small, max_chars=10)
    draw_arrow(draw, (330, 155), (400, 155), fill="#222222", width=2)
    draw.rounded_rectangle((400, 78, 505, 232), radius=10, fill="#FBF4FF", outline="#7532C8", width=2)
    draw_centered_text(draw, (400, 78, 505, 232), "H×W×1×N", small, max_chars=9)
    draw_arrow(draw, (505, 130), (590, 105), fill="#222222", width=2)
    draw_arrow(draw, (505, 180), (590, 205), fill="#222222", width=2)
    draw_round_rect(draw, (590, 78, 690, 130), "#DCEBFF", "#4F85A8", width=2, radius=8)
    draw_round_rect(draw, (590, 178, 690, 230), "#DCEBFF", "#4F85A8", width=2, radius=8)
    draw_centered_text(draw, (590, 78, 690, 130), "channel", font)
    draw_centered_text(draw, (590, 178, 690, 230), "spatial", font)
    draw.ellipse((690, 132, 734, 176), fill="#FFFFFF", outline="#222222", width=2)
    draw_centered_text(draw, (690, 132, 734, 176), "⊗", font)
    draw_arrow(draw, (690, 105), (712, 132), fill="#222222", width=2)
    draw_arrow(draw, (690, 205), (712, 176), fill="#222222", width=2)
    draw.text((676, 250), "H×W×C", font=small, fill=PALETTE["ink"])
    save_png(img, png_path)
