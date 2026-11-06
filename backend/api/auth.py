from fastapi import APIRouter, Depends, status
from fastapi.responses import RedirectResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from core.database import get_db
from models.user import User
from schemas.auth import (
    LinkedInUrlResponse,
    LoginRequest,
    MeResponse,
    RegisterRequest,
    TokenResponse,
)
from security.auth import get_current_user
from services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Xác thực"])


@router.post("/dang-ky", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    return await auth_service.register(db, data)


@router.post("/dang-nhap", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    return await auth_service.login(db, data)


@router.get("/toi", response_model=MeResponse)
async def me(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> MeResponse:
    return await auth_service.me(db, user)


@router.get("/linkedin/url", response_model=LinkedInUrlResponse)
async def linkedin_url() -> LinkedInUrlResponse:
    return auth_service.linkedin_authorize_url()


@router.get("/linkedin/callback")
async def linkedin_callback(
    code: str, state: str, db: AsyncSession = Depends(get_db)
) -> RedirectResponse:
    return RedirectResponse(await auth_service.linkedin_callback(db, code, state))
