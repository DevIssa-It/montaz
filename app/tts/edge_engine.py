"""Edge TTS engine — free Microsoft neural voices, no API key (default engine)."""
from __future__ import annotations

import asyncio

import edge_tts

from .base import TTSEngine, TTSError, Voice, register

_VOICES_CACHE: list[Voice] | None = None


class EdgeEngine(TTSEngine):
    id = "edge"
    label = "Edge TTS (free)"
    needs_key = False
    key_name = ""

    async def voices(self, keys: dict[str, str]) -> list[Voice]:
        global _VOICES_CACHE
        if _VOICES_CACHE is None:
            try:
                raw = await edge_tts.list_voices()
            except Exception as exc:  # noqa: BLE001 - surface a clean message
                raise TTSError(f"Gagal mengambil daftar voice Edge TTS: {exc}") from exc
            _VOICES_CACHE = [
                Voice(
                    id=v["ShortName"],
                    label=f"{v['ShortName']} ({v.get('Gender', '')})",
                    language=v["Locale"],
                    gender=v.get("Gender", ""),
                )
                for v in raw
            ]
        return _VOICES_CACHE

    async def synthesize(
        self, text: str, voice_id: str, out_path: str, keys: dict[str, str],
        prosody: dict[str, str] | None = None,
    ) -> None:
        if not text.strip():
            raise TTSError("Teks narasi kosong.")
        pros = prosody or {}
        kwargs = {k: v for k, v in (("rate", pros.get("rate")), ("pitch", pros.get("pitch"))) if v}
        # Microsoft's endpoint flakes occasionally; retry with backoff instead
        # of failing the whole render.
        last_exc: Exception | None = None
        for attempt, delay in enumerate((0, 1.5, 4.0, 8.0, 12.0), start=1):
            if delay:
                await asyncio.sleep(delay)
            try:
                await edge_tts.Communicate(text, voice_id, **kwargs).save(out_path)
                return
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
        raise TTSError(f"Edge TTS gagal setelah {attempt}x percobaan: {last_exc}") from last_exc


register(EdgeEngine())
