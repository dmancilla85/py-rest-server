"""
Rate limiting tests.

Each test re-imports the app modules with rate limiting enabled and tiny limits so
the enforcement can be observed without waiting. A fresh import is required because
the limits are read from the environment at import time by ``utils.ratelimit`` and
the in-memory storage is process-wide per ``Limiter`` instance.

The ``RATE_LIMIT_ENABLED=false`` default from ``conftest.py`` is overridden here and
restored afterwards so the rest of the suite keeps running without the limiter.
"""
import os
import sys
from unittest.mock import MagicMock, patch

import flask_jwt_extended
import pytest
from starlette.testclient import TestClient

RATE_LIMIT_ENABLED = "true"
RATE_LIMIT_DEFAULT = "3 per minute"
RATE_LIMIT_LOGIN = "2 per minute"
RATE_LIMIT_STORAGE_URI = "memory://"

RL_ENV_KEYS = (
    "RATE_LIMIT_ENABLED",
    "RATE_LIMIT_DEFAULT",
    "RATE_LIMIT_LOGIN",
    "RATE_LIMIT_STORAGE_URI",
)


def _purge():
    for m in list(sys.modules):
        if (
            m.startswith(("app", "connexion", "resources", "services", "utils", "flask_limiter"))
            or m
            in (
                "dotenv",
                "healthcheck",
                "prometheus_client",
                "flask_jwt_extended",
                "starlette.middleware.cors",
            )
        ):
            sys.modules.pop(m, None)


@pytest.fixture()
def fresh_app():
    saved = {key: os.environ.get(key) for key in RL_ENV_KEYS}
    os.environ["RATE_LIMIT_ENABLED"] = RATE_LIMIT_ENABLED
    os.environ["RATE_LIMIT_DEFAULT"] = RATE_LIMIT_DEFAULT
    os.environ["RATE_LIMIT_LOGIN"] = RATE_LIMIT_LOGIN
    os.environ["RATE_LIMIT_STORAGE_URI"] = RATE_LIMIT_STORAGE_URI

    _purge()

    app = _import_app_fresh()

    yield app

    _purge()
    for key, value in saved.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def _import_app_fresh():
    import app
    # app.py pushes the app context at import time. Pop it so it doesn't leak into
    # flask's contextvars (see tests/test_app.py for the rationale).
    from flask.globals import _cv_app
    ctx = _cv_app.get(None)
    if ctx is not None and ctx.app is app.app:
        ctx.pop()
    return app


@pytest.fixture()
def client(fresh_app):
    coll = MagicMock()
    coll.find.return_value = []
    coll.find_one.return_value = None

    with (
        patch("resources.base.MongoDbService") as mock_svc,
        patch("utils.healthchecks.MongoDbService") as health_svc,
        fresh_app.con_app.app.app_context(),
    ):
        mock_svc.return_value.get_collection.return_value = coll
        health_svc.return_value.get_info.return_value = {"ok": 1}
        yield TestClient(fresh_app.con_app)


@pytest.fixture()
def auth_headers(fresh_app):
    with fresh_app.con_app.app.test_request_context():
        token = flask_jwt_extended.create_access_token("tester")
    return {"Authorization": f"Bearer {token}"}


def _assert_rfc7807_429(response):
    assert response.status_code == 429
    body = response.json()
    assert body["status"] == 429
    assert body["title"] == "Too Many Requests"
    assert body["type"] == "/api/v1"
    assert "detail" in body


def test_default_limits_return_429(client, auth_headers):
    for _ in range(3):
        resp = client.get("/api/v1/categories", headers=auth_headers)
        assert resp.status_code == 200

    resp = client.get("/api/v1/categories", headers=auth_headers)
    _assert_rfc7807_429(resp)
    assert "Retry-After" in resp.headers
    assert "X-RateLimit-Limit" in resp.headers


def test_login_has_own_limit(client):
    users = MagicMock()
    users.find_one.return_value = None
    body = {"email": "user@test.com", "password": "secret"}

    with patch("resources.auth.users", users):
        for _ in range(2):
            resp = client.post("/api/v1/auth/login", json=body)
            assert resp.status_code == 400

        resp = client.post("/api/v1/auth/login", json=body)
        _assert_rfc7807_429(resp)


def test_login_limit_is_stricter_than_default(client):
    users = MagicMock()
    users.find_one.return_value = None
    body = {"email": "user@test.com", "password": "secret"}

    with patch("resources.auth.users", users):
        # The login limit (2/min) kicks in before the default limit (3/min).
        for _ in range(2):
            assert client.post("/api/v1/auth/login", json=body).status_code == 400
        assert client.post("/api/v1/auth/login", json=body).status_code == 429


def test_health_is_exempt_from_limits(client):
    for _ in range(6):
        resp = client.get("/api/health")
        assert resp.status_code == 200
