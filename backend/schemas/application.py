from datetime import datetime

from pydantic import BaseModel, Field

from enums.candidate import ApplicationStatus


class ApplicationCreate(BaseModel):
    cover_letter: str | None = Field(default=None, max_length=3000)


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    job_title: str
    company_name: str
    candidate_id: int
    candidate_name: str | None = None
    status: ApplicationStatus
    match_score: float | None
    status_history: list[dict]
    created_at: datetime


class ApplicationListResponse(BaseModel):
    items: list[ApplicationResponse]
    total: int
