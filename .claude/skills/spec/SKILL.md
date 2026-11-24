---
name: spec
description: "Write a short spec before non-trivial work: acceptance criteria, work packages, checks. Use for new features and any change touching auth, tokens, user data or migrations."
argument-hint: <short description of the change>
disable-model-invocation: true
---

# Write a spec

Input: `$ARGUMENTS`. Output: `docs/specs/<slug>.md` from `docs/specs/_template.md`. You do not implement anything here.

1. **Pick the track** from the table in CLAUDE.md. If the change needs no spec, say so and stop.
2. **Read the code that the change touches** before writing. Do not describe code you have not opened.
3. **Write the Business section first.** Acceptance criteria are numbered `AC1`, `AC2`, one per line as `- AC1: ...`.
   - Each criterion is observable from outside (UI, API response, stored data), with one possible reading.
   - Cover empty state, error path and a boundary for every feature criterion.
   - Reject vague wording ("works well", "fast", "secure") and rewrite it as something checkable.
4. **Ask only what the code cannot answer.** At most 4 questions per round, each with 2-3 options and a recommended one. Record answers in the Open questions table.
5. **Write the Technical section.** Packages are small and each lists which criteria it covers and which command or live scenario proves them. Every AC must appear in at least one package and in Checks.
6. **Short track:** one package, no risk section beyond one line.
7. **Stop.** Leave `Status: Draft`. Tell me the criteria and open questions. Status becomes `Ready` only after I say approve. Do not start `/implement` yourself.
