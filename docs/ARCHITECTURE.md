# Technical Documentation & System Architecture

| Field | Value |
|-------|-------|
| **Project Name** | api-rest |
| **Document ID** | ARCH-API-REST-v1.1.0 |
| **Version** | 1.1.0 |
| **Architecture Style** | Layered (N-Tier) |
| **Primary Language** | Python 3.14 |
| **Framework(s)** | Flask 3, Connexion 3 |
| **Date** | 2026-05-08 |
| **Status** | Approved |

---

## Revision History

| Version | Date | Description | Author |
|---------|------|-------------|--------|
| 1.0.0 | 2026-05-08 | Initial release | David A. Mancilla |
| 1.1.0 | 2026-08-01 | Added per-IP rate limiting (Flask-Limiter), RFC 7807 429 responses, and related configuration | David A. Mancilla |

---

## Table of Contents

1. [Introduction and Goals](#1-introduction-and-goals)
2. [Architecture Constraints](#2-architecture-constraints)
3. [System Scope and Context](#3-system-scope-and-context)
4. [Solution Strategy](#4-solution-strategy)
5. [Building Block View](#5-building-block-view)
6. [Runtime View](#6-runtime-view)
7. [Deployment View](#7-deployment-view)
8. [Cross-Cutting Concepts](#8-cross-cutting-concepts)
9. [Architecture Decisions](#9-architecture-decisions)
10. [Quality Requirements](#10-quality-requirements)
11. [Risks and Technical Debt](#11-risks-and-technical-debt)
12. [API Reference](#12-api-reference)
13. [Configuration Reference](#13-configuration-reference)
14. [Data Architecture](#14-data-architecture)
15. [Development Guide](#15-development-guide)

---

## 1. Introduction and Goals

### 1.1 Requirements Overview

The system provides a RESTful API for managing products, categories, users, and roles with JWT-based authentication and MongoDB persistence. It serves as a backend service for client applications requiring e-commerce or inventory management capabilities.

### 1.2 Quality Goals

| Priority | Quality Goal | Scenario |
|----------|-------------|----------|
| 1 | Security | All data access requires valid JWT authentication; passwords hashed with bcrypt; per-IP rate limiting protects against abuse and brute force |
| 2 | Maintainability | DRY principle applied via BaseResource; 98% test coverage |
| 3 | Interoperability | OpenAPI 3.0 specification enables any HTTP client to integrate |
| 4 | Observability | Health checks, environment dump, Prometheus metrics, and request logging |

### 1.3 Stakeholders

| Stakeholder | Interest |
|-------------|----------|
| API Consumers | Reliable, well-documented REST endpoints |
| System Administrators | Monitoring, configuration, and deployment |
| Developers | Clean codebase, test coverage, easy local setup |

---

## 2. Architecture Constraints

| Constraint | Rationale |
|------------|-----------|
| Python 3.14+ | Project uses latest Python features |
| MongoDB | Chosen for flexible document model |
| OpenAPI 3.0 | Contract-first API development via Connexion |
| Docker | Containerized deployment consistency |

---

## 3. System Scope and Context

### 3.1 Business Context

![Business Context Diagram](diagrams/business_context.svg)

### 3.2 Technical Context

| Interface | Protocol | Description |
|-----------|----------|-------------|
| REST API | HTTP/1.1 | All business operations |
| Database | MongoDB Wire Protocol | Data persistence via PyMongo |
| Monitoring | HTTP | Prometheus metrics scraping |
| API Docs | HTTP (Swagger UI) | Interactive documentation |

---

## 4. Solution Strategy

- **Architecture Pattern:** Layered (N-Tier) — API resources, service layer, utilities.
- **Technology Stack:**
  - **Web Framework:** Flask 3 with Connexion 3 for OpenAPI-driven request routing.
  - **ASGI Server:** Uvicorn via a2wsgi bridge for async performance.
  - **Database:** MongoDB with PyMongo driver, singleton connection management.
  - **Authentication:** JWT via Flask-JWT-Extended, bcrypt password hashing.
  - **Rate Limiting:** Flask-Limiter for per-IP request throttling (env-configurable).
  - **Monitoring:** py-healthcheck for health/endpoints, prometheus-client for metrics.
- **Key Design Principles:** DRY (via BaseResource generic CRUD), singleton pattern (MongoDbService), environment-based configuration.
- **Trade-offs:** Monolithic deployment chosen over microservices due to single-domain scope and team size; synchronous request handling accepted over async due to simplicity.

---

## 5. Building Block View

### 5.1 Level 1 — System Context

![System Context — Level 1](diagrams/system_context.svg)

### 5.2 Level 2 — Container View

![Container View — Level 2](diagrams/container_view.svg)

### 5.3 Level 3 — Component View

#### 5.3.1 BaseResource

| Property | Value |
|----------|-------|
| **Type** | Controller / Service |
| **File** | `app/resources/base.py` |
| **Responsibility** | Generic CRUD operations for any MongoDB collection |
| **Methods** | `get_items`, `get_item`, `create_item`, `update_item`, `delete_item` |
| **Dependencies** | `MongoDbService`, `jsonify`, `ObjectId`, `problem_http_response` |
| **Configuration** | Collection name, stringify fields, unique field, count inclusion |

#### 5.3.2 MongoDbService

| Property | Value |
|----------|-------|
| **Type** | Service |
| **File** | `app/services/mongodb_service.py` |
| **Responsibility** | Singleton MongoDB client instance management |
| **Methods** | `get_collection`, `get_info`, `is_connected` |
| **Dependencies** | `PyMongo MongoClient`, `os.environ` |
| **Pattern** | Singleton via metaclass `SingletonMeta` with thread-safe locking |

#### 5.3.3 Auth Resource

| Property | Value |
|----------|-------|
| **Type** | Controller |
| **File** | `app/resources/auth.py` |
| **Responsibility** | User authentication and JWT token management |
| **Methods** | `login`, `decode_token`, `_build_token` |
| **Dependencies** | `MongoDbService`, `bcrypt`, `flask_jwt_extended` |

#### 5.3.4 Resource Adapters (Categories, Products, Users, Roles)

| Resource | Collection | Unique Field | Stringify Fields | Include Count |
|----------|------------|--------------|------------------|---------------|
| Categories | `categories` | `name` | `_id`, `userId` | Yes |
| Products | `products` | `name` | `_id`, `userId`, `categoryId` | Yes |
| Users | `users` | `name` | `_id` | No |
| Roles | `roles` | `role` | `_id` | No |

#### 5.3.5 RateLimiter

| Property | Value |
|----------|-------|
| **Type** | Utility / Middleware |
| **File** | `app/utils/ratelimit.py` |
| **Responsibility** | Per-IP request throttling for API endpoints |
| **Methods** | module-level `limiter` (flask-limiter `Limiter`), `_parse_limits`, `_is_exempt`; constants `DEFAULT_LIMITS`, `LOGIN_LIMIT` |
| **Dependencies** | `flask_limiter`, `os.environ` |
| **Configuration** | `RATE_LIMIT_ENABLED`, `RATE_LIMIT_DEFAULT`, `RATE_LIMIT_LOGIN`, `RATE_LIMIT_STORAGE_URI` |

The `limiter` instance is created at module import time from the `RATE_LIMIT_*` environment variables. `app/app.py` calls `limiter.init_app(app)` and registers a 429 handler; `auth.login()` is decorated with `LOGIN_LIMIT`. The endpoints `/api/health`, `/api/environment`, and `/api/metrics` are exempt. Limiting is per IP only (no JWT-based keys) and can be fully disabled with `RATE_LIMIT_ENABLED=false`.

---

## 6. Runtime View

### 6.1 User Login Flow

![User Login Flow](diagrams/login_flow.svg)

### 6.2 CRUD Operation Flow (via BaseResource)

![CRUD Operation Flow](diagrams/crud_flow.svg)

### 6.3 Health Check Flow

![Health Check Flow](diagrams/health_check_flow.svg)

---

## 7. Deployment View

### 7.1 Docker Deployment

![Docker Deployment View](diagrams/docker_deployment.svg)

### 7.2 Build & Run Commands

```bash
# Build
docker build . -t py-rest-api --build-arg PORT=5000

# Run
docker run --rm -p 5000:5000 --env-file .env py-rest-api
```

---

## 8. Cross-Cutting Concepts

### 8.1 Security Concept

- **Authentication:** JWT Bearer tokens issued at `/api/v1/auth/login`.
- **Password Storage:** bcrypt hashing with per-password salts.
- **Token Validation:** Every authenticated request validated via `decode_token` function referenced in swagger.yml as `x-bearerInfoFunc`.
- **Rate Limiting:** Per-IP throttling on all `/api/v1/*` endpoints with a stricter limit on `/auth/login`; `/api/health`, `/api/environment`, and `/api/metrics` are exempt.
- **CORS:** Configured via middleware allowing all origins (configurable).
- **Secret Management:** All secrets read from environment variables; JWT secret key has a development-only fallback.

### 8.2 Error Handling Strategy

- **Validation Errors:** HTTP 400 with RFC 9457 Problem Details JSON format.
- **Not Found:** HTTP 404 with problem details.
- **Rate Limit Exceeded:** HTTP 429 with RFC 9457 Problem Details format plus `Retry-After` and `X-RateLimit-*` headers.
- **Internal Errors:** Caught by Flask/Connexion error handlers, logged with stack trace.
- **Error Format:**
  ```json
  {
    "type": "BadRequest",
    "title": "Invalid parameters",
    "detail": "Item ID is not valid."
  }
  ```

### 8.3 Logging and Monitoring

- **Access Logging:** Every request logged via `@app.after_request` handler with remote address, method, scheme, path, and status.
- **File Logging:** Timed rotating file handler configured in production mode.
- **Health Checks:** MongoDB connectivity check exposed at `/api/health`.
- **Metrics:** Prometheus metrics exposed at `/api/metrics`.
- **Environment Info:** Application metadata at `/api/environment`.

### 8.4 Internationalization

Not implemented. All API messages are in English.

---

## 9. Architecture Decisions

### ADR-001: Connexion Framework over Pure Flask

| Property | Value |
|----------|-------|
| **Date** | 2025 |
| **Status** | Accepted |
| **Context** | Needed OpenAPI 3.0 contract-first API development with automatic request validation and Swagger UI. |
| **Decision** | Use Connexion 3 (FlaskApp) instead of pure Flask routing. |
| **Consequences** | Positive: Automatic request/response validation, generated Swagger UI. Negative: Additional dependency, opinionated routing via operationId. |

### ADR-002: BaseResource Generic CRUD

| Property | Value |
|----------|-------|
| **Date** | 2025 |
| **Status** | Accepted |
| **Context** | Categories, products, users, and roles all follow identical CRUD patterns with minor configuration differences. |
| **Decision** | Extract common CRUD logic into `BaseResource` class with configurable collection name, unique field, and stringify fields. |
| **Consequences** | Positive: ~400 lines of duplicated code eliminated, single point of change for CRUD behavior. Negative: Custom per-resource behavior requires extending the class. |

### ADR-003: Singleton MongoDB Connection

| Property | Value |
|----------|-------|
| **Date** | 2025 |
| **Status** | Accepted |
| **Context** | Multiple resources need database access; creating multiple MongoClient instances is wasteful. |
| **Decision** | Implement `MongoDbService` as a thread-safe singleton using a metaclass with double-checked locking. |
| **Consequences** | Positive: Single connection pool shared across resources. Negative: Cannot easily use separate databases for different resources. |

### ADR-004: ASGI via a2wsgi

| Property | Value |
|----------|-------|
| **Date** | 2025 |
| **Status** | Accepted |
| **Context** | Connexion 3 supports ASGI natively through FlaskApp wrapper. |
| **Decision** | Run FlaskApp on Uvicorn ASGI server via a2wsgi bridge. |
| **Consequences** | Positive: ASGI performance characteristics. Negative: WSGI-ASGI bridge adds minor overhead. |

### ADR-005: In-App Rate Limiting with Flask-Limiter

| Property | Value |
|----------|-------|
| **Date** | 2026-08-01 |
| **Status** | Accepted |
| **Context** | No protection against abuse or brute-force login attempts; previously tracked as an open risk. |
| **Decision** | Add per-IP request throttling using Flask-Limiter, configured entirely through `RATE_LIMIT_*` environment variables (moving-window strategy, in-memory storage by default, stricter limit on `/auth/login`, operational endpoints exempt). |
| **Consequences** | Positive: all API endpoints are throttled per IP; RFC 7807 429 responses with `Retry-After`; fully disableable. Negative: limiting is per-IP only (no JWT-based keys), and the default in-memory storage is not shared across workers/restarts — use `RATE_LIMIT_STORAGE_URI=redis://...` for multi-worker deployments. |

---

## 10. Quality Requirements

| Requirement | Metric | Target |
|-------------|--------|--------|
| Code Coverage | pytest-cov | >= 90% |
| Test Count | pytest | >= 50 |
| Response Time | Average (health) | < 500ms |
| API Specification Coverage | OpenAPI 3.0 | 100% of endpoints documented |
| Configuration Externalization | Environment variables | 100% of secrets and settings |

---

## 11. Risks and Technical Debt

| Risk | Impact | Mitigation |
|------|--------|------------|
| In-memory rate-limit storage resets per worker/restart | Inconsistent throttling in multi-worker deployments | Set `RATE_LIMIT_STORAGE_URI=redis://...` |
| Open CORS (`*`) | Security in production | Restrict CORS in production `.env` |
| No input sanitization beyond OpenAPI | Database injection | Add server-side validation layer |
| Single MongoDB connection | Availability | Add connection retry and failover |

---

## 12. API Reference

### 12.1 REST Endpoints

#### POST /api/v1/auth/login

**Description:** Authenticate with email and password  
**Authentication:** None  
**Authorization:** None  

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "your-password"
}
```

**Response — 200 OK:**
```json
{
  "user": {
    "_id": "62032250fdca5ca1a170d977",
    "name": "John Smith",
    "email": "user@example.com",
    "role": "ADMIN_ROLE"
  },
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Error Codes:**
| Code | Meaning |
|------|---------|
| 400  | Invalid credentials, missing fields |
| 429  | Too many requests (per-IP login limit exceeded) |

#### GET /api/v1/categories

**Description:** List all categories  
**Authentication:** Bearer Token  
**Authorization:** Any authenticated user  

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | - | Page number (omit for all) |
| `per_page` | integer | No | 20 | Items per page |

**Response — 200 OK:**
```json
{
  "items": [
    {
      "_id": "6208136134ffbeeabc4b1ead",
      "name": "PASTRIES",
      "active": true,
      "userId": "62032250fdca5ca1a170d977"
    }
  ],
  "count": 1
}
```

#### POST /api/v1/categories

**Description:** Create a new category  
**Authentication:** Bearer Token  

**Request Body:**
```json
{
  "name": "PASTRY ROLL"
}
```

**Response — 201 Created:**
```json
{
  "_id": "6208136134ffbeeabc4b1ead",
  "name": "PASTRY ROLL"
}
```

**Error Codes:**
| Code | Meaning |
|------|---------|
| 400  | Missing name, duplicate name, invalid body |

#### GET /api/v1/categories/{item_id}

**Description:** Get a single category by ID  
**Authentication:** Bearer Token  

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | string | Yes | MongoDB ObjectId (24 hex chars) |

**Error Codes:**
| Code | Meaning |
|------|---------|
| 400  | Invalid ObjectId format |
| 404  | Category not found |

#### PUT /api/v1/categories/{item_id}

**Description:** Update an existing category  
**Authentication:** Bearer Token  

**Request Body:**
```json
{
  "name": "Updated Name"
}
```

**Error Codes:**
| Code | Meaning |
|------|---------|
| 400  | Invalid ObjectId, empty body |
| 404  | Category not found |

#### DELETE /api/v1/categories/{item_id}

**Description:** Delete a category  
**Authentication:** Bearer Token  

**Error Codes:**
| Code | Meaning |
|------|---------|
| 400  | Invalid ObjectId |
| 404  | Category not found |

#### GET /api/v1/products

**Description:** List all products  
**Authentication:** Bearer Token  

**Query Parameters:** Same as categories (`page`, `per_page`)

#### POST /api/v1/products

**Description:** Create a new product  
**Authentication:** Bearer Token  

**Request Body:**
```json
{
  "name": "PASTRY ROLL",
  "categoryId": "62083fbdb5d9510f71cf6988",
  "price": 10.50,
  "available": true
}
```

#### GET /api/v1/products/{item_id}

**Description:** Get a single product by ID  
**Authentication:** Bearer Token  

#### PUT /api/v1/products/{item_id}

**Description:** Update an existing product  
**Authentication:** Bearer Token  

#### DELETE /api/v1/products/{item_id}

**Description:** Delete a product  
**Authentication:** Bearer Token  

#### GET /api/v1/users

**Description:** List all users (no count in response)  
**Authentication:** Bearer Token  

#### POST /api/v1/users

**Description:** Create a new user  
**Authentication:** Bearer Token  

**Request Body:**
```json
{
  "name": "John Smith",
  "email": "user@example.com",
  "password": "12345678",
  "role": "ADMIN_ROLE"
}
```

#### GET /api/v1/users/{item_id}

**Description:** Get a single user by ID  
**Authentication:** Bearer Token  

#### PUT /api/v1/users/{item_id}

**Description:** Update an existing user  
**Authentication:** Bearer Token  

#### DELETE /api/v1/users/{item_id}

**Description:** Delete a user  
**Authentication:** Bearer Token  

#### GET /api/v1/roles

**Description:** List all roles (no count in response)  
**Authentication:** Bearer Token  

#### POST /api/v1/roles

**Description:** Create a new role  
**Authentication:** Bearer Token  

**Request Body:**
```json
{
  "name": "ADMIN_ROLE"
}
```

#### GET /api/v1/roles/{item_id}

**Description:** Get a single role by ID  
**Authentication:** Bearer Token  

#### PUT /api/v1/roles/{item_id}

**Description:** Update an existing role  
**Authentication:** Bearer Token  

#### DELETE /api/v1/roles/{item_id}

**Description:** Delete a role  
**Authentication:** Bearer Token  

#### GET /api/health

**Description:** Health check including MongoDB connectivity  
**Authentication:** None  

**Response — 200 OK:**
```json
{
  "status": "OK",
  "info": {
    "status": "OK",
    "info": "{'version': '7.0.0'}"
  }
}
```

#### GET /api/environment

**Description:** Application metadata  
**Authentication:** None  

**Response — 200 OK:**
```json
{
  "application": {
    "maintainer": "David A. Mancilla",
    "git_repo": "https://github.com/dmancilla85/py-rest-server",
    "version": "1.0.0"
  }
}
```

#### GET /api/metrics

**Description:** Prometheus metrics  
**Authentication:** None  

**Response — 200 OK:** Prometheus text format `text/plain; version=0.0.4`

### 12.2 Data Models / Schemas

#### Category

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `_id` | ObjectId | No | Primary key (24 hex chars) |
| `name` | string | No | Category name (unique) |
| `active` | boolean | Yes | Current status |
| `userId` | ObjectId | Yes | Creator user ID |

#### Product

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `_id` | ObjectId | No | Primary key |
| `name` | string | No | Product name |
| `categoryId` | ObjectId | Yes | Category reference |
| `price` | number | Yes | Product price |
| `active` | boolean | Yes | Current status |
| `available` | boolean | Yes | Availability flag |

#### User

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `_id` | ObjectId | No | Primary key |
| `name` | string | No | Full name |
| `email` | string | No | Email address |
| `password` | string | No | bcrypt password hash |
| `img` | string | Yes | Profile image URL |
| `role` | string | No | User role (ADMIN_ROLE/USER_ROLE) |
| `active` | boolean | Yes | Account status |

#### Role

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `_id` | ObjectId | No | Primary key |
| `name` | string | No | Role name (unique via `role` field) |
| `active` | boolean | Yes | Current status |

### 12.3 Error Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200  | OK | Successful operation |
| 201  | Created | Resource successfully created |
| 400  | Bad Request | Invalid input, missing fields, duplicate, invalid ObjectId |
| 401  | Unauthorized | Missing or invalid JWT token |
| 404  | Not Found | Resource does not exist |
| 429  | Too Many Requests | Rate limit exceeded (per-IP), includes `Retry-After` |
| 500  | Internal Server Error | Unexpected server failure |

---

## 13. Configuration Reference

### 13.1 Environment Variables

#### PORT

- **Type:** integer
- **Required:** No
- **Default:** 5000
- **Description:** HTTP server port number.
- **Example:** `PORT=8080`

#### MODE

- **Type:** string
- **Required:** No
- **Default:** DEBUG
- **Description:** Application mode. Set to `PRODUCTION` to enable file logging.
- **Example:** `MODE=PRODUCTION`

#### MONGODB_CONN

- **Type:** string (URI)
- **Required:** Yes
- **Description:** MongoDB connection string.
- **Example:** `MONGODB_CONN=mongodb+srv://user:pass@cluster.mongodb.net`

#### MONGODB_DB

- **Type:** string
- **Required:** Yes
- **Description:** MongoDB database name.
- **Example:** `MONGODB_DB=my_database`

#### LOG_LEVEL

- **Type:** string
- **Required:** No
- **Default:** INFO
- **Description:** Logging level. Options: NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL.
- **Example:** `LOG_LEVEL=DEBUG`

#### LOG_PATH

- **Type:** string (path)
- **Required:** Yes (when MODE=PRODUCTION)
- **Description:** Directory path for log files.
- **Example:** `LOG_PATH=/var/log/api-rest`

#### LOG_BACKUP_COUNT

- **Type:** integer
- **Required:** No
- **Default:** 10
- **Description:** Number of days to retain rotated log files.
- **Example:** `LOG_BACKUP_COUNT=30`

#### JWT_ISSUER

- **Type:** string
- **Required:** No
- **Default:** localhost
- **Description:** JWT `iss` claim value.
- **Example:** `JWT_ISSUER=my-api.example.com`

#### JWT_AUDIENCE

- **Type:** string
- **Required:** No
- **Default:** localhost
- **Description:** JWT `aud` claim value.
- **Example:** `JWT_AUDIENCE=my-app`

#### JWT_LIFETIME_SECONDS

- **Type:** integer
- **Required:** No
- **Default:** 3600
- **Description:** JWT token expiration in seconds.
- **Example:** `JWT_LIFETIME_SECONDS=86400`

#### JWT_SECRET_KEY

- **Type:** string (secret)
- **Required:** No (falls back to MONGODB_CONN)
- **Description:** Secret key used to sign JWT tokens.
- **Example:** `JWT_SECRET_KEY=a-very-long-random-string`

#### RATE_LIMIT_ENABLED

- **Type:** boolean
- **Required:** No
- **Default:** `true`
- **Description:** Master switch for rate limiting; set to `false` to disable throttling entirely.
- **Example:** `RATE_LIMIT_ENABLED=false`

#### RATE_LIMIT_DEFAULT

- **Type:** string (`;`-separated limits)
- **Required:** No
- **Default:** `60 per minute; 5 per second`
- **Description:** Per-IP limits applied to all `/api/v1/*` endpoints.
- **Example:** `RATE_LIMIT_DEFAULT=120 per minute`

#### RATE_LIMIT_LOGIN

- **Type:** string
- **Required:** No
- **Default:** `5 per minute`
- **Description:** Per-IP limit applied to `/api/v1/auth/login` (stricter than the default).
- **Example:** `RATE_LIMIT_LOGIN=3 per minute`

#### RATE_LIMIT_STORAGE_URI

- **Type:** string
- **Required:** No
- **Default:** `memory://`
- **Description:** Rate-limit storage backend URI. Use a shared backend (e.g. `redis://localhost:6379`) for multi-worker deployments.
- **Example:** `RATE_LIMIT_STORAGE_URI=redis://localhost:6379`

### 13.2 Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables (excluded from git) |
| `example.env` | Template with placeholder values |
| `swagger.yml` | OpenAPI 3.0 API specification |
| `pyproject.toml` | Project metadata, dependencies, tool config |

---

## 14. Data Architecture

### 14.1 Entity Relationship Overview

![Entity Relationship Diagram](diagrams/er_diagram.svg)

### 14.2 Data Flow

![Data Flow](diagrams/data_flow.svg)

### 14.3 Data Retention and Lifecycle

- Data lifecycle is managed externally (e.g., MongoDB TTL indexes). The system does not enforce data retention policies.
- Deletion is permanent via DELETE endpoints.

---

## 15. Development Guide

### 15.1 Prerequisites

- Python 3.14+
- `uv` package manager
- MongoDB instance (local or remote)

### 15.2 Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/dmancilla85/py-rest-server.git
   cd api-rest
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Configure environment:
   ```bash
   cp example.env .env
   ```
   Edit `.env` with your MongoDB connection string.

4. Start the server:
   ```bash
   uv run python main.py
   ```

5. Verify:
   ```bash
   curl http://localhost:5000/api/health
   ```
   Open `http://localhost:5000/api/v1/ui` for Swagger UI.

### 15.3 Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=term

# Run specific test file
uv run pytest tests/test_app.py -v

# Run rate limiting tests
uv run pytest tests/test_rate_limit.py -v
```

### 15.4 Build and Deployment

```bash
# Docker build
docker build . -t py-rest-api

# Docker run
docker run --rm -p 5000:5000 --env-file .env py-rest-api

# Custom port
docker build . -t py-rest-api --build-arg PORT=8080
docker run --rm -p 8080:8080 --env-file .env py-rest-api
```

### 15.5 Coding Conventions

- Follow PEP 8 style (enforced by ruff).
- Maintain >90% test coverage.
- All secrets and configuration via environment variables (never hardcoded).
- API endpoints defined by operationId in swagger.yml matching resource function names.
- CRUD resources should extend or instantiate `BaseResource` rather than duplicating logic.
