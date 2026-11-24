# AI Usage Statement

- **Project:** Campus Second-hand Marketplace (Campus Market)
- **Course:** INT6181 Applied Programming with Python — Group Project
- **Document version:** v1.0
- **Status:** Disclosure statement for submission
- **Owner:** HUANG BAIQI (documentation and reporting)
- **Contributors:** ZHANG ZHAOWEN (backend), GAO JINGYAN (GUI), DU YI (auxiliary services), ZHAO XIAOJUN (testing)
- **Applies to:** the repository `group9_campus_secondhand_system` as delivered on 24 November 2026

---

## Contents

1. Purpose and status
2. Course policy and how this project complies
3. Tools used and scope of use
4. Use by work area
5. What was not delegated to AI
6. Review and verification workflow
7. Evidence of AI assistance in the delivered artefacts
8. Risks and mitigations
9. Individual responsibility and report guidance
10. Limits of this statement
11. Declaration
12. Change log

---

## 1. Purpose and status

This statement records how generative AI was used in Group 9's INT6181 project, where the assistance appears in the delivered work, and how the team verified it. It exists because the course permits AI assistance in specification, testing, CI/CD, documentation and code review, and awards credit for well-documented use, while prohibiting plagiarism and unverified claims.

The statement is written for the assessor: it should let a reader tell which parts of the work were AI-assisted, which decisions were made by the team, and which results were independently executed.

Two boundaries apply throughout:

- AI was a drafting and review aid. The team chose the scope, accepted or rejected suggestions, ran every recorded test and owns the submitted result.
- This document records categories of use, not a prompt-by-prompt transcript. The repository keeps the outputs, tests and review notes, not chat histories.

---

## 2. Course policy and how this project complies

| Policy point | How the project complies |
|---|---|
| AI may assist with specification, testing, CI/CD, documentation and code review | AI was used mainly in those areas, with the limits in Section 3 |
| Disclosure is required, and documented AI use can earn credit | This statement, plus disclosures in `README.md`, `psd.md`, `group_plan.md`, the frontend handoff and test report, and the code review |
| Submitted work must be the group's own; plagiarism is prohibited | No third-party project, codebase or dataset was copied; the design, data format, contracts and interface were specified by the team; external ideas are cited where used |
| Every member must be able to explain their contribution | Each member reviewed and can account for the code in their module; individual reports describe personal contributions and AI use |
| Results must be real | Every test figure in this repository comes from an executed run recorded in `test_zhao/auto_test_record.md` or `gui_gao/TEST_REPORT.md`; no AI-generated number was reported as a measurement |

CI/CD was not required by the course brief and is not claimed as delivered. The project has no automated pipeline; verification is performed by running the documented commands locally.

---

## 3. Tools used and scope of use

- **Codex (generative coding assistant):** design proposals, initial implementations, test scaffolding, documentation drafting, English conversion and AI-assisted source review.
- **Image generation assistance:** concept and asset generation for the decorative interface illustrations, together with the script that composes them from geometric primitives. The shipped assets are produced locally by `gui_gao/tools/build_scene_art.py`; no third-party photos, screenshots or trademarks are used.
- **General AI chat assistance:** explanation of library behaviour, wording of documentation and translation checks.

Scope limits observed by the team:

- no real personal data, credentials or production data files were sent to an AI tool;
- no AI tool was given repository write access or asked to commit, merge or push;
- AI output was never accepted as evidence of correct behaviour without a local run;
- AI was not used to generate the graded individual reflections, which each member writes in their own words.

---

## 4. Use by work area

| Area | What AI assisted with | Who reviewed and adapted it | Where it appears |
|---|---|---|---|
| Requirements and design | Structuring the PRD and PSD, drafting acceptance criteria, proposing page layouts and state models | E, with A for backend rules and B for interface decisions | `docs_huang/prd.md`, `docs_huang/psd.md` |
| Backend | Draft validation functions, storage helpers, docstrings and error messages | A read, adapted and tested each change; D covered the behaviour with tests | `backend_zhang/`, `contracts/` |
| Auxiliary services | Draft service classes for favorites, enquiries, comments and logging | C adapted the classes to the contract; A checked interface use | `feature_du/` |
| Frontend | Draft Tkinter pages, theme tokens, animation helpers, English labels, demo data | B selected the visual direction and reworked layout, focus order and error states | `gui_gao/` |
| Tests | Draft test cases and assertions, including boundary cases | D designed the strategy, ran the suite and kept or rejected cases by result | `test_zhao/test_all.py`, `gui_gao/tests/` |
| Documentation | Draft and restructure README, contracts summaries, handoff notes, test records, group plan and this statement; convert Chinese drafts to English | E edited for accuracy against the repository; module owners checked their sections | `README.md`, `docs_huang/`, `gui_gao/*.md` |
| Code review | AI-assisted source inspection, defect hypotheses and reproduction notes | Reviewers reproduced the findings and fixed them; fixes are covered by regression tests | `docs_huang/code_review.md` |
| Illustrations | Concept generation and script scaffolding for the decorative scenes | B adjusted composition, palette and layering; assets regenerated locally | `gui_gao/assets/`, `gui_gao/tools/build_scene_art.py` |

