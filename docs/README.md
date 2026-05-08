# api-rest Documentation

**Version:** 1.0.0  
**Generated:** 2026-05-08  
**Project:** [py-rest-server](https://github.com/dmancilla85/py-rest-server)

---

## Documents

| Document | Description |
|----------|-------------|
| [SRS.md](./SRS.md) | Software Requirements Specification — functional and non-functional requirements following IEEE 830 standards. Contains 46 functional requirements with traceability matrix. |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Technical Documentation & System Architecture — arc42 architecture documentation with C4 model diagrams, API reference, data models, deployment guide, and environment variable reference. |
| [USER_MANUAL.md](./USER_MANUAL.md) | User Manual — step-by-step procedures for all API operations, authentication guide, troubleshooting, and glossary. |

---

## Quick Start

```bash
# Install dependencies
uv sync

# Configure environment
cp example.env .env
# Edit .env with your MongoDB connection string

# Run the server
uv run python main.py

# Open API docs
open http://localhost:5000/api/v1/ui
```

## Test Suite

52 tests — 96% code coverage:

```bash
uv run pytest --cov=app --cov-report=term
```
