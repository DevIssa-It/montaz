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
    shot_path: Path | None,
    out_dir: Path,
    total_seconds: float,
    fps: int = 10,
    counter: tuple[int, int] | None = None,
) -> Path:
    """Kinetic split card on the indigo field, Teams-intro style:
    left  — FEATURE label, word-by-word heading landing with a gold
            underline sweep, numbered bullets staggering in
    right — white panel with the app's REAL screenshot riding a Ken Burns
            zoom, gold corner brackets + LIVE badge
    bottom — thin gold film-progress line
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    base_img, _ = _base_bg(counter)
    total_frames = max(int(round(total_seconds * fps)), fps)
    heading = heading[:70]

    shot: Image.Image | None = None
    if shot_path and Path(shot_path).exists():
        try:
            shot = Image.open(shot_path).convert("RGB")
        except Exception:
            shot = None

    panel = (940, 190, 1800, 880)
    tx, max_w = 130, 700
    hf = font("sans", 72)
    bf = font("sans", 44)
    words = heading.split() or ["Demo"]

    def draw_text(d: ImageDraw.ImageDraw, p: float) -> None:
        d.text((tx, 210), "FEATURE", font=font("sans", 34), fill=_blend(GOLD, min(p * 4, 1)))
        x, y = tx, 300
        for wi, word in enumerate(words):
            wp = min(max(p * len(words) * 1.5 - wi * 0.7, 0), 1)
            if wp > 0:
                d.text((x, y + 24 * (1 - wp)), word, font=hf, fill=_blend(TEXT_LIGHT, wp))
            x += d.textlength(word + " ", font=hf)
        sweep = min(max(p * len(words) * 1.5 - len(words) * 0.8, 0), 1)
        if sweep > 0:
            d.rectangle([tx, y + 112, tx + max_w * sweep, y + 118], fill=GOLD)
        by = y + 180
        for bi, bullet in enumerate(bullets[:5]):
            bp = min(max(p * (len(bullets) + 1.5) - 1 - bi * 0.9, 0), 1)
            if bp <= 0:
                continue
            d.rounded_rectangle([tx, by, tx + 54, by + 42], radius=8,
                                outline=_blend(GOLD, bp), width=2)
            d.text((tx + 17, by + 5), str(bi + 1), font=font("mono", 26), fill=_blend(GOLD, bp))
            for li, line in enumerate(_wrap(d, bullet, bf, max_w - 76)[:2]):
                d.text((tx + 70, by + li * 2 - 2), line, font=bf, fill=_blend(TEXT_LIGHT, bp))
            by += 70

    def draw_shot(d: ImageDraw.ImageDraw, img: Image.Image, p: float) -> None:
        x0, y0, x1, y1 = panel
        _panel(img, d, (x0, y0, x1, y1))
        if shot is not None:
            zoom = 1.0 + 0.09 * p
            fit = shot.copy()
            fit.thumbnail((x1 - x0 - 44, y1 - y0 - 44))
            fit = fit.resize((int(fit.width * zoom), int(fit.height * zoom)))
            fx = x0 + (x1 - x0 - fit.width) // 2
            fy = y0 + (y1 - y0 - fit.height) // 2
            img.paste(fit, (fx, fy))
            k = 24
            bl, bt, br, bb = fx, fy, fx + fit.width, fy + fit.height
            for (cx, cy, dx, dy) in ((bl, bt, 1, 1), (br, bt, -1, 1), (bl, bb, 1, -1), (br, bb, -1, -1)):
                d.line([(cx, cy + dy * k), (cx, cy)], fill=GOLD, width=4)
                d.line([(cx, cy), (cx + dx * k, cy)], fill=GOLD, width=4)
            d.rounded_rectangle([bl + 12, bt + 12, bl + 114, bt + 50], radius=8, fill=(9, 10, 15))
            d.ellipse([bl + 24, bt + 22, bl + 38, bt + 36], fill=GOLD)
            d.text((bl + 46, bt + 16), "LIVE", font=font("mono", 22), fill=TEXT_LIGHT)
        else:
            d.text((x0 + 40, y0 + 40), "(app preview)", font=font("sans", 36), fill=(150, 150, 170))
        d.rounded_rectangle([x0, y0, x1, y1], radius=18,
                            outline=_blend(GOLD, min(p * 3, 1)), width=3)

    def render_frame(idx: int, path: Path) -> None:
        img = base_img.copy()
        d = ImageDraw.Draw(img)
        _ornaments(d, idx)
        p = idx / max(total_frames - 1, 1)
        if idx >= 2:
            draw_text(d, min(p * 2.4, 1.0))
        if idx >= int(total_frames * 0.20):
            draw_shot(d, img, min(
                (idx - int(total_frames * 0.20)) / max(total_frames - int(total_frames * 0.20) - 8, 1),
                1.0))
        d.rectangle([48, H - 40, 48 + (W - 96) * p, H - 34], fill=GOLD)
        img.save(path)

    for f in range(total_frames):
        render_frame(f, out_dir / f"f_{f:05d}.png")
    return out_dir


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
