from datetime import date, datetime

from sqlalchemy import Column, Text, UniqueConstraint
from sqlmodel import Field

from enums.job import FlagType, JobLevel, JobSource, JobStatus, WorkType
from models.base import TimestampedModel


class Job(TimestampedModel, table=True):
    __tablename__ = "jobs"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int | None = Field(default=None, foreign_key="companies.id", index=True)
    company_name: str = Field(max_length=255)
    title: str = Field(max_length=255, index=True)
    description: str = Field(sa_column=Column(Text, nullable=False))
    location_raw: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=120, index=True)
    work_type: WorkType = Field(default=WorkType.FULL_TIME)
    level: JobLevel = Field(default=JobLevel.JUNIOR)
    salary_raw: str | None = Field(default=None, max_length=120)
    salary_min: int | None = Field(default=None)
    salary_max: int | None = Field(default=None)
    min_years_experience: float = Field(default=0)
    deadline: date | None = Field(default=None, index=True)
    status: JobStatus = Field(default=JobStatus.OPEN, index=True)
    source: JobSource = Field(default=JobSource.EMPLOYER)
    source_url: str | None = Field(default=None, max_length=500)
    external_id: str | None = Field(default=None, max_length=255, index=True)
    posted_at: datetime | None = Field(default=None, index=True)
    closed_at: datetime | None = Field(default=None)


class JobSkill(TimestampedModel, table=True):
    __tablename__ = "job_skills"
    __table_args__ = (UniqueConstraint("job_id", "skill_id"),)

    id: int | None = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="jobs.id", index=True)
    skill_id: int = Field(foreign_key="skills.id", index=True)
    is_required: bool = Field(default=True)


class JobFlag(TimestampedModel, table=True):
    """Cờ chất lượng do hệ thống tự gắn; tin có cờ chưa xử lý nằm trong vùng cách ly."""

    __tablename__ = "job_flags"

    id: int | None = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="jobs.id", index=True)
    flag_type: FlagType = Field(index=True)
    score: float = Field(default=1.0)
    detail: str = Field(max_length=1000)
    related_job_id: int | None = Field(default=None, foreign_key="jobs.id")
    is_resolved: bool = Field(default=False, index=True)
    resolved_by: int | None = Field(default=None, foreign_key="users.id")
    resolution_note: str | None = Field(default=None, max_length=1000)
