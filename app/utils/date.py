from datetime import datetime, timezone


def get_iso_time() -> str:
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
