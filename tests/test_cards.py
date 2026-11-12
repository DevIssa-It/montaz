"""Card renderer tests: pixel output + dimensions."""
from __future__ import annotations

from PIL import Image

from app.render.cards import render_card, W, H


def test_title_card_renders(tmp_path):
    out = tmp_path / "card.png"
    render_card("title", "KostFinder", ["Find rooms fast"], out)
    img = Image.open(out)
    assert img.size == (W, H)


def test_bullets_card_renders(tmp_path):
    out = tmp_path / "bullets.png"
    render_card("bullets", "Key Features", ["One", "Two", "Three"], out)
    img = Image.open(out)
    assert img.size == (W, H)
