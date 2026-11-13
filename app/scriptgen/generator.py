"""Draft a Devpost-style scene script from extracted project facts, with optional LLM polish."""
from __future__ import annotations

import json
from typing import Any

import httpx

from ..project_store import new_scene
from .extractor import extract_project

# Rule-based narration templates per language. "en" is the fallback.
# Multiple variants per beat — pick different projects, get different scripts.
TEMPLATES: dict[str, dict[str, list[str]]] = {
    "en": {
        "intro": [
            "Hi judges! This is {name}. {tagline} "
            "In the next two minutes we'll show you what it does, how it works, and why it matters.",
            "Meet {name}. {tagline} We built it to fix a problem we kept running into ourselves — "
            "let us walk you through it.",
            "This is {name} — {tagline} Two minutes from now you'll know exactly why we spent our weekend on it.",
        ],
        "problem": [
            "Every hackathon project starts with a real pain point. "
            "Here's the problem {name} sets out to solve.",
            "It starts with a frustration we all know too well. "
            "This is what {name} is here to fix.",
            "Before the demo — the why. This is the problem {name} goes after.",
        ],
        "page": [
            "Let's take a look at {page}. {extra}",
            "Here's {page} in action. {extra}",
            "This is {page}. {extra}",
        ],
        "page_extra": [
            "Notice how the interface stays simple while the features run underneath.",
            "Everything here is live — nothing is mocked.",
            "No setup needed: it just works, right in the browser.",
        ],
        "features": [
            "So what can {name} actually do? Here are the key features we built during the hackathon.",
            "Under the surface, {name} packs a few things worth showing. Here are the highlights.",
            "These are the features that made us proud this weekend.",
        ],
        "stack": [
            "Under the hood, {name} is built with {stack}. Every part was chosen to ship fast and stay reliable.",
            "The tech: {stack}. Boring where it should be, sharp where it counts.",
            "{stack} — chosen so we could spend the weekend on features, not plumbing.",
        ],
        "outro": [
            "That's {name} — built in a weekend, ready to grow. "
            "Thanks for watching, and we'd love to hear your feedback!",
            "And that's {name}. It works, it's useful, and this is just the beginning. "
            "We'd love to hear what you think!",
            "Thanks for watching {name} in action. Try it, break it, tell us — that's what hackathons are for.",
        ],
    },
    "id": {
        "intro": [
            "Halo juri! Ini {name}. {tagline} "
            "Dalam dua menit ke depan kami akan menunjukkan apa yang dilakukan, bagaimana cara kerjanya, dan mengapa ini penting.",
            "Perkenalkan {name}. {tagline} Kami membangunnya untuk memecahkan masalah yang sendiri sering kami alami.",
            "Ini {name} — {tagline} Dua menit lagi, Anda akan tahu kenapa kami menghabiskan akhir pekan untuk ini.",
        ],
        "problem": [
            "Setiap project hackathon berawal dari masalah nyata. "
            "Inilah masalah yang ingin diselesaikan oleh {name}.",
            "Semuanya berawal dari keluhan yang terlalu sering kami dengar. "
            "Inilah yang ingin dibereskan {name}.",
            "Sebelum demo — alasan kenapa ini dibuat. Inilah masalah yang dihadapi {name}.",
        ],
        "page": [
            "Sekarang kita lihat {page}. {extra}",
            "Inilah {page} beraksi. {extra}",
            "Ini tampilan {page}. {extra}",
        ],
        "page_extra": [
            "Perhatikan antarmukanya tetap sederhana meski fiturnya berjalan di belakang layar.",
            "Semua yang Anda lihat live — tidak ada yang dibuat-buat.",
            "Tanpa setup: langsung jalan di browser.",
        ],
        "features": [
            "Jadi, apa saja yang bisa dilakukan {name}? Ini fitur-fitur utama yang kami bangun selama hackathon.",
            "Di balik permukaannya, {name} punya beberapa hal layak dipamerkan. Ini sorotannya.",
            "Inilah fitur yang membuat kami bangga akhir pekan ini.",
        ],
        "stack": [
            "Di balik layar, {name} dibangun dengan {stack}. Semua dipilih agar cepat dirilis dan tetap andal.",
            "Teknologinya: {stack}. Biasa-biasa saja di tempat yang harus biasa, tajam di tempat penting.",
            "{stack} — dipilih supaya akhir pekan kami habis untuk fitur, bukan utak-atik dasar.",
        ],
        "outro": [
            "Itulah {name} — dibangun dalam satu akhir pekan, siap untuk berkembang. "
            "Terima kasih sudah menonton, kami menantikan masukan dari Anda!",
            "Itu dia {name}. Berfungsi, berguna, dan ini baru permulaan. Kami menantikan pendapat Anda!",
            "Terima kasih sudah menonton {name} beraksi. Coba, uji, dan beri tahu kami — memang itu inti hackathon.",
        ],
    },
}

