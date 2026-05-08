import errno
import os
import pytest
from unittest.mock import patch, MagicMock
from utils.logs import create_directory, setup_handler, setup_logging


class TestCreateDirectory:
    def test_creates_new_directory(self, tmp_path):
        new_dir = tmp_path / "new_subdir"
        create_directory(str(new_dir))
        assert new_dir.exists()

    def test_existing_directory_does_not_raise(self, tmp_path):
        create_directory(str(tmp_path))

    @patch("os.makedirs", side_effect=OSError(17, "File exists"))
    def test_ignores_already_exists_error(self, mock_makedirs):
        try:
            create_directory("/some/path")
        except Exception:
            pytest.fail("Should not raise on EEXIST")


class TestSetupHandler:
    @patch("logging.handlers.TimedRotatingFileHandler")
    def test_creates_handler_with_correct_path(self, mock_handler_cls):
        handler = setup_handler("test-app")
        mock_handler_cls.assert_called_once()
        args = mock_handler_cls.call_args[0]
        assert "test-app.log" in args[0]


class TestSetupLogging:
    @patch("utils.logs.setup_handler")
    def test_debug_mode_does_not_add_handler(self, mock_setup):
        mock_logger = MagicMock()
        setup_logging("test-app", logger=mock_logger)
        mock_setup.assert_not_called()
        mock_logger.setLevel.assert_called_once()

    @patch.dict(os.environ, {"MODE": "PRODUCTION", "LOG_LEVEL": "INFO", "LOG_PATH": "./logs", "LOG_BACKUP_COUNT": "10"})
    @patch("utils.logs.setup_handler")
    def test_production_adds_file_handler(self, mock_setup):
        mock_logger = MagicMock()
        mock_setup.return_value = "handler"
        setup_logging("test-app", logger=mock_logger)
        mock_setup.assert_called_once()
        mock_logger.addHandler.assert_called_once_with("handler")
