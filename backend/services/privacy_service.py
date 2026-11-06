"""Quản lý đồng ý theo mục đích và quyền xem hồ sơ (Luật Bảo vệ dữ liệu cá nhân 2025)."""

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from enums.candidate import AccessSource, ConsentPurpose, RevokeReason
from exceptions.base import ConsentRequiredError
from models.candidate import CandidateProfile
from models.job import Job
from models.organization import Company
from models.privacy import Consent, ProfileAccessGrant
from schemas.privacy import (
    AccessGrantListResponse,
    AccessGrantResponse,
    ConsentListResponse,
    ConsentResponse,
)
from utils.time import utcnow

CONSENT_LABELS: dict[ConsentPurpose, str] = {
    ConsentPurpose.CV_ANALYSIS: "phân tích CV tự động",
    ConsentPurpose.JOB_RECOMMENDATION: "gợi ý việc làm",
    ConsentPurpose.EMPLOYER_DISCOVERY: "cho phép nhà tuyển dụng tìm thấy bạn",
    ConsentPurpose.SCHOOL_SHARING: "chia sẻ dữ liệu tổng hợp với nhà trường",
    ConsentPurpose.MODEL_IMPROVEMENT: "dùng phản hồi để cải thiện mô hình",
}


async def _get_consents(db: AsyncSession, candidate_id: int) -> dict[ConsentPurpose, Consent]:
    rows = (await db.exec(select(Consent).where(Consent.candidate_id == candidate_id))).all()
    consents = {row.purpose: row for row in rows}
    missing = [purpose for purpose in ConsentPurpose if purpose not in consents]
    for purpose in missing:
        consent = Consent(candidate_id=candidate_id, purpose=purpose, is_granted=False)
        db.add(consent)
        consents[purpose] = consent
    if missing:
        await db.commit()
    return consents


async def has_consent(db: AsyncSession, candidate_id: int, purpose: ConsentPurpose) -> bool:
    consent = (
        await db.exec(
            select(Consent).where(Consent.candidate_id == candidate_id, Consent.purpose == purpose)
        )
    ).first()
    return bool(consent and consent.is_granted)


async def require_consent(db: AsyncSession, candidate_id: int, purpose: ConsentPurpose) -> None:
    if not await has_consent(db, candidate_id, purpose):
        raise ConsentRequiredError(
            f"Bạn cần đồng ý cho mục đích '{CONSENT_LABELS[purpose]}' trong trang Quyền riêng tư"
        )


async def consented_candidate_ids(db: AsyncSession, purpose: ConsentPurpose) -> set[int]:
    rows = await db.exec(
        select(Consent.candidate_id).where(Consent.purpose == purpose, col(Consent.is_granted))
    )
    return set(rows.all())


async def list_consents(db: AsyncSession, candidate_id: int) -> ConsentListResponse:
    consents = await _get_consents(db, candidate_id)
    items = [
        ConsentResponse(
            purpose=c.purpose, is_granted=c.is_granted,
            granted_at=c.granted_at, revoked_at=c.revoked_at,
        )
        for c in sorted(consents.values(), key=lambda c: list(ConsentPurpose).index(c.purpose))
    ]
    return ConsentListResponse(items=items, total=len(items))


async def update_consent(
    db: AsyncSession, candidate: CandidateProfile, purpose: ConsentPurpose, is_granted: bool
) -> ConsentResponse:
    consent = (await _get_consents(db, candidate.id))[purpose]
    now = utcnow()
    consent.is_granted = is_granted
    if is_granted:
        consent.granted_at, consent.revoked_at = now, None
    else:
        consent.revoked_at = now
        if purpose == ConsentPurpose.EMPLOYER_DISCOVERY:
            # Rút đồng ý -> ẩn hồ sơ và thu hồi mọi quyền xem có được qua tìm kiếm
            candidate.is_discoverable = False
            await revoke_grants(
                db, candidate_id=candidate.id, source=AccessSource.DISCOVERY,
                reason=RevokeReason.CONSENT_WITHDRAWN, commit=False,
            )
    consent.updated_at = now
    await db.commit()
    return ConsentResponse(
        purpose=consent.purpose, is_granted=consent.is_granted,
        granted_at=consent.granted_at, revoked_at=consent.revoked_at,
    )


async def grant_access(
    db: AsyncSession, *, company_id: int, candidate_id: int, job_id: int, source: AccessSource
) -> ProfileAccessGrant:
    existing = (
        await db.exec(
            select(ProfileAccessGrant).where(
                ProfileAccessGrant.company_id == company_id,
                ProfileAccessGrant.candidate_id == candidate_id,
                ProfileAccessGrant.job_id == job_id,
                col(ProfileAccessGrant.revoked_at).is_(None),
            )
        )
    ).first()
    if existing:
        return existing
    grant = ProfileAccessGrant(
        company_id=company_id, candidate_id=candidate_id, job_id=job_id, source=source
    )
    db.add(grant)
    return grant


async def has_active_access(db: AsyncSession, company_id: int, candidate_id: int) -> bool:
    grant = (
        await db.exec(
            select(ProfileAccessGrant).where(
                ProfileAccessGrant.company_id == company_id,
                ProfileAccessGrant.candidate_id == candidate_id,
                col(ProfileAccessGrant.revoked_at).is_(None),
            )
        )
    ).first()
    return grant is not None


async def revoke_grants(
    db: AsyncSession,
    *,
    reason: RevokeReason,
    candidate_id: int | None = None,
    job_id: int | None = None,
    source: AccessSource | None = None,
    commit: bool = True,
) -> int:
    """Thu hồi quyền xem hồ sơ (Điều 25): khi từ chối ứng viên, đóng vị trí, hoặc rút đồng ý."""
    query = select(ProfileAccessGrant).where(col(ProfileAccessGrant.revoked_at).is_(None))
    if candidate_id is not None:
        query = query.where(ProfileAccessGrant.candidate_id == candidate_id)
    if job_id is not None:
        query = query.where(ProfileAccessGrant.job_id == job_id)
    if source is not None:
        query = query.where(ProfileAccessGrant.source == source)
    grants = (await db.exec(query)).all()
    now = utcnow()
    for grant in grants:
        grant.revoked_at, grant.revoke_reason, grant.updated_at = now, reason, now
    if commit:
        await db.commit()
    return len(grants)


async def list_access_grants(db: AsyncSession, candidate_id: int) -> AccessGrantListResponse:
    rows = (
        await db.exec(
            select(ProfileAccessGrant, Company.name, Job.title)
            .join(Company, Company.id == ProfileAccessGrant.company_id)
            .join(Job, Job.id == ProfileAccessGrant.job_id)
            .where(ProfileAccessGrant.candidate_id == candidate_id)
            .order_by(col(ProfileAccessGrant.created_at).desc())
        )
    ).all()
    items = [
        AccessGrantResponse(
            id=grant.id, company_name=company_name, job_title=job_title, source=grant.source,
            created_at=grant.created_at, revoked_at=grant.revoked_at,
            revoke_reason=grant.revoke_reason,
        )
        for grant, company_name, job_title in rows
    ]
    return AccessGrantListResponse(items=items, total=len(items))
