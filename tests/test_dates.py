import re
from datetime import datetime
from utils.dates import get_date, get_utc_date


class TestGetDate:
    def test_returns_string(self):
        result = get_date()
        assert isinstance(result, str)

    def test_iso_format_with_milliseconds(self):
        result = get_date()
        assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3,6}", result)

    def test_is_local_time(self):
        result = get_date()
        local = datetime.now()
        assert result.startswith(local.strftime("%Y"))


class TestGetUtcDate:
    def test_returns_string(self):
        result = get_utc_date()
        assert isinstance(result, str)

    def test_ends_with_plus_offset(self):
        result = get_utc_date()
        assert "+00:00" in result or result.endswith("Z")
