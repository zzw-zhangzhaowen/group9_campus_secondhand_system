# API Interface Specification
| Item | Description |
|---|---|
| Project Name | Campus Secondhand Marketplace Management System |
| Document Name | API_spec.md (Backend API Specification) |
| Author | ZHAO Xiaojun |
| Date Written | 2026-11-04 |
| Code Sources | backend_zhang (user module, item module)<br>feature_du (favorites, purchase intentions, messages) |
| Document Purpose | Reference for the APIs used in automated tests (test_zhao/test_all.py) |

---

## 1. Document Scope and General Conventions

### 1.1 Scope
- `user_repository`, `item_repository`, `json_store`, `security`, `validators`, `id_sequence`, `item_archive`, `config`, `response`, and `exceptions` under `backend_zhang`;
- All private functions and attributes beginning with an underscore (`_`);
- Callback functions for controls in the Tkinter GUI.

### 1.2 Unified Return Format
All publicly exposed interfaces (user module and item module) must return a uniform dictionary structure. Additional modules (favorites, intentions, messages) must also follow this format once aligned with the backend.
Successful response:

    {
      "success": True,
      "message": "Operation successful",
      "data": <any business data, possibly None, dict, list, bool>
    }

Failed response:

    {
      "success": False,
      "message": "Specific reason for failure",
      "data": None
    }

