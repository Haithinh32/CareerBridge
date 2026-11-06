from datetime import date, datetime

from pydantic import BaseModel, Field

from enums.job import FlagType, JobLevel, JobSource, JobStatus, ReviewAction, WorkType
from schemas.skill import SkillRef


class JobSkillInput(BaseModel):
    skill_id: int
    is_required: bool = True


class JobCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=20)
    location: str = Field(max_length=255)
    work_type: WorkType = WorkType.FULL_TIME
    level: JobLevel = JobLevel.JUNIOR
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    salary_raw: str | None = Field(default=None, max_length=120)
    min_years_experience: float = Field(default=0, ge=0, le=30)
    deadline: date
    skills: list[JobSkillInput] = Field(min_length=1)


class JobUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    location: str | None = Field(default=None, max_length=255)
    work_type: WorkType | None = None
    level: JobLevel | None = None
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    min_years_experience: float | None = Field(default=None, ge=0, le=30)
    deadline: date | None = None
    skills: list[JobSkillInput] | None = None


class JobFlagResponse(BaseModel):
    id: int
    flag_type: FlagType
    score: float
    detail: str
    related_job_id: int | None
    is_resolved: bool


class JobResponse(BaseModel):
    id: int
    company_id: int | None
    company_name: str
    title: str
    description: str
    location: str | None
    location_raw: str | None
    work_type: WorkType
    level: JobLevel
    salary_min: int | None
    salary_max: int | None
    salary_raw: str | None
    min_years_experience: float
    deadline: date | None
    status: JobStatus
    source: JobSource
    posted_at: datetime | None
    required_skills: list[SkillRef]
    optional_skills: list[SkillRef]
    application_count: int = 0
    flags: list[JobFlagResponse] = []


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int


class ReviewRequest(BaseModel):
    action: ReviewAction
    note: str | None = Field(default=None, max_length=1000)
    updates: JobUpdate | None = None
    # Bổ sung từ điển khi duyệt: {"alias": "reactjs", "skill_id": 3}
    new_aliases: list[dict] = []
