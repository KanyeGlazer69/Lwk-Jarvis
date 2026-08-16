# Jarvis for Windows

A phased, local-first Windows voice assistant built around:

- local **Hey Jarvis** wake-word detection;
- local microphone transcription;
- Gemini responses using a user-supplied API key protected with Windows DPAPI;
- persistent local memory;
- offline Windows speech output;
- explicit screen vision;
- strictly allowlisted Windows actions; and
- a desktop/tray interface with a compact transcription overlay.

## Safety and privacy

The repository contains source and setup scripts only. It intentionally excludes API keys,
memory databases, transcripts, downloaded models, virtual environments, and machine-specific
runtime data. Screen capture is only used for an explicit visual request. Windows actions use
a fixed allowlist and do not grant arbitrary shell access.

## Installation

Install the numbered phases in order and read each phase's `README-FIRST.txt` before running
its setup script. The setup is designed for a non-administrator PowerShell session and does
not permanently change PowerShell execution policy.

Phase 10 media/browser automation is included as experimental code. Its commands remain
strictly allowlisted, but it should be reviewed and dry-run tested before live use.

## Status

Phases 1–12 are included. Phase 11 launches Jarvis after Windows sign-in and places its
interface on the smallest connected display. Phase 12 adds an optional local Opera GX
extension for YouTube Skip buttons and SponsorBlock sponsor timestamps. Phase 11 uses
a personal Startup shortcut, with duplicate-instance protection. Hardware, microphone names, available Gemini models, and Windows
audio voices can differ across PCs, so validate each phase before continuing.
