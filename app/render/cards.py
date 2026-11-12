"""Render 1920x1080 scene cards (title / bullets / stack) + animated terminal frames.

Palette follows DESIGN.md Archetype B (Developer Tools):
pitch canvas #090A0F, card #12141A, text #EDEDED, muted #8B8F9A,
brand gold #FBBF24 (projector beam), hairline border #1C1D24.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
BG = (9, 10, 15)
CARD = (18, 20, 26)
TEXT = (237, 237, 237)
MUTED = (139, 143, 154)
ACCENT = (251, 191, 36)
BORDER = (28, 29, 36)
TERM_BG = (10, 13, 20)

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


def _base_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    # Hairline frame + accent bar: quiet, editorial, zero gradient.
    draw.rectangle([48, 48, W - 48, H - 48], outline=BORDER, width=2)
    draw.rectangle([48, 48, 96, 48 + 6], fill=ACCENT)
    return img, draw


def render_card(kind: str, heading: str, bullets: list[str], out_path: Path) -> Path:
    img, draw = _base_canvas()
    left, max_w = 160, W - 320
    if kind == "title":
        y = H // 2 - 60
        for line in _wrap(draw, heading or "Untitled Project", font("sans", 110), max_w)[:2]:
            draw.text((left, y), line, font=font("sans", 110), fill=TEXT)
            y += 140
        y += 24
        for line in _wrap(draw, bullets[0] if bullets else "", font("sans", 52), max_w)[:2]:
            draw.text((left, y), line, font=font("sans", 52), fill=MUTED)
            y += 66
    else:  # bullets | stack
        label = (heading or "").upper()
        draw.text((left, 170), label, font=font("sans", 44), fill=ACCENT)
        draw.line([left, 240, left + 720, 240], fill=BORDER, width=2)
        y = 300
        if kind == "bullets":
            for bullet in bullets[:5]:
                draw.ellipse([left, y + 26, left + 14, y + 40], fill=ACCENT)
                for i, line in enumerate(_wrap(draw, bullet, font("sans", 58), max_w - 60)[:2]):
                    draw.text((left + 56, y), line, font=font("sans", 58), fill=TEXT)
                    y += 72
                y += 26
        else:  # stack chips
            x, row_h = left, 0
            for item in bullets[:8]:
                fnt = font("mono", 46)
                chip_w = int(draw.textlength(item, font=fnt)) + 72
                if x + chip_w > W - 160:
                    x, y = left, y + row_h + 28
                    if y > H - 140:
                        break
                draw.rounded_rectangle([x, y, x + chip_w, y + 88], radius=10, outline=BORDER, width=2)
                draw.text((x + 36, y + 18), item, font=fnt, fill=TEXT)
                x += chip_w + 24
                row_h = 88
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def render_terminal_still(command: str, lines: list[str], out_path: Path) -> Path:
    """Single terminal-window frame (for timeline thumbnails)."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    tx0, ty0, tx1, ty1 = 140, 220, W - 140, H - 180
    draw.rounded_rectangle([tx0, ty0, tx1, ty1], radius=12, fill=TERM_BG, outline=BORDER, width=2)
    for i, color in enumerate(((239, 68, 68), (245, 158, 11), (34, 197, 94))):
        cx = tx0 + 44 + i * 44
        draw.ellipse([cx, ty0 + 28, cx + 20, ty0 + 48], fill=color)
    draw.text((tx1 - 330, ty0 + 20), "demo — terminal", font=font("mono", 30), fill=MUTED)
    mono = font("mono", 42)
    draw.text((tx0 + 56, ty0 + 104), f"$ {command}", font=mono, fill=TEXT)
    ly = ty0 + 188
    for line in lines[:8]:
        for wrap_line in _wrap(draw, line, mono, tx1 - tx0 - 112)[:2]:
            draw.text((tx0 + 56, ly), wrap_line, font=mono, fill=MUTED)
            ly += 58
        if ly > ty1 - 60:
            break
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def render_terminal_frames(command: str, lines: list[str], out_dir: Path, total_seconds: float, fps: int = 10) -> Path:
    """Progressive-reveal terminal window; returns the frames directory.

    Typing the command takes ~20% of the time, output lines reveal over the rest.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    total_frames = max(int(math.ceil(total_seconds * fps)), fps)
    type_frames = max(total_frames // 5, 1)
    n_lines = max(len(lines), 1)
    per_line = max((total_frames - type_frames) / n_lines, 1)

    for idx in range(total_frames):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        # Terminal window card.
        tx0, ty0, tx1, ty1 = 140, 220, W - 140, H - 180
        draw.rounded_rectangle([tx0, ty0, tx1, ty1], radius=12, fill=TERM_BG, outline=BORDER, width=2)
        for i, color in enumerate(((239, 68, 68), (245, 158, 11), (34, 197, 94))):
            cx = tx0 + 44 + i * 44
            draw.ellipse([cx, ty0 + 28, cx + 20, ty0 + 48], fill=color)
        draw.text((tx1 - 330, ty0 + 20), "demo — terminal", font=font("mono", 30), fill=MUTED)

        mono = font("mono", 42)
        x, y = tx0 + 56, ty0 + 104
        # 1) Command typed char-by-char.
        chars = max(int(len(command) * (idx + 1) / type_frames), 1) if idx < type_frames else len(command)
        typed = command[:chars]
        draw.text((x, y), f"$ {typed}", font=mono, fill=TEXT)
        cursor_x = x + int(draw.textlength(f"$ {typed}", font=mono))
        if idx < total_frames - 1 and (idx // 2) % 2 == 0:
            draw.rectangle([cursor_x + 10, y + 6, cursor_x + 30, y + 52], fill=ACCENT)
        if idx >= type_frames:
            # 2) Output lines revealed progressively.
            shown = min(int((idx - type_frames) / per_line) + 1, n_lines)
            ly = y + 84
            for line in lines[:shown]:
                for wrap_line in _wrap(draw, line, mono, tx1 - x - 56)[:2]:
                    draw.text((x, ly), wrap_line, font=mono, fill=MUTED if not line.startswith("$") else TEXT)
                    ly += 58
                if ly > ty1 - 60:
                    break
        img.save(out_dir / f"f_{idx:05d}.png")
    return out_dir
