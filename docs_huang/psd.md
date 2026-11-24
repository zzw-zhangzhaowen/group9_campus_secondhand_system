# Project Specification Document (PSD)

**Project:** Campus Second-hand Marketplace (Campus Market, Design B)
**Course:** INT6181 Applied Programming with Python — Group Project
**Document version:** v1.0
**Status:** Specification baseline
**Owner:** HUANG BAIQI (documentation and reporting)
**Reviewers:** ZHANG ZHAOWEN (backend), GAO JINGYAN (GUI), DU YI (auxiliary services), ZHAO XIAOJUN (testing)
**Repository:** `group9_campus_secondhand_system`

---

## Contents

1. Purpose, scope and precedence
2. Project definition
3. Reference documents
4. Functional specification
5. Non-functional specification
6. Architecture and module specification
7. Interface specification
8. Data specification
9. User interface specification
10. Error handling specification
11. Security and privacy specification
12. Performance and capacity
13. Test and acceptance specification
14. Build, packaging and submission
15. Risks and mitigations
16. Known limitations and deferred work
17. AI use declaration
18. Change log and approval

---

## 1. Purpose, scope and precedence

This PSD turns the course requirements and the approved PRD into an implementation-level specification: what the system must do, how the modules are built, which interfaces and data structures are fixed, how quality is verified, and which evidence proves each requirement is met.

It is written for the team and for assessors who need to check the delivered code against a stated specification. The order of precedence is:

1. `INT6181 Group Project Requirements_v2.pdf` (course requirements);
2. `docs_huang/prd.md` (product requirements);
3. `contracts/backend_api.md` and `contracts/data_schema.md` (frozen technical contracts);
4. this PSD (implementation specification);
5. `README.md` and module notes (operating instructions and handover).

---

## 2. Project definition

### 2.1 Problem and target users

University students buy and sell used goods in closed campus communities, but informal group chats lose listings, mix buyers and sellers, and leave no history of enquiries. The project delivers a stand-alone desktop application where a student can register, publish items with a photo path, browse and search by category and price, manage their own listings, save items, comment publicly, and send purchase enquiries — without payment or cloud infrastructure.

Primary users: students acting as buyers and sellers on one campus. Secondary user: a demonstrator or assessor running the application locally.

### 2.2 Goals and success criteria

| Goal | Success criterion |
|---|---|
| Functional, purposeful application | A complete buy/sell workflow runs locally from `main.py` with no external service |
| Stand-alone and reproducible | Standard-library Python 3.10+ only; JSON data files; no database or network dependency |
| Calm, usable interface | One window, five main areas, explicit validation and failure messages, keyboard access to main pages |
| Defensible technical depth | Layered modules, a frozen interface contract, automated tests, code review and documented AI use |
| Honest delivery | Known limitations and deferred items are recorded; no unverified claim is presented as tested |

### 2.3 In scope

- Local user registration, sign-in, nickname change and password change.
- Item publishing, browsing, keyword/category search, sorting, details, editing, off-sale/relist and permanent deletion.
- Favorites, public item comments, purchase enquiries and a per-user activity log.
- Local JSON persistence with atomic writes, locking and corruption detection.
- Tkinter desktop interface with an isolated demo mode and a custom practice data directory.
- Automated backend and feature tests, supplementary frontend tests, test records and code review.

### 2.4 Out of scope

Online payments, order settlement, delivery, administrator roles, user deletion, image hosting or upload, cloud deployment, cross-device sync, multi-process concurrency, real-time chat, and any migration of historical data beyond the documented enum change.

### 2.5 Team and ownership

| Member | Role | Owned area | Key deliverables |
|---|---|---|---|
| ZHANG ZHAOWEN (A) | Backend and data | `backend_zhang/`, `contracts/` | User/item services, storage, validation, contracts |
| GAO JINGYAN (B) | GUI | `gui_gao/` | Tkinter pages, gateway, compatibility layer, frontend tests, handoff |
| DU YI (C) | Auxiliary features | `feature_du/` | Favorites, intentions, messages, logs |
| ZHAO XIAOJUN (D) | Testing | `test_zhao/` | Unit suite, API specification, test strategy and record |
| HUANG BAIQI (E) | Documentation | `docs_huang/`, root docs | PRD, PSD, code review record, report and slides |