Conventions:
1. `success` must always be a Boolean; callers determine success or failure based solely on this field.
2. `message` must always be a Chinese prompt that can be displayed directly to users; the frontend must not alter its meaning.
3. In `backend_zhang`, `data` must always be returned as a `deepcopy`, so callers can modify the return value without contaminating internal data.
4. The `data` returned by user-related interfaces must be a redacted view and **must never include fields such as `password`, `password_hash`, or `password_salt**.
5. No interface may raise an uncaught exception to its caller; exceptions are uniformly converted at the service layer into a `success=False` response.

### 1.3 General Data and Parameter Validation Conventions
| Parameter Type | Constraint |
|---|---|
| `user_id` / `item_id` / `seller_id` | Must be positive integers (`1, 2, 3...`); negative numbers, 0, Boolean values, and non-numeric strings are all invalid |
| `category` (item category) | Must be one of the four whitelist values: `Books`、`Electronics`、`Clothing`、`Household goods`; case and wording must match exactly; values such as `Digital` and `Digital products` are invalid |
| `status` (item status) | Only two states: `For sale` and `Delisted` |
| `price` | Must be a number greater than 0; negative numbers, 0, empty strings, and alphabetic text are invalid; stored with two decimal places |
| `sort_by` (sort field) | Must be in the whitelist: `created_at`, `updated_at`, `price` |
| `descending` | Must be a Boolean |
| username | 3–20 characters, first character must be an English letter; only letters, digits, and underscores are allowed; uniqueness checks are case-insensitive |
| password | 8–32 characters, must contain at least one English letter and one digit; spaces are not allowed |
| nickname | 2–20 characters; Chinese characters, English letters, digits, and underscores; cannot be empty |
| item name | Must not be empty after trimming leading/trailing whitespace; maximum 20 characters |
| item description | Must not be empty after trimming leading/trailing whitespace; maximum 200 characters |
| image_path | May be an empty string; maximum 260 characters |
| Time fields | Uniform format: `YYYY-MM-DD HH:MM:SS` |

### 1.4 Error Message Style
- Login-related interfaces must use the unified failure message `Incorrect username or password`, without distinguishing between “user not found” and “incorrect password,” to avoid leaking account information.
- Permission-related failures must use the unified message `Not authorized to operate on this item`.
- Out-of-range or invalid input must specify the applicable field rule, for example, `Item category must be: Books, Electronics, Clothing, Household goods`.

---

## 2. Underlying Shared Storage Component: JsonArrayStore

Additional modules (favorites, intentions, messages) all depend on this component. Interface alignment is the core source of issues in this test round, so it is described in a separate section.
**Location**: `backend_zhang/json_store.py`

### 2.1 Available Public Methods

| Method | Signature | Description |
|---|---|---|
| load | `load(self) -> list[dict]` | Reads the entire JSON array file and returns a list of records; automatically creates the file and returns an empty list if it does not exist |
| save | `save(self, records: list[dict]) -> None` | Overwrites the JSON array file in its entirety |
| transaction | `transaction(self, mutator) -> Any` | Performs “read → modify → write” under a file lock and returns the value returned by `mutator`; this is the recommended approach |

### 2.2 Prohibited Usage (Errors Actually Encountered in This Test Round)
| Incorrect Usage | Consequence | Correct Usage |
|---|---|---|
| `store.read()` | `AttributeError: 'JsonArrayStore' object has no attribute 'read'` | `store.load()` |
| `store.write(records)` | `AttributeError: ... has no attribute 'write'` | `store.save(records)` |
| `store.get_all()` / `store.save_all()` | Attribute does not exist; raises `AttributeError` | `store.load()` / `store.save()` |
| `store.lock` | Attribute does not exist; raises `AttributeError` | The lock is the private member `store._lock`, and direct external access is not recommended; prefer `transaction()` |
| `from json_array_store import JsonArrayStore` | `ModuleNotFoundError: No module named 'json_array_store'` | `from backend_zhang.json_store import JsonArrayStore` |
| Using the class name `JsonStore` | `NameError: name 'JsonStore' is not defined` | The class is named `JsonArrayStore` |

### 2.3 Known Behavioral Characteristics
1. Atomic writes: creates a uniquely named temporary file in the same directory, calls `fsync`, then replaces the official file with `os.replace`; a crash midway will not corrupt the original file.
2. Corruption protection: JSON parsing failures raise `DataFileError`; the original file is **not automatically overwritten**.
3. A reentrant lock is reused within the process for each absolute path, ensuring mutual exclusion when multiple repository instances operate on the same file.
4. `JsonObjectStore` is a subclass used for files whose root node is a JSON object (such as the ID generator’s `items_meta.json`).

---

## 3. User Module: user_service
**Location**: `backend_zhang/user_service.py`
**Module-level default service**: `get_user_service()`; tests can switch to a temporary data file with `reset_user_service(data_file=...)`.

### 3.1 Interface Overview
| Function | Parameters | Return `data` Type | Description |
|---|---|---|---|
| register_user | username, password, nickname | dict | Registers a new user and returns redacted user information (id, username, nickname, created_at, updated_at) |
| login_user | username, password | dict | Validates login and returns user information with the same structure on success |
| get_user_by_id | user_id | dict | Retrieves user details by ID |
| get_public_user_info | user_id | dict | Minimal public information (id, username, nickname) |
| update_nickname | user_id, new_nickname | dict | Changes the nickname |
| change_password | user_id, old_password, new_password | None | Changes the password; the old password must be validated |
| user_exists | user_id | bool | Checks whether a user ID exists |

### 3.2 Key Business Rules
1. **register_user**
   - Username uniqueness checks are case-insensitive (`Student_01` and `student_01` are treated as the same username); on duplication, returns `success=False`, `message='Username already exists'`.
   - Passwords are stored using PBKDF2-HMAC-SHA256 with a random salt; plaintext passwords are neither persisted nor logged.
   - Registration fails if the password does not meet the rules, with a message specifying the rules.
2. **login_user**
   - If the username or password is empty, the user does not exist, or the password does not match, returns `success=False`, `message='Incorrect username or password'`.
   - Password verification uses a timing-safe comparison (`hmac.compare_digest`).
3. **change_password**
   - If the old password is incorrect, fails immediately with `Old password is incorrect`.
   - On success, also replaces the salt, immediately invalidating the old password.
4. **user_exists**
   - `data` is a Boolean: `True` means the user exists, and `False` means they do not; this interface is commonly used for pre-validation by the favorites, messages, and intentions modules.

---

## 4. Item Module: item_service
**Location**: `backend_zhang/item_service.py`
**Module-level default service**: `get_item_service()`; tests can isolate data with `reset_item_service(data_file=..., user_repository=..., deleted_file=..., meta_file=...)`.

### 4.1 Interface Overview
| Function | Parameters | Return `data` Type | Description |
|---|---|---|---|
| create_item | seller_id, name, category, price, description, image_path="" | dict | Lists an item and returns complete item information (including an automatically assigned ID) |
| get_all_items | include_removed=False, sort_by="created_at", descending=True | list[dict] | Gets the item list; by default, returns only items for sale |
| get_item_by_id | item_id, include_removed=False | dict | Retrieves a single item |
| get_items_by_seller | seller_id, include_removed=False, sort_by, descending | list[dict] | Retrieves all items belonging to a seller |
| update_item | item_id, seller_id, updated_data(dict) | dict | Updates an item posted by the caller |
| remove_item | item_id, seller_id | dict | Delists an item (For sale → Delisted) |
| restore_item | item_id, seller_id | dict | Relists an item (Delisted → For sale) |
| delete_item_permanently | item_id, seller_id | dict | Permanently deletes an item, first writing it to the deletion archive |
| search_items | keyword="", category="", include_removed=False, sort_by, descending | list[dict] | Searches by keyword and category in combination |
| item_exists | item_id, include_removed=True | bool | Checks whether an item ID exists |
| is_item_active | item_id | bool | Checks whether an item exists and is for sale |
| get_item_status | item_id | str | Returns `For sale` or `Delisted` |
| get_public_item_info | item_id | dict | Brief public information (id, seller_id, name, category, price, status) |
| is_item_deleted | item_id | dict | Checks the deletion archive; includes seven fields: item_id, deleted, alive, seller_id, name, status_before_delete, deleted_at |
| list_deleted_items | limit=50 (1–500) | list[dict] | Lists deleted-item archive entries in descending order by deletion time |

### 4.2 Key Business Rules
1. **create_item**
   - `category` must match one of the four whitelist values; otherwise, returns `success=False`, `message='Item category must be: Books, Electronics, Clothing, Household goods'`.
   - Rejects listing if `price` is negative or 0.
   - The user corresponding to `seller_id` must exist; otherwise, displays `Seller user does not exist`.
   - Item IDs are assigned by the independent ID generator `items_meta.json`, strictly increase, and are never reused after deletion.
2. **Permission requirements**
   - `update_item`, `remove_item`, `restore_item`, and `delete_item_permanently` all require the operator’s `seller_id` to match the item’s actual poster; otherwise, returns `Not authorized to operate on this item`.
3. **Status transitions**
   - Only two-way transitions are allowed: `For sale → Delisted` (`remove_item`), `Delisted → For sale` (`restore_item`).
   - Repeated delisting or relisting returns failure.
   - After delisting, the default `get_item_by_id` query returns `success=False`; pass `include_removed=True` to retrieve it.
4. **delete_item_permanently**
   - First writes an item snapshot to the `items_deleted.json` archive, then physically deletes the item; if archiving fails, deletion is not performed.
   - After deletion, `is_item_deleted` can retrieve the archive record, with `alive=False`.
5. **Search**
   - Keywords match item names and descriptions, case-insensitively.
   - An empty `category` or `category` set to “All” means no category filter.

---

## 5. Additional Modules: feature_du
**Location**: `feature_du/favorites.py`, `intentions.py`, `messages.py`
**Storage conventions**: All use `JsonArrayStore`, reading and writing via `.load()` / `.save()` or `.transaction(mutator)`. Data files are injected through the `data_file` constructor parameter; tests should point them to temporary files.

### 5.1 Interface Overview
| Class | Method | Parameters | Description |
|---|---|---|---|
| FavoriteService | toggle_favorite | user_id, item_id | Toggles favorite status: adds if not favorited; removes if already favorited |
| FavoriteService | get_user_favorites | user_id | Gets a list of favorited item information for a specified user |
| IntentionService | create_intention | user_id, item_id, seller_id | Submits a purchase intention and returns the new intention record |
| IntentionService | get_user_intentions | user_id | Gets all intention records where the user is the buyer or seller |
| MessageService | add_message | item_id, user_id, content | Adds a message to an item |
| MessageService | get_item_messages | item_id | Gets all messages for a specified item |

### 5.2 Key Business Rules
1. **Favorite `toggle_favorite`**
   - Pre-validation: the user must exist, and the item must exist and be for sale; otherwise, returns `User does not exist` or `Item does not exist or has been delisted`, respectively.
   - Repeated calls for the same `(user_id, item_id)` have “toggle” semantics: the first returns `Favorite added`, and the second returns `Favorite removed`.
2. **Intention `create_intention`**
   - Pre-validation: the buyer user must exist, the seller user must exist, and the item must be for sale.
   - **If the buyer’s `user_id` is the same as `seller_id` (submitting an intention for their own item), the request must be rejected** with `You cannot submit an intention for an item you posted yourself`.
   - Intention record fields: `intention_id`, `user_id`, `item_id`, `seller_id`, `status` (initially `pending`), `created_at`.
3. **Message `add_message`**
   - Rejects saving if the content is empty after trimming leading/trailing whitespace (including content consisting only of spaces or tabs), with `Message content cannot be empty`.
   - Pre-validation: the user must exist, and the item must be for sale.
   - Message record fields: `message_id`, `item_id`, `user_id`, `content`, `created_at`.
4. **Inter-module call constraints**
   - Additional modules **must not directly read or write** `users.json` / `items.json`.
   - User and item validation must always call `user_service.user_exists()`, `item_service.is_item_active()`, and `item_service.get_public_item_info()`.

### 5.3 Current Integration Status (Corrections Made in This Test Round)
| Item | Original Implementation | After Alignment |
|---|---|---|
| Read method | `self.store.read()` | `self.store.load()` |
| Write method | `self.store.write(msgs)` | `self.store.save(msgs)` |
| Lock access | `self.store.lock` | Changed to private `_lock`, or use `transaction()` directly |
| Storage class name | `JsonStore` | `JsonArrayStore` |
| Import statement | `from json_array_store import JsonArrayStore` | `from backend_zhang.json_store import JsonArrayStore` |

---

## 6. Interface Dependencies and Call Order
1. **Users must exist before items can be created**: `create_item` validates that the user corresponding to `seller_id` exists, so tests must first call `register_user` to create the seller account.
2. **Items must exist before they can be favorited, messaged, or used for intentions**: all three additional modules require the item to exist and be for sale.
3. **Intentions require all three parameters**: `user_id` (buyer), `seller_id` (seller), and `item_id` (item) must all be correct, and the buyer must not be the seller.
4. **Permissions depend on identity**: delisting, relisting, updating, and permanently deleting an item all validate ownership by `seller_id`.
5. **Test isolation requirements**: all services support overriding the default path using `data_file`; tests must use a separate temporary directory and must not write to the production data under `backend_zhang/data/`.

---

## 7. Issues Found During Interface Review and Testing
| No. | Location | Issue Description | Severity | Status |
|---|---|---|---|---|
| B-001 | All `feature_du` services | Accessing `self.store.lock`; this attribute does not exist (the private member is `_lock`), raising `AttributeError` | High | Fixed |
| B-002 | All `feature_du` services | Uses nonexistent class name `JsonStore`; the actual class is `JsonArrayStore`, raising `NameError` | High | Fixed |
| B-003 | messages.py | Calls nonexistent `store.read()` | High | Fixed |
| B-004 | messages.py | Calls nonexistent `store.write()` | High | Fixed |
| B-005 | messages.py | Incorrect import path `from json_array_store import ...`, causing `ModuleNotFoundError` | High | Fixed |