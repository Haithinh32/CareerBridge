from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from core.database import get_db
from models.user import User
from schemas.application import ApplicationResponse, ApplicationStatusUpdate
from schemas.candidate import CandidateProfileResponse
from security.auth import get_employer_or_admin, get_employer_user
from services import application_service

router = APIRouter(prefix="/api/ung-tuyen", tags=["Ứng tuyển"])


@router.patch("/{application_id}/trang-thai", response_model=ApplicationResponse)
async def update_status(
    application_id: int,
    data: ApplicationStatusUpdate,
    user: User = Depends(get_employer_or_admin),
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    return await application_service.update_status(db, user, application_id, data.status)


profile_router = APIRouter(prefix="/api/ho-so-ung-vien", tags=["Ứng tuyển"])


@profile_router.get("/{candidate_id}", response_model=CandidateProfileResponse)
async def view_candidate_profile(
    candidate_id: int,
    job_id: int | None = None,
    user: User = Depends(get_employer_user),
    db: AsyncSession = Depends(get_db),
) -> CandidateProfileResponse:
    return await application_service.view_candidate_profile(db, user, candidate_id, job_id)
