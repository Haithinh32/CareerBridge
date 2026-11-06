"""Dựng JobResponse theo lô (gom truy vấn kỹ năng, cờ, số hồ sơ để tránh N+1)."""

from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from ai.matcher import JobFeatures
from models.application import Application
from models.job import Job, JobFlag, JobSkill
from schemas.job import JobFlagResponse, JobResponse
from services.skill_service import get_skill_names, to_refs


async def load_job_skills(
    db: AsyncSession, job_ids: list[int]
) -> dict[int, tuple[set[int], set[int]]]:
    """job_id -> (kỹ năng bắt buộc, kỹ năng ưu tiên)."""
    result: dict[int, tuple[set[int], set[int]]] = {jid: (set(), set()) for jid in job_ids}
    if not job_ids:
        return result
    rows = (
        await db.exec(
            select(JobSkill).where(
                col(JobSkill.job_id).in_(job_ids), col(JobSkill.deleted_at).is_(None)
            )
        )
    ).all()
    for row in rows:
        required, optional = result[row.job_id]
        (required if row.is_required else optional).add(row.skill_id)
    return result


async def build_job_responses(
    db: AsyncSession, jobs: list[Job], *, include_flags: bool = False
) -> list[JobResponse]:
    job_ids = [job.id for job in jobs]
    names = await get_skill_names(db)
    skills = await load_job_skills(db, job_ids)

    counts: dict[int, int] = {}
    flags: dict[int, list[JobFlagResponse]] = {}
    if job_ids:
        count_rows = await db.exec(
            select(Application.job_id, func.count(Application.id))
            .where(col(Application.job_id).in_(job_ids))
            .group_by(Application.job_id)
        )
        counts = dict(count_rows.all())
        if include_flags:
            flag_rows = (
                await db.exec(
                    select(JobFlag).where(
                        col(JobFlag.job_id).in_(job_ids), col(JobFlag.deleted_at).is_(None)
                    )
                )
            ).all()
            for flag in flag_rows:
                flags.setdefault(flag.job_id, []).append(
                    JobFlagResponse.model_validate(flag, from_attributes=True)
                )

    responses = []
    for job in jobs:
        required, optional = skills.get(job.id, (set(), set()))
        responses.append(
            JobResponse(
                **job.model_dump(
                    include={
                        "id", "company_id", "company_name", "title", "description", "location",
                        "location_raw", "work_type", "level", "salary_min", "salary_max",
                        "salary_raw", "min_years_experience", "deadline", "status", "source",
                        "posted_at",
                    }
                ),
                required_skills=to_refs(required, names),
                optional_skills=to_refs(optional, names),
                application_count=counts.get(job.id, 0),
                flags=flags.get(job.id, []),
            )
        )
    return responses


async def build_job_features(db: AsyncSession, jobs: list[Job]) -> list[JobFeatures]:
    skills = await load_job_skills(db, [job.id for job in jobs])
    return [
        JobFeatures(
            job_id=job.id,
            title=job.title,
            text=job.description,
            required_skill_ids=skills[job.id][0],
            optional_skill_ids=skills[job.id][1],
            min_years_experience=job.min_years_experience,
            location=job.location,
            work_type=job.work_type.value if job.work_type else None,
        )
        for job in jobs
    ]
