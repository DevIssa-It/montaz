"""Render pipeline: TTS all scenes -> build visual per scene -> segments -> concat -> final.mp4."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import random
from typing import Any

from .. import project_store
from ..capture import browser as browser_capture
from ..capture import terminal as terminal_capture
from ..tts import base as tts_base
from ..tts import edge_engine, elevenlabs_engine, openai_engine, gemini_engine  # noqa: F401 - register engines
from . import cards, ffmpeg

logger = logging.getLogger(__name__)

AUDIO_EXT = {"edge": "mp3", "elevenlabs": "mp3", "openai": "mp3", "gemini": "wav"}


@dataclass
class RenderStatus:
    state: str = "idle"  # idle | running | done | error
    progress: float = 0.0
    message: str = ""
    error: str = ""
    output: str = ""
    steps: list[str] = field(default_factory=list)

    def begin(self) -> None:
        self.state, self.progress, self.error, self.steps = "running", 0.0, "", []

    def step(self, frac: float, msg: str) -> None:
        self.progress = min(frac, 0.99)
        self.message = msg
        self.steps.append(msg)


def _tts_settings(project: dict[str, Any], settings: dict[str, Any]) -> tuple[str, str]:
    override = project.get("tts") or {}
    engine_id = override.get("engine") or settings.get("tts_engine", "edge")
    voice = override.get("voice") or settings.get("voice", "en-US-AndrewNeural")
    return engine_id, voice


def _prosody_for(scene: dict[str, Any]) -> dict[str, str]:
    """Deterministic per-scene voice variation so TTS never sounds monotone."""
    seed_src = f"{scene.get('id', '')}{scene.get('narration', '')[:60]}"
    rng = random.Random(int(hashlib.md5(seed_src.encode()).hexdigest()[:8], 16))
    rate = rng.choice([-9, -6, -4, 2])
    pitch = rng.choice([-3, -1, 1, 3])
    # edge-tts requires an explicit sign, e.g. "+2%" not "2%".
    return {
        "rate": f"{rate:+d}%",
        "pitch": f"{pitch:+d}Hz",
    }


async def _synthesize_all(scenes: list[dict[str, Any]], audio_dir: Path, engine_id: str, voice: str, keys: dict[str, str], status: RenderStatus) -> None:
    engine = tts_base.get_engine(engine_id)
    total = max(len(scenes), 1)
    for i, scene in enumerate(scenes):
        status.step(0.05 + 0.30 * i / total, f"TTS {i + 1}/{total}: {scene.get('title') or scene['id']}")
        out = audio_dir / f"{scene['id']}.{AUDIO_EXT.get(engine_id, 'mp3')}"
        await engine.synthesize(scene["narration"], voice, str(out), keys, prosody=_prosody_for(scene))
        scene["audio"] = out.name


def run_render(project_id: str, settings: dict[str, Any], status: RenderStatus, force: bool = False) -> str:
    """Blocking full render; call from a worker thread. Returns output path."""
    project = project_store.get_project(project_id)
    if project is None:
        raise RuntimeError(f"Project {project_id} tidak ditemukan.")
    if not project["scenes"]:
        raise RuntimeError("Project belum punya scene. Generate naskah dulu.")
    pdir = project_store.project_dir(project_id)
    audio_dir, assets_dir, output_dir = pdir / "audio", pdir / "assets", pdir / "output"
    work = output_dir / "work"
    # Recreate the runtime layout ourselves — folders may be missing after
    # a cache clear, and TTS/capture write into them directly.
    for folder in (audio_dir, assets_dir, output_dir, work):
        folder.mkdir(parents=True, exist_ok=True)
    scenes = [dict(s) for s in project["scenes"]]

    engine_id, voice = _tts_settings(project, settings)
    keys = settings.get("api_keys", {})

    # 1) Narration audio for every scene.
    status.step(0.02, "Menyiapkan narasi (TTS)...")
    todo = [s for s in scenes if force or not s.get("audio") or not (audio_dir / s.get("audio", "")).exists()]
    if todo:
        asyncio.run(_synthesize_all(todo, audio_dir, engine_id, voice, keys, status))

    # 2) Per-scene visual + segment.
    total = len(scenes)
    segments: list[Path] = []
    # Two real app screenshots (home + first demoed page) — feature cards
    # CUT between them mid-scene so the panel shows navigation.
    shots: list[Path] = []
    if project.get("app_url"):
        try:
            shots.append(browser_capture.screenshot_url(
                project["app_url"], work / "app_shot_1.png"))
        except Exception:  # noqa: BLE001 - app down? cards degrade gracefully
            shots = []
        if shots:
            first_page = next(
                (a.get("url") for s in scenes if s.get("visual", {}).get("type") == "browser"
                 for a in (s["visual"].get("actions") or []) if a.get("do") == "goto"),
                None,
            )
            if first_page:
                try:
                    shots.append(browser_capture.screenshot_url(first_page, work / "app_shot_2.png"))
                except Exception:  # noqa: BLE001
                    pass
    for i, scene in enumerate(scenes):
        frac = 0.35 + 0.55 * i / total
        status.step(frac, f"Scene {i + 1}/{total}: {scene.get('title') or scene['id']}")
        audio_path = audio_dir / scene["audio"]
        duration = ffmpeg.scene_duration(audio_path)
        visual = scene.get("visual") or {}
        vtype = visual.get("type", "card")
        seg = work / f"seg_{i:03d}.mp4"

        if vtype == "card":
            card = visual.get("card") or {}
            frames = cards.render_split_frames(
                card.get("heading") or scene.get("title", ""),
                card.get("bullets", []),
                shots,
                work / f"cardf_{i:03d}",
                duration,
                fps=10,
                counter=(i + 1, total),
                variant=i % 2,
            )
            ffmpeg.segment_from_frames(frames, 10, audio_path, seg, duration)
        elif vtype == "terminal":
            result = terminal_capture.run_command(visual.get("command", "echo hello"), project.get("project_folder", ""))
            frames = cards.render_terminal_frames(
                result["command"], result["lines"], work / f"term_{i:03d}", duration
            )
            ffmpeg.segment_from_frames(frames, 10, audio_path, seg, duration)
        elif vtype == "browser":
            clip = browser_capture.capture_scene(
                visual.get("actions", []), work / f"cap_{i:03d}", duration, project.get("app_url", "")
            )
            ffmpeg.segment_from_video(clip, audio_path, seg, duration)
        elif vtype in ("image", "video"):
            asset = project_store.resolve_asset_path(project_id, str(visual.get("path", "")))
            if asset is None or not asset.exists():
                raise RuntimeError(f"Aset scene {i + 1} tidak ditemukan: {visual.get('path')}")
            if vtype == "image":
                ffmpeg.segment_from_image(asset, audio_path, seg, duration, zoom_in=(i % 2 == 0))
            else:
                ffmpeg.segment_from_video(asset, audio_path, seg, duration)
        else:
            raise RuntimeError(f"Tipe visual tidak dikenal: {vtype}")
        segments.append(seg)

    # 3) Concat (+ optional BGM).
    status.step(0.93, "Menyusun video final...")
    final = output_dir / "final.mp4"
    ffmpeg.concat_segments(segments, final)
    bgm = project.get("bgm") or {}
    if bgm.get("enabled") and bgm.get("path"):
        bgm_path = project_store.resolve_asset_path(project_id, str(bgm["path"]))
        if bgm_path is not None and bgm_path.exists():
            with_bgm = output_dir / "final_bgm.mp4"
            ffmpeg.mix_bgm(final, bgm_path, with_bgm, float(bgm.get("volume", 0.15)))
            final = with_bgm

    status.state, status.progress, self_output = "done", 1.0, str(final)
    status.output = self_output
    status.message = f"Selesai: {final.name}"
    return self_output


def safe_run(project_id: str, settings: dict[str, Any], status: RenderStatus) -> None:
    """Entry point for worker threads: never raises, records the error instead."""
    status.begin()
    try:
        run_render(project_id, settings, status)
    except Exception as exc:  # noqa: BLE001 - status carries the message
        status.state, status.error = "error", f"{exc}"
        status.message = f"Render gagal: {exc}"
        logger.exception("Render failed")
