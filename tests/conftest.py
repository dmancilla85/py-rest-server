import os
import pytest
from unittest.mock import MagicMock, patch

os.environ.setdefault("MONGODB_CONN", "mongodb://test:27017")
os.environ.setdefault("MONGODB_DB", "test_db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ISSUER", "test-issuer")
os.environ.setdefault("JWT_AUDIENCE", "test-audience")
os.environ.setdefault("JWT_LIFETIME_SECONDS", "3600")
os.environ.setdefault("MODE", "DEBUG")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("LOG_PATH", "./test_logs")
os.environ.setdefault("LOG_BACKUP_COUNT", "5")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("RATE_LIMIT_DEFAULT", "60 per minute; 5 per second")
os.environ.setdefault("RATE_LIMIT_LOGIN", "5 per minute")
os.environ.setdefault("RATE_LIMIT_STORAGE_URI", "memory://")


@pytest.fixture
def mock_collection():
    coll = MagicMock()
    coll.find.return_value = []
    coll.find_one.return_value = None
    insert_result = MagicMock()
    insert_result.inserted_id = "507f1f77bcf86cd799439011"
    coll.insert_one.return_value = insert_result
    update_result = MagicMock()
    update_result.matched_count = 1
    coll.update_one.return_value = update_result
    delete_result = MagicMock()
    delete_result.deleted_count = 1
    coll.delete_one.return_value = delete_result
    return coll


@pytest.fixture
def mock_mongo_service(mock_collection):
    with patch("resources.base.MongoDbService") as mock_svc:
        instance = mock_svc.return_value
        instance.get_collection.return_value = mock_collection
        yield instance
