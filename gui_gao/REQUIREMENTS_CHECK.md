# Frontend requirements review

This is the English edition of the review made on 4 November 2026. It preserves that review's evidence and limits; it is not a new check of Moodle, deadlines or the group's submission status. The language update on 10 November is described in `README.md`, `HANDOFF.md` and `TEST_REPORT.md`.

At the time of the review, Gao's frontend covered the six functional areas in the available group plan and was ready for integration review. This did not establish that the whole group project was ready to submit or guarantee a grade.

## Sources and dates

1. The locally available `INT6181 Group Project Requirements_v2.pdf`, pages 1–3. Version 2 specified an Individual Report; the earlier version had specified a Group Report. The review used version 2.
2. The previously supplied `group9_python group project(2).docx`, sections 1–8. Its WeChat temporary file was no longer available on 4 November, so the review used the text previously extracted from it and cross-checked the local README, repository guide and contracts. A subsequent revision of the group plan could not be ruled out.
3. The 4 November review used local and remote main at `1971a062fbd5abffbeef1fdea740162e42126185`, with the B-design changes then still local. Later delivery must be checked against the relevant commit, not inferred from this snapshot.
4. The review did not recheck current Moodle announcements, deadlines, proposal status, peer review or uploaded files. Those historical findings must not be treated as current submission status.

## Group plan

| Requirement | Implementation and evidence | Review finding |
|---|---|---|
| Python, Tkinter, JSON and unittest | Existing `main.py --gui`, service storage, `gui_gao/tests/` | Matches the agreed approach |
| Registration, sign-in and display-name changes; ordinary users only | Login and account pages call public user services | Implemented; no administrator role added |
| Create, view, edit and delete items | Listing, detail and own-item pages; off-sale/relist controls and deletion confirmation | Implemented; service enforces ownership |
| Name, category, price, description and local image path | Validated form; native PNG/GIF preview and optional Pillow JPEG support | Implemented |
| Four categories and keyword search | Combined filters, sorting, pagination and empty states | Implemented |
| Save, view and unsave items | Detail control and separate saved-item page; unsave remains possible after deletion | Connected to the actual service |
| Post and read item comments | Detail composer and relevant-thread list; 500-character limit and draft warning | Connected to the actual service |
| Enquiries and records, without transactions | Send, sent/received lists; duplicate, self and unavailable-item guards | Connected to the actual service |
| Key-action activity log | Current user's records, newest first; passwords and comment bodies excluded | Connected to the actual service |
| Bind pages to existing functions | Core gateway and private additional-service adapter | Working through the adapter; interface alignment still needs the owners' review |
| Gao owns the GUI | Implementation and supplementary tests in `gui_gao/` | Teammate source unchanged |
| Merge, integrate and test | 42 frontend tests and 19 backend checks passed in that review | Local evidence only; not complete group acceptance |

The plan described information display and expressions of interest. Payment, delivery, reservations, administrators and a full order lifecycle were outside that plan. The 10 November delivery follows the latest upstream English category/status enums; it does not rewrite user content or migrate stored records. The latest favorite service blocks unsaving unavailable items, so the historical table above no longer describes that behavior. Current behavior and integration limits are in `HANDOFF.md`.

## Teacher requirements recorded on 4 November

| Requirement | Evidence then available | Qualification |
|---|---|---|
| Originality and usefulness, 10% | Working campus second-hand scenario | Explain its purpose; similarity to other groups was not checked |
| Usability, 10% | Native Mac GUI, background service calls, input feedback, retry and draft/deletion prompts | One-machine evidence, not a guarantee across environments |
| Technical depth, 55% | Modular services/pages, persistence, filters, sorting and numeric validation | Explain the actual implementation |
| Good level: specifications and tests | Contracts, frontend README/handoff, 42 frontend tests and 19 backend checks | Additional-service contract and group-wide testing handoff still needed |
| Excellent level: documentation and code review | Usage notes, handoff and review records | Requires group understanding and review; no grade guarantee |
| AI-related bonus | AI assistance with specifications, tests, documentation and review disclosed | Report actual use; CI/CD was an enhancement direction rather than mandatory in this review |
| 15-minute demonstration video with representative live use | Demonstrable application | Final video was not found in the reviewed repository; other locations were not checked |
| Five-minute classroom technical explanation with at most five selected slides; peer review and questions | Interfaces, tests and error handling could provide material | Final slides and peer-review status were not verified |
| Individual PDF report of at least 600 words per member | Contribution and AI-use notes available | A shared README does not replace the individual report |

## Group delivery checklist from that review

These are coordination items, not a claim that the files are still missing today.

| Material or action | Preparation | Owner |
|---|---|---|
| Source, entry point, tests and README | Review and integrate each member's changes deliberately | Members and integrator |
| Additional-service interface | Align storage methods and agree a personal-thread query | DU YI and backend owner |
| Group tests | Combine supplementary GUI checks with the agreed group suite | ZHAO XIAOJUN |
| Final demonstration machine | Verify dependencies, images, startup and representative flows there | Whole group |
| `group9_project.zip` | Code, tests, README and reproducible fictional examples; exclude real accounts, runtime records and caches | Integrator |
| `group9_presentation.pptx`, video and classroom slides | Match actual functions and select technical points for the short presentation | HUANG BAIQI and whole group |
| Each member's report PDF | At least 600 words on contribution, challenges, learning and reflection; cite resources and disclose AI assistance | Each member |
| Moodle details and final upload | Recheck proposal/member details, current deadlines, destinations and submission state | Group contact and each member |

## Findings retained from the original code review

- A fixed-height home banner had clipped action buttons. Content-based sizing and minimum-window assertions fixed it.
- Scanning only available items missed discussions on deleted items without other links. Candidate IDs are now obtained through the service's store; public message methods then load threads. Participant and unrelated-user cases are tested.
- Duplicate enquiries are rejected. A logging failure does not repeat a completed business action. Corrupt JSON is preserved. Saved items and logs are scoped to the signed-in user.
- The additional services' storage-name mismatch is handled within Gao's adapter, without editing their source. Standalone imports still need their owners' attention; see `HANDOFF.md`.
- This is a single-machine JSON application, without network authorisation or cross-process transaction guarantees.

Historical environment: macOS, Python 3.12.14 and Tk 9.0.4. That review passed 42 frontend tests, 19 backend checks and the whitespace check, using isolated fictional data. See `TEST_REPORT.md` for later results rather than reusing those counts as current evidence.
