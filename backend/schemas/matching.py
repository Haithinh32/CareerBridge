from pydantic import BaseModel

from schemas.job import JobResponse
from schemas.skill import CourseResponse, SkillRef


class MatchExplanation(BaseModel):
    score: float
    features: dict[str, float]
    matched_skills: list[SkillRef]
    missing_required_skills: list[SkillRef]
    missing_optional_skills: list[SkillRef]
    reasons: list[str]


class JobRecommendation(BaseModel):
    job: JobResponse
    match: MatchExplanation
    is_saved: bool = False
    has_applied: bool = False
    feedback: bool | None = None


class JobRecommendationListResponse(BaseModel):
    items: list[JobRecommendation]
    total: int


class CandidateRanking(BaseModel):
    candidate_id: int
    full_name: str
    school_name: str | None
    major: str | None
    location: str | None
    years_experience: float
    application_id: int | None
    application_status: str | None
    is_applicant: bool
    match: MatchExplanation


class CandidateRankingListResponse(BaseModel):
    items: list[CandidateRanking]
    total: int


class FeedbackCreate(BaseModel):
    job_id: int
    is_relevant: bool
    comment: str | None = None


class SkillGapItem(BaseModel):
    skill: SkillRef
    demand_share: float
    is_required_often: bool
    courses: list[CourseResponse]


class SkillGapResponse(BaseModel):
    target_position: str
    jobs_analyzed: int
    have_skills: list[SkillRef]
    missing_skills: list[SkillGapItem]
    readiness: float


class WeightsResponse(BaseModel):
    version: int
    weights: dict[str, float]
    metrics: dict
    sample_size: int
