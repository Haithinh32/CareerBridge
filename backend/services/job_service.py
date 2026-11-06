from sqlmodel import col, func, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from ai.normalizer import normalize_location
from enums.candidate import RevokeReason
from enums.job import JobStatus, WorkType
from enums.user import UserRole, VerificationStatus
from exceptions.base import (
    CompanyNotVerifiedError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from models.application import SavedJob
from models.candidate import CandidateProfile
from models.job import Job, JobSkill
from models.user import User
from schemas.job import JobCreate, JobListResponse, JobResponse, JobUpdate
from services import organization_service, privacy_service, quality_service
from services.job_editing import apply_job_update, apply_salary, set_job_skills
from services.job_view import build_job_responses
from utils.time import utcnow


async def get_job_or_404(db: AsyncSession, job_id: int) -> Job:
    job = await db.get(Job, job_id)
    if job is None or job.deleted_at is not None:
        raise NotFoundError("Không tìm thấy tin tuyển dụng")
    return job


async def get_owned_job(db: AsyncSession, job_id: int, user: User) -> Job:
    job = await get_job_or_404(db, job_id)
    if user.role == UserRole.ADMIN:
        return job
    company = await organization_service.get_company_for_user(db, user)
    if job.company_id != company.id:
        raise PermissionDeniedError("Tin này không thuộc doanh nghiệp của bạn")
    return job


async def create_job(db: AsyncSession, user: User, data: JobCreate) -> JobResponse:
    company = await organization_service.get_company_for_user(db, user)
    if company.verification_status != VerificationStatus.VERIFIED:
        raise CompanyNotVerifiedError()
    if data.salary_min and data.salary_max and data.salary_min > data.salary_max:
        raise ValidationError("Lương tối thiểu không được lớn hơn lương tối đa")
    now = utcnow()
    job = Job(
        **data.model_dump(exclude={"skills", "location"}),
        company_id=company.id,
        company_name=company.name,
        location_raw=data.location,
        location=normalize_location(data.location),
        posted_at=now,
    )
    apply_salary(job)
    db.add(job)
    await db.flush()
    await set_job_skills(db, job.id, data.skills)
    await db.flush()
    # Kiểm tra chất lượng ngay khi đăng: tin có dấu hiệu bất thường vào vùng cách ly
    await quality_service.evaluate_job(db, job, commit=False)
    await db.commit()
    return (await build_job_responses(db, [job], include_flags=True))[0]


async def update_job(db: AsyncSession, user: User, job_id: int, data: JobUpdate) -> JobResponse:
    job = await get_owned_job(db, job_id, user)
    if job.status in (JobStatus.CLOSED, JobStatus.REJECTED):
        raise ValidationError("Không thể sửa tin đã đóng hoặc đã bị loại")
    await apply_job_update(db, job, data)
    await db.flush()
    await quality_service.evaluate_job(db, job, commit=False)
    await db.commit()
    return (await build_job_responses(db, [job], include_flags=True))[0]


async def close_job(db: AsyncSession, user: User, job_id: int) -> JobResponse:
    """Đóng vị trí -> tự động thu hồi quyền xem hồ sơ của mọi ứng viên liên quan."""
    job = await get_owned_job(db, job_id, user)
    now = utcnow()
    job.status, job.closed_at, job.updated_at = JobStatus.CLOSED, now, now
    await privacy_service.revoke_grants(
        db, job_id=job.id, reason=RevokeReason.JOB_CLOSED, commit=False
    )
    await db.commit()
    return (await build_job_responses(db, [job]))[0]


async def get_job(db: AsyncSession, job_id: int, user: User | None = None) -> JobResponse:
    job = await get_job_or_404(db, job_id)
    is_owner_or_admin = False
    if user and user.role == UserRole.ADMIN:
        is_owner_or_admin = True
    elif user and user.role == UserRole.EMPLOYER:
        company = await organization_service.find_company_for_user(db, user)
        is_owner_or_admin = company is not None and company.id == job.company_id
    if job.status != JobStatus.OPEN and not is_owner_or_admin:
        if job.status in (JobStatus.QUARANTINED, JobStatus.REJECTED):
            raise NotFoundError("Không tìm thấy tin tuyển dụng")
    return (await build_job_responses(db, [job], include_flags=is_owner_or_admin))[0]


async def list_jobs(
    db: AsyncSession,
    *,
    q: str | None = None,
    location: str | None = None,
    work_type: WorkType | None = None,
    skill_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
) -> JobListResponse:
    query = select(Job).where(Job.status == JobStatus.OPEN, col(Job.deleted_at).is_(None))
    if q:
        pattern = f"%{q}%"
        query = query.where(
            or_(col(Job.title).ilike(pattern), col(Job.company_name).ilike(pattern))
        )
    if location:
        query = query.where(Job.location == normalize_location(location))
    if work_type:
        query = query.where(Job.work_type == work_type)
    if skill_id:
        query = query.where(
            col(Job.id).in_(select(JobSkill.job_id).where(JobSkill.skill_id == skill_id))
        )
    total = (await db.exec(select(func.count()).select_from(query.subquery()))).one()
    jobs = (
        await db.exec(query.order_by(col(Job.posted_at).desc()).offset(skip).limit(limit))
    ).all()
    return JobListResponse(items=await build_job_responses(db, list(jobs)), total=total)


async def list_company_jobs(db: AsyncSession, user: User) -> JobListResponse:
    company = await organization_service.get_company_for_user(db, user)
    jobs = (
        await db.exec(
            select(Job)
            .where(Job.company_id == company.id, col(Job.deleted_at).is_(None))
            .order_by(col(Job.created_at).desc())
        )
    ).all()
    items = await build_job_responses(db, list(jobs), include_flags=True)
    return JobListResponse(items=items, total=len(items))


async def save_job(db: AsyncSession, candidate: CandidateProfile, job_id: int) -> None:
    await get_job_or_404(db, job_id)
    existing = (
        await db.exec(
            select(SavedJob).where(
                SavedJob.job_id == job_id, SavedJob.candidate_id == candidate.id
            )
        )
    ).first()
    if existing is None:
        db.add(SavedJob(job_id=job_id, candidate_id=candidate.id))
    elif existing.deleted_at is not None:
        existing.deleted_at = None
    await db.commit()


async def unsave_job(db: AsyncSession, candidate: CandidateProfile, job_id: int) -> None:
    existing = (
        await db.exec(
            select(SavedJob).where(
                SavedJob.job_id == job_id, SavedJob.candidate_id == candidate.id
            )
        )
    ).first()
    if existing and existing.deleted_at is None:
        existing.deleted_at = utcnow()
        await db.commit()


async def list_saved_jobs(db: AsyncSession, candidate: CandidateProfile) -> JobListResponse:
    jobs = (
        await db.exec(
            select(Job)
            .join(SavedJob, SavedJob.job_id == Job.id)
            .where(SavedJob.candidate_id == candidate.id, col(SavedJob.deleted_at).is_(None))
            .order_by(col(SavedJob.created_at).desc())
        )
    ).all()
    items = await build_job_responses(db, list(jobs))
    return JobListResponse(items=items, total=len(items))
