@echo off
title Jarvis Phase 2 - Live Wake Test
"%LOCALAPPDATA%\Jarvis\Phase1\.venv\Scripts\python.exe" "%LOCALAPPDATA%\Jarvis\Phase2\jarvis_listener.py" --test-seconds 60
set "JARVIS_EXIT=%ERRORLEVEL%"
echo.
echo Press any key to close.
pause >nul
exit /b %JARVIS_EXIT%
