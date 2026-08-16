"""Self-test the memory database against a disposable temporary database."""

import pathlib
import tempfile

from jarvis_memory import MemoryStore


with tempfile.TemporaryDirectory() as directory:
    store = MemoryStore(pathlib.Path(directory) / "test.db")
    exchange_id = store.record_exchange("Remember my test color is blue.", "Okay.")
    stored = store.upsert_memories(
        [{"key": "test color", "value": "blue", "category": "test", "importance": 3}],
        exchange_id,
    )
    assert stored == 1
    assert "test color: blue" in store.context()
    row = store.list_memories()[0]
    assert store.forget(int(row["id"]))
    assert not store.list_memories()
    store.close()
print("MEMORY CREATE / RECALL / FORGET SELF-TEST PASSED")
