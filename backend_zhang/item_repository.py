"""Item data access layer (items.json is maintained only by this package; other
modules must not open it directly).

Only reads/writes data; status transitions, permission checks, search and sort
all live in item_service.
"""

from __future__ import annotations

from backend_zhang import config
from backend_zhang.exceptions import ConflictError
from backend_zhang.json_store import JsonArrayStore


class ItemRepository:
    def __init__(self, data_file: str | None = None):
        self.store = JsonArrayStore(data_file or config.DEFAULT_ITEMS_FILE)

    @property
    def data_file(self) -> str:
        return self.store.path

    # ---------- Internal read/write ----------
    def _load_items(self) -> list[dict]:
        return self.store.load()

    def _save_items(self, items: list[dict]) -> None:
        self.store.save(items)

    # ---------- Query ----------
    def list_items(self) -> list[dict]:
        return [dict(item) for item in self._load_items()]

    def find_by_id(self, item_id: int) -> dict | None:
        for item in self._load_items():
            if item.get("id") == item_id:
                return dict(item)
        return None

    def list_by_seller(self, seller_id: int) -> list[dict]:
        return [dict(item) for item in self._load_items() if item.get("seller_id") == seller_id]

    def exists(self, item_id: int) -> bool:
        return self.find_by_id(item_id) is not None

    def count(self) -> int:
        return len(self._load_items())

    # ---------- Write ----------
    def create(self, record: dict, item_id: int | None = None) -> dict:
        """Create an item.

        ``item_id`` is obtained by the service layer from the ID counter
        (items_meta.json) to stay strictly monotonic and never reused after
        deletion; if omitted, it falls back to "max existing ID + 1".
        """
        payload = dict(record)

        def mutator(items: list[dict]) -> dict:
            new_id = item_id if item_id is not None else self._next_id(items)
            if any(item.get("id") == new_id for item in items):
                raise ConflictError(f"Item ID {new_id} is already in use, please retry")
            # Put id first so the field order in items.json matches the document.
            record = {"id": new_id, **payload}
            items.append(record)
            return dict(record)

        return self.store.transaction(mutator)

    def update(self, item_id: int, changes: dict) -> dict | None:
        """Update fields by ID, returning the updated record; None if not found."""
        def mutator(items: list[dict]) -> dict | None:
            for item in items:
                if item.get("id") == item_id:
                    item.update(changes)
                    return dict(item)
            return None

        return self.store.transaction(mutator)

    def delete(self, item_id: int) -> bool:
        """Permanently delete (removes the record only from items.json, never
        touching other modules' files)."""
        def mutator(items: list[dict]) -> bool:
            for index, item in enumerate(items):
                if item.get("id") == item_id:
                    items.pop(index)
                    return True
            return False

        return self.store.transaction(mutator)

    # ---------- Primary key ----------
    def max_id(self) -> int:
        """Largest item ID currently in items.json (0 if empty)."""
        return self._next_id(self._load_items()) - 1

    @staticmethod
    def _next_id(items: list[dict]) -> int:
        largest = 0
        for item in items:
            try:
                largest = max(largest, int(item.get("id", 0)))
            except (TypeError, ValueError):
                continue
        return largest + 1
