"""Script generator tests: draft structure + language templates + page scenes."""
from __future__ import annotations

from app.scriptgen.generator import generate_draft, page_scenes


def test_draft_has_core_scenes(mini_repo):
    scenes = generate_draft(str(mini_repo), "http://localhost:3000", "en-US")
    titles = [s["title"] for s in scenes]
    assert "Intro" in titles
    assert "The Problem" in titles
    assert "Built With" in titles
    assert "Outro" in titles
    # Per-feature scenes explain every feature (Teams-style walkthrough).
    feature_scenes = [t for t in titles if t.startswith("Feature:")]
    assert len(feature_scenes) == 3  # mini repo has 3 features
    assert any("Smart search" in t for t in feature_scenes)
    # Every scene carries a visual and a unique id.
    ids = [s["id"] for s in scenes]
    assert len(ids) == len(set(ids))
    assert all(s["visual"]["type"] for s in scenes)


def test_narration_mentions_project_name(mini_repo):
    scenes = generate_draft(str(mini_repo), "", "en-US")
    intro = next(s for s in scenes if s["title"] == "Intro")
    assert "KostFinder" in intro["narration"]


def test_indonesian_templates(mini_repo):
    scenes = generate_draft(str(mini_repo), "", "id-ID")
    intro = next(s for s in scenes if s["title"] == "Intro")
    assert "Halo juri" in intro["narration"]


def test_unknown_language_falls_back_to_english(mini_repo):
    scenes = generate_draft(str(mini_repo), "", "xx-XX")
    intro = next(s for s in scenes if s["title"] == "Intro")
    assert "Hi judges" in intro["narration"]


def test_page_scenes_use_browser_capture():
    pages = [
        {"url": "http://localhost:3000/", "title": "Home"},
        {"url": "http://localhost:3000/rooms", "title": "Rooms"},
    ]
    scenes = page_scenes(pages, "en-US")
    assert len(scenes) == 2
    for scene in scenes:
        assert scene["visual"]["type"] == "browser"
        kinds = [a["do"] for a in scene["visual"]["actions"]]
        assert kinds[0] == "goto" and "record" in kinds
