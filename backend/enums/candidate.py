from enum import Enum


class SkillSource(str, Enum):
    AI_EXTRACTED = "ai_extracted"
    MANUAL = "manual"


class DocumentType(str, Enum):
    CV = "cv"
    PROJECT = "project"
    LINKEDIN_PDF = "linkedin_pdf"


class FileFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"


class ApplicationStatus(str, Enum):
    SUBMITTED = "submitted"
    VIEWED = "viewed"
    INTERVIEW = "interview"
    HIRED = "hired"
    REJECTED = "rejected"


class ConsentPurpose(str, Enum):
    CV_ANALYSIS = "cv_analysis"
    JOB_RECOMMENDATION = "job_recommendation"
    EMPLOYER_DISCOVERY = "employer_discovery"
    SCHOOL_SHARING = "school_sharing"
    MODEL_IMPROVEMENT = "model_improvement"


class AccessSource(str, Enum):
    APPLICATION = "application"
    DISCOVERY = "discovery"


class RevokeReason(str, Enum):
    CANDIDATE_REJECTED = "candidate_rejected"
    JOB_CLOSED = "job_closed"
    CONSENT_WITHDRAWN = "consent_withdrawn"