---

## 3. Reference documents

| Document | Location | Role in this PSD |
|---|---|---|
| Course project requirements v2 | `INT6181 Group Project Requirements_v2.pdf` | Assessment criteria, submission rules, AI policy |
| Product requirements document | `docs_huang/prd.md` | Product scope, functional intent, acceptance criteria |
| Backend API contract v1.3 | `contracts/backend_api.md` | Frozen interface signatures, field rules, failure messages |
| Data format contract | `contracts/data_schema.md` | File ownership, record schemas, integrity rules |
| Group test record | `test_zhao/auto_test_record.md` | Execution history, defects and final regression |
| Frontend verification record | `gui_gao/TEST_REPORT.md` | Frontend test scope and results |
| Frontend handoff | `gui_gao/HANDOFF.md` | Integration boundaries and compatibility decisions |
| Code review record | `docs_huang/code_review/code_review.md` | Review findings, fixes and residual risks |
| Repository guide | `README.md` | Run instructions, directory map, current status |

---

## 4. Functional specification

Each requirement has a stable ID used by the test and traceability sections. "Backend" means the rule is enforced in `backend_zhang`; "GUI" means presentation only.

| ID | Requirement | Specified behaviour | Acceptance criterion |
|---|---|---|---|
| FR-01 | Registration | Username 3–20 characters, starts with an ASCII letter, letters/digits/underscore only, uniqueness case-insensitive. Password 8–32 characters with at least one letter and one digit, no spaces. Nickname 2–20 characters (Chinese, letters, digits, underscore). Password stored as PBKDF2-HMAC-SHA256 with a random salt; no password field returned. | Duplicate and invalid inputs are rejected with the contractual message; a valid registration returns user detail without `password_hash` / `password_salt`; a second registration with a different case of the same username fails. |
| FR-02 | Sign-in and session | Sign-in validates credentials and returns user detail. Failure always reports `Invalid username or password`, regardless of whether the account exists. The GUI holds the session locally and offers sign-out. | Correct credentials open the main window; wrong password and unknown account produce the same message; sign-out returns to the sign-in page. |
| FR-03 | Browse and search | The default listing hides `off_sale` items. Search matches name or description (trimmed keyword, case-insensitive for ASCII), optional category filter. Sort fields restricted to `created_at`, `updated_at`, `price`, ascending or descending. The GUI shows 12 items per page with empty states and retry. | Search results contain only matching, on-sale items; invalid sort field fails; page size and paging controls behave correctly at 0, 1 and many results. |
| FR-04 | Item details | Detail view shows name, category, price, description, seller nickname, status and timestamps, plus an edit link for the owner. Images preview PNG/GIF natively; JPEG is previewed when Pillow is present; a missing or unreadable image shows a placeholder. | Opening an item shows all stored fields; another user's item offers no edit action; missing images never crash the window. |
| FR-05 | Publish and edit | Item name and description are non-empty after trimming and at most 20 and 200 characters. Category is one of four enums. Price must be a number greater than 0, at most 100,000,000 and is rounded to two decimals then re-checked so a positive value cannot become 0.0. Image path is optional and at most 260 characters. Editing accepts only name, category, price, description and image path; `created_at` is preserved. | Invalid price/category/length are rejected with specific messages; a valid publish appears in the listing with `on_sale`; editing refreshes `updated_at` only; editing someone else's item fails with a permission error. |
| FR-06 | Own listing management | Only the seller may edit, take off sale, relist or permanently delete. Off-sale and relist are valid only from the opposite state. Permanent deletion writes a read-only snapshot to `items_deleted.json` first, then removes the live record; deletion is irreversible. | Repeated off-sale fails; relisting restores visibility; deleted items disappear from listings and detail queries; an archive record exists with the original title, price and deletion time. |
| FR-07 | Account management | The signed-in user may change the display name and password. A password change requires the current password and replaces the salt and hash. | Nickname change persists across restart; wrong current password is rejected; old password stops working and the new one succeeds. |
| FR-08 | Favorites | Toggle adds or removes a favorite for an existing, on-sale item. The saved list returns public item information for existing items, including off-sale ones. Off-sale or deleted saved entries remain visible as read-only history in the GUI; the service blocks toggling unavailable items. | Toggling twice restores the original state; the list contains only the current user's records; off-sale items cannot be newly saved; deleted items are shown from the archive and cannot be unsaved. |
| FR-09 | Public comments | Comments are public per item, non-empty after trimming and limited to 500 characters. The list returns all comments for the item, oldest to newest as stored. | A blank comment is rejected; a 501-character comment is rejected in the GUI; other users' comments are readable; comments survive restart. |
| FR-10 | Purchase enquiries | A buyer may submit an intention for an existing, on-sale item belonging to another user. Records start as `pending` and are listed for both buyer and seller. Self-enquiries and enquiries for unavailable items are rejected. No accept, reject, cancel or payment state exists. | Sending an enquiry shows it in both sent and received lists; an enquiry on one's own item fails with the contractual message; no action implies a transaction or a sold status. |
| FR-11 | Activity log | Key actions of the current user are recorded and displayed newest first. Passwords and comment bodies are never written to the log. If logging fails after a successful action, the GUI states that the action succeeded and warns against repeating it. | The log contains the user's own actions only; no password text appears; a simulated logging failure does not make the UI claim the action failed. |
| FR-12 | Data modes | Production uses `backend_zhang/data/`. The backend demo writes `demo_data/`, cleared before each run. The GUI `--demo` uses a temporary directory cleared on normal exit; `--data-dir` keeps a separate practice directory. | Demo and practice runs never read or modify production users or items; production data survives restart; concurrent processes on one directory are not supported and are documented as such. |

