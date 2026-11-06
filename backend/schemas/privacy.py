from datetime import datetime

from pydantic import BaseModel

from enums.candidate import AccessSource, ConsentPurpose, RevokeReason


class ConsentResponse(BaseModel):
    purpose: ConsentPurpose
    is_granted: bool
    granted_at: datetime | None
    revoked_at: datetime | None


class ConsentListResponse(BaseModel):
    items: list[ConsentResponse]
    total: int


class ConsentUpdate(BaseModel):
    is_granted: bool


class AccessGrantResponse(BaseModel):
    id: int
    company_name: str
    job_title: str
    source: AccessSource
    created_at: datetime
    revoked_at: datetime | None
    revoke_reason: RevokeReason | None


class AccessGrantListResponse(BaseModel):
    items: list[AccessGrantResponse]
    total: int
