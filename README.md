# REST-API Python

Flask + Connexion REST API with MongoDB, JWT auth, Prometheus metrics, and an OpenAPI 3.0 spec.

## Features

- **OpenAPI 3.0 contract** — `swagger.yml` is the single source of truth for the API; Connexion wires every endpoint to its handler.
- **Generic CRUD** — resources (`users`, `roles`, `products`, `categories`) share a `BaseResource` implementation: ObjectId validation, pagination (`page`/`per_page`), and RFC 7807 problem responses.
- **JWT authentication** — password login with bcrypt-hashed credentials; protected endpoints require a bearer token.
- **Rate limiting** — per-IP limits on all `/api/v1/*` endpoints (configurable via env), with a stricter limit on login; exceeding a limit returns RFC 7807 `429` with `Retry-After` and `X-RateLimit-*` headers. `/api/health`, `/api/environment`, and `/api/metrics` are exempt.
- **Observability** — health check, environment dump, and Prometheus metrics endpoints plus per-request access logging.
- **Tests without a database** — the whole suite runs mocked; MongoDB is not required.

## Prerequisites

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- MongoDB (optional to boot, required for CRUD)

## Quick Start

```bash
# Install dependencies
uv sync

# Copy and configure environment
cp example.env .env
# Edit .env with your MongoDB connection string

# Run the server
uv run python main.py
```

## Swagger UI

Open `http://localhost:5000/api/v1/ui` in your browser.

## Configuration

All settings are read from `.env` (via `python-dotenv`) or the environment.

| Variable | Required | Description |
|---|---|---|
| `PORT` | no | Server port (default `5000`) |
| `MODE` | no | `DEBUG` or `PRODUCTION` |
| `MONGODB_CONN` | yes | MongoDB connection string |
| `MONGODB_DB` | yes | MongoDB database name |
| `LOG_LEVEL` | no | Log level: `NOTSET`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_PATH` | no | Log directory |
| `LOG_BACKUP_COUNT` | no | Days to keep rotated logs (default `10`) |
| `JWT_SECRET_KEY` | no | Token signing key. Falls back to `MONGODB_CONN`, then a dev-only default |
| `JWT_ISSUER` | no | Token issuer claim |
| `JWT_AUDIENCE` | no | Token audience claim |
| `JWT_LIFETIME_SECONDS` | no | Token lifetime in seconds (default `3600`) |
| `RATE_LIMIT_ENABLED` | no | Enable rate limiting (`true`/`false`, default `true`) |
| `RATE_LIMIT_DEFAULT` | no | Per-IP limits for `/api/v1/*` endpoints, `;`-separated (default `60 per minute; 5 per second`) |
| `RATE_LIMIT_LOGIN` | no | Per-IP limit for `/auth/login` (default `5 per minute`) |
| `RATE_LIMIT_STORAGE_URI` | no | Rate-limit storage backend (default `memory://`; use `redis://...` for multi-worker) |

> **Note:** `example.env` includes every variable the app reads (`MONGODB_DB` and the `RATE_LIMIT_*` vars included). Copy it to `.env` and fill in your values.

The server boots even when MongoDB is unreachable, but CRUD requests then fail (500). `/api/health` reflects the database state.

## Rate Limiting

Rate limiting is enforced per IP address on all `/api/v1/*` endpoints and on `/api/v1/auth/login` (which has a stricter, separate limit). When a limit is exceeded the API returns `429 Too Many Requests` in RFC 7807 problem-details format, along with:

- `Retry-After` — seconds until the limit window resets
- `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

The operational endpoints `/api/health`, `/api/environment`, and `/api/metrics` are exempt from rate limits. Set `RATE_LIMIT_ENABLED=false` to disable limiting entirely, or point `RATE_LIMIT_STORAGE_URI` at Redis when running more than one worker.

## API Endpoints

Contract endpoints (base path `/api/v1`):

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `/auth/login` | Login with email + password, returns a JWT | No |
| GET / POST | `/categories` | List / create categories | JWT |
| GET / PUT / DELETE | `/categories/{item_id}` | Read / update / delete a category | JWT |
| GET / POST | `/products` | List / create products | JWT |
| GET / PUT / DELETE | `/products/{item_id}` | Read / update / delete a product | JWT |
| GET / POST | `/users` | List / create users | JWT |
| GET / PUT / DELETE | `/users/{item_id}` | Read / update / delete a user | JWT |
| GET / POST | `/roles` | List / create roles | JWT |
| GET / PUT / DELETE | `/roles/{item_id}` | Read / update / delete a role | JWT |

Operational endpoints (registered directly in `app/app.py`):

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Service and MongoDB health status |
| GET | `/api/environment` | Environment dump (app info, versions) |
| GET | `/api/metrics` | Prometheus metrics |

## Authentication

Login returns the user document and a JWT:

```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret"}'
```

Use the returned token on protected endpoints:

```bash
curl http://localhost:5000/api/v1/categories \
  -H "Authorization: Bearer <TOKEN>"
```

## Testing

The suite is fully mocked — no MongoDB needed:

```bash
uv run pytest        # all tests
uv run pytest tests/test_auth.py   # single file
uv run pytest --cov  # with coverage (currently 98%, 68 tests)
```

## Docker

```bash
docker build . -t py-rest-api
docker run --rm -p 5000:5000 py-rest-api
```

## Tech Stack

| Component | Technology |
|---|---|
| Framework | Flask 3 + Connexion 3 |
| Server | Uvicorn (ASGI) |
| Database | MongoDB (PyMongo) |
| Auth | JWT (Flask-JWT-Extended) |
| Rate Limiting | Flask-Limiter 4 |
| API Spec | OpenAPI 3.0 (Swagger) |
| Monitoring | Prometheus metrics + health checks |

## Documentation

- [`docs/SRS.md`](docs/SRS.md) — Software Requirements Specification
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — Technical documentation & system architecture
- [`docs/USER_MANUAL.md`](docs/USER_MANUAL.md) — User manual
