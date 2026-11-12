# TASK.md — Montage (dulu: Demo Video Studio)

## 1. Active Objective
App open source untuk membuat **video demo hackathon otomatis end-to-end** (format Devpost: capture layar + narasi TTS, tanpa wajah, tanpa editing manual). User menunjuk folder project + URL web app yang sedang jalan → app menulis naskah (rule-based, AI opsional), meng-capture demo via Playwright, menarasikan via TTS, merakit MP4 via FFmpeg. **V1 SELESAI & TERVERIFIKASI E2E.**
**Nama FINAL: montaz** (keputusan user 2026-11-12, kata milik user sendiri). Riwayat lengkap (~18 kandidat): Demo Video Studio → Montage (bentrok montage.app) → Oner/Zinger/Oomph/Kicker/Bake (aneh/ambigu) → Rushes (kesan buru-buru) → Foley (mismatch teknis: foley=SFX bukan narration + foley.io + user tak nyaman nama facet suara) → Vertov (nama orang, user tak kenal & tak mau risiko) → Voiceframe (menekan facet voice, tertangkap user) → **montaz** ✓. Verifikasi montaz: npm 404 ✓, PyPI 404 ✓, GitHub 406 repo semuanya komunitas Rusia "монтаж" tanpa produk video aktif ✓. Tagline: "many cuts, one story." Wordmark SELALU lowercase (mitigasi typo-feel; ejaan adalah brand). Caveat yang disadari user: trademark satu-huruf lemah — acceptable untuk OSS gratis, tinjau ulang jika komersial besar. Logo: BrandMark = dua layer bracket intercut + klip emerald tengah (many cuts → one story) di web/src/components/BrandMark.tsx + favicon.svg; splash sekali per sesi (sessionStorage `montaz.booted`). Tanpa watermark di video user. Saat push GitHub: repo `montaz`.

## 2. Current Architecture & Configurations
- **Stack**: FastAPI (Python 3.14, venv `.venv/`) + React 19 + Vite 8 + TS 7 + Tailwind v4 + shadcn Base UI (style `base-mira`, build → `web/dist/` DI-COMMIT, diserve FastAPI) + Playwright Chromium + FFmpeg (system, fallback `imageio-ffmpeg` — tidak ada ffprobe, durasi via parsing stderr).
- **Package manager JS: pnpm WAJIB (npm DILARANG user — memory `no-npm-use-pnpm`).**
- **Desain**: Archetype B DESIGN.md — `#090A0F`/`#12141A`/border `rgba(255,255,255,0.08)`/teks `#EDEDED`/accent emerald/radius 8px. shadcn via CLI (`pnpm dlx shadcn@latest ...`).
- **Backend**: `app/main.py` (routes; SEMUA route /api WAJIB di atas mount static), `settings.py`, `project_store.py` (+ `resolve_asset_path` anti-traversal), `tts/` (registry + edge/elevenlabs/openai/gemini), `scriptgen/` (extractor/crawler/generator), `capture/` (browser sync_playwright 1280×720, terminal), `render/` (cards PIL, ffmpeg xfade 0.4s, pipeline job thread).
- **Data**: `data/<id>/project.json` — scenes[] visual type: card|browser|terminal|image|video.
- **Keamanan**: bind 127.0.0.1 saja, TANPA CORS (same-origin), API key tak pernah dikirim ke UI (boolean), path traversal diblok, command terminal hanya dari project.json user sendiri.
- **Frontend**: `web/src/` — App.tsx (SSOT: projects + activeProject), pages/{Projects,Studio,Render,Settings}Page.tsx, lib/api.ts, types.ts. TS strict (`noUnusedLocals`, `verbatimModuleSyntax`, TS7 tanpa baseUrl).
- **Git**: repo ter-init, 2 commit (`bedbf96` initial, `9cc3060` fix E2E). Identitas: Qiforiss67.

## 3. Completed Work & Verified Items
- [x] Bootstrap env lengkap (venv, deps, Chromium, edge-tts online, ffmpeg 9.0.2 bundled).
- [x] Backend penuh + keamanan (audit SoC/SSOT/security diterapkan).
- [x] Frontend 4 layar, build hijau (TS strict), dist ter-commit.
- [x] **pytest 17/17 hijau** + **harness `test-project` hijau** (jalankan via venv python: `demo-video-studio/.venv/Scripts/python.exe C:/Users/ahmad/agent_eval_harness.py test-project demo-video-studio`).
- [x] **E2E penuh lulus**: dummy app (e2e-dummy-app/, port 8077) → project `kostfinder-e2e-1794444859` → scriptgen 7 scene (2 browser capture hasil crawl) → render → **final.mp4 48.7s, 1920×1080 h264+aac, 2.6 MB**.
- [x] UI terverifikasi visual via browser (Settings/Projects/Studio/Render) — Archetype B lolos checklist: tanpa purple/balon/glassmorphism, border rapi, mono timecode, 4-state (empty Studio, skeleton, toast error, done).
- [x] Bug hasil E2E sudah diperbaiki & di-commit (health route order, pad sintaks, parser tagline).

## 4. Immediate Next Actions (kandidat lanjutan)
1. Push ke GitHub (`git remote add origin ...` + push) bila user mau publikasi.
2. Tombol "Polish dengan AI" sudah ada di backend (`polish: true`) — belum ada tombol UI terpisah (scriptgen UI selalu polish=false); tambahkan toggle di ProjectsPage bila diinginkan.
3. BGM: backend siap (`bgm.enabled/path/volume` + `mix_bgm`), UI belum menyediakan upload file BGM — path diisi manual via project.json.
4. v2 (di luar scope): mobile capture (ADB), auto-launch project dari folder, .exe PyInstaller, BGM library.

## Catatan eksekusi (Windows/git-bash)
- Path CLI native: `C:/...` forward slash. venv: `.venv/Scripts/python.exe`.
- Jalankan studio: `scripts/run.bat` (atau uvicorn manual). Dummy E2E: `python -m http.server 8077` di `../e2e-dummy-app`.
- Server E2E masih berjalan di background sesi ini (port 8000 studio, 8077 dummy app).
- Model: Flash cukup untuk seluruh build; tak perlu top-up (terbukti selesai tanpa kuota habis).
