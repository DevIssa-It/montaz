"""Studio settings: API keys & defaults, persisted to settings.local.json (gitignored)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_PATH = REPO_ROOT / "settings.local.json"
EXAMPLE_PATH = REPO_ROOT / "settings.example.json"
DATA_DIR = REPO_ROOT / "data"

DEFAULT_SETTINGS: dict[str, Any] = {
    "tts_engine": "edge",
    "language": "en-US",
    "voice": "en-US-AndrewNeural",
    "api_keys": {
        "elevenlabs": "",
        "openai": "",
        "gemini": "",
    },
    # Optional LLM used for script polishing; empty = rule-based only.
    "script_polish_model": "",
}

_KEY_FIELDS = ("api_keys",)


def load_settings() -> dict[str, Any]:
    settings = json.loads(json.dumps(DEFAULT_SETTINGS))  # deep copy
    if SETTINGS_PATH.exists():
        stored = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        for key, value in stored.items():
            if key in settings:
                settings[key] = value
    return settings


def save_settings(updates: dict[str, Any]) -> dict[str, Any]:
    settings = load_settings()
    for key, value in updates.items():
        if key not in DEFAULT_SETTINGS:
            continue
        if key in _KEY_FIELDS and isinstance(value, dict):
            settings[key].update({k: str(v or "") for k, v in value.items() if k in settings[key]})
        else:
            settings[key] = value
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    return settings


def mask_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Settings safe to send to the UI: keys reduced to set/unset flags."""
    masked = json.loads(json.dumps(settings))
    masked["api_keys"] = {k: bool(v) for k, v in settings.get("api_keys", {}).items()}
    return masked


def write_example_settings() -> None:
    if not EXAMPLE_PATH.exists():
        example = json.loads(json.dumps(DEFAULT_SETTINGS))
        example["api_keys"] = {k: "PASTE-YOUR-KEY-HERE" for k in DEFAULT_SETTINGS["api_keys"]}
        EXAMPLE_PATH.write_text(json.dumps(example, indent=2), encoding="utf-8")
