"""Render 1920x1080 scene visuals for montaz.

Video style follows the reference (Teams-style product intro):
- a vivid indigo field with large organic curves (no black voids)
- drifting gold/white rings and dots for life
- app demo lives inside a WHITE panel with soft shadow, Ken-Burns'd
- dark text on white panels, white/gold text on the indigo field
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
INDIGO = (88, 87, 214)
INDIGO_CURVE = (63, 62, 176)
INDIGO_DEEP = (51, 50, 158)
PANEL = (255, 255, 255)
TEXT_DARK = (24, 26, 32)
TEXT_LIGHT = (255, 255, 255)
MUTED_LIGHT = (216, 216, 244)
GOLD = (251, 191, 36)
TERM_BG = (13, 16, 22)

FONT_CANDIDATES = {
    "sans": [
        "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ],
    "mono": [
        "C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/cour.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
    ],
}
_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    key = (kind, size)
    if key not in _font_cache:
        for path in FONT_CANDIDATES[kind]:
            if Path(path).exists():
                _font_cache[key] = ImageFont.truetype(path, size)
                break
        else:
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]


def _wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words, lines, current = text.split(), [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=fnt) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _blend(fg: tuple[int, int, int], p: float) -> tuple[int, int, int]:
    """Fade a foreground color in from the indigo field."""
    return tuple(int(INDIGO[i] + (fg[i] - INDIGO[i]) * p) for i in range(3))


def _base_bg(counter: tuple[int, int] | None = None) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Vivid indigo field + two large organic curves + brand footer + counter."""
    img = Image.new("RGB", (W, H), INDIGO)
    draw = ImageDraw.Draw(img)
    # large organic curves (reference-style depth, no flat void)
    draw.ellipse([W - 900, -500, W + 900, H + 200], fill=INDIGO_CURVE)
    draw.ellipse([-500, H - 520, 900, H + 700], fill=INDIGO_DEEP)
    draw.ellipse([W - 620, H - 900, W + 560, H - 120], fill=INDIGO_CURVE)
    # brand footer
    draw.rectangle([W - 470, H - 74, W - 440, H - 66], fill=GOLD)
    draw.text((W - 424, H - 84), "montaz", font=font("sans", 30), fill=TEXT_LIGHT)
    if counter:
        idx, total = counter
        label = f"{idx:02d} / {total:02d}"
        fnt = font("mono", 34)
        tw = draw.textlength(label, font=fnt)
        draw.rounded_rectangle(
            [W - 160 - tw - 44, 64, W - 116, 120], radius=10, fill=(70, 69, 185)
        )
        draw.text((W - 160 - tw - 22, 72), label, font=fnt, fill=TEXT_LIGHT)
    return img, draw


def _ornaments(draw: ImageDraw.ImageDraw, idx: int) -> None:
    """Drifting gold/white rings and dots behind the panels."""
    items = [
        (210, 180, 26, GOLD, 0.9), (420, 620, 16, TEXT_LIGHT, 0.55),
        (120, 800, 34, GOLD, 0.5), (640, 130, 14, TEXT_LIGHT, 0.5),
        (760, 880, 30, GOLD, 0.45), (1770, 150, 22, GOLD, 0.6),
        (1660, 620, 13, TEXT_LIGHT, 0.5), (W - 150, 880, 34, GOLD, 0.5),
        (1020, 120, 12, TEXT_LIGHT, 0.45),
    ]
    for k, (x, y, r, color, alpha) in enumerate(items):
        dx = int(math.sin(idx * 0.12 + k * 1.7) * 12)
        dy = int(math.cos(idx * 0.09 + k * 2.1) * 9)
        col = tuple(int(INDIGO[i] + (color[i] - INDIGO[i]) * alpha) for i in range(3))
        draw.ellipse([x + dx - r, y + dy - r, x + dx + r, y + dy + r], fill=col)


def _panel(img: Image.Image, draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int = 18) -> None:
    """White panel with a soft fake shadow (layered rounded rects)."""
    x0, y0, x1, y1 = box
    for grow, shade in ((46, (44, 43, 150)), (28, (52, 51, 165)), (14, (60, 59, 180))):
        draw.rounded_rectangle(
            [x0 - grow, y0 - grow * 0.4, x1 + grow, y1 + grow], radius=radius + grow,
            fill=shade,
        )
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=PANEL)


