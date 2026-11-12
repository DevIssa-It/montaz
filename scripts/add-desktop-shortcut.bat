@echo off
REM Creates a "montaz" desktop shortcut that opens the app window
REM (via scripts\open-app.bat). Safe to re-run.
setlocal
cd /d "%~dp0.."

if not exist web\public\favicon.ico (
  echo [montaz] icon missing - generating...
  .venv\Scripts\python.exe scripts\generate_icons.py
)

powershell -NoProfile -Command "try { $ws = New-Object -ComObject WScript.Shell; $desktop = [Environment]::GetFolderPath('Desktop'); $root = (Get-Location).Path; $s = $ws.CreateShortcut((Join-Path $desktop 'montaz.lnk')); $s.TargetPath = (Join-Path $root 'scripts\open-app.bat'); $s.WorkingDirectory = (Join-Path $root 'scripts'); $s.IconLocation = (Join-Path $root 'web\public\favicon.ico'); $s.Description = 'montaz - many cuts, one story'; $s.Save(); Write-Output ('[montaz] Desktop shortcut created: ' + (Join-Path $desktop 'montaz.lnk')) } catch { Write-Output ('[montaz] Shortcut creation failed: ' + $_.Exception.Message); exit 1 }"
endlocal
