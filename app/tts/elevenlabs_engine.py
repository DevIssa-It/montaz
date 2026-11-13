"""ElevenLabs engine — most natural voices; needs an API key (free tier available)."""
from __future__ import annotations

import httpx

from .base import TTSEngine, TTSError, Voice, http_error_message, register

API_BASE = "https://api.elevenlabs.io/v1"
MODEL_ID = "eleven_multilingual_v2"  # best quality, 29+ languages


class ElevenLabsEngine(TTSEngine):
    id = "elevenlabs"
    label = "ElevenLabs"
    needs_key = True
    key_name = "elevenlabs"

    def _key(self, keys: dict[str, str]) -> str:
        key = keys.get(self.key_name, "")
        if not key:
            raise TTSError("API key ElevenLabs belum diisi di Settings.")
        return key

    async def voices(self, keys: dict[str, str]) -> list[Voice]:
        key = self._key(keys)
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(f"{API_BASE}/voices", headers={"xi-api-key": key})
        if resp.status_code != 200:
            raise TTSError(http_error_message(resp.status_code, resp.text))
        voices = []
        for v in resp.json().get("voices", []):
            labels = v.get("labels", {}) or {}
            voices.append(
                Voice(
                    id=v["voice_id"],
                    label=v.get("name", v["voice_id"]),
                    language=labels.get("language") or labels.get("accent") or "multi",
                    gender=labels.get("gender", ""),
                )
            )
        return voices

    async def synthesize(
        self, text: str, voice_id: str, out_path: str, keys: dict[str, str],
        prosody: dict[str, str] | None = None,  # not used by cloud engines
    ) -> None:
        key = self._key(keys)
        if not text.strip():
            raise TTSError("Teks narasi kosong.")
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{API_BASE}/text-to-speech/{voice_id}",
                headers={"xi-api-key": key, "Accept": "audio/mpeg"},
                json={"text": text, "model_id": MODEL_ID},
            )
        if resp.status_code != 200:
            raise TTSError(http_error_message(resp.status_code, resp.text))
        with open(out_path, "wb") as fh:
            fh.write(resp.content)


register(ElevenLabsEngine())
