"""Google Gemini TTS engine — needs an API key; returns raw PCM which we wrap into WAV."""
from __future__ import annotations

import base64
import json
import struct

import httpx

from .base import TTSEngine, TTSError, Voice, http_error_message, register

API_BASE = "https://generativelanguage.googleapis.com/v1beta"
MODEL_ID = "gemini-2.5-flash-preview-tts"
SAMPLE_RATE = 24000
VOICE_IDS = [
    "Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda", "Orus", "Aoede",
    "Callirrhoe", "Autonoe", "Enceladus", "Iapetus", "Umbriel", "Algieba",
    "Despina", "Erinome", "Algenib", "Rasalgethi", "Laomedeia", "Achernar",
    "Alnilam", "Saphira", "Gacrux", "Pulcherrima",
]


def _pcm_to_wav(pcm: bytes, rate: int = SAMPLE_RATE, channels: int = 1, sample_width: int = 2) -> bytes:
    """Wrap raw signed 16-bit little-endian PCM in a RIFF/WAVE container."""
    data_len = len(pcm)
    header = b"RIFF" + struct.pack("<I", 36 + data_len) + b"WAVE"
    header += b"fmt " + struct.pack("<IHHIIHH", 16, 1, channels, rate,
                                    rate * channels * sample_width, channels * sample_width, 16)
    header += b"data" + struct.pack("<I", data_len)
    return header + pcm


class GeminiEngine(TTSEngine):
    id = "gemini"
    label = "Gemini TTS"
    needs_key = True
    key_name = "gemini"

    def _key(self, keys: dict[str, str]) -> str:
        key = keys.get(self.key_name, "")
        if not key:
            raise TTSError("API key Gemini belum diisi di Settings.")
        return key

    async def voices(self, keys: dict[str, str]) -> list[Voice]:
        # Prebuilt voices are a fixed list; no API call needed to enumerate.
        return [Voice(id=v, label=v, language="multi") for v in VOICE_IDS]

    async def test_connection(self, keys: dict[str, str]) -> None:
        key = self._key(keys)
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(f"{API_BASE}/models?key={key}&pageSize=1")
        if resp.status_code != 200:
            raise TTSError(http_error_message(resp.status_code, resp.text))

    async def synthesize(self, text: str, voice_id: str, out_path: str, keys: dict[str, str]) -> None:
        key = self._key(keys)
        if not text.strip():
            raise TTSError("Teks narasi kosong.")
        payload = {
            "contents": [{"parts": [{"text": f"Narrate this naturally: {text}"}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice_id}}},
            },
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{API_BASE}/models/{MODEL_ID}:generateContent?key={key}", json=payload
            )
        if resp.status_code != 200:
            raise TTSError(http_error_message(resp.status_code, resp.text))
        try:
            inline = resp.json()["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
            mime = resp.json()["candidates"][0]["content"]["parts"][0]["inlineData"].get("mimeType", "")
        except (KeyError, IndexError, ValueError) as exc:
            raise TTSError(f"Respons Gemini tidak berisi audio: {resp.text[:200]}") from exc
        pcm = base64.b64decode(inline)
        audio = _pcm_to_wav(pcm) if "wav" not in mime else pcm
        with open(out_path, "wb") as fh:
            fh.write(audio)


register(GeminiEngine())
