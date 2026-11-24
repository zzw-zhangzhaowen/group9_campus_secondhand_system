# Group Project Plan

- **Project:** Campus Second-hand Marketplace (Campus Market)
- **Course:** INT6181 Applied Programming with Python — Group Project
- **Document version:** v1.0
- **Status:** Working plan and delivery record
- **Owner:** HUANG BAIQI (memberE documentation and reporting)
- **Reviewers:** ZHANG ZHAOWEN (A), GAO JINGYAN (B), DU YI (C), ZHAO XIAOJUN (D)
- **Repository:** `group9_campus_secondhand_system`

---

## Contents

1. Purpose and planning assumptions
2. Project scope summary
3. Team and roles
4. Work breakdown and ownership
5. Milestones and schedule
6. Collaboration and version control
7. Integration and interface management
8. Quality plan
9. Risk management
10. Deliverables and submission checklist
11. Presentation plan
12. Individual report plan
13. AI use plan and disclosure
14. Status snapshot
15. Key decisions
16. Change log

---

## 1. Purpose and planning assumptions

This plan defines how Group 9 organises, builds, verifies and submits the INT6181 project. It is a working plan rather than a forecast written in advance: tasks, owners and status are kept current so the document doubles as a delivery record.

Planning assumptions:

- five members, one module owner per area, with cross-review rather than isolated work;
- a stand-alone Python desktop application using Tkinter and local JSON, no cloud service or database;
- roughly five working weeks from requirements freeze to submission, matching the phase plan in `docs_huang/prd.md` Section 12;
- every member contributes to code, tests or documentation, and produces an individual report;
- generative AI may be used under the course policy, with review and disclosure.

The plan follows the course requirement that the entry file is `main.py`, instructions live in `README.md`, and the package is submitted as `groupN_project.zip` with a `groupN_presentation.pptx`.

---

## 2. Project scope summary

**In scope:** local registration and sign-in, item publishing and management, browsing, keyword/category search and price sorting, item details, favorites, public comments, purchase enquiries, activity log, JSON persistence, a Tkinter interface with an isolated demo mode, automated tests and documentation.

**Out of scope:** online payment, order settlement, delivery, administrator roles, user deletion, image upload or hosting, cloud deployment, cross-device sync, multi-process concurrency, real-time chat.

The scope is frozen at the level of user-facing behaviour; implementation details may change inside a module as long as the contracts in `contracts/` are respected.

---

## 3. Team and roles

| Member | Letter | Role | Owned area | Main responsibilities | Key outputs |
|---|---|---|---|---|---|
| ZHANG ZHAOWEN | A | Backend and data lead | `backend_zhang/`, `contracts/` | Storage, validation, permissions, state transitions, ID allocation, deletion archive, interface contracts | User/item services, contracts v1.3, backend self-check |
| GAO JINGYAN | B | GUI lead | `gui_gao/` | Window and page design, gateway, background calls, English localisation, demo mode, frontend tests | Tkinter application, handoff and verification records |
| DU YI | C | Auxiliary features lead | `feature_du/` | Favorites, purchase enquiries, public comments, activity log, own data files | Four service classes, integration fixes |
| ZHAO XIAOJUN | D | Testing lead | `test_zhao/` | Test strategy, API specification, automated suite, defect tracking, regression | 31-case unittest suite, test record |
| HUANG BAIQI | E | Documentation and reporting lead | `docs_huang/`, root documentation | PRD, PSD, group plan, code review record, report, slides, submission packaging | `prd.md`, `psd.md`, `group_plan.md`, `code_review/`, final package |

Student names and IDs are recorded in the group proposal submitted on Moodle. Where a member's area touches another module, the module owner reviews the change rather than the contributor editing it directly.

---

## 4. Work breakdown and ownership

