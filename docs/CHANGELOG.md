# Changelog

Outcomes of closed specs, newest first.

## 2026-11-24: Fix react-hooks/set-state-in-effect, rule back to error

- `job-card.tsx`, `use-scroll.ts` and `auth-context.tsx` no longer call `setState` synchronously in effects. The job card adjusts state during render, and `useScroll` uses `useSyncExternalStore`. `AuthProvider` reads the `sw_authed` cookie once at boot through `useSyncExternalStore` and freezes it in state.
- `react-hooks/set-state-in-effect` is back at its `error` default, and the `warn` override is removed from `frontend/eslint.config.mjs`. User-visible behaviour is unchanged.
- New mocked Playwright tests: `tests/mobile/job-card.spec.ts` and `tests/mobile/navbar-scroll.spec.ts`. Live `/verify` gave Pass on 8 criteria and Partial on 6. The AC5 failure (0% card loses "Saved" on the hide-0% toggle) was confirmed pre-existing on HEAD and left out of the spec.
- Follow-ups are filed as GitHub issues: bcrypt pin, register-then-login 500, the 0% saved card, the auth navigation race, and the 20 e2e tests that fail without the `sw_authed` cookie.
