@echo off
rem Double-click once to put a "Roblox Piano" icon on the Desktop and Start menu.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0assets\create_shortcut.ps1"
echo.
pause
