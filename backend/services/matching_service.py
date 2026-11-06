"""Gợi ý việc làm, xếp hạng ứng viên, báo cáo thiếu hụt kỹ năng, học trọng số từ phản hồi."""

from collections import Counter

from sqlmodel import and_, col, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from ai.matcher import (
    MatchResult,
    rank_candidates_for_job,
    rank_jobs_for_candidate,
)
from ai.text_utils import jaccard, tokenize
from ai.weight_learner import learn_weights
from constants import (
    CANDIDATE_RANKING_LIMIT,
    DEFAULT_MATCH_WEIGHTS,
    MAX_JOBS_FOR_MATCHING,
    RECOMMENDATION_LIMIT,
)
from enums.candidate import ConsentPurpose
from enums.job import JobStatus
from exceptions.base import NotFoundError, ValidationError
from models.application import Application, RecommendationFeedback, SavedJob
from models.candidate import CandidateProfile
from models.job import Job
from models.organization import School
from models.system import MatchingWeights
from models.user import User
from schemas.analytics import TaskResultResponse
from schemas.matching import (
    CandidateRanking,
    CandidateRankingListResponse,
    FeedbackCreate,
    JobRecommendation,
    JobRecommendationListResponse,
    MatchExplanation,
    SkillGapItem,
    SkillGapResponse,
    WeightsResponse,
)
from services import candidate_service, job_service, privacy_service, skill_service
from services.job_view import build_job_features, build_job_responses, load_job_skills

GAP_MIN_DEMAND_SHARE = 0.2
GAP_MAX_SKILLS = 10
GAP_MIN_TITLE_SIMILARITY = 0.2
GAP_FALLBACK_JOBS = 30


async def get_active_weights(db: AsyncSession) -> WeightsResponse:
    row = (
        await db.exec(select(MatchingWeights).where(col(MatchingWeights.is_active)))
    ).first()
    if row is None:
        return WeightsResponse(
            version=0, weights=DEFAULT_MATCH_WEIGHTS, metrics={}, sample_size=0
        )
    return WeightsResponse(
        version=row.version, weights=row.weights, metrics=row.metrics, sample_size=row.sample_size
    )


def to_explanation(result: MatchResult, names: dict[int, str]) -> MatchExplanation:
    return MatchExplanation(
        score=result.score,
        features=result.features,
        matched_skills=skill_service.to_refs(result.matched_skill_ids, names),
        missing_required_skills=skill_service.to_refs(result.missing_required_ids, names),
        missing_optional_skills=skill_service.to_refs(result.missing_optional_ids, names),
        reasons=result.reasons,
    )


async def _open_jobs(db: AsyncSession) -> list[Job]:
    """Giới hạn số tin đưa vào TF-IDF để thời gian/bộ nhớ mỗi request không tăng vô hạn."""
    return list(
        (
            await db.exec(
                select(Job)
                .where(Job.status == JobStatus.OPEN, col(Job.deleted_at).is_(None))
                .order_by(col(Job.posted_at).desc())
                .limit(MAX_JOBS_FOR_MATCHING)
            )
        ).all()
    )


async def _rank_for_candidate(
    db: AsyncSession, profile: CandidateProfile, jobs: list[Job]
) -> list[MatchResult]:
    candidate = (await candidate_service.load_candidate_features(db, [profile]))[0]
    weights = (await get_active_weights(db)).weights
    names = await skill_service.get_skill_names(db)
    return rank_jobs_for_candidate(
        candidate, await build_job_features(db, jobs), weights=weights, skill_names=names
    )


async def recommend_jobs(
    db: AsyncSession, profile: CandidateProfile, *, limit: int = RECOMMENDATION_LIMIT
) -> JobRecommendationListResponse:
    await privacy_service.require_consent(db, profile.id, ConsentPurpose.JOB_RECOMMENDATION)
    jobs = await _open_jobs(db)
    results = (await _rank_for_candidate(db, profile, jobs))[:limit]
    return await _build_recommendations(db, profile, jobs, results)


async def explain_job(
    db: AsyncSession, profile: CandidateProfile, job_id: int
) -> JobRecommendation:
    """Giải thích độ phù hợp của một tin bất kỳ (kể cả tin không nằm trong top gợi ý)."""
    await privacy_service.require_consent(db, profile.id, ConsentPurpose.JOB_RECOMMENDATION)
    job = await job_service.get_job_or_404(db, job_id)
    if job.status in (JobStatus.QUARANTINED, JobStatus.REJECTED):
        raise NotFoundError("Không tìm thấy tin tuyển dụng")
    jobs = await _open_jobs(db)
    if all(j.id != job.id for j in jobs):
        jobs.append(job)
    results = [r for r in await _rank_for_candidate(db, profile, jobs) if r.job_id == job_id]
    return (await _build_recommendations(db, profile, jobs, results)).items[0]


