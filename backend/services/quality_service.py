"""Gắn cờ tin kém chất lượng, vùng cách ly, và theo dõi chất lượng dữ liệu."""

from sqlmodel import col, func, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from ai.data_quality import JobQualityRow, compute_metrics, detect_drops
from ai.normalizer import LOCATION_ALIASES, normalize_location, parse_salary
from ai.quality_checker import FlagResult, JobSnapshot, check_job, find_duplicates
from ai.text_utils import normalize_text
from constants import QUALITY_HISTORY_WINDOW
from enums.candidate import RevokeReason
from enums.job import FlagType, JobStatus, ReviewAction
from enums.quality import QualityMetric
from enums.user import VerificationStatus
from exceptions.base import NotFoundError, ValidationError
from models.job import Job, JobFlag, JobSkill
from models.organization import Company
from models.skill import Skill, SkillAlias
from models.system import DataQualityAlert, DataQualitySnapshot
from models.user import User
from schemas.analytics import (
    QualityAlertResponse,
    QualityDashboardResponse,
    QualitySnapshotResponse,
    TaskResultResponse,
)
from schemas.job import JobListResponse, JobResponse, ReviewRequest
from services import privacy_service, skill_service
from services.job_editing import apply_job_update
from services.job_view import build_job_responses
from utils.time import today, utcnow

ACTIVE_STATUSES = (JobStatus.OPEN, JobStatus.QUARANTINED)
METRIC_LABELS: dict[str, str] = {
    QualityMetric.COMPLETENESS.value: "Độ đầy đủ",
    QualityMetric.ACCURACY.value: "Độ chính xác",
    QualityMetric.FRESHNESS.value: "Độ tươi mới",
    QualityMetric.UNIQUENESS.value: "Độ không trùng",
}


async def _snapshots(db: AsyncSession, jobs: list[Job]) -> list[JobSnapshot]:
    job_ids = [job.id for job in jobs]
    skill_counts: dict[int, int] = {}
    if job_ids:
        rows = await db.exec(
            select(JobSkill.job_id, func.count(JobSkill.id))
            .where(col(JobSkill.job_id).in_(job_ids), col(JobSkill.deleted_at).is_(None))
            .group_by(JobSkill.job_id)
        )
        skill_counts = dict(rows.all())
    verified = set(
        (
            await db.exec(
                select(Company.id).where(
                    Company.verification_status == VerificationStatus.VERIFIED
                )
            )
        ).all()
    )
    return [
        JobSnapshot(
            job_id=job.id,
            title=job.title,
            description=job.description,
            company_name=job.company_name,
            level=job.level.value if job.level else None,
            min_years_experience=job.min_years_experience,
            salary_max=job.salary_max,
            deadline=job.deadline,
            skill_count=skill_counts.get(job.id, 0),
            has_verified_company=job.company_id in verified,
        )
        for job in jobs
    ]


async def _save_flags(db: AsyncSession, job: Job, results: list[FlagResult]) -> list[JobFlag]:
    existing = (
        await db.exec(
            select(JobFlag).where(JobFlag.job_id == job.id, col(JobFlag.is_resolved).is_(False))
        )
    ).all()
    existing_types = {flag.flag_type for flag in existing}
    created = []
    for result in results:
        if result.flag_type in existing_types:
            continue
        flag = JobFlag(
            job_id=job.id, flag_type=result.flag_type, score=result.score,
            detail=result.detail, related_job_id=result.related_job_id,
        )
        db.add(flag)
        created.append(flag)
        existing_types.add(result.flag_type)

    if FlagType.EXPIRED in existing_types and job.status == JobStatus.OPEN:
        job.status = JobStatus.EXPIRED
    elif existing_types - {FlagType.EXPIRED} and job.status == JobStatus.OPEN:
        job.status = JobStatus.QUARANTINED
    job.updated_at = utcnow()
    return created


