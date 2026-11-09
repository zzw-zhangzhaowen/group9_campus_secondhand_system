"""Item module service layer (public interface).

Responsibilities: argument validation, permission checks, status transitions,
search/sort, and the unified response format. All data reads/writes go through
item_repository; the service layer never opens JSON files directly.
"""

from __future__ import annotations

import os
from typing import Any

from backend_zhang import config, validators
from backend_zhang.exceptions import BackendError, ValidationError
from backend_zhang.id_sequence import ItemIdSequence
from backend_zhang.item_archive import ItemArchive
from backend_zhang.item_repository import ItemRepository
from backend_zhang.json_store import now_text
from backend_zhang.response import failure, success
from backend_zhang.user_repository import UserRepository

# Fields allowed by update_item; status can only be changed via remove / restore.
EDITABLE_FIELDS = ("name", "category", "price", "description", "image_path")

# Archive file name / ID counter file name (both live next to items.json).
ARCHIVE_FILE_NAME = "items_deleted.json"
META_FILE_NAME = "items_meta.json"


# ---------- Internal helpers ----------
def _full_view(item: dict) -> dict:
    """Full item info (item data has no sensitive fields, safe to pass to the GUI)."""
    return {
        "id": item.get("id"),
        "seller_id": item.get("seller_id"),
        "name": item.get("name"),
        "category": item.get("category"),
        "price": item.get("price"),
        "description": item.get("description"),
        "image_path": item.get("image_path", ""),
        "status": item.get("status"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
    }


def _public_view(item: dict) -> dict:
    """Minimal public info, for favorites / messages / intents modules."""
    return {
        "id": item.get("id"),
        "seller_id": item.get("seller_id"),
        "name": item.get("name"),
        "category": item.get("category"),
        "price": item.get("price"),
        "status": item.get("status"),
    }


def _sort_key(field: str):
    """Sort key: times as strings (fixed format, comparable directly), price as number."""
    if field == config.SORT_PRICE:
        def key(record: dict) -> float:
            try:
                return float(record.get("price") or 0)
            except (TypeError, ValueError):
                return 0.0
        return key
    return lambda record: str(record.get(field, ""))


class ItemService:
    """Item business logic. Pass an independent data_file / user_repository to
    isolate data in tests."""

    def __init__(
        self,
        data_file: str | None = None,
        user_repository: UserRepository | None = None,
        deleted_file: str | None = None,
        meta_file: str | None = None,
    ):
        self.repository = ItemRepository(data_file)
        # Query user existence only via the repository, never read/write users.json directly.
        self.user_repository = user_repository or UserRepository()
        # Read-only archive of deleted items (v1.2): placed next to items.json
        # when not explicitly given, so tests passing a temp dir keep the archive
        # isolated from the production data directory.
        sibling_dir = os.path.dirname(os.path.abspath(data_file)) if data_file else None
        if deleted_file is None and sibling_dir:
            deleted_file = os.path.join(sibling_dir, ARCHIVE_FILE_NAME)
        self.archive = ItemArchive(deleted_file)
        # Item ID counter (v1.3): also defaults to the items.json directory.
        if meta_file is None and sibling_dir:
            meta_file = os.path.join(sibling_dir, META_FILE_NAME)
        self.id_sequence = ItemIdSequence(meta_file)

    # ---------- Internal ----------
    def _find_item_internal(self, item_id: int) -> dict | None:
        return self.repository.find_by_id(item_id)

    def _seller_exists(self, seller_id: int) -> bool:
        return self.user_repository.exists(seller_id)

    def _allocate_item_id(self) -> int:
        """Allocate an item ID (v1.3): strictly monotonic, never reused after deletion.

        The floor is max(max existing ID + 1, max archived item_id + 1), then the
        max with the counter, so even if items_meta.json is lost or shrunk it will
        not collide with existing or deleted item IDs.
        """
        floor = max(self.repository.max_id() + 1, self.archive.max_item_id() + 1, 1)
        return self.id_sequence.allocate(floor)

    @staticmethod
    def _filter_by_status(records: list[dict], include_removed: bool) -> list[dict]:
        if include_removed:
            return list(records)
        return [record for record in records if record.get("status") == config.STATUS_ON_SALE]

    @staticmethod
    def _sort_records(records: list[dict], sort_by: str, descending: bool) -> list[dict]:
        return sorted(records, key=_sort_key(sort_by), reverse=descending)

    def _prepare_query(self, include_removed: Any, sort_by: Any, descending: Any) -> tuple[bool, str, bool]:
        """Validate query parameters; raises ValidationError on failure."""
        removed = validators.validate_bool(include_removed, "include_removed")
        field, desc = validators.validate_sort(sort_by, descending)
        return removed, field, desc

    def _load_owned_item(self, item_id: Any, seller_id: Any) -> tuple[dict | None, dict | None]:
        """Validate ID + user existence + item existence + seller match; returns (item, error response)."""
        try:
            iid = validators.validate_item_id(item_id)
            sid = validators.validate_seller_id(seller_id)
        except ValidationError as exc:
            return None, failure(exc.message)

        try:
            if not self._seller_exists(sid):
                return None, failure("User does not exist")
            item = self._find_item_internal(iid)
        except BackendError as exc:
            return None, failure(exc.message)

        if item is None:
            return None, failure("Item does not exist")
        if item.get("seller_id") != sid:
            return None, failure("Permission denied for this item")
        return item, None

    # ---------- Publish ----------
    def create_item(
        self,
        seller_id: Any,
        name: Any,
        category: Any,
        price: Any,
        description: Any,
        image_path: Any = "",
    ) -> dict:
        try:
            sid = validators.validate_seller_id(seller_id)
        except ValidationError as exc:
            return failure(exc.message)

        try:
            if not self._seller_exists(sid):
                return failure("Seller user does not exist")
        except BackendError as exc:
            return failure(exc.message)

        try:
            clean_name = validators.validate_item_name(name)
            clean_category = validators.validate_category(category)
            clean_price = validators.validate_price(price)
            clean_description = validators.validate_item_description(description)
            clean_image = validators.validate_image_path(image_path)
        except ValidationError as exc:
            return failure(exc.message)

        now = now_text()
        record = {
            "seller_id": sid,
            "name": clean_name,
            "category": clean_category,
            "price": clean_price,
            "description": clean_description,
            "image_path": clean_image,
            "status": config.STATUS_ON_SALE,
            "created_at": now,
            "updated_at": now,
        }
        try:
            new_id = self._allocate_item_id()
        except BackendError as exc:
            return failure(f"Failed to publish item: could not allocate item ID ({exc.message})")
        try:
            saved = self.repository.create(record, new_id)
        except BackendError as exc:
            return failure(exc.message)
        return success(_full_view(saved), "Item published successfully")

    # ---------- Query ----------
    def get_all_items(
        self,
        include_removed: Any = False,
        sort_by: Any = config.SORT_CREATED_AT,
        descending: Any = True,
    ) -> dict:
        try:
            removed, field, desc = self._prepare_query(include_removed, sort_by, descending)
            records = self.repository.list_items()
        except ValidationError as exc:
            return failure(exc.message)
        except BackendError as exc:
            return failure(exc.message)

        records = self._filter_by_status(records, removed)
        records = self._sort_records(records, field, desc)
        return success([_full_view(item) for item in records], "Items retrieved successfully")

    def get_item_by_id(self, item_id: Any, include_removed: Any = False) -> dict:
        try:
            iid = validators.validate_item_id(item_id)
            removed = validators.validate_bool(include_removed, "include_removed")
            item = self._find_item_internal(iid)
        except ValidationError as exc:
            return failure(exc.message)
        except BackendError as exc:
            return failure(exc.message)

        if item is None:
            return failure("Item does not exist")
        if item.get("status") != config.STATUS_ON_SALE and not removed:
            return failure("Item does not exist or is off sale")
        return success(_full_view(item), "Item retrieved successfully")

    def get_items_by_seller(
        self,
        seller_id: Any,
        include_removed: Any = False,
        sort_by: Any = config.SORT_CREATED_AT,
        descending: Any = True,
    ) -> dict:
        try:
            sid = validators.validate_seller_id(seller_id)
            removed, field, desc = self._prepare_query(include_removed, sort_by, descending)
            records = self.repository.list_by_seller(sid)
        except ValidationError as exc:
            return failure(exc.message)
        except BackendError as exc:
            return failure(exc.message)

        records = self._filter_by_status(records, removed)
        records = self._sort_records(records, field, desc)
        return success([_full_view(item) for item in records], "Items retrieved successfully")

    def search_items(
        self,
        keyword: Any = "",
        category: Any = "",
        include_removed: Any = False,
        sort_by: Any = config.SORT_CREATED_AT,
        descending: Any = True,
    ) -> dict:
        """Combined keyword (name or description, case-insensitive) + category search, then sort."""
        try:
            text = validators.normalize_keyword(keyword)
            category_filter = validators.normalize_category_filter(category)
            removed, field, desc = self._prepare_query(include_removed, sort_by, descending)
            records = self.repository.list_items()
        except ValidationError as exc:
            return failure(exc.message)
        except BackendError as exc:
            return failure(exc.message)

        records = self._filter_by_status(records, removed)
        if category_filter:
            records = [item for item in records if item.get("category") == category_filter]
        if text:
            needle = text.lower()
            records = [
                item
                for item in records
                if needle in str(item.get("name", "")).lower()
                or needle in str(item.get("description", "")).lower()
            ]
        records = self._sort_records(records, field, desc)
        return success([_full_view(item) for item in records], "Items searched successfully")

    # ---------- Edit / status transitions ----------
    def update_item(self, item_id: Any, seller_id: Any, updated_data: Any) -> dict:
        item, error = self._load_owned_item(item_id, seller_id)
        if error is not None:
            return error
        if not isinstance(updated_data, dict):
            return failure("updated_data must be a dictionary")

        changes: dict[str, Any] = {}
        try:
            if "name" in updated_data:
                changes["name"] = validators.validate_item_name(updated_data["name"])
            if "category" in updated_data:
                changes["category"] = validators.validate_category(updated_data["category"])
            if "price" in updated_data:
                changes["price"] = validators.validate_price(updated_data["price"])
            if "description" in updated_data:
                changes["description"] = validators.validate_item_description(updated_data["description"])
            if "image_path" in updated_data:
                changes["image_path"] = validators.validate_image_path(updated_data["image_path"])
        except ValidationError as exc:
            return failure(exc.message)

        if not changes:
            return failure("No editable fields provided (only " + ", ".join(EDITABLE_FIELDS) + " are allowed)")

        changes["updated_at"] = now_text()  # created_at stays unchanged.
        try:
            updated = self.repository.update(item["id"], changes)
        except BackendError as exc:
            return failure(exc.message)
        if updated is None:
            return failure("Item does not exist")
        return success(_full_view(updated), "Item updated successfully")

    def remove_item(self, item_id: Any, seller_id: Any) -> dict:
        """Take off sale (on sale -> off sale)."""
        item, error = self._load_owned_item(item_id, seller_id)
        if error is not None:
            return error
        if item.get("status") != config.STATUS_ON_SALE:
            return failure("Item is already off sale")

        try:
            updated = self.repository.update(
                item["id"],
                {"status": config.STATUS_OFF_SALE, "updated_at": now_text()},
            )
        except BackendError as exc:
            return failure(exc.message)
        if updated is None:
            return failure("Item does not exist")
        return success(_full_view(updated), "Item taken off sale")

    def restore_item(self, item_id: Any, seller_id: Any) -> dict:
        """Relist (off sale -> on sale)."""
        item, error = self._load_owned_item(item_id, seller_id)
        if error is not None:
            return error
        if item.get("status") != config.STATUS_OFF_SALE:
            return failure("Item is already on sale")

        try:
            updated = self.repository.update(
                item["id"],
                {"status": config.STATUS_ON_SALE, "updated_at": now_text()},
            )
        except BackendError as exc:
            return failure(exc.message)
        if updated is None:
            return failure("Item does not exist")
        return success(_full_view(updated), "Item relisted")

    def delete_item_permanently(self, item_id: Any, seller_id: Any) -> dict:
        """Permanently delete. Does not require taking off sale first; only removes
        the items.json record and leaves other modules' data untouched.

        v1.2: before deletion the backend writes a snapshot into items_deleted.json
        (write-only, never read back; no interface can restore an item from it), so
        favorites/messages/intents modules can show "item deleted". If the archive
        write fails, deletion is **not** performed, avoiding the situation where the
        item is gone but no deletion record can be found.
        """
        item, error = self._load_owned_item(item_id, seller_id)
        if error is not None:
            return error

        try:
            self.archive.append(item, item["seller_id"])
        except BackendError as exc:
            return failure(f"Item not deleted: failed to write deletion archive ({exc.message})")

        try:
            deleted = self.repository.delete(item["id"])
        except BackendError as exc:
            # Roll back the archive just written so no fake "deleted" record remains.
            try:
                self.archive.discard_latest(item["id"])
            except BackendError:
                pass
            return failure(exc.message)
        if not deleted:
            try:
                self.archive.discard_latest(item["id"])
            except BackendError:
                pass
            return failure("Item does not exist")
        return success({"id": item["id"]}, "Item permanently deleted")

    # ---------- Helper query interfaces (for other modules) ----------
    def item_exists(self, item_id: Any, include_removed: Any = True) -> dict:
        try:
            iid = validators.validate_item_id(item_id)
            removed = validators.validate_bool(include_removed, "include_removed")
            item = self._find_item_internal(iid)
        except ValidationError as exc:
            return failure(exc.message)
        except BackendError as exc:
            return failure(exc.message)

        if item is None:
            return success(False, "Item does not exist")
        if not removed and item.get("status") != config.STATUS_ON_SALE:
            return success(False, "Item is off sale")
        return success(True, "Query successful")

    def is_item_active(self, item_id: Any) -> dict:
        """Pre-check for favorites/messages/intents when loading related data: the
        item exists and is on sale.

        Read-only interface added in v1.1; does not change any existing semantics.
        """
        try:
            iid = validators.validate_item_id(item_id)
            item = self._find_item_internal(iid)
        except ValidationError as exc:
            return failure(exc.message)
        except BackendError as exc:
            return failure(exc.message)

        if item is None:
            return success(False, "Item has been deleted")
        if item.get("status") != config.STATUS_ON_SALE:
            return success(False, "Item is off sale")
        return success(True, "Item is on sale")

    def get_item_status(self, item_id: Any) -> dict:
        try:
            iid = validators.validate_item_id(item_id)
            item = self._find_item_internal(iid)
        except ValidationError as exc:
            return failure(exc.message)
        except BackendError as exc:
            return failure(exc.message)

        if item is None:
            return failure("Item does not exist")
        return success(item.get("status"), "Query successful")

    def get_public_item_info(self, item_id: Any) -> dict:
        try:
            iid = validators.validate_item_id(item_id)
            item = self._find_item_internal(iid)
        except ValidationError as exc:
            return failure(exc.message)
        except BackendError as exc:
            return failure(exc.message)

        if item is None:
            return failure("Item does not exist")
        return success(_public_view(item), "Item info retrieved successfully")

    # ---------- Deleted item archive (v1.2, read-only) ----------
    def is_item_deleted(self, item_id: Any) -> dict:
        """Whether this item ID has been permanently deleted (read-only, for history display).

        ``data`` always contains 7 fields:
        ``{item_id, deleted, alive, seller_id, name, status_before_delete, deleted_at}``
        - deleted=True means a deletion archive exists;
        - alive=True means this ID still has a live item (when the ID has been
          reused by a new item, deleted and alive can both be True).
        """
        try:
            iid = validators.validate_item_id(item_id)
            alive = self._find_item_internal(iid) is not None
            record = self.archive.find_latest(iid)
        except ValidationError as exc:
            return failure(exc.message)
        except BackendError as exc:
            return failure(exc.message)

        data = {
            "item_id": iid,
            "deleted": record is not None,
            "alive": alive,
            "seller_id": record.get("seller_id") if record else None,
            "name": record.get("name") if record else None,
            "status_before_delete": record.get("status_before_delete") if record else None,
            "deleted_at": record.get("deleted_at") if record else None,
        }
        if record is None:
            return success(data, "No deletion record for this item")
        if alive:
            return success(data, "This ID once had a deleted item, but it has been reused by a new item")
        return success(data, "Item permanently deleted")

    def list_deleted_items(self, limit: Any = 50) -> dict:
        """Return archive snapshots in reverse deletion-time order (read-only, for reports and auditing)."""
        if isinstance(limit, bool) or not isinstance(limit, int):
            return failure("limit must be an integer")
        if limit < 1 or limit > 500:
            return failure("limit must be between 1 and 500")
        try:
            records = self.archive.list_records(limit)
        except BackendError as exc:
            return failure(exc.message)
        return success(records, "Deleted items retrieved successfully")


# ---------- Module-level public interface (GUI and other modules call these) ----------
_default_service: ItemService | None = None


def get_item_service() -> ItemService:
    global _default_service
    if _default_service is None:
        _default_service = ItemService()
    return _default_service


def reset_item_service(
    data_file: str | None = None,
    user_repository: UserRepository | None = None,
    deleted_file: str | None = None,
    meta_file: str | None = None,
) -> ItemService:
    """Switch the default service's data files (for tests and demos)."""
    global _default_service
    _default_service = ItemService(data_file, user_repository, deleted_file, meta_file)
    return _default_service


def create_item(
    seller_id: Any,
    name: Any,
    category: Any,
    price: Any,
    description: Any,
    image_path: Any = "",
) -> dict:
    return get_item_service().create_item(seller_id, name, category, price, description, image_path)


def get_all_items(
    include_removed: Any = False,
    sort_by: Any = config.SORT_CREATED_AT,
    descending: Any = True,
) -> dict:
    return get_item_service().get_all_items(include_removed, sort_by, descending)


def get_item_by_id(item_id: Any, include_removed: Any = False) -> dict:
    return get_item_service().get_item_by_id(item_id, include_removed)


def get_items_by_seller(
    seller_id: Any,
    include_removed: Any = False,
    sort_by: Any = config.SORT_CREATED_AT,
    descending: Any = True,
) -> dict:
    return get_item_service().get_items_by_seller(seller_id, include_removed, sort_by, descending)


def update_item(item_id: Any, seller_id: Any, updated_data: Any) -> dict:
    return get_item_service().update_item(item_id, seller_id, updated_data)


def remove_item(item_id: Any, seller_id: Any) -> dict:
    return get_item_service().remove_item(item_id, seller_id)


def restore_item(item_id: Any, seller_id: Any) -> dict:
    return get_item_service().restore_item(item_id, seller_id)


def delete_item_permanently(item_id: Any, seller_id: Any) -> dict:
    return get_item_service().delete_item_permanently(item_id, seller_id)


def search_items(
    keyword: Any = "",
    category: Any = "",
    include_removed: Any = False,
    sort_by: Any = config.SORT_CREATED_AT,
    descending: Any = True,
) -> dict:
    return get_item_service().search_items(keyword, category, include_removed, sort_by, descending)


def item_exists(item_id: Any, include_removed: Any = True) -> dict:
    return get_item_service().item_exists(item_id, include_removed)


def is_item_active(item_id: Any) -> dict:
    """Whether the item is tradeable (exists and on sale). Used as a pre-check by
    favorites/messages/intents modules."""
    return get_item_service().is_item_active(item_id)


def get_item_status(item_id: Any) -> dict:
    return get_item_service().get_item_status(item_id)


def get_public_item_info(item_id: Any) -> dict:
    return get_item_service().get_public_item_info(item_id)


def is_item_deleted(item_id: Any) -> dict:
    """Whether the item has been permanently deleted (for showing "item deleted" in
    history/favorites lists). Added in v1.2."""
    return get_item_service().is_item_deleted(item_id)


def list_deleted_items(limit: Any = 50) -> dict:
    """Deleted item archive list (reverse deletion-time order). Added in v1.2, read-only."""
    return get_item_service().list_deleted_items(limit)
