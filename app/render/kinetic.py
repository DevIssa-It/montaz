"""Kinetic split-card renderer — Teams-intro vocabulary:
- auto-fit heading, word-by-word landing, one GOLD key word, underline sweep
- confetti sparkles + cartoon heart sticker pop-ins
- numbered bullets that gain a check when complete
- white app panel: screenshots CUT between pages, Ken Burns zoom,
  gold corner brackets, LIVE badge
- thin gold film-progress line
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .cards import (GOLD, MUTED_LIGHT, TEXT_DARK, TEXT_LIGHT, _base_bg, _blend,
                    _ornaments, _panel, font, _wrap)

W, H = 1920, 1080
PANEL_BOX = (940, 190, 1800, 880)


def _fit_heading(draw: ImageDraw.ImageDraw, heading: str, max_w: int) -> tuple[int, list[str]]:
    size = 74
    words = heading.split()
    probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    while size >= 40:
        fnt = font("sans", size)
        lines, current, ok = [], "", True
        for word in words:
            cand = f"{current} {word}".strip()
            if probe.textlength(cand, font=fnt) <= max_w:
                current = cand
            else:
                if current:
                    lines.append(current)
                current = word
                if len(lines) >= 2:
                    ok = False
                    break
        if current:
            lines.append(current)
        if ok and len(lines) <= 2 and all(probe.textlength(l, font=fnt) <= max_w for l in lines):
            return size, lines
        size -= 6
    return 44, [heading[:30]]


def _sticker_heart(d: ImageDraw.ImageDraw, x: float, y: float, s: float, p: float) -> None:
    size = s * min(p * 1.6, 1.0)
    r = size * 0.30
    col = _blend((244, 63, 94), p)
    dark = _blend((190, 40, 70), p)
    cy = y - size * 0.12
    d.ellipse([x - size * 0.5, cy - r, x - size * 0.5 + r * 2, cy + r], fill=col)
    d.ellipse([x + size * 0.5 - r * 2, cy - r, x + size * 0.5, cy + r], fill=col)
    d.polygon([(x - size * 0.52, cy - size * 0.02), (x + size * 0.52, cy - size * 0.02),
               (x, y + size * 0.52)], fill=col)
    d.ellipse([x - size * 0.34, cy - size * 0.16, x - size * 0.10, cy + size * 0.08], fill=dark)
    d.ellipse([x - size * 0.30, cy - size * 0.14, x - size * 0.18, cy - size * 0.02],
              fill=(255, 255, 255))


def _sticker_sparkle(d: ImageDraw.ImageDraw, x: float, y: float, s: float, p: float) -> None:
    size = s * min(p * 1.7, 1.0)
    col = _blend((251, 191, 36), p)
    k = size * 0.22
    d.polygon([(x, y - size), (x + k, y - k), (x + size, y), (x + k, y + k),
               (x, y + size), (x - k, y + k), (x - size, y), (x - k, y - k)], fill=col)
    d.ellipse([x - size * 0.10, y - size * 0.10, x + size * 0.10, y + size * 0.10], fill=(255, 255, 255))


def _sticker_ring(d: ImageDraw.ImageDraw, x: float, y: float, r: float, p: float) -> None:
    col = _blend((251, 191, 36), p)
    d.ellipse([x - r, y - r, x + r, y + r], outline=col, width=6)


def render_split_frames(
    heading: str,
    bullets: list[str],
    shots: list[Path] | None,
    out_dir: Path,
    total_seconds: float,
    fps: int = 10,
    counter: tuple[int, int] | None = None,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    base_img, _ = _base_bg(counter)
    total_frames = max(int(round(total_seconds * fps)), fps)
    heading = heading[:80]

    shot_imgs: list[Image.Image] = []
    for sp in (shots or [])[:2]:
        if sp and Path(sp).exists():
            try:
                shot_imgs.append(Image.open(sp).convert("RGB"))
            except Exception:
                pass

    tx, max_w = 130, 660
    hsize, hlines = _fit_heading(ImageDraw.Draw(Image.new("RGB", (8, 8))), heading, max_w)
    hf = font("sans", hsize)
    bf = font("sans", 42)
    words = heading.split()
    gold_word = max(words, key=len) if words else ""

    def draw_text(d: ImageDraw.ImageDraw, p: float) -> None:
        d.text((tx, 205), "FEATURE", font=font("sans", 34), fill=_blend(GOLD, min(p * 5, 1)))
        # words land line by line (wrapped), staggered; one gold key word
        global_index = 0
        for li, line in enumerate(hlines):
            ly = 295 + li * (hsize + 14)
            x = tx
            for word in line.split():
                wp = min(max(p * len(words) * 1.5 - global_index * 0.7, 0), 1)
                if wp > 0:
                    col = GOLD if word == gold_word else _blend(TEXT_LIGHT, wp)
                    d.text((x, ly + 22 * (1 - wp)), word, font=hf, fill=col)
                x += d.textlength(word + " ", font=hf)
                global_index += 1
        sweep = min(max(p * len(words) * 1.5 - len(words) * 0.8, 0), 1)
        if sweep > 0:
            for li, line in enumerate(hlines):
                line_w = d.textlength(line, font=hf)
                d.rectangle([tx, 295 + (li + 1) * (hsize + 14) - 6,
                             tx + min(max_w, line_w) * sweep, 295 + (li + 1) * (hsize + 14)],
                            fill=GOLD)
        for k, (sx, sy) in enumerate(((tx + max_w + 30, 290), (tx + max_w - 70, 240),
                                      (tx - 34, 380), (tx + max_w * 0.55, 205))):
            sp = min(max(p * 6 - 1.2 - k * 0.5, 0), 1)
            if sp > 0 and k % 2 == 0:
                _sticker_sparkle(d, sx, sy, 16 + (k % 3) * 5, sp)
            elif sp > 0:
                _sticker_heart(d, sx, sy, 15 + (k % 2) * 6, sp)
        _sticker_heart(d, 100, 470, 44, min(p * 2, 1))
        _sticker_sparkle(d, 745, 430, 30, min(max(p * 4 - 1, 0), 1))
        _sticker_ring(d, 90, 300, 14, min(max(p * 5 - 2, 0), 1))
        by = 295 + len(hlines) * (hsize + 14) + 70
        for bi, bullet in enumerate(bullets[:5]):
            bp = min(max(p * (len(bullets) + 1.6) - 1 - bi * 0.9, 0), 1)
            if bp <= 0:
                continue
            done = bp >= 1
            d.ellipse([tx, by, tx + 52, by + 52], fill=_blend(GOLD, bp))
            if done:
                d.line([(tx + 14, by + 27), (tx + 22, by + 36), (tx + 38, by + 16)],
                       fill=(9, 10, 15), width=4)
            else:
                d.text((tx + 19, by + 8), str(bi + 1), font=font("mono", 26),
                       fill=_blend((9, 10, 15), bp))
            for li, line in enumerate(_wrap(d, bullet, bf, max_w - 76)[:2]):
                d.text((tx + 68, by + li * 2 - 2), line, font=bf, fill=_blend(TEXT_LIGHT, bp))
            by += 74

    def draw_shot(d: ImageDraw.ImageDraw, img: Image.Image, p: float, phase: float) -> None:
        x0, y0, x1, y1 = PANEL_BOX
        _panel(img, d, (x0, y0, x1, y1))
        if shot_imgs:
            shot = shot_imgs[0] if (phase < 0.55 and len(shot_imgs) > 1) else shot_imgs[-1]
            zoom = 1.0 + 0.08 * phase
            fit = shot.copy()
            fit.thumbnail((x1 - x0 - 44, y1 - y0 - 96))
            fit = fit.resize((int(fit.width * zoom), int(fit.height * zoom)))
            fx = x0 + (x1 - x0 - fit.width) // 2
            fy = y0 + 24 + (y1 - y0 - 96 - fit.height) // 2
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
                            outline=_blend(GOLD, min(phase * 3, 1)), width=3)

    def render_frame(idx: int, path: Path) -> None:
        img = base_img.copy()
        d = ImageDraw.Draw(img)
        _ornaments(d, idx)
        p = idx / max(total_frames - 1, 1)
        if idx >= 2:
            draw_text(d, min(p * 2.4, 1.0))
        if idx >= int(total_frames * 0.18):
            draw_shot(d, img, min(
                (idx - int(total_frames * 0.18)) / max(total_frames - int(total_frames * 0.18) - 8, 1),
                1.0), min(p * 1.4, 1.0))
        d.rectangle([48, H - 40, 48 + (W - 96) * p, H - 34], fill=GOLD)
        img.save(path)

    for f in range(total_frames):
        render_frame(f, out_dir / f"f_{f:05d}.png")
    return out_dir
