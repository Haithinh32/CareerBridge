from datetime import timedelta
from urllib.parse import urlencode

import httpx
import jwt
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import (
    FRONTEND_URL,
    JWT_ALGORITHM,
    JWT_SECRET,
    LINKEDIN_CLIENT_ID,
    LINKEDIN_CLIENT_SECRET,
    LINKEDIN_REDIRECT_URI,
)
from enums.user import AuthProvider, UserRole, VerificationStatus
from exceptions.base import (
    AuthenticationError,
    ConflictError,
    ExternalServiceError,
    ValidationError,
)
from models.candidate import CandidateProfile
from models.organization import Company, School
from models.user import User
from schemas.auth import (
    LinkedInUrlResponse,
    LoginRequest,
    MeResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from security.auth import create_access_token, hash_password, verify_password
from services import organization_service
from utils.tax_code import is_valid_tax_code, normalize_tax_code
from utils.time import utcnow

LINKEDIN_AUTHORIZE_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
LINKEDIN_SCOPE = "openid profile email"
OAUTH_STATE_TTL_MINUTES = 10
HTTP_TIMEOUT_SECONDS = 10


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user),
        user=UserResponse.model_validate(user, from_attributes=True),
    )


async def register(db: AsyncSession, data: RegisterRequest) -> TokenResponse:
    if data.role == UserRole.ADMIN:
        raise ValidationError("Không thể tự đăng ký tài khoản quản trị")
    email = data.email.lower()
    if (await db.exec(select(User).where(User.email == email))).first():
        raise ConflictError("Email đã được sử dụng")

    user = User(
        email=email, password_hash=hash_password(data.password),
        full_name=data.full_name, role=data.role,
    )
    db.add(user)
    await db.flush()

    if data.role == UserRole.CANDIDATE:
        db.add(CandidateProfile(user_id=user.id))
    elif data.role == UserRole.EMPLOYER:
        if not data.company_name or not data.tax_code:
            raise ValidationError("Nhà tuyển dụng cần nhập tên doanh nghiệp và mã số thuế")
        tax_code = normalize_tax_code(data.tax_code)
        if not is_valid_tax_code(tax_code):
            raise ValidationError("Mã số thuế không hợp lệ")
        if (await db.exec(select(Company).where(Company.tax_code == tax_code))).first():
            raise ConflictError("Mã số thuế đã được đăng ký")
        # Mã hợp lệ về định dạng/chữ số kiểm tra -> xác minh tự động.
        # Khi có API tra cứu của Tổng cục Thuế, gọi tại đây để kiểm tra trạng thái hoạt động.
        db.add(
            Company(
                owner_user_id=user.id, name=data.company_name, tax_code=tax_code,
                verification_status=VerificationStatus.VERIFIED,
            )
        )
    elif data.role == UserRole.SCHOOL:
        if not data.school_name:
            raise ValidationError("Nhà trường cần nhập tên trường")
        existing = (await db.exec(select(School).where(School.name == data.school_name))).first()
        if existing and existing.owner_user_id:
            raise ConflictError("Trường này đã có tài khoản quản lý")
        if existing:
            existing.owner_user_id = user.id
        else:
            db.add(School(owner_user_id=user.id, name=data.school_name))
    await db.commit()
    return _token_response(user)


async def login(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    user = (await db.exec(select(User).where(User.email == data.email.lower()))).first()
    if user is None or not verify_password(data.password, user.password_hash):
        raise AuthenticationError("Email hoặc mật khẩu không đúng")
    if not user.is_active or user.deleted_at is not None:
        raise AuthenticationError("Tài khoản đã bị khóa")
    return _token_response(user)


async def me(db: AsyncSession, user: User) -> MeResponse:
    response = MeResponse.model_validate(user, from_attributes=True)
    if user.role == UserRole.EMPLOYER:
        company = await organization_service.find_company_for_user(db, user)
        if company:
            response.company_id = company.id
            response.company_verification = company.verification_status
    elif user.role == UserRole.SCHOOL:
        school = await organization_service.find_school_for_user(db, user)
        response.school_id = school.id if school else None
    elif user.role == UserRole.CANDIDATE:
        profile = (
            await db.exec(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
        ).first()
        response.candidate_id = profile.id if profile else None
    return response


def linkedin_authorize_url() -> LinkedInUrlResponse:
    if not LINKEDIN_CLIENT_ID:
        raise ValidationError("Chưa cấu hình đăng nhập LinkedIn (LINKEDIN_CLIENT_ID)")
    state = jwt.encode(
        {"purpose": "linkedin", "exp": utcnow() + timedelta(minutes=OAUTH_STATE_TTL_MINUTES)},
        JWT_SECRET, algorithm=JWT_ALGORITHM,
    )
    params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "state": state,
        "scope": LINKEDIN_SCOPE,
    }
    return LinkedInUrlResponse(url=f"{LINKEDIN_AUTHORIZE_URL}?{urlencode(params)}")


async def linkedin_callback(db: AsyncSession, code: str, state: str) -> str:
    """Đổi code lấy thông tin người dùng (OpenID Connect), trả về URL frontend kèm token."""
    try:
        payload = jwt.decode(state, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Phiên đăng nhập LinkedIn không hợp lệ") from exc
    if payload.get("purpose") != "linkedin":
        raise AuthenticationError("Phiên đăng nhập LinkedIn không hợp lệ")

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            token_res = await client.post(
                LINKEDIN_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": LINKEDIN_REDIRECT_URI,
                    "client_id": LINKEDIN_CLIENT_ID,
                    "client_secret": LINKEDIN_CLIENT_SECRET,
                },
            )
            token_res.raise_for_status()
            info_res = await client.get(
                LINKEDIN_USERINFO_URL,
                headers={"Authorization": f"Bearer {token_res.json()['access_token']}"},
            )
            info_res.raise_for_status()
            info = info_res.json()
    except (httpx.HTTPError, KeyError) as exc:
        raise ExternalServiceError("Không kết nối được LinkedIn") from exc

    sub, email = info.get("sub"), (info.get("email") or "").lower()
    if not sub or not email:
        raise ExternalServiceError("LinkedIn không trả về email")
    # Chỉ liên kết với tài khoản sẵn có khi LinkedIn xác nhận email, tránh chiếm quyền tài khoản
    if info.get("email_verified") is not True:
        raise AuthenticationError("Email LinkedIn chưa được xác minh")
    user = (await db.exec(select(User).where(User.linkedin_sub == sub))).first()
    if user is None:
        user = (await db.exec(select(User).where(User.email == email))).first()
        if user:
            user.linkedin_sub = sub
        else:
            user = User(
                email=email, full_name=info.get("name") or email, role=UserRole.CANDIDATE,
                auth_provider=AuthProvider.LINKEDIN, linkedin_sub=sub,
            )
            db.add(user)
            await db.flush()
            db.add(CandidateProfile(user_id=user.id))
        await db.commit()
    token = create_access_token(user)
    return f"{FRONTEND_URL}/dang-nhap/linkedin#token={token}"
