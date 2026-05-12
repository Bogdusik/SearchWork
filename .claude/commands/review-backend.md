Check changed files in backend/ for SearchWork-specific issues:

**Async / SQLAlchemy:**
- All relationship accesses use `selectinload()` — without it, `MissingGreenlet` at runtime
- `await db.execute(...)` everywhere a DB result is needed
- No `db.query(...)` (sync style) in async routers

**datetime:**
- Uses `datetime.now(timezone.utc).replace(tzinfo=None)`, not `datetime.utcnow()`

**Pydantic schemas:**
- All new model fields are covered in the corresponding schema in schemas.py
- Response schemas don't expose sensitive fields (e.g., binary CV)

**Job sources:**
- New service returns a list of dicts with keys: `external_id`, `source`, `title`, `company`, `location`, `url`, `description`, `salary_min`, `salary_max`
- Salary fields can be None — no hard float() casts

If you find an issue — show the specific line and suggest a fix.
