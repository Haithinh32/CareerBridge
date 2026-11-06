from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from api.deps import get_candidate_profile
from core.database import get_db
from enums.job import WorkType
from models.candidate import CandidateProfile
from models.user import User
from schemas.application import (
    ApplicationCreate,
    ApplicationListResponse,
    ApplicationResponse,
)
from schemas.job import JobCreate, JobListResponse, JobResponse, JobUpdate
from schemas.matching import CandidateRankingListResponse
from security.auth import get_employer_or_admin, get_employer_user, get_optional_user
from services import application_service, job_service, matching_service

router = APIRouter(prefix="/api/tin-tuyen-dung", tags=["Tin tuyển dụng"])


@router.get("", response_model=JobListResponse)
async def list_jobs(
    q: str | None = None,
    location: str | None = None,
    work_type: WorkType | None = None,
    skill_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> JobListResponse:
    return await job_service.list_jobs(
        db, q=q, location=location, work_type=work_type, skill_id=skill_id,
        skip=skip, limit=limit,
    )


@router.get("/cua-toi", response_model=JobListResponse)
async def my_company_jobs(
    user: User = Depends(get_employer_user), db: AsyncSession = Depends(get_db)
) -> JobListResponse:
    return await job_service.list_company_jobs(db, user)


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    data: JobCreate, user: User = Depends(get_employer_user), db: AsyncSession = Depends(get_db)
) -> JobResponse:
    return await job_service.create_job(db, user, data)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    return await job_service.get_job(db, job_id, user)


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    data: JobUpdate,
    user: User = Depends(get_employer_or_admin),
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    return await job_service.update_job(db, user, job_id, data)


@router.post("/{job_id}/dong", response_model=JobResponse)
async def close_job(
    job_id: int, user: User = Depends(get_employer_or_admin), db: AsyncSession = Depends(get_db)
) -> JobResponse:
    return await job_service.close_job(db, user, job_id)


@router.get("/{job_id}/xep-hang-ung-vien", response_model=CandidateRankingListResponse)
async def rank_candidates(
    job_id: int, user: User = Depends(get_employer_or_admin), db: AsyncSession = Depends(get_db)
) -> CandidateRankingListResponse:
    return await matching_service.rank_candidates(db, user, job_id)


@router.get("/{job_id}/ung-tuyen", response_model=ApplicationListResponse)
async def list_applications(
    job_id: int, user: User = Depends(get_employer_or_admin), db: AsyncSession = Depends(get_db)
) -> ApplicationListResponse:
    return await application_service.list_for_job(db, user, job_id)


@router.post(
    "/{job_id}/ung-tuyen", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED
)
async def apply(
    job_id: int,
    data: ApplicationCreate,
    profile: CandidateProfile = Depends(get_candidate_profile),
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    return await application_service.apply(db, profile, job_id, data)


@router.post("/{job_id}/luu", status_code=status.HTTP_204_NO_CONTENT)
async def save_job(
    job_id: int,
    profile: CandidateProfile = Depends(get_candidate_profile),
    db: AsyncSession = Depends(get_db),
) -> None:
    await job_service.save_job(db, profile, job_id)


@router.delete("/{job_id}/luu", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_job(
    job_id: int,
    profile: CandidateProfile = Depends(get_candidate_profile),
    db: AsyncSession = Depends(get_db),
) -> None:
    await job_service.unsave_job(db, profile, job_id)
