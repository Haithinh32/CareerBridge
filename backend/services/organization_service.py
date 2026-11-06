from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from enums.job import JobStatus
from enums.user import VerificationStatus
from exceptions.base import ConflictError, NotFoundError, PermissionDeniedError, ValidationError
from models.job import Job
from models.organization import Company, School, SchoolCompanyLink, SchoolFeedPost
from models.user import User
from schemas.organization import (
    CompanyListResponse,
    CompanyResponse,
    CompanyUpdate,
    FeedPostCreate,
    FeedPostListResponse,
    FeedPostResponse,
    SchoolListResponse,
    SchoolResponse,
)
from services.job_view import build_job_responses
from utils.time import utcnow


async def find_company_for_user(db: AsyncSession, user: User) -> Company | None:
    return (
        await db.exec(
            select(Company).where(
                Company.owner_user_id == user.id, col(Company.deleted_at).is_(None)
            )
        )
    ).first()


async def get_company_for_user(db: AsyncSession, user: User) -> Company:
    company = await find_company_for_user(db, user)
    if company is None:
        raise NotFoundError("Tài khoản chưa gắn với doanh nghiệp nào")
    return company


async def find_school_for_user(db: AsyncSession, user: User) -> School | None:
    return (await db.exec(select(School).where(School.owner_user_id == user.id))).first()


async def get_school_for_user(db: AsyncSession, user: User) -> School:
    school = await find_school_for_user(db, user)
    if school is None:
        raise NotFoundError("Tài khoản chưa gắn với nhà trường nào")
    return school


def _company_response(company: Company) -> CompanyResponse:
    return CompanyResponse.model_validate(company, from_attributes=True)


async def get_my_company(db: AsyncSession, user: User) -> CompanyResponse:
    return _company_response(await get_company_for_user(db, user))


async def update_my_company(db: AsyncSession, user: User, data: CompanyUpdate) -> CompanyResponse:
    company = await get_company_for_user(db, user)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(company, key, value)
    company.updated_at = utcnow()
    await db.commit()
    return _company_response(company)


async def list_companies(db: AsyncSession, *, verified_only: bool = True) -> CompanyListResponse:
    query = select(Company).where(col(Company.deleted_at).is_(None)).order_by(Company.name)
    if verified_only:
        query = query.where(Company.verification_status == VerificationStatus.VERIFIED)
    companies = (await db.exec(query)).all()
    return CompanyListResponse(items=[_company_response(c) for c in companies], total=len(companies))


async def list_schools(db: AsyncSession) -> SchoolListResponse:
    schools = (
        await db.exec(select(School).where(col(School.deleted_at).is_(None)).order_by(School.name))
    ).all()
    return SchoolListResponse(
        items=[SchoolResponse(id=s.id, name=s.name) for s in schools], total=len(schools)
    )


async def list_linked_companies(db: AsyncSession, user: User) -> CompanyListResponse:
    school = await get_school_for_user(db, user)
    companies = (
        await db.exec(
            select(Company)
            .join(SchoolCompanyLink, SchoolCompanyLink.company_id == Company.id)
            .where(
                SchoolCompanyLink.school_id == school.id,
                col(SchoolCompanyLink.deleted_at).is_(None),
            )
            .order_by(Company.name)
        )
    ).all()
    return CompanyListResponse(items=[_company_response(c) for c in companies], total=len(companies))


async def link_company(db: AsyncSession, user: User, company_id: int) -> CompanyResponse:
    school = await get_school_for_user(db, user)
    company = await db.get(Company, company_id)
    if company is None or company.verification_status != VerificationStatus.VERIFIED:
        raise NotFoundError("Không tìm thấy doanh nghiệp đã xác minh")
    link = (
        await db.exec(
            select(SchoolCompanyLink).where(
                SchoolCompanyLink.school_id == school.id,
                SchoolCompanyLink.company_id == company_id,
            )
        )
    ).first()
    if link and link.deleted_at is None:
        raise ConflictError("Đã liên kết với doanh nghiệp này")
    if link:
        link.deleted_at = None
    else:
        db.add(SchoolCompanyLink(school_id=school.id, company_id=company_id))
    await db.commit()
    return _company_response(company)


async def unlink_company(db: AsyncSession, user: User, company_id: int) -> None:
    school = await get_school_for_user(db, user)
    link = (
        await db.exec(
            select(SchoolCompanyLink).where(
                SchoolCompanyLink.school_id == school.id,
                SchoolCompanyLink.company_id == company_id,
                col(SchoolCompanyLink.deleted_at).is_(None),
            )
        )
    ).first()
    if link is None:
        raise NotFoundError("Không có liên kết này")
    link.deleted_at = utcnow()
    await db.commit()


async def list_linked_jobs(db: AsyncSession, user: User) -> list[Job]:
    school = await get_school_for_user(db, user)
    return list(
        (
            await db.exec(
                select(Job)
                .join(SchoolCompanyLink, SchoolCompanyLink.company_id == Job.company_id)
                .where(
                    SchoolCompanyLink.school_id == school.id,
                    col(SchoolCompanyLink.deleted_at).is_(None),
                    Job.status == JobStatus.OPEN,
                )
                .order_by(col(Job.posted_at).desc())
            )
        ).all()
    )


async def create_feed_post(db: AsyncSession, user: User, data: FeedPostCreate) -> FeedPostResponse:
    """Nhà trường chỉ được đẩy tin của doanh nghiệp đã liên kết lên feed."""
    school = await get_school_for_user(db, user)
    job = await db.get(Job, data.job_id)
    if job is None or job.status != JobStatus.OPEN:
        raise NotFoundError("Không tìm thấy tin đang mở")
    linked = (
        await db.exec(
            select(SchoolCompanyLink).where(
                SchoolCompanyLink.school_id == school.id,
                SchoolCompanyLink.company_id == job.company_id,
                col(SchoolCompanyLink.deleted_at).is_(None),
            )
        )
    ).first()
    if linked is None:
        raise PermissionDeniedError("Tin này không thuộc doanh nghiệp liên kết với trường")
    post = SchoolFeedPost(school_id=school.id, job_id=job.id, note=data.note)
    db.add(post)
    await db.commit()
    job_response = (await build_job_responses(db, [job]))[0]
    return FeedPostResponse(
        id=post.id, school_name=school.name, note=post.note,
        created_at=post.created_at, job=job_response,
    )


async def list_feed(db: AsyncSession, school_id: int | None) -> FeedPostListResponse:
    if school_id is None:
        raise ValidationError("Bạn chưa chọn trường trong hồ sơ")
    rows = (
        await db.exec(
            select(SchoolFeedPost, Job, School)
            .join(Job, Job.id == SchoolFeedPost.job_id)
            .join(School, School.id == SchoolFeedPost.school_id)
            .where(SchoolFeedPost.school_id == school_id, col(SchoolFeedPost.deleted_at).is_(None))
            .order_by(col(SchoolFeedPost.created_at).desc())
        )
    ).all()
    job_responses = {
        j.id: j for j in await build_job_responses(db, [job for _, job, _ in rows])
    }
    items = [
        FeedPostResponse(
            id=post.id, school_name=school.name, note=post.note,
            created_at=post.created_at, job=job_responses[job.id],
        )
        for post, job, school in rows
    ]
    return FeedPostListResponse(items=items, total=len(items))
