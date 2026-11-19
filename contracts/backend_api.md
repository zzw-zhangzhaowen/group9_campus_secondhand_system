# Backend API Contract (backend_api.md)

Owner: ZHANG ZHAOWEN | Version: v1.3 | Code: `backend_zhang/`

This file is the **sole contract between `backend_zhang`, the GUI (`gui_gao`) and the auxiliary modules (`feature_du`)**.
No module may bypass the public interfaces defined here to read or write `users.json` / `items.json` / `items_deleted.json` directly.

---

## 0. How to Call

```python
# User module
from backend_zhang.user_service import (
    register_user, login_user, get_user_by_id, get_public_user_info,
    update_nickname, change_password, user_exists, to_safe_dict,
)

# Item module
from backend_zhang.item_service import (
    create_item, get_all_items, get_item_by_id, get_items_by_seller,
    update_item, remove_item, restore_item, delete_item_permanently,
    search_items, item_exists, is_item_active, get_item_status, get_public_item_info,
    is_item_deleted, list_deleted_items,
)
```

The module-level functions above use the production data files under `backend_zhang/data/*.json`.
For tests and demos, instantiate the services and pass your own data files (see Section 5); never pollute the production data.

---

## 1. Unified Response Format

**Every** public interface returns the same structure:

```python
{
    "success": True | False,      # bool
    "message": "Registration successful",   # str, safe to display directly to the user
    "data": {...} | [...] | True | False | None
}
```

Example failure:

```python
{"success": False, "message": "Permission denied for this item", "data": None}
```

Calling convention: **check `success` first, then use `data`**; `data` is always a deep copy, so modifying it never affects the data files.

---

## 2. User Interfaces

| Interface | Parameters | `data` on success |
|---|---|---|
| `register_user` | username, password, nickname | User detail (no password fields) |
| `login_user` | username, password | User detail (no password fields) |
| `get_user_by_id` | user_id | User detail |
| `get_public_user_info` | user_id | `{id, username, nickname}` |
| `update_nickname` | user_id, new_nickname | User detail |
| `change_password` | user_id, old_password, new_password | `None` |
| `user_exists` | user_id | `True / False` |

User detail fields: `{id, username, nickname, created_at, updated_at}`.
**No interface ever returns `password_hash` / `password_salt`.**

### Field Rules

| Field | Rule |
|---|---|
| username | 3–20 characters; first character must be an ASCII letter; letters/digits/underscore only; case-insensitive uniqueness |
| password | 8–32 characters; at least one ASCII letter; at least one digit; no spaces (leading/trailing included); never stored in plain text |
| nickname | 2–20 characters; Chinese characters / letters / digits / underscore; non-empty; uniqueness not required |

### Common Failure Messages

These are the exact `message` strings returned by the code.

| Scenario | message |
|---|---|
| Username already taken | `Username already exists` |
| Invalid username | `Username must be 3-20 characters, start with an ASCII letter, and contain only letters, digits and underscores` |
| Invalid password | `Password length must be 8-32 characters` / `Password must contain at least one letter` / `Password must contain at least one digit` / `Password must not contain spaces` |
| Invalid nickname | `Nickname cannot be empty` / `Nickname length must be 2-20 characters` / `Nickname can only contain Chinese characters, letters, digits and underscores` |
| Login failure | `Invalid username or password` (does not distinguish unknown account from wrong password) |
| Unknown user | `User does not exist` |
| Wrong old password | `Old password is incorrect` |

### Examples

```python
>>> register_user("student_01", "abcd1234", "Alice")
{'success': True, 'message': 'Registration successful',
 'data': {'id': 1, 'username': 'student_01', 'nickname': 'Alice',
          'created_at': '2026-10-27 10:00:00', 'updated_at': '2026-10-27 10:00:00'}}

>>> login_user("student_01", "wrong9999")
{'success': False, 'message': 'Invalid username or password', 'data': None}
```

---

## 3. Item Interfaces

| Interface | Parameters | `data` on success |
|---|---|---|
| `create_item` | seller_id, name, category, price, description, image_path="" | Item detail |
| `get_all_items` | include_removed=False, sort_by="created_at", descending=True | Item list |
| `get_item_by_id` | item_id, include_removed=False | Item detail or failure |
| `get_items_by_seller` | seller_id, include_removed=False, sort_by, descending | Item list |
| `update_item` | item_id, seller_id, updated_data(dict) | Item detail |
| `remove_item` | item_id, seller_id | Item detail (status = `off_sale`) |
| `restore_item` | item_id, seller_id | Item detail (status = `on_sale`) |
| `delete_item_permanently` | item_id, seller_id | `{"id": item_id}` |
| `search_items` | keyword="", category="", include_removed=False, sort_by, descending | Item list |
| `item_exists` | item_id, include_removed=True | `True / False` |
| `is_item_active` | item_id | `True / False` (exists and on sale; added in v1.1) |
| `get_item_status` | item_id | `"on_sale"` / `"off_sale"` |
| `get_public_item_info` | item_id | `{id, seller_id, name, category, price, status}` |
| `is_item_deleted` | item_id | Deletion archive summary (added in v1.2, see 4.1) |
| `list_deleted_items` | limit=50 | Archive snapshot list (added in v1.2, see 4.1) |

