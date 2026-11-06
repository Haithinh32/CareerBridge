from enum import Enum


class UserRole(str, Enum):
    CANDIDATE = "candidate"
    EMPLOYER = "employer"
    SCHOOL = "school"
    ADMIN = "admin"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class AuthProvider(str, Enum):
    PASSWORD = "password"
    LINKEDIN = "linkedin"
