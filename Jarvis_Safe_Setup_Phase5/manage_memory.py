"""Interactive viewer and deletion controls for Jarvis memory."""

from jarvis_memory import MemoryStore


def show(store: MemoryStore) -> None:
    rows = store.list_memories()
    print("\nJARVIS DURABLE MEMORIES")
    print("=" * 70)
    if not rows:
        print("No durable memories stored.")
        return
    for row in rows:
        print(f"[{row['id']}] {row['memory_key']} = {row['memory_value']}")
        print(f"    category={row['category']} importance={row['importance']} updated={row['updated_at']}")


def main() -> None:
    store = MemoryStore()
    try:
        while True:
            show(store)
            print("\nEnter a memory ID to forget it, A to forget ALL durable memories, or Q to quit.")
            choice = input("> ").strip()
            if choice.lower() == "q":
                return
            if choice.lower() == "a":
                if input('Type FORGET ALL to confirm: ').strip() == "FORGET ALL":
                    store.clear_memories()
                    print("All durable memories forgotten.")
                continue
            try:
                memory_id = int(choice)
            except ValueError:
                print("Invalid choice.")
                continue
            print("Memory forgotten." if store.forget(memory_id) else "No memory has that ID.")
    finally:
        store.close()


if __name__ == "__main__":
    main()
