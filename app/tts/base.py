"""TTS engine registry & shared interface."""
from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any


class TTSError(RuntimeError):
    """Raised with a user-facing message (bad key, quota, network...)."""


@dataclass
class Voice:
    id: str
    label: str
    language: str
    gender: str = ""


class TTSEngine(abc.ABC):
    id: str = ""
    label: str = ""
    needs_key: bool = False
    key_name: str = ""  # settings.api_keys field

    @abc.abstractmethod
    async def voices(self, keys: dict[str, str]) -> list[Voice]:
        """List available voices (may hit the provider API)."""

    @abc.abstractmethod
    async def synthesize(
        self, text: str, voice_id: str, out_path: str, keys: dict[str, str],
        prosody: dict[str, str] | None = None,
    ) -> None:
        """Synthesize narration audio to out_path (.mp3 or .wav).

        prosody may carry engine-specific rate/pitch hints; engines that
        do not support them ignore it."""


    async def test_connection(self, keys: dict[str, str]) -> None:
        """Raise TTSError on failure; default = listing voices."""
        await self.voices(keys)


_ENGINES: dict[str, TTSEngine] = {}


def register(engine: TTSEngine) -> None:
    _ENGINES[engine.id] = engine


def get_engine(engine_id: str) -> TTSEngine:
    engine = _ENGINES.get(engine_id)
    if engine is None:
        raise TTSError(f"Unknown TTS engine: {engine_id}")
    return engine


def list_engines(keys: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {
            "id": e.id,
            "label": e.label,
            "needs_key": e.needs_key,
            "ready": (not e.needs_key) or bool(keys.get(e.key_name, "")),
        }
        for e in _ENGINES.values()
    ]


def http_error_message(status: int, body: str) -> str:
    """Map common HTTP failures to short human messages."""
    if status in (401, 403):
        return "API key ditolak (salah atau kadaluarsa)."
    if status == 429:
        return "Kuota/rate limit habis untuk API key ini."
    if status >= 500:
        return f"Server provider bermasalah (HTTP {status}). Coba lagi nanti."
    return f"HTTP {status}: {body[:200]}"
