"""Draft a Devpost-style scene script from extracted project facts, with optional LLM polish."""
from __future__ import annotations

import json
from typing import Any

import httpx

from ..project_store import new_scene
from .extractor import extract_project

# Rule-based narration templates per language. "en" is the fallback.
TEMPLATES: dict[str, dict[str, str]] = {
    "en": {
        "intro": (
            "Hi judges! This is {name}. {tagline} "
            "In the next two minutes we'll show you what it does, how it works, and why it matters."
        ),
        "problem": (
            "Every hackathon project starts with a real pain point. "
            "Here's the problem {name} sets out to solve."
        ),
        "page": "Let's take a look at {page}. {extra}",
        "page_extra": "Notice how the interface stays simple while the features run underneath.",
        "features": "So what can {name} actually do? Here are the key features we built during the hackathon.",
        "stack": "Under the hood, {name} is built with {stack}. Every part was chosen to ship fast and stay reliable.",
        "outro": (
            "That's {name} — built in a weekend, ready to grow. "
            "Thanks for watching, and we'd love to hear your feedback!"
        ),
    },
    "id": {
        "intro": (
            "Halo juri! Ini {name}. {tagline} "
            "Dalam dua menit ke depan kami akan menunjukkan apa yang dilakukan, bagaimana cara kerjanya, dan mengapa ini penting."
        ),
        "problem": (
            "Setiap project hackathon berawal dari masalah nyata. "
            "Inilah masalah yang ingin diselesaikan oleh {name}."
        ),
        "page": "Sekarang kita lihat {page}. {extra}",
        "page_extra": "Perhatikan antarmukanya tetap sederhana meski fiturnya berjalan di belakang layar.",
        "features": "Jadi, apa saja yang bisa dilakukan {name}? Ini fitur-fitur utama yang kami bangun selama hackathon.",
        "stack": "Di balik layar, {name} dibangun dengan {stack}. Semua dipilih agar cepat dirilis dan tetap andal.",
        "outro": (
            "Itulah {name} — dibangun dalam satu akhir pekan, siap untuk berkembang. "
            "Terima kasih sudah menonton, kami menantikan masukan dari Anda!"
        ),
    },
}


def _templates(language: str) -> dict[str, str]:
    base = language.split("-")[0].lower()
    return TEMPLATES.get(base, TEMPLATES["en"])


def _clean_tagline(tagline: str) -> str:
    tagline = tagline.strip().strip("*#`")
    return tagline if len(tagline) < 160 else tagline[:157] + "..."


def generate_draft(project_folder: str, app_url: str, language: str, crawl_limit: int = 4) -> list[dict[str, Any]]:
    """Build the initial scene list: intro card → problem → app pages → features → stack → outro."""
    facts = extract_project(project_folder)
    tpl = _templates(language)
    name = facts["name"]
    tagline = _clean_tagline(facts.get("tagline", "") or "")
    scenes: list[dict[str, Any]] = []

    scenes.append(
        new_scene(
            title="Intro",
            narration=tpl["intro"].format(name=name, tagline=tagline or "A hackathon project."),
            visual={"type": "card", "card": {"kind": "title", "heading": name, "bullets": [tagline] if tagline else []}},
        )
    )
    if facts.get("problem"):
        scenes.append(
            new_scene(
                title="The Problem",
                narration=tpl["problem"].format(name=name),
                visual={"type": "card", "card": {"kind": "bullets", "heading": "The Problem", "bullets": facts["problem"][:3]}},
            )
        )

    # App walkthrough scenes are added by main.py after crawling (needs app_url live).
    # Placeholder markers are returned in meta so the caller knows what to insert.
    if facts.get("features"):
        scenes.append(
            new_scene(
                title="Key Features",
                narration=tpl["features"].format(name=name),
                visual={"type": "card", "card": {"kind": "bullets", "heading": "Key Features", "bullets": facts["features"][:5]}},
            )
        )
    if facts.get("stack"):
        stack_str = ", ".join(facts["stack"][:5])
        scenes.append(
            new_scene(
                title="Built With",
                narration=tpl["stack"].format(name=name, stack=stack_str),
                visual={"type": "card", "card": {"kind": "stack", "heading": "Built With", "bullets": facts["stack"][:7]}},
            )
        )
    scenes.append(
        new_scene(
            title="Outro",
            narration=tpl["outro"].format(name=name),
            visual={"type": "card", "card": {"kind": "title", "heading": name, "bullets": []}},
        )
    )
    return scenes


def page_scenes(pages: list[dict[str, str]], language: str) -> list[dict[str, Any]]:
    """Browser-capture scenes for crawled pages; inserted after the problem scene."""
    tpl = _templates(language)
    scenes = []
    for page in pages[:4]:
        title = page.get("title") or page["url"]
        narration = tpl["page"].format(
            page=title, extra=tpl["page_extra"] if page is pages[0] else ""
        )
        scenes.append(
            new_scene(
                title=f"Demo: {title}"[:60],
                narration=narration,
                visual={"type": "browser", "actions": [{"do": "goto", "url": page["url"]}, {"do": "wait", "ms": 800}, {"do": "record"}]},
            )
        )
    return scenes


def _polish_prompt(scenes: list[dict[str, Any]], language: str) -> str:
    payload = [{"id": s["id"], "title": s["title"], "narration": s["narration"]} for s in scenes]
    return (
        "You rewrite hackathon demo video narration. Rules: keep the SAME JSON structure and ids; "
        "one narration per scene; 1-3 sentences each; spoken style, energetic but not cheesy; "
        f"write in language '{language}'; do not invent features that are not implied by the input. "
        "Return ONLY a JSON array like the input.\n\n" + json.dumps(payload, ensure_ascii=False)
    )


async def polish_with_llm(scenes: list[dict[str, Any]], language: str, keys: dict[str, str]) -> list[dict[str, Any]]:
    """Optionally rewrite narrations via OpenAI or Gemini (first available key). Returns scenes (possibly unchanged)."""
    prompt = _polish_prompt(scenes, language)
    texts: list[dict[str, str]] | None = None
    try:
        if keys.get("openai"):
            texts = await _polish_openai(prompt, keys["openai"])
        elif keys.get("gemini"):
            texts = await _polish_gemini(prompt, keys["gemini"])
    except (httpx.HTTPError, ValueError, KeyError):
        return scenes  # silent fallback: keep rule-based draft
    if not texts:
        return scenes
    by_id = {item.get("id"): item.get("narration", "") for item in texts if isinstance(item, dict)}
    for scene in scenes:
        improved = by_id.get(scene["id"], "").strip()
        if improved:
            scene["narration"] = improved
    return scenes


async def _polish_openai(prompt: str, key: str) -> list[dict[str, str]] | None:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.7,
            },
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return parsed if isinstance(parsed, list) else parsed.get("scenes") or parsed.get("narrations")


async def _polish_gemini(prompt: str, key: str) -> list[dict[str, str]] | None:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json", "temperature": 0.7},
            },
        )
        resp.raise_for_status()
        content = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(content)
        return parsed if isinstance(parsed, list) else parsed.get("scenes") or parsed.get("narrations")
