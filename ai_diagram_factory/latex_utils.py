"""Shared LaTeX / dvisvgm helpers used by TikZ-driven renderers.

The pipeline is::

    .tex (standalone document class)
        --> pdflatex / xelatex  -->  .pdf
        --> dvisvgm --pdf / dvisvgm --no-fonts  -->  .svg

Tight bounding boxes come from ``\\documentclass[border=2pt]{standalone}``,
so the resulting SVG drops cleanly into Draw.io as a placement asset.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any

from .config import LATEX_TEMP_DIR


PDFLATEX_CANDIDATES = (
    Path("C:/Users/86180/AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdflatex.exe"),
    Path("C:/Program Files/MiKTeX/miktex/bin/x64/pdflatex.exe"),
    Path("/usr/bin/pdflatex"),
    Path("/usr/local/bin/pdflatex"),
)

XELATEX_CANDIDATES = (
    Path("C:/Users/86180/AppData/Local/Programs/MiKTeX/miktex/bin/x64/xelatex.exe"),
    Path("C:/Program Files/MiKTeX/miktex/bin/x64/xelatex.exe"),
    Path("/usr/bin/xelatex"),
    Path("/usr/local/bin/xelatex"),
)

DVISVGM_CANDIDATES = (
    Path("C:/Users/86180/AppData/Local/Programs/MiKTeX/miktex/bin/x64/dvisvgm.exe"),
    Path("C:/Program Files/MiKTeX/miktex/bin/x64/dvisvgm.exe"),
    Path("/usr/bin/dvisvgm"),
    Path("/usr/local/bin/dvisvgm"),
)

LATEX_ENGINE_CANDIDATES = ("pdflatex", "xelatex")


def find_pdflatex() -> str | None:
    return shutil.which("pdflatex") or _first_existing(PDFLATEX_CANDIDATES)


def find_xelatex() -> str | None:
    return shutil.which("xelatex") or _first_existing(XELATEX_CANDIDATES)


def find_dvisvgm() -> str | None:
    return shutil.which("dvisvgm") or _first_existing(DVISVGM_CANDIDATES)


def find_latex_engine(engine: str) -> str | None:
    normalized = engine.lower().strip()
    if normalized == "pdflatex":
        return find_pdflatex()
    if normalized == "xelatex":
        return find_xelatex()
    raise ValueError(f"Unsupported LaTeX engine: {engine}")


def _first_existing(paths: tuple[Path, ...]) -> str | None:
    for candidate in paths:
        if candidate.is_file():
            return str(candidate)
    return None


def build_standalone_tex(
    body: str,
    libraries: list[str] | None = None,
    extra_packages: list[str] | None = None,
    preamble: str = "",
    border_pt: int = 2,
    engine: str = "pdflatex",
) -> str:
    """Wrap a TikZ ``\\begin{tikzpicture}...\\end{tikzpicture}`` body in a
    standalone document so the resulting PDF/SVG has a tight bounding box."""
    libs = ", ".join(libraries or ["arrows.meta", "positioning", "calc", "shapes.geometric"])
    packages = "\n".join(f"\\usepackage{{{pkg}}}" for pkg in (extra_packages or []))
    unicode_preamble = ""
    if engine == "xelatex":
        unicode_preamble = r"""
\usepackage{fontspec}
\IfFontExistsTF{Microsoft YaHei}{\setmainfont{Microsoft YaHei}}{\IfFontExistsTF{Times New Roman}{\setmainfont{Times New Roman}}{}}
"""
    return rf"""\documentclass[border={border_pt}pt]{{standalone}}
