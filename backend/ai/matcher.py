"""Thuật toán khớp lai (hybrid) giữa ứng viên và tin tuyển dụng.

Điểm phù hợp = tổng có trọng số của 6 đặc trưng, mỗi đặc trưng nằm trong [0, 1]:
- skill:      độ phủ kỹ năng (80% kỹ năng bắt buộc + 20% kỹ năng ưu tiên)
- text:       độ tương đồng cosine TF-IDF giữa CV và mô tả công việc
- experience: số năm kinh nghiệm so với yêu cầu tối thiểu
- location:   khớp địa điểm (làm từ xa luôn khớp)
- work_type:  khớp hình thức làm việc mong muốn
- title:      độ trùng từ giữa vị trí mục tiêu và tiêu đề tin
Trọng số mặc định nằm trong constants, và được tinh chỉnh bằng ai.weight_learner.
"""

from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ai.text_utils import jaccard, normalize_text, tokenize
from constants import DEFAULT_MATCH_WEIGHTS, REQUIRED_SKILL_SHARE
from enums.job import WorkType
from enums.quality import MatchFeature

REMOTE_LOCATION = "Từ xa"
NEUTRAL_SCORE = 0.5


@dataclass
class CandidateFeatures:
    candidate_id: int
    skill_ids: set[int]
    text: str
    years_experience: float = 0.0
    location: str | None = None
    work_types: list[str] = field(default_factory=list)
    target_position: str | None = None


@dataclass
class JobFeatures:
    job_id: int
    title: str
    text: str
    required_skill_ids: set[int]
    optional_skill_ids: set[int] = field(default_factory=set)
    min_years_experience: float = 0.0
    location: str | None = None
    work_type: str | None = None


@dataclass
class MatchResult:
    candidate_id: int
    job_id: int
    score: float
    features: dict[str, float]
    matched_skill_ids: list[int]
    missing_required_ids: list[int]
    missing_optional_ids: list[int]
    reasons: list[str]


class TextSimilarity:
    """TF-IDF trên văn bản đã bỏ dấu; fit trên toàn bộ tài liệu của lần xếp hạng."""

    def __init__(self, documents: list[str]) -> None:
        self._vectorizer = TfidfVectorizer(
            ngram_range=(1, 2), sublinear_tf=True, min_df=1, tokenizer=tokenize,
            token_pattern=None, lowercase=False,
        )
        normalized = [normalize_text(doc) or "_" for doc in documents]
        self._matrix = self._vectorizer.fit_transform(normalized)

    def similarity(self, i: int, j: int) -> float:
        return float(cosine_similarity(self._matrix[i], self._matrix[j])[0, 0])

    def similarity_to_all(self, i: int, others: list[int]) -> list[float]:
        if not others:
            return []
        return cosine_similarity(self._matrix[i], self._matrix[others])[0].tolist()


def skill_coverage(candidate_skills: set[int], job: JobFeatures) -> float:
    required, optional = job.required_skill_ids, job.optional_skill_ids
    if not required and not optional:
        return NEUTRAL_SCORE
    req_cov = len(candidate_skills & required) / len(required) if required else 1.0
    opt_cov = len(candidate_skills & optional) / len(optional) if optional else 1.0
    return REQUIRED_SKILL_SHARE * req_cov + (1 - REQUIRED_SKILL_SHARE) * opt_cov


def experience_fit(years: float, min_years: float) -> float:
    if min_years <= 0:
        return 1.0
    return min(1.0, years / min_years)


def location_fit(candidate_location: str | None, job: JobFeatures) -> float:
    if job.work_type == WorkType.REMOTE.value or job.location == REMOTE_LOCATION:
        return 1.0
    if not candidate_location or not job.location:
        return NEUTRAL_SCORE
    return 1.0 if normalize_text(candidate_location) == normalize_text(job.location) else 0.0


def work_type_fit(preferred: list[str], job_work_type: str | None) -> float:
    if not preferred or not job_work_type:
        return NEUTRAL_SCORE
    if job_work_type in preferred:
        return 1.0
    # Hybrid chấp nhận được với người muốn toàn thời gian hoặc từ xa
    if job_work_type == WorkType.HYBRID.value and (
        WorkType.FULL_TIME.value in preferred or WorkType.REMOTE.value in preferred
    ):
        return 0.7
    return 0.0


def title_fit(target_position: str | None, job_title: str) -> float:
    if not target_position:
        return NEUTRAL_SCORE
    return min(1.0, 2 * jaccard(set(tokenize(target_position)), set(tokenize(job_title))))


def compute_features(
    candidate: CandidateFeatures, job: JobFeatures, text_similarity: float
) -> dict[str, float]:
    return {
        MatchFeature.SKILL.value: skill_coverage(candidate.skill_ids, job),
        MatchFeature.TEXT.value: text_similarity,
        MatchFeature.EXPERIENCE.value: experience_fit(
            candidate.years_experience, job.min_years_experience
        ),
        MatchFeature.LOCATION.value: location_fit(candidate.location, job),
        MatchFeature.WORK_TYPE.value: work_type_fit(candidate.work_types, job.work_type),
        MatchFeature.TITLE.value: title_fit(candidate.target_position, job.title),
    }


