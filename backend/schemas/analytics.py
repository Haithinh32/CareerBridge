from datetime import datetime

from pydantic import BaseModel

from enums.quality import QualityMetric


class OverviewResponse(BaseModel):
    total_candidates: int
    total_open_jobs: int
    total_applications: int
    total_companies: int
    avg_salary_million: float | None
    hire_rate: float


class LabelValue(BaseModel):
    label: str
    value: float
    extra: float | None = None


class LabelValueListResponse(BaseModel):
    items: list[LabelValue]
    total: int


class SalaryTrendPoint(BaseModel):
    month: str
    avg_min_million: float | None
    avg_max_million: float | None
    job_count: int


class SalaryTrendListResponse(BaseModel):
    items: list[SalaryTrendPoint]
    total: int


class FunnelStage(BaseModel):
    stage: str
    count: int
    rate_from_previous: float | None
    rate_from_start: float


class FunnelListResponse(BaseModel):
    items: list[FunnelStage]
    total: int


class SkillSupplyDemand(BaseModel):
    skill: str
    demand_share: float
    supply_share: float
    gap: float


class SkillSupplyDemandListResponse(BaseModel):
    items: list[SkillSupplyDemand]
    total: int


class QualitySnapshotResponse(BaseModel):
    id: int
    taken_at: datetime
    total_jobs: int
    completeness: float
    accuracy: float
    freshness: float
    uniqueness: float


class QualityAlertResponse(BaseModel):
    id: int
    metric: QualityMetric
    value: float
    baseline: float
    message: str
    is_acknowledged: bool
    created_at: datetime


class QualityDashboardResponse(BaseModel):
    snapshots: list[QualitySnapshotResponse]
    alerts: list[QualityAlertResponse]
    open_flags_by_type: dict[str, int]
    quarantined_jobs: int


class TaskResultResponse(BaseModel):
    message: str
    details: dict = {}