Item detail fields:
`{id, seller_id, name, category, price, description, image_path, status, created_at, updated_at}`

### Field Rules

| Field | Rule |
|---|---|
| id | Assigned by the backend, positive integer, **strictly monotonic and never reused** (guaranteed by the `items_meta.json` counter since v1.3); callers must not supply it |
| name | Non-empty after trimming, at most 20 characters |
| description | Non-empty after trimming, at most 200 characters |
| category | One of `books` / `electronics` / `clothing` / `household` (see the enum migration note in Section 6) |
| price | Must be a number **> 0** (rejects 0, negatives, empty string, `None`, booleans and non-numeric text); rounded to two decimals, then re-checked, so small positive inputs such as `0.004` are rejected rather than stored as `0.0`; upper bound 100,000,000; stored as float |
| image_path | May be empty, at most 260 characters; the backend only stores the path and never processes the image |

### Query Rules

- `include_removed=False` (default): excludes `off_sale` items.
- `sort_by` accepts only `created_at` / `updated_at` / `price`; any other value fails (prevents raw user input from becoming a sort key).
- `descending=True` sorts descending; prices compare numerically, timestamps compare as `YYYY-MM-DD HH:MM:SS` strings.
- `search_items` matches **name or description**, trims the keyword and ignores case for ASCII text;
  an empty `category` or `"all"` means no category filter; both conditions can be combined.

### Status and Permissions

| Current status | Operation | Result |
|---|---|---|
| `on_sale` | `remove_item` | `off_sale` |
| `off_sale` | `restore_item` | `on_sale` |
| `off_sale` | `remove_item` | Failure: `Item is already off sale` |
| `on_sale` | `restore_item` | Failure: `Item is already on sale` |
| Any | `delete_item_permanently` | Record permanently removed (no need to take it off sale first); a read-only archive snapshot is written before deletion (since v1.2) |

The following operations **must be performed by the seller** (enforced in the backend): `update_item`, `remove_item`, `restore_item`, `delete_item_permanently`.

Failure messages: `Item does not exist` / `User does not exist` / `Permission denied for this item` / disallowed status.

### Timestamp Rules

- Create: `created_at = updated_at = current time`
- Edit: `created_at` unchanged, `updated_at` refreshed
- Take off sale / relist: `updated_at` refreshed
- Format is always `YYYY-MM-DD HH:MM:SS`

### Examples

```python
>>> create_item(1, "Python Textbook", "books", 30, "Beginner-friendly", "")
{'success': True, 'message': 'Item published successfully',
 'data': {'id': 1, 'seller_id': 1, 'name': 'Python Textbook', 'category': 'books',
          'price': 30.0, 'description': 'Beginner-friendly', 'image_path': '',
          'status': 'on_sale', 'created_at': '2026-10-27 10:00:00',
          'updated_at': '2026-10-27 10:00:00'}}

>>> search_items(keyword="python", category="books", sort_by="price", descending=False)
{'success': True, 'message': 'Items searched successfully', 'data': [...]}
```

`update_item` accepts only `name / category / price / description / image_path` in `updated_data`;
all other fields (`id`, `seller_id`, `status`, `created_at`, `updated_at`) are ignored,
and submitting only those fields returns `No editable fields provided (only name, category, price, description, image_path are allowed)`.

---

## 4. Boundary for Auxiliary Modules

Favorites (`favorites.json`), messages (`messages.json`), intentions (`intentions.json`) and logs (`logs.json`)
are maintained by `feature_du/` itself, which **must not read or write `users.json` / `items.json` directly**.

They may call:

| Interface | Purpose |
|---|---|
| `user_exists(user_id)` | Validate that a user exists |
| `item_exists(item_id, include_removed=True)` | Validate that an item exists (including off-sale items) |
| `is_item_active(item_id)` | **Recommended**: batch pre-check when loading favorites/messages, to see whether an item is still tradable |
| `is_item_deleted(item_id)` | **Recommended since v1.2**: check whether an item was permanently deleted and read its name/price for history display |
| `get_public_item_info(item_id)` | Display title/price/status (including off-sale, to show "item taken off sale") |
| `get_item_status(item_id)` | Check whether an item is on sale before submitting an intention |
| `get_public_user_info(user_id)` | Display a nickname |
| `to_safe_dict(user)` | Explicit sanitisation: drop every `password*` field before logging or display |

