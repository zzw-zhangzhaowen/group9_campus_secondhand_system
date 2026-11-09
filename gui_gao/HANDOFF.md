# Frontend handoff — Design B

Updated on 10 November 2026. The English UI was first checked against `b603d99`, then adapted to the team's latest upstream `7ef1a95` before delivery. Implementation stays in `gui_gao/`; only Gao's sections of the shared README and repository guide are updated. The standalone browser preview remains separate. Remote delivery is established by the commit containing this record, not by this document alone.

## Start and demonstrate

- Production: `python3 main.py --gui` from the repository root; register on first use.
- Isolated demo: `python3 -m gui_gao --demo`, or open `gui_gao/launch_demo.command` on macOS.
- Demo credentials: `gao_demo` / `Campus123`. Demo accounts and items are fictional.
- Production data is in `backend_zhang/data/`. `--data-dir` selects a practice directory. `--demo` creates temporary data and clears it on normal exit. Do not share one directory between concurrent processes.

Suggested walkthrough: sign in, filter/search, open another seller's item, save/comment/send an enquiry, visit all four Community pages, inspect received enquiries, take an own item off sale and relist it, then check Activity log. The browser version uses sample data and does not test the desktop backend.

## Language boundary

The GUI displays Books, Electronics, Clothing, Home & Living, Available and Off sale. `localization.py` maps these to the current backend enums: `books`, `electronics`, `clothing`, `household`, `on_sale` and `off_sale`. It also recognizes legacy labels for display. User-written content is preserved. Stored files are not migrated or rewritten by this conversion. Errors are translated in Gao's adapter. Keep these mappings in the frontend unless the group jointly changes its data contract.

The English launcher is the preferred path. A small shortcut at the historical launcher path preserves existing links and local shortcuts.

## Additional-service compatibility

The private loader in `feature_gateway.py` adapts imports inside the four feature modules only. Current services use `JsonArrayStore.transaction` and validate users/items through module imports:

| Existing call | Frontend adapter |
|---|---|
| `JsonStore` / `JsonArrayStore` | `StoreBridge(JsonArrayStore)` |
| `.lock` | Backend path-specific shared `RLock` |
| `.read()` | `.load()` |
| `.write(records)` | `.save(records)` |
| Imported user/item services | The current gateway's service instances, preserving isolated demo/practice data |

Source files and global imports remain unchanged. Saves execute the real services and retain atomic storage and corrupt-file errors. The current team modules import successfully; their module-level validation still needs context binding when used with non-default data. The frontend provides that binding locally rather than resetting global defaults. A regression test blocks all access to default production services while exercising demo interactions.

The current favorite query omits deleted items. The frontend reads saved IDs through `FavoriteService.store.load()` to retain read-only history, then resolves item details through public services. It does not write those records itself. Saving/removal still calls `toggle_favorite`; the returned record or `None` is normalized to a UI boolean. The team service rejects toggles for off-sale/deleted items, so the GUI hides Unsave for those entries.

The services do not expose a personal-thread query. The adapter obtains candidate item IDs using `MessageService.store.read()`, then calls `get_item_messages`. It shows discussions on the user's items or discussions they joined, including unavailable/deleted items. Replace this step when a public `get_user_threads(user_id)` method is supplied. The frontend does not directly open business JSON files.

Enquiries currently support creation and query only, with a `pending` status. The GUI adds signed-in identity, self-enquiry, duplicate and availability guards. These are single-machine constraints; a future network service must enforce them server-side. Do not add accept/cancel/payment buttons without supporting services.

Activity records contain action names and item IDs/titles, not passwords or comment text. A logging failure does not undo or repeat a successful business action. Stored English action labels and legacy labels can coexist; the latter are translated for display.

## Remaining group coordination

1. DU YI and the backend owner should agree service-instance injection, a personal-thread query and whether unavailable saved items can be removed. Replace the private loader/read-only history bridge when public interfaces cover these needs.
2. ZHAO XIAOJUN owns group testing in `test_zhao/`; Gao's supplementary tests remain under `gui_gao/tests/`.
3. HUANG BAIQI should align the report, slides and user manual with actual public-comment and enquiry behaviour and AI use.
4. Carry local photo files to the demonstration machine and test there. Relative paths resolve from the repository root. Agree any currency change as a group.
5. Review and stage only owned paths. Exclude production records, caches and obsolete app wrappers.

Recommended reading order: `gateway.py`, `localization.py`, `app.run_task()`, the item and interaction pages, then `feature_gateway.py` and the tests. Passing a rejection test means invalid input was correctly refused; it does not mean every input should succeed.
