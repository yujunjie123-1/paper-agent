from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

from ..canvas import draw_arrow, draw_centered_text, draw_round_rect, load_font, new_canvas, save_png
from ..styles import PALETTE


def render_tikz_lstm(figure: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    fig_dir = out_dir / figure["id"]
    fig_dir.mkdir(parents=True, exist_ok=True)
    tex_path = fig_dir / f"{figure['id']}.tex"
    png_path = fig_dir / f"{figure['id']}.png"
    tex_path.write_text(_build_lstm_tex(figure), encoding="utf-8")
    latex_backend = _try_pdflatex(tex_path)
    _render_lstm_png(figure, png_path)
    sources = [str(tex_path)]
    pdf_path = tex_path.with_suffix(".pdf")
    if pdf_path.exists():
        sources.append(str(pdf_path))
    return {"id": figure["id"], "kind": "tikz_lstm", "png": str(png_path), "sources": sources, "backend": latex_backend}


def render_tikz_attention_gate(figure: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    fig_dir = out_dir / figure["id"]
    fig_dir.mkdir(parents=True, exist_ok=True)
    tex_path = fig_dir / f"{figure['id']}.tex"
    png_path = fig_dir / f"{figure['id']}.png"
    tex_path.write_text(_build_attention_gate_tex(figure), encoding="utf-8")
    latex_backend = _try_pdflatex(tex_path)
    _render_attention_gate_png(figure, png_path)
    sources = [str(tex_path)]
    pdf_path = tex_path.with_suffix(".pdf")
    if pdf_path.exists():
        sources.append(str(pdf_path))
    return {"id": figure["id"], "kind": "tikz_attention_gate", "png": str(png_path), "sources": sources, "backend": latex_backend}


def _try_pdflatex(tex_path: Path) -> dict[str, Any]:
    pdflatex = shutil.which("pdflatex") or _known_pdflatex_path()
    if not pdflatex:
        return {"status": "pillow_preview", "reason": "pdflatex executable not found"}
    ascii_root = Path("C:/Users/86180/Documents/ai_diagram_factory_latex_tmp")
    ascii_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="tikz_", dir=str(ascii_root)) as tmp:
        tmp_dir = Path(tmp)
        tmp_tex = tmp_dir / tex_path.name
        shutil.copy2(tex_path, tmp_tex)
        result = _run_pdflatex(pdflatex, tmp_tex)
        tmp_pdf = tmp_tex.with_suffix(".pdf")
        if result.returncode == 0 and tmp_pdf.exists():
            final_pdf = tex_path.with_suffix(".pdf")
            shutil.copy2(tmp_pdf, final_pdf)
            return {"status": "pdflatex", "pdf": str(final_pdf)}
        return {"status": "pillow_preview", "returncode": result.returncode, "stderr": result.stderr[-2000:], "stdout": result.stdout[-2000:]}


def _run_pdflatex(pdflatex: str, tex_path: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            [pdflatex, "-interaction=nonstopmode", "-halt-on-error", str(tex_path.name)],
            cwd=str(tex_path.parent),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(exc.cmd, 124, stdout=exc.stdout or "", stderr=str(exc))


def _known_pdflatex_path() -> str | None:
    candidates = [
        Path("C:/Users/86180/AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdflatex.exe"),
        Path("C:/Program Files/MiKTeX/miktex/bin/x64/pdflatex.exe"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return None


def _build_lstm_tex(figure: dict[str, Any]) -> str:
    title = figure.get("title", "LSTM Cell")
    return rf"""\documentclass{{article}}
\usepackage[margin=0.3in]{{geometry}}
\usepackage{{tikz}}
\pagestyle{{empty}}
\usetikzlibrary{{positioning,arrows.meta,calc}}
\begin{{document}}
\begin{{center}}
\begin{{tikzpicture}}[>=Stealth, node distance=1.2cm, every node/.style={{font=\small}}]
\node[draw, rounded corners, fill=cyan!8, minimum width=10cm, minimum height=4.6cm] (cell) {{{title}}};
\node[draw, circle, fill=white] (mul1) at (-3,0.8) {{$\times$}};
\node[draw, circle, fill=white] (add) at (-1,0.8) {{$+$}};
\node[draw, circle, fill=white] (mul2) at (1.2,0.8) {{$\times$}};
\node[draw, rounded corners, fill=red!12] (f) at (-3,-0.8) {{$f_t$}};
\node[draw, rounded corners, fill=red!12] (i) at (-1.5,-0.8) {{$i_t$}};
\node[draw, rounded corners, fill=red!12] (c) at (0,-0.8) {{$\tilde{{c}}_t$}};
\node[draw, rounded corners, fill=red!12] (o) at (1.5,-0.8) {{$o_t$}};
\draw[->] (-5,0.8) -- (mul1);
\draw[->] (mul1) -- (add);
\draw[->] (add) -- (mul2);
\draw[->] (mul2) -- (5,0.8);
\draw[->] (-4,-2.2) -- (f);
\draw[->] (-4,-2.2) -- (i);
\draw[->] (-4,-2.2) -- (c);
\draw[->] (-4,-2.2) -- (o);
\draw[->] (f) -- (mul1);
\draw[->] (i) -- (add);
\draw[->] (c) -- (add);
\draw[->] (o) -- (mul2);
\end{{tikzpicture}}
\end{{center}}
\end{{document}}
"""


def _build_attention_gate_tex(figure: dict[str, Any]) -> str:
    title = figure.get("title", "Attention Gate")
    return rf"""\documentclass{{article}}
\usepackage[margin=0.2in]{{geometry}}
\usepackage{{tikz}}
\pagestyle{{empty}}
\usetikzlibrary{{positioning,arrows.meta,calc}}
\begin{{document}}
\begin{{center}}
\begin{{tikzpicture}}[>=Stealth, node distance=0.9cm, every node/.style={{font=\small}}]
\node[draw, dashed, rounded corners, fill=cyan!4, minimum width=3.0cm, minimum height=4.6cm] (x) at (0,0) {{$N\times H\times W\times C$}};
\node[draw, rounded corners, fill=cyan!18, minimum width=1.2cm, minimum height=0.8cm] (conv) at (3.0,0.8) {{$1\times1$ conv}};
\node[draw, dashed, rounded corners, fill=violet!5, minimum width=1.3cm, minimum height=2.4cm] (a) at (5.2,0.2) {{$H\times W\times1\times N$}};
\node[draw, rounded corners, fill=blue!18, minimum width=1.4cm, minimum height=0.8cm] (ca) at (7.3,1.2) {{channel}};
\node[draw, rounded corners, fill=blue!18, minimum width=1.4cm, minimum height=0.8cm] (sa) at (7.3,-0.7) {{spatial}};
\node[draw, circle, fill=white] (mul) at (9.0,0.2) {{$\otimes$}};
\node[draw, rounded corners, fill=red!12, minimum width=1.4cm, minimum height=0.9cm] (out) at (10.8,0.2) {{$H\times W\times C$}};
\draw[->] (x) -- node[above] {{conv}} (conv);
\draw[->] (conv) -- node[above] {{concat}} (a);
\draw[->] (a) -- (ca);
\draw[->] (a) -- (sa);
\draw[->] (ca) -| (mul);
\draw[->] (sa) -| (mul);
\draw[->] (mul) -- (out);
\node at (5.4,2.5) {{{title}}};
\end{{tikzpicture}}
\end{{center}}
\end{{document}}
"""


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