---

## 5. Non-functional specification

| ID | Area | Requirement | Verification |
|---|---|---|---|
| NFR-01 | Proper execution | Runs on Python 3.10+ from `main.py` with only the standard library; no crash on the defined workflows; GUI requires Tkinter and a desktop. | Backend self-check, unit suite, frontend suite and manual demo |
| NFR-02 | Ease of use | Single window, five main areas (Browse, My listings, Account, Community, List an item), labelled fields, inline hints, 12 items per page, minimum layout 1000 × 700, keyboard shortcuts for main pages. | Frontend UI tests and manual walkthrough |
| NFR-03 | Error handling | Every public interface returns `{"success", "message", "data"}`; invalid input yields a specific message; corrupt files yield an error and are never overwritten; business-expected states (no deletion record, item off sale) are successes with an explanatory message. | Unit tests, contract review, manual invalid-input checks |
| NFR-04 | Responsiveness | Service calls run on a single background worker so Tk stays responsive; submission and navigation are disabled while a request is in flight; image preview refuses files over 20 MB or 25 million pixels; animations stop when a page closes. | Frontend tests for duplicate-submit protection and cleanup; manual interaction |
| NFR-05 | Security and privacy | PBKDF2-HMAC-SHA256, 120,000 iterations, per-user random salt; timing-safe comparison; unified sign-in failure; public projections exclude password fields; `to_safe_dict` strips `password*`. | Unit and integration tests; code review |
| NFR-06 | Data integrity | Atomic writes (unique temp file, `fsync`, `os.replace`); one `RLock` per absolute path; strictly monotonic item IDs; archive-before-delete; invalid UTF-8 treated as corruption; rollback failures reported. | Unit tests for UTF-8, price rounding and rollback; review record |
| NFR-07 | Portability | Windows, macOS and Linux desktop targets; macOS `.command` launcher; path handling through `os.path`; no platform-specific shell dependency in the application. | macOS runs recorded; Windows logic verified 24 November 2026; Linux visual check pending |
| NFR-08 | Maintainability | Layered packages, public interfaces only across module boundaries, module docstrings, English UI strings and code comments, frozen contracts with a change log. | Code review and repository structure |
| NFR-09 | Testability | Data paths injectable; service resets for tests; all tests use temporary directories; frontend tests use temporary data. | `python -m unittest test_zhao.test_all`; frontend suite |
| NFR-10 | Documentation and review | README, PRD, PSD, contracts, test strategy/record, frontend handoff and a code review covering all modules. | Documentation index in `README.md`; review record |

---

## 6. Architecture and module specification

### 6.1 Layering

```
GUI (gui_gao) / auxiliary services (feature_du)
        │  GUI calls public services only; feature_du reuses json_store and owns its files
        ▼
Service layer      user_service.py / item_service.py
        ▼
Business rules     validators → permissions → state transitions → response
        ▼
Data access        user_repository / item_repository / item_archive / id_sequence → json_store
        ▼
JSON files         users.json / items.json / items_deleted.json / items_meta.json
                   favorites.json / messages.json / intentions.json / logs.json
```