def render_card(kind: str, heading: str, bullets: list[str], out_path: Path) -> Path:
    """Static card (timeline thumbnails): indigo field + white panel + dark text."""
    img, draw = _base_bg()
    _ornaments(draw, 12)
    box = (300, 170, W - 300, H - 190)
    _panel(img, draw, box)
    px, py = box[0] + 60, box[1] + 54
    draw = ImageDraw.Draw(img)
    if kind == "title":
        draw.rectangle([px, py, px + 110, py + 8], fill=GOLD)
        y = py + 66
        for line in _wrap(draw, heading or "Untitled Project", font("sans", 92), box[2] - box[0] - 120)[:2]:
            draw.text((px, y), line, font=font("sans", 92), fill=TEXT_DARK)
            y += 118
        y += 16
        for line in _wrap(draw, bullets[0] if bullets else "", font("sans", 42), box[2] - box[0] - 120)[:2]:
            draw.text((px, y), line, font=font("sans", 42), fill=(96, 100, 118))
            y += 56
    else:
        draw.text((px, py), (heading or "").upper(), font=font("sans", 40), fill=(202, 148, 12))
        draw.line([px, py + 62, px + 620, py + 62], fill=(225, 227, 236), width=2)
        y = py + 106
        if kind == "bullets":
            for bullet in bullets[:5]:
                draw.ellipse([px, y + 18, px + 12, y + 30], fill=GOLD)
                for line in _wrap(draw, bullet, font("sans", 46), box[2] - box[0] - 130)[:2]:
                    draw.text((px + 44, y), line, font=font("sans", 46), fill=TEXT_DARK)
                    y += 62
                y += 18
        else:
            x, row = px, 0
            for item in bullets[:8]:
                fnt = font("mono", 38)
                cw = int(draw.textlength(item, font=fnt)) + 60
                if x + cw > box[2] - 80:
                    x, row = px, row + 100
                draw.rounded_rectangle([x, y + row, x + cw, y + row + 74], radius=12,
                                       outline=(222, 224, 234), width=2)
                draw.text((x + 30, y + row + 16), item, font=fnt, fill=TEXT_DARK)
                x += cw + 20
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def render_split_frames(
    heading: str,
    bullets: list[str],
    shots: list[Path] | None,
    out_dir: Path,
    total_seconds: float,
    fps: int = 10,
    counter: tuple[int, int] | None = None,
) -> Path:
    """Kinetic split card (Teams-intro style) — implemented in kinetic.py."""
    # Lazy import: kinetic imports shared helpers from this module.
    from .kinetic import render_split_frames as _impl

    return _impl(heading, bullets, shots, out_dir, total_seconds, fps, counter)


def render_terminal_still(command: str, lines: list[str], out_path: Path) -> Path:
    """Single terminal-window frame (for timeline thumbnails)."""
    img, draw = _base_bg()
    _ornaments(draw, 20)
    box = (220, 200, W - 220, H - 200)
    _panel(img, draw, box, radius=14)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([box[0] + 4, box[1] + 4, box[2] - 4, box[3] - 4], radius=12, fill=TERM_BG)
    for i, color in enumerate(((239, 68, 68), (245, 158, 11), (34, 197, 94))):
        cx = box[0] + 52 + i * 44
        d.ellipse([cx, box[1] + 30, cx + 20, box[1] + 50], fill=color)
    mono = font("mono", 40)
    d.text((box[0] + 56, box[1] + 110), f"$ {command}", font=mono, fill=TEXT_LIGHT)
    ly = box[1] + 200
    for line in lines[:8]:
        for wrap_line in _wrap(d, line, mono, box[2] - box[0] - 112)[:2]:
            d.text((box[0] + 56, ly), wrap_line, font=mono, fill=MUTED_LIGHT)
            ly += 56
        if ly > box[3] - 70:
            break
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def render_terminal_frames(command: str, lines: list[str], out_dir: Path, total_seconds: float, fps: int = 10) -> Path:
    """Progressive-reveal terminal animation on the indigo field."""
    still = render_terminal_still(command, [], out_dir / "_base.png")
    out_dir.mkdir(parents=True, exist_ok=True)
    total_frames = max(int(math.ceil(total_seconds * fps)), fps)
    type_frames = max(total_frames // 5, 1)
    n_lines = max(len(lines), 1)
    per_line = max((total_frames - type_frames) / n_lines, 1)
    base = Image.open(still)
    for idx in range(total_frames):
        img = base.copy()
        d = ImageDraw.Draw(img)
        mono = font("mono", 40)
        x, y = 276, 318
        chars = max(int(len(command) * (idx + 1) / type_frames), 1) if idx < type_frames else len(command)
        typed = command[:chars]
        d.text((x, y), f"$ {typed}", font=mono, fill=TEXT_LIGHT)
        if idx >= type_frames:
            shown = min(int((idx - type_frames) / per_line) + 1, n_lines)
            ly = y + 96
            for line in lines[:shown]:
                for wrap_line in _wrap(d, line, mono, 1400)[:2]:
                    d.text((x, ly), wrap_line, font=mono, fill=MUTED_LIGHT)
                    ly += 56
                if ly > 860:
                    break
        img.save(out_dir / f"f_{idx:05d}.png")
    (out_dir / "_base.png").unlink(missing_ok=True)
    return out_dir
