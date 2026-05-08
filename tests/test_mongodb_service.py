import pytest
from unittest.mock import patch, MagicMock


class TestSingletonMeta:
    def test_same_instance(self):
        from services.mongodb_service import MongoDbService

        with patch("services.mongodb_service.MongoClient") as mock_client:
            mock_client.return_value.server_info.return_value = {}
            a = MongoDbService()
            b = MongoDbService()
            assert a is b

    def test_initialization_failure(self):
        from services.mongodb_service import MongoDbService

        # Reset singleton for this test
        with patch.object(MongoDbService, "_instances", {}), \
             patch.object(MongoDbService, "_locks", {}), \
             patch("services.mongodb_service.MongoClient") as mock_client:
            mock_client.side_effect = Exception("Connection error")
            svc = MongoDbService()
            assert svc.is_connected() is False
            assert svc.get_info() == "Disconnected"


class TestMongoDbService:
    def test_get_collection_returns_none_when_disconnected(self):
        from services.mongodb_service import MongoDbService

        with patch.object(MongoDbService, "_instances", {}), \
             patch.object(MongoDbService, "_locks", {}), \
             patch("services.mongodb_service.MongoClient") as mock_client:
            mock_client.side_effect = Exception("fail")
            svc = MongoDbService()
            assert svc.get_collection("anything") is None

    def test_get_collection_returns_collection(self):
        from services.mongodb_service import MongoDbService

        with patch.object(MongoDbService, "_instances", {}), \
             patch.object(MongoDbService, "_locks", {}), \
             patch("services.mongodb_service.MongoClient") as mock_client:
            mock_db = MagicMock()
            mock_client.return_value.__getitem__.return_value = mock_db
            svc = MongoDbService()
            result = svc.get_collection("users")
            mock_db.__getitem__.assert_called_once_with("users")
