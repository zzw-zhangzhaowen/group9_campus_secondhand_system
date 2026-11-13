# Frontend verification record

## 10 November 2026 — English frontend update

Delivery scope: `gui_gao/` and only Gao's notes in the shared README and repository guide. The separate web prototype remains local. Initial English checks used `b603d99`; pre-upload integration used upstream `7ef1a95`. Verify the containing commit on the remote branch for delivery status.

### Pre-upload integration with latest upstream

The team changed its category/status enums and additional-service interfaces after the initial English checks. The first run against `7ef1a95` reported 3 failures and 29 errors across 53 tests. The fixes are confined to Gao's frontend: current English wire mappings, gateway-local service context, normalized favorite results and read-only unavailable saved history. Tests now follow the current service restriction on unsaving off-sale/deleted items.

Final result: **55 tests passed in 7.604 seconds, with no skipped tests**. Two added regressions verify that isolated feature validation never calls default production services and that independent directories with matching IDs remain separate. No teammate source was edited. The earlier 53-test result below is the pre-sync baseline, not the final upload result.

### Automated desktop checks

Environment: macOS on Apple Silicon, Python 3.12.14 with Tk. Run from the repository root:

```sh
python3.12 -m unittest discover -s gui_gao/tests -v
```

Result: **53 tests passed in 11.494 seconds, with no skipped tests**. After adding two legacy account-action labels, the four localization tests were run again and passed in 0.092 seconds.

Coverage includes:

- Authentication, account updates, safe session fields and input validation.
- Listing creation, editing, ownership restrictions, off-sale/relist actions and deletion.
- Search, category filters, sorting, stale records and storage failures.
- Saved items, comments, enquiries and activity logs, including user isolation and duplicate-action protection.
- Real Tk windows, navigation, form recovery, image fallbacks and the 1000 × 700 minimum layout.
- Route movement through positions 1, 2 and 3; stepped clock hands; pause/resume, reduced motion and callback cleanup when pages close.
- English display labels with the original backend category and status values preserved.
- English handling of known backend errors and historical activity labels. User-written titles, descriptions, names and comments remain unchanged.

The tests use isolated temporary data and do not write to the group's production data files.

### Web prototype checks

The separate prototype uses sample data. It is not evidence of browser-to-backend integration.

- Syntax checks passed for `app.js`, `b-pages.js`, `b-auth.js` and `b-scenes.js`.
- Eleven routes were checked at both 1366 × 1000 and 390 × 844: home, my listings, account, publish, item details, saved items, comments, enquiries, activity log, sign-in and registration.
- These checks found no horizontal page overflow, broken images, remaining Chinese interface text or JavaScript page errors. The design overview and its four new English thumbnails were also checked.
- Eleven interaction groups passed: category filtering; search; saving/unsaving and sending an enquiry; comments; sent/received enquiry tabs; publishing and off-sale/relist actions; display-name editing; sign-in validation, password visibility and demo sign-in; route animation controls; clock animation controls; and system reduced-motion handling.
- English labels required extra room on narrow screens. Navigation now wraps, and the four community tabs use a two-column layout. The final 390 px enquiry page was visually inspected.

### Native visual inspection and scope

The English sign-in, account and publishing pages were inspected in the native Mac app. The route and clock animations are covered by automated Tk checks; this update does not claim a separate native visual inspection of those two animations. Their browser equivalents were checked independently.

Before syncing upstream, all 28 files outside `gui_gao/` in the initial snapshot were unchanged. The upload then incorporated the team's 11 upstream commits by fast-forward. Relative to `7ef1a95`, this delivery changes only `gui_gao/` and Gao's notes in the shared README and repository guide. Teammates' source and contracts have no changes from that upstream version. The standalone prototype is stored separately.

The backend's own self-checks were not rerun for this language update. The 19-test backend results below are historical. Windows/Linux native rendering, multi-process writes and the final group demonstration environment have not been verified by this update.

## Earlier checks

These records describe earlier versions. They do not establish the current GitHub upload or assignment-submission status.

