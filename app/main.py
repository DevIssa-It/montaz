"""FastAPI app: studio API + static serving (web/dist, project data).

Security model (local single-user tool):
- Binds 127.0.0.1 only (see scripts/run.*); no CORS middleware — the UI is
  served same-origin, so other websites in your browser cannot call this API.
- API keys stay on disk (settings.local.json) and are never sent to the UI.
- Terminal scenes run shell commands from the user's own project.json on the
  user's own machine; the API never accepts a raw command from the network.
"""
from __future__ import annotations

import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import project_store, settings as settings_mod
from .render import pipeline
from .scriptgen import crawler, generator
from .tts import base as tts_base
from .tts import edge_engine, elevenlabs_engine, openai_engine, gemini_engine  # noqa: F401 - register engines

app = FastAPI(title="Foley", docs_url="/api/docs")

# One render job per project.
_jobs: dict[str, pipeline.RenderStatus] = {}
_job_threads: dict[str, threading.Thread] = {}


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "web_dist": (settings_mod.REPO_ROOT / "web" / "dist").exists()}

# ---------------------------------------------------------------- settings

class SettingsUpdate(BaseModel):
    tts_engine: str | None = None
    language: str | None = None
    voice: str | None = None
    api_keys: dict[str, str] | None = None
    script_polish_model: str | None = None


@app.get("/api/settings")
def get_settings() -> dict:
    return settings_mod.mask_settings(settings_mod.load_settings())


@app.put("/api/settings")
def put_settings(update: SettingsUpdate) -> dict:
    updates = {k: v for k, v in update.model_dump().items() if v is not None}
    return settings_mod.mask_settings(settings_mod.save_settings(updates))


@app.post("/api/settings/test/{engine_id}")
async def test_engine(engine_id: str) -> dict:
    keys = settings_mod.load_settings().get("api_keys", {})
    try:
        await tts_base.get_engine(engine_id).test_connection(keys)
        return {"ok": True, "message": "Koneksi berhasil."}
    except tts_base.TTSError as exc:
        return {"ok": False, "message": str(exc)}


# ---------------------------------------------------------------- TTS catalog

@app.get("/api/tts/engines")
def engines() -> list[dict]:
    keys = settings_mod.load_settings().get("api_keys", {})
    return tts_base.list_engines(keys)


@app.get("/api/tts/voices")
async def voices(engine: str, language: str | None = None) -> list[dict]:
    keys = settings_mod.load_settings().get("api_keys", {})
    try:
        items = await tts_base.get_engine(engine).voices(keys)
    except tts_base.TTSError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if language:
        items = [v for v in items if v.language.lower().startswith(language.split("-")[0].lower())]
    return [
        {"id": v.id, "label": v.label, "language": v.language, "gender": v.gender}
        for v in sorted(items, key=lambda v: (v.language, v.id))
    ]


# ---------------------------------------------------------------- projects

class ProjectCreate(BaseModel):
    name: str
    project_folder: str = ""
    app_url: str = ""


class ProjectUpdate(BaseModel):
    name: str | None = None
    project_folder: str | None = None
    app_url: str | None = None
    tts: dict | None = None
    bgm: dict | None = None
    scenes: list[dict] | None = None


@app.post("/api/projects")
def create_project(body: ProjectCreate) -> dict:
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Nama project wajib diisi.")
    if body.project_folder and not Path(body.project_folder).is_dir():
        raise HTTPException(status_code=400, detail=f"Folder tidak ditemukan: {body.project_folder}")
    return project_store.create_project(body.name.strip(), body.project_folder, body.app_url)


@app.get("/api/projects")
def list_projects() -> list[dict]:
    return project_store.list_projects()


@app.get("/api/projects/{pid}")
def get_project(pid: str) -> dict:
    project = project_store.get_project(pid)
    if project is None:
        raise HTTPException(status_code=404, detail="Project tidak ditemukan.")
    return project


@app.put("/api/projects/{pid}")
def update_project(pid: str, body: ProjectUpdate) -> dict:
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    project = project_store.update_project(pid, updates)
    if project is None:
        raise HTTPException(status_code=404, detail="Project tidak ditemukan.")
    return project


@app.delete("/api/projects/{pid}")
def delete_project(pid: str) -> dict:
    if not project_store.delete_project(pid):
        raise HTTPException(status_code=404, detail="Project tidak ditemukan.")
    _jobs.pop(pid, None)
    return {"ok": True}


# ---------------------------------------------------------------- script generation

class ScriptGenRequest(BaseModel):
    language: str = ""
    polish: bool = False


