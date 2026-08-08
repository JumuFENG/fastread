# AGENTS.md

Legado-like Chinese web novel reader. FastAPI + SQLAlchemy 2 + Jinja2 + vanilla JS (server-rendered, no npm/build step). Comments and UI strings are Chinese; match that style.

## Run

- Start: `python main.py` — serves at `http://localhost:8777` (port from `config/config.json` → `client.port`, default 8777).
- `.venv/read` is a working venv (Python 3.12, deps from `requirements.txt`). Run with `.venv/read/bin/python main.py`. Homebrew `python3` (3.14) lacks the project deps.
- No `.env` / `.env.example` — all config lives in `config/config.json` (`client`/`ai`/`database` sections via `Config` in `app/lofig.py`). `database.py` resolves the SQLite path itself: DB lives at `data/reader.db` (`app/database.py` computes it from `__file__`).
- Create extra book sources: sources are added via UI or `sources/` files.
- Docs: `http://localhost:8777/docs`.

## Single-user mode

- The app is single-user: no login, registration, JWT, or user management. `routers/auth.py`, `routers/users.py`, `init_admin.py`, `templates/auth.html`, `templates/users.html`, `static/js/token-manager.js` were removed. All data (reading progress, excerpts, templates, rewrites, sensitive words) belongs to one implicit user.
- `database.py` has no `User` model and no `user_id` columns. If upgrading an old DB, run `python tools/migrate_db.py` (it drops `user_id` columns from the data tables and the `users` table).

## Database

- SQLite `data/reader.db` is git-ignored and committed nowhere; it is real local dev data (54MB). Never delete it casually.
- Tables are created at startup via `Base.metadata.create_all` in `main.py`. Alembic is in requirements but unused; `tools/migrate_db.py` does manual raw-SQLite `ALTER TABLE` to add columns (e.g. `is_cached`, `cached_at`). For schema changes follow that pattern: add column to model + idempotent ALTER in `tools/migrate_db.py`.
- Chapter content is lazy: `Chapter.content` stays NULL, fetched from the source site on demand, then fully cached to DB (`app/routers/books.py:190`).

## Book sources / parsers

- `app/parsers/parser_loader.py` discovers parsers two ways: (1) subclasses of `BaseBookSourceParser` in `sources/*.py`, (2) entries in `sources/sources.json` (git-ignored user data).
- Adding a source = either drop a `sources/xx_parser.py` subclass or append to `sources.json`. Parser API: `search_books`, `get_book_info`, `get_chapter_list`, `update_chapter_list`, `get_chapter_content`, `can_handle_url`, `get_parser_name`. Parsing is CSS-selector config driven (`cfg_template` in `app/parsers/base_parser.py`); override methods per-site.
- `sources/*.py` files hit live novel sites — network-dependent and site-layout fragile. Keep edits surgical and re-test the specific parser.

## Tests

- NOT pytest and no CI. `tests/` are standalone async scripts that hit live websites: run `python tests/test_parsers.py` (edit `__main__` at the bottom to select which source), `python tests/test_chapter.py`. Tests use a separate `data/test.db` (schema auto-created), never the real `data/reader.db`.
- The test DB path is set via Config.db_config()['dbpath'] = 'data/test.db' in test script before import database.py.
- For new parser work, add a `test_*` function there following the existing pattern.

## Frontend

- Recent conventions (respect when touching these): rewrite/creation is fully client-side, nothing saved to server (`static/js/app.js`); templates & excerpts have their own pages; reading progress and sensitive words are server-backed via `/api/reading` and `/api/sensitive-words`.
- AI creation (reader rewritePanel AI tab, `/api/ai/generate`) is server-backed: AI settings (API URL/key/model) live in `config/config.json` via `Config.ai_config()`, saved from the settings page through `/api/ai/config`; generation is proxied server-side (OpenAI-compatible chat completions).

## Desktop / installer / auto-update (ported from yfdaxin pattern)

- `desktop.py` = PyQt6 + QtWebEngine wrapper: starts uvicorn on 127.0.0.1 in a thread if the port isn't already serving, opens the web UI. PyQt6 is NOT in requirements.txt — installed by installer/launcher scripts.
- `scripts/installer.py` + `scripts/installer.spec` + `scripts/build_installer.bat` = Windows PyInstaller onefile GUI installer (needs admin, `uac_admin`). Deploys `main.py`/`desktop.py`/`app`/`templates`/`static`/`requirements.txt`/`scripts/win_service.py`/`res` icons. The「注册为后台服务并开机自启」checkbox makes the Windows service (`scripts/win_service.py`, runs `main.py`) optional.
- `scripts/install_boot_service.sh` = macOS (.app bundle in /Applications) / Linux (.desktop) launcher; crontab `@reboot` boot service only with the `--service` arg (default off).
- Auto-update (product_id=4): `app/routers/updates.py` — `GET /api/update/check` and `POST /api/update/apply` against `{update_server}/api/products/4/latest`, downloads `{update_server}/downloads/fastread/fastread-{v}.zip`, extracts and overwrites project files skipping `config/data/logs/sources/.git`. Config keys under `client`: `update_server` (default `https://prod.ailyf.cn`), `upgrade` (`auto` applies on startup via `main.py:start_server` thread / `manual` shows a banner in `base.html`). `VERSION` lives in `app/lofig.py`.
- Icons in `res/` are generated by `python tools/make_icons.py` (stdlib-only) — regenerate, don't hand-edit.
