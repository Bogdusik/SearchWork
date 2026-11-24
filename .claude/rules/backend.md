---
paths:
  - "backend/**/*.py"
---

# Backend rules

- Type hints everywhere. Request and response bodies are Pydantic models, never raw dicts.
- Route handlers stay thin. Business logic lives in service functions that can be tested without HTTP.
- Every non-public route depends on the auth dependency. A new route without it needs an explicit reason.
- Auth and token endpoints are rate limited (slowapi). Do not remove or loosen limits silently.
- CORS origins come from environment config. Never `*` together with credentials.
- SQL goes through the ORM or bound parameters. Never build SQL with f-strings.
- Schema changes use the project's existing mechanism (create_all plus ALTER statements in main.py startup). Make every ALTER safe to run twice. Record the schema change under Risks in the spec.
- Errors returned to clients carry no stack traces, SQL or internal paths.
- Never log passwords, tokens, refresh tokens or full request bodies of auth endpoints.
