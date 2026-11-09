# Group 9 frontend — GAO JINGYAN

This is the campus second-hand project's Python Tkinter frontend. Design B uses blue, lime accents, illustrated sections and item cards. The desktop application calls the team's existing services. The separate browser prototype is a design preview with sample data.

The implementation is confined to `gui_gao/`. The shared README and repository guide update only Gao's delivery notes. The main entry point, contracts, backend and other members' code are unchanged by this delivery. This version integrates with upstream `7ef1a95`.

## Run

From the repository root, use Python 3.10 or later with Tkinter:

```sh
python3 main.py --gui
```

Create an account on first use. Production data is managed by the backend in `backend_zhang/data/`.

For an isolated demo:

```sh
python3 -m gui_gao --demo
```

On macOS, you can double-click `launch_demo.command`. The older launcher is retained as a small compatibility shortcut so existing links in the shared README still work.

- Demo username: `gao_demo`; password: `Campus123`.
- Three fictional users, eight illustrated items, saved items, public discussions, sent/received enquiries and activity records.
- Temporary demo data is cleared on normal exit. It does not read or change production users or items.
- For a separate practice folder, run `python3 -m gui_gao --data-dir /path/to/practice-data`. Do not run multiple processes against the same directory.
- The removed macOS `.app` wrapper is obsolete. Use the command or launcher above.

## Pages and connected functions

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

## English presentation and compatibility

Page text, validation, service error feedback, demo content, code comments and this module's documentation are English. `localization.py` translates the existing category/status wire values at the frontend boundary. Saving and filtering send the current team enums (`books`, `electronics`, `clothing`, `household`; `on_sale` and `off_sale` for statuses). Legacy display labels are recognized, but this update does not migrate old data or change service interfaces. User-written titles, descriptions, names and comments are preserved in their original language. Existing activity action labels are translated for display without rewriting records.

Categories shown to the user are Books, Electronics, Clothing and Home & Living. Password and display-name validation still follow the team contract, including support for Chinese characters in user-entered names. Known service errors receive specific English messages; unexpected non-English errors receive a general English recovery message without exposing raw data.

## Visuals and interactions

- Login illustration with a lamp switch; password reveal/hide and a demo credential button.
- Account profile preview, live item/saved/enquiry counts and a reduced-motion setting.
- Listing form with a live card preview, field readiness, append-only description prompts and a photo checklist.
- Saved-item availability filter, comment character count, handover checklist and activity search.
- Enquiry route marker cycles through 1, 2 and 3. The activity clock moves its hands in steps. Both are decorative, can be paused and respect reduced motion. They do not represent a transaction state or the actual time.
- Animation callbacks stop when the page is closed. Other artwork uses brief hover motion.
- Photo preview supports 100%, 200% and 300% zoom, scroll, reset and Escape to close. Missing photos show a placeholder.
- Checklists are local reminders. They do not save business data or notify another user.

Original layered illustrations are in `assets/scenes/`. The optional generator, `tools/build_scene_art.py`, requires Pillow and its configured font. Running the frontend uses the PNG files and does not require Pillow.

## Code map

```text
main.py --gui (existing team entry point)
  -> gui_gao.main() -> app.py, pages, widgets.py
  -> gateway.py / localization.py -> public user and item services
  -> feature_gateway.py -> four feature_du services via a private compatibility loader
  -> existing backend storage
```

`app.py` manages navigation, serial background service calls and error feedback. `page_design.py`, `theme.py` and `widgets.py` contain shared presentation. `validation.py` gives immediate feedback; final permissions and validation remain with the backend. `demo.py` creates fictional data through service calls. `gui_gao/tests/` contains Gao's supplementary checks and does not replace another member's group tests.

The layout draws on search/category patterns from Xianyu, image-led listings from Carousell HK and seller-management organisation from eBay Seller Hub. Site source code, logos and photos were not copied.

## Errors, storage and integration limits

Service calls run serially on a worker thread, keeping Tk responsive. Submission and navigation are disabled while a request runs to prevent duplicate actions. Failed item saves retain the form. Submitted passwords are cleared and never included in activity records.

The frontend uses the signed-in user's ID and does not accept a user-supplied seller ID. Corrupt data produces an error; it is not silently treated as an empty database or reset. An invalid newly selected image must be replaced or removed. An existing inaccessible image path is retained when editing, avoiding unrequested data loss.

Native image previews support PNG/GIF; JPEG can be supported when Pillow is already installed. Images over 20 MB or 25 million pixels are not previewed. Photos remain at their local paths, so carry them with the project when demonstrating it. The currency remains the team's existing ¥ symbol; this update does not change price units. Names are limited to 20 characters and descriptions to 200. Prices follow backend rounding, with a frontend check against rounding tiny values to zero.

`feature_gateway.py` loads the actual additional-service source with module-local bindings to the gateway's user/item services and a `JsonArrayStore` facade. This keeps demo and practice validation in their selected data directories without changing global service defaults. It also normalizes the current favorite-toggle result for the UI. No teammate source or global modules are patched. See [HANDOFF.md](HANDOFF.md) for the remaining integration boundaries.

Saved items, comments, enquiries and logs use the selected directory's `favorites.json`, `messages.json`, `intentions.json` and `system_logs.json`. Production records persist; demo records are temporary. The current team service blocks all favorite toggles for off-sale/deleted items. Their saved history remains visible, with no Unsave action. An off-sale item can be unsaved after its seller relists it. Comments and enquiry history remain readable; new interactions require an available item. The current enquiry service supports only creation and reading of `pending` records. No accept/reject/cancel/payment actions are invented.

Activity logs show only the current user and exclude passwords and comment text. If logging fails after an action succeeds, the UI reports that the action was saved and warns against submitting it twice. This is a single-machine JSON application, not a network-authorised service. Cross-device sync, cross-process transactions, image hosting and online payments are outside its scope. Windows/Linux native desktop behaviour has not been verified.

## Checks and delivery

```sh
python3 -m unittest discover -s gui_gao/tests -v
python3 main.py --check
```

Frontend tests use temporary data. Tk tests require a graphical desktop; a skipped test does not establish a pass. The second command is the team's existing backend check. Current and historical evidence is separated in [TEST_REPORT.md](TEST_REPORT.md).

Deliver the whole `gui_gao/` folder at the repository root. The existing entry point already imports it. Stage only owned files after reviewing the diff; do not use blanket staging. Update only Gao's corresponding notes in the shared README and repository guide. Teammates' code is excluded from this delivery. Verify the remote branch after pushing; a local commit alone is not an upload.

The frontend is one part of the group submission. Final group testing, demonstration files, slides and individual reports need their own checks; see [REQUIREMENTS_CHECK.md](REQUIREMENTS_CHECK.md).

<a id="7-ai-&#20351;&#29992;&#35828;&#26126;"></a>

## AI use

Codex assisted with design proposals, initial code, illustration generation, testing, documentation and the English conversion. Gao selected the functional scope and visual direction. The code has not been independently rewritten line by line by Gao or fully reviewed by the group. Describe AI assistance and subsequent personal contributions accurately in the individual report and group disclosure.
