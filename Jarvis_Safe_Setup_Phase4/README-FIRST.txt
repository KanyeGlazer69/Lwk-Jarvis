JARVIS PHASE 4 - AI BRAIN
==========================

Phase 4 sends only the transcribed text to Google's Gemini API and prints the
answer. Microphone audio remains local. Persistent memory and spoken replies are
not part of this phase.

Jarvis discovers the current Gemini Flash models available to your key and picks
the newest compatible option. Free-tier content may be used by Google to improve
its products; consult Google's current pricing and privacy information.

SETUP
1. Create a free API key at https://aistudio.google.com/app/apikey
2. Do not paste the key into chat or screenshots.
3. Run %LOCALAPPDATA%\Jarvis\Phase4\Configure-Gemini-Key.ps1 in PowerShell.
4. Paste the key into its hidden prompt. Windows DPAPI encrypts it for your user.
5. Double-click Test-Phase4.cmd and ask one question after saying Hey Jarvis.

For continuous use after the test, double-click Start-Jarvis-Thinking.cmd.