Rules:

- Only public service functions cross module boundaries; private helpers (leading underscore) are not imported outside their module.
- The GUI never writes JSON directly and never reimplements permissions, search or state changes.
- `feature_du` may read user/item facts only through the interfaces listed in Section 7.4 and must not open `users.json` or `items.json`.
- `items_meta.json` is read and written only by `id_sequence.py`; the archive only by `item_archive.py`.

### 6.2 Module responsibilities

| Module | Owner | Files | Responsibility | Public surface |
|---|---|---|---|---|
| `backend_zhang` | A | `config`, `exceptions`, `response`, `json_store`, `security`, `validators`, `user_repository`, `item_repository`, `item_archive`, `id_sequence`, `user_service`, `item_service` | Storage, validation, permissions, state transitions, ID allocation, deletion archive | User and item functions; `UserService` / `ItemService` classes; reset helpers |
| `feature_du` | C | `favorites.py`, `intentions.py`, `messages.py`, `logs.py` | Favorites, enquiries, public comments, activity log; own JSON files | Four service classes |
| `gui_gao` | B | `app.py`, `gateway.py`, `feature_gateway.py`, `localization.py`, `lifecycle.py`, page modules, `theme`, `widgets`, `validation`, `demo.py` | Presentation, navigation, background calls, English labels, demo data | `main()`, page classes, `Gateway` |
| `test_zhao` | D | `test_all.py`, `API_spec.md`, `test_strategy.md`, `auto_test_record.md` | Automated interface tests and test documentation | `unittest` suite |
| `docs_huang` | E | `prd.md`, `psd.md`, `code_review/` | Requirements, specification, review, report | Documents |

### 6.3 Runtime flow

1. `main.py` selects self-check, demo or GUI mode.
2. The GUI builds a `Gateway` for production, temporary demo data or a practice directory.
3. Page actions call gateway methods, which call public services on a worker thread.
4. Services validate input, check permissions, mutate JSON through the store and return a uniform result.
5. The page renders success, a specific failure message, or a retry state; activity logging runs where specified.

---

## 7. Interface specification

### 7.1 Uniform response

Every public interface returns:

```python
{"success": True | False, "message": str, "data": <dict | list | bool | None>}
```

`success` and `message` are the contract for callers; `data` is deep-copied on return. Business-expected states (for example, no deletion record) still return `success=True` with an explanatory message and are asserted through `data`.

### 7.2 User interfaces

| Interface | Parameters | `data` on success |
|---|---|---|
| `register_user` | username, password, nickname | User detail without password fields |
| `login_user` | username, password | User detail without password fields |
| `get_user_by_id` | user_id | User detail |
| `get_public_user_info` | user_id | `{id, username, nickname}` |
| `update_nickname` | user_id, new_nickname | User detail |
| `change_password` | user_id, old_password, new_password | `None` |
| `user_exists` | user_id | `True / False` |
| `to_safe_dict` | user dict | Copy with every `password*` field removed |

Failure messages include `Username already exists`, the username/password/nickname rule messages, `Invalid username or password`, `User does not exist` and `Old password is incorrect`.

### 7.3 Item interfaces

| Interface | Parameters | `data` on success |
|---|---|---|
| `create_item` | seller_id, name, category, price, description, image_path="" | Item detail |
| `get_all_items` | include_removed=False, sort_by="created_at", descending=True | Item list |
| `get_item_by_id` | item_id, include_removed=False | Item detail |
| `get_items_by_seller` | seller_id, include_removed=False, sort_by, descending | Item list |
| `update_item` | item_id, seller_id, updated_data | Item detail |
| `remove_item` / `restore_item` | item_id, seller_id | Item detail with new status |
| `delete_item_permanently` | item_id, seller_id | `{"id": item_id}` |
| `search_items` | keyword, category, include_removed=False, sort_by, descending | Item list |
| `item_exists` | item_id, include_removed=True | `True / False` |
| `is_item_active` | item_id | `True / False` |
| `get_item_status` | item_id | `"on_sale"` / `"off_sale"` |
| `get_public_item_info` | item_id | `{id, seller_id, name, category, price, status}` |
| `is_item_deleted` | item_id | Seven-field archive summary |
| `list_deleted_items` | limit=50 (1–500) | Snapshots, newest first |

