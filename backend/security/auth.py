from collections.abc import Awaitable, Callable
from datetime import timedelta

import bcrypt
import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET
from core.database import get_db
from enums.user import UserRole
from exceptions.base import AuthenticationError, PermissionDeniedError
from models.user import User
from utils.time import utcnow

_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "role": user.role.value,
        "exp": utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise AuthenticationError()
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise AuthenticationError("Token không hợp lệ hoặc đã hết hạn") from exc
    user = await db.get(User, user_id)
    if user is None or not user.is_active or user.deleted_at is not None:
        raise AuthenticationError("Tài khoản không tồn tại hoặc đã bị khóa")
    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Dùng cho endpoint công khai nhưng hiển thị thêm thông tin khi đã đăng nhập."""
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials, db)
    except AuthenticationError:
        return None


def require_roles(*roles: UserRole) -> Callable[..., Awaitable[User]]:
    async def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise PermissionDeniedError()
        return user

    return _checker


get_candidate_user = require_roles(UserRole.CANDIDATE)
get_employer_user = require_roles(UserRole.EMPLOYER)
get_school_user = require_roles(UserRole.SCHOOL)
get_admin_user = require_roles(UserRole.ADMIN)
get_employer_or_admin = require_roles(UserRole.EMPLOYER, UserRole.ADMIN)
