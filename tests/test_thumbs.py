"""Thumbnail cache tests: card scene + placeholder fallback."""
from __future__ import annotations

from app import project_store
from app.render import thumbs


def _make_project(tmp_path, monkeypatch):
    monkeypatch.setattr(project_store, "DATA_DIR", tmp_path / "data")
    project = project_store.create_project("ThumbTest")
    scene = {
        "id": "sc_thumb1",
        "title": "Intro",
        "narration": "",
        "visual": {"type": "card", "card": {"kind": "title", "heading": "Hello", "bullets": []}},
    }
    project_store.update_project(project["id"], {"scenes": [scene]})
    project = project_store.get_project(project["id"])
    return project, scene


def test_card_thumb_generated(tmp_path, monkeypatch):
    project, scene = _make_project(tmp_path, monkeypatch)
    path = thumbs.ensure_thumb(project["id"], scene, project)
    assert path.exists() and path.stat().st_size > 1000
    # second call hits the cache (no regeneration, same file)
    again = thumbs.ensure_thumb(project["id"], scene, project)
    assert again == path


def test_browser_scene_without_app_url_falls_back_to_placeholder(tmp_path, monkeypatch):
    project, _ = _make_project(tmp_path, monkeypatch)
    scene = {
        "id": "sc_thumb2",
        "title": "Demo",
        "narration": "",
        "visual": {"type": "browser", "actions": [{"do": "goto", "url": "/x"}]},
    }
    project_store.update_project(project["id"], {"scenes": [scene]})
    fresh = project_store.get_project(project["id"])
    target = next(s for s in fresh["scenes"] if s["id"] == "sc_thumb2")
    path = thumbs.ensure_thumb(project["id"], target, fresh)
    assert path.exists()  # placeholder card, never raises
