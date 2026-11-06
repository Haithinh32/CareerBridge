from datetime import datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field

from enums.quality import QualityMetric
from models.base import TimestampedModel


class MatchingWeights(TimestampedModel, table=True):
    """Phiên bản trọng số thuật toán khớp; chỉ một bản có is_active = True."""

    __tablename__ = "matching_weights"

    id: int | None = Field(default=None, primary_key=True)
    version: int = Field(index=True)
    weights: dict = Field(default_factory=dict, sa_column=Column(JSON))
    metrics: dict = Field(default_factory=dict, sa_column=Column(JSON))
    sample_size: int = Field(default=0)
    is_active: bool = Field(default=False, index=True)


class DataQualitySnapshot(TimestampedModel, table=True):
    __tablename__ = "data_quality_snapshots"

    id: int | None = Field(default=None, primary_key=True)
    taken_at: datetime = Field(index=True)
    total_jobs: int
    completeness: float
    accuracy: float
    freshness: float
    uniqueness: float


class DataQualityAlert(TimestampedModel, table=True):
    __tablename__ = "data_quality_alerts"

    id: int | None = Field(default=None, primary_key=True)
    snapshot_id: int = Field(foreign_key="data_quality_snapshots.id")
    metric: QualityMetric
    value: float
    baseline: float
    message: str = Field(max_length=500)
    is_acknowledged: bool = Field(default=False, index=True)
