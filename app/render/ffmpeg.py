"""FFmpeg wrapper: duration probing, scene segments, crossfade concat, BGM mix.

Uses the system ffmpeg when present, else the imageio-ffmpeg bundled binary
(that bundle ships ffmpeg only — no ffprobe — hence the stderr parsing below).
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

XFADE = 0.4  # crossfade seconds
PAD = 0.6    # breathing room after narration per scene
FPS = 30
TARGET = "1920:1080"
VCODEC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
ACODEC = ["-c:a", "aac", "-b:a", "192k"]


def ffmpeg_exe() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def _run(args: list[str]) -> subprocess.CompletedProcess:
    proc = subprocess.run([ffmpeg_exe(), "-hide_banner", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg gagal: {proc.stderr[-600:]}")
    return proc


def probe_duration(media_path: str | Path) -> float:
    proc = subprocess.run(
        [ffmpeg_exe(), "-hide_banner", "-i", str(media_path)],
        capture_output=True, text=True,
    )
    match = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", proc.stderr)
    if not match:
        raise RuntimeError(f"Tidak bisa membaca durasi: {media_path}")
    h, m, s = match.groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def scene_duration(audio_path: str | Path) -> float:
    return max(probe_duration(audio_path) + PAD, 1.5)


def _scale_pad() -> list[str]:
    # NOTE: pad takes colon-separated dims ("1920:1080"); the WxH shorthand is scale-only.
    return [
        "-vf",
        f"scale={TARGET}:force_original_aspect_ratio=decrease,"
        f"pad={TARGET}:(ow-iw)/2:(oh-ih)/2:color=0x090A0F,setsar=1",
    ]


def segment_from_image(image_path: Path, audio_path: Path, out_path: Path, duration: float, zoom_in: bool = True) -> Path:
    zoom_expr = "1+0.00045*in" if zoom_in else "max(1.15-0.00045*in,1.0)"
    _run([
        "-loop", "1", "-framerate", str(FPS), "-t", f"{duration:.3f}", "-i", str(image_path),
        "-i", str(audio_path),
        "-vf", (
            f"scale=2400:1350:force_original_aspect_ratio=increase,crop=2400:1350,"
            f"zoompan=z='{zoom_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps={FPS}"
        ),
        "-af", "apad", "-t", f"{duration:.3f}",
        *VCODEC, *ACODEC, "-shortest", "-y", str(out_path),
    ])
    return out_path


def segment_from_frames(frames_dir: Path, fps: int, audio_path: Path, out_path: Path, duration: float) -> Path:
    _run([
        "-framerate", str(fps), "-i", str(frames_dir / "f_%05d.png"),
        "-i", str(audio_path),
        "-vf", f"scale=1920:1080,fps={FPS}",
        "-af", "apad", "-t", f"{duration:.3f}",
        *VCODEC, *ACODEC, "-y", str(out_path),
    ])
    return out_path


def segment_from_video(clip_path: Path, audio_path: Path, out_path: Path, duration: float) -> Path:
    """Clip muted, looped if shorter / trimmed if longer than narration."""
    _run([
        "-stream_loop", "-1", "-t", f"{duration:.3f}", "-i", str(clip_path),
        "-i", str(audio_path),
        *_scale_pad(),
        "-map", "0:v:0", "-map", "1:a:0",
        "-af", "apad", "-t", f"{duration:.3f}", "-r", str(FPS),
        *VCODEC, *ACODEC, "-y", str(out_path),
    ])
    return out_path


def concat_segments(segment_paths: list[Path], out_path: Path) -> Path:
    """Chain xfade video + acrossfade audio; falls back to hard-cut concat on failure."""
    if len(segment_paths) == 1:
        shutil.copyfile(segment_paths[0], out_path)
        return out_path
    try:
        return _concat_xfade(segment_paths, out_path)
    except RuntimeError:
        return _concat_hardcut(segment_paths, out_path)


def _concat_xfade(segment_paths: list[Path], out_path: Path) -> Path:
    durations = [probe_duration(p) for p in segment_paths]
    inputs: list[str] = []
    for p in segment_paths:
        inputs += ["-i", str(p)]
    filters: list[str] = []
    vprev, aprev = "0:v", "0:a"
    offset = 0.0
    for i in range(1, len(segment_paths)):
        offset += durations[i - 1] - XFADE
        vout, aout = f"v{i}", f"a{i}"
        filters.append(
            f"[{vprev}][{i}:v]xfade=transition=fade:duration={XFADE}:offset={offset:.3f}[{vout}]"
        )
        filters.append(f"[{aprev}][{i}:a]acrossfade=d={XFADE}:c1=tri:c2=tri[{aout}]")
        vprev, aprev = vout, aout
    _run([
        *inputs,
        "-filter_complex", ";".join(filters),
        "-map", f"[{vprev}]", "-map", f"[{aprev}]",
        *VCODEC, *ACODEC, "-y", str(out_path),
    ])
    return out_path


def _concat_hardcut(segment_paths: list[Path], out_path: Path) -> Path:
    list_file = out_path.parent / "concat_list.txt"
    list_file.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in segment_paths), encoding="utf-8"
    )
    _run(["-f", "concat", "-safe", "0", "-i", str(list_file), *VCODEC, *ACODEC, "-y", str(out_path)])
    list_file.unlink(missing_ok=True)
    return out_path


def mix_bgm(video_path: Path, bgm_path: Path, out_path: Path, volume: float = 0.15) -> Path:
    _run([
        "-i", str(video_path), "-i", str(bgm_path),
        "-filter_complex",
        f"[1:a]volume={volume},afade=t=out:st={max(probe_duration(video_path) - 1.0, 0):.2f}:d=1.0[b];"
        f"[0:a][b]amix=inputs=2:duration=first:dropout_transition=3[a]",
        "-map", "0:v", "-map", "[a]",
        *VCODEC, *ACODEC, "-y", str(out_path),
    ])
    return out_path
