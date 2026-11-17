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

> Back-end Lead Response: Pending.

**Issue 2: Existing records may need migration**

- Observation: The update changed category and status values. The GUI aligned with the new values in [`4cc8832`](https://github.com/zzw-zhangzhaowen/group9_campus_secondhand_system/commit/4cc8832).
- Impact: Files created before the enum change can contain values outside the current contract.
- Expectation: Document whether such files need migration and how to reuse them safely.

> Back-end Lead Response: Pending.

**Issue 3: A positive input can be stored as a zero price**

- Observation: Direct calls to [`validate_price`](https://github.com/zzw-zhangzhaowen/group9_campus_secondhand_system/blob/1758451964a219b6e470c2d0e8181810b2d3be18/backend_zhang/validators.py#L135-L163) returned `0.0` for `0.004` and `0.005`. Positivity is checked before rounding.
- Impact: Direct service callers can accept prices that the GUI rejects.
- Expectation: Validate the rounded amount and test `0.004`, `0.005`, `0.006` and `0.01`.

> Back-end Lead Response: Pending.

**Issue 4: Invalid UTF-8 escapes the login error handler**

- Observation: A temporary users file containing an invalid UTF-8 byte caused `UserService.login()` to raise `UnicodeDecodeError`. [`JsonArrayStore._load_unlocked`](https://github.com/zzw-zhangzhaowen/group9_campus_secondhand_system/blob/1758451964a219b6e470c2d0e8181810b2d3be18/backend_zhang/json_store.py#L77-L98)
- Impact: The caller receives an exception instead of the usual readable failure response.
- Expectation: Convert decoding errors to `DataFileError` in both JSON readers and verify the malformed file stays intact.

> Back-end Lead Response: Pending.

**Issue 5: A failed delete can leave a deletion snapshot behind**

- Observation: With both the delete and rollback operations forced to fail, the live item and the archive snapshot both remained. [`delete_item_permanently`](https://github.com/zzw-zhangzhaowen/group9_campus_secondhand_system/blob/1758451964a219b6e470c2d0e8181810b2d3be18/backend_zhang/item_service.py#L374-L398)
- Impact: The returned error reports only the deletion failure, so the stale archive entry goes unnoticed.
- Expectation: Report the rollback failure, document how to reconcile the archive, and test the double-failure path.

> Back-end Lead Response: Pending.

Review method: AI-assisted source inspection, direct reproduction of the price boundary and invalid UTF-8, and fault injection for archive rollback. Reproduction used temporary data. Backend author response pending.

---

## Appendix: AI‑assisted Review Screenshots

![AI review – gui_gao issue summary](code_review_screenshots/ai_review_1_gui_issue_summary.png)

![AI review – conclusion](code_review_screenshots/ai_review_2_conclusion.png)

![AI review – cross‑platform root causes](code_review_screenshots/ai_review_3_cross_platform_causes.png)

![AI review – cross‑platform fix priority](code_review_screenshots/ai_review_4_cross_platform_priority.png)
