from __future__ import annotations

import math
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .styles import PALETTE


def load_font(size: int = 24, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def new_canvas(width: int, height: int, bg: str = "#FFFFFF") -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (width, height), bg)
    return img, ImageDraw.Draw(img)


def text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[float, float, float, float],
    text: str,
    font,
    fill: str = PALETTE["ink"],
    max_chars: int = 16,
) -> None:
    x1, y1, x2, y2 = box
    lines = []
    for raw in str(text).split("\n"):
        lines.extend(textwrap.wrap(raw, width=max_chars) or [""])
    line_heights = [text_size(draw, line, font)[1] for line in lines]
    total_h = sum(line_heights) + max(0, len(lines) - 1) * 4
    y = y1 + ((y2 - y1) - total_h) / 2
    for line, h in zip(lines, line_heights):
        w, _ = text_size(draw, line, font)
        draw.text((x1 + ((x2 - x1) - w) / 2, y), line, font=font, fill=fill)
        y += h + 4


def draw_round_rect(
    draw: ImageDraw.ImageDraw,
    box: tuple[float, float, float, float],
    fill: str,
    outline: str,
    width: int = 3,
    radius: int = 16,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[float, float],
    end: tuple[float, float],
    fill: str = PALETTE["ink"],
    width: int = 3,
    dashed: bool = False,
) -> None:
    if dashed:
        _draw_dashed_line(draw, start, end, fill=fill, width=width)
    else:
        draw.line([start, end], fill=fill, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    arrow_len = 14
    spread = 0.45
    p1 = (
        end[0] - arrow_len * math.cos(angle - spread),
        end[1] - arrow_len * math.sin(angle - spread),
    )
    p2 = (
        end[0] - arrow_len * math.cos(angle + spread),
        end[1] - arrow_len * math.sin(angle + spread),
    )
    draw.polygon([end, p1, p2], fill=fill)


def _draw_dashed_line(
    draw: ImageDraw.ImageDraw,
    start: tuple[float, float],
    end: tuple[float, float],
    fill: str,
    width: int,
    dash: int = 12,
    gap: int = 8,
) -> None:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    dist = math.hypot(dx, dy)
    if dist == 0:
        return
    steps = int(dist // (dash + gap)) + 1
    ux, uy = dx / dist, dy / dist
    for i in range(steps):
        a = i * (dash + gap)
        b = min(a + dash, dist)
        if a >= dist:
            break
        draw.line(
            [(start[0] + ux * a, start[1] + uy * a), (start[0] + ux * b, start[1] + uy * b)],
            fill=fill,
            width=width,
        )


def save_png(img: Image.Image, path: str | Path) -> Path:
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    img.save(target)
    return target
