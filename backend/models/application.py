from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field

from enums.candidate import ApplicationStatus
from models.base import TimestampedModel


class Application(TimestampedModel, table=True):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("job_id", "candidate_id"),)

    id: int | None = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="jobs.id", index=True)
    candidate_id: int = Field(foreign_key="candidate_profiles.id", index=True)
    status: ApplicationStatus = Field(default=ApplicationStatus.SUBMITTED, index=True)
    match_score: float | None = Field(default=None)
    cover_letter: str | None = Field(default=None, max_length=3000)
    # [{"status": "...", "at": "ISO datetime"}] - phục vụ tính tỷ lệ chuyển đổi theo phễu
    status_history: list[dict] = Field(default_factory=list, sa_column=Column(JSON))


class SavedJob(TimestampedModel, table=True):
    __tablename__ = "saved_jobs"
    __table_args__ = (UniqueConstraint("job_id", "candidate_id"),)

    id: int | None = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="jobs.id", index=True)
    candidate_id: int = Field(foreign_key="candidate_profiles.id", index=True)


class RecommendationFeedback(TimestampedModel, table=True):
    """Đánh giá 'gợi ý này có phù hợp không' - dữ liệu huấn luyện trọng số khớp."""

    __tablename__ = "recommendation_feedback"
    __table_args__ = (UniqueConstraint("job_id", "candidate_id"),)

    id: int | None = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="jobs.id", index=True)
    candidate_id: int = Field(foreign_key="candidate_profiles.id", index=True)
    is_relevant: bool
    features: dict = Field(default_factory=dict, sa_column=Column(JSON))
    comment: str | None = Field(default=None, max_length=1000)