### 7.4 Auxiliary service interfaces

| Service | Method | Parameters | Success message |
|---|---|---|---|
| `FavoriteService` | `toggle_favorite` | user_id, item_id | `Item favorited successfully` / `Item removed from favorites` |
| | `get_user_favorites` | user_id | `Favorites retrieved successfully` |
| `IntentionService` | `create_intention` | user_id, item_id, seller_id | `Purchase intention submitted successfully` |
| | `get_user_intentions` | user_id | `Intentions retrieved successfully` |
| `MessageService` | `add_message` | item_id, user_id, content | `Message added successfully` |
| | `get_item_messages` | item_id | `Messages retrieved successfully` |
| `LogService` | `log_action` | user_id, action_type, detail="" | `Log recorded successfully` |
| | `get_logs` | user_id=None | `Logs retrieved successfully` |

Auxiliary services may call only `user_exists`, `item_exists`, `is_item_active`, `is_item_deleted`, `get_public_item_info`, `get_item_status`, `get_public_user_info` and `to_safe_dict`.

### 7.5 Permission matrix

| Operation | Requirement |
|---|---|
| Browse, search, view details | Any signed-in user; on-sale items for the default listing |
| Publish | Signed-in user becomes the seller |
| Edit / off-sale / relist / delete | The recorded seller only; backend enforced |
| Save / comment / enquiry | Signed-in user; item must exist and be on sale for new actions |
| Enquiry on own item | Rejected |
| Account changes | The signed-in user only |
| Read archive | Any caller through `is_item_deleted` / `list_deleted_items`; never by opening the file |

### 7.6 Interface evolution

Versions v1.0–v1.3 and the enum change are recorded in `contracts/backend_api.md` Section 6. Additions are read-only; no breaking change was introduced after v1.0. The GUI maps display labels to the current enums without rewriting stored data.

---

## 8. Data specification

### 8.1 Files and ownership

| File | Root type | Owner | Purpose |
|---|---|---|---|
| `users.json` | Array | backend | Accounts |
| `items.json` | Array | backend | Live listings |
| `items_deleted.json` | Array | backend | Append-only deletion archive |
| `items_meta.json` | Object | backend (`id_sequence`) | Item ID counter |
| `favorites.json` | Array | feature_du | Favorite records |
| `messages.json` | Array | feature_du | Item comments |
| `intentions.json` | Array | feature_du | Purchase enquiries |
| `logs.json` | Array | feature_du | Activity records (`system_logs.json` through the GUI adapter) |

### 8.2 Record schemas

- User: `{id, username, password_hash, password_salt, nickname, created_at, updated_at}`.
- Item: `{id, seller_id, name, category, price, description, image_path, status, created_at, updated_at}`.
- Archive snapshot: `{item_id, seller_id, name, category, price, description, image_path, status_before_delete, created_at, updated_at, deleted_at, deleted_by}`.
- Counter: `{next_item_id}`.
- Favorite: `{user_id, item_id}`.
- Comment: `{message_id, item_id, user_id, content, created_at}`.
- Enquiry: `{intention_id, user_id, item_id, seller_id, status: "pending", created_at}`.
- Log: `{log_id, user_id, action_type, detail, timestamp}`.

### 8.3 Enumerations

| Enum | Allowed values |
|---|---|
| Category | `books`, `electronics`, `clothing`, `household` |
| Status | `on_sale`, `off_sale` |
| Enquiry status | `pending` |
| Sortable fields | `created_at`, `updated_at`, `price` |

Display labels are Books, Electronics, Clothing and Home & Living; Available and Off sale for statuses.

### 8.4 State transitions

```
on_sale  --remove_item-->  off_sale
off_sale --restore_item--> on_sale
any      --delete_item_permanently--> archived, removed from items.json
```

Repeated transitions are rejected (`Item is already off sale` / `Item is already on sale`). Deletion does not require off-sale first and never cascades into favorites, comments or enquiries; each module decides how to show history.

### 8.5 Identifier policy