AI use was denser in the first draft of each artefact and thinner in the final state: the delivered code and documents reflect repeated human editing, defect fixing and test-driven correction, not an unedited generation.

---

## 5. What was not delegated to AI

The following remained team decisions and team work:

1. **Scope.** Which features exist (for example, enquiries without accept/reject, deletion with a read-only archive) and which are explicitly out of scope.
2. **Contracts.** The response envelope, permission rules, enum values, ID policy and file ownership were decided by A and confirmed by the other owners.
3. **Verification.** Every reported test count and timing comes from a run on a named machine and date; skipped cases are reported as skipped.
4. **Judgement about defects.** Which findings were fixed, which were accepted as risks, and which were deferred, as recorded in the code review and PSD Section 16.
5. **Individual reports.** Each member writes their own contribution, challenges and reflection; AI may check language, not invent experience.
6. **Submission.** Packaging, Moodle upload, presentation delivery and the decision to submit are human actions.

---

## 6. Review and verification workflow

AI-assisted changes followed the same route as any other change:

1. **State the need** in terms of the contract or requirement, not as "write this feature".
2. **Generate a draft** limited to one file or one behaviour.
3. **Read the draft** against the contract: response shape, permission checks, error messages, naming.
4. **Adapt** to the module's conventions; remove speculative abstractions and unused parameters.
5. **Run it**: `python main.py` for the backend self-check, the unittest suite for behaviour, the GUI for interaction.
6. **Add or adjust tests** so the behaviour is covered by an executed case.
7. **Review by another member** before merge, as described in the group plan.
8. **Record** the change, and any resulting defect, in the test record or code review.

Additional rules:

- a generated suggestion that contradicts the contract is rejected rather than accommodated by weakening the contract;
- generated text is checked for claims the repository cannot support, and unsupported claims are removed;
- AI-assisted review findings are treated as hypotheses until reproduced with temporary data;
- no AI-generated file is committed without a human reading it in full.

---

## 7. Evidence of AI assistance in the delivered artefacts

- `README.md` states the areas of AI assistance and links the code review.
- `docs_huang/psd.md` Section 17 declares the use and the review responsibility.
- `docs_huang/group_plan.md` Section 13 states the controls and the disclosure locations.
- `gui_gao/HANDOFF.md` and `gui_gao/TEST_REPORT.md` note AI-assisted frontend work and the verification performed.
- `docs_huang/code_review.md` is explicitly an AI-assisted review; the defects it reports were reproduced, fixed and covered by regression tests (price rounding at the two-decimal boundary, invalid UTF-8 handling, archive rollback). Its residual findings include the open Pillow zoom defect, Issue 3-1.
- Test evidence is independent of AI: 19 backend self-checks, 31 unit cases (4.106 s), and the frontend suite (56 cases; 36 passed and 20 Tk-window cases skipped on the 24 November Windows run without an interactive desktop).

---

## 8. Risks and mitigations

| Risk | How it showed up | Mitigation applied |
|---|---|---|
| Plausible but wrong API usage | Early drafts called helpers that did not exist or used the wrong response shape | Drafts were run immediately; contract review and tests caught the mismatch |
| Over-broad edits | Generated patches touched unrelated files or restyled working code | Changes were limited to one behaviour; diffs reviewed before commit |
| Style drift | Mixed naming, comment language and formatting | Team conventions applied; English UI strings and docstrings enforced in review |
| Fabricated confidence | Suggestions asserted behaviour that had not been executed | Every claim checked against a run; unverified platforms labelled unverified |
| Duplicated logic | Draft code re-implemented permissions or search in the GUI | Layering rule enforced: the GUI calls services only |
| Privacy leakage | Risk of pasting real data or credentials into a prompt | Only synthetic demo data used; production JSON never shared |
| Over-reliance | Temptation to accept output because it looked complete | Review checklist plus a second reviewer from another module |
| Undisclosed use | Assistance easy to forget in later edits | Disclosure maintained in five documents and repeated in individual reports |

The residual risk the team accepts is that some AI-assisted passages may still read more polished than the surrounding text; content accuracy, not tone, was the review priority.

---

## 9. Individual responsibility and report guidance

Each member is responsible for the code, tests and documents they merged, including defects introduced with AI assistance.

For the individual report (at least 600 words, PDF), each member should state:

1. which parts of their module were AI-assisted and which were written or substantially rewritten by them;
2. one AI suggestion they rejected and why;
3. one defect or misunderstanding they found and how it was verified;
4. what they personally learned about validating generated code.

A generic statement such as "AI helped with the code" is not sufficient; the report should name concrete files and decisions.

---

## 10. Limits of this statement


- It summarises categories of use. The team did not retain full chat transcripts, so it cannot reconstruct every prompt.
- It covers tools the team knows were used. If a member used an additional AI tool for their own report or slides, they must disclose it in that artefact and in their report.
- It does not certify correctness. Correctness is evidenced by the tests, review and documented limitations, not by this statement.