async def _build_recommendations(
    db: AsyncSession, profile: CandidateProfile, jobs: list[Job], results: list[MatchResult]
) -> JobRecommendationListResponse:
    by_id = {job.id: job for job in jobs}
    responses = {
        r.id: r for r in await build_job_responses(db, [by_id[res.job_id] for res in results])
    }
    names = await skill_service.get_skill_names(db)
    saved = set(
        (
            await db.exec(
                select(SavedJob.job_id).where(
                    SavedJob.candidate_id == profile.id, col(SavedJob.deleted_at).is_(None)
                )
            )
        ).all()
    )
    applied = set(
        (
            await db.exec(
                select(Application.job_id).where(Application.candidate_id == profile.id)
            )
        ).all()
    )
    feedback = dict(
        (
            await db.exec(
                select(RecommendationFeedback.job_id, RecommendationFeedback.is_relevant).where(
                    RecommendationFeedback.candidate_id == profile.id
                )
            )
        ).all()
    )
    items = [
        JobRecommendation(
            job=responses[res.job_id],
            match=to_explanation(res, names),
            is_saved=res.job_id in saved,
            has_applied=res.job_id in applied,
            feedback=feedback.get(res.job_id),
        )
        for res in results
    ]
    return JobRecommendationListResponse(items=items, total=len(items))


async def match_score_for(db: AsyncSession, profile: CandidateProfile, job: Job) -> MatchResult:
    jobs = await _open_jobs(db)
    if all(j.id != job.id for j in jobs):
        jobs.append(job)
    return next(r for r in await _rank_for_candidate(db, profile, jobs) if r.job_id == job.id)


async def submit_feedback(
    db: AsyncSession, profile: CandidateProfile, data: FeedbackCreate
) -> None:
    """Lưu đánh giá kèm vector đặc trưng tại thời điểm gợi ý để huấn luyện lại trọng số."""
    job = await job_service.get_job_or_404(db, data.job_id)
    result = await match_score_for(db, profile, job)
    existing = (
        await db.exec(
            select(RecommendationFeedback).where(
                RecommendationFeedback.candidate_id == profile.id,
                RecommendationFeedback.job_id == job.id,
            )
        )
    ).first()
    if existing:
        existing.is_relevant, existing.features = data.is_relevant, result.features
        existing.comment = data.comment
    else:
        db.add(
            RecommendationFeedback(
                candidate_id=profile.id, job_id=job.id, is_relevant=data.is_relevant,
                features=result.features, comment=data.comment,
            )
        )
    await db.commit()


async def rank_candidates(
    db: AsyncSession, user: User, job_id: int, *, limit: int = CANDIDATE_RANKING_LIMIT
) -> CandidateRankingListResponse:
    """Xếp hạng ứng viên cho một tin: người đã ứng tuyển + người bật 'cho phép tìm thấy'."""
    job = await job_service.get_owned_job(db, job_id, user)
    applications = {
        app.candidate_id: app
        for app in (await db.exec(select(Application).where(Application.job_id == job.id))).all()
    }
    discoverable_ids = await privacy_service.consented_candidate_ids(
        db, ConsentPurpose.EMPLOYER_DISCOVERY
    )
    profiles = (
        await db.exec(
            select(CandidateProfile).where(
                col(CandidateProfile.deleted_at).is_(None),
                or_(
                    col(CandidateProfile.id).in_(list(applications)),
                    and_(
                        col(CandidateProfile.is_discoverable).is_(True),
                        col(CandidateProfile.id).in_(list(discoverable_ids)),
                    ),
                ),
            )
        )
    ).all()
    if not profiles:
        return CandidateRankingListResponse(items=[], total=0)

    candidates = await candidate_service.load_candidate_features(db, list(profiles))
    job_features = (await build_job_features(db, [job]))[0]
    names = await skill_service.get_skill_names(db)
    weights = (await get_active_weights(db)).weights
    results = rank_candidates_for_job(
        job_features, candidates, weights=weights, skill_names=names
    )[:limit]

    by_id = {p.id: p for p in profiles}
    users = {
        u.id: u
        for u in (
            await db.exec(select(User).where(col(User.id).in_([p.user_id for p in profiles])))
        ).all()
    }
    schools = {s.id: s.name for s in (await db.exec(select(School))).all()}
    items = []
    for res in results:
        profile = by_id[res.candidate_id]
        app = applications.get(profile.id)
        items.append(
            CandidateRanking(
                candidate_id=profile.id,
                full_name=users[profile.user_id].full_name,
                school_name=schools.get(profile.school_id),
                major=profile.major,
                location=profile.location,
                years_experience=profile.years_experience,
                application_id=app.id if app else None,
                application_status=app.status.value if app else None,
                is_applicant=app is not None,
                match=to_explanation(res, names),
            )
        )
    return CandidateRankingListResponse(items=items, total=len(items))