| ID | Work package | Owner | Support | Deliverable | Dependency |
|---|---|---|---|---|---|
| WP1 | Requirements and interface freeze | A | E, all | PRD, backend API contract, data schema, enum decision | Course requirements |
| WP2 | Storage and backend services | A | D | `backend_zhang/`, 19 self-checks | WP1 |
| WP3 | Auxiliary services | C | A, D | `feature_du/` favorites, intentions, messages, logs | WP2 interfaces |
| WP4 | Desktop interface | B | A, C | `gui_gao/` pages, gateway, compatibility layer, demo mode | WP2 and WP3 interfaces |
| WP5 | Test design and execution | D | all | Test strategy, API specification, 31-case suite, test record | WP2 and WP3 |
| WP6 | Frontend verification | B | D | Frontend suite, `TEST_REPORT.md`, `HANDOFF.md` | WP4 |
| WP7 | Documentation and review | E | A, B, C, D | PRD, PSD, group plan, code review, README updates | All work packages |
| WP8 | Integration and release | B | all | Integrated build, `group9_project.zip` | WP2–WP7 |
| WP9 | Presentation and individual reports | E | all | `group9_presentation.pptx`, five report PDFs | WP8 |

Work package rules:

- each owner keeps a runnable module and its own tests or evidence;
- changes to shared interfaces go through WP1's change process, not a direct edit;
- integration work never silently rewrites another member's data or defaults;
- documentation owners update only their own sections of shared files.

---

## 5. Milestones and schedule

The schedule follows four delivery phases; status is as at 24 November 2026.

| Milestone | Phase | Target | Gate criteria | Status |
|---|---|---|---|---|
| M1 Requirements and design freeze | Week 1 | End of week 1 | PRD reviewed; interface and data contracts frozen; page sketches agreed | Completed |
| M2 Module self-tests | Weeks 2–3 | End of week 3 | Backend, auxiliary services and GUI each run and pass their own checks | Completed |
| M3 Integration and system testing | Week 4 | End of week 4 | Integrated build runs; unit suite and frontend suite pass; defects recorded | Completed |
| M4 Documentation and package | Week 5 | Before submission | README, PRD, PSD, review record and package complete | In progress |
| M5 Presentation and reports | Week 5 | Before presentation | Slides and video ready; individual reports drafted | Pending |

Working rhythm:

- short sync every two days in the group chat, with blockers named explicitly;
- one weekly checkpoint against the milestone gate;
- review of staged changes before merging, not after;
- no silent scope growth after M1; new ideas are recorded as deferred items.

---

## 6. Collaboration and version control

### 6.1 Branch and commit rules

- One branch per task: `feat/<area>-<topic>`, for example `feat/gui-community-pages`.
- Commit by directory, never `git add .`; production JSON, demo output and local practice data stay untracked.
- Commit messages state the area and the behaviour changed.
- A merge requires a reviewer from another area; the reviewer checks behaviour, tests and contract compliance.
- Conflicts are resolved by the owner of the file, with the other author present; no force-push over a teammate's commits.

### 6.2 Review duties

| Change | Reviewer |
|---|---|
| Backend service or data format | A (author) + D (tests) |
| Auxiliary service | C (author) + A (contract) |
| GUI page or gateway | B (author) + peer (A, C or D) |
| Shared README or contract | E (documentation) + affected owner |
| Test suite | D (author) + module owner |

### 6.3 Communication

- Decisions that affect another module are written into the contract or README, not left in chat.
- A blocker is raised within the same day; the owner proposes an option rather than only reporting the problem.
- Weekly checkpoint records: what is done, what is blocked, what changed in scope.

---

## 7. Integration and interface management

### 7.1 Contract freeze and change process

1. A change request states the interface, the reason and the impact on GUI and auxiliary services.
2. The backend owner updates `contracts/backend_api.md` or `data_schema.md` first.
3. Affected owners confirm compatibility; additions must not break existing callers.
4. The GUI and tests are updated in the same integration window; the change is recorded in the contract change log.

### 7.2 Integration sequence

1. Backend services and storage pass the self-check.
2. Auxiliary services connect through public interfaces only.
3. The GUI gateway binds to the public services; the compatibility layer loads `feature_du` with its own storage context.
4. Isolated demo and practice directories are verified before production data is touched.
5. Frontend suite and unit suite run together before packaging.

