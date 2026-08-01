# AGENTS.md

Flask + Connexion REST API, OpenAPI-driven, MongoDB backend. Managed with `uv`, requires Python 3.14.

## Commands

```bash
uv sync                  # install deps
uv run python app/app.py # run the API (Swagger UI at http://localhost:5000/api/v1/ui)
uv run pytest            # run tests (no MongoDB needed - all mocked)
uv run pytest tests/test_auth.py   # single test file
uv run pytest --cov      # coverage
```

There is no lint/typecheck tooling. CI runs `uv sync` + `uv run pytest` via `.github/workflows/tests.yml` on every push to `master`/`develop` and on every PR (including Dependabot PRs). Dependency updates are handled by `.github/dependabot.yml` (pip/docker/github-actions, weekly, grouped patch+minor).

## Gotchas

- **`main.py` needs `app/` on `sys.path`** because `app/app.py` imports `utils`/`resources`/`services` as top-level modules that only resolve when the `app/` dir is on the path. `main.py` now inserts `app/` into `sys.path` before importing (matching the top-level convention) and works from the repo root, as does the Dockerfile `CMD`. `uv run python app/app.py` also works. Don't "fix" imports to `app.*` — tests and `swagger.yml` depend on the current top-level form.
- **Namespace packages, no `__init__.py` anywhere** in `app/`. Imports are top-level: `from resources.base import BaseResource`, `from services.mongodb_service import MongoDbService`, `from utils.logs import setup_logging`. Tests resolve these via `[tool.pytest.ini_options] pythonpath = ["app"]`. `swagger.yml` references `resources.auth.decode_token` via `x-bearerInfoFunc` under the same scheme.
- **MongoDB is optional at boot.** `MongoDbService._initialize_client` swallows connection errors, so the app starts fine with a dead DB; `get_collection()` then returns `None` and CRUD requests 500. `/api/health` reflects DB state.
- **`example.env` tracks `.env`** — it now includes every variable the app reads, including `MONGODB_DB` and the `RATE_LIMIT_*` vars. Copy it to `.env` and fill in real values. Docs in `docs/` were refreshed for rate limiting but may lag behind code in other areas; trust code.
- JWT secret fallback in `app/app.py:57`: `JWT_SECRET_KEY or MONGODB_CONN or "dev-secret-change-in-production"`.
- **Rate limiting reads env at import time.** `app/utils/ratelimit.py` builds the module-level `Limiter` from `RATE_LIMIT_*` env vars once, at import. Tests that need different limits must re-import `app` after setting env (see `tests/test_rate_limit.py`). Limiting is per-IP only (no JWT-based keys) and can be fully disabled with `RATE_LIMIT_ENABLED=false`.
- **Dead files are intentional — don't delete.** `static/favicon.ico` (kept to avoid 404s) and `app/utils/dates.py` (unused) are kept on purpose. `requirements.txt` is superseded by `uv`/`pyproject.toml` but is kept and refreshed whenever dependencies change.
- **Test isolation:** `tests/test_app.py` re-imports the `app` module, and `app/app.py:50` pushes a Flask app context at import that is never popped. `test_app.py`'s `_import_app()` helper pops it, so connexion executor threads (which copy `flask`'s `_cv_app` contextvar via `contextvars.copy_context()`/a2wsgi) don't inherit a stale Flask app without a JWTManager. If you add a test that re-imports `app`, pop the pushed context the same way or later HTTP tests will 401 every authenticated request: `decode_token` (see `app/resources/auth.py`) returns `None` on any decode failure and connexion turns that into 401.

## Architecture

- `swagger.yml` (repo root) is the API contract source of truth; Connexion loads it via `con_app.add_api("../swagger.yml")`. New/changed endpoints live there.
- `app/resources/*.py` are thin modules exposing `get_items/get_item/create_item/update_item/delete_item` functions; most instantiate the generic `BaseResource` (`app/resources/base.py`), which does all CRUD, ObjectId validation, pagination (`page`/`per_page`), and RFC 7807 problem responses via `httpproblem`. `auth.py` is the JWT bearer-handler module referenced by the spec: its `decode_token` returns the decoded claims dict or `None` on any failure (connexion maps `None` to a 401 via `BearerSecurityHandler`), and its `login()` is decorated with the login rate limit.
- `app/services/mongodb_service.py`: `MongoDbService` singleton (thread-safe metaclass) wrapping `pymongo`.
- `app/utils/`: logging setup (`logs.py`), date helpers, health check for `/api/health`, and rate limiting (`ratelimit.py`). `ratelimit.py` exposes a module-level `limiter` (flask-limiter) plus `DEFAULT_LIMITS`/`LOGIN_LIMIT`; `app/app.py` calls `limiter.init_app(app)` and registers a 429 handler; `auth.py` decorates `login()` with `LOGIN_LIMIT`.
- Extra routes registered in `app/app.py`: `/api/health`, `/api/environment`, `/api/metrics` (Prometheus). These plus `RATE_LIMIT_EXEMPT`-style prefixes are exempt from rate limits (`/api/health`, `/api/environment`, `/api/metrics`).
