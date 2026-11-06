from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from core.database import get_db
from models.user import User
from schemas.skill import (
    SkillAliasCreate,
    SkillAliasResponse,
    SkillCreate,
    SkillListResponse,
    SkillResponse,
    SkillUpdate,
)
from security.auth import get_admin_user
from services import skill_service

router = APIRouter(prefix="/api/ky-nang", tags=["Từ điển kỹ năng"])


@router.get("", response_model=SkillListResponse)
async def list_skills(q: str | None = None, db: AsyncSession = Depends(get_db)) -> SkillListResponse:
    return await skill_service.list_skills(db, q=q)


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    data: SkillCreate, _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)
) -> SkillResponse:
    return await skill_service.create_skill(db, data)


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: int,
    data: SkillUpdate,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> SkillResponse:
    return await skill_service.update_skill(db, skill_id, data)


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: int, _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)
) -> None:
    await skill_service.delete_skill(db, skill_id)


@router.post(
    "/{skill_id}/tu-dong-nghia",
    response_model=SkillAliasResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_alias(
    skill_id: int,
    data: SkillAliasCreate,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> SkillAliasResponse:
    return await skill_service.add_alias(db, skill_id, data)


@router.delete("/tu-dong-nghia/{alias_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alias(
    alias_id: int, _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)
) -> None:
    await skill_service.delete_alias(db, alias_id)
