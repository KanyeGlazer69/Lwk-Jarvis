JARVIS PHASE 5 - PERSISTENT MEMORY
==================================

Phase 5 keeps a small local SQLite database under:
  %LOCALAPPDATA%\Jarvis\Phase5\memory.db

It archives conversations and extracts only durable facts or preferences that
you explicitly state. It does not store the Gemini API key. Use
Manage-Jarvis-Memory.cmd to view or forget durable memories.

Test across two wake interactions:
1. Say: "Hey Jarvis, remember that my favorite color is blue."
2. After Jarvis answers and resets, say: "Hey Jarvis, what is my favorite color?"
3. Jarvis should answer blue.
