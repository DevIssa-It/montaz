"""OpenAI TTS engine — needs an API key; static voice list, multilingual."""
from __future__ import annotations

import httpx

from .base import TTSEngine, TTSError, Voice, http_error_message, register

API_BASE = "https://api.openai.com/v1"
MODEL_ID = "gpt-4o-mini-tts"
VOICE_IDS = [
    "alloy", "ash", "ballad", "coral", "echo", "fable",
    "onyx", "nova", "sage", "shimmer",
]


class OpenAIEngine(TTSEngine):
    id = "openai"
    label = "OpenAI TTS"
    needs_key = True
    key_name = "openai"

    def _key(self, keys: dict[str, str]) -> str:
        key = keys.get(self.key_name, "")
        if not key:
            raise TTSError("API key OpenAI belum diisi di Settings.")
        return key

    async def voices(self, keys: dict[str, str]) -> list[Voice]:
        # OpenAI TTS voices are a fixed list; no API call needed to enumerate.
        return [Voice(id=v, label=v.capitalize(), language="multi") for v in VOICE_IDS]

    async def test_connection(self, keys: dict[str, str]) -> None:
        key = self._key(keys)
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                f"{API_BASE}/models?limit=1", headers={"Authorization": f"Bearer {key}"}
            )
        if resp.status_code != 200:
            raise TTSError(http_error_message(resp.status_code, resp.text))

    async def synthesize(
        self, text: str, voice_id: str, out_path: str, keys: dict[str, str],
        prosody: dict[str, str] | None = None,  # not used by cloud engines
    ) -> None:
        key = self._key(keys)
        if not text.strip():
            raise TTSError("Teks narasi kosong.")
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{API_BASE}/audio/speech",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": MODEL_ID, "voice": voice_id, "input": text, "response_format": "mp3"},
            )
        if resp.status_code != 200:
            raise TTSError(http_error_message(resp.status_code, resp.text))
        with open(out_path, "wb") as fh:
            fh.write(resp.content)


register(OpenAIEngine())