async def evaluate_job(db: AsyncSession, job: Job, *, commit: bool = True) -> list[JobFlag]:
    """Chạy toàn bộ luật cho một tin (gọi khi đăng mới, sửa, hoặc nhập từ feed)."""
    snapshot = (await _snapshots(db, [job]))[0]
    results = check_job(snapshot, today())

    # Chỉ nạp các tin có thể trùng (cùng doanh nghiệp hoặc cùng tiêu đề), không nạp toàn bộ
    others = (
        await db.exec(
            select(Job).where(
                col(Job.status).in_(ACTIVE_STATUSES),
                col(Job.deleted_at).is_(None),
                Job.id != job.id,
                or_(
                    func.lower(Job.company_name) == job.company_name.lower(),
                    func.lower(Job.title) == job.title.lower(),
                ),
            )
        )
    ).all()
    if others:
        pairs = find_duplicates([snapshot, *await _snapshots(db, list(others))])
        for newer, older, sim in pairs:
            if job.id in (newer, older):
                other_id = older if newer == job.id else newer
                results.append(
                    FlagResult(
                        FlagType.DUPLICATE, sim,
                        f"Trùng {sim:.0%} với tin #{other_id}", related_job_id=other_id,
                    )
                )
                break
    flags = await _save_flags(db, job, results)
    if commit:
        await db.commit()
    return flags


async def scan_all_jobs(db: AsyncSession) -> TaskResultResponse:
    """Quét lại toàn bộ tin đang hoạt động (chạy định kỳ)."""
    jobs = list(
        (
            await db.exec(
                select(Job).where(col(Job.status).in_(ACTIVE_STATUSES), col(Job.deleted_at).is_(None))
            )
        ).all()
    )
    snapshots = await _snapshots(db, jobs)
    by_id = {job.id: job for job in jobs}
    results: dict[int, list[FlagResult]] = {
        snap.job_id: check_job(snap, today()) for snap in snapshots
    }
    for newer, older, sim in find_duplicates(snapshots):
        results[newer].append(
            FlagResult(FlagType.DUPLICATE, sim, f"Trùng {sim:.0%} với tin #{older}", older)
        )
    created = 0
    for job_id, flag_results in results.items():
        created += len(await _save_flags(db, by_id[job_id], flag_results))
    await db.commit()
    return TaskResultResponse(
        message=f"Đã quét {len(jobs)} tin, gắn {created} cờ mới",
        details={"scanned": len(jobs), "new_flags": created},
    )


async def list_quarantine(db: AsyncSession) -> JobListResponse:
    jobs = (
        await db.exec(
            select(Job)
            .where(Job.status == JobStatus.QUARANTINED, col(Job.deleted_at).is_(None))
            .order_by(col(Job.created_at).desc())
        )
    ).all()
    items = await build_job_responses(db, list(jobs), include_flags=True)
    for item in items:
        item.flags = [flag for flag in item.flags if not flag.is_resolved]
    return JobListResponse(items=items, total=len(items))


async def review_job(
    db: AsyncSession, job_id: int, data: ReviewRequest, admin: User
) -> JobResponse:
    """Duyệt tin trong vùng cách ly: sửa, cho đăng, hoặc loại; có thể bổ sung từ điển."""
    job = await db.get(Job, job_id)
    if job is None or job.deleted_at is not None:
        raise NotFoundError("Không tìm thấy tin tuyển dụng")
    if job.status != JobStatus.QUARANTINED:
        raise ValidationError("Tin này không nằm trong vùng cách ly")

    for item in data.new_aliases:
        skill = await db.get(Skill, int(item["skill_id"]))
        if skill is None:
            raise NotFoundError(f"Không tìm thấy kỹ năng #{item['skill_id']}")
        db.add(SkillAlias(skill_id=skill.id, alias=normalize_text(item["alias"])))
    if data.new_aliases:
        skill_service.invalidate_dictionary()

    if data.updates:
        await apply_job_update(db, job, data.updates)

    flags = (
        await db.exec(
            select(JobFlag).where(JobFlag.job_id == job.id, col(JobFlag.is_resolved).is_(False))
        )
    ).all()
    for flag in flags:
        flag.is_resolved, flag.resolved_by = True, admin.id
        flag.resolution_note = data.note
    if data.action == ReviewAction.APPROVE:
        job.status = JobStatus.OPEN
    else:
        job.status = JobStatus.REJECTED
        await privacy_service.revoke_grants(
            db, job_id=job.id, reason=RevokeReason.JOB_CLOSED, commit=False
        )
    job.updated_at = utcnow()
    await db.commit()
    return (await build_job_responses(db, [job], include_flags=True))[0]


