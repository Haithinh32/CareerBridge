from datetime import datetime

from pydantic import BaseModel, Field

from enums.candidate import DocumentType, SkillSource
from enums.job import WorkType


class CandidateSkillResponse(BaseModel):
    skill_id: int
    name: str
    category: str
    source: SkillSource
    is_confirmed: bool
    level: int | None


class CandidateProfileResponse(BaseModel):
    id: int
    full_name: str
    email: str
    school_id: int | None
    school_name: str | None
    major: str | None
    study_year: int | None
    location: str | None
    work_types: list[str]
    availability: str | None
    target_position: str | None
    years_experience: float
    education: list[dict]
    projects: list[dict]
    is_discoverable: bool
    skills: list[CandidateSkillResponse]


class CandidateProfileUpdate(BaseModel):
    school_id: int | None = None
    major: str | None = Field(default=None, max_length=255)
    study_year: int | None = Field(default=None, ge=1, le=8)
    location: str | None = Field(default=None, max_length=120)
    work_types: list[WorkType] | None = None
    availability: str | None = Field(default=None, max_length=500)
    target_position: str | None = Field(default=None, max_length=255)
    years_experience: float | None = Field(default=None, ge=0, le=40)


class SkillConfirmItem(BaseModel):
    skill_id: int
    level: int | None = Field(default=None, ge=1, le=5)


class SkillConfirmRequest(BaseModel):
    """Danh sách kỹ năng cuối cùng sau khi ứng viên xác nhận/sửa; thay thế danh sách cũ."""

    skills: list[SkillConfirmItem]


class DiscoverableUpdate(BaseModel):
    is_discoverable: bool


class DocumentResponse(BaseModel):
    id: int
    document_type: DocumentType
    file_name: str
    parsed_at: datetime | None
    created_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int


class CvAnalysisResponse(BaseModel):
    document: DocumentResponse
    extracted_skills: list[CandidateSkillResponse]
    education: list[dict]
    projects: list[dict]
    years_experience: float
    email: str | None
    phone: str | None
