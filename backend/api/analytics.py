from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from core.database import get_db
from enums.user import UserRole
from models.user import User
from schemas.analytics import (
    FunnelListResponse,
    LabelValueListResponse,
    OverviewResponse,
    SalaryTrendListResponse,
    SkillSupplyDemandListResponse,
)
from security.auth import require_roles
from services import analytics_service, organization_service

router = APIRouter(prefix="/api/bi", tags=["BI Dashboard"])

get_bi_user = require_roles(UserRole.EMPLOYER, UserRole.ADMIN, UserRole.SCHOOL)


async def _company_scope(db: AsyncSession, user: User) -> int | None:
    """Nhà tuyển dụng chỉ xem số liệu tuyển dụng của doanh nghiệp mình; admin xem toàn hệ thống."""
    if user.role == UserRole.EMPLOYER:
        return (await organization_service.get_company_for_user(db, user)).id
    return None


@router.get("/tong-quan", response_model=OverviewResponse)
async def overview(
    user: User = Depends(get_bi_user), db: AsyncSession = Depends(get_db)
) -> OverviewResponse:
    return await analytics_service.overview(db, await _company_scope(db, user))


@router.get("/ung-vien-theo-ky-nang", response_model=LabelValueListResponse)
async def candidates_by_skill(
    limit: int = Query(15, ge=1, le=50),
    _: User = Depends(get_bi_user),
    db: AsyncSession = Depends(get_db),
) -> LabelValueListResponse:
    return await analytics_service.candidates_by_skill(db, limit=limit)


@router.get("/xu-huong-luong", response_model=SalaryTrendListResponse)
async def salary_trend(
    skill_id: int | None = None,
    months: int = Query(12, ge=1, le=36),
    _: User = Depends(get_bi_user),
    db: AsyncSession = Depends(get_db),
) -> SalaryTrendListResponse:
    return await analytics_service.salary_trend(db, skill_id=skill_id, months=months)


@router.get("/luong-theo-ky-nang", response_model=LabelValueListResponse)
async def salary_by_skill(
    _: User = Depends(get_bi_user), db: AsyncSession = Depends(get_db)
) -> LabelValueListResponse:
    return await analytics_service.salary_by_skill(db)


@router.get("/ty-le-chuyen-doi", response_model=FunnelListResponse)
async def conversion_funnel(
    job_id: int | None = None,
    user: User = Depends(get_bi_user),
    db: AsyncSession = Depends(get_db),
) -> FunnelListResponse:
    return await analytics_service.conversion_funnel(
        db, company_id=await _company_scope(db, user), job_id=job_id
    )


@router.get("/nhu-cau-ky-nang", response_model=LabelValueListResponse)
async def skill_demand(
    _: User = Depends(get_bi_user), db: AsyncSession = Depends(get_db)
) -> LabelValueListResponse:
    return await analytics_service.skill_demand(db)


@router.get("/tin-theo-dia-diem", response_model=LabelValueListResponse)
async def jobs_by_location(
    _: User = Depends(get_bi_user), db: AsyncSession = Depends(get_db)
) -> LabelValueListResponse:
    return await analytics_service.jobs_by_location(db)


@router.get("/cung-cau-ky-nang", response_model=SkillSupplyDemandListResponse)
async def supply_demand(
    _: User = Depends(get_bi_user), db: AsyncSession = Depends(get_db)
) -> SkillSupplyDemandListResponse:
    return await analytics_service.supply_demand(db)
