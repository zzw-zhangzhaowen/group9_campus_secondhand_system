# Campus Second-hand Marketplace (group9_campus_secondhand_system)

A **prototype** campus second-hand marketplace built with Python, Tkinter and local JSON files. It has no real payments and no cloud deployment.

> Repository status (24 November 2026): the backend `backend_zhang`, the Design B "Campus Market" frontend `gui_gao`, the auxiliary services `feature_du`, the group test suite `test_zhao` and the documentation and review folder `docs_huang` are all in the repository.
> Verified on 24 November 2026 on Windows with Python 3.13.18: the backend self-check passed 19 checks; `python -m unittest test_zhao.test_all` ran 31 tests and all passed (4.1 s); the frontend suite ran 56 tests, 36 passed and 20 Tk-window cases were skipped because that session had no interactive desktop (18.1 s).


See the [frontend guide](#frontend-guide) for frontend instructions, [gui_gao/HANDOFF.md](gui_gao/HANDOFF.md) for handover notes, [gui_gao/TEST_REPORT.md](gui_gao/TEST_REPORT.md) for frontend checks and [test_zhao/auto_test_record.md](test_zhao/auto_test_record.md) for the group test record.

---

## 1. Directory layout

The tree below reflects the repository as it stands. Runtime JSON under `backend_zhang/data/` and `demo_data/` is not committed.

```
campus-secondhand/
├── backend_zhang/            # Core backend (ZHANG ZHAOWEN)
│   ├── __init__.py
│   ├── config.py             # Data paths, categories, statuses, sort whitelist, hashing parameters
│   ├── exceptions.py         # Shared exception types
│   ├── response.py           # Uniform result format: success() / failure()
│   ├── json_store.py         # Data access: atomic writes, file locks, corruption detection, transaction()
│   ├── security.py           # Password hashing (PBKDF2 + random salt)
│   ├── validators.py         # Field validation
│   ├── user_repository.py    # User data access
│   ├── item_repository.py    # Item data access
│   ├── item_archive.py       # Read-only archive of deleted items (items_deleted.json)
│   ├── id_sequence.py        # Item ID counter (items_meta.json, strictly monotonic)
│   ├── user_service.py       # User service layer: public functions + UserService
│   ├── item_service.py       # Item service layer: public functions + ItemService
│   └── data/                 # Runtime data (production JSON is gitignored)
│       ├── users.example.json
│       ├── items.example.json
│       ├── items_deleted.example.json
│       ├── items_meta.example.json
│       └── users.json …      # Locally generated production data, not committed
├── feature_du/               # Auxiliary services (DU YI)
│   ├── __init__.py
│   ├── favorites.py          # FavoriteService: toggle_favorite / get_user_favorites
│   ├── intentions.py         # IntentionService: create_intention / get_user_intentions
│   ├── messages.py           # MessageService: add_message / get_item_messages
│   └── logs.py               # LogService: log_action / get_logs
├── gui_gao/                  # Tkinter interface (GAO JINGYAN)
│   ├── __init__.py           # main(), called by the root entry point
│   ├── __main__.py           # Standalone demo / custom data directory entry
│   ├── app.py                # Window, navigation, background tasks, error feedback
│   ├── gateway.py            # Calls the public backend services
│   ├── feature_gateway.py    # Module-local frontend compatibility loader for feature_du
│   ├── localization.py       # English labels and current backend enum mapping
│   ├── lifecycle.py          # Releases widget-owned Tcl variables on page destruction
│   ├── interaction_page.py   # Saved items / comments / enquiries / personal activity
│   ├── login_page.py
│   ├── home_page.py
│   ├── item_page.py
│   ├── publish_page.py
│   ├── account_page.py
│   ├── page_design.py        # Page banners, sign-in illustration and statistic shortcuts
│   ├── theme.py / widgets.py / validation.py
│   ├── demo.py               # Fictional demo data created through service calls
│   ├── assets/               # Eight original item illustration PNGs
│   ├── assets/scenes/        # Nine layered page illustrations (*-base / *-float, 840 × 600)
│   ├── tools/                # Optional illustration generator (not needed to run the frontend)
│   ├── tests/                # Supplementary frontend tests (test_ui / test_gateway / test_features / test_localization)
│   ├── launch_demo.command   # macOS isolated demo launcher
│   ├── 启动演示.command       # Chinese-named compatibility shortcut to the historical launcher
│   ├── .gitignore
│   └── HANDOFF.md / TEST_REPORT.md / REQUIREMENTS_CHECK.md
├── test_zhao/                # Group unit tests and test documentation (ZHAO XIAOJUN)
│   ├── __init__.py
│   ├── test_all.py            # unittest entry: users / items / favorites / intentions / messages + review regressions
│   ├── API_spec.md            # API specification (4 November 2026)
│   ├── test_strategy.md       # Test strategy (5 November 2026)
│   ├── auto_test_record.md    # Test record: run-by-run log, five blocking defects (B-001 to B-005), final regression
│   └── image.png / image-1.png / image-2.png   # Test-run screenshots
├── docs_huang/               # Documentation and reviews (HUANG BAIQI)
│   ├── prd.md                # PRD v1.0 (English edition, 19 November 2026, 17 chapters)
│   ├── code_review.md    # Frontend, backend, integration and group-test reviews
│   ├── group_plan.md         # group plan
│   ├── AI_usage.md           # AI usage statement
│   └── psd.md                # Project Specification Document
├── contracts/
│   ├── backend_api.md        # Backend API contract v1.3
│   └── data_schema.md        # Data format contract
├── demo_data/                # Demo data (created by python main.py --demo, gitignored)
├── .gitignore
├── README.md
└── main.py                   # Entry point: self-check by default / --demo / --gui
```

---

## 2. Running the application

Python 3.10 or later is required. The repository was verified on Windows with Python 3.13.18 (24 November 2026). The GUI needs Tkinter and a graphical desktop; core features and PNG/GIF previews use only the standard library, so no `pip install` is needed. If the local `python3` is not a suitable version, use another installed Python 3.10+ interpreter, and on Windows replace `python3` with `python`. Run all commands from the repository root.

```bash
# Backend self-check (temporary data, 19 checks, production data untouched)
python3 main.py

# Backend business demo (writes demo_data/, cleared before each run)
python3 main.py --demo

# Launch the production GUI (gui_gao.main() is connected)
python3 main.py --gui

# Recommended first step: isolated frontend demo (temporary data, cleared on normal exit)
python3 -m gui_gao --demo

# Keep practice data in a separate directory (optional)
python3 -m gui_gao --data-dir ./my_practice_data

# Group unit tests (31 cases, temporary directory, production data untouched)
python3 -m unittest test_zhao.test_all

# Supplementary frontend tests (Tk-window cases need a desktop and are skipped without one)
python3 -m unittest discover -s gui_gao/tests
```

Production mode has no preset accounts, so register first. The isolated frontend demo account is `gao_demo` with password `Campus123`; the other demo users and items are fictional. The frontend demo uses a system temporary directory and is separate from the backend `main.py --demo`; a custom practice directory keeps its data, so do not commit its JSON files.

Mac: open `gui_gao/launch_demo.command`. The historical `gui_gao/启动演示.command` remains a compatibility shortcut. The optional `.app` launcher was removed from version control because it opened duplicate windows and duplicated existing entry points; the command line and `.command` launches both remain and require local Python/Tkinter. JPEG previews can be enhanced by Pillow when it is already installed, but Pillow is not a required dependency. See the frontend guide below.

On the first call to any interface, `users.json`, `items.json` and `items_deleted.json` under `backend_zhang/data/` are created as empty arrays `[]`, and `items_meta.json` is created as `{"next_item_id": 1}`.

---

## 3. Architecture

```
GUI / feature_du
      │  The GUI calls public interfaces only; feature_du reuses json_store's
      │  atomic storage and manages its own data files
      ▼
Service layer   user_service.py / item_service.py
      ▼
Business rules  validation (validators) → permissions → state transitions → result (response)
      ▼
Data access     user_repository / item_repository / item_archive / id_sequence → json_store
      ▼
JSON files      users.json / items.json / items_deleted.json (read-only archive) /
                items_meta.json (ID counter), plus the auxiliary services'
                favorites.json / intentions.json / messages.json / logs.json
```

- Public service functions always return `{"success", "message", "data"}`.
- Internal helpers start with an underscore (`_load_users`, `_save_users`, `_hash_password`, `_verify_password`, `_find_user_internal`, `_find_item_internal` and similar) and are **not exposed**.
- Permission checks, search logic and state changes run in the backend; the GUI must not reimplement them.

---

## 4. Interfaces (contracts in `contracts/backend_api.md` and `contracts/data_schema.md`, per-interface detail in `test_zhao/API_spec.md`)

Users: `register_user` / `login_user` / `get_user_by_id` / `get_public_user_info` /
`update_nickname` / `change_password` / `user_exists` / `to_safe_dict`

Items: `create_item` / `get_all_items` / `get_item_by_id` / `get_items_by_seller` /
`update_item` / `remove_item` / `restore_item` / `delete_item_permanently` /
`search_items` / `item_exists` / `is_item_active` / `get_item_status` / `get_public_item_info` /
`is_item_deleted` / `list_deleted_items`

Auxiliary services (`feature_du/`): `FavoriteService.toggle_favorite` / `get_user_favorites`,
`IntentionService.create_intention` / `get_user_intentions`,
`MessageService.add_message` / `get_item_messages`,
`LogService.log_action` / `get_logs`

`reset_user_service()` / `reset_item_service()` let tests and demos switch data directories without changing business rules.

```python
from backend_zhang.user_service import login_user
from backend_zhang.item_service import search_items, is_item_active, is_item_deleted

result = login_user("student_01", "abcd1234")
if result["success"]:
    print(result["data"]["nickname"])

if is_item_active(1)["data"]:
    ...  # The item exists and is on sale, so an enquiry may be sent

record = is_item_deleted(2)["data"]   # Was the item deleted? Show its historical title
if record["deleted"]:
    print(record["name"], record["deleted_at"])
```

### 4.1 Auxiliary services (feature_du — DU YI)

| Module | File | Public methods | Default data file (when `data_file` is omitted) |
|---|---|---|---|
| Favorites | `favorites.py` | `toggle_favorite` / `get_user_favorites` | `backend_zhang/data/favorites.json` |
| Intentions | `intentions.py` | `create_intention` / `get_user_intentions` | `backend_zhang/data/intentions.json` |
| Messages | `messages.py` | `add_message` / `get_item_messages` | `backend_zhang/data/messages.json` |
| Logs | `logs.py` | `log_action` / `get_logs` | `backend_zhang/data/logs.json` |

- All four services store through `JsonArrayStore`, keeping atomic replacement and file locking, and return the same `{"success", "message", "data"}` shape.
- The frontend compatibility layer (`gui_gao/feature_gateway.py`) writes logs to `system_logs.json` in the selected data directory; the other three keep their own file names.
- The intention service currently creates and reads `pending` records only. It has no accept, reject, cancel or payment states.

Frontend integration with root `feature_du/` uses Gao's module-local service bindings and storage facade. This preserves isolated demo/practice data without changing teammate source or global defaults. The four Community pages call the real services. Current restrictions and remaining coordination are recorded in [HANDOFF](gui_gao/HANDOFF.md).

### 4.2 Frontend (gui_gao — GAO JINGYAN)

13 November Tkinter update: platform font fallback, rounded B-style banners and statistic panels, refined login/listing layouts and visible animation controls. Widget-owned Tcl variables are released on the UI thread during destruction. All 56 frontend tests passed with automatic garbage collection enabled on macOS / Python 3.12 (11.355 seconds). See `gui_gao/TEST_REPORT.md` for details.

- English pages, validation, error messages, demo content, code comments and module documentation. Updated on 10 November 2026 against upstream `7ef1a95`.
- Connected: registration/sign-in, category/keyword search, price sorting, pagination, item details, publishing/editing, own-item off-sale/relist/delete actions, display-name/password updates, saved items, public comments, sent/received enquiries and personal activity.
- Design B retains illustrated sections, sign-in password visibility, profile summaries, live listing previews, image zoom, filters, checklists and comment counts. The enquiry marker moves through 1 → 2 → 3; clock hands move in steps. Animations can be paused, respect reduced motion and clean up when pages close.
- Display labels map to current backend enums: `books`, `electronics`, `clothing`, `household`, `on_sale` and `off_sale`. User-written content and stored data are not rewritten.
- The frontend binds feature validation to the selected gateway data directory and normalizes the latest favorite result. Off-sale/deleted saved items remain visible as read-only history; the current service does not allow unsaving them. Enquiries support creation/query, without payment, acceptance, cancellation or sold-state actions.
- Core mutations and permissions stay with public backend services. Work runs off the Tk UI thread with duplicate-submit protection, errors, draft warnings and deletion confirmation. The local browser prototype is a separate sample-data design preview and is not part of this repository delivery.

## 5. Data safety

| Area | Approach |
|---|---|
| Password storage | PBKDF2-HMAC-SHA256, 120,000 iterations, a random salt per user, no plaintext stored |
| Password comparison | Timing-safe comparison with `hmac.compare_digest` |
| Sign-in feedback | A single "invalid username or password" message, so account existence is not revealed |
| Public data | Users expose only `id/username/nickname`; `password_hash` and `password_salt` are never returned |
| Redaction fallback | `to_safe_dict(user)` strips every `password*` field for logging and debugging |
| Returned copies | `success()` / `failure()` deep-copy `data`, so callers cannot mutate service memory |
| Sort injection | Sortable fields are checked against a whitelist (`created_at` / `updated_at` / `price`) |
| Corrupt JSON | An explicit error and `success=false`; no crash and no overwrite of the original file (invalid UTF-8 counts as corruption; fixed 18 November 2026) |
| Write protection | One `threading.RLock` per absolute path; a unique `mkstemp` temporary file, then `fsync` and `os.replace` |
| Data isolation | Production data sits in `backend_zhang/data/`; the backend demo uses `demo_data/`; the frontend `--demo` and self-checks use temporary directories, and `--data-dir` selects a practice directory; favorites, intentions, messages and logs each keep their own file and never write to `users.json` or `items.json` |
| Deletion traceability | A snapshot is written to `items_deleted.json` before permanent deletion; the archive is append-only and read-only, and items cannot be restored from it; deletion aborts if the archive write fails |
| ID reuse | Item IDs come from the `items_meta.json` counter, floored at both "current maximum ID + 1" and "archived maximum ID + 1"; deleted IDs are never reused and a lost counter cannot cause collisions |

---

## 6. Test and verification scope

**ZHAO XIAOJUN** owns the group unit tests in `test_zhao/`; the strategy, API specification and execution record are `test_strategy.md`, `API_spec.md` and `auto_test_record.md`. Gao's supplementary frontend tests live in `gui_gao/tests/` and do not replace the group test allocation.

Local verification on 24 November 2026 (Windows, Python 3.13.18):

| Command | Scope | Result |
|---|---|---|
| `python main.py` | Backend self-check, temporary data | All 19 checks passed |
| `python -m unittest test_zhao.test_all` | Group unit tests | All 31 cases passed, 4.106 s |
| `python -m unittest discover -s gui_gao/tests` | Supplementary frontend tests | 56 cases run: 36 passed, 20 Tk-window cases skipped (no interactive desktop), 18.115 s |

The 31 cases in `test_all.py` are 8 user cases, 6 item cases, 9 favorites/intentions/messages cases and 8 review regressions (3 price-rounding boundaries, 3 invalid UTF-8 cases and 2 archive-rollback failures). The first 23 match the final regression in `auto_test_record.md`; the last 8 verify the fixes for Issues 3, 4 and 5 in `docs_huang/code_review/code_review.md`.

```bash
# Supplementary frontend tests (temporary data; Tk-window cases need a desktop)
python3 -m unittest discover -s gui_gao/tests -v

# Group unit tests (temporary data)
python3 -m unittest test_zhao.test_all -v

# Backend self-check (temporary data)
python3 main.py
```

Frontend check on 10 November 2026: **55 tests passed, no skips, 7.604 seconds**, using Python 3.12.14 and real Tk windows on macOS. The 13 November update recorded **56 tests passed in 11.355 seconds**; the 24 November Windows run executed 56 tests with 36 passed and 20 Tk-window cases skipped (18.115 seconds), because that session had no interactive desktop. Checks include current enum mapping, feature-service data isolation, favorite return values, UI flows, animation controls and cleanup. Native Windows/Linux rendering and the final group demonstration machine remain unverified. See [TEST_REPORT](gui_gao/TEST_REPORT.md), [requirements review](gui_gao/REQUIREMENTS_CHECK.md), [test record](test_zhao/auto_test_record.md) and [AI-use disclosure](#ai-use).

The backend already provides everything the tests need:

```python
import os, tempfile
from backend_zhang.user_service import UserService
from backend_zhang.item_service import ItemService
from backend_zhang.user_repository import UserRepository

with tempfile.TemporaryDirectory() as tmp:
    users_file = os.path.join(tmp, "users.json")
    items_file = os.path.join(tmp, "items.json")
    user_service = UserService(users_file)                       # Data paths are configurable
    item_service = ItemService(items_file, UserRepository(users_file))
    # The archive items_deleted.json is placed beside items_file, so tests isolate naturally;
    # ItemService(items_file, repo, deleted_file=...) also sets it explicitly.

    user_service.register("student_01", "abcd1234", "Ming")
```

- Responses were verified: both success and failure return `{"success", "message", "data"}`, so assertions only need `success` and `message`.
- Every field limit, permission rule and state transition is documented in `contracts/backend_api.md`.
- Time fields can be asserted by injecting the time source; service-level time comes from `backend_zhang.json_store.now_text`.

When submitting group tests, sample data templates belong in `test_zhao/fixtures/`; never commit real user or transaction data.

---

## 7. Known limitations

1. User IDs still use "current maximum ID + 1". Users cannot be deleted in this version, so IDs are not reused. Item IDs moved to a counter in v1.3, so they are strictly monotonic and never reused after deletion.
2. Username uniqueness is checked inside the file lock, which assumes one machine and one process. Concurrent multi-process writes to the same file are out of scope.
3. `image_path` stores only a string. The path is not checked for existence and the image is not processed.
4. User deletion, administrator roles, online payments and cloud deployment are not implemented, in line with the requirements document.
5. `items_deleted.json` grows with every deletion. There is no cleanup or paginated archive (`list_deleted_items` caps at 500 records per call).
6. If an exception occurs between issuing an item ID and writing the item, the ID is skipped; a corrupt `items_meta.json` makes publishing fail with a repair hint. Both are the cost and guard of "unique + monotonic" and do not affect existing data.
7. `LogService` in `feature_du/logs.py` is implemented and wired into the frontend, but the `test_zhao` suite covers only favorites, intentions and messages (the log module was not runnable when the test strategy was written). The log service has no dedicated unit tests yet.
8. The review records two non-blocking risks: incomplete input validation in the auxiliary services, and intention-ID generation that could duplicate IDs in extreme cases. Current cases do not trigger either, and by agreement both are deferred to a later version rather than changed in this delivery.

---

## 8. Git conventions

`backend_zhang/data/users.json`, `items.json`, `items_deleted.json` and `items_meta.json`,
`backend_zhang/data/{favorites,messages,intentions,system_logs}.json` and
`demo_data/*.json` are listed in `.gitignore`;
the default log path `backend_zhang/data/logs.json` is not ignored yet, so add a rule before switching to it.
Do not use `git add .` to stage every member's files at once; commit directory by directory.

After uploading a module, each member should update the matching directory, entry point, verification result and integration notes in the root README. For shared documents, change only the sections tied to your own delivery and do not overwrite other members' content.

For a frontend update, for example, stage only after confirming the diff:

```bash
git status --short
git diff -- gui_gao README.md
git add -- gui_gao README.md
git diff --cached --stat
git diff --cached
```

Confirm the staged set contains only the files you own, then commit and push; after pushing, check the target branch and files on GitHub. Sync with the remote before uploading, review conflicts and coordinate rather than force-overwriting a teammate's commits.

---

## 9. Documentation index

| Document | Location | Status |
|---|---|---|
| Product requirements document, PRD v1.0 | `docs_huang/prd.md` | Committed, English edition, 17 chapters, 19 November 2026 |
| Code review record | `docs_huang/code_review/code_review.md` | Committed; frontend, backend, integration and group-test reviews plus four screenshots |
| Backend API contract v1.3 | `contracts/backend_api.md` | Committed |
| Data format contract | `contracts/data_schema.md` | Committed |
| Test strategy, API specification, test record | `test_zhao/test_strategy.md`, `API_spec.md`, `auto_test_record.md` | Committed |
| Frontend handoff, verification, requirements review | `gui_gao/HANDOFF.md`, `TEST_REPORT.md`, `REQUIREMENTS_CHECK.md` | Committed |
| Group plan, AI-use note, PSD | `docs_huang/group_plan.md`, `AI_usage.md`, `psd.md` | Empty placeholders, to be completed |
| Formal report and slides | Not in the repository | Not submitted |


<a id="frontend-guide"></a>

## Frontend guide

### Run

From the repository root, use Python 3.10 or later with Tkinter:

```sh
python3 main.py --gui
```

Create an account on first use. Production data is managed by the backend in `backend_zhang/data/`.

For an isolated demo:

```sh
python3 -m gui_gao --demo
```

On macOS, double-click `gui_gao/launch_demo.command`.

- Demo username: `gao_demo`; password: `Campus123`.
- Three fictional users, eight illustrated items, saved items, public discussions, sent/received enquiries and activity records.
- Temporary demo data is cleared on normal exit. It does not read or change production users or items.
- For a separate practice folder, run `python3 -m gui_gao --data-dir /path/to/practice-data`. Do not run multiple processes against the same directory.

### Pages and connected functions

| Page | Functions | Existing service |
|---|---|---|
| Sign in / Register | Field validation, duplicate usernames, failed-login feedback, session cleanup | `login_user`, `register_user` |
| Browse | Category and keyword search, price sorting, 12 items per page, empty states and retry | `search_items`, `get_public_user_info` |
| Item details | Photo, description, price, seller, status, timestamps and owner edit link | `get_item_by_id`, `get_public_user_info` |
| List / Edit item | Name, category, price, description, optional local photo, validation and unsaved-change prompt | `create_item`, `update_item` |
| My listings | Own items, edit, take off sale, relist and confirmed permanent deletion | `get_items_by_seller`, `remove_item`, `restore_item`, `delete_item_permanently` |
| Account | Display name, current-password verification and password change, activity link | `update_nickname`, `change_password` |
| Saved items | Save/unsave available items; personal list and read-only unavailable-item history | `FavoriteService` |
| Comments | Public item discussions, related threads, 500-character limit, draft warning | `MessageService` |
| Enquiries | Send interest, view sent/received records, reject duplicate and self enquiries | `IntentionService` |
| Activity log | Current user's actions, newest first, search within displayed records | `LogService` |

Available and Off sale are the two existing item states. Enquiries do not make payments, reserve goods or mark items sold. Comments are public, not private messages. Success is shown only after the service saves the action. Permanent deletion cannot be undone through the GUI; the backend archive is for history only.

Tab moves focus. Enter submits sign-in and search forms. On macOS, Command+1/2/3/4/N opens Browse, My listings, Account, Community and List an item. Other desktop systems use Control.

### English presentation and compatibility

Page text, validation, service error feedback, demo content, code comments and this module's documentation are English. `localization.py` translates the existing category/status wire values at the frontend boundary. Saving and filtering send the current team enums (`books`, `electronics`, `clothing`, `household`; `on_sale` and `off_sale` for statuses). Legacy display labels are recognized, but this update does not migrate old data or change service interfaces. User-written titles, descriptions, names and comments are preserved in their original language. Existing activity action labels are translated for display without rewriting records.

Categories shown to the user are Books, Electronics, Clothing and Home & Living. Password and display-name validation still follow the team contract, including support for Chinese characters in user-entered names. Known service errors receive specific English messages; unexpected non-English errors receive a general English recovery message without exposing raw data.

### Visuals and interactions

- Login illustration with a lamp switch; password reveal/hide and a demo credential button.
- Account profile preview, live item/saved/enquiry counts and a reduced-motion setting.
- Listing form with a live card preview, field readiness, append-only description prompts and a photo checklist.
- Saved-item availability filter, comment character count, handover checklist and activity search.
- Enquiry route marker cycles through 1, 2 and 3. The activity clock moves its hands in steps. Both are decorative, can be paused and respect reduced motion. They do not represent a transaction state or the actual time.
- Animation callbacks stop when the page is closed. Other artwork uses brief hover motion.
- The photo dialog provides zoom controls, scrolling, reset and Escape to close. The Pillow-backed zoom defect remains open in [docs_huang/code_review/code_review.md](docs_huang/code_review/code_review.md) (Issue 3-1). Missing photos show a placeholder.
- Checklists are local reminders. They do not save business data or notify another user.

Original layered illustrations are in `gui_gao/assets/scenes/`. The optional generator, `gui_gao/tools/build_scene_art.py`, requires Pillow and its configured font. Running the frontend uses the PNG files and does not require Pillow.

### Code map

```text
main.py --gui (existing team entry point)
  -> gui_gao.main() -> app.py, pages, widgets.py
  -> gateway.py / localization.py -> public user and item services
  -> feature_gateway.py -> four feature_du services via a private compatibility loader
  -> existing backend storage
```

`app.py` manages navigation, serial background service calls and error feedback. `page_design.py`, `theme.py` and `widgets.py` contain shared presentation. `validation.py` gives immediate feedback; final permissions and validation remain with the backend. `demo.py` creates fictional data through service calls. `gui_gao/tests/` contains Gao's supplementary checks and does not replace another member's group tests.

The layout draws on search/category patterns from Xianyu, image-led listings from Carousell HK and seller-management organisation from eBay Seller Hub. Site source code, logos and photos were not copied.

### Errors, storage and integration limits

Service calls run serially on a worker thread, keeping Tk responsive. Submission and navigation are disabled while a request runs to prevent duplicate actions. Failed item saves retain the form. Submitted passwords are cleared and never included in activity records.

The frontend uses the signed-in user's ID and does not accept a user-supplied seller ID. Corrupt data produces an error; it is not silently treated as an empty database or reset. An invalid newly selected image must be replaced or removed. An existing inaccessible image path is retained when editing, avoiding unrequested data loss.

Native image previews support PNG/GIF; JPEG can be supported when Pillow is already installed. Images over 20 MB or 25 million pixels are not previewed. Photos remain at their local paths, so carry them with the project when demonstrating it. The currency remains the team's existing ¥ symbol; this update does not change price units. Names are limited to 20 characters and descriptions to 200. Prices follow backend rounding, with a frontend check against rounding tiny values to zero.

`feature_gateway.py` loads the actual additional-service source with module-local bindings to the gateway's user/item services and a `JsonArrayStore` facade. This keeps demo and practice validation in their selected data directories without changing global service defaults. It also normalizes the current favorite-toggle result for the UI. No teammate source or global modules are patched. See [HANDOFF](gui_gao/HANDOFF.md) for the remaining integration boundaries.

Saved items, comments, enquiries and logs use the selected directory's `favorites.json`, `messages.json`, `intentions.json` and `system_logs.json`. Production records persist; demo records are temporary. The current team service blocks all favorite toggles for off-sale/deleted items. Their saved history remains visible, with no Unsave action. An off-sale item can be unsaved after its seller relists it. Comments and enquiry history remain readable; new interactions require an available item. The current enquiry service supports only creation and reading of `pending` records. No accept/reject/cancel/payment actions are invented.

Activity logs show only the current user and exclude passwords and comment text. If logging fails after an action succeeds, the UI reports that the action was saved and warns against submitting it twice. This is a single-machine JSON application, not a network-authorised service. Cross-device sync, cross-process transactions, image hosting and online payments are outside its scope. Windows/Linux visual rendering has not been inspected; the 24 November 2026 Windows run covered logic and non-Tk checks, with Tk-window cases skipped.

### Frontend checks

Run `python3 -m unittest discover -s gui_gao/tests -v` from the repository root. Tests use temporary data and Tk tests require a graphical desktop. Historical results are recorded in [TEST_REPORT](gui_gao/TEST_REPORT.md); the latest local run is summarised in [section 6](#6-test-and-verification-scope).

<a id="ai-use"></a>

### AI use

Codex assisted with design proposals, initial code, illustration generation, testing, documentation and the English conversion. Gao selected the functional scope and visual direction. The frontend, backend, integration and group-test reviews with the frontend responses are recorded in [docs_huang/code_review/code_review.md](docs_huang/code_review/code_review.md).


## Frontend illustration assets

These illustrations were drawn from geometric shapes by `gui_gao/tools/build_scene_art.py`. They do not use third-party photos, site screenshots or trademarks.

Each scene has transparent `*-base.png` and `*-float.png` layers at 840 × 600 pixels. Floating layers provide short hover motion. The login floating layer is the lamp beam, initially hidden.

The enquiry route and activity clock use the base PNG plus independently drawn SVG or Tk Canvas markers/hands. This allows animation, pause and reduced motion without rotating the whole illustration. They do not show transaction progress or real time.

Colours are blue, navy, lime, cream and apricot. The art is decorative, not a real item photo. The browser uses the `home` scene; the desktop homepage uses a collage of item illustrations.

The app reads the PNGs directly. Regeneration is optional and requires Pillow and the font configured in the generator; adjust the font path to your development machine.
