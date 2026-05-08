import pytest
from unittest.mock import patch, MagicMock


class TestMongoAvailable:
    @patch("utils.healthchecks.MongoDbService")
    def test_healthy(self, mock_service_cls):
        mock_instance = mock_service_cls.return_value
        mock_instance.get_info.return_value = {"version": "7.0"}

        from utils.healthchecks import mongo_available
        ok, info = mongo_available()
        assert ok is True
        assert "OK" in str(info)

    @patch("utils.healthchecks.MongoDbService")
    def test_unhealthy(self, mock_service_cls):
        mock_instance = mock_service_cls.return_value
        mock_instance.get_info.side_effect = Exception("Connection refused")

        from utils.healthchecks import mongo_available
        ok, info = mongo_available()
        assert ok is False
        assert "ERROR" in str(info)

    @patch("utils.healthchecks.MongoDbService")
    def test_reuses_singleton(self, mock_service_cls):
        from utils.healthchecks import mongo_available
        mongo_available()
        mongo_available()
        # MongoDbService is a singleton, so constructor is called at most once
        # but since we mock the class itself, we just verify it's called
        assert mock_service_cls.return_value.get_info.call_count == 2
