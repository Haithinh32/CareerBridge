from datetime import datetime

from pydantic import BaseModel, Field

from enums.user import VerificationStatus
from schemas.job import JobResponse


class CompanyResponse(BaseModel):
    id: int
    name: str
    tax_code: str
    verification_status: VerificationStatus
    industry: str | None
    address: str | None
    website: str | None


class CompanyListResponse(BaseModel):
    items: list[CompanyResponse]
    total: int


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=120)
    address: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=255)


class SchoolResponse(BaseModel):
    id: int
    name: str


class SchoolListResponse(BaseModel):
    items: list[SchoolResponse]
    total: int


class SchoolLinkCreate(BaseModel):
    company_id: int


class FeedPostCreate(BaseModel):
    job_id: int
    note: str | None = Field(default=None, max_length=1000)


class FeedPostResponse(BaseModel):
    id: int
    school_name: str
    note: str | None
    created_at: datetime
    job: JobResponse


class FeedPostListResponse(BaseModel):
    items: list[FeedPostResponse]
    total: int
