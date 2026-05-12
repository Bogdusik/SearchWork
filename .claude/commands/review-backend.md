Проверь изменённые файлы в backend/ на SearchWork-специфичные проблемы:

**Async / SQLAlchemy:**
- Все relationship доступы используют `selectinload()` — без него `MissingGreenlet` в рантайме
- `await db.execute(...)` везде где нужен результат из БД
- Нет `db.query(...)` (синхронный стиль) в async роутерах

**datetime:**
- Используется `datetime.now(timezone.utc).replace(tzinfo=None)`, не `datetime.utcnow()`

**Pydantic schemas:**
- Все новые поля модели покрыты в соответствующей схеме в schemas.py
- Response схемы не раскрывают лишних полей (например бинарный CV)

**Job sources:**
- Новый сервис возвращает список словарей с ключами: `external_id`, `source`, `title`, `company`, `location`, `url`, `description`, `salary_min`, `salary_max`
- Salary поля могут быть None — нет жёстких float() кастов

Если находишь проблему — покажи конкретную строку и предложи исправление.