from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class TimestampedModel(SQLModel):
    """Các cột dùng chung: thời điểm tạo/cập nhật và xóa mềm."""

    created_at: datetime = Field(default_factory=_utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=_utcnow, nullable=False)
    deleted_at: datetime | None = Field(default=None, index=True)
