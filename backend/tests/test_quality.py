from datetime import date, datetime, timedelta

from ai.data_quality import JobQualityRow, compute_metrics, detect_drops
from ai.quality_checker import JobSnapshot, check_job, find_duplicates
from ai.weight_learner import learn_weights
from constants import DEFAULT_MATCH_WEIGHTS, MIN_FEEDBACK_FOR_TRAINING
from enums.job import FlagType
from utils.tax_code import is_valid_tax_code, make_valid_tax_code

TODAY = date(2026, 11, 4)
GOOD_DESCRIPTION = (
    "Phát triển và bảo trì hệ thống backend bằng Python, thiết kế REST API, "
    "làm việc cùng đội sản phẩm. Yêu cầu nắm vững SQL và Git."
)


def _snapshot(job_id: int = 1, **kwargs: object) -> JobSnapshot:
    defaults = dict(
        job_id=job_id, title="Backend Developer", description=GOOD_DESCRIPTION,
        company_name="Công ty A", level="junior", min_years_experience=1,
        salary_max=20_000_000, deadline=TODAY + timedelta(days=10), skill_count=3,
        has_verified_company=True,
    )
    defaults.update(kwargs)
    return JobSnapshot(**defaults)


def _types(snapshot: JobSnapshot) -> set[FlagType]:
    return {flag.flag_type for flag in check_job(snapshot, TODAY)}


def test_good_job_has_no_flags() -> None:
    assert _types(_snapshot()) == set()


def test_expired() -> None:
    assert FlagType.EXPIRED in _types(_snapshot(deadline=TODAY - timedelta(days=1)))


def test_fresher_requiring_years() -> None:
    assert FlagType.FRESHER_REQUIRES_EXPERIENCE in _types(
        _snapshot(title="Fresher Java Developer", level="fresher", min_years_experience=3)
    )
    assert FlagType.FRESHER_REQUIRES_EXPERIENCE not in _types(
        _snapshot(title="Fresher Java Developer", level="fresher", min_years_experience=0)
    )


def test_scam() -> None:
    scam = _snapshot(
        title="Tuyển CTV online",
        description="Việc nhẹ lương cao, chỉ cần đóng phí hồ sơ và đặt cọc đồng phục. "
        "Liên hệ Zalo ngay để nhận việc làm tại nhà.",
        has_verified_company=False,
    )
    assert FlagType.SCAM in _types(scam)


def test_incomplete() -> None:
    assert FlagType.INCOMPLETE in _types(_snapshot(description="Tuyển gấp", skill_count=0))


def test_duplicates_require_same_company_or_title() -> None:
    a = _snapshot(1)
    b = _snapshot(2)
    c = _snapshot(3, company_name="Công ty B", title="Kỹ sư phần mềm")
    assert find_duplicates([a, b, c]) == [(2, 1, 1.0)]


def test_quality_metrics_and_drop_alert() -> None:
    now = datetime(2026, 11, 4)
    row = JobQualityRow(True, True, True, True, True, True, True, True, now, False)
    stale = JobQualityRow(True, True, False, False, False, False, False, False,
                          now - timedelta(days=90), True)
    metrics = compute_metrics([row, stale], now)
    assert metrics.completeness == 0.6667
    assert metrics.freshness == 0.5
    assert metrics.uniqueness == 0.5

    history = [{"freshness": 0.9}] * 3
    assert detect_drops({"freshness": 0.5}, history) == [("freshness", 0.5, 0.9)]
    assert detect_drops({"freshness": 0.85}, history) == []


def test_tax_code() -> None:
    # 31*0 + 29*1 + 23*0 + 19*0 + 17*1 + 13*0 + 7*1 + 5*0 + 3*7 = 74; 10 - 74 % 11 = 2
    assert make_valid_tax_code("010010107") == "0100101072"
    assert is_valid_tax_code("0100101072")
    assert is_valid_tax_code("0100101072-001")
    assert not is_valid_tax_code("0100101079")
    assert not is_valid_tax_code("12345")


def test_weight_learner_needs_enough_data() -> None:
    row = {name: 0.5 for name in DEFAULT_MATCH_WEIGHTS}
    assert learn_weights([row], [True], DEFAULT_MATCH_WEIGHTS) is None


def test_weight_learner_boosts_predictive_feature() -> None:
    rows, labels = [], []
    for i in range(MIN_FEEDBACK_FOR_TRAINING * 3):
        relevant = i % 2 == 0
        row = {name: 0.5 for name in DEFAULT_MATCH_WEIGHTS}
        row["skill"] = 0.9 if relevant else 0.1  # chỉ kỹ năng quyết định nhãn
        row["location"] = (i % 3) / 2
        rows.append(row)
        labels.append(relevant)
    learned = learn_weights(rows, labels, DEFAULT_MATCH_WEIGHTS)
    assert learned is not None
    assert abs(sum(learned.weights.values()) - 1) < 1e-3
    assert learned.weights["skill"] > DEFAULT_MATCH_WEIGHTS["skill"]
