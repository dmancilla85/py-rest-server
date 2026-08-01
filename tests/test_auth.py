import json
import pytest
from unittest.mock import MagicMock, patch, ANY
from flask import Flask


@pytest.fixture
def app():
    return Flask(__name__)


@pytest.fixture
def app_ctx(app):
    with app.app_context():
        yield


class TestLogin:
    def test_missing_json_body(self, app):
        from resources.auth import login
        with app.test_request_context("/auth/login", method="POST",
                                       data="not-json", content_type="text/plain"):
            result = login()
        assert result.status_code == 400

    def test_empty_email(self, app):
        from resources.auth import login
        with app.test_request_context("/auth/login", method="POST",
                                       data=json.dumps({"email": "", "password": "pass"}),
                                       content_type="application/json"):
            result = login()
        assert result.status_code == 400

    def test_empty_password(self, app):
        from resources.auth import login
        with app.test_request_context("/auth/login", method="POST",
                                       data=json.dumps({"email": "user@test.com", "password": ""}),
                                       content_type="application/json"):
            result = login()
        assert result.status_code == 400

    def test_user_not_found(self, app):
        from resources.auth import users, login
        users.find_one = MagicMock(return_value=None)
        with app.test_request_context("/auth/login", method="POST",
                                       data=json.dumps({"email": "unknown@test.com", "password": "pass"}),
                                       content_type="application/json"):
            result = login()
        assert result.status_code == 400

    @patch("resources.auth._build_token", return_value="mock-token")
    def test_wrong_password(self, mock_token, app):
        from resources.auth import users, login
        import bcrypt
        hashed = bcrypt.hashpw(b"correct-password", bcrypt.gensalt())
        users.find_one = MagicMock(return_value={
            "_id": "507f1f77bcf86cd799439011",
            "email": "user@test.com",
            "password": hashed.decode("utf-8"),
        })
        with app.test_request_context("/auth/login", method="POST",
                                       data=json.dumps({"email": "user@test.com", "password": "wrong"}),
                                       content_type="application/json"):
            result = login()
        assert result.status_code == 400

    @patch("resources.auth._build_token", return_value="mock-token")
    def test_successful_login(self, mock_token, app):
        from resources.auth import users, login
        import bcrypt
        hashed = bcrypt.hashpw(b"correct-password", bcrypt.gensalt())
        users.find_one = MagicMock(return_value={
            "_id": "507f1f77bcf86cd799439011",
            "email": "user@test.com",
            "password": hashed.decode("utf-8"),
            "name": "Test User",
        })
        with app.test_request_context("/auth/login", method="POST",
                                       data=json.dumps({"email": "user@test.com", "password": "correct-password"}),
                                       content_type="application/json"):
            result = login()
        assert result.status_code == 200
        data = json.loads(result.get_data())
        assert data["token"] == "mock-token"
        assert data["user"]["email"] == "user@test.com"


class TestDecodeToken:
    @patch("flask_jwt_extended.decode_token", return_value={"sub": "user@test.com"})
    def test_valid_token(self, mock_decode):
        from resources.auth import decode_token
        result = decode_token("valid-token")
        assert result == {"sub": "user@test.com"}

    @patch("flask_jwt_extended.decode_token", side_effect=Exception("token expired"))
    def test_invalid_token(self, mock_decode):
        from resources.auth import decode_token
        result = decode_token("expired-token")
        assert result is None
