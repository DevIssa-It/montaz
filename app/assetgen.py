"""AI image generation for scene assets.

Uses the user's own API key (Settings): OpenAI gpt-image-1 preferred,
Gemini image generation as fallback. Output is a PNG saved into the
project's assets folder — after that it's a plain local asset.
"""
from __future__ import annotations

import base64

import httpx


class AssetGenError(RuntimeError):
    """User-facing failure (missing key, provider error)."""


def _has_key(keys: dict[str, str]) -> str | None:
    if keys.get("openai"):
        return "openai"
    if keys.get("gemini"):
        return "gemini"
    return None


def available_engine(keys: dict[str, str]) -> str | None:
    return _has_key(keys)


def _http_error(status: int, body: str) -> AssetGenError:
    if status in (401, 403):
        return AssetGenError("API key ditolak (salah atau kadaluarsa).")
    if status == 429:
        return AssetGenError("Kuota/rate limit habis untuk API key ini.")
    return AssetGenError(f"Provider error (HTTP {status}): {body[:200]}")


async def generate_image(prompt: str, keys: dict[str, str], out_path) -> None:
    engine = _has_key(keys)
    if engine is None:
        raise AssetGenError("Butuh API key OpenAI atau Gemini di Settings untuk generate aset.")
    if not prompt.strip():
        raise AssetGenError("Prompt kosong.")
    if engine == "openai":
        data = await _openai_image(prompt, keys["openai"])
    else:
        data = await _gemini_image(prompt, keys["gemini"])
    with open(out_path, "wb") as fh:
        fh.write(data)


async def _openai_image(prompt: str, key: str) -> bytes:
    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(
            "https://api.openai.com/v1/images/generations",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": "gpt-image-1",
                "prompt": prompt,
                "size": "1536x1024",  # closest landscape to 16:9
                "n": 1,
            },
        )
    if resp.status_code != 200:
        raise _http_error(resp.status_code, resp.text)
    payload = resp.json()["data"][0]
    b64 = payload.get("b64_json")
    if not b64:
        raise AssetGenError("OpenAI tidak mengembalikan gambar.")
    return base64.b64decode(b64)


async def _gemini_image(prompt: str, key: str) -> bytes:
    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-2.0-flash-exp-image-generation:generateContent",
            params={"key": key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
            },
        )
    if resp.status_code != 200:
        raise _http_error(resp.status_code, resp.text)
    try:
        parts = resp.json()["candidates"][0]["content"]["parts"]
        inline = next(p["inlineData"] for p in parts if "inlineData" in p)
    except (KeyError, IndexError, StopIteration, ValueError) as exc:
        raise AssetGenError("Gemini tidak mengembalikan gambar.") from exc
    return base64.b64decode(inline["data"])
