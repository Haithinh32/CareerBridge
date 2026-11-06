from datetime import datetime

from sqlalchemy import JSON, Column, Text, UniqueConstraint
from sqlmodel import Field

from enums.candidate import DocumentType, FileFormat, SkillSource
from models.base import TimestampedModel


class CandidateProfile(TimestampedModel, table=True):
    __tablename__ = "candidate_profiles"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True)
    school_id: int | None = Field(default=None, foreign_key="schools.id", index=True)
    major: str | None = Field(default=None, max_length=255)
    study_year: int | None = Field(default=None)
    location: str | None = Field(default=None, max_length=120, index=True)
    work_types: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    availability: str | None = Field(default=None, max_length=500)
    target_position: str | None = Field(default=None, max_length=255)
    years_experience: float = Field(default=0)
    education: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    projects: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    cv_text: str | None = Field(default=None, sa_column=Column(Text))
    is_discoverable: bool = Field(default=False)


class CandidateSkill(TimestampedModel, table=True):
    __tablename__ = "candidate_skills"
    __table_args__ = (UniqueConstraint("candidate_id", "skill_id"),)

    id: int | None = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="candidate_profiles.id", index=True)
    skill_id: int = Field(foreign_key="skills.id", index=True)
    source: SkillSource = Field(default=SkillSource.MANUAL)
    is_confirmed: bool = Field(default=False)
    level: int | None = Field(default=None, ge=1, le=5)


class CandidateDocument(TimestampedModel, table=True):
    """CV, đồ án hoặc hồ sơ LinkedIn xuất PDF mà ứng viên tải lên."""

    __tablename__ = "candidate_documents"

    id: int | None = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="candidate_profiles.id", index=True)
    document_type: DocumentType
    file_format: FileFormat
    file_name: str = Field(max_length=255)
    storage_path: str = Field(max_length=500)
    raw_text: str | None = Field(default=None, sa_column=Column(Text))
    parsed_at: datetime | None = Field(default=None)
