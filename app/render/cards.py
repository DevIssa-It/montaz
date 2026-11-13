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


def _deco_base(counter: tuple[int, int] | None = None) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Editorial canvas: pitch bg + faint dot grid + hairline frame + brand footer
    + optional scene counter chip ('03 / 07' deck style)."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    # faint dot grid (structure, not noise)
    for gx in range(120, W - 60, 64):
        for gy in range(120, H - 60, 64):
            draw.ellipse([gx, gy, gx + 3, gy + 3], fill=(26, 27, 34))
    # hairline frame + accent tick
    draw.rectangle([48, 48, W - 48, H - 48], outline=BORDER, width=2)
    draw.rectangle([48, 48, 96, 48 + 6], fill=ACCENT)
    # brand footer
    draw.rectangle([W - 470, H - 74, W - 440, H - 66], fill=ACCENT)
    draw.text((W - 424, H - 84), "montaz", font=font("sans", 30), fill=MUTED)
    draw.text((W - 424, H - 46), "many cuts, one story", font=font("sans", 22), fill=(90, 94, 104))
    # scene counter chip
    if counter:
        idx, total = counter
        label = f"{idx:02d} / {total:02d}"
        fnt = font("mono", 34)
        tw = draw.textlength(label, font=fnt)
        draw.rounded_rectangle(
            [W - 160 - tw - 44, 70, W - 116, 126], radius=10, outline=BORDER, width=2
        )
        draw.text((W - 160 - tw - 22, 78), label, font=fnt, fill=MUTED)
    return img, draw


def _blend(fg: tuple[int, int, int], p: float) -> tuple[int, int, int]:
    """Fade a foreground color in from the background (alpha-by-color)."""
    return tuple(int(BG[i] + (fg[i] - BG[i]) * p) for i in range(3))


def render_card(kind: str, heading: str, bullets: list[str], out_path: Path) -> Path:
    img, draw = _deco_base()
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


