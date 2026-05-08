import json
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from resources.base import BaseResource


@pytest.fixture
def app():
    return Flask(__name__)


@pytest.fixture
def app_ctx(app):
    with app.app_context():
        yield


@pytest.fixture
def mock_cursor():
    cursor = MagicMock()
    cursor.skip.return_value = cursor
    cursor.limit.return_value = []
    return cursor


@pytest.fixture
def resource(app, mock_collection, app_ctx):
    with patch("resources.base.MongoDbService") as mock_svc:
        instance = mock_svc.return_value
        instance.get_collection.return_value = mock_collection
        res = BaseResource("test_items", stringify_fields=["_id", "userId"])
        yield res


class TestGetItems:
    def test_returns_json_response(self, resource, app):
        with app.test_request_context("/"):
            result = resource.get_items()
        assert result.status_code == 200
        data = json.loads(result.get_data())
        assert "items" in data
        assert "count" in data

    def test_stringifies_fields(self, resource, mock_collection, app):
        mock_collection.find.return_value = [
            {"_id": "id1", "userId": "uid1", "name": "test"}
        ]
        with app.test_request_context("/"):
            result = resource.get_items()
        data = json.loads(result.get_data())
        assert data["count"] == 1

    def test_empty_collection(self, resource, mock_collection, app):
        mock_collection.find.return_value = []
        with app.test_request_context("/"):
            result = resource.get_items()
        data = json.loads(result.get_data())
        assert data["items"] == []
        assert data["count"] == 0

    def test_with_pagination(self, resource, mock_collection, app, mock_cursor):
        mock_collection.find.return_value = mock_cursor
        with app.test_request_context("/?page=1&per_page=10"):
            result = resource.get_items()
        data = json.loads(result.get_data())
        assert "items" in data
        mock_collection.find().skip.assert_called_once_with(0)
        mock_collection.find().skip().limit.assert_called_once_with(10)

    def test_without_pagination(self, resource, mock_collection, app):
        with app.test_request_context("/"):
            result = resource.get_items()
        mock_collection.find.assert_called_once_with()


class TestGetItem:
    def test_invalid_object_id(self, resource, app_ctx):
        result = resource.get_item("invalid-id")
        assert result.status_code == 400

    def test_item_not_found(self, resource, mock_collection, app_ctx):
        mock_collection.find_one.return_value = None
        result = resource.get_item("507f1f77bcf86cd799439011")
        assert result.status_code == 404

    def test_item_found(self, resource, mock_collection, app_ctx):
        mock_collection.find_one.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "name": "test",
            "userId": "uid1",
        }
        result = resource.get_item("507f1f77bcf86cd799439011")
        assert result.status_code == 200
        data = json.loads(result.get_data())
        assert data["name"] == "test"


class TestCreateItem:
    def test_empty_body(self, resource, app):
        with app.test_request_context("/", method="POST", data="{}", content_type="application/json"):
            result = resource.create_item()
        assert result.status_code == 400

    def test_creates_item_successfully(self, resource, mock_collection, app):
        mock_collection.find_one.return_value = None
        with app.test_request_context("/", method="POST",
                                       data=json.dumps({"name": "new-item"}),
                                       content_type="application/json"):
            result = resource.create_item()
        assert result[1] == 201
        data = json.loads(result[0].get_data())
        assert data["_id"] == "507f1f77bcf86cd799439011"

    def test_duplicate_item(self, resource, mock_collection, app):
        mock_collection.find_one.return_value = {"_id": "existing", "name": "dup"}
        with app.test_request_context("/", method="POST",
                                       data=json.dumps({"name": "dup"}),
                                       content_type="application/json"):
            result = resource.create_item()
        assert result.status_code == 400


class TestUpdateItem:
    def test_invalid_object_id(self, resource, app_ctx):
        result = resource.update_item("bad-id")
        assert result.status_code == 400

    def test_item_not_found(self, resource, mock_collection, app):
        mock_collection.update_one.return_value.matched_count = 0
        with app.test_request_context("/", method="PUT",
                                       data=json.dumps({"name": "anything"}),
                                       content_type="application/json"):
            result = resource.update_item("507f1f77bcf86cd799439011")
        assert result.status_code == 404

    def test_update_success(self, resource, mock_collection, app):
        mock_collection.update_one.return_value.matched_count = 1
        with app.test_request_context("/", method="PUT",
                                       data=json.dumps({"name": "updated"}),
                                       content_type="application/json"):
            result = resource.update_item("507f1f77bcf86cd799439011")
        assert result.status_code == 200
        data = json.loads(result.get_data())
        assert data["name"] == "updated"


class TestDeleteItem:
    def test_invalid_object_id(self, resource, app_ctx):
        result = resource.delete_item("bad-id")
        assert result.status_code == 400

    def test_item_not_found(self, resource, mock_collection, app_ctx):
        mock_collection.delete_one.return_value.deleted_count = 0
        result = resource.delete_item("507f1f77bcf86cd799439011")
        assert result.status_code == 404

    def test_delete_success(self, resource, mock_collection, app_ctx):
        mock_collection.delete_one.return_value.deleted_count = 1
        result = resource.delete_item("507f1f77bcf86cd799439011")
        assert result.status_code == 200
        data = json.loads(result.get_data())
        assert data["message"] == "Item deleted"


class TestResourceConfig:
    def test_no_count_for_roles(self, mock_collection, app):
        with patch("resources.base.MongoDbService") as mock_svc:
            mock_svc.return_value.get_collection.return_value = mock_collection
            res = BaseResource("roles", include_count=False)
            with app.test_request_context("/"):
                result = res.get_items()
            data = json.loads(result.get_data())
            assert "count" not in data

    def test_custom_unique_field(self, mock_collection):
        with patch("resources.base.MongoDbService") as mock_svc:
            mock_svc.return_value.get_collection.return_value = mock_collection
            res = BaseResource("roles", unique_field="role")
            assert res.unique_field == "role"
