# Session Progress

## Current Task

**Что делаем:** Углублённое изучение Claude Code — нюансы, подводные камни, практика.
**План:** `~/.claude/plans/goofy-sauteeing-swan.md`
**Источник:** https://github.com/FlorianBruniaux/claude-code-ultimate-guide

## Что уже пройдено

### Фаза 1 — Контекст ✅
- Context Zones: Green/Yellow/Red/Critical
- Context Rot (-20-30% качества при переполнении)
- Правило одной задачи (-39% при смешивании)
- /compact делать на 70%, не на 90%
- Практика: подключили remotive_service.py за одну чистую сессию

### Фаза 2 — Persistent Memory ✅
- 5 уровней памяти (session → auto-memory → CLAUDE.md → external state → MCP Serena)
- Обогатили `.claude/CLAUDE.md` — API quirks Reed/Adzuna, подводные камни async, datetime
- Создали этот файл `PROGRESS.md` (session teleportation pattern)

### Фаза 3 — Hooks ✅ (нужна проверка в новой сессии)
- Хуки получают данные через **stdin как JSON**, не через env vars
- Файл путь: `json.load(sys.stdin)['tool_input']['file_path']`
- `jq` недоступен в Git Bash — используем Python для парсинга stdin
- Settings watcher НЕ перезагружает хуки динамически — нужен рестарт сессии

**Настроенные хуки в `.claude/settings.json`:**
- `PostToolUse(Edit|Write)` → `python -m py_compile` на .py файлах (блокирует при синтаксической ошибке)
- `Stop` → напоминание запустить тесты и обновить PROGRESS.md

### Фаза 4 — Agents & Skills ✅
- `~/.claude/skills/add-job-source/SKILL.md` — создан, работает как `/add-job-source`
- `.claude/agents/backend-reviewer.md` — агент для ревью FastAPI кода

### Фаза 5 — Trinity Pattern ✅

**Суть:** Agents + Hooks + MCP = замкнутый цикл без человека в середине.

```
HOOK  → рефлекс (py_compile на каждый .py, детерминировано)
MCP   → руки (Playwright = браузер, Context7 = документация)
Agent → мозг (фокусированная персона, специализация)
```

**Практика на SearchWork:**
- MCP Context7: вытащил FastAPI async session injection docs прямо из репо fastapi/fastapi
- MCP Playwright: navigate → fill("software developer") → click → network_requests() → response_body() → screenshot()
  - Обнаружили что backend вернул 226K данных (200 OK), UI рендерит job cards с match scores
- Хук PostToolUse уже был настроен (py_compile) — первая вершина триады

**Ключевой инсайт:**
- Без MCP: агент слепой, угадывает работает ли что-то
- Без хуков: агент реактивный, ждёт когда человек скажет о проблеме
- Без специализации: общий Claude делает всё посредственно
- Вместе: агент сам smoke-тестирует, диагностирует, ищет в доках

### Фаза 6 — Permission Model & Security ✅

**5 режимов:** Default → Auto-accept → Plan → Auto → Bypass (dangerous)

**Permission Fatigue:** 70% снижение внимания при частых промптах → люди одобряют не читая.
Решение: намеренный allowlist для предсказуемого, промпты только для нестандартного.

**Практика — аудит и очистка allowlist:**
- `settings.local.json`: 75 строк → 16 (история промптов → намеренные правила)
- Удалено: `python -c '...'` (произвольный код), `node -e '...'`, `python` без аргументов, `taskkill /PID ...`, 20+ hardcoded pytest путей, `winget install *`
- Оставлено: `npm run *`, `pytest *`, `python -m pytest *`, `python -m py_compile *`, git команды, MCP

**Ключевой инсайт:** `python -c '...'` в allowlist = дыра для prompt injection.
Сценарий: job description с вредоносным текстом → Claude обрабатывает → prompt injection → команда в allowlist → API ключи утекли без единого промпта.

### Фаза 7 — Model Economics ✅

**Три модели:**
- Opus 4.7 — архитектурные решения, неочевидные трейдоффы (дорогой)
- Sonnet 4.6 — рутинный код, конфигурация, объяснения (баланс)
- Haiku 4.5 — механические правки, один файл (дёшево)

**OpusPlan pattern:** открыть сессию Opus для плана → новая сессия Sonnet для исполнения.
Экономит деньги: не платишь за Opus reasoning пока Sonnet генерирует код.

**Важное:** `/fast` = Opus 4.6 с быстрым выводом, НЕ Opus 4.7.

**На SearchWork:**
- Добавить job source → Sonnet (известный паттерн, есть skill)
- Архитектура scheduled search → Opus (трейдоффы, выбор технологии)
- Переименовать переменную → Haiku (механика)

### Дополнительные темы ✅

**XML Tags (§2.8):**
- Теги структурируют промпт: `<context>`, `<code>`, `<error>`, `<task>`, `<constraints>`
- Claude парсит роли кусков, а не угадывает что важно
- Создан `.claude/commands/debug.md` — шаблон с XML тегами для отладки

**Semantic Anchors (§2.9):**
- `# [ANCHOR: name]` в коде → ссылаться по имени в промпте
- Полезно в длинных файлах (jobs.py, ai_service.py)

**Plan Mode (§2.3):** `/plan` — только чтение, план без изменений. Использовать перед задачами в 2+ файла.

**Rewind (§2.4):** откат к предыдущему состоянию сессии через UI без `/clear`.

**Commands vs Skills (Ch.6):**
- Commands (`.claude/commands/`) — сохранённый текст промпта, простой шорткат
- Skills (`~/.claude/skills/`) — сложный workflow с чеклистом и инструментами
- Созданы команды: `/review-backend` (SearchWork pitfalls), `/debug` (XML шаблон)

## Курс завершён ✅

Источник: https://github.com/FlorianBruniaux/claude-code-ultimate-guide
