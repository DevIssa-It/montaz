"""FFmpeg smoke test: real segments from cards + concat, no network needed.

Audio is synthesized locally with ffmpeg's sine generator so the suite runs offline.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.render import cards, ffmpeg


def _sine_mp3(path: Path, seconds: float) -> None:
    subprocess.run(
        [
            ffmpeg.ffmpeg_exe(), "-hide_banner", "-f", "lavfi",
            "-i", f"sine=frequency=440:duration={seconds}",
            "-q:a", "9", "-y", str(path),
        ],
        check=True, capture_output=True,
    )


@pytest.fixture()
def audio_files(tmp_path: Path) -> list[Path]:
    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    _sine_mp3(a, 2.0)
    _sine_mp3(b, 2.0)
    return [a, b]


def test_probe_duration(audio_files):
    duration = ffmpeg.probe_duration(audio_files[0])
    assert 1.9 <= duration <= 2.4


def test_segments_and_concat(tmp_path: Path, audio_files):
    card_a = cards.render_card("title", "Alpha", [], tmp_path / "a.png")
    card_b = cards.render_card("bullets", "Beta", ["x", "y"], tmp_path / "b.png")
    seg_a = ffmpeg.segment_from_image(card_a, audio_files[0], tmp_path / "seg_a.mp4", 2.5)
    seg_b = ffmpeg.segment_from_image(card_b, audio_files[1], tmp_path / "seg_b.mp4", 2.5)
    final = ffmpeg.concat_segments([seg_a, seg_b], tmp_path / "final.mp4")

    duration = ffmpeg.probe_duration(final)
    # 2.5 + 2.5 minus one crossfade (0.4s) ≈ 4.6s; hard-cut fallback would give 5.0s.
    assert 4.0 <= duration <= 5.2


def test_segment_from_video_loop(tmp_path: Path, audio_files):
    # A 1s video source looped to cover 2.5s of narration.
    src = tmp_path / "clip.mp4"
    subprocess.run(
        [
            ffmpeg.ffmpeg_exe(), "-hide_banner", "-f", "lavfi",
            "-i", "testsrc=size=640x360:duration=1", "-r", "30",
            "-pix_fmt", "yuv420p", "-y", str(src),
        ],
        check=True, capture_output=True,
    )
    seg = ffmpeg.segment_from_video(src, audio_files[0], tmp_path / "seg.mp4", 2.5)
    assert 2.3 <= ffmpeg.probe_duration(seg) <= 2.8
