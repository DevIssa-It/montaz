@echo off
REM Open montaz as a desktop-style app window:
REM   1. starts the local server only if it is not already running
REM   2. opens an app window (Edge/Chrome --app, no address bar)
setlocal
cd /d "%~dp0.."

if not exist .venv (
  echo [montaz] No .venv found - run scripts\setup.bat first.
  pause
  exit /b 1
)

netstat -ano | findstr /C:":8000" | findstr /C:"LISTENING" >nul
if errorlevel 1 (
  echo [montaz] Starting server...
  start "montaz server" /min .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
  timeout /t 2 >nul
)

set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if exist "%EDGE%" (
  start "" "%EDGE%" --app=http://localhost:8000
  exit /b 0
)
set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if exist "%CHROME%" (
  start "" "%CHROME%" --app=http://localhost:8000
  exit /b 0
)
start "" http://localhost:8000
endlocal