| Date and change | Frontend result | Backend self-checks in that run |
| --- | --- | --- |
| 4 November — route and clock animations | 49 passed, 0 skipped, 13.043 s | Not rerun |
| 4 November — section illustrations and interactions | 48 passed, 0 skipped, 8.966 s | Not rerun |
| 4 November — secondary pages and authentication | 45 passed, 0 skipped, 7.641 s | Not rerun |
| 4 November — B design and additional pages | 42 passed, 0 skipped, 4.916 s | 19 passed using temporary data |
| 3 November — window cleanup regression | 29 passed, 0 skipped, 3.301 s | 19 passed |
| 1 November — initial frontend | 28 passed, 0 skipped, 3.631 s | 19 passed using temporary data |

### 4 November — animation controls

The checks covered route stopping positions and direction, a fixed clock centre, stepped hand rotation, cancellation of scheduled work while paused, resume behavior, reduced motion and page-destruction cleanup. Browser positions and angles changed during playback and remained stable while paused. Reduced motion disabled animation and playback controls. Native Tk pages were created by the tests, but the manual desktop preview in that run stopped at saved items; it did not visually verify the two desktop animations.

### 4 November — illustrations and page interactions

The illustrations update checked the lamp toggle, non-destructive photo checklists, saved-item and activity filters, image zoom limits and cleanup of illustration animations. Native sign-in, home and saved-item pages were inspected. Browser checks covered the lamp, filters, activity search, listing preview, checklists, comment counter/reset, zoom up to 300%, reset/close and account-help expansion.

The preceding secondary-page update added checks for live listing previews, comment drafts, account summaries and motion preferences, password visibility, failed-sign-in recovery and minimum-window layout. Native sign-in, account, publishing and saved-item pages were inspected. Browser checks also exercised registration validation and demo sign-in.

### 4 November — B design and additional pages

The 42 frontend checks comprised 18 core service/validation checks, 12 additional-feature integration checks and 12 Tk checks. They covered saved items across sessions, user isolation, deleted-item history, comment validation, both sides of enquiries, duplicate/self/off-sale enquiry rejection, competing submissions, damaged-file preservation and safe logging. Tk checks exercised the four community pages, details-page actions, narrow-window layout and leaving an unsaved draft. The actual Mac app displayed the B home page and all four community pages.

### 3 November — window cleanup

Repeated Tk window creation and destruction initially caused an abnormal exit: garbage collection in a background service thread triggered disposal of old Tk variables. The fix explicitly released variables and images on the main thread during widget destruction and waited for service workers before exit. A regression check repeatedly switched sign-in/registration views and triggered collection from a worker. The complete suite then passed.

That fix did not diagnose or resolve the old optional `.app` launcher's reopening warning. The supported launch paths are the Python entry point and the command launcher.

### 1 November — initial frontend

The initial environment was macOS Apple Silicon, Python 3.12.14 and Tk 9.0.4 without Pillow. The 28 checks comprised 18 service/validation checks and 10 real Tk window checks. They covered registration and sign-in recovery, safe session fields, listing permissions, search/category/sort behavior, account updates, price and field boundaries, corrupt JSON preservation, form recovery, missing-image fallbacks and minimum-window widths.

Native inspection covered sign-in, home, publishing, my listings and account settings. The demo showed eight sample listings, including three owned by the sample Gao account. Keyboard navigation and vertical form scrolling were checked. A narrow-window issue was corrected by choosing three or four card columns when rendering; keyboard number shortcuts were also separated from mouse events.

At that initial stage, the additional community features were not yet connected. The later 4 November integration results supersede that historical limitation. Frontend checks remain separate from the group's final integration, presentation and submission review.


## Tkinter B-style update — 13 November 2026

Updated platform font selection, rounded blue banners and pale statistic panels,
login proportions, listing cards and larger secondary-page illustrations.
Animation controls use styled ttk buttons so their labels remain visible on macOS.

Widget-owned Tcl variables now release their resources during the owner widget's
Destroy event on the UI thread. Retired page cycles are collected before submitting
service work. Automatic garbage collection stays enabled. A regression test holds
a retired page variable and verifies its release after navigation.

Validation on macOS / Python 3.12: the ordinary unittest discovery command passed
56 tests in 11.355 seconds, with no Tcl cleanup exceptions. This supersedes the
earlier diagnostic run that disabled automatic garbage collection. Native screenshots
were reviewed for sign-in, browse, profile, enquiries, activity and listing forms.
Minimum-width, route/clock animation, pause/reduced-motion and service-flow tests
passed. Windows and Linux rendering have not been verified.

All implementation and test changes are confined to gui_gao.
