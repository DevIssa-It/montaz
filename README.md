# <img src="web/public/favicon.svg" align="top" width="28" alt=""> Foley

**Sound on.** Create a hackathon demo video (Devpost style: screen capture + voice-over, no face, no manual editing) **automatically** — from your own project folder and running web app.

Foley is the film-craft of giving silent footage its sound — and that is exactly what this tool does: you point it at your project; it writes the narration script, captures your app with a headless browser, synthesizes a natural voice-over, and assembles a final MP4. You only review and tweak.

## How it works

```
project folder + running app URL
        │
        ▼
 1. Script generator ── reads README, stack files, routes, and crawls your app's pages
 2. TTS engine ──────── Edge TTS by default (free, 40+ languages, no key needed)
 3. Auto-capture ────── Playwright records each scene from your running app (1280×720)
 4. Renderer ────────── FFmpeg assembles cards, captures, and audio into final.mp4
```

Scenes are editable before rendering: narration text, capture steps (`goto`, `click`, `fill`, `scroll`, `wait`, `record`), terminal demo commands, title/bullet cards.

## Quickstart (Windows / macOS / Linux)

Requires **Python 3.11+**. Node/pnpm is only needed if you want to modify the UI — a prebuilt frontend is included.

```bash
git clone https://github.com/<you>/demo-video-studio
cd demo-video-studio
scripts/setup.bat   # or: scripts/setup.sh
scripts/run.bat     # or: scripts/run.sh
```

The studio opens at `http://localhost:8000` (bound to `127.0.0.1` only).

### Making a video

1. **Projects** — enter your project folder (local path) and the URL where your web app is running (e.g. `http://localhost:3000`), then **Generate script**.
2. **Studio** — review scenes; edit narration, capture steps, or visuals; press **Synthesize & play** to hear any scene.
3. **Render** — one click. Watch the progress log, then download `final.mp4`.

## TTS engines

| Engine | Needs API key | Notes |
|---|---|---|
| Edge TTS (default) | No | Microsoft neural voices, 40+ languages incl. Indonesian (`id-ID`) |
| ElevenLabs | Yes | Most natural intonation; free tier ≈ 10 min audio/month |
| OpenAI TTS | Yes | `gpt-4o-mini-tts` voices |
| Gemini TTS | Yes | `gemini-2.5-flash-preview-tts` voices |

Optional **AI script polish** uses your OpenAI or Gemini key to rewrite narrations. Without any key everything still works — the rule-based generator is the default.

## Security model (local, single-user)

- The server binds `127.0.0.1` only and ships **no CORS** — other websites in your browser cannot call the API.
- API keys live in `settings.local.json` (gitignored) and are **never** sent back to the UI — only a set/unset flag.
- Asset paths are resolved strictly inside the project's own directory (path traversal is rejected).
- Terminal scenes run shell commands from your own `project.json` on your own machine; the API never accepts raw commands over the network.

## Development

```bash
# backend
.venv/Scripts/python.exe -m pytest tests/        # Windows
.venv/bin/python -m pytest tests/                # macOS/Linux

# frontend (pnpm; the project does not use npm)
cd web && pnpm install && pnpm dlx shadcn@latest add <component>
pnpm build   # emits web/dist/, which the server serves
```

See `TASK.md` for the current architecture snapshot and `CONTRIBUTING.md` for conventions.

## Known limits

- Auto-capture targets **web apps** (mobile capture and richer walkthrough AI are on the v2 list).
- FFmpeg system binary is used when present; otherwise the bundled `imageio-ffmpeg` binary is used automatically.
- The headless Chromium download is ~130 MB, one time per machine.

## License

MIT — see [LICENSE](LICENSE).
