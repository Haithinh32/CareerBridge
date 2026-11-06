import pytest

from ai.matcher import (
    CandidateFeatures,
    JobFeatures,
    experience_fit,
    rank_candidates_for_job,
    rank_jobs_for_candidate,
    skill_coverage,
    weighted_score,
)
from constants import DEFAULT_MATCH_WEIGHTS
from enums.job import WorkType

NAMES = {1: "Python", 2: "SQL", 3: "Docker", 4: "React", 5: "JavaScript", 6: "Figma"}


def _candidate(skills: set[int], **kwargs: object) -> CandidateFeatures:
    defaults = dict(
        candidate_id=1, skill_ids=skills, text="python sql backend api",
        years_experience=1, location="Hà Nội", work_types=[WorkType.FULL_TIME.value],
        target_position="Backend Developer",
    )
    defaults.update(kwargs)
    return CandidateFeatures(**defaults)


def _job(job_id: int, required: set[int], optional: set[int] | None = None,
         **kwargs: object) -> JobFeatures:
    defaults = dict(
        job_id=job_id, title="Backend Developer Python", text="Phát triển API bằng python sql",
        required_skill_ids=required, optional_skill_ids=optional or set(),
        min_years_experience=1, location="Hà Nội", work_type=WorkType.FULL_TIME.value,
    )
    defaults.update(kwargs)
    return JobFeatures(**defaults)


def test_skill_coverage_weights_required_skills() -> None:
    job = _job(1, {1, 2}, {3})
    assert skill_coverage({1, 2, 3}, job) == pytest.approx(1.0)
    assert skill_coverage({1, 2}, job) == pytest.approx(0.8)
    assert skill_coverage({3}, job) == pytest.approx(0.2)
    assert skill_coverage(set(), _job(2, set())) == 0.5


def test_experience_fit() -> None:
    assert experience_fit(0, 0) == 1.0
    assert experience_fit(1, 2) == 0.5
    assert experience_fit(5, 2) == 1.0


def test_weighted_score_bounds() -> None:
    perfect = {name: 1.0 for name in DEFAULT_MATCH_WEIGHTS}
    assert weighted_score(perfect) == 100.0
    assert weighted_score({name: 0.0 for name in DEFAULT_MATCH_WEIGHTS}) == 0.0


def test_ranking_prefers_matching_job() -> None:
    candidate = _candidate({1, 2, 3})
    backend = _job(1, {1, 2}, {3})
    frontend = _job(2, {4, 5}, title="Frontend Developer React",
                    text="Xây dựng giao diện bằng react javascript")
    designer = _job(3, {6}, title="UI Designer", text="Thiết kế giao diện figma",
                    location="Đà Nẵng")
    results = rank_jobs_for_candidate(candidate, [designer, frontend, backend], skill_names=NAMES)
    assert [r.job_id for r in results] == [1, 2, 3]
    assert results[0].score > 80


def test_explanation_lists_matched_and_missing() -> None:
    result = rank_jobs_for_candidate(_candidate({1}), [_job(1, {1, 2}, {3})], skill_names=NAMES)[0]
    assert result.matched_skill_ids == [1]
    assert result.missing_required_ids == [2]
    assert result.missing_optional_ids == [3]
    assert any("1/2 kỹ năng bắt buộc" in r for r in result.reasons)
    assert any("SQL" in r for r in result.reasons)


def test_remote_job_matches_any_location() -> None:
    candidate = _candidate({1, 2}, location="Cần Thơ")
    remote = _job(1, {1, 2}, location="Từ xa", work_type=WorkType.REMOTE.value)
    onsite = _job(2, {1, 2}, location="Hà Nội")
    results = {r.job_id: r for r in rank_jobs_for_candidate(candidate, [remote, onsite])}
    assert results[1].features["location"] == 1.0
    assert results[2].features["location"] == 0.0


def test_rank_candidates_for_job() -> None:
    job = _job(1, {1, 2})
    strong = _candidate({1, 2, 3}, candidate_id=10)
    weak = _candidate({6}, candidate_id=11, text="thiết kế figma", target_position="Designer")
    results = rank_candidates_for_job(job, [weak, strong])
    assert [r.candidate_id for r in results] == [10, 11]


def test_empty_inputs() -> None:
    assert rank_jobs_for_candidate(_candidate({1}), []) == []
    assert rank_candidates_for_job(_job(1, {1}), []) == []
