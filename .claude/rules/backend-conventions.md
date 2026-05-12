---
paths:
  - "backend/**"
---

# Backend Conventions

## Service interface

Every job source service must expose this exact async signature:

```python
async def search_jobs(query: str, location: str = "UK") -> list[dict]:
```

Each returned dict must include: `external_id`, `source`, `title`, `company`, `location`, `salary_min` (int or None), `salary_max` (int or None), `url`, `description`. Use `httpx.AsyncClient(timeout=10)` for HTTP calls.

## Routers

- Use `APIRouter()` with `Depends(get_db)` on every endpoint that touches the DB.
- Register new routers in `main.py` with `app.include_router(module.router)`.
- Use `HTTPException(404, "...")` for not-found; let unhandled exceptions 500 naturally.

## Database

- All queries are async: `await db.execute(select(...))`, `result.scalar_one_or_none()`, `result.scalars().all()`.
- Use `selectinload()` for relationship eager-loading (no lazy loading with async sessions).
- Never use `datetime.utcnow()` — use the `_utcnow()` helper: `datetime.now(timezone.utc).replace(tzinfo=None)`.

## Models

- Use `Mapped[T]` + `mapped_column()` for all columns.
- Store list-of-strings fields as `JSONList` (the custom `TypeDecorator` in `models.py`) — never use `ARRAY`, which breaks SQLite in tests.

## Tests

- Tests run against an in-memory SQLite DB — `JSONList` handles the SQLite/PostgreSQL difference transparently.
- Run with: `cd backend && python -m pytest tests/ -v`
