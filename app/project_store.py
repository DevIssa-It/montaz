"""Per-project storage: project.json (scenes & config), assets/, audio/, output/.

Layout: data/<project_id>/project.json + assets/ + audio/ + output/
"""
from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any

from .settings import DATA_DIR

VALID_VISUAL_TYPES = {"card", "browser", "terminal", "image", "video"}


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:48] or "project"


def project_dir(project_id: str) -> Path:
    return DATA_DIR / project_id


def _project_path(project_id: str) -> Path:
    return project_dir(project_id) / "project.json"


def new_scene(title: str = "", narration: str = "", visual: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "id": f"sc_{uuid.uuid4().hex[:8]}",
        "title": title,
        "narration": narration,
        "visual": visual or {"type": "card", "card": {"kind": "title", "heading": "", "bullets": []}},
        "audio": None,  # relative path under audio/, filled after TTS
    }


def create_project(name: str, project_folder: str = "", app_url: str = "") -> dict[str, Any]:
    project_id = f"{_slugify(name)}-{int(time.time())}"
    pdir = project_dir(project_id)
    (pdir / "assets").mkdir(parents=True, exist_ok=True)
    (pdir / "audio").mkdir(parents=True, exist_ok=True)
    (pdir / "output").mkdir(parents=True, exist_ok=True)
    project = {
        "id": project_id,
        "name": name,
        "project_folder": project_folder,
        "app_url": app_url.rstrip("/"),
        "tts": {},  # engine/language/voice overrides; empty = follow global settings
        "bgm": {"enabled": False, "path": "", "volume": 0.15},
        "scenes": [],
        "created_at": time.time(),
    }
    _project_path(project_id).write_text(json.dumps(project, indent=2), encoding="utf-8")
    return project


def list_projects() -> list[dict[str, Any]]:
    if not DATA_DIR.exists():
        return []
    projects = []
    for pdir in sorted(DATA_DIR.iterdir()):
        pfile = pdir / "project.json"
        if pfile.exists():
            projects.append(json.loads(pfile.read_text(encoding="utf-8")))
    return projects


def get_project(project_id: str) -> dict[str, Any] | None:
    pfile = _project_path(project_id)
    if not pfile.exists():
        return None
    return json.loads(pfile.read_text(encoding="utf-8"))


def update_project(project_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    project = get_project(project_id)
    if project is None:
        return None
    scenes = updates.pop("scenes", None)
    for key, value in updates.items():
        if key in ("id", "created_at"):
            continue
        if key in project:
            project[key] = value
    if scenes is not None:
        clean = []
        for scene in scenes:
            if not isinstance(scene, dict) or not scene.get("id"):
                continue
            visual = scene.get("visual") or {}
            if visual.get("type") not in VALID_VISUAL_TYPES:
                visual = {"type": "card", "card": {"kind": "title", "heading": "", "bullets": []}}
            scene["visual"] = visual
            clean.append(scene)
        project["scenes"] = clean
    project["updated_at"] = time.time()
    _project_path(project_id).write_text(json.dumps(project, indent=2), encoding="utf-8")
    return project


def has_rendered_video(project_id: str) -> bool:
    """True once a final video exists in the project's output folder."""
    output = project_dir(project_id) / "output"
    return any(output.glob("final*.mp4"))


def delete_project(project_id: str) -> bool:
    import shutil

    pdir = project_dir(project_id)
    if pdir.exists():
        shutil.rmtree(pdir)
        return True
    return False


def resolve_asset_path(project_id: str, relative: str) -> Path | None:
    """Resolve a relative asset path under the project dir; blocks `../` traversal."""
    if not relative:
        return None
    root = project_dir(project_id).resolve()
    try:
        candidate = (root / relative).resolve()
        candidate.relative_to(root)
    except (ValueError, OSError):
        return None
    return candidate
