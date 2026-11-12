"""Playwright headless-browser capture: run a scene's action list, record video."""
from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

VIEWPORT = {"width": 1280, "height": 720}
FPS = 30


class CaptureError(RuntimeError):
    pass


def _apply_action(page, action: dict[str, Any]) -> float:
    """Run one action on the page; returns seconds consumed (for record)."""
    kind = action.get("do")
    if kind == "goto":
        page.goto(action["url"], wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(400)
    elif kind == "click":
        page.click(action["selector"], timeout=8000)
        page.wait_for_timeout(400)
    elif kind == "fill":
        page.fill(action["selector"], action.get("text", ""), timeout=8000)
    elif kind == "press":
        page.keyboard.press(action.get("key", "Enter"))
    elif kind == "scroll":
        page.mouse.wheel(0, int(action.get("delta", 600)))
        page.wait_for_timeout(300)
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
                recorded += _apply_action(page, action)
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
