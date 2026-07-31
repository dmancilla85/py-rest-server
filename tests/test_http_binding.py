from unittest.mock import MagicMock, patch

import flask_jwt_extended
import pytest
from bson import ObjectId
from starlette.testclient import TestClient

from app import con_app

RESOURCES = ["categories", "products", "users", "roles"]

VALID_BODIES = {
    "categories": {"name": "updated"},
    "products": {"name": "updated", "categoryId": "62083fbdb5d9510f71cf6988"},
    "users": {"name": "John", "role": "ADMIN_ROLE", "email": "u@example.com", "password": "secret"},
    "roles": {"name": "updated"},
}


@pytest.fixture
def client():
    coll = MagicMock()
    coll.find.return_value = []
    coll.find_one.return_value = None
    delete_result = MagicMock()
    delete_result.deleted_count = 1
    coll.delete_one.return_value = delete_result
    update_result = MagicMock()
    update_result.matched_count = 1
    coll.update_one.return_value = update_result

    with patch("resources.base.MongoDbService") as mock_svc:
        mock_svc.return_value.get_collection.return_value = coll
        yield TestClient(con_app)


@pytest.fixture
def auth_headers():
    with con_app.app.test_request_context():
        token = flask_jwt_extended.create_access_token("tester")
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("resource", RESOURCES)
def test_delete_item(client, auth_headers, resource):
    resp = client.delete(f"/api/v1/{resource}/{ObjectId()}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"message": "Item deleted"}


@pytest.mark.parametrize("resource", RESOURCES)
def test_update_item(client, auth_headers, resource):
    resp = client.put(
        f"/api/v1/{resource}/{ObjectId()}",
        headers=auth_headers,
        json=VALID_BODIES[resource],
    )
    assert resp.status_code == 200


@pytest.mark.parametrize("resource", RESOURCES)
def test_list_items(client, auth_headers, resource):
    resp = client.get(f"/api/v1/{resource}", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    if resource in ("categories", "products"):
        assert "count" in body
