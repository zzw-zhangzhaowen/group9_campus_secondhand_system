# Code Review Record for Front‑end Module (`gui_gao`)

> Reviewer: ZHANG Zhaowen_11751161

---

## Review Overview

This review covers three iterative versions: ver1 / ver2 / ver3. The back‑end logic in `backend_zhang` is generally stable. The GUI layer contains issues regarding UI presentation, feature completeness, cross‑platform compatibility and test stability. Some defects are blocking‑level and will crash the program; others relate to layout adaptation and test quality.

---

## Iteration Ver1 Review

**Iteration Background**: First round of basic GUI page implementation
**Commit hash**: `82a3a1d` · **Date**: 2026‑10‑30

**Issue 1: Front‑end visual presentation is too simplistic**

- Observation: Page layout and component styling are minimal. Polished visual experience is not achieved.
- Impact: Poor demo presentation, reduces usability score for the project.
- Expectation: Fully utilise existing design tokens defined in `theme.py` (colors, fonts). Refine cards, forms, buttons and spacing to improve overall UI quality.

> Front‑end Lead Response:
> Implemented in [8ce1f96](https://github.com/zzw-zhangzhaowen/group9_campus_secondhand_system/commit/8ce1f96). The Tkinter version now uses platform font fallback, rounded banners and statistic panels, refined sign-in spacing, and consistent listing cards. I checked the rendered pages on macOS.

---

## Iteration Ver2 Review

**Iteration Background**: Basic item and account pages implemented
**Commit hash**: `1971a06` · **Date**: 2026‑11‑03

**Issue 2: Front‑end does not implement corresponding parts for `feature_du` modules; only `backend_zhang` basic functions are integrated**

- Observation: Back‑end services including `FavoriteService`, `MessageService`, `IntentionService` and `LogService` have been fully implemented. However, the GUI layer lacks complete integration for these features. Although the `InteractionPage` route exists, feature completeness is insufficient.
- Impact: End‑to‑end workflows for supplementary features cannot be completed. Only core user‑item functions are usable; favourite, message, intention and operation log workflows do not work fully.
- Expectation: GUI shall invoke public APIs from `feature_du`. Complete full interactions: toggle favourite, view messages, submit intention request and view operation logs.

> Front‑end Lead Response:
> The GUI now connects saved items, public comments, enquiries and the activity log. [4cc8832](https://github.com/zzw-zhangzhaowen/group9_campus_secondhand_system/commit/4cc8832) aligns the adapter with the current service contracts and adds isolation coverage. Unavailable saved items remain visible as read-only history under the current service rules.

---

## Iteration Ver3 Review (AI‑assisted code review, attachment: AI review screenshots)

**Commit hash**: `7ef1a95` · **Date**: 2026‑11‑09 (8 days ago)

> Reference materials: `gui_gao_issue_list.md`, `gui_gao_cross_platform_report.md`
> Test status: Total 56 test cases under `gui_gao/tests`. 4 FAILED + 1 ERROR on Windows; all 56 passed on macOS. These are environment‑sensitive cross‑platform behaviours.

### P0 Blocking Bug (Highest priority, must be fixed)

**Issue 3‑1: Image zoom invokes non‑existent `zoom()` method and causes crash**

- Location: `gui_gao/item_page.py:113,127`
- Observation: When Pillow is available, clicking zoom‑in button raises `AttributeError: 'PhotoImage' object has no attribute 'zoom'`, blocking functionality. This path is never triggered on macOS without Pillow installed, hence the bug remained hidden.
- Impact: Image preview zoom is completely broken; program crashes immediately during demo.
- Suggestion: Replace with `resize()` / `thumbnail()` to generate new image objects. After fix, verify zoom workflow both on Windows (with Pillow) and macOS (without Pillow).

> Front‑end Lead Response:
> Confirmed by source inspection. The dialog still calls Tk zoom on a photo that can be created by Pillow. Open. I propose moving scaling behind the image loader and exercising both loaders before closing this finding.

### P1 Layout Adaptation Defects

**Issue 3‑2: Horizontal content overflow on several pages under minimum window size**

- Location: `home_page.py`, my‑items page
- Observation: At minimum window size `1000×700`, home page overflows by 10 px, mine page overflows by 31 px. Account page overflows occasionally.
- Root cause: Hard‑coded pixel dimensions and fixed `wraplength` values. Different font glyph widths across platforms further amplify layout shifting.
- Suggestion: Replace fixed hard‑coded widths with adaptive layout, or add horizontal scrollbar. Unify font strategy to mitigate cross‑platform layout drift.

> Front‑end Lead Response:
> [8ce1f96](https://github.com/zzw-zhangzhaowen/group9_campus_secondhand_system/commit/8ce1f96) improves font fallback and banner spacing. The macOS suite passed its layout assertions. The reported Windows overflow on Browse, My Listings and Account still needs verification.

### P1 Test Timing Defects (Business functionality works, but UI unit‑tests are flaky)

**Issue 3‑3: Unstable layout assertion timing in UI tests**

- Location: `gui_gao/tests/test_ui.py:433, 91`
- Observation: Only `update_idletasks()` is called, which cannot guarantee completion of canvas dimension allocation. Canvas width may return tiny value and cause assertion failure.
- Suggestion: Use `self.root.update()` or poll and wait until canvas size is ready before running assertions.

> Front‑end Lead Response:
> Agreed. Wait for the mapped canvas to reach a usable width before asserting layout, with a bounded timeout. This Windows timing issue remains open.

**Issue 3‑4: Animation job assertion occasionally returns None, causing intermittent test failures**

- Location: `gui_gao/tests/test_ui.py:328`
- Observation: Assertion executes before animation job gets scheduled after page navigation, obtaining `art.job = None`. Real‑world animation behaviour in GUI remains correct; this is a test‑only timing problem.
- Suggestion: Wait for animation scheduling completion before assertion, or verify animation instance creation after page switch.

> Front‑end Lead Response:
> Agreed. Wait for the animation callback to be scheduled before asserting its state, then verify pause and cleanup separately. Windows timing still needs verification.

### P2 Systematic Cross‑platform Risks

**Issue 3‑5: Noticeable cross‑platform rendering differences in GUI**

Root cause summary:
1. Font candidate list picks different fonts on macOS and Windows. Glyph width inconsistency combined with hard‑coded `wraplength` causes text wrapping and widget height shifts.
2. Tk version divergence: Tk 9.0.4 on macOS vs Tk 8.6.15 on Windows. Widget rendering and timer callback timings behave differently.
3. Two separate image‑loading branches depending on presence or absence of Pillow. Image scaling and EXIF orientation handling produce different visual outputs.

- Current status: Original test report marks `Windows and Linux rendering have not been verified`. Full validation was only performed under macOS.
- Expectation:
  1. Add environment matrix into README: required versions for Python, Tk, Pillow.
  2. Reduce hard‑coded pixel values to mitigate font‑driven layout drift.
  3. Complete full GUI test pass on Windows and remove the "Windows un‑verified" note in documentation.

> Front‑end Lead Response:
> Verified environment for [8ce1f96](https://github.com/zzw-zhangzhaowen/group9_campus_secondhand_system/commit/8ce1f96) was macOS with Python 3.12 and Tk. All 56 tests passed there with automatic garbage collection enabled. Windows and Linux validation, including the Pillow path, remains open.

---

## Overall Review Conclusion

1. The P0 `zoom()` crash must be repaired; otherwise the demonstration will crash.
2. P1 issues such as layout overflow and test timing problems reduce Windows test pass‑rate. Core business logic is correct, yet unstable unit‑tests may hurt project testing‑related marks.
3. UI visual quality can be further improved by re‑using the existing `theme` design system.
4. This review leverages generative AI for code inspection. AI review screenshots are attached as supporting evidence, which can be saved inside `code_review.md` to satisfy INT6181 course requirements for code review and AI‑usage bonus points.

> Overall Front‑end Summary Response:
> The visual refresh, service integration and Tcl cleanup are documented above. The Pillow zoom defect is the next priority.
> Overall fix timeline: Visual and cleanup update shipped in 8ce1f96. Zoom and Windows follow-up are open.
> Questions / Back-end support required: No backend change is required for the GUI zoom and layout fixes.

---

## Backend review by Gao Jingyan

**Review_Section:** `backend_zhang/`
**Reviewer:** GAO Jingyan

### Backend Review — 2026-11-17

**Commit hash:** [`1758451`](https://github.com/zzw-zhangzhaowen/group9_campus_secondhand_system/commit/1758451964a219b6e470c2d0e8181810b2d3be18) · **Review date:** 2026-11-17

**Review Background:** Current storage, validation and deletion behavior. The initial storage implementation is traceable to [`4fe7ac9`](https://github.com/zzw-zhangzhaowen/group9_campus_secondhand_system/commit/4fe7ac9). Category and status values were updated in [`74cf032`](https://github.com/zzw-zhangzhaowen/group9_campus_secondhand_system/commit/74cf032).

**Issue 1: Concurrent GUI instances can lose updates**

- Observation: Atomic replacement protects against partially written JSON. The storage lock is shared only within one process.
- Impact: Two GUI instances using the same data directory can read the same old state and overwrite each other's changes.
- Expectation: Document single-instance use for shared data, or add interprocess locking if concurrent instances are supported.

> Back-end Lead Response: Accepted as a documented constraint, not a code defect. `README.md` Section 7 (Known Limitations) already states that the file lock is in-process and multi-process concurrent writes are out of scope. The product is a local desktop application with one GUI instance; cross-process locking would add OS-specific file-lock code for a scenario the requirements do not cover. No code change.

**Issue 2: Existing records may need migration**

- Observation: The update changed category and status values. The GUI aligned with the new values in [`4cc8832`](https://github.com/zzw-zhangzhaowen/group9_campus_secondhand_system/commit/4cc8832).
- Impact: Files created before the enum change can contain values outside the current contract.
- Expectation: Document whether such files need migration and how to reuse them safely.

> Back-end Lead Response: Accepted as a documentation gap. No automatic migration will be added: the archive and ID-counter files are append-only and the validator rejects out-of-contract values rather than silently rewriting them, so an old-format file is deliberately not auto-converted. Data written before the enum change must be migrated manually (map old Chinese category/status values to `books/electronics/clothing/household` and `on_sale/off_sale`) or started fresh. I will add this note to the migration table in `contracts/backend_api.md`. No code change.

**Issue 3: A positive input can be stored as a zero price**

- Observation: Direct calls to [`validate_price`](https://github.com/zzw-zhangzhaowen/group9_campus_secondhand_system/blob/1758451964a219b6e470c2d0e8181810b2d3be18/backend_zhang/validators.py#L135-L163) returned `0.0` for `0.004` and `0.005`. Positivity is checked before rounding.
- Impact: Direct service callers can accept prices that the GUI rejects.
- Expectation: Validate the rounded amount and test `0.004`, `0.005`, `0.006` and `0.01`.

> Back-end Lead Response: Fixed. `validate_price` now rounds to two decimals first and re-checks positivity on the rounded value, so a small positive input that rounds to `0.00` is rejected instead of being stored as a zero price. Verified: `0.004`, `0.005`, `0.001` raise `ValidationError`; `0.006` and `0.01` return `0.01`; `-10` and the normal path are unchanged. Added `TestPriceRoundingBoundary` (3 tests) covering the boundary values and the service-level `create_item` call.

**Issue 4: Invalid UTF-8 escapes the login error handler**

- Observation: A temporary users file containing an invalid UTF-8 byte caused `UserService.login()` to raise `UnicodeDecodeError`. [`JsonArrayStore._load_unlocked`](https://github.com/zzw-zhangzhaowen/group9_campus_secondhand_system/blob/1758451964a219b6e470c2d0e8181810b2d3be18/backend_zhang/json_store.py#L77-L98)
- Impact: The caller receives an exception instead of the usual readable failure response.
- Expectation: Convert decoding errors to `DataFileError` in both JSON readers and verify the malformed file stays intact.

> Back-end Lead Response: Fixed. Both `JsonArrayStore._load_unlocked` and `JsonObjectStore._load_unlocked` now catch `UnicodeDecodeError` and raise `DataFileError` with a clear "not valid UTF-8" hint; the corrupt file is never overwritten. Verified on both store types (exception type and byte-for-byte file integrity), and `login_user()` against an invalid-UTF-8 users file now returns an ordinary readable failure instead of raising. Added `TestInvalidUtf8Handling` (3 tests).

**Issue 5: A failed delete can leave a deletion snapshot behind**

- Observation: With both the delete and rollback operations forced to fail, the live item and the archive snapshot both remained. [`delete_item_permanently`](https://github.com/zzw-zhangzhaowen/group9_campus_secondhand_system/blob/1758451964a219b6e470c2d0e8181810b2d3be18/backend_zhang/item_service.py#L374-L398)
- Impact: The returned error reports only the deletion failure, so the stale archive entry goes unnoticed.
- Expectation: Report the rollback failure, document how to reconcile the archive, and test the double-failure path.

> Back-end Lead Response: Fixed. `delete_item_permanently` no longer swallows a rollback `BackendError`. On the double-failure path the response now explicitly reports both the deletion failure and the archive rollback failure, and instructs the caller to reconcile `items_deleted.json` manually. Verified by fault injection: double failure reports "rollback also failed", single delete failure keeps its original message, and the normal delete path is unaffected. Added `TestArchiveRollbackFailure` (2 tests).

Review method: AI-assisted source inspection, direct reproduction of the price boundary and invalid UTF-8, and fault injection for archive rollback. Reproduction used temporary data. All three code defects fixed and covered by tests; the two design/documentation findings are accepted with documentation follow-ups.


---

## Integration & Unit Test Review by Du Yi

**Review_Section:** `tests/test_all.py`
**Reviewer:** DU Yi

### Test Suite Review — 2026-11-19

**Review Background:** Consolidated unit and integration test suite covering `feature_du` (`FavoriteService`, `IntentionService`, `MessageService`) and `backend_zhang` (`user_service`, `item_service`, `validators`, `json_store`), including regression test classes (`TestPriceRoundingBoundary`, `TestInvalidUtf8Handling`, `TestArchiveRollbackFailure`) added after the 2026-11-17 backend review (`1758451`). Total: 31 test cases across 6 `unittest.TestCase` classes.

**Issue 1: `LogService` from `feature_du` is completely omitted from the test suite**

- Location: `tests/test_all.py:29-31`, `TestFeatureC` (`tests/test_all.py:34-130`)
- Observation: `TestFeatureC` imports and exercises `FavoriteService`, `IntentionService`, and `MessageService`, but omits `LogService` (`feature_du/logs.py`), which was implemented in Iteration Ver2. In addition, negative and state-transition paths for `FavoriteService`, `IntentionService`, and `MessageService` (such as duplicate purchase intentions, seller intention status updates, and favoriting non-existent or off-sale items) are not tested.
- Impact: Operation logging workflows and boundary validations in `feature_du` lack automated regression coverage.
- Expectation: Add `LogService` test cases (recording and querying user/system operation logs) to `TestFeatureC`, and expand `FavoriteService`, `IntentionService`, and `MessageService` coverage to include duplicate requests, status transitions, and invalid item IDs.

**Issue 2: Incomplete `reset_item_service()` parameters and class-level shared fixtures risk state leakage**

- Location: `tests/test_all.py:45`, `tests/test_all.py:135-144`, `tests/test_all.py:193-209`, `tests/test_all.py:269`
- Observation:
  1. `TestFeatureC.setUp` (line 45) and `TestPriceRoundingBoundary.test_price_service_rejects_round_to_zero` (line 269) call `reset_item_service(data_file=..., user_repository=ur)` without passing explicit `deleted_file` and `meta_file` paths (unlike `TestItemModule.setUpClass` on lines 203–204).
  2. `TestUserModule` and `TestItemModule` initialize temporary JSON storage once in `setUpClass` rather than per test method (`setUp`), causing sequential test methods to mutate shared records.
  3. None of the test classes restore default service paths or clear singleton state in `tearDown` / `tearDownClass`.
- Impact: Omitting `deleted_file` and `meta_file` risks writing to default repository data paths if archive/meta operations are triggered, and shared class-level JSON files introduce implicit test-order dependencies.
- Expectation: Pass explicit temporary `deleted_file` and `meta_file` paths in every `reset_item_service()` call, isolate mutable fixtures per test method where practical, and clean up singleton service state during teardown.

**Issue 3: Unused imports and missing authorization / lifecycle boundary tests in `TestUserModule` and `TestItemModule`**

- Location: `tests/test_all.py:11-21`, `tests/test_all.py:134-190`, `tests/test_all.py:193-244`
- Observation: Ten imported functions—`get_user_by_id`, `get_public_user_info`, `get_all_items`, `get_items_by_seller`, `item_exists`, `is_item_active`, `get_item_status`, `get_public_item_info`, `is_item_deleted`, and `list_deleted_items`—are imported on lines 12 and 17–20 but never invoked. Moreover, `TestItemModule` does not verify seller ownership restrictions (e.g., another user attempting `update_item`, `remove_item`, `restore_item`, or `delete_item_permanently`), and `TestUserModule` lacks failure cases for `change_password` (wrong old password or weak new password).
- Impact: Dead imports reduce maintainability, while access-control regressions or sensitive-field leaks (e.g., `password_hash` in public user queries) could go undetected.
- Expectation: Remove unused imports or add targeted tests for cross-user authorization checks, invalid password updates, item status-transition boundaries, and public query helpers.

**Issue 4: Loose assertions in `TestFeatureC` and `TestItemModule`**

- Location: `tests/test_all.py:80`, `tests/test_all.py:103`, `tests/test_all.py:126`, `tests/test_all.py:214`, `tests/test_all.py:225-235`
- Observation:
  1. `test_favorite_get_user_fav` checks `len(res["data"]) == 1` without verifying `item_id` or `user_id`; `test_intention_get_user_intention` (line 103) and `test_message_get_item_msg` (line 126) use `assertGreaterEqual(len(res["data"]), 1)` despite using a fresh temp directory per test, and do not assert payload fields (`content`, `seller_id`).
  2. `test_remove_restore_item` (lines 225–235) checks `get_item_by_id(iid)` returns `success=False` after `remove_item`, without checking `get_item_status(iid)` or `is_item_active(iid)` to distinguish `off_sale` items from permanently deleted items.
  3. `self.item1_id = res["data"]["id"]` in `test_create_item_ok` (line 214) sets an unused attribute on a single-method `TestCase` instance.
- Impact: Field-level data corruption or status misclassifications (e.g., `remove_item` deleting an item instead of marking it `off_sale`) would not fail the test suite.
- Expectation: Tighten list-length assertions to `assertEqual(..., 1)` with field-level checks, explicitly verify item status states during remove/restore flows, and remove the unused `self.item1_id` assignment.

**Issue 5: `sys.path.append` mutation and unclear suite scope relative to `gui_gao/tests`**

- Location: `tests/test_all.py:1-4`, `tests/test_all.py:296-297`
- Observation: Line 4 appends the parent directory to `sys.path` via `sys.path.append(...)` instead of `sys.path.insert(0, ...)` or standard package discovery (`python -m unittest`). In addition, despite the filename `test_all.py`, the file runs only the 31 back-end and feature tests (`backend_zhang` and `feature_du`) and does not include or reference the 56 GUI tests under `gui_gao/tests`.
- Impact: Appending to `sys.path` can resolve stale modules if an identically named package appears earlier on `PYTHONPATH`, and contributors or evaluators running `test_all.py` may assume it executes the entire project test suite.
- Expectation: Prefer `sys.path.insert(0, ...)` (or standard `unittest` discovery from the repository root) and add a module-level docstring clarifying that `test_all.py` covers `backend_zhang` and `feature_du` tests alongside the command for running `gui_gao/tests`.

> Test Suite Owner Response: Pending follow-up.

---

## Overall Test Suite Review Conclusion

1. The 31 existing tests in `tests/test_all.py` pass cleanly in isolation and effectively verify core CRUD flows plus the three backend regression fixes (`TestPriceRoundingBoundary`, `TestInvalidUtf8Handling`, `TestArchiveRollbackFailure`).
2. Adding `LogService` coverage, tightening `reset_item_service()` file isolation, and adding ownership/negative test cases will close the remaining verification gaps across `feature_du` and `backend_zhang`.

Review method: Manual source inspection of `tests/test_all.py` against `backend_zhang` and `feature_du` service contracts and prior `code_review.md` findings.
