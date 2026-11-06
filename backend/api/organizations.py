from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from core.database import get_db
from models.user import User
from schemas.analytics import SkillSupplyDemandListResponse
from schemas.job import JobListResponse
from schemas.organization import (
    CompanyListResponse,
    CompanyResponse,
    CompanyUpdate,
    FeedPostCreate,
    FeedPostListResponse,
    FeedPostResponse,
    SchoolLinkCreate,
    SchoolListResponse,
)
from security.auth import get_employer_user, get_school_user
from services import analytics_service, organization_service
from services.job_view import build_job_responses

company_router = APIRouter(prefix="/api/doanh-nghiep", tags=["Doanh nghiệp"])
school_router = APIRouter(prefix="/api/nha-truong", tags=["Nhà trường"])


@company_router.get("", response_model=CompanyListResponse)
async def list_companies(db: AsyncSession = Depends(get_db)) -> CompanyListResponse:
    return await organization_service.list_companies(db)


@company_router.get("/cua-toi", response_model=CompanyResponse)
async def get_my_company(
    user: User = Depends(get_employer_user), db: AsyncSession = Depends(get_db)
) -> CompanyResponse:
    return await organization_service.get_my_company(db, user)


@company_router.put("/cua-toi", response_model=CompanyResponse)
async def update_my_company(
    data: CompanyUpdate,
    user: User = Depends(get_employer_user),
    db: AsyncSession = Depends(get_db),
) -> CompanyResponse:
    return await organization_service.update_my_company(db, user, data)


@school_router.get("", response_model=SchoolListResponse)
async def list_schools(db: AsyncSession = Depends(get_db)) -> SchoolListResponse:
    return await organization_service.list_schools(db)


@school_router.get("/lien-ket", response_model=CompanyListResponse)
async def list_links(
    user: User = Depends(get_school_user), db: AsyncSession = Depends(get_db)
) -> CompanyListResponse:
    return await organization_service.list_linked_companies(db, user)


@school_router.post("/lien-ket", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def link_company(
    data: SchoolLinkCreate,
    user: User = Depends(get_school_user),
    db: AsyncSession = Depends(get_db),
) -> CompanyResponse:
    return await organization_service.link_company(db, user, data.company_id)


@school_router.delete("/lien-ket/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_company(
    company_id: int, user: User = Depends(get_school_user), db: AsyncSession = Depends(get_db)
) -> None:
    await organization_service.unlink_company(db, user, company_id)


@school_router.get("/tin-lien-ket", response_model=JobListResponse)
async def linked_jobs(
    user: User = Depends(get_school_user), db: AsyncSession = Depends(get_db)
) -> JobListResponse:
    jobs = await organization_service.list_linked_jobs(db, user)
    return JobListResponse(items=await build_job_responses(db, jobs), total=len(jobs))


@school_router.get("/feed", response_model=FeedPostListResponse)
async def list_feed(
    user: User = Depends(get_school_user), db: AsyncSession = Depends(get_db)
) -> FeedPostListResponse:
    school = await organization_service.get_school_for_user(db, user)
    return await organization_service.list_feed(db, school.id)


@school_router.post("/feed", response_model=FeedPostResponse, status_code=status.HTTP_201_CREATED)
async def create_feed_post(
    data: FeedPostCreate,
    user: User = Depends(get_school_user),
    db: AsyncSession = Depends(get_db),
) -> FeedPostResponse:
    return await organization_service.create_feed_post(db, user, data)


@school_router.get("/bao-cao-ky-nang", response_model=SkillSupplyDemandListResponse)
async def skill_report(
    user: User = Depends(get_school_user), db: AsyncSession = Depends(get_db)
) -> SkillSupplyDemandListResponse:
    school = await organization_service.get_school_for_user(db, user)
    return await analytics_service.supply_demand(db, school_id=school.id)
