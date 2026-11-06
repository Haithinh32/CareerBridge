from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from enums.candidate import AccessSource, ApplicationStatus, ConsentPurpose, RevokeReason
from enums.job import JobStatus
from exceptions.base import (
    ConflictError,
    NotFoundError,
    ProfileAccessRevokedError,
    ValidationError,
)
from models.application import Application
from models.candidate import CandidateProfile
from models.job import Job
from models.user import User
from schemas.application import (
    ApplicationCreate,
    ApplicationListResponse,
    ApplicationResponse,
)
from schemas.candidate import CandidateProfileResponse
from services import (
    candidate_service,
    job_service,
    matching_service,
    organization_service,
    privacy_service,
)
from utils.time import utcnow

# Trạng thái nhà tuyển dụng được phép chuyển tới, theo trạng thái hiện tại
ALLOWED_TRANSITIONS: dict[ApplicationStatus, set[ApplicationStatus]] = {
    ApplicationStatus.SUBMITTED: {
        ApplicationStatus.VIEWED, ApplicationStatus.INTERVIEW, ApplicationStatus.REJECTED,
    },
    ApplicationStatus.VIEWED: {ApplicationStatus.INTERVIEW, ApplicationStatus.REJECTED},
    ApplicationStatus.INTERVIEW: {ApplicationStatus.HIRED, ApplicationStatus.REJECTED},
    ApplicationStatus.HIRED: set(),
    ApplicationStatus.REJECTED: set(),
}


def _history_entry(status: ApplicationStatus) -> dict:
    return {"status": status.value, "at": utcnow().isoformat()}


def _set_status(app: Application, status: ApplicationStatus) -> None:
    app.status = status
    app.status_history = [*(app.status_history or []), _history_entry(status)]
    app.updated_at = utcnow()


async def _responses(db: AsyncSession, apps: list[Application]) -> list[ApplicationResponse]:
    job_ids = {a.job_id for a in apps}
    candidate_ids = {a.candidate_id for a in apps}
    jobs = {j.id: j for j in (await db.exec(select(Job).where(col(Job.id).in_(job_ids)))).all()}
    names = dict(
        (
            await db.exec(
                select(CandidateProfile.id, User.full_name)
                .join(User, User.id == CandidateProfile.user_id)
                .where(col(CandidateProfile.id).in_(candidate_ids))
            )
        ).all()
    )
    return [
        ApplicationResponse(
            id=a.id, job_id=a.job_id, job_title=jobs[a.job_id].title,
            company_name=jobs[a.job_id].company_name, candidate_id=a.candidate_id,
            candidate_name=names.get(a.candidate_id), status=a.status,
            match_score=a.match_score, status_history=a.status_history or [],
            created_at=a.created_at,
        )
        for a in apps
    ]


async def apply(
    db: AsyncSession, profile: CandidateProfile, job_id: int, data: ApplicationCreate
) -> ApplicationResponse:
    job = await job_service.get_job_or_404(db, job_id)
    if job.status != JobStatus.OPEN:
        raise ValidationError("Tin tuyển dụng không còn nhận hồ sơ")
    existing = (
        await db.exec(
            select(Application).where(
                Application.job_id == job_id, Application.candidate_id == profile.id
            )
        )
    ).first()
    if existing:
        raise ConflictError("Bạn đã ứng tuyển tin này")

    match = await matching_service.match_score_for(db, profile, job)
    app = Application(
        job_id=job.id, candidate_id=profile.id, cover_letter=data.cover_letter,
        match_score=match.score, status_history=[_history_entry(ApplicationStatus.SUBMITTED)],
    )
    db.add(app)
    # Ứng tuyển = đồng ý cho doanh nghiệp này xem hồ sơ trong phạm vi vị trí này
    if job.company_id:
        await privacy_service.grant_access(
            db, company_id=job.company_id, candidate_id=profile.id, job_id=job.id,
            source=AccessSource.APPLICATION,
        )
    await db.commit()
    return (await _responses(db, [app]))[0]


async def list_for_candidate(db: AsyncSession, profile: CandidateProfile) -> ApplicationListResponse:
    apps = (
        await db.exec(
            select(Application)
            .where(Application.candidate_id == profile.id)
            .order_by(col(Application.created_at).desc())
        )
    ).all()
    return ApplicationListResponse(items=await _responses(db, list(apps)), total=len(apps))


async def list_for_job(db: AsyncSession, user: User, job_id: int) -> ApplicationListResponse:
    job = await job_service.get_owned_job(db, job_id, user)
    apps = (
        await db.exec(
            select(Application)
            .where(Application.job_id == job.id)
            .order_by(col(Application.match_score).desc())
        )
    ).all()
    return ApplicationListResponse(items=await _responses(db, list(apps)), total=len(apps))


async def update_status(
    db: AsyncSession, user: User, application_id: int, status: ApplicationStatus
) -> ApplicationResponse:
    app = await db.get(Application, application_id)
    if app is None:
        raise NotFoundError("Không tìm thấy hồ sơ ứng tuyển")
    await job_service.get_owned_job(db, app.job_id, user)
    if status not in ALLOWED_TRANSITIONS[app.status]:
        raise ValidationError(f"Không thể chuyển từ '{app.status.value}' sang '{status.value}'")
    _set_status(app, status)
    if status == ApplicationStatus.REJECTED:
        # Điều 25: từ chối ứng viên -> doanh nghiệp tự động mất quyền xem hồ sơ
        await privacy_service.revoke_grants(
            db, candidate_id=app.candidate_id, job_id=app.job_id,
            reason=RevokeReason.CANDIDATE_REJECTED, commit=False,
        )
    await db.commit()
    return (await _responses(db, [app]))[0]


async def view_candidate_profile(
    db: AsyncSession, user: User, candidate_id: int, job_id: int | None
) -> CandidateProfileResponse:
    company = await organization_service.get_company_for_user(db, user)
    profile = await db.get(CandidateProfile, candidate_id)
    if profile is None or profile.deleted_at is not None:
        raise NotFoundError("Không tìm thấy ứng viên")

    if not await privacy_service.has_active_access(db, company.id, candidate_id):
        can_discover = profile.is_discoverable and await privacy_service.has_consent(
            db, candidate_id, ConsentPurpose.EMPLOYER_DISCOVERY
        )
        if not can_discover or job_id is None:
            raise ProfileAccessRevokedError()
        job = await job_service.get_owned_job(db, job_id, user)
        if job.status != JobStatus.OPEN:
            raise ProfileAccessRevokedError("Vị trí đã đóng, không thể xem hồ sơ")
        # Điều 25: đã từ chối ở vị trí này thì không được lấy lại quyền xem qua nhánh tìm kiếm
        rejected = (
            await db.exec(
                select(Application).where(
                    Application.job_id == job.id,
                    Application.candidate_id == candidate_id,
                    Application.status == ApplicationStatus.REJECTED,
                )
            )
        ).first()
        if rejected:
            raise ProfileAccessRevokedError()
        await privacy_service.grant_access(
            db, company_id=company.id, candidate_id=candidate_id, job_id=job.id,
            source=AccessSource.DISCOVERY,
        )

    submitted = (
        await db.exec(
            select(Application)
            .join(Job, Job.id == Application.job_id)
            .where(
                Application.candidate_id == candidate_id,
                Job.company_id == company.id,
                Application.status == ApplicationStatus.SUBMITTED,
            )
        )
    ).all()
    for app in submitted:
        _set_status(app, ApplicationStatus.VIEWED)
    await db.commit()
    return await candidate_service.build_profile_response(db, profile)
