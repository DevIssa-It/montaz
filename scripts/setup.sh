#!/usr/bin/env bash
# One-time setup for Demo Video Studio (macOS/Linux).
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"
command -v "$PYTHON" >/dev/null 2>&1 || { echo "[setup] $PYTHON not found. Install Python 3.11+ first."; exit 1; }

if [ ! -d .venv ]; then
  echo "[setup] Creating virtual environment..."
  "$PYTHON" -m venv .venv
fi

echo "[setup] Installing Python dependencies..."
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

echo "[setup] Installing headless Chromium for auto-capture (~130 MB, one time)..."
.venv/bin/python -m playwright install chromium

echo ""
echo "[setup] Done. Run scripts/run.sh to start the studio at http://localhost:8000"
