"""Per-scene thumbnail cache: a real frame for every timeline block.

- card     -> rendered by cards.py (PIL)
- browser  -> live Playwright screenshot of the target URL (what you see
              is what the capture will record)
- terminal -> rendered still of the command + captured output
- image    -> scaled asset
- video    -> frame extracted by FFmpeg at half duration
Everything else -> title placeholder. Results are cached under
data/<pid>/thumbs/ keyed by an md5 of the scene's visual config, so a
changed scene regenerates but untouched scenes reuse their frame.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from .. import project_store
from ..capture import terminal as terminal_capture
from . import cards, ffmpeg

THUMB_W, THUMB_H = 384, 216


def _scale_to_thumb(src: Path, dst: Path) -> None:
    subprocess.run(
        [
            ffmpeg.ffmpeg_exe(), "-hide_banner", "-i", str(src),
            "-vf",
            f"scale={THUMB_W}:{THUMB_H}:force_original_aspect_ratio=decrease,"
            f"pad={THUMB_W}:{THUMB_H}:(ow-iw)/2:(oh-ih)/2:color=0x090A0F",
            "-frames:v", "1", "-y", str(dst),
        ],
        check=True, capture_output=True,
    )


def _browser_shot(url: str, dst: Path) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(700)
        page.screenshot(path=str(dst))
        browser.close()


def _video_frame(src: Path, dst: Path) -> None:
    duration = ffmpeg.probe_duration(src)
    at = max(min(duration / 2, duration - 0.2), 0)
    subprocess.run(
        [ffmpeg.ffmpeg_exe(), "-hide_banner", "-ss", f"{at:.2f}", "-i", str(src),
         "-frames:v", "1", "-y", str(dst)],
        check=True, capture_output=True,
    )


def _terminal_still(visual: dict[str, Any], project: dict[str, Any], dst: Path) -> None:
    result = terminal_capture.run_command(
        visual.get("command", "echo hello"), project.get("project_folder", "")
    )
    cards.render_terminal_still(result["command"], result["lines"], dst)


def _resolve_first_url(scene: dict[str, Any], project: dict[str, Any]) -> str | None:
    app_url = (project.get("app_url") or "").rstrip("/")
    for action in scene.get("visual", {}).get("actions", []):
        if action.get("do") == "goto":
            url = action.get("url", "")
            if url.startswith("/"):
                return app_url + url if app_url else None
            return url or None
    return app_url or None


def ensure_thumb(project_id: str, scene: dict[str, Any], project: dict[str, Any]) -> Path:
    """Generate (or reuse) the thumbnail for one scene; returns the PNG path."""
    pdir = project_store.project_dir(project_id)
    thumbs = pdir / "thumbs"
    thumbs.mkdir(exist_ok=True)
    dst = thumbs / f"{scene['id']}.png"
    meta = thumbs / f"{scene['id']}.json"

    config = json.dumps(
        {"visual": scene.get("visual"), "app_url": project.get("app_url"),
         "title": scene.get("title")},
        sort_keys=True,
    )
    hash_value = hashlib.md5(config.encode()).hexdigest()
    if dst.exists() and meta.exists() and json.loads(meta.read_text()).get("hash") == hash_value:
        return dst

    work = thumbs / f"_work_{scene['id']}.png"
    vtype = (scene.get("visual") or {}).get("type", "card")
    visual = scene.get("visual") or {}

    try:
        if vtype == "card":
            card = visual.get("card") or {}
            cards.render_card(
                card.get("kind", "title"),
                card.get("heading") or scene.get("title", ""),
                card.get("bullets", []),
                work,
            )
        elif vtype == "browser":
            url = _resolve_first_url(scene, project)
            if url is None:
                raise ValueError("no app_url")
            _browser_shot(url, work)
        elif vtype == "terminal":
            _terminal_still(visual, project, work)
        elif vtype in ("image", "video"):
            asset = project_store.resolve_asset_path(project_id, str(visual.get("path", "")))
            if asset is None or not asset.exists():
                raise ValueError("asset missing")
            if vtype == "image":
                _scale_to_thumb(asset, work)
                work.replace(dst)
                meta.write_text(json.dumps({"hash": hash_value}), encoding="utf-8")
                return dst
            _video_frame(asset, work)
        else:
            raise ValueError(f"unknown type {vtype}")

        _scale_to_thumb(work, dst)
    except Exception:
        # Placeholder so the timeline never breaks: a title card.
        cards.render_card("title", scene.get("title", ""), ["frame unavailable"], work)
        _scale_to_thumb(work, dst)
    finally:
        work.unlink(missing_ok=True)

    meta.write_text(json.dumps({"hash": hash_value}), encoding="utf-8")
    return dst
