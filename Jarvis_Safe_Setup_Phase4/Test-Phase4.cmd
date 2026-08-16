@echo off
title Jarvis Phase 4 - AI Response Test
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%LOCALAPPDATA%\Jarvis\Phase4\Run-Jarvis-Phase4.ps1" -Once
set "JARVIS_EXIT=%ERRORLEVEL%"
echo.
echo Press any key to close.
pause >nul
exit /b %JARVIS_EXIT%
