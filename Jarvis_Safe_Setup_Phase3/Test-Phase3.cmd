@echo off
title Jarvis Phase 3 - Wake and Transcribe Test
"%LOCALAPPDATA%\Jarvis\Phase1\.venv\Scripts\python.exe" "%LOCALAPPDATA%\Jarvis\Phase3\jarvis_hear.py" --once
set "JARVIS_EXIT=%ERRORLEVEL%"
echo.
echo Press any key to close.
pause >nul
exit /b %JARVIS_EXIT%
