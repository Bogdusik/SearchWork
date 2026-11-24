---
name: implement
description: Implement an approved spec package by package with a bounded repair loop, then run evals. Use only on a spec with Status Ready.
argument-hint: <path to spec in docs/specs/>
disable-model-invocation: true
---

# Implement a spec

Input: spec path in `$ARGUMENTS`.

## Preconditions
- `Status: Ready` in the spec. Otherwise stop and say what is missing.
- `git status` is read first. Note files with uncommitted changes that are not part of the spec: do not touch them.
- Create `.claude/state/active.md` (gitignored) with: baseline commit (`git rev-parse HEAD`), current package, hypothesis, check command, `failed repairs: 0/3`, `review round: 0/2`. Update it as you go so a dropped session can resume.
- Set `Status: In progress`.

## Loop, per package
1. **Plan.** One falsifiable hypothesis: "if I change X, check Y goes from red to green".
2. **Specify.** Add or extend the check first. Run it. It must fail, and for the intended reason. If it passes already, the check is wrong: fix the check.
3. **Act.** Smallest edit inside the package scope.
4. **Verify.** Run the package check. Green means move on.
5. **Correct.** Red means form a new hypothesis from the failure output, not from guessing. Increment `failed repairs`.

At `failed repairs: 3/3` stop. Write a blocker (what was tried, last failure output, your best theory) and wait for me.
Missing secret, service or access is a blocker, not a repair attempt, and does not count toward the 3.

## Forbidden
- Weakening or deleting a test, adding skip/only/xfail, loosening assertions.
- Editing outside package scope, or overwriting my uncommitted changes.
- Claiming something passed without running it in this session.
- Writing approvals on my behalf. Only I move a spec to Ready or Closed.

## After all packages
1. `just evals fast`. Fix until green or hit a stop condition.
2. Record each passed criterion in the spec Evidence section as `Passed YYYY-MM-DD: <command> -> <result> (ACn)`. Old evidence stays valid only if the files it depends on did not change since.
3. Run `/spec-review <spec>`. Max 2 rounds: review 1, fix, review 2. Blockers left after round 2 go to me as a decision list.
4. For the full track run `/verify <spec>`.
5. Set `Status: Awaiting approval`. Never write Done or Closed.

## Final report (short)
- **Outcome:** one sentence.
- **Implemented:** packages and criteria with evidence status.
- **Blocked:** anything not proven, and why.
- **Not deployed:** state it explicitly unless I confirmed a deploy.
- **Next action:** one line, what I should decide or run.
