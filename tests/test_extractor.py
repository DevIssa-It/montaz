"""Extractor tests against the mini_repo fixture."""
from __future__ import annotations

from app.scriptgen.extractor import extract_project


def test_extracts_title_and_tagline(mini_repo):
    facts = extract_project(str(mini_repo))
    assert facts["name"] == "KostFinder"
    assert "boarding rooms" in facts["tagline"]


def test_extracts_features_and_problem(mini_repo):
    facts = extract_project(str(mini_repo))
    assert any("Smart search" in f for f in facts["features"])
    assert len(facts["problem"]) >= 1


def test_detects_stack_and_routes(mini_repo):
    facts = extract_project(str(mini_repo))
    assert "Node.js" in facts["stack"]
    assert "React" in facts["stack"]
    assert "/rooms" in facts["routes"]


def test_missing_folder_raises(tmp_path):
    import pytest

    with pytest.raises(ValueError):
        extract_project(str(tmp_path / "does-not-exist"))