Item IDs are positive integers issued by `items_meta.json`, with the allocation floor `max(counter, highest live ID + 1, highest archived item_id + 1)`. IDs are strictly monotonic and never reused, so an archived or favorite `item_id` cannot silently point to a new item. A failed write may skip a number, which is accepted. User IDs use the highest live ID + 1; users cannot be deleted in this version.

### 8.6 Integrity rules

- UTF-8 with `ensure_ascii=False`, timestamps in `YYYY-MM-DD HH:MM:SS`.
- Missing file → the parent directory is created and an empty value is written (`[]` or `{}`).
- Corrupt file, including invalid UTF-8 → explicit failure, original file preserved, no silent reset.
- Writes use a unique temporary file in the same directory, `fsync`, then `os.replace`.
- One lock per absolute path serialises writers within a process; cross-process writers are out of scope.
- Archive write failure aborts deletion; a rollback failure is reported and requires manual reconciliation.

---

## 9. User interface specification

### 9.1 Navigation and layout

One window with a top navigation bar, page content and a status footer. Main destinations: Browse, My listings, Account, Community, List an item. The minimum supported layout is 1000 × 700. Case-sensitive shortcuts (`Command` on macOS, `Control` elsewhere): 1 Browse, 2 My listings, 3 Account, 4 Community, N List an item. Tab moves focus; Enter submits sign-in and search forms.

### 9.2 Pages

| Page | Main functions | Services used |
|---|---|---|
| Sign in / Register | Validation, duplicate-name feedback, demo credentials, session cleanup | `login_user`, `register_user` |
| Browse | Keyword/category filters, sorting, 12 per page, empty and retry states | `search_items`, `get_public_user_info` |
| Item details | Photo preview, fields, seller, owner edit, save/comment/enquiry actions | `get_item_by_id`, `get_public_user_info`, feature services |
| List / Edit item | Live preview, field readiness, unsaved-change prompt, photo check | `create_item`, `update_item` |
| My listings | Own items, edit, off-sale, relist, confirmed deletion | `get_items_by_seller`, `remove_item`, `restore_item`, `delete_item_permanently` |
| Account | Profile preview, counts, nickname and password change, reduced-motion setting | `update_nickname`, `change_password` |
| Saved items | Availability filter, unsave when available, read-only history | `FavoriteService`, `is_item_deleted` |
| Comments | Public threads, 500-character counter and draft warning | `MessageService` |
| Enquiries | Sent/received tabs, duplicate and self-enquiry guards | `IntentionService` |
| Activity log | Current user's actions, newest first, local search | `LogService` |

### 9.3 Validation and feedback

The GUI validates before calling a service and displays the failure message returned by the backend; the backend remains authoritative. Errors appear inline or in a page-level notice, not as raw exceptions. Unsaved item edits prompt before navigation. Destructive deletion requires explicit confirmation. Success is shown only after a successful service result.

### 9.4 Images

PNG and GIF preview through Tk; JPEG preview requires Pillow and is optional. Files over 20 MB or 25 million pixels are refused for preview. Only the path is stored; moving the project without the images shows placeholders. The Pillow zoom path has a known open defect recorded as Issue 3-1 in the code review.

### 9.5 Modes and data locations

| Mode | Command | Data location |
|---|---|---|
| Production | `python main.py --gui` | `backend_zhang/data/` |
| Backend demo | `python main.py --demo` | `demo_data/`, cleared per run |
| GUI demo | `python -m gui_gao --demo` | Temporary directory, cleared on normal exit |
| Practice | `python -m gui_gao --data-dir <dir>` | The chosen directory |

### 9.6 Language and accessibility

The interface, validation text, demo content and comments are English; user-entered text keeps its original language. Chinese characters are accepted in nicknames. Animations respect reduced motion, can be paused and release callbacks on page destruction. Decorative route markers and the activity clock do not represent transaction state or real time.

---

## 10. Error handling specification

| Layer | Responsibility | Example |
|---|---|---|
| Validation | Field-level rules with specific messages | `Password must contain at least one digit` |
| Permission | Ownership checks | `Permission denied for this item` |
| State | Illegal transitions | `Item is already off sale` |
| Storage | Missing, corrupt or unwritable files | `Data file is corrupt: items.json ...` |
| Feature services | Existence and availability checks | `Item does not exist or is off shelf` |
| GUI | Presentation, retry and duplicate-submit protection | Inline error, retry button, disabled controls |

