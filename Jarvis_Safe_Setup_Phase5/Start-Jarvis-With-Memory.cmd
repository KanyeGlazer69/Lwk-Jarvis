@echo off
title Jarvis Phase 5 - Wake, Hear, Think, and Remember
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%LOCALAPPDATA%\Jarvis\Phase4\Run-Jarvis-Phase4.ps1"
set "JARVIS_EXIT=%ERRORLEVEL%"
echo.
echo Jarvis stopped. Press any key to close.
pause >nul
exit /b %JARVIS_EXIT%