_CONTRACTIONS = [
    ("It is", "It's"), ("it is", "it's"),
    ("We are", "We're"), ("we are", "we're"),
    ("You are", "You're"), ("you are", "you're"),
    ("do not", "don't"), ("Do not", "Don't"),
    ("will not", "won't"), ("cannot", "can't"), ("can not", "can't"),
    ("That is", "That's"), ("that is", "that's"),
    ("Here is", "Here's"), ("here is", "here's"),
    ("what it is", "what it's"), ("it is not", "it isn't"),
]

_BANNED_AI_PHRASES = [
    "delve", "seamless", "seamlessly", "robust", "cutting-edge",
    "revolutionize", "game-changer", "game changer", "in today's fast-paced world",
    "in the ever-evolving", "unlock the power", "harness the power",
    "elevate your", "take it to the next level", "look no further",
    "empower", "streamline your workflow", "at the end of the day",
]


def _pick(rng, variants: list[str]) -> str:
    return variants[rng.randrange(len(variants))]


def _templates(language: str) -> dict[str, list[str]]:
    base = language.split("-")[0].lower()
    return TEMPLATES.get(base, TEMPLATES["en"])


def _clean_tagline(tagline: str) -> str:
    tagline = tagline.strip().strip("*#`")
    return tagline if len(tagline) < 160 else tagline[:157] + "..."



def humanize(text: str) -> str:
    """Light rule-based de-slop: contractions + tightened spacing.
    Deterministic, no AI involved."""
    for a, b in _CONTRACTIONS:
        text = text.replace(a, b)
    return text.replace("  ", " ").strip()


def _rng_for(name: str):
    import random
    import hashlib as _hashlib
    return random.Random(int(_hashlib.md5(name.encode()).hexdigest()[:8], 16))


def generate_draft(project_folder: str, app_url: str, language: str, crawl_limit: int = 4) -> list[dict[str, Any]]:
    """Build the initial scene list: intro card → problem → app pages → features → stack → outro."""
    facts = extract_project(project_folder)
    tpl = _templates(language)
    name = facts["name"]
    tagline = _clean_tagline(facts.get("tagline", "") or "")
    rng = _rng_for(name)
    scenes: list[dict[str, Any]] = []

    scenes.append(
        new_scene(
            title="Intro",
            narration=humanize(_pick(rng, tpl["intro"]).format(name=name, tagline=tagline or "A hackathon project.")),
            visual={"type": "card", "card": {"kind": "title", "heading": name, "bullets": [tagline] if tagline else []}},
        )
    )
    if facts.get("problem"):
        scenes.append(
            new_scene(
                title="The Problem",
                narration=humanize(_pick(rng, tpl["problem"]).format(name=name)),
                visual={"type": "card", "card": {"kind": "bullets", "heading": "The Problem", "bullets": facts["problem"][:3]}},
            )
        )

    # App walkthrough scenes are added by main.py after crawling (needs app_url live).
    # Placeholder markers are returned in meta so the caller knows what to insert.
    if facts.get("features"):
        scenes.append(
            new_scene(
                title="Key Features",
                narration=humanize(_pick(rng, tpl["features"]).format(name=name)),
                visual={"type": "card", "card": {"kind": "bullets", "heading": "Key Features", "bullets": facts["features"][:5]}},
            )
        )
    if facts.get("stack"):
        stack_str = ", ".join(facts["stack"][:5])
        scenes.append(
            new_scene(
                title="Built With",
                narration=humanize(_pick(rng, tpl["stack"]).format(name=name, stack=stack_str)),
                visual={"type": "card", "card": {"kind": "stack", "heading": "Built With", "bullets": facts["stack"][:7]}},
            )
        )
    scenes.append(
        new_scene(
            title="Outro",
            narration=humanize(_pick(rng, tpl["outro"]).format(name=name)),
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
        rng = _rng_for(title)
        extra = _pick(rng, tpl["page_extra"]) if page is pages[0] else ""
        narration = humanize(_pick(rng, tpl["page"]).format(page=title, extra=extra))
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
        "sound human, never corporate: use contractions, vary sentence length, keep one concrete "
        "detail per line; never use these words or phrases: " + ", ".join(_BANNED_AI_PHRASES) + "; "
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
