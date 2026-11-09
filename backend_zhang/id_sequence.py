"""Item ID allocator (items_meta.json). Added in v1.3.

Section 10 of the requirements requires item IDs to be unique positive
integers. The original implementation used "max existing ID + 1", which reuses
a freed ID after the last record is permanently deleted - old item_ids stored
in favorites/messages/intents would then point to a brand-new item, a subtle
data corruption.

This module solves it with a standalone counter:

- ``items_meta.json`` stores ``{"next_item_id": N}`` and atomically writes back
  ``N + 1`` after each allocation;
- the lower bound is ``max(counter, max existing ID + 1, max archived item_id + 1)``,
  so even if the counter file is lost or shrunk it will not collide with
  existing or deleted item IDs;
- treated the same as items.json: atomic write + file lock + never overwrite a
  corrupt file;
- if item publishing fails after allocation, the number is skipped (a gap);
  that is the normal cost of "unique and monotonic".

This module is internal to backend_zhang; other modules must not call it.
"""

from __future__ import annotations

from typing import Any

from backend_zhang import config
from backend_zhang.exceptions import DataFileError
from backend_zhang.json_store import JsonObjectStore


class ItemIdSequence:
    """Item ID counter (monotonically increasing)."""

    def __init__(self, data_file: str | None = None):
        self.store = JsonObjectStore(data_file or config.DEFAULT_ITEMS_META_FILE)

    @property
    def data_file(self) -> str:
        return self.store.path

    # ---------- Internal ----------
    @staticmethod
    def _as_int(value: Any, default: int = 1) -> int:
        """Coerce any dirty data into a positive int (keeps allocating even if
        the counter is hand-edited into garbage)."""
        try:
            number = int(value)
        except (TypeError, ValueError):
            return default
        return number if number >= 1 else default

    def peek(self) -> int:
        """Peek the next ID that would be allocated (without consuming it)."""
        meta = self.store.load()
        return self._as_int(meta.get("next_item_id"))

    # ---------- Allocation ----------
    def allocate(self, floor: int = 1) -> int:
        """Allocate an ID inside the lock and persist the counter, returning the
        assigned ID.

        ``floor``: the minimum usable ID guaranteed by the caller
        (max existing ID + 1, max archived ID + 1).
        """
        base = self._as_int(floor)

        def mutator(meta: dict) -> int:
            current = self._as_int(meta.get("next_item_id"))
            candidate = max(current, base)
            meta["next_item_id"] = candidate + 1
            return candidate

        return self.store.transaction(mutator)

    def reset(self, next_item_id: int = 1) -> None:
        """Reset the counter (for demo/test cleanup only; never call it in production)."""
        value = self._as_int(next_item_id)
        if value < 1:
            raise DataFileError("next_item_id must be a positive integer")
        self.store.save({"next_item_id": value})
