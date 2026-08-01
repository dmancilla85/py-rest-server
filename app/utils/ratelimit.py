"""
Rate limiting setup.

The limiter is created here (app-less) so that ``resources.*`` modules can import
it for the ``@limiter.limit`` decorator without creating an import cycle with
``app.py``. ``app.py`` calls ``limiter.init_app(app)`` after the Flask app exists.
"""
from os import environ as env

from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Flask routes that must never be rate limited.
EXEMPT_ENDPOINTS = frozenset({"healthcheck", "environment", "metrics", "static"})
# Connexion swagger UI / spec paths served by the API itself.
EXEMPT_PREFIXES = ("/api/v1/ui", "/api/v1/openapi.json", "/api/v1/swagger.json")

DEFAULT_LIMITS = env.get("RATE_LIMIT_DEFAULT", "60 per minute; 5 per second")
LOGIN_LIMIT = env.get("RATE_LIMIT_LOGIN", "5 per minute")
STORAGE_URI = env.get("RATE_LIMIT_STORAGE_URI", "memory://")


def _enabled() -> bool:
    return env.get("RATE_LIMIT_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}


def _parse_limits(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(";") if part.strip()]


def _is_exempt() -> bool:
    if request.endpoint in EXEMPT_ENDPOINTS:
        return True
    return request.path.startswith(EXEMPT_PREFIXES)


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=_parse_limits(DEFAULT_LIMITS),
    default_limits_exempt_when=_is_exempt,
    storage_uri=STORAGE_URI,
    strategy="moving-window",
    headers_enabled=True,
    enabled=_enabled(),
)
