from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from core.database import get_db
from models.candidate import CandidateProfile
from models.user import User
from security.auth import get_candidate_user
from services import candidate_service


async def get_candidate_profile(
    user: User = Depends(get_candidate_user), db: AsyncSession = Depends(get_db)
) -> CandidateProfile:
    return await candidate_service.get_profile_for_user(db, user)
