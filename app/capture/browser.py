"""Playwright headless-browser capture: run a scene's action list, record video.

Captures feel human: the cursor glides to each element, clicks flash a
gold ripple, text is typed letter by letter, scrolling moves in steps,
and natural jitter separates actions.
"""
from __future__ import annotations

import random
import shutil
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

VIEWPORT = {"width": 1280, "height": 720}
FPS = 30


class CaptureError(RuntimeError):
    pass


# Gold click ripple injected into the page so the recorded cursor feels alive.
RIPPLE_STYLE = """
@keyframes montaz-ripple {
  from { transform: scale(.3); opacity: .85; }
  to   { transform: scale(2.4); opacity: 0; }
}
.montaz-ripple {
  position: fixed; width: 46px; height: 46px; margin: -23px 0 0 -23px;
  border-radius: 9999px; border: 3px solid rgba(251,191,36,.9);
  pointer-events: none; z-index: 2147483647;
  animation: montaz-ripple .55s ease-out forwards;
}
"""


def _inject_ripple_css(page) -> None:
    page.add_style_tag(content=RIPPLE_STYLE)


def _ripple(page, x: float, y: float) -> None:
    page.evaluate(
        """([x, y]) => {
             const r = document.createElement('div');
             r.className = 'montaz-ripple';
             r.style.left = x + 'px';
             r.style.top = y + 'px';
             document.body.appendChild(r);
             setTimeout(() => r.remove(), 700);
           }""",
        [x, y],
    )


def _human_click(page, selector: str, timeout: int = 8000) -> None:
    """Move the cursor smoothly to the element, flash a ripple, then click."""
    loc = page.locator(selector).first
    box = loc.bounding_box(timeout=timeout)
    if box:
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.mouse.move(cx, cy, steps=16)
        page.wait_for_timeout(140)
        _ripple(page, cx, cy)
        page.wait_for_timeout(200)
    loc.click(timeout=timeout)


def _apply_action(page, action: dict[str, Any], rng) -> float:
    """Run one action on the page; returns seconds consumed (for record)."""
    kind = action.get("do")
    if kind == "goto":
        page.goto(action["url"], wait_until="domcontentloaded", timeout=20000)
        _inject_ripple_css(page)
        page.wait_for_timeout(400 + rng.randint(0, 250))
    elif kind == "click":
        _human_click(page, action["selector"], timeout=8000)
        page.wait_for_timeout(400 + rng.randint(0, 250))
    elif kind == "fill":
        _human_click(page, action["selector"], timeout=8000)
        page.keyboard.press("Control+A")
        page.keyboard.type(action.get("text", ""), delay=38)  # typewriter
        page.wait_for_timeout(300 + rng.randint(0, 200))
    elif kind == "press":
        page.keyboard.press(action.get("key", "Enter"))
        page.wait_for_timeout(300 + rng.randint(0, 200))
    elif kind == "scroll":
        delta = int(action.get("delta", 600))
        for _ in range(4):  # smooth-ish wheel steps
            page.mouse.wheel(0, delta // 4 or 1)
            page.wait_for_timeout(140)
        page.wait_for_timeout(250 + rng.randint(0, 200))
    elif kind == "wait":
        page.wait_for_timeout(min(int(action.get("ms", 500)), 5000))
    elif kind == "record":
        secs = float(action.get("seconds", 0))
        if secs > 0:
            page.wait_for_timeout(int(secs * 1000))
        return secs
    else:
        raise CaptureError(f"Aksi capture tidak dikenal: {kind}")
    return 0.0


def capture_scene(actions: list[dict[str, Any]], out_dir: Path, record_seconds: float, base_url: str = "") -> Path:
    """Record one scene. Returns path to the .webm video.

    `record_seconds` should match the narration audio duration; actions run first,
    then any trailing "record" action pads to fill the remaining time.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport=VIEWPORT, record_video_dir=str(out_dir), record_video_size=VIEWPORT)
        page = context.new_page()
        recorded = 0.0
        rng = random.Random(int(record_seconds * 1000) + len(str(actions)))
        try:
            # Absolute URL, or relative to the project's app_url.
            for action in actions:
                if action.get("do") == "goto" and action["url"].startswith("/"):
                    if not base_url:
                        raise CaptureError("Aksi goto relatif butuh app_url project (isi di layar Project).")
                    action = {**action, "url": base_url + action["url"]}
                if action.get("do") == "record" and record_seconds > 0:
                    remaining = max(record_seconds - recorded, float(action.get("seconds", 0)))
                    action = {**action, "seconds": remaining}
                recorded += _apply_action(page, action, rng)
        finally:
            video = page.video
            page.close()
            context.close()
            path = video.path() if video else None
            browser.close()
    if not path or not Path(path).exists():
        raise CaptureError("Playwright tidak menghasilkan video untuk scene ini.")
    final = out_dir / "capture.webm"
    shutil.move(str(path), final)
    return final