Rules: exceptions are not used for ordinary business branching; unexpected exceptions are converted to failures with a readable message; passwords and raw file contents never appear in messages or logs; a failure after a partial write is reported and never swallowed.

---

## 11. Security and privacy specification

- Passwords are never stored or returned in plaintext; only PBKDF2-HMAC-SHA256 hashes with per-user salts are persisted.
- Password comparison uses `hmac.compare_digest`.
- Sign-in does not reveal whether an account exists.
- Public projections expose `id`, `username`, `nickname` only; detail views exclude password fields.
- Logging excludes passwords and comment bodies; `to_safe_dict` provides an explicit sanitisation step.
- The application is local and unauthenticated at the OS level; file-system access is the effective trust boundary. Data files should not be committed or shared with real personal data.

---

## 12. Performance and capacity

| Aspect | Specification |
|---|---|
| Startup | Backend self-check and GUI start should complete without noticeable delay on a standard laptop; no formal benchmark is claimed |
| Interaction | All service calls run serially off the Tk thread; controls are disabled during a request to prevent duplicates |
| Listing volume | JSON arrays scanned linearly; suitable for a campus prototype with hundreds of records; no index or pagination at the storage layer |
| Rendering | 12 cards per page; resizing is debounced (about 120 ms); animations are short and stop on page close |
| Images | Preview guard at 20 MB / 25 million pixels |

Scalability beyond a few thousand records, concurrent processes and network access are outside this specification.

---

## 13. Test and acceptance specification

### 13.1 Levels

| Level | Scope | Tool |
|---|---|---|
| Backend self-check | Core user and item flows, 19 checks, temporary data | `python main.py` |
| Unit and integration tests | User, item, favorites, intentions, messages plus review regressions, 31 cases | `python -m unittest test_zhao.test_all` |
| Supplementary frontend tests | Gateway, localization, features, UI, 56 cases (20 Tk-window cases require a desktop) | `python -m unittest discover -s gui_gao/tests` |
| Manual GUI testing | Navigation, rendering, image preview, animation controls | Manual walkthrough |
| Code review | Frontend, backend, integration, test suite | `docs_huang/code_review/code_review.md` |

### 13.2 Verified results (24 November 2026)

| Run | Result |
|---|---|
| Backend self-check | 19 of 19 checks passed |
| Group unit tests | 31 of 31 passed, 4.106 s |
| Frontend tests (Windows) | 56 run, 36 passed, 20 Tk-window cases skipped without an interactive desktop, 18.115 s |
| Frontend tests (macOS, 13 November 2026) | 56 of 56 passed, 11.355 s |

### 13.3 Test allocation

| Suite | Count | Coverage |
|---|---|---|
| `TestUserModule` | 8 | Registration, duplicate, weak password, login, wrong password, nickname, password change, existence |
| `TestItemModule` | 6 | Publish, negative price, keyword search, off-sale/relist, deletion, edit |
| `TestFeatureC` | 9 | Favorite add/remove/list, intention create/list/self-guard, comment add/blank/list |
| Review regressions | 8 | Price-rounding boundary (3), invalid UTF-8 (3), archive rollback (2) |

### 13.4 Acceptance criteria

The delivery is acceptable for this iteration when:

1. every FR in Section 4 is demonstrated in the GUI or by its automated case;
2. all 31 unit cases and the 19 self-checks pass on a clean checkout;
3. the frontend suite passes on a desktop machine, with documented skips only where no desktop exists;
4. no blocking defect from the code review remains open, and residual risks are listed in Section 16;
5. data isolation holds: tests, demo and production never share files;
6. `README.md` states how to run the project and matches the repository.

### 13.5 Course criterion mapping

| Course criterion (weight) | Evidence in this project |
|---|---|
| Originality and practicality (10%) | Campus-only second-hand workflow, stand-alone local application, realistic listing/enquiry features |
| Usability (10%) | Single-window GUI, inline validation, uniform error messages, worker thread, demo mode |
| Technical depth (55%) | Layered modules, frozen interface and data contracts, 31 automated tests, 56 frontend tests, code review, documentation |
| Presentation (20%) | Demonstrates key flows with fictional data; no payment claim; evidence files linked from README |
| Individual report (5%) | Each member documents their own module, challenges and decisions |
| AI bonus | AI used in specification, code, illustrations, tests, documentation and review, with disclosure |