Recommended pattern (loading the favorites list):

```python
from backend_zhang.item_service import is_item_active, get_public_item_info, is_item_deleted

for favorite in favorites:
    info = get_public_item_info(favorite["item_id"])
    if not info["success"]:
        record = is_item_deleted(favorite["item_id"])["data"]   # since v1.2
        show_item_as_deleted(favorite, record["name"], record["deleted_at"])
    elif not is_item_active(favorite["item_id"])["data"]:
        show_item_as_off_shelf(favorite, info["data"])   # item taken off sale
    else:
        show_normal(favorite, info["data"])
```

After an item is permanently deleted, the backend changes **only** `items.json` (plus the read-only archive `items_deleted.json`);
whether to keep or clear favorites/messages/intentions history is decided by each module.

> v1.1 note: `is_item_active` is an **added** read-only interface; no existing interface's parameters, return value or semantics were changed.
> v1.2 note: the "three statuses + soft delete" design was **not adopted** (it conflicts with the requirement that records be permanently removed and unrecoverable).
> The compromise is "two statuses unchanged + a separate read-only archive", detailed in 4.1.

### 4.1 Deleted-Item Archive (added in v1.2)

`delete_item_permanently` behaves as before (physically removes the record from `items.json`, returns `{"id": item_id}`),
but writes an item snapshot to `items_deleted.json` before deletion (format: `contracts/data_schema.md` Section 3).
The archive is **append-and-read only**; no interface can restore an item from it.

**`is_item_deleted(item_id)`** → `data` always has 7 fields:

```python
>>> delete_item_permanently(2, 1)
{'success': True, 'message': 'Item permanently deleted', 'data': {'id': 2}}
>>> is_item_deleted(2)
{'success': True, 'message': 'Item permanently deleted',
 'data': {'item_id': 2, 'deleted': True, 'alive': False, 'seller_id': 1,
          'name': 'Mechanical Keyboard', 'status_before_delete': 'on_sale',
          'deleted_at': '2026-10-28 19:15:36'}}
>>> is_item_deleted(99)
{'success': True, 'message': 'No deletion record for this item',
 'data': {'item_id': 99, 'deleted': False, 'alive': False, 'seller_id': None,
          'name': None, 'status_before_delete': None, 'deleted_at': None}}
```

| Field | Meaning |
|---|---|
| `deleted` | Whether a deletion archive record exists |
| `alive` | Whether an item currently holds this ID. With the v1.3 monotonic-ID counter a deleted ID is never reused, so this is always `False` for newly deleted items; `deleted=True, alive=True` can only come from legacy data created before v1.3 |
| `name` / `price` etc. | Values from the deletion snapshot, `None` when there is no archive record |

**`list_deleted_items(limit=50)`** → `data` is a list of snapshots (most recently deleted first), `limit` an integer from 1–500.

Failure scenarios (business-expected states still do not count as interface errors):

| Scenario | success | message |
|---|---|---|
| No deletion record | `True` | `No deletion record for this item` (`data.deleted=False`) |
| Invalid item_id | `False` | Parameter message |
| limit not an integer / out of range | `False` | `limit must be an integer` / `limit must be between 1 and 500` |
| Archive file corrupt (including invalid UTF-8) | `False` | `Data file is corrupt: items_deleted.json is not valid UTF-8 ...` / `Data file is corrupt: items_deleted.json (line ...) ...` |

> `delete_item_permanently` **refuses to delete** when the archive write fails (`success=False`, item kept),
> guaranteeing "if it is deleted, a deletion record exists". Repair or delete `items_deleted.json` (auto-rebuilt as `[]`) and retry.
> If deletion fails *and* rolling back the just-written archive also fails, the response explicitly reports both failures and asks for manual reconciliation:
> `Item not deleted (...); deletion archive rollback also failed (...). Please reconcile items_deleted.json manually.`
> This case is never silently swallowed (fixed 2026-11-18).

---

## 5. Custom Data Paths (for Tests and Demos)

Data paths are configurable; callers can pass their own files to fully isolate production data:

