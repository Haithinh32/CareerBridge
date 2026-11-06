from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlmodel.ext.asyncio.session import AsyncSession

from api.deps import get_candidate_profile
from constants import UPLOAD_MAX_SIZE_MB
from core.database import get_db
from enums.candidate import DocumentType
from models.candidate import CandidateProfile
from schemas.application import ApplicationListResponse
from schemas.candidate import (
    CandidateProfileResponse,
    CandidateProfileUpdate,
    CvAnalysisResponse,
    DiscoverableUpdate,
    DocumentListResponse,
    SkillConfirmRequest,
)
from schemas.job import JobListResponse
from schemas.organization import FeedPostListResponse
from services import application_service, candidate_service, job_service, organization_service

router = APIRouter(prefix="/api/ung-vien", tags=["Ứng viên"])


@router.get("/ho-so", response_model=CandidateProfileResponse)
async def get_profile(
    profile: CandidateProfile = Depends(get_candidate_profile),
    db: AsyncSession = Depends(get_db),
) -> CandidateProfileResponse:
    return await candidate_service.build_profile_response(db, profile)


@router.put("/ho-so", response_model=CandidateProfileResponse)
async def update_profile(
    data: CandidateProfileUpdate,
    profile: CandidateProfile = Depends(get_candidate_profile),
    db: AsyncSession = Depends(get_db),
) -> CandidateProfileResponse:
    return await candidate_service.update_profile(db, profile, data)


@router.post(
    "/tai-lieu", response_model=CvAnalysisResponse, status_code=status.HTTP_201_CREATED
)
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(DocumentType.CV),
    profile: CandidateProfile = Depends(get_candidate_profile),
    db: AsyncSession = Depends(get_db),
) -> CvAnalysisResponse:
    # Đọc tối đa giới hạn + 1 byte để từ chối file quá lớn mà không nạp hết vào bộ nhớ
    content = await file.read(UPLOAD_MAX_SIZE_MB * 1024 * 1024 + 1)
    return await candidate_service.upload_document(
        db, profile, file_name=file.filename or "cv", content=content,
        document_type=document_type,
    )


@router.get("/tai-lieu", response_model=DocumentListResponse)
async def list_documents(
    profile: CandidateProfile = Depends(get_candidate_profile),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    return await candidate_service.list_documents(db, profile)


@router.delete("/tai-lieu/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    profile: CandidateProfile = Depends(get_candidate_profile),
    db: AsyncSession = Depends(get_db),
) -> None:
    await candidate_service.delete_document(db, profile, document_id)


@router.put("/ky-nang", response_model=CandidateProfileResponse)
async def confirm_skills(
    data: SkillConfirmRequest,
    profile: CandidateProfile = Depends(get_candidate_profile),
    db: AsyncSession = Depends(get_db),
) -> CandidateProfileResponse:
    return await candidate_service.confirm_skills(db, profile, data)


@router.patch("/cho-phep-tim-kiem", response_model=CandidateProfileResponse)
async def set_discoverable(
    data: DiscoverableUpdate,
    profile: CandidateProfile = Depends(get_candidate_profile),
    db: AsyncSession = Depends(get_db),
) -> CandidateProfileResponse:
    return await candidate_service.set_discoverable(db, profile, data.is_discoverable)


@router.get("/ung-tuyen", response_model=ApplicationListResponse)
async def my_applications(
    profile: CandidateProfile = Depends(get_candidate_profile),
    db: AsyncSession = Depends(get_db),
) -> ApplicationListResponse:
    return await application_service.list_for_candidate(db, profile)


@router.get("/tin-da-luu", response_model=JobListResponse)
async def saved_jobs(
    profile: CandidateProfile = Depends(get_candidate_profile),
    db: AsyncSession = Depends(get_db),
) -> JobListResponse:
    return await job_service.list_saved_jobs(db, profile)


@router.get("/feed-truong", response_model=FeedPostListResponse)
async def school_feed(
    profile: CandidateProfile = Depends(get_candidate_profile),
    db: AsyncSession = Depends(get_db),
) -> FeedPostListResponse:
    return await organization_service.list_feed(db, profile.school_id)
