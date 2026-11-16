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
> ____________

---

## Iteration Ver2 Review

**Iteration Background**: Basic item and account pages implemented
**Commit hash**: `1971a06` · **Date**: 2026‑11‑03

**Issue 2: Front‑end does not implement corresponding parts for `feature_du` modules; only `backend_zhang` basic functions are integrated**

- Observation: Back‑end services including `FavoriteService`, `MessageService`, `IntentionService` and `LogService` have been fully implemented. However, the GUI layer lacks complete integration for these features. Although the `InteractionPage` route exists, feature completeness is insufficient.
- Impact: End‑to‑end workflows for supplementary features cannot be completed. Only core user‑item functions are usable; favourite, message, intention and operation log workflows do not work fully.
- Expectation: GUI shall invoke public APIs from `feature_du`. Complete full interactions: toggle favourite, view messages, submit intention request and view operation logs.

> Front‑end Lead Response:
> ____________

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
> ____________

### P1 Layout Adaptation Defects

**Issue 3‑2: Horizontal content overflow on several pages under minimum window size**

- Location: `home_page.py`, my‑items page
- Observation: At minimum window size `1000×700`, home page overflows by 10 px, mine page overflows by 31 px. Account page overflows occasionally.
- Root cause: Hard‑coded pixel dimensions and fixed `wraplength` values. Different font glyph widths across platforms further amplify layout shifting.
- Suggestion: Replace fixed hard‑coded widths with adaptive layout, or add horizontal scrollbar. Unify font strategy to mitigate cross‑platform layout drift.

> Front‑end Lead Response:
> ____________

### P1 Test Timing Defects (Business functionality works, but UI unit‑tests are flaky)

**Issue 3‑3: Unstable layout assertion timing in UI tests**

- Location: `gui_gao/tests/test_ui.py:433, 91`
- Observation: Only `update_idletasks()` is called, which cannot guarantee completion of canvas dimension allocation. Canvas width may return tiny value and cause assertion failure.
- Suggestion: Use `self.root.update()` or poll and wait until canvas size is ready before running assertions.

> Front‑end Lead Response:
> ____________

**Issue 3‑4: Animation job assertion occasionally returns None, causing intermittent test failures**

- Location: `gui_gao/tests/test_ui.py:328`
- Observation: Assertion executes before animation job gets scheduled after page navigation, obtaining `art.job = None`. Real‑world animation behaviour in GUI remains correct; this is a test‑only timing problem.
- Suggestion: Wait for animation scheduling completion before assertion, or verify animation instance creation after page switch.

> Front‑end Lead Response:
> ____________

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
> ____________

---

## Overall Review Conclusion

1. The P0 `zoom()` crash must be repaired; otherwise the demonstration will crash.
2. P1 issues such as layout overflow and test timing problems reduce Windows test pass‑rate. Core business logic is correct, yet unstable unit‑tests may hurt project testing‑related marks.
3. UI visual quality can be further improved by re‑using the existing `theme` design system.
4. This review leverages generative AI for code inspection. AI review screenshots are attached as supporting evidence, which can be saved inside `code_review.md` to satisfy INT6181 course requirements for code review and AI‑usage bonus points.

> Overall Front‑end Summary Response:
> ____________
> Overall fix timeline: ________
> Questions / Back‑end support required: ________

---

## Appendix: AI‑assisted Review Screenshots

![AI review – gui_gao issue summary](code_review_screenshots/ai_review_1_gui_issue_summary.png)

![AI review – conclusion](code_review_screenshots/ai_review_2_conclusion.png)

![AI review – cross‑platform root causes](code_review_screenshots/ai_review_3_cross_platform_causes.png)

![AI review – cross‑platform fix priority](code_review_screenshots/ai_review_4_cross_platform_priority.png)