### 7.3 Shared decisions already fixed

- Category and status enums use English wire values; display labels are mapped in the frontend.
- Items keep two states plus a read-only deletion archive, not a soft-delete state.
- Item IDs are monotonic and never reused.
- The GUI never reads JSON directly; it only calls services.
- Demo, practice and production data never share directories.

---

## 8. Quality plan

### 8.1 Definition of done

A task is done only when:

1. the behaviour works from a clean run, not only in a local session;
2. invalid input and boundary cases return a specific message, not an exception;
3. tests cover the new behaviour with temporary data;
4. related documentation is updated;
5. another member has reviewed the change;
6. no production data, credential or generated temporary file is committed.

### 8.2 Gates

| Gate | Requirement | Evidence |
|---|---|---|
| Backend | 19 self-checks pass | `python main.py` |
| Unit and integration | 31 cases pass | `python -m unittest test_zhao.test_all` |
| Frontend | Suite passes on a desktop; skips documented | `python -m unittest discover -s gui_gao/tests` |
| Manual demo | Full workflow completes with fictional data | Walkthrough notes |
| Documentation | README matches the repository; contracts current | Documentation index |
| Review | No open blocking defect | `docs_huang/code_review/code_review.md` |

### 8.3 Evidence discipline

Results are reported with the command, environment and date. A historical result is labelled as historical. Unverified platforms are named as unverified, which is why the Windows run records 20 skipped Tk-window cases rather than claiming a full pass.

---

## 9. Risk management

| Risk | Likelihood | Impact | Owner | Mitigation | Status |
|---|---|---|---|---|---|
| Interface drift between modules | Medium | Integration rework | A | Frozen contracts; change process; additive changes only | Mitigated |
| JSON corruption or interrupted write | Low | Data loss | A | Atomic replace, locks, corruption detection, no overwrite | Mitigated |
| Concurrent writers on one data directory | Low | Lost updates | A | Single-process assumption documented; demo/practice isolation | Accepted |
| GUI regressions after backend change | Medium | Broken workflow | B | Gateway tests and frontend suite rerun after each sync | Mitigated |
| Platform rendering differences | Medium | Visual defects | B | Font fallback, minimum layout, macOS and Windows runs recorded | Partially mitigated |
| Pillow image zoom defect | Medium | Crash during demo | B | Defect recorded; zoom path avoided in the live demo | Open |
| Auxiliary validation gaps | Low | Over-long input stored | C | GUI enforces limits; service-level validation deferred | Accepted |
| Test coverage gap for the activity log | Low | Undetected regression | D | Manual checks; dedicated tests deferred | Accepted |
| Schedule slip in documentation or slides | Medium | Late submission | E | Documentation drafted in parallel with WP7; M4 checkpoint | Open |
| Submission packaging error | Low | Mark deduction | B, E | Checklist in Section 10; package verified on a clean folder | Open |

Risks are reviewed at the weekly checkpoint; a risk that becomes a defect moves to the code review or test record.

---

## 10. Deliverables and submission checklist

| Item | Course requirement | Owner | Status |
|---|---|---|---|
| Group proposal | Brief description, member names and IDs, nominated contact, submitted on Moodle | Nominated contact | Submitted at project start; verify the Moodle record |
| Source code | Python project, entry file named `main.py` | A, B, C | Completed |
| `README.md` | Instructions on how to run the project | E, B | Completed |
| Project package | All source, data files and README zipped as `group9_project.zip` | B, E | Completed |
| Code and tests on Moodle | Project code and test cases submitted | D, A | Completed |
| Presentation file | `group9_presentation.pptx` submitted on Moodle | E | Completed |
| Individual reports | One PDF per member, at least 600 words | Each member | Completed |
| Peer assessment | Every member participates | Each member | Completed |

Packaging check before upload:

