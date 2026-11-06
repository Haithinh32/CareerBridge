from sqlmodel import Field

from enums.user import AuthProvider, UserRole
from models.base import TimestampedModel


class User(TimestampedModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=255)
    password_hash: str | None = Field(default=None, max_length=255)
    full_name: str = Field(max_length=255)
    role: UserRole = Field(index=True)
    auth_provider: AuthProvider = Field(default=AuthProvider.PASSWORD)
    linkedin_sub: str | None = Field(default=None, unique=True, max_length=255)
    is_active: bool = Field(default=True)
