# Data Format Specification (data_schema.md)

Owner: ZHANG ZHAOWEN | Files: `backend_zhang/data/users.json`, `items.json`, `items_deleted.json`, `items_meta.json`

## 0. General Conventions

- Encoding: UTF-8 (`ensure_ascii=False`, human-readable text)
- Root node: `users.json` / `items.json` / `items_deleted.json` are **JSON arrays**; `items_meta.json` is a **JSON object**
- IDs: positive integers, unique, **strictly monotonic and never reused** (assigned by the `items_meta.json` counter since v1.3)
- Timestamps: strings in `YYYY-MM-DD HH:MM:SS` format
- Write strategy: create a unique temp file in the same directory → `fsync` → `os.replace` (an interruption never leaves a half-written JSON file)
- Missing file: parent directory is created and an empty value is written (array `[]` / object `{}`)
- Corrupt file: the interface returns `{"success": false, "message": "Data file is corrupt: ..."}` and **never overwrites the original file**; invalid UTF-8 is treated as corruption (fixed 2026-11-18)

---

## 1. users.json

```json
[
  {
    "id": 1,
    "username": "student_01",
    "password_hash": "0f1e2d3c... (SHA-256 hex, 64 chars)",
    "password_salt": "9a8b7c6d... (16-byte random salt, 32 hex chars)",
    "nickname": "Alice",
    "created_at": "2026-10-27 10:00:00",
    "updated_at": "2026-10-27 10:00:00"
  }
]
```

| Field | Type | Description |
|---|---|---|
| id | int | Unique user ID, positive integer, auto-incremented |
| username | str | Login name, 3–20 characters, starts with a letter, case-insensitive uniqueness |
| password_hash | str | PBKDF2-HMAC-SHA256 derived hash (120,000 iterations) |
| password_salt | str | Random salt (`secrets.token_hex(16)`) |
| nickname | str | Display name, 2–20 characters |
| created_at | str | Registration time |
| updated_at | str | Last modified time (nickname / password change) |

Rules:

- Plain-text passwords **never appear in any file**;
- `password_hash` / `password_salt` are **never returned to callers**;
- Changing the password also replaces the salt, so the hash changes;
- User deletion is not supported in this version.

---

## 2. items.json

```json
[
  {
    "id": 1,
    "seller_id": 1,
    "name": "Python Textbook",
    "category": "books",
    "price": 30.0,
    "description": "Beginner-friendly Python textbook.",
    "image_path": "",
    "status": "on_sale",
    "created_at": "2026-10-27 10:00:00",
    "updated_at": "2026-10-27 10:00:00"
  }
]
```

| Field | Type | Description |
|---|---|---|
| id | int | Unique item ID, positive integer, **strictly monotonic and never reused** (assigned by the v1.3 counter) |
| seller_id | int | Seller's user ID (references `users.id`) |
| name | str | Item name, ≤ 20 characters |
| category | str | `books` / `electronics` / `clothing` / `household` |
| price | float | Price, **must be > 0**, rounded to two decimals, upper bound 100,000,000 |
| description | str | Item description, ≤ 200 characters, non-empty |
| image_path | str | Image path, may be an empty string (no image processing in the backend) |
| status | str | `on_sale` / `off_sale` |
| created_at | str | Publication time, **unchanged on edit** |
| updated_at | str | Last update time (edit / take off sale / relist) |

Rules:

- Status moves only between these two values: `on_sale --take off sale--> off_sale`, `off_sale --relist--> on_sale`;
- Permanent deletion removes the whole object from the array (no need to take it off sale first);
- Linked to the user table through `seller_id`; deleting an item does **not cascade** into other modules' files.

---

## 3. items_deleted.json (added in v1.2, read-only archive of deleted items)

On permanent deletion, the backend writes a snapshot **before** removing the record from `items.json`, so favorites / messages / intentions can display history such as "item deleted (Python Textbook)" (per the requirements: each module keeps its own history).

