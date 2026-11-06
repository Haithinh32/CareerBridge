from datetime import UTC, date, datetime


def utcnow() -> datetime:
    """Thời điểm hiện tại theo UTC, không kèm tzinfo (thống nhất giữa SQLite và PostgreSQL)."""
    return datetime.now(UTC).replace(tzinfo=None)


def today() -> date:
    return utcnow().date()
