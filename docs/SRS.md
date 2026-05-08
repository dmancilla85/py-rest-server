# Software Requirements Specification

| Field | Value |
|-------|-------|
| **Project Name** | api-rest |
| **Document ID** | SRS-API-REST-v1.0.0 |
| **Version** | 1.0.0 |
| **Status** | Approved |
| **Date** | 2026-05-08 |
| **Authors** | David A. Mancilla |
| **Classification** | Internal |

---

## Revision History

| Version | Date | Description | Author |
|---------|------|-------------|--------|
| 1.0.0 | 2026-05-08 | Initial release | David A. Mancilla |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [System Features (Functional Requirements)](#3-system-features-functional-requirements)
4. [External Interface Requirements](#4-external-interface-requirements)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [Appendix A: Requirements Traceability Matrix](#appendix-a-requirements-traceability-matrix)

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification defines the functional and non-functional requirements for the api-rest system version 1.0.0. It is intended for use by development teams, QA engineers, project managers, and stakeholders to establish a shared understanding of system behavior. This document does not describe implementation details or system architecture.

### 1.2 Scope

The system is a RESTful API server that provides CRUD operations for products, categories, users, and roles backed by a MongoDB database. It handles authentication via JWT tokens, exposes health check and metrics endpoints for monitoring, and supports Swagger/OpenAPI 3.0 interactive documentation. The system explicitly does NOT provide a user interface, email notifications, payment processing, or third-party identity federation beyond password-based login.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|------|------------|
| API | Application Programming Interface |
| CRUD | Create, Read, Update, Delete |
| JWT | JSON Web Token |
| MongoDB | NoSQL document database |
| REST | Representational State Transfer |
| SRS | Software Requirements Specification |
| FR | Functional Requirement |
| NFR | Non-Functional Requirement |
| CORS | Cross-Origin Resource Sharing |
| Prometheus | Open-source monitoring and alerting toolkit |

### 1.4 References

| Reference | Description |
|-----------|-------------|
| OpenAPI 3.0 | API specification format used by swagger.yml |
| RFC 7519 | JSON Web Token standard |
| Flask 3 | Web framework documentation |
| Connexion 3 | OpenAPI-first framework for Flask |

### 1.5 Overview

This document is organized into six sections. Section 1 provides the introduction. Section 2 describes the overall product context. Section 3 lists all functional requirements organized by feature. Section 4 covers external interfaces. Section 5 specifies non-functional requirements. Appendix A provides a traceability matrix.

---

## 2. Overall Description

### 2.1 Product Perspective

The api-rest system is a standalone REST API server. It depends on an external MongoDB instance for data persistence. It does not depend on any other internal systems or services. Consumers are client applications (web, mobile, or CLI) that communicate over HTTP.

```
┌─────────────────────────────────────────────────┐
│                 External Systems                 │
│  [MongoDB Atlas / Self-hosted MongoDB]           │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
                ┌──────────────┐
                │  api-rest    │
                │  (REST API)  │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │  Client App  │
                │  (Web/Mobile)│
                └──────────────┘
```

### 2.2 Product Functions (Summary)

- **Authentication:** Login with email and password, JWT token issuance and validation.
- **Category Management:** Create, read, update, and delete product categories.
- **Product Management:** Create, read, update, and delete products.
- **User Management:** Create, read, update, and delete system users.
- **Role Management:** Create, read, update, and delete user roles.
- **Monitoring:** Health check endpoint, environment information dump, Prometheus metrics.
- **API Documentation:** Interactive Swagger UI at `/api/v1/ui`.

### 2.3 User Classes and Characteristics

| User Class | Description | Technical Sophistication | Frequency | Primary Goals | Privileges |
|------------|-------------|--------------------------|-----------|---------------|------------|
| API Client | Application or service consuming the API | High | Variable | Perform CRUD operations, authenticate | Varies by JWT claims |
| Administrator | User managing the system | Medium | Daily | Manage users, roles, monitor health | Full access |
| Developer | Engineer integrating with the API | High | Frequent | Read API docs, test endpoints | Varies |

### 2.4 Operating Environment

| Component | Specification |
|-----------|---------------|
| Runtime | Python 3.14+ |
| Server | Uvicorn (ASGI) via a2wsgi |
| Database | MongoDB 6.0+ |
| Operating System | Linux (production), Windows/macOS (development) |
| Container | Docker with Python 3.14 base image |

### 2.5 Design and Implementation Constraints

- All API responses SHALL conform to REST conventions.
- API specification SHALL be defined in OpenAPI 3.0 format (swagger.yml).
- Authentication SHALL use JWT Bearer tokens.
- Passwords SHALL be hashed using bcrypt.
- The system SHALL operate behind a reverse proxy in production.

### 2.6 User Documentation

- Swagger UI interactive documentation at `/api/v1/ui`.
- Technical documentation in `docs/ARCHITECTURE.md`.
- User manual in `docs/USER_MANUAL.md`.

### 2.7 Assumptions and Dependencies

- A MongoDB instance is available and reachable at the configured connection string.
- Network access to MongoDB is permitted from the server's network.
- The JWT secret key is provided via environment variable.
- Prometheus monitoring infrastructure is external (if used).

---

## 3. System Features (Functional Requirements)

### 3.1 Authentication

#### 3.1.1 Description and Priority

The system SHALL authenticate users via email and password, issuing a JWT token upon successful authentication. **Priority: Critical**

#### 3.1.2 Stimulus/Response Sequences

- **Stimulus:** Client sends POST request to `/api/v1/auth/login` with email and password.
- **Response:** System returns JWT token and user object on success, or error details on failure.

#### 3.1.3 Functional Requirements

- **FR-001:** The system SHALL accept POST requests to `/api/v1/auth/login` with a JSON body containing `email` and `password` fields.
- **FR-002:** The system SHALL return HTTP 400 if the request body is missing or empty.
- **FR-003:** The system SHALL return HTTP 400 if `email` or `password` fields are empty.
- **FR-004:** The system SHALL look up the user by email in the `users` MongoDB collection.
- **FR-005:** The system SHALL return HTTP 400 with error detail "Email is not valid" if no user matches the provided email.
- **FR-006:** The system SHALL verify the password against the stored bcrypt hash.
- **FR-007:** The system SHALL return HTTP 400 with error detail "The password is incorrect" if the password does not match.
- **FR-008:** The system SHALL issue a JWT access token on successful authentication.
- **FR-009:** The system SHALL include `iss`, `iat`, `aud`, `exp`, and `sub` claims in the JWT.
- **FR-010:** The system SHALL return HTTP 200 with the user object and token on successful login.

### 3.2 Category Management

#### 3.2.1 Description and Priority

The system SHALL provide full CRUD operations for product categories. **Priority: High**

#### 3.2.2 Stimulus/Response Sequences

- **Stimulus:** Client sends GET/POST/PUT/DELETE requests to `/api/v1/categories` or `/api/v1/categories/{item_id}`.
- **Response:** System returns the requested data, creation confirmation, update confirmation, or deletion confirmation.

#### 3.2.3 Functional Requirements

- **FR-011:** The system SHALL list all categories when receiving GET `/api/v1/categories`.
- **FR-012:** The system SHALL accept pagination via `page` and `per_page` query parameters on GET `/api/v1/categories`.
- **FR-013:** The system SHALL create a new category when receiving POST `/api/v1/categories` with a JSON body.
- **FR-014:** The system SHALL return HTTP 201 with the created category on successful creation.
- **FR-015:** The system SHALL return HTTP 400 if a category with the same name already exists.
- **FR-016:** The system SHALL return a single category when receiving GET `/api/v1/categories/{item_id}`.
- **FR-017:** The system SHALL return HTTP 400 if `item_id` is not a valid MongoDB ObjectId.
- **FR-018:** The system SHALL return HTTP 404 if the category ID does not exist.
- **FR-019:** The system SHALL update a category when receiving PUT `/api/v1/categories/{item_id}`.
- **FR-020:** The system SHALL delete a category when receiving DELETE `/api/v1/categories/{item_id}`.
- **FR-021:** The system SHALL return HTTP 200 with confirmation message on successful deletion.

### 3.3 Product Management

#### 3.3.1 Description and Priority

The system SHALL provide full CRUD operations for products. **Priority: High**

#### 3.3.2 Stimulus/Response Sequences

- **Stimulus:** Client sends GET/POST/PUT/DELETE requests to `/api/v1/products` or `/api/v1/products/{item_id}`.
- **Response:** System returns product list, single product, or operation confirmation.

#### 3.3.3 Functional Requirements

- **FR-022:** The system SHALL list all products when receiving GET `/api/v1/products`.
- **FR-023:** The system SHALL support pagination on GET `/api/v1/products` via `page` and `per_page` query parameters.
- **FR-024:** The system SHALL create a new product when receiving POST `/api/v1/products`.
- **FR-025:** The system SHALL return HTTP 201 with the created product on successful creation.
- **FR-026:** The system SHALL return a single product when receiving GET `/api/v1/products/{item_id}`.
- **FR-027:** The system SHALL validate `item_id` as a valid MongoDB ObjectId for product operations.
- **FR-028:** The system SHALL update a product when receiving PUT `/api/v1/products/{item_id}`.
- **FR-029:** The system SHALL delete a product when receiving DELETE `/api/v1/products/{item_id}`.

### 3.4 User Management

#### 3.4.1 Description and Priority

The system SHALL provide CRUD operations for system users. **Priority: High**

#### 3.4.2 Stimulus/Response Sequences

- **Stimulus:** Client sends GET/POST/PUT/DELETE requests to `/api/v1/users` or `/api/v1/users/{item_id}`.
- **Response:** System returns user data or operation confirmation.

#### 3.4.3 Functional Requirements

- **FR-030:** The system SHALL list all users when receiving GET `/api/v1/users`.
- **FR-031:** The system SHALL NOT include a count in user list responses.
- **FR-032:** The system SHALL create a new user when receiving POST `/api/v1/users`.
- **FR-033:** The system SHALL return a single user when receiving GET `/api/v1/users/{item_id}`.
- **FR-034:** The system SHALL update a user when receiving PUT `/api/v1/users/{item_id}`.
- **FR-035:** The system SHALL delete a user when receiving DELETE `/api/v1/users/{item_id}`.

### 3.5 Role Management

#### 3.5.1 Description and Priority

The system SHALL provide CRUD operations for user roles. **Priority: Medium**

#### 3.5.2 Stimulus/Response Sequences

- **Stimulus:** Client sends GET/POST/PUT/DELETE requests to `/api/v1/roles` or `/api/v1/roles/{item_id}`.
- **Response:** System returns role data or operation confirmation.

#### 3.5.3 Functional Requirements

- **FR-036:** The system SHALL list all roles when receiving GET `/api/v1/roles`.
- **FR-037:** The system SHALL NOT include a count in role list responses.
- **FR-038:** The system SHALL create a new role when receiving POST `/api/v1/roles`.
- **FR-039:** The system SHALL check uniqueness on the `role` field (not `name`) for roles.
- **FR-040:** The system SHALL return a single role when receiving GET `/api/v1/roles/{item_id}`.
- **FR-041:** The system SHALL update a role when receiving PUT `/api/v1/roles/{item_id}`.
- **FR-042:** The system SHALL delete a role when receiving DELETE `/api/v1/roles/{item_id}`.

### 3.6 Health and Monitoring

#### 3.6.1 Description and Priority

The system SHALL expose health check, environment information, and Prometheus metrics endpoints. **Priority: Medium**

#### 3.6.2 Stimulus/Response Sequences

- **Stimulus:** Client requests `/api/health`, `/api/environment`, or `/api/metrics`.
- **Response:** System returns health status, application metadata, or Prometheus-formatted metrics.

#### 3.6.3 Functional Requirements

- **FR-043:** The system SHALL expose GET `/api/health` returning health check results including MongoDB connectivity.
- **FR-044:** The system SHALL expose GET `/api/environment` returning application metadata including maintainer, repository URL, and version.
- **FR-045:** The system SHALL expose GET `/api/metrics` returning Prometheus-formatted metrics data.
- **FR-046:** The system SHALL log every HTTP request with remote address, method, scheme, path, and response status.

---

## 4. External Interface Requirements

### 4.1 User Interfaces

The system SHALL serve Swagger UI at `/api/v1/ui` for interactive API documentation and testing.

### 4.2 Hardware Interfaces

No direct hardware interface requirements.

### 4.3 Software Interfaces

| Interface | Technology | Details |
|-----------|------------|---------|
| MongoDB | PyMongo 4.17 | Database operations via MongoDB connection string |
| Prometheus | prometheus-client 0.25 | Metrics exposition at `/api/metrics` |
| Swagger UI | swagger-ui-bundle 1.1 | Interactive API documentation |

### 4.4 Communications Interfaces

| Protocol | Port | Encryption | Details |
|----------|------|------------|---------|
| HTTP | 5000 (configurable) | None (terminated at reverse proxy) | REST API |
| MongoDB | 27017 (external) | TLS (optional) | Database connection |

---

## 5. Non-Functional Requirements

### 5.1 Performance Requirements (NFR-P)

- **NFR-P-001:** The system SHALL respond to health check requests within 500ms.
- **NFR-P-002:** The system SHALL list paginated resources within 1 second for collections under 10,000 documents.

### 5.2 Security Requirements (NFR-SEC)

- **NFR-SEC-001:** The system SHALL require JWT Bearer token authentication for all CRUD operations on categories, products, users, and roles.
- **NFR-SEC-002:** The system SHALL hash passwords using bcrypt before storing them.
- **NFR-SEC-003:** The system SHALL NOT expose the JWT secret key in any response.
- **NFR-SEC-004:** The system SHALL validate JWT tokens on every authenticated request via the `decode_token` function.
- **NFR-SEC-005:** The system SHALL allow configurable CORS origins, methods, and headers.

### 5.3 Software Quality Attributes (NFR-Q)

- **NFR-Q-001:** The system SHALL maintain at least 90% code coverage as measured by pytest-cov.
- **NFR-Q-002:** The system SHALL use environment variables for all configurable settings.
- **NFR-Q-003:** The system SHALL follow the OpenAPI 3.0 specification defined in swagger.yml.

### 5.4 Reliability and Availability (NFR-R)

- **NFR-R-001:** The system SHALL detect MongoDB connection failures and report them via the health check endpoint.
- **NFR-R-002:** The system SHALL log errors with stack traces for all unexpected exceptions.

---

## 6. Appendix A: Requirements Traceability Matrix

| Req ID | Description | Feature | Priority | Status |
|--------|-------------|---------|----------|--------|
| FR-001 | Accept login POST request | Authentication | Critical | Implemented |
| FR-002 | Return 400 for empty body | Authentication | Critical | Implemented |
| FR-003 | Return 400 for empty fields | Authentication | Critical | Implemented |
| FR-004 | Lookup user by email | Authentication | Critical | Implemented |
| FR-005 | Return 400 for unknown email | Authentication | Critical | Implemented |
| FR-006 | Verify bcrypt password | Authentication | Critical | Implemented |
| FR-007 | Return 400 for wrong password | Authentication | Critical | Implemented |
| FR-008 | Issue JWT on success | Authentication | Critical | Implemented |
| FR-009 | Include standard JWT claims | Authentication | Critical | Implemented |
| FR-010 | Return user + token on success | Authentication | Critical | Implemented |
| FR-011 | List categories | Category Management | High | Implemented |
| FR-012 | Paginate categories | Category Management | High | Implemented |
| FR-013 | Create category | Category Management | High | Implemented |
| FR-014 | Return 201 on category creation | Category Management | High | Implemented |
| FR-015 | Reject duplicate category name | Category Management | High | Implemented |
| FR-016 | Get single category | Category Management | High | Implemented |
| FR-017 | Validate ObjectId | Category Management | High | Implemented |
| FR-018 | Return 404 for missing category | Category Management | High | Implemented |
| FR-019 | Update category | Category Management | High | Implemented |
| FR-020 | Delete category | Category Management | High | Implemented |
| FR-021 | Confirm deletion | Category Management | High | Implemented |
| FR-022 | List products | Product Management | High | Implemented |
| FR-023 | Paginate products | Product Management | High | Implemented |
| FR-024 | Create product | Product Management | High | Implemented |
| FR-025 | Return 201 on product creation | Product Management | High | Implemented |
| FR-026 | Get single product | Product Management | High | Implemented |
| FR-027 | Validate product ObjectId | Product Management | High | Implemented |
| FR-028 | Update product | Product Management | High | Implemented |
| FR-029 | Delete product | Product Management | High | Implemented |
| FR-030 | List users | User Management | High | Implemented |
| FR-031 | No count in user list | User Management | High | Implemented |
| FR-032 | Create user | User Management | High | Implemented |
| FR-033 | Get single user | User Management | High | Implemented |
| FR-034 | Update user | User Management | High | Implemented |
| FR-035 | Delete user | User Management | High | Implemented |
| FR-036 | List roles | Role Management | Medium | Implemented |
| FR-037 | No count in role list | Role Management | Medium | Implemented |
| FR-038 | Create role | Role Management | Medium | Implemented |
| FR-039 | Check uniqueness on role field | Role Management | Medium | Implemented |
| FR-040 | Get single role | Role Management | Medium | Implemented |
| FR-041 | Update role | Role Management | Medium | Implemented |
| FR-042 | Delete role | Role Management | Medium | Implemented |
| FR-043 | Health check endpoint | Monitoring | Medium | Implemented |
| FR-044 | Environment info endpoint | Monitoring | Medium | Implemented |
| FR-045 | Metrics endpoint | Monitoring | Medium | Implemented |
| FR-046 | HTTP request logging | Monitoring | Medium | Implemented |
