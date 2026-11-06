"""Chỉ số BI: kỹ năng ứng viên, xu hướng lương, phễu chuyển đổi, cung - cầu kỹ năng.

Gom nhóm bằng Python thay vì hàm ngày tháng của từng CSDL để chạy giống nhau trên SQLite và
PostgreSQL; với khối lượng dữ liệu lớn nên chuyển sang view/materialized view.
"""

from collections import Counter, defaultdict
from datetime import timedelta

from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from constants import TOP_SKILLS_LIMIT
from enums.candidate import ApplicationStatus, ConsentPurpose
from enums.job import JobStatus
from enums.user import VerificationStatus
from models.application import Application
from models.candidate import CandidateProfile, CandidateSkill
from models.job import Job, JobSkill
from models.organization import Company
from models.skill import Skill
from schemas.analytics import (
    FunnelListResponse,
    FunnelStage,
    LabelValue,
    LabelValueListResponse,
    OverviewResponse,
    SalaryTrendListResponse,
    SalaryTrendPoint,
    SkillSupplyDemand,
    SkillSupplyDemandListResponse,
)
from services import privacy_service
from utils.time import utcnow

MILLION = 1_000_000
DAYS_PER_MONTH = 31
FUNNEL_STAGES: list[tuple[ApplicationStatus, str]] = [
    (ApplicationStatus.SUBMITTED, "Ứng tuyển"),
    (ApplicationStatus.VIEWED, "Đã xem"),
    (ApplicationStatus.INTERVIEW, "Mời phỏng vấn"),
    (ApplicationStatus.HIRED, "Trúng tuyển"),
]
_STAGE_ORDER = {status: i for i, (status, _) in enumerate(FUNNEL_STAGES)}


