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

## Iteration Ver3 Review (AI‑assisted code review)

**Commit hash**: `7ef1a95` · **Date**: 2026‑11‑09

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
**Review_Section:** `test_zhao`
**Reviewer:** DU Yi

### Test Suite Review — 2026-11-19
**Review Background:**
Reviewed the automated test suite written by ZHAO Xiaojun. This test suite covers `feature_du` modules (`FavoriteService`, `IntentionService`, `MessageService`) and `backend_zhang` modules (`user_service`, `item_service`, validators, json_store). It also includes dedicated boundary and exception regression test classes: `TestPriceRoundingBoundary`, `TestInvalidUtf8Handling`, `TestArchiveRollbackFailure`.
Total: 31 test cases across 6 `unittest.TestCase` classes.

**Overall Comment:**
The test suite is well-structured and stable. Test isolation using temporary directories and `tearDown` cleanup is implemented properly for most test classes. Core positive flows and key error paths for both backend and feature modules are covered. All tests pass on my local environment. The regression tests for special exception scenarios are very helpful for our project stability.

**Minor Issue 1: Unused imported helper functions**
- Location: `tests/test_all.py:12, 17-20`
- Observation: Several helper functions from `item_service` and `user_service` are imported but not used in current test cases.
- Impact: No functional risk. It only slightly reduces code cleanliness.
- Suggestion: Remove unused imports if they are not planned for future extension.

> Test Suite Owner Response: 
> Will clean up unused imports in the next commit.


**Minor Issue 2: A small inconsistency in `reset_item_service()` arguments**
- Location: `TestFeatureC.setUp()` and `TestPriceRoundingBoundary.test_price_service_rejects_round_to_zero()`
- Observation: In `TestItemModule`, `reset_item_service()` passes `deleted_file` and `meta_file`, while `TestFeatureC` and the price boundary test omit these two parameters.
- Impact: Low risk. The service will fall back to default paths only when archive functions are triggered, which is not touched in these test cases.
- Suggestion: For consistency, add temporary `deleted_file` and `meta_file` paths when calling `reset_item_service()` in `TestFeatureC`.

> Test Suite Owner Response:
> Will align the parameter passing style later.

**Minor Issue 3: Some assertions only check length without verifying inner fields**
- Location: `test_favorite_get_user_fav`, `test_intention_get_user_intention`, `test_message_get_item_msg`
- Observation: These cases verify the returned data list is non-empty, but do not assert the exact `item_id`, `user_id` or message content.
- Impact: Low risk. Basic return success is already guaranteed.
- Suggestion: Add simple field assertions to strengthen the test precision if time permits.

> Test Suite Owner Response:
> May add field checks as optional improvement.

**Minor Issue 4: LogService is not included in the current test suite**
- Location: `TestFeatureC`
- Observation: `LogService` in `feature_du/logs.py` has been implemented, but there are no corresponding test cases.
- Impact: Low priority for current delivery. Core favorite / intention / message functions are fully covered.
- Suggestion: Can add LogService test cases as an optional extension.

> Test Suite Owner Response:
> Marked as nice-to-have, not required for current submission.

---

## Overall Test Suite Review Conclusion
1. The 31 test cases run reliably. Normal business flows, password validation, commodity CRUD, favorite/intention/message functions, plus three special exception regression scenarios are well verified.
2. All identified points are minor cosmetic or optional enhancement suggestions; none are blocking defects. The test suite meets our project testing requirements.

Review method: Run the test suite locally + manual code reading against `backend_zhang` and `feature_du` service interfaces.



---

# Code Review Record for Supplementary Module (`feature_du`)
## **Reviewer:**  ZHAO Xiaojun_11751202

---

## Review Overview
This review covers the iterative development of the `feature_du` module implemented by DU Yi, including `FavoriteService`, `IntentionService`, `LogService` and `MessageService`.
Review method: automated black-box testing with `test_zhao/test_all.py`, using isolated temporary JSON data files. All findings in this review are extracted from the recorded test execution log and bug report list.

---

## Iteration Ver1 Review
**Iteration Background**: Initial implementation of favorite, purchase intention and message services
**Test round**: Second run
**Test status**: 18 tests executed; user & item module tests all passed, 4 basic additional-module tests failed with runtime exceptions (blocking defects)

**Issue B‑001: Direct access to private lock attribute `_lock`**
- Location: All services under `feature_du`
- Observation: The code directly accessed `self.store.lock`, while the lock attribute inside `JsonArrayStore` is named `_lock` (private). This raised `AttributeError` and blocked all feature functions.
- Impact: Favorite toggle, intention submission and message operations could not run at all.
- Expectation: Follow the storage component specification and use the provided `transaction()` method for atomic read-modify-write operations instead of manually operating the lock.

