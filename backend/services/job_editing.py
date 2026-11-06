"""Ghi dữ liệu tin tuyển dụng (dùng chung cho nhà tuyển dụng, quản trị viên và bộ thu thập)."""

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from ai.normalizer import normalize_location, parse_salary
from exceptions.base import ValidationError
from models.job import Job, JobSkill
from models.skill import Skill
from schemas.job import JobSkillInput, JobUpdate
from utils.time import utcnow


async def set_job_skills(db: AsyncSession, job_id: int, skills: list[JobSkillInput]) -> None:
    skill_ids = {item.skill_id for item in skills}
    valid = set(
        (
            await db.exec(
                select(Skill.id).where(col(Skill.id).in_(skill_ids), col(Skill.deleted_at).is_(None))
            )
        ).all()
    )
    unknown = skill_ids - valid
    if unknown:
        raise ValidationError(f"Kỹ năng không tồn tại: {sorted(unknown)}")
    existing = (await db.exec(select(JobSkill).where(JobSkill.job_id == job_id))).all()
    for row in existing:
        await db.delete(row)
    await db.flush()
    seen: set[int] = set()
    for item in skills:
        if item.skill_id in seen:
            continue
        seen.add(item.skill_id)
        db.add(JobSkill(job_id=job_id, skill_id=item.skill_id, is_required=item.is_required))


def apply_salary(job: Job) -> None:
    """Nếu chỉ có chuỗi lương thô (tin thu thập), chuẩn hóa về VND/tháng."""
    if job.salary_raw and job.salary_min is None and job.salary_max is None:
        job.salary_min, job.salary_max = parse_salary(job.salary_raw)
    if job.salary_min and job.salary_max and job.salary_min > job.salary_max:
        raise ValidationError("Lương tối thiểu không được lớn hơn lương tối đa")


async def apply_job_update(db: AsyncSession, job: Job, data: JobUpdate) -> None:
    values = data.model_dump(exclude_unset=True, exclude={"skills", "location"})
    for key, value in values.items():
        setattr(job, key, value)
    if data.location is not None:
        job.location_raw = data.location
        job.location = normalize_location(data.location)
    apply_salary(job)
    if data.skills is not None:
        await set_job_skills(db, job.id, data.skills)
    job.updated_at = utcnow()
