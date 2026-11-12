@echo off
REM Start the studio (localhost only) and open it in your browser.
setlocal
cd /d "%~dp0.."

if not exist .venv (
  echo [run] No .venv found - run scripts\setup.bat first.
  exit /b 1
)

start "" http://localhost:8000
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
endlocal