async def skill_gap(
    db: AsyncSession, profile: CandidateProfile, target_position: str | None
) -> SkillGapResponse:
    """So kỹ năng hiện có với kỹ năng các tin cùng vị trí mục tiêu thường yêu cầu."""
    target = (target_position or profile.target_position or "").strip()
    if not target:
        raise ValidationError("Hãy nhập vị trí mục tiêu")
    jobs = await _open_jobs(db)
    target_tokens = set(tokenize(target))
    similar = [
        job for job in jobs
        if jaccard(target_tokens, set(tokenize(job.title))) >= GAP_MIN_TITLE_SIMILARITY
    ]
    if not similar:
        ranked = await _rank_for_candidate(db, profile, jobs)
        top_ids = {r.job_id for r in ranked[:GAP_FALLBACK_JOBS]}
        similar = [job for job in jobs if job.id in top_ids]

    job_skills = await load_job_skills(db, [job.id for job in similar])
    demand: Counter[int] = Counter()
    required_count: Counter[int] = Counter()
    for required, optional in job_skills.values():
        demand.update(required | optional)
        required_count.update(required)

    candidate = (await candidate_service.load_candidate_features(db, [profile]))[0]
    names = await skill_service.get_skill_names(db)
    n = len(similar) or 1
    relevant = {sid: cnt / n for sid, cnt in demand.items() if cnt / n >= GAP_MIN_DEMAND_SHARE}
    missing_ids = sorted(
        (sid for sid in relevant if sid not in candidate.skill_ids),
        key=lambda sid: -relevant[sid],
    )[:GAP_MAX_SKILLS]
    courses = await skill_service.courses_for_skills(db, missing_ids)

    total_weight = sum(relevant.values()) or 1.0
    have_weight = sum(share for sid, share in relevant.items() if sid in candidate.skill_ids)
    return SkillGapResponse(
        target_position=target,
        jobs_analyzed=len(similar),
        have_skills=skill_service.to_refs(
            [sid for sid in relevant if sid in candidate.skill_ids], names
        ),
        missing_skills=[
            SkillGapItem(
                skill=skill_service.to_refs([sid], names)[0],
                demand_share=round(relevant[sid], 3),
                is_required_often=required_count[sid] / n >= GAP_MIN_DEMAND_SHARE,
                courses=courses.get(sid, []),
            )
            for sid in missing_ids
        ],
        readiness=round(have_weight / total_weight, 3),
    )


async def retrain_weights(db: AsyncSession) -> TaskResultResponse:
    """Chỉ dùng phản hồi của ứng viên đồng ý mục đích 'cải thiện mô hình'."""
    consenting = await privacy_service.consented_candidate_ids(
        db, ConsentPurpose.MODEL_IMPROVEMENT
    )
    feedback = (
        await db.exec(
            select(RecommendationFeedback).where(
                col(RecommendationFeedback.candidate_id).in_(list(consenting))
            )
        )
    ).all()
    current = await get_active_weights(db)
    learned = learn_weights(
        [f.features for f in feedback], [f.is_relevant for f in feedback], current.weights
    )
    if learned is None:
        return TaskResultResponse(
            message="Chưa đủ phản hồi để huấn luyện lại",
            details={"feedback_count": len(feedback)},
        )
    for row in (
        await db.exec(select(MatchingWeights).where(col(MatchingWeights.is_active)))
    ).all():
        row.is_active = False
    db.add(
        MatchingWeights(
            version=current.version + 1, weights=learned.weights, metrics=learned.metrics,
            sample_size=learned.sample_size, is_active=True,
        )
    )
    await db.commit()
    return TaskResultResponse(
        message=f"Đã cập nhật trọng số phiên bản {current.version + 1}",
        details={"weights": learned.weights, "metrics": learned.metrics},
    )