```python
import os, tempfile
from backend_zhang.user_service import UserService
from backend_zhang.item_service import ItemService
from backend_zhang.user_repository import UserRepository

with tempfile.TemporaryDirectory() as tmp:
    users_file = os.path.join(tmp, "users.json")
    items_file = os.path.join(tmp, "items.json")
    user_service = UserService(users_file)
    # When deleted_file / meta_file are omitted, the archive and ID counter are placed
    # next to items.json (since v1.2 / v1.3), so a temporary directory isolates all three.
    item_service = ItemService(items_file, UserRepository(users_file))
    # Or specify them explicitly: ItemService(items_file, repo, deleted_file=..., meta_file=...)
    ...
```

Production uses the module-level functions (e.g. `register_user(...)`), which always operate on `backend_zhang/data/*.json`.

---

## 6. Interface Change Log

| Version | Change | Impact | Migration |
|---|---|---|---|
| v1.0 | First frozen release: all user/item interfaces implemented per the requirements document | GUI and feature_du can integrate directly | — |
| v1.1 | Added `is_item_active(item_id)` and `to_safe_dict(user)`; unique temp-file names in `json_store` (internal) | Pure addition, no breaking change | None; call as needed |
| v1.2 | Added `is_item_deleted(item_id)` and `list_deleted_items(limit=50)`; `delete_item_permanently` writes a read-only archive first; `ItemService` gains optional `deleted_file` | Pure addition; `delete_item_permanently` parameters, return value and semantics unchanged | None; call new interfaces as needed |
| v1.3 | Item IDs become **strictly monotonic and never reused** (new `items_meta.json` counter, `ItemService` gains optional `meta_file`) | Internal implementation only; interface parameters and return values unchanged; IDs may skip numbers | None; historical data needs no processing |
| Enum change | Categories changed from Chinese values to `books/electronics/clothing/household`, statuses to `on_sale/off_sale` (`config.py` is authoritative; GUI is aligned) | Old Chinese values no longer pass validation; the backend never silently rewrites historical data | **Manual migration required**: replace old Chinese category/status values in existing data files with the English enums, or start from fresh data. No automatic conversion is provided |
| Review fixes (2026-11-18) | Price is rounded to two decimals and re-checked for positivity, with an upper bound; invalid UTF-8 raises `DataFileError` instead of an uncaught `UnicodeDecodeError`; archive rollback failure is reported instead of swallowed | Behaviour fixes only; no interface, parameter or field changes | None for callers; clients should treat the new validation messages as normal failures |

v1.3 details:

1. **Problem**: the old "highest existing ID + 1" reused an ID after the last record was deleted,
   so old `item_id` values stored in favorites/messages/intentions could point to a different item (silent data corruption).
2. **Solution**: added `backend_zhang/id_sequence.py` + `items_meta.json` (`{"next_item_id": N}`).
   The allocation floor is `max(counter, highest existing ID + 1, highest archived item_id + 1)`, so no collision occurs
   even if the counter is deleted or manually lowered.
3. **Impact**: IDs are allocated exclusively by the backend; callers never could specify one, so GUI / feature_du need **zero changes**.
   The only visible difference is that a new item after a deletion gets a larger ID — expected behaviour.
4. **Error handling**: a corrupt counter file makes `create_item` fail with a repair hint (no crash, no overwrite of the original file).
   Repair or delete the file (it is rebuilt as `{}`) and retry.
5. **Not applicable**: user IDs still use "highest existing ID + 1" (users cannot be deleted in this version, so reuse is impossible).

v1.2 details:

1. **Deleted-item archive** — `items.json` still uses physical deletion, items still have two statuses, and existing interfaces are unchanged;
   the archive `items_deleted.json` is append-only and read-only, and cannot restore an item (per the requirements).
2. **`is_item_deleted(item_id)`** — returns 7 fields including `deleted / alive` for history display;
   no archive record still returns `success=True` (a business-expected state).
3. **`list_deleted_items(limit=50)`** — archive list for reports and auditing, `limit` restricted to 1–500.
4. **`deleted_file` parameter** — when omitted, the archive is placed next to `items.json`; passing a temporary directory isolates it automatically.
5. **"Three statuses + soft delete" rejected** — conflicts with the requirements (records must be permanently removed); this compromise is used instead.

v1.1 details:

1. **`is_item_active(item_id)`** — read-only interface returning `data: True/False`.
   A missing or off-sale item returns `success=True + data=False` (business-expected state, not an interface error),
   with messages `Item does not exist` / `Item is off sale` / `Query successful` respectively.
2. **`to_safe_dict(user)`** — given a user dict from the repository, returns a copy with every `password*` field removed;
   used as a safety net by the logging module and GUI debug output.
3. **Atomic write hardening** — temp files use unique names from `tempfile.mkstemp()` (previously a fixed `<name>.tmp`),
   followed by `fsync` and `os.replace`. No external behaviour change; only safer under concurrency and exceptions.
