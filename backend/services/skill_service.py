from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from ai.skill_extractor import SkillDictionary, SkillEntry
from ai.text_utils import normalize_text
from constants import COURSES_PER_SKILL
from exceptions.base import ConflictError, NotFoundError
from models.skill import Course, Skill, SkillAlias
from schemas.skill import (
    CourseResponse,
    SkillAliasCreate,
    SkillAliasResponse,
    SkillCreate,
    SkillListResponse,
    SkillRef,
    SkillResponse,
    SkillUpdate,
)
from utils.time import utcnow

_dictionary_cache: SkillDictionary | None = None


def invalidate_dictionary() -> None:
    global _dictionary_cache
    _dictionary_cache = None


async def load_dictionary(db: AsyncSession) -> SkillDictionary:
    """Từ điển kỹ năng được cache trong bộ nhớ, xóa cache mỗi khi quản trị viên sửa từ điển."""
    global _dictionary_cache
    if _dictionary_cache is not None:
        return _dictionary_cache
    skills = (await db.exec(select(Skill).where(col(Skill.deleted_at).is_(None)))).all()
    aliases = (await db.exec(select(SkillAlias).where(col(SkillAlias.deleted_at).is_(None)))).all()
    alias_map: dict[int, list[str]] = {}
    for alias in aliases:
        alias_map.setdefault(alias.skill_id, []).append(alias.alias)
    _dictionary_cache = SkillDictionary(
        [SkillEntry(s.id, s.name, s.category, tuple(alias_map.get(s.id, []))) for s in skills]
    )
    return _dictionary_cache


async def get_skill_names(db: AsyncSession) -> dict[int, str]:
    dictionary = await load_dictionary(db)
    return {skill_id: entry.name for skill_id, entry in dictionary.entries.items()}


def to_refs(ids: list[int] | set[int], names: dict[int, str]) -> list[SkillRef]:
    return [SkillRef(skill_id=i, name=names.get(i, f"#{i}")) for i in sorted(ids)]


async def list_skills(db: AsyncSession, *, q: str | None = None) -> SkillListResponse:
    query = select(Skill).where(col(Skill.deleted_at).is_(None)).order_by(Skill.category, Skill.name)
    skills = (await db.exec(query)).all()
    aliases = (await db.exec(select(SkillAlias).where(col(SkillAlias.deleted_at).is_(None)))).all()
    alias_map: dict[int, list[SkillAliasResponse]] = {}
    for alias in aliases:
        alias_map.setdefault(alias.skill_id, []).append(
            SkillAliasResponse(id=alias.id, alias=alias.alias)
        )
    items = [
        SkillResponse(id=s.id, name=s.name, category=s.category, aliases=alias_map.get(s.id, []))
        for s in skills
    ]
    if q:
        needle = normalize_text(q)
        items = [
            item for item in items
            if needle in normalize_text(item.name)
            or any(needle in normalize_text(a.alias) for a in item.aliases)
        ]
    return SkillListResponse(items=items, total=len(items))


async def _ensure_alias_free(db: AsyncSession, alias: str) -> str:
    normalized = normalize_text(alias)
    existing_alias = (
        await db.exec(select(SkillAlias).where(SkillAlias.alias == normalized))
    ).first()
    if existing_alias and existing_alias.deleted_at is None:
        raise ConflictError(f"Từ '{alias}' đã thuộc một kỹ năng khác")
    return normalized


async def create_skill(db: AsyncSession, data: SkillCreate) -> SkillResponse:
    existing = (await db.exec(select(Skill).where(Skill.name == data.name))).first()
    if existing and existing.deleted_at is None:
        raise ConflictError(f"Kỹ năng '{data.name}' đã tồn tại")
    skill = Skill(name=data.name, category=data.category)
    db.add(skill)
    await db.flush()
    alias_responses = []
    for raw in data.aliases:
        alias = SkillAlias(skill_id=skill.id, alias=await _ensure_alias_free(db, raw))
        db.add(alias)
        await db.flush()
        alias_responses.append(SkillAliasResponse(id=alias.id, alias=alias.alias))
    await db.commit()
    invalidate_dictionary()
    return SkillResponse(
        id=skill.id, name=skill.name, category=skill.category, aliases=alias_responses
    )


async def update_skill(db: AsyncSession, skill_id: int, data: SkillUpdate) -> SkillResponse:
    skill = await db.get(Skill, skill_id)
    if skill is None or skill.deleted_at is not None:
        raise NotFoundError("Không tìm thấy kỹ năng")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(skill, key, value)
    skill.updated_at = utcnow()
    await db.commit()
    invalidate_dictionary()
    return SkillResponse(id=skill.id, name=skill.name, category=skill.category)


async def delete_skill(db: AsyncSession, skill_id: int) -> None:
    skill = await db.get(Skill, skill_id)
    if skill is None or skill.deleted_at is not None:
        raise NotFoundError("Không tìm thấy kỹ năng")
    skill.deleted_at = utcnow()
    await db.commit()
    invalidate_dictionary()


async def add_alias(db: AsyncSession, skill_id: int, data: SkillAliasCreate) -> SkillAliasResponse:
    skill = await db.get(Skill, skill_id)
    if skill is None or skill.deleted_at is not None:
        raise NotFoundError("Không tìm thấy kỹ năng")
    normalized = await _ensure_alias_free(db, data.alias)
    existing = (await db.exec(select(SkillAlias).where(SkillAlias.alias == normalized))).first()
    if existing:
        # Khôi phục từ đồng nghĩa đã xóa mềm, gán lại cho kỹ năng mới
        existing.skill_id, existing.deleted_at = skill_id, None
        alias = existing
    else:
        alias = SkillAlias(skill_id=skill_id, alias=normalized)
        db.add(alias)
    await db.commit()
    invalidate_dictionary()
    return SkillAliasResponse(id=alias.id, alias=alias.alias)


async def delete_alias(db: AsyncSession, alias_id: int) -> None:
    alias = await db.get(SkillAlias, alias_id)
    if alias is None or alias.deleted_at is not None:
        raise NotFoundError("Không tìm thấy từ đồng nghĩa")
    alias.deleted_at = utcnow()
    await db.commit()
    invalidate_dictionary()


async def courses_for_skills(
    db: AsyncSession, skill_ids: list[int]
) -> dict[int, list[CourseResponse]]:
    if not skill_ids:
        return {}
    courses = (
        await db.exec(
            select(Course)
            .where(col(Course.skill_id).in_(skill_ids), col(Course.deleted_at).is_(None))
            .order_by(col(Course.is_free).desc(), Course.id)
        )
    ).all()
    result: dict[int, list[CourseResponse]] = {}
    for course in courses:
        bucket = result.setdefault(course.skill_id, [])
        if len(bucket) < COURSES_PER_SKILL:
            bucket.append(CourseResponse.model_validate(course, from_attributes=True))
    return result
