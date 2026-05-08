from datetime import datetime, timezone


def get_date():
    format_str = "%Y-%m-%dT%H:%M:%S.%f"
    return datetime.now().strftime(format_str)


def get_utc_date():
    return datetime.now(timezone.utc).isoformat()