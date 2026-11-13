"""Edge TTS engine — free Microsoft neural voices, no API key (default engine)."""
from __future__ import annotations

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
        try:
            pros = prosody or {}
            await edge_tts.Communicate(
                text, voice_id,
                rate=pros.get("rate"), pitch=pros.get("pitch"),
            ).save(out_path)
        except Exception as exc:  # noqa: BLE001
            raise TTSError(f"Edge TTS gagal: {exc}") from exc


register(EdgeEngine())