\usepackage{{tikz}}
\usepackage{{amsmath,amssymb}}
{packages}
\usetikzlibrary{{{libs}}}
{unicode_preamble}
{preamble}
\begin{{document}}
{body}
\end{{document}}
"""


def compile_tex_to_pdf(tex_path: Path, engine: str = "pdflatex") -> dict[str, Any]:
    """Compile the given .tex file in an ASCII-safe temp directory and return
    a status dict that includes the produced PDF path on success."""
    if os.environ.get("AI_DIAGRAM_FACTORY_SKIP_LATEX") == "1":
        return {"status": "skipped", "engine": engine, "reason": "disabled by AI_DIAGRAM_FACTORY_SKIP_LATEX"}
    engine_path = find_latex_engine(engine)
    if not engine_path:
        return {"status": f"no_{engine}", "engine": engine}
    engine_probe = _probe_executable(engine_path, "--version")
    if engine_probe["status"] != "ok":
        return {
            "status": f"{engine}_unavailable",
            "engine": engine,
            "reason": engine_probe["reason"],
            "stdout": engine_probe.get("stdout", ""),
            "stderr": engine_probe.get("stderr", ""),
        }
    ascii_root = LATEX_TEMP_DIR
    ascii_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="aidf_tex_", dir=str(ascii_root)) as tmp:
        tmp_dir = Path(tmp)
        tmp_tex = tmp_dir / "main.tex"
        tmp_tex.write_text(tex_path.read_text(encoding="utf-8"), encoding="utf-8")
        cmd = [engine_path, "-interaction=nonstopmode", "-halt-on-error", "main.tex"]
        try:
            result = subprocess.run(
                cmd,
                cwd=str(tmp_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )
        except subprocess.TimeoutExpired as exc:
            return {"status": "timeout", "engine": engine, "stderr": str(exc), "command": cmd}
        tmp_pdf = tmp_dir / "main.pdf"
        if result.returncode != 0 or not tmp_pdf.exists():
            _write_log(tex_path.with_suffix(f".{engine}.log"), result.stdout, result.stderr)
            return {
                "status": f"{engine}_failed",
                "engine": engine,
                "returncode": result.returncode,
                "stderr": result.stderr[-2000:],
                "stdout": result.stdout[-2000:],
                "command": cmd,
            }
        final_pdf = tex_path.with_suffix(".pdf")
        shutil.copy2(tmp_pdf, final_pdf)
        _write_log(tex_path.with_suffix(f".{engine}.log"), result.stdout, result.stderr)
        return {"status": "ok", "engine": engine, "pdf": str(final_pdf), "command": cmd}


def convert_pdf_to_svg(pdf_path: Path, svg_path: Path, text_mode: str = "paths") -> dict[str, Any]:
    """Convert a PDF to SVG via ``dvisvgm --pdf``. Requires dvisvgm + Ghostscript."""
    dvisvgm = find_dvisvgm()
    if not dvisvgm:
        return {"status": "no_dvisvgm"}
    dvisvgm_probe = _probe_executable(dvisvgm, "--version")
    if dvisvgm_probe["status"] != "ok":
        return {
            "status": "dvisvgm_unavailable",
            "reason": dvisvgm_probe["reason"],
            "stdout": dvisvgm_probe.get("stdout", ""),
            "stderr": dvisvgm_probe.get("stderr", ""),
        }
    ascii_root = LATEX_TEMP_DIR
    ascii_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="aidf_svg_", dir=str(ascii_root)) as tmp:
        tmp_dir = Path(tmp)
        tmp_pdf = tmp_dir / "main.pdf"
        tmp_svg = tmp_dir / "main.svg"
        shutil.copy2(pdf_path, tmp_pdf)
        cmd = [dvisvgm, "--pdf", "--exact-bbox", "main.pdf", "-o", "main.svg"]
        if text_mode == "paths":
            cmd.insert(2, "--no-fonts")
        try:
            result = subprocess.run(
                cmd,
                cwd=str(tmp_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )
        except Exception as exc:
            return {"status": "error", "reason": str(exc), "command": cmd}
        _write_log(svg_path.with_suffix(".dvisvgm.log"), result.stdout, result.stderr)
        if result.returncode == 0 and tmp_svg.is_file():
            shutil.copy2(tmp_svg, svg_path)
            return {"status": "ok", "svg": str(svg_path), "command": cmd, "text_mode": text_mode}
        return {
            "status": "dvisvgm_failed",
            "returncode": result.returncode,
            "stderr": result.stderr[-2000:],
            "stdout": result.stdout[-2000:],
            "command": cmd,
            "text_mode": text_mode,
        }


def compile_tikz_body_to_svg(
    body: str,
    out_dir: Path,
    name: str,
    libraries: list[str] | None = None,
    extra_packages: list[str] | None = None,
    preamble: str = "",
    border_pt: int = 2,
    engine: str = "auto",
    text_mode: str = "paths",
) -> dict[str, Any]:
    """High-level helper: write a TikZ body, compile, convert to SVG.

    Always writes the ``.tex`` source. Returns a status dict carrying the
    produced ``.pdf`` and ``.svg`` paths when each step succeeds.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    tex_path = out_dir / f"{name}.tex"
    pdf_path = out_dir / f"{name}.pdf"
    svg_path = out_dir / f"{name}.svg"
    selected_engine = _select_engine(engine, body, preamble, extra_packages)
    tex_text = build_standalone_tex(
        body,
        libraries=libraries,
        extra_packages=extra_packages,
        preamble=preamble,
        border_pt=border_pt,
        engine=selected_engine,
    )
    tex_path.write_text(tex_text, encoding="utf-8")

    pdf_status = compile_tex_to_pdf(tex_path, engine=selected_engine)
    result: dict[str, Any] = {
        "tex": str(tex_path),
        "engine": selected_engine,
        "pdf_status": pdf_status,
    }
    if pdf_status.get("status") == "ok":
        result["pdf"] = pdf_status["pdf"]
        svg_status = convert_pdf_to_svg(pdf_path, svg_path, text_mode=text_mode)
        result["svg_status"] = svg_status
        if svg_status.get("status") == "ok":
            result["svg"] = str(svg_path)
    return result


def _select_engine(
    engine: str,
    body: str,
    preamble: str,
    extra_packages: list[str] | None = None,
) -> str:
    normalized = engine.lower().strip()
    if normalized in LATEX_ENGINE_CANDIDATES:
        return normalized
    if normalized != "auto":
        raise ValueError(f"Unsupported LaTeX engine: {engine}")
    text = body + preamble + " ".join(extra_packages or [])
    return "xelatex" if any(ord(ch) > 127 for ch in text) and find_xelatex() else "pdflatex"


def _write_log(path: Path, stdout: str, stderr: str) -> None:
    path.write_text(f"STDOUT\n{stdout}\n\nSTDERR\n{stderr}\n", encoding="utf-8")


@lru_cache(maxsize=16)
def _probe_executable(executable: str, arg: str) -> dict[str, str]:
    try:
        result = subprocess.run(
            [executable, arg],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
        )
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "reason": f"{Path(executable).name} did not respond to {arg} within 8 seconds."}
    except Exception as exc:
        return {"status": "error", "reason": str(exc)}

    stdout = result.stdout[-2000:]
    stderr = result.stderr[-2000:]
    combined = f"{stdout}\n{stderr}".lower()
    if result.returncode != 0:
        if "fresh tex installation" in combined or "please finish the setup" in combined:
            return {
                "status": "not_configured",
                "reason": "MiKTeX is installed but its first-run setup is not complete.",
                "stdout": stdout,
                "stderr": stderr,
            }
        return {
            "status": "failed",
            "reason": f"{Path(executable).name} {arg} exited with {result.returncode}.",
            "stdout": stdout,
            "stderr": stderr,
        }
    return {"status": "ok", "reason": "", "stdout": stdout, "stderr": stderr}