def render_split_frames(
    heading: str,
    bullets: list[str],
    shot_path: Path | None,
    out_dir: Path,
    total_seconds: float,
    fps: int = 10,
    counter: tuple[int, int] | None = None,
) -> Path:
    """Split-layout card: narration beats land on the LEFT while the app's
    REAL screenshot slides in on the RIGHT (gold frame) — the visual asset
    the deck was missing."""
    out_dir.mkdir(parents=True, exist_ok=True)
    base_img, _ = _deco_base(counter)
    total_frames = max(int(round(total_seconds * fps)), fps)

    shot: Image.Image | None = None
    if shot_path and Path(shot_path).exists():
        try:
            shot = Image.open(shot_path).convert("RGB")
        except Exception:
            shot = None

    # Layout: text column left (160..860), app panel right (940..1760)
    panel = (940, 240, 1760, 900)  # 820x660 → shot fitted inside
    tx, max_w = 160, 640
    hf = font("sans", 84)
    bf = font("sans", 46)

    def draw_text(d: ImageDraw.ImageDraw, img: Image.Image, p: float) -> None:
        d.text((tx, 260), "LIVE DEMO", font=font("sans", 34), fill=_blend(ACCENT, p))
        d.line([tx, 320, tx + 520, 320], fill=_blend(BORDER, p), width=2)
        y = 380
        for line in _wrap(d, heading, hf, max_w)[:2]:
            d.text((tx, y), line, font=hf, fill=_blend(TEXT, p))
            y += 106
        y += 20
        for bullet in bullets[:4]:
            d.ellipse([tx, y + 14, tx + 14, y + 28], fill=_blend(ACCENT, p))
            for line in _wrap(d, bullet, bf, max_w - 50)[:2]:
                d.text((tx + 44, y), line, font=bf, fill=_blend(TEXT, p))
                y += 60

    def draw_shot(d: ImageDraw.ImageDraw, img: Image.Image, p: float) -> None:
        x0, y0, x1, y1 = panel
        slide = int(60 * (1 - p))  # slides in from the right
        px0, py0, px1, py1 = x0 + slide, y0, x1 + slide, y1
        d.rounded_rectangle([px0, py0, px1, py1], radius=14, fill=(13, 16, 22))
        if shot is not None:
            fit = shot.copy()
            fit.thumbnail((px1 - px0 - 36, py1 - py0 - 36))
            img.paste(fit, (px0 + (px1 - px0 - fit.width) // 2, py0 + (py1 - py0 - fit.height) // 2))
        else:
            d.text((px0 + 40, py0 + 40), "(app preview)", font=font("sans", 36), fill=MUTED)
        d.rounded_rectangle([px0, py0, px1, py1], radius=14,
                            outline=_blend((251, 191, 36), p), width=3)

    text_frames = max(int(total_frames * 0.30), 2)
    shot_start = int(total_frames * 0.30)

    for idx in range(total_frames):
        img = base_img.copy()
        d = ImageDraw.Draw(img)
        if idx >= 2:
            p = min((idx - 2) / max(text_frames - 2, 1), 1.0)
            draw_text(d, img, p)
        if idx >= shot_start:
            p = min((idx - shot_start) / max(total_frames - shot_start - 6, 1), 1.0)
            draw_shot(d, img, p)
        img.save(out_dir / f"f_{idx:05d}.png")
    return out_dir


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


def render_card_frames(
    kind: str,
    heading: str,
    bullets: list[str],
    out_dir: Path,
    total_seconds: float,
    fps: int = 10,
    counter: tuple[int, int] | None = None,
) -> Path:
    """Progressive-reveal card animation: elements fade/slide in one by one
    (accent bar grows, heading lands, bullets appear per beat), then hold.
    The result reads as a designed deck, not a static slide."""
    out_dir.mkdir(parents=True, exist_ok=True)
    base_img, _ = _deco_base(counter)
    left, max_w = 160, W - 320
    total_frames = max(int(round(total_seconds * fps)), fps)

    plans: list[tuple[int, int, Any]] = []  # (start, end, draw_fn(draw, p))

    def fade_text(pos, text, fnt, fill, dx=0.0, dy=0.0):
        def _fn(d: ImageDraw.ImageDraw, p: float) -> None:
            d.text((pos[0] + dx * (1 - p), pos[1] + dy * (1 - p)), text, font=fnt, fill=_blend(fill, p))
        return _fn

    def grow_bar(pos, w=96):
        def _fn(d: ImageDraw.ImageDraw, p: float) -> None:
            d.rectangle([pos[0], pos[1], pos[0] + w * p, pos[1] + 6], fill=ACCENT)
        return _fn

    def fade_dot(pos):
        def _fn(d: ImageDraw.ImageDraw, p: float) -> None:
            d.ellipse([pos[0], pos[1], pos[0] + 14, pos[1] + 14], fill=_blend(ACCENT, p))
        return _fn

    def fade_chip(pos, label, fnt, w):
        def _fn(d: ImageDraw.ImageDraw, p: float) -> None:
            d.rounded_rectangle([pos[0] + 40 * (1 - p), pos[1], pos[0] + 40 * (1 - p) + w, pos[1] + 88],
                                radius=10, outline=_blend((60, 62, 72), p), width=2)
            d.text((pos[0] + 40 * (1 - p) + 36, pos[1] + 18), label, font=fnt, fill=_blend(TEXT, p))
        return _fn

    if kind == "title":
        hf = font("sans", 110)
        lines = _wrap(ImageDraw.Draw(Image.new("RGB", (8, 8))), heading or "Untitled Project", hf, max_w)[:2]
        y = H // 2 - 60
        plans.append((0, int(total_frames * 0.12), grow_bar((left, y - 74))))
        for line in lines:
            plans.append((int(total_frames * 0.10), int(total_frames * 0.34), fade_text((left, y), line, hf, TEXT)))
            y += 140
        y += 24
        tf = font("sans", 52)
        for line in _wrap(ImageDraw.Draw(Image.new("RGB", (8, 8))), bullets[0] if bullets else "", tf, max_w)[:2]:
            plans.append((int(total_frames * 0.38), int(total_frames * 0.58), fade_text((left, y), line, tf, MUTED)))
            y += 66
    else:
        lf = font("sans", 44)
        plans.append((0, int(total_frames * 0.14), fade_text((left, 170), (heading or "").upper(), lf, ACCENT)))
        plans.append((int(total_frames * 0.12), int(total_frames * 0.26), fade_text((left, 240), "─" * 60, font("sans", 24), BORDER)))
        y = 300
        if kind == "bullets":
            bf = font("sans", 58)
            beat = max(int(total_frames * 0.10), 3)
            for bi, bullet in enumerate(bullets[:5]):
                start = int(total_frames * 0.22) + bi * beat
                end = start + beat
                plans.append((start, end, fade_dot((left, y + 26))))
                for line in _wrap(ImageDraw.Draw(Image.new("RGB", (8, 8))), bullet, bf, max_w - 60)[:2]:
                    plans.append((start, end, fade_text((left + 56, y), line, bf, TEXT, dx=44)))
                    y += 72
                y += 26
        else:  # stack chips
            cf = font("mono", 46)
            beat = max(int(total_frames * 0.08), 2)
            x, row = left, 0
            for ci, item in enumerate(bullets[:8]):
                start = int(total_frames * 0.22) + ci * beat
                cw = 72 + int(len(item) * 24)
                if x + cw > W - 160:
                    x, row = left, row + 116
                plans.append((start, start + beat, fade_chip((x, 300 + row), item, cf, cw)))
                x += cw + 24
    def render_frame(idx: int, path: Path) -> None:
        img = base_img.copy()
        d = ImageDraw.Draw(img)
        for start, end, fn in plans:
            if idx >= start:
                p = min((idx - start) / max(end - start, 1), 1.0)
                fn(d, p)
        img.save(path)

    for f in range(total_frames):
        render_frame(f, out_dir / f"f_{f:05d}.png")
    return out_dir
