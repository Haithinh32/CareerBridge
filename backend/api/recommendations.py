from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from api.deps import get_candidate_profile
from constants import RECOMMENDATION_LIMIT
from core.database import get_db
from models.candidate import CandidateProfile
from schemas.matching import (
    FeedbackCreate,
    JobRecommendation,
    JobRecommendationListResponse,
    SkillGapResponse,
)
from services import matching_service

router = APIRouter(prefix="/api/goi-y", tags=["Gợi ý AI"])


@router.get("/viec-lam", response_model=JobRecommendationListResponse)
async def recommend_jobs(
    limit: int = Query(RECOMMENDATION_LIMIT, ge=1, le=100),
    profile: CandidateProfile = Depends(get_candidate_profile),
    db: AsyncSession = Depends(get_db),
) -> JobRecommendationListResponse:
    return await matching_service.recommend_jobs(db, profile, limit=limit)


@router.get("/viec-lam/{job_id}", response_model=JobRecommendation)
async def explain_job(
    job_id: int,
    profile: CandidateProfile = Depends(get_candidate_profile),
    db: AsyncSession = Depends(get_db),
) -> JobRecommendation:
    return await matching_service.explain_job(db, profile, job_id)


@router.post("/phan-hoi", status_code=status.HTTP_204_NO_CONTENT)
async def submit_feedback(
    data: FeedbackCreate,
    profile: CandidateProfile = Depends(get_candidate_profile),
    db: AsyncSession = Depends(get_db),
) -> None:
    await matching_service.submit_feedback(db, profile, data)


@router.get("/thieu-hut-ky-nang", response_model=SkillGapResponse)
async def skill_gap(
    target_position: str | None = None,
    profile: CandidateProfile = Depends(get_candidate_profile),
    db: AsyncSession = Depends(get_db),
) -> SkillGapResponse:
    return await matching_service.skill_gap(db, profile, target_position)
