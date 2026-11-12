"""Shared pytest fixtures: repo path + a tiny fake hackathon repo to extract from."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture()
def mini_repo(tmp_path: Path) -> Path:
    """A minimal project folder with README, package.json, and route patterns."""
    repo = tmp_path / "kostfinder"
    (repo / "src").mkdir(parents=True)
    (repo / "README.md").write_text(
        """# KostFinder

Find boarding rooms near your campus in seconds.

## Features
- Smart search by price and distance
- Room photo galleries
- Owner contact shortcuts

## The Problem
Students waste weeks walking around to find a room that fits their budget.
""",
        encoding="utf-8",
    )
    (repo / "package.json").write_text(
        '{"dependencies": {"react": "^19.0.0", "tailwindcss": "^4.0.0"}}',
        encoding="utf-8",
    )
    (repo / "src" / "server.js").write_text(
        "app.get('/rooms', listRooms);\napp.post('/rooms', createRoom);\n",
        encoding="utf-8",
    )
    return repo
