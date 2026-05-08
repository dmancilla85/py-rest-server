import sys
import pytest
from unittest.mock import MagicMock, patch


def _reset():
    for m in list(sys.modules):
        if m.startswith("app") or m.startswith("connexion") or m in (
            "dotenv", "healthcheck", "prometheus_client",
            "flask_jwt_extended", "starlette.middleware.cors",
        ):
            sys.modules.pop(m, None)


class TestApplicationData:
    def test_returns_expected_values(self):
        _reset()
        with (
            patch("connexion.FlaskApp"),
            patch("dotenv.load_dotenv"),
            patch("utils.logs.setup_logging"),
            patch("healthcheck.HealthCheck"),
            patch("healthcheck.EnvironmentDump"),
        ):
            import app
            data = app.application_data()
            assert data["maintainer"] == "David A. Mancilla"
            assert "github.com" in data["git_repo"]
            assert data["version"] == "1.0.0"


class TestAppBootstrap:
    def _bootstrap_app(self, **extra_patches):
        _reset()
        mock_flask = MagicMock()

        mock_connexion_app = MagicMock()
        mock_connexion_app.app = mock_flask

        patches = dict(
            connexion_flaskapp=patch("connexion.FlaskApp", return_value=mock_connexion_app),
            dotenv=patch("dotenv.load_dotenv"),
            logging=patch("utils.logs.setup_logging"),
            healthcheck=patch("healthcheck.HealthCheck"),
            envdump=patch("healthcheck.EnvironmentDump"),
            jwt=patch("flask_jwt_extended.JWTManager"),
            metrics=patch("prometheus_client.generate_latest", return_value=b""),
        )
        patches.update(extra_patches)

        for p in patches.values():
            p.start()

        import app

        for p in reversed(list(patches.values())):
            p.stop()

        return app, mock_flask, mock_connexion_app

    def test_creates_flask_app(self):
        app, _, mock_ca = self._bootstrap_app()
        mock_ca.add_middleware.assert_called_once()
        mock_ca.add_api.assert_called_once_with("../swagger.yml")

    def test_adds_routes(self):
        from flask import Flask as RealFlask
        real_app = RealFlask(__name__)
        _reset()

        mock_ca = MagicMock()
        mock_ca.app = real_app

        with (
            patch("connexion.FlaskApp", return_value=mock_ca),
            patch("dotenv.load_dotenv"),
            patch("utils.logs.setup_logging"),
            patch("healthcheck.HealthCheck"),
            patch("healthcheck.EnvironmentDump"),
            patch("flask_jwt_extended.JWTManager"),
            patch("prometheus_client.generate_latest", return_value=b""),
        ):
            import app
            rules = [r.rule for r in real_app.url_map.iter_rules()]
            assert "/api/health" in rules
            assert "/api/environment" in rules
            assert "/api/metrics" in rules

    def test_jwt_secret_key_from_env(self):
        with patch.dict("os.environ", {"JWT_SECRET_KEY": "custom-secret"}, clear=False):
            app, mock_flask, _ = self._bootstrap_app()
            mock_flask.config.__setitem__.assert_any_call("JWT_SECRET_KEY", "custom-secret")

    def test_jwt_secret_fallback_to_mongodb(self):
        with patch.dict("os.environ", {
            "JWT_SECRET_KEY": "",
            "MONGODB_CONN": "mongodb://fallback",
        }, clear=False):
            app, mock_flask, _ = self._bootstrap_app()
            mock_flask.config.__setitem__.assert_any_call("JWT_SECRET_KEY", "mongodb://fallback")

    def test_adds_health_check(self):
        mock_hc = MagicMock()
        app, _, _ = self._bootstrap_app(
            healthcheck=patch("healthcheck.HealthCheck", return_value=mock_hc),
        )
        mock_hc.add_check.assert_called_once()


class TestAfterRequest:
    def test_returns_response(self):
        from flask import Flask as RealFlask
        real_app = RealFlask(__name__)
        _reset()

        mock_ca = MagicMock()
        mock_ca.app = real_app

        with (
            patch("connexion.FlaskApp", return_value=mock_ca),
            patch("dotenv.load_dotenv"),
            patch("utils.logs.setup_logging"),
            patch("healthcheck.HealthCheck"),
            patch("healthcheck.EnvironmentDump"),
            patch("flask_jwt_extended.JWTManager"),
            patch("prometheus_client.generate_latest", return_value=b""),
        ):
            import app
            resp = MagicMock()
            resp.status = "200 OK"
            with real_app.test_request_context("/"):
                result = app.after_request(resp)
            assert result == resp