async def _quality_rows(db: AsyncSession) -> list[JobQualityRow]:
    jobs = (await db.exec(select(Job).where(col(Job.deleted_at).is_(None)))).all()
    skill_job_ids = set(
        (await db.exec(select(JobSkill.job_id).where(col(JobSkill.deleted_at).is_(None)))).all()
    )
    duplicate_ids = set(
        (
            await db.exec(select(JobFlag.job_id).where(JobFlag.flag_type == FlagType.DUPLICATE))
        ).all()
    )
    rows = []
    for job in jobs:
        salary_min, salary_max = parse_salary(job.salary_raw) if job.salary_raw else (None, None)
        location = normalize_location(job.location_raw) if job.location_raw else None
        rows.append(
            JobQualityRow(
                has_title=bool(job.title),
                has_description=len(job.description or "") > 0,
                has_location=bool(job.location_raw),
                has_salary_raw=bool(job.salary_raw),
                has_deadline=job.deadline is not None,
                has_skills=job.id in skill_job_ids,
                # "Thỏa thuận" là giá trị hợp lệ dù không có số
                salary_parsed=bool(salary_min or salary_max)
                or "thoa thuan" in (job.salary_raw or "").lower()
                or "thỏa thuận" in (job.salary_raw or "").lower(),
                location_normalized=location in LOCATION_ALIASES,
                posted_at=job.posted_at,
                is_duplicate=job.id in duplicate_ids,
            )
        )
    return rows


async def take_snapshot(db: AsyncSession) -> TaskResultResponse:
    """Chụp 4 chỉ số chất lượng và cảnh báo khi một chỉ số tụt bất thường so với các lần trước."""
    now = utcnow()
    metrics = compute_metrics(await _quality_rows(db), now)
    history = (
        await db.exec(
            select(DataQualitySnapshot)
            .order_by(col(DataQualitySnapshot.taken_at).desc())
            .limit(QUALITY_HISTORY_WINDOW)
        )
    ).all()
    snapshot = DataQualitySnapshot(taken_at=now, **vars(metrics))
    db.add(snapshot)
    await db.flush()

    drops = detect_drops(
        metrics.as_dict(),
        [
            {
                QualityMetric.COMPLETENESS.value: h.completeness,
                QualityMetric.ACCURACY.value: h.accuracy,
                QualityMetric.FRESHNESS.value: h.freshness,
                QualityMetric.UNIQUENESS.value: h.uniqueness,
            }
            for h in history
        ],
    )
    for metric, value, baseline in drops:
        db.add(
            DataQualityAlert(
                snapshot_id=snapshot.id, metric=QualityMetric(metric), value=value,
                baseline=baseline,
                message=f"{METRIC_LABELS[metric]} tụt từ {baseline:.0%} xuống {value:.0%}",
            )
        )
    await db.commit()
    return TaskResultResponse(
        message=f"Đã chụp chỉ số chất lượng, {len(drops)} cảnh báo",
        details={**metrics.as_dict(), "alerts": len(drops)},
    )


async def get_dashboard(db: AsyncSession, *, limit: int = 30) -> QualityDashboardResponse:
    snapshots = (
        await db.exec(
            select(DataQualitySnapshot).order_by(col(DataQualitySnapshot.taken_at).desc()).limit(limit)
        )
    ).all()
    alerts = (
        await db.exec(
            select(DataQualityAlert).order_by(col(DataQualityAlert.created_at).desc()).limit(50)
        )
    ).all()
    flag_rows = await db.exec(
        select(JobFlag.flag_type, func.count(JobFlag.id))
        .where(col(JobFlag.is_resolved).is_(False))
        .group_by(JobFlag.flag_type)
    )
    quarantined = (
        await db.exec(select(func.count(Job.id)).where(Job.status == JobStatus.QUARANTINED))
    ).one()
    return QualityDashboardResponse(
        snapshots=[
            QualitySnapshotResponse.model_validate(s, from_attributes=True)
            for s in reversed(snapshots)
        ],
        alerts=[QualityAlertResponse.model_validate(a, from_attributes=True) for a in alerts],
        open_flags_by_type={ft.value: n for ft, n in flag_rows.all()},
        quarantined_jobs=quarantined,
    )


async def acknowledge_alert(db: AsyncSession, alert_id: int) -> None:
    alert = await db.get(DataQualityAlert, alert_id)
    if alert is None:
        raise NotFoundError("Không tìm thấy cảnh báo")
    alert.is_acknowledged = True
    await db.commit()
