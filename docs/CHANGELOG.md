# Changelog

Outcomes of closed specs, newest first.

## 2026-11-27: ntfy job alerts

- New per-user job alerts: `GET/PUT /alerts` and `POST /alerts/test` (3/minute) store a search query, cities, minimum score and ntfy topic. A card on the CV page edits them and sends a test push. Validation errors on `/alerts` do not echo submitted values, and the topic never reaches logs.
- A background loop in the API (`services/alert_scheduler.py`) ticks at startup and every 15 minutes, and scans each enabled user once per `ALERT_SCAN_INTERVAL_HOURS` (default 6). A PostgreSQL transaction-level advisory lock allows one tick at a time across processes. Missed intervals after sleep or downtime are not replayed.
- A scan scores only jobs not yet in `seen_jobs` (at most 5 Claude calls at once). It pushes matches at or above the minimum score, top 5 plus one "+N more" push. Jobs whose scoring raised stay unseen and are retried next scan. The first scan, and the first scan after the query or cities change, is a silent baseline.
- Two new tables, `alert_settings` and `seen_jobs`, created by `create_all`. `collect_filtered_jobs` was extracted in `routers/jobs.py` with no behaviour change. `/verify`: 21 criteria, 11 pass, 10 partial, 0 fail. Partial because the local Anthropic key is invalid, so scoring was checked against a mock.
- Not deployed. Known follow-ups: Adzuna keys in job-source error logs (fixed separately), pushes lost when ntfy is down during a scan, non-UK jobs passing the location filter.

## 2026-11-24: Pin bcrypt to 4.0.1, unique refresh tokens (issue #9)

- `backend/requirements.txt` pins `bcrypt==4.0.1` next to `passlib[bcrypt]==1.7.4`. Fresh installs had resolved bcrypt 5.0.0, which breaks passlib's self-test, so every register and password login returned 500. Existing `$2b$` hashes keep verifying.
- `create_refresh_token` in `backend/auth.py` adds a random `jti`. Two tokens issued for one user in the same second no longer collide on `refresh_tokens.token` (register then login returned 500). Tokens without a `jti` still decode.
- New `backend/tests/test_auth_router.py` (11 tests) covers register, login, legacy hashes, error paths and same-second token issues. In a clean Python 3.11 venv it passes; with bcrypt 5.0.0 9 tests fail. `backend/venv` is synced to bcrypt 4.0.1.
- Not deployed. Watch the next Railway build for a bcrypt 4.0.1 wheel. Replacing passlib, which is unmaintained, is a follow-up.

## 2026-11-24: Fix react-hooks/set-state-in-effect, rule back to error

- `job-card.tsx`, `use-scroll.ts` and `auth-context.tsx` no longer call `setState` synchronously in effects. The job card adjusts state during render, and `useScroll` uses `useSyncExternalStore`. `AuthProvider` reads the `sw_authed` cookie once at boot through `useSyncExternalStore` and freezes it in state.
- `react-hooks/set-state-in-effect` is back at its `error` default, and the `warn` override is removed from `frontend/eslint.config.mjs`. User-visible behaviour is unchanged.
- New mocked Playwright tests: `tests/mobile/job-card.spec.ts` and `tests/mobile/navbar-scroll.spec.ts`. Live `/verify` gave Pass on 8 criteria and Partial on 6. The AC5 failure (0% card loses "Saved" on the hide-0% toggle) was confirmed pre-existing on HEAD and left out of the spec.
- Follow-ups are filed as GitHub issues: bcrypt pin, register-then-login 500, the 0% saved card, the auth navigation race, and the 20 e2e tests that fail without the `sw_authed` cookie.