> Feature Lead  Response:
> Fixed. Removed direct lock access. All data modification logic is wrapped inside the `transaction()` callback function, complying with the official usage convention of `JsonArrayStore`.

**Issue B‑002: Incorrect storage class name `JsonStore`**
- Location: `messages.py`, `favorites.py`, `intentions.py`
- Observation: The code referenced class `JsonStore`, but the actual exposed class from `backend_zhang.json_store` is `JsonArrayStore`. This caused `NameError`. Import statements were not updated consistently after the class rename.
- Impact: Service initialization failed, the supplementary module could not start.
- Expectation: Replace all `JsonStore` references with `JsonArrayStore` and synchronize import statements.

> Feature Lead  Response:
> Fixed. Global replacement: `JsonStore` → `JsonArrayStore`. All import statements were updated to match.

---

## Iteration Ver2 Review
**Iteration Background**: After fixing lock and class-name issues, continue testing message service
**Test round**: Third run

**Issue B‑003: Calling non-existent storage method `.read()`**
- Location: `feature_du/messages.py`
- Observation: `MessageService` called `self.store.read()`. The standard read method defined in `JsonArrayStore` is `.load()`, triggering `AttributeError`.
- Impact: Message list query failed.
- Expectation: Change read calls to `.load()`.

> Feature Lead  Response:
> Fixed. `self.store.read()` updated to `self.store.load()`. Core business logic remained unchanged.

**Test round**: Fourth run

**Issue B‑004: Calling non-existent storage method `.write()`**
- Location: `feature_du/messages.py`
- Observation: After fixing the read method, the save path still called `self.store.write()`. The standard save method is `.save(data)`.
- Impact: New messages could not be persisted into JSON file.
- Expectation: Align write operation with `.save(data)`, consistent with favorites and intention services.

> Feature Lead  Response:
> Fixed. `self.store.write(messages)` changed to `self.store.save(messages)`. The read/write pair became `.load()` / `.save()`.

**Test round**: Fifth run

**Issue B‑005: Incorrect import statement for storage class**
- Location: `feature_du/messages.py`
- Observation: Used `from json_array_store import JsonArrayStore`. `JsonArrayStore` belongs to the `backend_zhang.json_store` package, not a top-level module, causing `ModuleNotFoundError`.
- Impact: The message service could not be imported or started.
- Expectation: Unify import style consistent with other service files.

> Feature Lead  Response:
> Fixed. Import statement changed to `from backend_zhang.json_store import JsonArrayStore`. Import error eliminated.

---

## Iteration Ver3 Review (Final regression run)
**Test round**: Sixth run / Final regression run
**Reference materials**: `API_spec.md`, `test_zhao/test_all.py`
**Test status**: All blocking bugs above were fixed. Boundary test cases for feature modules were supplemented, total test cases expanded to 23. All 23 test cases passed.

> Note: A `DeprecationWarning` from `backend_zhang.security` still appears. This warning comes from the underlying library and has no influence on business logic.

### P2 Non-blocking risks recorded during testing (not treated as urgent bugs for this iteration)
**Issue**: Potential duplicate intention ID risk and incomplete input validation
- Observation: The test record noted two low-priority risks: insufficient input validation and the ID generation logic for purchase intentions may produce duplicate IDs under special scenarios.
- Impact: No failure triggered under current test scenarios; risk only exists theoretically.
- Suggestion: Reserve these points for future version optimization, add strict input validation and more robust ID generation strategy.

> Feature Lead  Response:
> Accepted as deferred optimization tasks. These will not be modified in this iteration, and will be recorded in the known limitation section.

---

## Overall Review Conclusion
Five high-severity blocking defects were found sequentially during the multi-round automated test of `feature_du`. All of them have been fixed by Member C and verified by my test suite.

After all fixes, the four supplementary services follow the unified API response contract agreed with `backend_zhang`. The 9 test cases for favorite, purchase intention and message modules all pass, covering normal workflows and boundary rules such as rejecting self-submitted intention and blank messages.

The remaining two non-blocking risks are deferred optimization items and will be documented, without code changes required for this submission.

Review evidence: full automated test script `test_zhao/test_all.py` and the bug report table in the test record document.

> Overall Feature Module Summary Response:
> All blocking defects reported in the test runs have been repaired. The supplementary feature module passes all 9 dedicated test cases. The two low-priority risks are acknowledged as future optimization items and will be documented. No further code revision in this iteration.
> Questions / Backend support required: None.