def _avg(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


async def _applications(
    db: AsyncSession, company_id: int | None, job_id: int | None = None
) -> list[Application]:
    query = select(Application).join(Job, Job.id == Application.job_id)
    if company_id is not None:
        query = query.where(Job.company_id == company_id)
    if job_id is not None:
        query = query.where(Application.job_id == job_id)
    return list((await db.exec(query)).all())


async def overview(db: AsyncSession, company_id: int | None = None) -> OverviewResponse:
    job_query = select(Job).where(Job.status == JobStatus.OPEN, col(Job.deleted_at).is_(None))
    if company_id is not None:
        job_query = job_query.where(Job.company_id == company_id)
    open_jobs = (await db.exec(job_query)).all()
    salaries = [
        (j.salary_min + j.salary_max) / 2 / MILLION
        for j in open_jobs if j.salary_min and j.salary_max
    ]
    apps = await _applications(db, company_id)
    hired = sum(1 for a in apps if a.status == ApplicationStatus.HIRED)
    return OverviewResponse(
        total_candidates=(await db.exec(select(func.count(CandidateProfile.id)))).one(),
        total_open_jobs=len(open_jobs),
        total_applications=len(apps),
        total_companies=(
            await db.exec(
                select(func.count(Company.id)).where(
                    Company.verification_status == VerificationStatus.VERIFIED
                )
            )
        ).one(),
        avg_salary_million=_avg(salaries),
        hire_rate=round(hired / len(apps), 4) if apps else 0.0,
    )


async def candidates_by_skill(
    db: AsyncSession, *, limit: int = TOP_SKILLS_LIMIT
) -> LabelValueListResponse:
    rows = (
        await db.exec(
            select(Skill.name, func.count(col(CandidateSkill.candidate_id).distinct()))
            .join(CandidateSkill, CandidateSkill.skill_id == Skill.id)
            .where(col(CandidateSkill.deleted_at).is_(None))
            .group_by(Skill.name)
            .order_by(func.count(col(CandidateSkill.candidate_id).distinct()).desc())
            .limit(limit)
        )
    ).all()
    items = [LabelValue(label=name, value=count) for name, count in rows]
    return LabelValueListResponse(items=items, total=len(items))


async def salary_trend(
    db: AsyncSession, *, skill_id: int | None = None, months: int = 12
) -> SalaryTrendListResponse:
    since = utcnow() - timedelta(days=months * DAYS_PER_MONTH)
    query = select(Job).where(col(Job.posted_at) >= since, col(Job.deleted_at).is_(None))
    if skill_id is not None:
        query = query.where(
            col(Job.id).in_(select(JobSkill.job_id).where(JobSkill.skill_id == skill_id))
        )
    buckets: dict[str, list[Job]] = defaultdict(list)
    for job in (await db.exec(query)).all():
        buckets[job.posted_at.strftime("%Y-%m")].append(job)
    items = [
        SalaryTrendPoint(
            month=month,
            avg_min_million=_avg([j.salary_min / MILLION for j in jobs if j.salary_min]),
            avg_max_million=_avg([j.salary_max / MILLION for j in jobs if j.salary_max]),
            job_count=len(jobs),
        )
        for month, jobs in sorted(buckets.items())
    ]
    return SalaryTrendListResponse(items=items, total=len(items))


def _furthest_stage(app: Application) -> int:
    """Giai đoạn xa nhất hồ sơ từng đạt tới (hồ sơ bị từ chối vẫn được tính các bước trước đó)."""
    reached = [
        _STAGE_ORDER[ApplicationStatus(h["status"])]
        for h in app.status_history or []
        if ApplicationStatus(h["status"]) in _STAGE_ORDER
    ]
    if app.status in _STAGE_ORDER:
        reached.append(_STAGE_ORDER[app.status])
    return max(reached, default=0)


async def conversion_funnel(
    db: AsyncSession, *, company_id: int | None = None, job_id: int | None = None
) -> FunnelListResponse:
    apps = await _applications(db, company_id, job_id)
    furthest = [_furthest_stage(a) for a in apps]
    counts = [sum(1 for f in furthest if f >= i) for i in range(len(FUNNEL_STAGES))]
    start = counts[0] or 1
    items = [
        FunnelStage(
            stage=label,
            count=counts[i],
            rate_from_previous=round(counts[i] / counts[i - 1], 4) if i and counts[i - 1] else None,
            rate_from_start=round(counts[i] / start, 4),
        )
        for i, (_, label) in enumerate(FUNNEL_STAGES)
    ]
    return FunnelListResponse(items=items, total=len(items))


async def _skill_demand_shares(db: AsyncSession) -> tuple[dict[str, float], int]:
    rows = (
        await db.exec(
            select(Skill.name, JobSkill.job_id)
            .join(JobSkill, JobSkill.skill_id == Skill.id)
            .join(Job, Job.id == JobSkill.job_id)
            .where(Job.status == JobStatus.OPEN, col(JobSkill.deleted_at).is_(None))
        )
    ).all()
    job_count = len({job_id for _, job_id in rows}) or 1
    counter = Counter(name for name, _ in rows)
    return {name: n / job_count for name, n in counter.items()}, job_count


async def skill_demand(db: AsyncSession, *, limit: int = TOP_SKILLS_LIMIT) -> LabelValueListResponse:
    shares, _ = await _skill_demand_shares(db)
    top = sorted(shares.items(), key=lambda kv: -kv[1])[:limit]
    items = [LabelValue(label=name, value=round(share * 100, 1)) for name, share in top]
    return LabelValueListResponse(items=items, total=len(items))


async def jobs_by_location(db: AsyncSession) -> LabelValueListResponse:
    rows = (
        await db.exec(
            select(Job.location, func.count(Job.id))
            .where(Job.status == JobStatus.OPEN)
            .group_by(Job.location)
            .order_by(func.count(Job.id).desc())
        )
    ).all()
    items = [LabelValue(label=loc or "Không rõ", value=n) for loc, n in rows]
    return LabelValueListResponse(items=items, total=len(items))


async def salary_by_skill(db: AsyncSession, *, limit: int = TOP_SKILLS_LIMIT) -> LabelValueListResponse:
    rows = (
        await db.exec(
            select(Skill.name, Job.salary_min, Job.salary_max)
            .join(JobSkill, JobSkill.skill_id == Skill.id)
            .join(Job, Job.id == JobSkill.job_id)
            .where(col(Job.salary_min).is_not(None), col(Job.salary_max).is_not(None))
        )
    ).all()
    buckets: dict[str, list[float]] = defaultdict(list)
    for name, lo, hi in rows:
        buckets[name].append((lo + hi) / 2 / MILLION)
    top = sorted(buckets.items(), key=lambda kv: -len(kv[1]))[:limit]
    items = [
        LabelValue(label=name, value=_avg(values) or 0, extra=len(values))
        for name, values in sorted(top, key=lambda kv: -(sum(kv[1]) / len(kv[1])))
    ]
    return LabelValueListResponse(items=items, total=len(items))


async def supply_demand(
    db: AsyncSession, *, school_id: int | None = None, limit: int = TOP_SKILLS_LIMIT
) -> SkillSupplyDemandListResponse:
    """So sánh tỷ lệ tin cần kỹ năng (cầu) với tỷ lệ ứng viên có kỹ năng (cung).

    Báo cáo cho nhà trường chỉ tính sinh viên của trường đã đồng ý chia sẻ dữ liệu tổng hợp.
    """
    demand, _ = await _skill_demand_shares(db)
    profile_query = select(CandidateProfile.id).where(col(CandidateProfile.deleted_at).is_(None))
    if school_id is not None:
        consenting = await privacy_service.consented_candidate_ids(
            db, ConsentPurpose.SCHOOL_SHARING
        )
        profile_query = profile_query.where(
            CandidateProfile.school_id == school_id,
            col(CandidateProfile.id).in_(list(consenting)),
        )
    candidate_ids = list((await db.exec(profile_query)).all())
    supply_counter: Counter[str] = Counter()
    if candidate_ids:
        rows = (
            await db.exec(
                select(Skill.name, CandidateSkill.candidate_id)
                .join(CandidateSkill, CandidateSkill.skill_id == Skill.id)
                .where(
                    col(CandidateSkill.candidate_id).in_(candidate_ids),
                    col(CandidateSkill.deleted_at).is_(None),
                )
            )
        ).all()
        supply_counter = Counter(name for name, _ in set(rows))
    n_candidates = len(candidate_ids) or 1
    top = sorted(demand.items(), key=lambda kv: -kv[1])[:limit]
    items = [
        SkillSupplyDemand(
            skill=name,
            demand_share=round(share, 4),
            supply_share=round(supply_counter[name] / n_candidates, 4),
            gap=round(share - supply_counter[name] / n_candidates, 4),
        )
        for name, share in top
    ]
    return SkillSupplyDemandListResponse(items=items, total=len(items))