```json
[
  {
    "item_id": 2,
    "seller_id": 1,
    "name": "Mechanical Keyboard",
    "category": "electronics",
    "price": 120.0,
    "description": "87-key blue switches, like new",
    "image_path": "images/kb.png",
    "status_before_delete": "on_sale",
    "created_at": "2026-10-27 10:00:00",
    "updated_at": "2026-10-27 10:00:00",
    "deleted_at": "2026-10-28 19:15:36",
    "deleted_by": 1
  }
]
```

| Field | Type | Description |
|---|---|---|
| item_id | int | ID of the deleted item (**not** `id`, to avoid confusion with live items) |
| seller_id | int | Original seller's user ID |
| name / category / price / description / image_path | — | Original field values at deletion time (snapshot) |
| status_before_delete | str | Status at deletion: `on_sale` / `off_sale` |
| created_at / updated_at | str | The item's original timestamps, unchanged by archiving |
| deleted_at | str | Time of permanent deletion |
| deleted_by | int | User who performed the deletion (currently always the seller; kept for future extension) |

Rules:

- **Append-only and read-only**: no interface can restore an item from this file into `items.json` (per the requirement that deletion is irreversible);
- `items.json` still uses physical deletion and items still have only two statuses (`on_sale` / `off_sale`); existing interface semantics are unchanged;
- With the v1.3 monotonic-ID counter a deleted ID is never reused, so a new item cannot inherit an old archive record;
  the `alive=True` case in `is_item_deleted` only occurs for legacy data created before v1.3;
- If this file is corrupt (including invalid UTF-8), `delete_item_permanently` **refuses to delete** and asks for repair,
  avoiding "item gone but no deletion record"; repair or delete the file (auto-rebuilt as `[]`) to continue;
  if rollback of an already-written archive also fails, the response reports both failures and asks for manual reconciliation;
- The archive is maintained only by `backend_zhang`; other modules query it through `is_item_deleted` / `list_deleted_items` and must never open it directly.

---

## 4. items_meta.json (added in v1.3, item ID counter)

```json
{
  "next_item_id": 5
}
```

| Field | Type | Description |
|---|---|---|
| next_item_id | int | Next item ID to allocate (incremented after each allocation) |

Rules:

- **Read and written only by `id_sequence.py` in the backend**; no other module may open it; fully transparent to GUI / feature_du;
- Allocation floor = `max(next_item_id, highest existing item ID + 1, highest archived item_id + 1)`:
  even if this file is deleted or manually lowered, IDs cannot collide with existing or deleted items;
- A failed write after validation may leave a skipped number — a normal cost of "unique + monotonic" IDs;
- If this file is corrupt, `create_item` fails with a repair hint (never silently overwritten); repair or delete it (auto-rebuilt as `{}`) and retry;
- User IDs still use "highest existing ID + 1" (users cannot be deleted in this version, so reuse is impossible).

---

## 5. Files Owned by Other Modules (not maintained here)

| File | Owner | Description |
|---|---|---|
| `favorites.json` | feature_du | Favorite records |
| `messages.json` | feature_du | Item messages |
| `intentions.json` | feature_du | Purchase intentions |
| `logs.json` | feature_du | Operation logs |

These modules may read user/item information only through the public interfaces in Section 4 of `contracts/backend_api.md`.

---

## 6. Example Data

| File | Purpose |
|---|---|
| `backend_zhang/data/users.example.json` | Empty-array template, safe to commit |
| `backend_zhang/data/items.example.json` | Empty-array template, safe to commit |
| `backend_zhang/data/items_deleted.example.json` | Empty-array template, safe to commit |
| `backend_zhang/data/items_meta.example.json` | Counter initial-value template, safe to commit |
| `tests_zhao/fixtures/` | Test data directory, placed by the test owner (ZHAO XIAOJUN) |

`users.json` / `items.json` / `items_deleted.json` / `items_meta.json` are listed in `.gitignore` and will not be uploaded by mistake.
Place test data in `tests_zhao/fixtures/` or `tempfile.TemporaryDirectory()`; never use the production data files.
