@echo off
REM One-time setup for Foley (Windows).
REM Requires Python 3.11+ on PATH. FFmpeg is optional (a bundled binary is used as fallback).
setlocal
cd /d "%~dp0.."

where python >nul 2>nul
if errorlevel 1 (
  echo [setup] Python was not found on PATH. Install it from https://python.org first.
  exit /b 1
)

if not exist .venv (
  echo [setup] Creating virtual environment...
  python -m venv .venv || exit /b 1
)

echo [setup] Installing Python dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip || exit /b 1
.venv\Scripts\python.exe -m pip install -r requirements.txt || exit /b 1

echo [setup] Installing headless Chromium for auto-capture (~130 MB, one time)...
.venv\Scripts\python.exe -m playwright install chromium

echo.
echo [setup] Done. Run scripts\run.bat to start the studio at http://localhost:8000
endlocal
