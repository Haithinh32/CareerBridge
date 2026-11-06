from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from api.deps import get_candidate_profile
from core.database import get_db
from enums.candidate import ConsentPurpose
from models.candidate import CandidateProfile
from schemas.privacy import (
    AccessGrantListResponse,
    ConsentListResponse,
    ConsentResponse,
    ConsentUpdate,
)
from services import privacy_service

router = APIRouter(prefix="/api/quyen-rieng-tu", tags=["Quyền riêng tư"])


@router.get("/dong-y", response_model=ConsentListResponse)
async def list_consents(
    profile: CandidateProfile = Depends(get_candidate_profile),
    db: AsyncSession = Depends(get_db),
) -> ConsentListResponse:
    return await privacy_service.list_consents(db, profile.id)


@router.put("/dong-y/{purpose}", response_model=ConsentResponse)
async def update_consent(
    purpose: ConsentPurpose,
    data: ConsentUpdate,
    profile: CandidateProfile = Depends(get_candidate_profile),
    db: AsyncSession = Depends(get_db),
) -> ConsentResponse:
    return await privacy_service.update_consent(db, profile, purpose, data.is_granted)


@router.get("/quyen-truy-cap", response_model=AccessGrantListResponse)
async def list_access_grants(
    profile: CandidateProfile = Depends(get_candidate_profile),
    db: AsyncSession = Depends(get_db),
) -> AccessGrantListResponse:
    return await privacy_service.list_access_grants(db, profile.id)
