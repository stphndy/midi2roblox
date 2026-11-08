@echo off
rem Starts midi2roblox. Double-click this, or use the desktop shortcut
rem made by "Create Desktop Shortcut.bat".
title midi2roblox
cd /d "%~dp0"

rem Prefer the project's virtual environment, then Python 3.12, then any Python.
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" midi2roblox.py %*
) else (
    where py >nul 2>nul && (
        py -3.12 midi2roblox.py %*
    ) || (
        python midi2roblox.py %*
    )
)

echo.
echo midi2roblox has stopped. Press any key to close this window.
pause >nul
