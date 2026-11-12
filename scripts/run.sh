#!/usr/bin/env bash
# Start the studio (localhost only) and open it in your browser.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
  echo "[run] No .venv found - run scripts/setup.sh first."
  exit 1
fi

( sleep 1;
  if command -v xdg-open >/dev/null 2>&1; then xdg-open http://localhost:8000;
  elif command -v open >/dev/null 2>&1; then open http://localhost:8000;
  fi ) &

.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
