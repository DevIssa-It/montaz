# TASK.md — Hackathon Demo Video Studio

## 1. Active Objective
App open source untuk membuat **video demo hackathon otomatis end-to-end** (format Devpost: capture layar + narasi TTS, tanpa wajah, tanpa editing manual). User menunjuk folder project + URL web app yang sedang jalan → app menulis naskah (rule-based, AI opsional), meng-capture demo via Playwright, menarasikan via TTS, merakit MP4 via FFmpeg.

**Dijalankan pakai GLM-5.3-Flash (plan gratis) tanpa top-up — jangan ganti model tanpa diminta.**

## 2. Current Architecture & Configurations
- **Stack**: FastAPI (Python 3.14, venv `.venv/`) + React+Vite+TS+Tailwind+shadcn/ui (frontend, build → `web/dist/` diserve FastAPI) + Playwright Chromium + FFmpeg (system, fallback `imageio-ffmpeg` binary — TIDAK ada ffprobe, durasi via parsing stderr `ffmpeg -i`).
- **Package manager JS: pnpm WAJIB (npm DILARANG user — lihat memory `no-npm-use-pnpm`).**
- **Desain**: DESIGN.md Archetype B — bg `#090A0F`, card `#12141A`, border `rgba(255,255,255,0.08)`, teks `#EDEDED`, accent emerald, radius 6–8px, DILARANG purple gradient / glassmorphism / rounded-2xl. shadcn via CLI (`pnpm dlx shadcn@latest ...`), komponen TIDAK dibuat manual.
- **Struktur backend**: `app/settings.py` (settings.local.json, keys gitignored), `app/project_store.py` (data/<id>/project.json + assets/audio/output), `app/tts/` (base registry + edge/elevenlabs/openai/gemini engines), `app/scriptgen/` (extractor README+stack+routes regex, crawler BFS same-origin max 6 halaman, generator template en/id + polish OpenAI/Gemini opsional), `app/capture/` (browser.py sync_playwright → webm 1280x720; terminal.py jalankan command asli), `app/render/` (cards.py PIL 1920x1080; ffmpeg.py xfade 0.4s fallback hardcut; pipeline.py job background), `app/main.py` (routes: /api/settings, /api/tts/engines|voices, /api/projects CRUD, /scriptgen, /audio preview, /assets upload, /render + /render/status, mount /api/data + web/dist).
- **Data project**: `data/<project_id>/project.json` — scenes[]: id, title, narration, visual {type: card|browser|terminal|image|video, ...aksi/asset}, audio (rel path). TTS per scene disynth dulu → durasi scene = durasi audio + pad 0.6s.
- **Environment terverifikasi**: Python 3.14 venv OK; deps terpasang (requirements.txt); edge-tts synth OK (uji 17KB mp3); Chromium Playwright terinstall; ffmpeg 9.0.2 via imageio-ffmpeg; pnpm 10.27.0 + corepack; Node 22.
- **Tanpa API key apa pun app jalan penuh** (Edge TTS + rule-based naskah). Key hanya upgrade (ElevenLabs/OpenAI/Gemini TTS, polish LLM).

## 3. Completed Work & Verified Items
- [x] Bootstrap env lengkap (semua di atas terverifikasi via terminal).
- [x] Backend semua modul ditulis: settings, project_store, 4 TTS engines, scriptgen (extractor/crawler/generator), capture (browser/terminal), render (cards/ffmpeg/pipeline), main.py dengan semua routes.
- [x] main.py dibersihkan (asyncio unused dihapus, param force dihapus).

## 4. Immediate Next Actions
1. Buat `__init__.py` untuk app/, app/tts/, app/scriptgen/, app/capture/, app/render/, tests/.
2. Scaffold frontend: `pnpm create vite web --template react-ts` → tailwindcss → `pnpm dlx shadcn@latest init` → `add button card select dialog tabs progress slider input textarea label badge separator tooltip sonner skeleton alert scroll-area switch` → tema Archetype B di index.css (CSS vars shadcn di-override).
3. Implementasi 4 layar (src/App.tsx + src/pages/* + src/lib/api.ts): Settings (engine→voices kaskade, kolom key + test-connection), Project (folder+URL+Generate), Studio 3-panel ala Descript (scene list | preview 16:9 | inspector + preview audio <audio src=/api/data/...>), Render (POST /render + poll status + <video> final).
4. Tests pytest: extractor (fixture mini), generator, cards render, ffmpeg smoke 2 kartu ±2s assert durasi; jalankan `pytest` + `python C:/Users/ahmad/agent_eval_harness.py test-project demo-video-studio` (path Windows forward slash!).
5. Packaging: scripts/setup.bat|.sh, run.bat|.sh, README EN, LICENSE MIT, CONTRIBUTING, .gitignore (settings.local.json, data/, .venv, node_modules), git init + commit.
6. E2E: dummy web app 2 route (python http.server atau serve via uvicorn kecil) → buat project via API → scriptgen → render → cek output/final.mp4 (durasi ffprobe) → cek UI via browser-use skill (screenshot, checklist DESIGN.md §5).

## Catatan eksekusi penting (Windows/git-bash)
- Path CLI native Windows: `C:/...` forward slash, BUKAN `/c/...`.
- venv python: `.venv/Scripts/python.exe`.
- Plan user: Flash cukup; kalau bug sulit 2-3 iterasi gagal → delegasikan potongan itu ke model penuh sebagai subagent transien (konvensi §4 AGENTS.md).
