@echo off
title Jarvis Phase 2 - Hey Jarvis Listener
"%LOCALAPPDATA%\Jarvis\Phase1\.venv\Scripts\python.exe" "%LOCALAPPDATA%\Jarvis\Phase2\jarvis_listener.py" --listen
set "JARVIS_EXIT=%ERRORLEVEL%"
echo.
echo Listener stopped. Press any key to close.
pause >nul
exit /b %JARVIS_EXIT%
