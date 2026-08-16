JARVIS PHASE 6 - SPOKEN RESPONSES
=================================

Phase 6 uses the offline Microsoft David Desktop voice already included with
Windows. No response text is sent to a separate voice service.

Settings are in %LOCALAPPDATA%\Jarvis\Phase6\config.json:
- enabled: true/false
- voice: Microsoft David Desktop or Microsoft Zira Desktop
- rate: -10 to 10
- volume: 0 to 100

The microphone remains active while Gemini thinks and Jarvis speaks because this
setup uses earbuds. Post-interaction queue/model resets still discard stale audio.
