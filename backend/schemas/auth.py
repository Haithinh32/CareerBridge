from pydantic import BaseModel, ConfigDict, EmailStr, Field

from enums.user import UserRole, VerificationStatus


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    role: UserRole
    # Bắt buộc với nhà tuyển dụng
    company_name: str | None = None
    tax_code: str | None = None
    # Bắt buộc với nhà trường
    school_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: UserRole


class MeResponse(UserResponse):
    company_id: int | None = None
    company_verification: VerificationStatus | None = None
    school_id: int | None = None
    candidate_id: int | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class LinkedInUrlResponse(BaseModel):
    url: str
