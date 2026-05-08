# REST-API Python

Flask + Connexion REST API with MongoDB, JWT auth, Prometheus metrics, and OpenAPI 3.0 spec.

## Quick Start

```bash
# Install dependencies
uv sync

# Copy and configure environment
cp example.env .env
# Edit .env with your MongoDB connection string

# Run the server
uv run python app/app.py
```

## Swagger UI

Open `http://localhost:5000/api/v1/ui` in your browser.

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
| API Spec | OpenAPI 3.0 (Swagger) |
| Monitoring | Prometheus metrics + health checks |
