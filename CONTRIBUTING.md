# Contributing

Thanks for helping improve montaz. A few conventions keep the codebase consistent:

## Package management
- **pnpm only** for anything Node-related (`pnpm install`, `pnpm dlx shadcn@latest add ...`, `pnpm build`). Do not use npm/npx — the project has standardized on pnpm for disk efficiency.
- Frontend components come from the shadcn CLI; only compose custom components (scene list, action editor) from shadcn primitives.

## Design rules
- Follow the project's design DNA: matte dark surfaces, small radii, hairline borders, `font-mono tabular-nums` for any duration/timecode. No purple gradients, no glassmorphism, no oversized rounded corners.
- Every interactive element must handle loading, empty, error, and success states.

## Backend
- Python 3.11+, stdlib typing style (`from __future__ import annotations`), no speculative abstractions.
- Errors that users can act on raise `TTSError` (TTS layer) or `RuntimeError` with an Indonesian user-facing message in the render pipeline.

## Before opening a PR
0. By opening a PR you agree to [CLA.md](CLA.md) (license-grant to the project).
1. `pnpm build` in `web/` must pass (TypeScript strict).
2. `.venv/Scripts/python.exe -m pytest tests/` (or `.venv/bin/python` on Unix) must be green.
3. Run the appropriate setup script in a clean folder to sanity-check the install flow if you touched dependencies.
