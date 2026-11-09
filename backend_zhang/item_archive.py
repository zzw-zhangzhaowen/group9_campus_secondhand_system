"""Archive of permanently deleted items (items_deleted.json). Added in v1.2,
as the implementation for discussion item C of v1.1.

Section 13 of the requirements requires that after permanent deletion, the item
record is removed from items.json for good and cannot be restored. But
favorites / messages / intent orders may still hold the deleted item's ID
(Section 16: history is kept by each module itself). To let those modules and
the GUI show a real title like "item deleted (Python textbook)", this module
keeps a read-only snapshot for every permanent deletion.

Design constraints (consistent with the requirements):
1. items.json is still physically deleted, item status is still two-state
   (on sale / off sale), existing interface semantics are unchanged;
2. the archive is append-only and read-only; no interface can restore an item
   back into items.json from it;
3. the archive file is maintained only by backend_zhang; other modules may only
   query it through item_service's read-only interfaces;
4. it uses JsonArrayStore just like items.json (atomic write + file lock + never
   overwrite a corrupt file).
"""

from __future__ import annotations

from typing import Any

from backend_zhang import config
from backend_zhang.json_store import JsonArrayStore, now_text


class ItemArchive:
    """Read/write for items_deleted.json (writes are only append / discard_latest, no update)."""

    def __init__(self, data_file: str | None = None):
        self.store = JsonArrayStore(data_file or config.DEFAULT_ITEMS_DELETED_FILE)

    @property
    def data_file(self) -> str:
        return self.store.path

    # ---------- Internal read/write ----------
    def _load_records(self) -> list[dict]:
        return self.store.load()

    def _save_records(self, records: list[dict]) -> None:
        self.store.save(records)

    # ---------- Write ----------
    def append(self, item: dict, operator_id: int) -> dict:
        """Save a snapshot before permanent deletion and return the archive record."""
        snapshot = {
            "item_id": item.get("id"),
            "seller_id": item.get("seller_id"),
            "name": item.get("name"),
            "category": item.get("category"),
            "price": item.get("price"),
            "description": item.get("description"),
            "image_path": item.get("image_path", ""),
            "status_before_delete": item.get("status"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "deleted_at": now_text(),
            "deleted_by": operator_id,
        }

        def mutator(records: list[dict]) -> dict:
            records.append(snapshot)
            return dict(snapshot)

        return self.store.transaction(mutator)

    def discard_latest(self, item_id: int) -> bool:
        """Undo the latest archive entry (used only to roll back when the actual
        deletion failed, so a fake archive is not left behind)."""
        def mutator(records: list[dict]) -> bool:
            for index in range(len(records) - 1, -1, -1):
                if records[index].get("item_id") == item_id:
                    records.pop(index)
                    return True
            return False

        return self.store.transaction(mutator)

    # ---------- Query ----------
    def find_latest(self, item_id: int) -> dict | None:
        """Most recent deletion archive for an item ID; None if there is no archive."""
        for record in reversed(self._load_records()):
            if record.get("item_id") == item_id:
                return dict(record)
        return None

    def list_records(self, limit: int | None = None) -> list[dict]:
        """Return records in reverse archive order (most recently deleted first)."""
        records = [dict(record) for record in self._load_records()]
        records.reverse()
        if limit is not None:
            records = records[:limit]
        return records

    def count(self) -> int:
        return len(self._load_records())

    def max_item_id(self) -> int:
        """Largest item ID ever archived (0 if none), used as the ID allocation floor."""
        largest = 0
        for record in self._load_records():
            try:
                largest = max(largest, int(record.get("item_id", 0)))
            except (TypeError, ValueError):
                continue
        return largest

    def exists(self, item_id: Any) -> bool:
        return self.find_latest(int(item_id)) is not None
