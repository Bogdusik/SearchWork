---
paths:
  - "backend/tests/**/*.py"
  - "frontend/tests/**/*.ts"
---

# Testing rules

- Name tests by behavior: `<unit>_<scenario>_<expected>` or a sentence that reads as a claim.
- One behavior per test. Arrange, act, assert, in that order, without comments restating the steps.
- A test must fail for the intended reason before the fix exists. Run it red first.
- Never delete assertions, add `skip`, `only`, `xfail` or loosen matchers to get green. If a test is wrong, say so and explain.
- Synthetic data only. No real people, emails, CV text or tokens.
- No real external network and never a production database. Mock at the boundary (HTTP client, job board API).
- Playwright: role and label locators first, `data-testid` second, CSS last. Wait on a response or an element, not on fixed timeouts.
- Do not print whole page snapshots into logs. Extract the few values you assert on.
