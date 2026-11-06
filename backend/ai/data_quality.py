"""Chỉ số chất lượng dữ liệu tin tuyển dụng và phát hiện sụt giảm bất thường."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from constants import FRESHNESS_WINDOW_DAYS, QUALITY_DROP_THRESHOLD
from enums.quality import QualityMetric

MIN_HISTORY_FOR_ALERT = 3


@dataclass
class JobQualityRow:
    has_title: bool
    has_description: bool
    has_location: bool
    has_salary_raw: bool
    has_deadline: bool
    has_skills: bool
    salary_parsed: bool
    location_normalized: bool
    posted_at: datetime | None
    is_duplicate: bool


@dataclass
class QualityMetrics:
    total_jobs: int
    completeness: float
    accuracy: float
    freshness: float
    uniqueness: float

    def as_dict(self) -> dict[str, float]:
        return {
            QualityMetric.COMPLETENESS.value: self.completeness,
            QualityMetric.ACCURACY.value: self.accuracy,
            QualityMetric.FRESHNESS.value: self.freshness,
            QualityMetric.UNIQUENESS.value: self.uniqueness,
        }


def compute_metrics(rows: list[JobQualityRow], now: datetime) -> QualityMetrics:
    """
    - Đầy đủ: tỷ lệ trung bình các trường bắt buộc có giá trị
    - Chính xác: tỷ lệ trường lương/địa điểm có dữ liệu thô được chuẩn hóa thành công
    - Tươi mới: tỷ lệ tin đăng trong FRESHNESS_WINDOW_DAYS ngày gần nhất
    - Không trùng: 1 - tỷ lệ tin bị đánh dấu trùng
    """
    n = len(rows)
    if n == 0:
        return QualityMetrics(0, 1.0, 1.0, 1.0, 1.0)

    fields = ("has_title", "has_description", "has_location", "has_salary_raw",
              "has_deadline", "has_skills")
    completeness = sum(sum(getattr(r, f) for f in fields) / len(fields) for r in rows) / n

    salary_rows = [r for r in rows if r.has_salary_raw]
    location_rows = [r for r in rows if r.has_location]
    checks = [r.salary_parsed for r in salary_rows] + [r.location_normalized for r in location_rows]
    accuracy = sum(checks) / len(checks) if checks else 1.0

    cutoff = now - timedelta(days=FRESHNESS_WINDOW_DAYS)
    freshness = sum(1 for r in rows if r.posted_at and r.posted_at >= cutoff) / n
    uniqueness = 1 - sum(r.is_duplicate for r in rows) / n
    return QualityMetrics(
        total_jobs=n,
        completeness=round(completeness, 4),
        accuracy=round(accuracy, 4),
        freshness=round(freshness, 4),
        uniqueness=round(uniqueness, 4),
    )


def detect_drops(
    current: dict[str, float],
    history: list[dict[str, float]],
    threshold: float = QUALITY_DROP_THRESHOLD,
) -> list[tuple[str, float, float]]:
    """So với trung bình các lần chụp trước; trả về (chỉ số, giá trị, mốc) bị tụt quá ngưỡng."""
    if len(history) < MIN_HISTORY_FOR_ALERT:
        return []
    drops = []
    for metric, value in current.items():
        baseline = sum(h[metric] for h in history) / len(history)
        if baseline - value >= threshold:
            drops.append((metric, value, round(baseline, 4)))
    return drops