@app.post("/api/projects/{pid}/scriptgen")
async def scriptgen(pid: str, body: ScriptGenRequest) -> dict:
    project = project_store.get_project(pid)
    if project is None:
        raise HTTPException(status_code=404, detail="Project tidak ditemukan.")
    if not project.get("project_folder"):
        raise HTTPException(status_code=400, detail="Isi folder project dulu di layar Project.")
    settings = settings_mod.load_settings()
    language = body.language or settings.get("language", "en-US")

    try:
        scenes = generator.generate_draft(project["project_folder"], project.get("app_url", ""), language)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Live app pages -> browser-capture scenes right after the Problem card.
    if project.get("app_url"):
        pages = await crawler.crawl_site(project["app_url"])
        if pages:
            insert_at = next(
                (i + 1 for i, s in enumerate(scenes) if s["title"] == "The Problem"), 1
            )
            scenes[insert_at:insert_at] = generator.page_scenes(pages, language)

    if body.polish:
        keys = settings.get("api_keys", {})
        if not (keys.get("openai") or keys.get("gemini")):
            raise HTTPException(status_code=400, detail="Polish AI butuh API key OpenAI atau Gemini di Settings.")
        scenes = await generator.polish_with_llm(scenes, language, keys)

    project = project_store.update_project(pid, {"scenes": scenes})
    return project


# ---------------------------------------------------------------- scene audio preview

class SceneAudioRequest(BaseModel):
    scene_id: str
    engine: str = ""
    voice: str = ""


@app.post("/api/projects/{pid}/audio")
async def scene_audio(pid: str, body: SceneAudioRequest) -> dict:
    project = project_store.get_project(pid)
    if project is None:
        raise HTTPException(status_code=404, detail="Project tidak ditemukan.")
    scene = next((s for s in project["scenes"] if s["id"] == body.scene_id), None)
    if scene is None:
        raise HTTPException(status_code=404, detail="Scene tidak ditemukan.")
    settings = settings_mod.load_settings()
    engine_id = body.engine or (project.get("tts") or {}).get("engine") or settings["tts_engine"]
    voice = body.voice or (project.get("tts") or {}).get("voice") or settings["voice"]
    engine = tts_base.get_engine(engine_id)
    audio_dir = project_store.project_dir(pid) / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    ext = pipeline.AUDIO_EXT.get(engine_id, "mp3")
    out = audio_dir / f"{scene['id']}.{ext}"
    try:
        await engine.synthesize(scene["narration"], voice, str(out), settings.get("api_keys", {}))
    except tts_base.TTSError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    scene["audio"] = out.name
    project_store.update_project(pid, {"scenes": project["scenes"]})
    return {"ok": True, "audio": f"/api/data/{pid}/audio/{out.name}"}


# ---------------------------------------------------------------- assets

@app.post("/api/projects/{pid}/assets")
async def upload_asset(pid: str, file: UploadFile) -> dict:
    project = project_store.get_project(pid)
    if project is None:
        raise HTTPException(status_code=404, detail="Project tidak ditemukan.")
    assets_dir = project_store.project_dir(pid) / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in file.filename or "asset")
    dest = assets_dir / safe_name
    dest.write_bytes(await file.read())
    return {"ok": True, "path": f"assets/{safe_name}", "url": f"/api/data/{pid}/assets/{safe_name}"}


# ---------------------------------------------------------------- render

@app.post("/api/projects/{pid}/render")
def start_render(pid: str) -> dict:
    project = project_store.get_project(pid)
    if project is None:
        raise HTTPException(status_code=404, detail="Project tidak ditemukan.")
    current = _jobs.get(pid)
    if current and current.state == "running":
        raise HTTPException(status_code=409, detail="Render sedang berjalan untuk project ini.")
    status = pipeline.RenderStatus()
    _jobs[pid] = status
    settings_snapshot = settings_mod.load_settings()
    thread = threading.Thread(
        target=lambda: pipeline.safe_run(pid, settings_snapshot, status), daemon=True
    )
    _job_threads[pid] = thread
    thread.start()
    return {"ok": True, "state": status.state}


@app.get("/api/projects/{pid}/render/status")
def render_status(pid: str) -> dict:
    status = _jobs.get(pid)
    if status is None:
        return {"state": "idle", "progress": 0.0, "message": "", "steps": []}
    out = status.output
    return {
        "state": status.state,
        "progress": status.progress,
        "message": status.message,
        "error": status.error,
        "steps": status.steps,
        "output": f"/api/data/{pid}/output/{Path(out).name}" if out else "",
    }


# ---------------------------------------------------------------- static

# NOTE: mounts swallow every path registered AFTER them, so all /api routes
# (including health) must be defined above this section.
settings_mod.DATA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/api/data", StaticFiles(directory=settings_mod.DATA_DIR), name="data")

WEB_DIST = settings_mod.REPO_ROOT / "web" / "dist"
if WEB_DIST.exists():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")
