"""Project store tests: CRUD + scene validation + traversal guard."""
from __future__ import annotations

from app import project_store


def test_create_update_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(project_store, "DATA_DIR", tmp_path / "data")
    project = project_store.create_project("Demo", "C:/tmp/folder", "http://localhost:3000")
    assert project["name"] == "Demo"
    assert (tmp_path / "data" / project["id"]).exists()

    scenes = [
        {"id": "sc_1", "title": "Intro", "narration": "hi", "visual": {"type": "card", "card": {"kind": "title", "heading": "H", "bullets": []}}},
        {"id": "sc_2", "title": "Bad", "narration": "x", "visual": {"type": "hologram"}},
    ]
    updated = project_store.update_project(project["id"], {"scenes": scenes})
    assert updated is not None
    assert len(updated["scenes"]) == 2
    # Invalid visual type is coerced back to a card.
    assert updated["scenes"][1]["visual"]["type"] == "card"

    assert project_store.delete_project(project["id"])
    assert project_store.get_project(project["id"]) is None


def test_resolve_asset_path_blocks_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(project_store, "DATA_DIR", tmp_path / "data")
    project = project_store.create_project("Sec")
    pid = project["id"]

    inside = project_store.resolve_asset_path(pid, "assets/cover.png")
    assert inside is not None and inside.is_relative_to((tmp_path / "data" / pid).resolve())

    escape = project_store.resolve_asset_path(pid, "../outside.png")
    assert escape is None

    deep = project_store.resolve_asset_path(pid, "../../etc/passwd")
    assert deep is None

    empty = project_store.resolve_asset_path(pid, "")
    assert empty is None
