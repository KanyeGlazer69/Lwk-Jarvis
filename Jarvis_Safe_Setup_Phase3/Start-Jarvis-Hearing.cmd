@echo off
title Jarvis Phase 3 - Wake, Record, and Transcribe
"%LOCALAPPDATA%\Jarvis\Phase1\.venv\Scripts\python.exe" "%LOCALAPPDATA%\Jarvis\Phase3\jarvis_hear.py"
set "JARVIS_EXIT=%ERRORLEVEL%"
echo.
echo Jarvis hearing stopped. Press any key to close.
pause >nul
exit /b %JARVIS_EXIT%