Against the rubric levels (Minimum → Marginal → Satisfactory → Good → Excellent), the delivered evidence targets **Excellent**: modularity, specification, testing, documentation and code review are all present.

---

## 14. Build, packaging and submission

- **Runtime:** Python 3.10+; standard library only for the application; Pillow optional for JPEG previews and the illustration generator.
- **Entry point:** `main.py` with `--check` (default), `--demo` and `--gui`.
- **Instructions:** `README.md` (run commands, accounts, directory map, limitations).
- **Package:** source, data files and README zipped as `group9_project.zip` (course template: `groupN_project.zip`).
- **Presentation:** `group9_presentation.pptx` (`groupN_presentation.pptx`).
- **Individual reports:** one PDF per member, at least 600 words, structured as introduction, project description, personal contributions, challenges, lessons and conclusion.
- **Version control:** commit by directory, never `git add .`; production JSON and demo output stay untracked.

---

## 15. Risks and mitigations

| Risk | Impact | Mitigation | Status |
|---|---|---|---|
| JSON corruption or interrupted write | Lost or unreadable data | Atomic replace, corruption detection, no overwrite, repair guidance | Mitigated |
| Concurrent processes on one directory | Lost updates | Documented as unsupported; per-path lock within one process | Accepted |
| Deleted item ID reuse (historical data) | Wrong item shown in saved history | v1.3 monotonic counter; `alive` flag for legacy data | Mitigated |
| Archive growth | Slower archive queries | Limit 1–500 per call; cleanup deferred | Accepted |
| Platform differences (fonts, Tk rendering) | Visual defects on another machine | Font fallback, minimum layout, macOS and Windows runs recorded | Partially mitigated |
| Pillow-dependent zoom defect | Crash when zooming with Pillow | Defect recorded (Issue 3-1); fix deferred, path documented | Open |
| Incomplete validation in auxiliary services | Over-long comments or malformed IDs reach storage | GUI enforces 500 characters; service-level validation deferred | Accepted |
| Duplicate intention IDs in extreme cases | Two enquiries share an ID | Serialised transaction; review risk accepted, fix deferred | Accepted |
| Log module not covered by unit tests | Undetected regression in activity log | Manual and GUI checks only; dedicated tests deferred | Accepted |
| Single demonstration machine failure | Failed live demo | Isolated demo mode with fictional data; README run steps | Mitigated |

---

## 16. Known limitations and deferred work

1. Single-machine, single-process design; no concurrent writers, network access or cloud backup.
2. No user deletion, administrator role, payment, order settlement or delivery.
3. `image_path` stores a string only; no upload, existence check or processing.
4. The deletion archive grows without cleanup and is queried with a 1–500 limit per call.
5. A failed ID write can skip a number; a corrupt counter blocks publishing until repaired.
6. The Pillow-backed image zoom defect remains open (code review Issue 3-1).
7. Auxiliary services validate existence and availability but not all field lengths (the 500-character comment limit is enforced by the GUI adapter; the intention ID allocation remains a reviewed risk).
8. `LogService` has no dedicated automated tests; the activity log is verified manually.
9. Windows and Linux visual rendering have not been inspected; the Windows run covered logic with Tk-window tests skipped.
10. Historical data using the old Chinese category/status values requires manual migration; no automatic conversion is provided.

Deferred items are recorded here and in the code review rather than presented as delivered behaviour.

---

## 17. AI use declaration

Generative AI (Codex) assisted with design proposals, initial implementations, illustration generation, test scaffolding, documentation and the English conversion. All members selected the functional scope, reviewed generated code, ran the tests recorded in this repository and remain responsible for the delivered result. AI assistance is disclosed in `README.md`, the frontend handoff and test report, and the code review, in line with the course AI policy.

---

## 18. Change log and approval

| Version | Date | Change | Author |
|---|---|---|---|
| v1.0 | 24 November 2026 | First PSD: requirements, architecture, interfaces, data, UI, quality, acceptance and risks aligned with the delivered repository | HUANG BAIQI |

Approval requires review by the four module owners. Any later change to an interface or data schema must be recorded in `contracts/` first and then reflected here.
