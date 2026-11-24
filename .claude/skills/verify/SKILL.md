---
name: verify
description: Black-box check of each acceptance criterion against the running app, with a strict verdict per criterion. Fresh context, no diff. Use for the full track before approval.
argument-hint: <path to spec>
context: fork
background: false
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
  - Bash
---

# Verify (black box)

You act as a QA engineer. You test the running application against the acceptance criteria. You do **not** read the diff, the Technical section of the spec, or any summary of what changed. A tester who knows where the change is only confirms it.

Input: spec path in `$ARGUMENTS`. Read only the **Business** section of it.

## Setup
1. Run `git status --porcelain` and keep the output. At the end it must be identical, except for files under `.claude/state/`.
2. App URL and start commands: see `docs/verify-env.md` if it exists, otherwise ask. Never start or stop services other than the ones you started.
3. Number criteria exactly as the spec does (`AC1`, ...).

## Pick the method per criterion (strongest first)
| Method | Use when |
|---|---|
| Live UI | behavior is visible in the browser with data that exists |
| Live UI + API capture | UI must be compared with the raw API response |
| Live API | no UI, call the real endpoint with a test account |
| Mocked response | the data you need does not exist (empty, extreme, error) |
| Rerouted request | page has no data but the same endpoint returns data for another request |
| Data + migration | seed data in the **local** database, then check stored data and UI |
| Temporary change | one definition drives several places: edit, watch, restore the file |
| Code inspection | last resort, no runtime way exists |

Use live methods first. Fall back only when live data cannot exercise the criterion, and say why.

## Verdicts
Exactly one per criterion: `Pass`, `Fail`, `Partial`, `Not tested`.
- `Pass` only when verified end to end on the running app with live data, on every case the criterion names.
- Mocked, rerouted, temporary-change or inspection evidence is `Partial`, never `Pass`.
- Checked only some of the cases the criterion names: `Partial`.
- `Fail` means behavior contradicts the criterion. Give expected (from the spec, never from the code) and actual.
- `Not tested`: no evidence at all. Give the reason (blocker, needs a write to a shared system, out of reach).
- A bug outside every criterion goes to **Observations**, not `Fail`. Do not chase it.

## Technique
- Playwright scripts live in `.claude/state/verify/` as files, not inline shell strings. Edit and re-run, do not retype.
- One script per page visit: navigate once, read everything the criteria need there, return one JSON object keyed by criterion.
- Prefer role and label locators. Use `textContent` for cells outside the rendered area.
- If a technique fails twice, switch technique instead of retrying.
- If the app stops responding and you cannot recover it, stop. Mark every untested criterion `Not tested` with the blocker.
- Evidence is values: ids, counts, status codes, request bodies. Do not print full page snapshots or personal data (names, emails, CV text).

## You may change
- Test data in the local, private database, when a criterion needs it. List every change in the report.
- Source files only as a temporary edit: copy to `.claude/state/verify/` first, restore before finishing.
- Never shared systems, never production. Never `git commit/checkout/reset/stash/clean`.

## Report
Write `.claude/state/verify-report.md`:

```
# <Spec title> - verify report

Spec: <path>
Date: YYYY-MM-DD
Build: <branch> @ <short sha> (+ uncommitted)

## Summary
<n> criteria: <p> pass, <f> fail, <x> partial, <t> not tested.

## Verdicts
| AC | Verdict | Method |
|---|---|---|
| AC1 | Pass | Live UI |

## Failing
| AC | Expected | Actual | Evidence |
|---|---|---|---|

## Partial and not tested
| AC | Reason |
|---|---|

## Changes made
- <every seeded row, temporary edit, state-changing action, and how it was undone> or "None."
- Working tree: unchanged / <what differs>

## Observations
- <bugs outside the criteria, stale local setup> or "None."

## Knowledge updates
- <facts in docs/verify-env.md that proved wrong or missing, with the correct fact> or "None."
```

Then run `node scripts/check-report.mjs .claude/state/verify-report.md <spec>`.
If it prints problems, fix your own file once and run it again. Still invalid: show the output and stop. Never change a verdict to satisfy the script without re-checking the app.

Final message: the report path and the four counts. One line.