1. clean checkout runs `python main.py`, `--demo` and `--gui`;
2. no `__pycache__`, no production JSON, no practice data, no local screenshots outside the documented test images;
3. README commands match the archive layout;
4. archive opens into one top-level folder and the entry point runs from there;
5. presentation file opens on the demonstration machine and the demo data is restored before presenting.

---

## 11. Presentation plan

### 11.1 Fifteen-minute video

| Segment | Time | Content | Speaker (proposed) |
|---|---|---|---|
| Opening and problem | 0:00–2:00 | Campus resale problem, target users, project goal | E |
| Requirements and architecture | 2:00–5:00 | Scope, module map, contracts, data design | A |
| Live demonstration | 5:00–11:00 | Registration, browse/search, detail, save/comment/enquiry, own listings, account, activity log | B |
| Quality evidence | 11:00–13:00 | 19 checks, 31 tests, frontend suite, code review, known limitations | D |
| Conclusion | 13:00–15:00 | What works, what is deferred, lessons, AI use | C |

The demonstration uses the isolated demo account `gao_demo` / `Campus123` with fictional data, so a failed production file cannot break the presentation.

### 11.2 Five-minute in-class segment

Up to five slides, five minutes, technical focus:

1. Title and one-sentence scope.
2. Architecture and why the layering matters.
3. One key mechanism: monotonic IDs with a read-only deletion archive.
4. Evidence: tests, review, and one honest limitation.
5. Conclusion and a single improvement for a next version.


### 11.3 Demonstration script and fallback

1. Sign in with the demo account; show Browse and a category filter.
2. Open another seller's item; save it, post a comment, send an enquiry.
3. Open Community; show sent and received enquiries and the activity log.
4. Publish an item; edit it; take it off sale and relist it.
5. Show Account; change the display name; sign out.
6. If a live action fails, fall back to the pre-recorded video segment and explain the known limitation rather than improvising data changes.

---

## 12. Individual report plan

Each member writes at least 600 words in PDF, following the required structure: introduction, project description, personal contributions, challenges faced, lessons learned, conclusion. Reports describe each member's own module, decisions and fixes, and do not restate the group PRD.

| Member | Report focus | Evidence to cite |
|---|---|---|
| A | Storage design, validation, ID policy, archive, contract maintenance | Contract versions, self-check, regression fixes |
| B | Interface design, background calls, compatibility layer, localisation | Frontend suite, handoff, screenshots |
| C | Auxiliary services, integration defects, logging | Test record, defect list B-001 to B-005 |
| D | Test strategy, case design, regression, defect tracking | 31-case suite, test record |
| E | Requirements, specification, review coordination, packaging | PRD, PSD, review record |


---

## 13. AI use plan and disclosure

Generative AI is used within the course policy:

- **Where used:** design proposals, initial code, illustration generation, test scaffolding, documentation drafting and the English conversion.
- **Controls:** every generated change is read and run by the owning member; tests are executed locally; no AI-generated output is reported as an unverified test result; external sources are cited.
- **Disclosure:** `README.md`, `psd.md`, `gui_gao/HANDOFF.md`, `gui_gao/TEST_REPORT.md` and `docs_huang/code_review/code_review.md` state where AI assisted.
- **Responsibility:** the member who merges a change owns it, including any defect it introduces.

---


## 14. Key decisions

| Decision | Rationale | Consequence |
|---|---|---|
| Local JSON instead of a database | No deployment, easy inspection and marking | Linear scans; single-process assumption |
| Two item states plus a read-only archive | Permanent deletion is required, but history is still needed | Archive grows; no restore path |
| Monotonic item IDs via a counter | Prevents a reused ID pointing saved records at a different item | Possible skipped numbers |
| English wire enums | Matches the English interface and avoids encoding confusion | Old Chinese values need manual migration |
| GUI never reads JSON directly | One place enforces permissions and state rules | Slightly more gateway code |
| Module-local compatibility loader for `feature_du` | Connect real services without editing teammate code or demo defaults | One adapter to maintain |
| Isolated demo and practice modes | Protects production data during demonstration and testing | Extra startup paths to test |

---
