from sqlmodel import Field, UniqueConstraint

from enums.user import VerificationStatus
from models.base import TimestampedModel


class Company(TimestampedModel, table=True):
    __tablename__ = "companies"

    id: int | None = Field(default=None, primary_key=True)
    owner_user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    name: str = Field(max_length=255, index=True)
    tax_code: str = Field(unique=True, max_length=20)
    verification_status: VerificationStatus = Field(default=VerificationStatus.PENDING)
    industry: str | None = Field(default=None, max_length=120)
    address: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=255)


class School(TimestampedModel, table=True):
    __tablename__ = "schools"

    id: int | None = Field(default=None, primary_key=True)
    owner_user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    name: str = Field(max_length=255, unique=True)


class SchoolCompanyLink(TimestampedModel, table=True):
    """Doanh nghiệp liên kết với nhà trường."""

    __tablename__ = "school_company_links"
    __table_args__ = (UniqueConstraint("school_id", "company_id"),)

    id: int | None = Field(default=None, primary_key=True)
    school_id: int = Field(foreign_key="schools.id", index=True)
    company_id: int = Field(foreign_key="companies.id", index=True)


class SchoolFeedPost(TimestampedModel, table=True):
    """Tin tuyển dụng của doanh nghiệp liên kết được nhà trường đẩy lên feed sinh viên."""

    __tablename__ = "school_feed_posts"

    id: int | None = Field(default=None, primary_key=True)
    school_id: int = Field(foreign_key="schools.id", index=True)
    job_id: int = Field(foreign_key="jobs.id", index=True)
    note: str | None = Field(default=None, max_length=1000)
