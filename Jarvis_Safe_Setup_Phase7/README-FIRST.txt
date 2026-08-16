JARVIS PHASE 7 - EXPLICIT SCREEN VISION
========================================

Jarvis captures a screen only for explicit phrases such as:
- "Look at my screen"
- "Describe my wallpaper"
- "Look at monitor two"
- "What do you see on all monitors?"

The screenshot is held in memory, sent to Gemini with that request, and not saved
to disk. Ordinary requests never trigger capture. Anything visible—including
notifications or private content—may appear in the image sent to Gemini.