def weighted_score(features: dict[str, float], weights: dict[str, float] | None = None) -> float:
    weights = weights or DEFAULT_MATCH_WEIGHTS
    total = sum(weights.values()) or 1.0
    raw = sum(weights.get(name, 0.0) * value for name, value in features.items()) / total
    return round(100 * raw, 1)


def explain(
    candidate: CandidateFeatures,
    job: JobFeatures,
    features: dict[str, float],
    skill_names: dict[int, str],
) -> tuple[list[int], list[int], list[int], list[str]]:
    """Sinh lời giải thích dễ hiểu cho người dùng."""
    matched = sorted((job.required_skill_ids | job.optional_skill_ids) & candidate.skill_ids)
    missing_req = sorted(job.required_skill_ids - candidate.skill_ids)
    missing_opt = sorted(job.optional_skill_ids - candidate.skill_ids)

    def names(ids: list[int]) -> str:
        return ", ".join(skill_names.get(i, str(i)) for i in ids)

    reasons: list[str] = []
    if job.required_skill_ids:
        have = len(job.required_skill_ids & candidate.skill_ids)
        reasons.append(f"Có {have}/{len(job.required_skill_ids)} kỹ năng bắt buộc")
    if matched:
        reasons.append(f"Kỹ năng khớp: {names(matched)}")
    if missing_req:
        reasons.append(f"Còn thiếu kỹ năng bắt buộc: {names(missing_req)}")
    if job.min_years_experience > 0:
        if features[MatchFeature.EXPERIENCE.value] >= 1:
            reasons.append(f"Đáp ứng yêu cầu {job.min_years_experience:g} năm kinh nghiệm")
        else:
            reasons.append(
                f"Yêu cầu {job.min_years_experience:g} năm kinh nghiệm, "
                f"bạn có {candidate.years_experience:g} năm"
            )
    if features[MatchFeature.LOCATION.value] == 1 and job.location:
        reasons.append(f"Đúng địa điểm mong muốn ({job.location})")
    elif features[MatchFeature.LOCATION.value] == 0:
        reasons.append(f"Khác địa điểm: tin ở {job.location}")
    if features[MatchFeature.WORK_TYPE.value] == 1:
        reasons.append("Đúng hình thức làm việc mong muốn")
    if features[MatchFeature.TITLE.value] >= 0.5 and candidate.target_position:
        reasons.append(f"Gần với vị trí mục tiêu '{candidate.target_position}'")
    if features[MatchFeature.TEXT.value] >= 0.25:
        reasons.append("Nội dung CV tương đồng cao với mô tả công việc")
    return matched, missing_req, missing_opt, reasons


def _match(
    candidate: CandidateFeatures,
    job: JobFeatures,
    text_sim: float,
    weights: dict[str, float] | None,
    skill_names: dict[int, str],
) -> MatchResult:
    features = compute_features(candidate, job, text_sim)
    matched, missing_req, missing_opt, reasons = explain(candidate, job, features, skill_names)
    return MatchResult(
        candidate_id=candidate.candidate_id,
        job_id=job.job_id,
        score=weighted_score(features, weights),
        features={k: round(v, 4) for k, v in features.items()},
        matched_skill_ids=matched,
        missing_required_ids=missing_req,
        missing_optional_ids=missing_opt,
        reasons=reasons,
    )


def rank_jobs_for_candidate(
    candidate: CandidateFeatures,
    jobs: list[JobFeatures],
    *,
    weights: dict[str, float] | None = None,
    skill_names: dict[int, str] | None = None,
) -> list[MatchResult]:
    if not jobs:
        return []
    sim = TextSimilarity([candidate.text, *(f"{job.title} {job.text}" for job in jobs)])
    text_scores = sim.similarity_to_all(0, list(range(1, len(jobs) + 1)))
    results = [
        _match(candidate, job, text_scores[i], weights, skill_names or {})
        for i, job in enumerate(jobs)
    ]
    return sorted(results, key=lambda r: r.score, reverse=True)


def rank_candidates_for_job(
    job: JobFeatures,
    candidates: list[CandidateFeatures],
    *,
    weights: dict[str, float] | None = None,
    skill_names: dict[int, str] | None = None,
) -> list[MatchResult]:
    if not candidates:
        return []
    sim = TextSimilarity([f"{job.title} {job.text}", *(c.text for c in candidates)])
    text_scores = sim.similarity_to_all(0, list(range(1, len(candidates) + 1)))
    results = [
        _match(candidate, job, text_scores[i], weights, skill_names or {})
        for i, candidate in enumerate(candidates)
    ]
    return sorted(results, key=lambda r: r.score, reverse=True)
