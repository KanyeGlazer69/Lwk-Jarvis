JARVIS PHASE 3 - UNDERSTAND WHAT YOU SAY
=========================================

Phase 3 adds local speech recording, natural silence detection, and high-accuracy
English speech-to-text using distil-large-v3. Microphone audio is processed locally
and is not uploaded.

Live test:
1. Double-click %LOCALAPPDATA%\Jarvis\Phase3\Test-Phase3.cmd
2. Say "Hey Jarvis"
3. Wait for the beep, then say a sentence naturally
4. Stop talking; recording ends automatically after the configured silence interval
5. Confirm the window prints the correct transcript and PHASE 3 LIVE TEST PASSED

The latest transcript is stored at:
  %LOCALAPPDATA%\Jarvis\Phase3\last-transcript.txt

This phase does not connect to an AI service and does not start with Windows.
