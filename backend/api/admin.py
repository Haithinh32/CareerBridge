from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from core.database import get_db
from models.user import User
from schemas.analytics import QualityDashboardResponse, TaskResultResponse
from schemas.job import JobListResponse, JobResponse, ReviewRequest
from schemas.matching import WeightsResponse
from security.auth import get_admin_user
from services import ingest_service, matching_service, quality_service

router = APIRouter(prefix="/api/quan-tri", tags=["Quản trị"])


@router.get("/tin-cach-ly", response_model=JobListResponse)
async def list_quarantine(
    _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)
) -> JobListResponse:
    return await quality_service.list_quarantine(db)


@router.post("/tin-cach-ly/{job_id}/duyet", response_model=JobResponse)
async def review_job(
    job_id: int,
    data: ReviewRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    return await quality_service.review_job(db, job_id, data, admin)


@router.post("/quet-chat-luong", response_model=TaskResultResponse)
async def scan_jobs(
    _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)
) -> TaskResultResponse:
    return await quality_service.scan_all_jobs(db)


@router.get("/chat-luong-du-lieu", response_model=QualityDashboardResponse)
async def quality_dashboard(
    _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)
) -> QualityDashboardResponse:
    return await quality_service.get_dashboard(db)


@router.post("/chat-luong-du-lieu/chup", response_model=TaskResultResponse)
async def take_snapshot(
    _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)
) -> TaskResultResponse:
    return await quality_service.take_snapshot(db)


@router.post("/canh-bao/{alert_id}/da-xem", status_code=status.HTTP_204_NO_CONTENT)
async def acknowledge_alert(
    alert_id: int, _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)
) -> None:
    await quality_service.acknowledge_alert(db, alert_id)


@router.post("/thu-thap", response_model=TaskResultResponse)
async def run_ingestion(
    _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)
) -> TaskResultResponse:
    return await ingest_service.run_ingestion(db)


@router.get("/trong-so", response_model=WeightsResponse)
async def get_weights(
    _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)
) -> WeightsResponse:
    return await matching_service.get_active_weights(db)


@router.post("/trong-so/huan-luyen", response_model=TaskResultResponse)
async def retrain_weights(
    _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)
) -> TaskResultResponse:
    return await matching_service.retrain_weights(db)
