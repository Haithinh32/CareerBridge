from datetime import datetime

from sqlmodel import Field, UniqueConstraint

from enums.candidate import AccessSource, ConsentPurpose, RevokeReason
from models.base import TimestampedModel


class Consent(TimestampedModel, table=True):
    """Đồng ý xử lý dữ liệu cá nhân, tách riêng theo từng mục đích."""

    __tablename__ = "consents"
    __table_args__ = (UniqueConstraint("candidate_id", "purpose"),)

    id: int | None = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="candidate_profiles.id", index=True)
    purpose: ConsentPurpose
    is_granted: bool = Field(default=False)
    granted_at: datetime | None = Field(default=None)
    revoked_at: datetime | None = Field(default=None)


class ProfileAccessGrant(TimestampedModel, table=True):
    """Quyền xem hồ sơ của doanh nghiệp; bị thu hồi khi từ chối ứng viên hoặc đóng vị trí."""

    __tablename__ = "profile_access_grants"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    candidate_id: int = Field(foreign_key="candidate_profiles.id", index=True)
    job_id: int = Field(foreign_key="jobs.id", index=True)
    source: AccessSource
    revoked_at: datetime | None = Field(default=None, index=True)
    revoke_reason: RevokeReason | None = Field(default=None)
