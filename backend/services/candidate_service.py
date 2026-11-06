from pathlib import Path
from uuid import uuid4

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from ai.cv_parser import extract_text, parse_cv
from ai.matcher import CandidateFeatures
from ai.normalizer import normalize_location
from constants import UPLOAD_MAX_SIZE_MB
from core.config import UPLOAD_DIR
from enums.candidate import ConsentPurpose, DocumentType, FileFormat, SkillSource
from exceptions.base import NotFoundError, ValidationError
from models.candidate import CandidateDocument, CandidateProfile, CandidateSkill
from models.organization import School
from models.skill import Skill
from models.user import User
from schemas.candidate import (
    CandidateProfileResponse,
    CandidateProfileUpdate,
    CandidateSkillResponse,
    CvAnalysisResponse,
    DocumentListResponse,
    DocumentResponse,
    SkillConfirmRequest,
)
from services import privacy_service, skill_service
from utils.time import utcnow

FILE_EXTENSIONS: dict[str, FileFormat] = {".pdf": FileFormat.PDF, ".docx": FileFormat.DOCX}


async def get_profile_for_user(db: AsyncSession, user: User) -> CandidateProfile:
    profile = (
        await db.exec(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
    ).first()
    if profile is None:
        raise NotFoundError("Không tìm thấy hồ sơ ứng viên")
    return profile


async def _skill_rows(db: AsyncSession, candidate_id: int) -> list[CandidateSkillResponse]:
    rows = (
        await db.exec(
            select(CandidateSkill, Skill)
            .join(Skill, Skill.id == CandidateSkill.skill_id)
            .where(
                CandidateSkill.candidate_id == candidate_id,
                col(CandidateSkill.deleted_at).is_(None),
            )
            .order_by(col(CandidateSkill.is_confirmed).desc(), Skill.name)
        )
    ).all()
    return [
        CandidateSkillResponse(
            skill_id=skill.id, name=skill.name, category=skill.category,
            source=cs.source, is_confirmed=cs.is_confirmed, level=cs.level,
        )
        for cs, skill in rows
    ]


async def build_profile_response(
    db: AsyncSession, profile: CandidateProfile
) -> CandidateProfileResponse:
    user = await db.get(User, profile.user_id)
    school = await db.get(School, profile.school_id) if profile.school_id else None
    return CandidateProfileResponse(
        id=profile.id,
        full_name=user.full_name,
        email=user.email,
        school_id=profile.school_id,
        school_name=school.name if school else None,
        major=profile.major,
        study_year=profile.study_year,
        location=profile.location,
        work_types=profile.work_types or [],
        availability=profile.availability,
        target_position=profile.target_position,
        years_experience=profile.years_experience,
        education=profile.education or [],
        projects=profile.projects or [],
        is_discoverable=profile.is_discoverable,
        skills=await _skill_rows(db, profile.id),
    )


async def update_profile(
    db: AsyncSession, profile: CandidateProfile, data: CandidateProfileUpdate
) -> CandidateProfileResponse:
    values = data.model_dump(exclude_unset=True)
    if "location" in values:
        values["location"] = normalize_location(values["location"])
    if "work_types" in values and values["work_types"] is not None:
        values["work_types"] = [wt.value for wt in data.work_types]
    if values.get("school_id") and await db.get(School, values["school_id"]) is None:
        raise NotFoundError("Không tìm thấy trường")
    for key, value in values.items():
        setattr(profile, key, value)
    profile.updated_at = utcnow()
    await db.commit()
    return await build_profile_response(db, profile)


def _document_response(doc: CandidateDocument) -> DocumentResponse:
    return DocumentResponse.model_validate(doc, from_attributes=True)


async def upload_document(
    db: AsyncSession,
    profile: CandidateProfile,
    *,
    file_name: str,
    content: bytes,
    document_type: DocumentType,
) -> CvAnalysisResponse:
    """Lưu file, đọc nội dung, chạy AI trích kỹ năng/học vấn/dự án (cần đồng ý 'phân tích CV')."""
    await privacy_service.require_consent(db, profile.id, ConsentPurpose.CV_ANALYSIS)
    file_format = FILE_EXTENSIONS.get(Path(file_name).suffix.lower())
    if file_format is None:
        raise ValidationError("Chỉ hỗ trợ file PDF hoặc DOCX")
    if len(content) > UPLOAD_MAX_SIZE_MB * 1024 * 1024:
        raise ValidationError(f"File vượt quá {UPLOAD_MAX_SIZE_MB}MB")

    try:
        text = extract_text(content, file_format)
    except Exception as exc:  # thư viện đọc file ném nhiều loại lỗi khác nhau với file hỏng
        raise ValidationError("Không đọc được file, vui lòng kiểm tra lại") from exc
    if not text.strip():
        raise ValidationError("File không có văn bản (có thể là ảnh scan)")

    upload_dir = Path(UPLOAD_DIR) / str(profile.id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    storage_path = upload_dir / f"{uuid4().hex}{Path(file_name).suffix.lower()}"
    storage_path.write_bytes(content)

    dictionary = await skill_service.load_dictionary(db)
    parsed = parse_cv(text, dictionary)
    now = utcnow()
    document = CandidateDocument(
        candidate_id=profile.id, document_type=document_type, file_format=file_format,
        file_name=file_name, storage_path=str(storage_path), raw_text=text, parsed_at=now,
    )
    db.add(document)

    existing = {
        cs.skill_id: cs
        for cs in (
            await db.exec(select(CandidateSkill).where(CandidateSkill.candidate_id == profile.id))
        ).all()
    }
    for skill in parsed.skills:
        current = existing.get(skill.skill_id)
        if current is None:
            db.add(
                CandidateSkill(
                    candidate_id=profile.id, skill_id=skill.skill_id,
                    source=SkillSource.AI_EXTRACTED, is_confirmed=False,
                )
            )
        elif current.deleted_at is not None and not current.is_confirmed:
            current.deleted_at = None

    # Gộp nội dung mọi tài liệu để làm văn bản so khớp
    profile.cv_text = "\n\n".join(filter(None, [profile.cv_text, text]))[-50_000:]
    if parsed.education:
        profile.education = parsed.education
    if parsed.projects:
        profile.projects = [*(profile.projects or []), *parsed.projects]
    profile.years_experience = max(profile.years_experience, parsed.years_experience)
    profile.updated_at = now
    try:
        await db.commit()
    except Exception:
        # Không để lại file mồ côi trên đĩa khi ghi CSDL thất bại
        storage_path.unlink(missing_ok=True)
        raise

    names = {s.skill_id for s in parsed.skills}
    extracted = [s for s in await _skill_rows(db, profile.id) if s.skill_id in names]
    return CvAnalysisResponse(
        document=_document_response(document),
        extracted_skills=extracted,
        education=parsed.education,
        projects=parsed.projects,
        years_experience=parsed.years_experience,
        email=parsed.email,
        phone=parsed.phone,
    )


async def list_documents(db: AsyncSession, profile: CandidateProfile) -> DocumentListResponse:
    docs = (
        await db.exec(
            select(CandidateDocument)
            .where(
                CandidateDocument.candidate_id == profile.id,
                col(CandidateDocument.deleted_at).is_(None),
            )
            .order_by(col(CandidateDocument.created_at).desc())
        )
    ).all()
    return DocumentListResponse(items=[_document_response(d) for d in docs], total=len(docs))


async def delete_document(db: AsyncSession, profile: CandidateProfile, document_id: int) -> None:
    doc = await db.get(CandidateDocument, document_id)
    if doc is None or doc.candidate_id != profile.id or doc.deleted_at is not None:
        raise NotFoundError("Không tìm thấy tài liệu")
    doc.deleted_at = utcnow()
    Path(doc.storage_path).unlink(missing_ok=True)
    await db.commit()


async def confirm_skills(
    db: AsyncSession, profile: CandidateProfile, data: SkillConfirmRequest
) -> CandidateProfileResponse:
    """Ứng viên xác nhận/sửa danh sách kỹ năng AI đã trích; kỹ năng bị bỏ sẽ bị xóa mềm."""
    wanted = {item.skill_id: item for item in data.skills}
    valid = set(
        (await db.exec(select(Skill.id).where(col(Skill.id).in_(list(wanted))))).all()
    )
    if set(wanted) - valid:
        raise ValidationError(f"Kỹ năng không tồn tại: {sorted(set(wanted) - valid)}")
    existing = {
        cs.skill_id: cs
        for cs in (
            await db.exec(select(CandidateSkill).where(CandidateSkill.candidate_id == profile.id))
        ).all()
    }
    now = utcnow()
    for skill_id, row in existing.items():
        if skill_id not in wanted and row.deleted_at is None:
            row.deleted_at = now
    for skill_id, item in wanted.items():
        row = existing.get(skill_id)
        if row is None:
            db.add(
                CandidateSkill(
                    candidate_id=profile.id, skill_id=skill_id, source=SkillSource.MANUAL,
                    is_confirmed=True, level=item.level,
                )
            )
        else:
            row.deleted_at, row.is_confirmed, row.level, row.updated_at = None, True, item.level, now
    await db.commit()
    return await build_profile_response(db, profile)


async def set_discoverable(
    db: AsyncSession, profile: CandidateProfile, is_discoverable: bool
) -> CandidateProfileResponse:
    if is_discoverable:
        await privacy_service.require_consent(db, profile.id, ConsentPurpose.EMPLOYER_DISCOVERY)
    profile.is_discoverable = is_discoverable
    profile.updated_at = utcnow()
    await db.commit()
    return await build_profile_response(db, profile)


async def load_candidate_features(
    db: AsyncSession, profiles: list[CandidateProfile]
) -> list[CandidateFeatures]:
    """Chỉ dùng kỹ năng chưa bị xóa (đã xác nhận hoặc AI trích chưa được xem lại)."""
    ids = [p.id for p in profiles]
    skill_map: dict[int, set[int]] = {pid: set() for pid in ids}
    if ids:
        rows = (
            await db.exec(
                select(CandidateSkill.candidate_id, CandidateSkill.skill_id).where(
                    col(CandidateSkill.candidate_id).in_(ids),
                    col(CandidateSkill.deleted_at).is_(None),
                )
            )
        ).all()
        for candidate_id, skill_id in rows:
            skill_map[candidate_id].add(skill_id)
    names = await skill_service.get_skill_names(db)
    features = []
    for p in profiles:
        project_text = " ".join(
            f"{proj.get('name', '')} {proj.get('description', '')}" for proj in p.projects or []
        )
        skill_text = " ".join(names.get(sid, "") for sid in skill_map[p.id])
        features.append(
            CandidateFeatures(
                candidate_id=p.id,
                skill_ids=skill_map[p.id],
                text=" ".join(
                    filter(None, [p.target_position, p.major, skill_text, project_text, p.cv_text])
                ),
                years_experience=p.years_experience,
                location=p.location,
                work_types=p.work_types or [],
                target_position=p.target_position,
            )
        )
    return features
