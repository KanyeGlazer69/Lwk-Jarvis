JARVIS SAFE SETUP - PHASE 1 v3
================================

READ THIS BEFORE RUNNING THE INSTALLER.

WHAT THIS INSTALLS
------------------
- The official Python Install Manager from the Microsoft Store, if needed
- Python 3.12 for your Windows user account
- An isolated virtual environment at:
  %LOCALAPPDATA%\Jarvis\Phase1\.venv
- openWakeWord and sounddevice inside that environment
- A short microphone diagnostic that records one second only in memory;
  the audio is not saved

SAFETY LIMITS
-------------
This setup:
- does NOT request administrator access
- does NOT change the firewall
- does NOT change the registry
- does NOT change Windows security policy
- does NOT permanently change PowerShell ExecutionPolicy
- uses pip --no-cache-dir to reduce storage usage
- reports free storage before and after setup
- stops immediately when an external command fails

HOW TO RUN IT
-------------
1. Extract the ZIP completely. Do not run the script from inside the ZIP.
2. Open the extracted Jarvis_Safe_Setup_Phase1_v3 folder.
3. Click the File Explorer address bar, type powershell, and press Enter.
   This opens a PowerShell window in the correct folder and keeps it visible.
4. Paste this command and press Enter:

   powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\Setup-Jarvis-Phase1-v3.ps1"

The Bypass setting applies only to that one PowerShell process. It does not
permanently loosen your PowerShell settings.

Do not run PowerShell as Administrator. If the installer detects an elevated
window, it stops without installing anything.

SUCCESS
-------
The final line should say:

PHASE 1 COMPLETE - DIAGNOSTIC PASSED

IF IT STOPS
-----------
Leave the manually opened PowerShell window open. Take a screenshot showing
SETUP STOPPED and the message immediately below it. Do not make random security,
registry, firewall, or ExecutionPolicy changes.

The Microsoft Store source and package agreements are accepted only as needed
for the official Python Install Manager installation.
