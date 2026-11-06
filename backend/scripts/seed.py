"""Tạo dữ liệu mẫu. Chạy từ thư mục backend:  python -m scripts.seed

XÓA TOÀN BỘ dữ liệu hiện có rồi tạo lại. Mọi tài khoản dùng mật khẩu 'matkhau123'.
"""

import asyncio
import random
from datetime import timedelta

from sqlmodel import select

from ai.matcher import CandidateFeatures, rank_jobs_for_candidate
from ai.normalizer import detect_level, normalize_location, parse_salary
from ai.text_utils import normalize_text
from core.database import drop_db, init_db, session_factory
from enums.candidate import (
    AccessSource,
    ApplicationStatus,
    ConsentPurpose,
    RevokeReason,
    SkillSource,
)
from enums.job import JobLevel, JobSource, JobStatus, WorkType
from enums.user import UserRole, VerificationStatus
from models import (
    Application,
    CandidateProfile,
    CandidateSkill,
    Company,
    Consent,
    Course,
    DataQualitySnapshot,
    Job,
    JobSkill,
    ProfileAccessGrant,
    RecommendationFeedback,
    School,
    SchoolCompanyLink,
    SchoolFeedPost,
    Skill,
    SkillAlias,
    User,
)
from scripts.seed_data import (
    BAD_JOBS,
    COMPANIES,
    COURSES,
    FIRST_NAMES,
    JOB_TEMPLATES,
    LAST_NAMES,
    LEVEL_SETTINGS,
    LOCATION_FORMATS,
    MAJORS,
    MIDDLE_NAMES,
    SALARY_FORMATS,
    SCHOOLS,
    SKILLS,
    TARGET_POSITIONS,
)
from security.auth import hash_password
from services import quality_service
from services.job_view import build_job_features
from utils.tax_code import make_valid_tax_code
from utils.time import utcnow

PASSWORD = "matkhau123"
N_JOBS = 220
N_CANDIDATES = 180
N_HISTORY_SNAPSHOTS = 10
OPEN_WINDOW_DAYS = 90
FEEDBACK_PER_CANDIDATE = 6
SOFT_SKILLS = ["Tiếng Anh", "Giao tiếp", "Làm việc nhóm", "Git", "Agile/Scrum"]

rng = random.Random(42)


def _person_name() -> str:
    return f"{rng.choice(LAST_NAMES)} {rng.choice(MIDDLE_NAMES)} {rng.choice(FIRST_NAMES)}"


def _email_slug(name: str, i: int) -> str:
    return normalize_text(name).replace(" ", ".") + str(i)


def _salary_raw(lo: int, hi: int) -> str:
    fmt = rng.choice(SALARY_FORMATS)
    return fmt.format(lo=lo, hi=hi, lo_full=f"{lo * 1_000_000:,}".replace(",", "."),
                      hi_full=f"{hi * 1_000_000:,}".replace(",", "."))


def _job_description(title: str, required: list[str], optional: list[str], years: float) -> str:
    years_line = (
        f"- Có ít nhất {years:g} năm kinh nghiệm ở vị trí tương đương" if years
        else "- Chấp nhận sinh viên mới tốt nghiệp, sẽ được đào tạo thêm"
    )
    optional_line = f"- Ưu tiên ứng viên biết {', '.join(optional)}" if optional else ""
    return (
        f"Mô tả công việc:\n- Tham gia phát triển sản phẩm ở vị trí {title}\n"
        "- Phối hợp với các nhóm sản phẩm, thiết kế và kiểm thử\n"
        "- Viết tài liệu kỹ thuật, tham gia review và cải tiến quy trình\n\n"
        f"Yêu cầu:\n- Thành thạo {', '.join(required)}\n{optional_line}\n{years_line}\n"
        "- Có khả năng tự học, làm việc nhóm tốt\n\n"
        "Quyền lợi:\n- Lương tháng 13, thưởng theo hiệu quả công việc\n"
        "- Bảo hiểm đầy đủ, 12 ngày phép/năm, khám sức khỏe định kỳ"
    )


def _cv_text(name: str, school: str, major: str, target: str, skills: list[str],
             years: float, template_title: str) -> str:
    projects = [
        f"Đồ án tốt nghiệp: Hệ thống {template_title.lower()} mini\n"
        f"- Sử dụng {', '.join(skills[:3])}",
        f"Dự án cá nhân: Ứng dụng quản lý công việc\n- Công nghệ: {', '.join(skills[1:4])}",
    ]
    experience = (
        f"KINH NGHIỆM LÀM VIỆC\n{years:g} năm kinh nghiệm\n"
        f"- Thực tập/làm việc ở vị trí {target}\n" if years else ""
    )
    return (
        f"{name}\nEmail: {_email_slug(name, 0)}@gmail.com\n\nMỤC TIÊU\n"
        f"Mong muốn trở thành {target}.\n\nHỌC VẤN\n{school}\nChuyên ngành {major}\n"
        f"GPA: {rng.choice(['3.0', '3.2', '3.4', '3.6'])}/4\n\n{experience}"
        f"DỰ ÁN\n" + "\n".join(projects) + f"\n\nKỸ NĂNG\n{', '.join(skills)}\n"
    )


async def seed() -> None:
    await drop_db()
    await init_db()
    now = utcnow()
    password_hash = hash_password(PASSWORD)

    async with session_factory() as db:
        # ---- Từ điển kỹ năng & khóa học ----
        skill_ids: dict[str, int] = {}
        for name, category, aliases in SKILLS:
            skill = Skill(name=name, category=category)
            db.add(skill)
            await db.flush()
            skill_ids[name] = skill.id
            for alias in aliases:
                db.add(SkillAlias(skill_id=skill.id, alias=normalize_text(alias)))
        for skill_name, title, provider, url, hours, is_free in COURSES:
            db.add(Course(skill_id=skill_ids[skill_name], title=title, provider=provider,
                          url=url, duration_hours=hours, is_free=is_free))

        # ---- Tài khoản quản trị, nhà trường, doanh nghiệp ----
        db.add(User(email="admin@careerbridge.vn", password_hash=password_hash,
                    full_name="Quản trị viên", role=UserRole.ADMIN))
        schools: list[School] = []
        for i, school_name in enumerate(SCHOOLS, start=1):
            owner = User(email=f"truong{i}@careerbridge.vn", password_hash=password_hash,
                         full_name=f"Phòng Quan hệ doanh nghiệp - {school_name}",
                         role=UserRole.SCHOOL)
            db.add(owner)
            await db.flush()
            school = School(owner_user_id=owner.id, name=school_name)
            db.add(school)
            schools.append(school)

        companies: list[Company] = []
        for i, (company_name, industry, city) in enumerate(COMPANIES, start=1):
            owner = User(email=f"ntd{i}@careerbridge.vn", password_hash=password_hash,
                         full_name=f"Bộ phận tuyển dụng {i}", role=UserRole.EMPLOYER)
            db.add(owner)
            await db.flush()
            tax_code = None
            while tax_code is None:
                tax_code = make_valid_tax_code(f"0{rng.randint(10_000_000, 99_999_999)}")
            company = Company(owner_user_id=owner.id, name=company_name, tax_code=tax_code,
                              verification_status=VerificationStatus.VERIFIED,
                              industry=industry, address=city)
            db.add(company)
            companies.append(company)
        await db.flush()
        for school in schools:
            for company in rng.sample(companies, 4):
                db.add(SchoolCompanyLink(school_id=school.id, company_id=company.id))

        # ---- Tin tuyển dụng ----
        jobs: list[Job] = []
        job_template: dict[int, int] = {}
        for _ in range(N_JOBS):
            t_idx = rng.randrange(len(JOB_TEMPLATES))
            base_title, required, optional, (sal_lo, sal_hi) = JOB_TEMPLATES[t_idx]
            level = rng.choices(list(LEVEL_SETTINGS), weights=[1, 2, 3, 3, 2])[0]
            prefix, years, factor = LEVEL_SETTINGS[level]
            company = rng.choice(companies)
            days_ago = int(rng.random() ** 1.6 * 365)
            posted = now - timedelta(days=days_ago, hours=rng.randint(0, 23))
            # Lương tăng nhẹ theo thời gian để biểu đồ xu hướng có ý nghĩa
            trend = 1 + 0.12 * (1 - days_ago / 365)
            lo = max(3, round(sal_lo * factor * trend))
            hi = max(lo + 2, round(sal_hi * factor * trend))
            salary_raw = _salary_raw(lo, hi)
            city = company.address if rng.random() < 0.7 else rng.choice(list(LOCATION_FORMATS))
            location_raw = rng.choice(LOCATION_FORMATS[city])
            opt = rng.sample(optional, k=rng.randint(1, len(optional)))
            title = f"{prefix} {base_title}".strip()
            is_open = days_ago <= OPEN_WINDOW_DAYS
            salary_min, salary_max = parse_salary(salary_raw)
            work_type = (
                WorkType.INTERNSHIP if level == "intern"
                else rng.choices([WorkType.FULL_TIME, WorkType.HYBRID, WorkType.REMOTE,
                                  WorkType.PART_TIME], weights=[6, 2, 1, 1])[0]
            )
            job = Job(
                company_id=company.id, company_name=company.name, title=title,
                description=_job_description(title, required, opt, years),
                location_raw=location_raw, location=normalize_location(location_raw),
                work_type=work_type, level=detect_level(title) or JobLevel(level),
                salary_raw=salary_raw, salary_min=salary_min, salary_max=salary_max,
                min_years_experience=years, posted_at=posted,
                deadline=(posted + timedelta(days=100)).date(),
                status=JobStatus.OPEN if is_open else JobStatus.CLOSED,
                closed_at=None if is_open else posted + timedelta(days=45),
                source=JobSource.EMPLOYER, created_at=posted, updated_at=posted,
            )
            db.add(job)
            await db.flush()
            jobs.append(job)
            job_template[job.id] = t_idx
            for name in required:
                db.add(JobSkill(job_id=job.id, skill_id=skill_ids[name], is_required=True))
            for name in opt:
                db.add(JobSkill(job_id=job.id, skill_id=skill_ids[name], is_required=False))

        # Tin có vấn đề + một bản sao y hệt của một tin đang mở (để minh họa phát hiện tin trùng)
        for bad in BAD_JOBS:
            salary_min, salary_max = parse_salary(bad["salary"])
            db.add(Job(
                company_name=bad["company"], title=bad["title"], description=bad["description"],
                location_raw=bad["location"], location=normalize_location(bad["location"]),
                level=JobLevel(bad["level"]), min_years_experience=bad["years"],
                salary_raw=bad["salary"], salary_min=salary_min, salary_max=salary_max,
                posted_at=now - timedelta(days=1), deadline=(now + timedelta(days=30)).date(),
                source=JobSource.CRAWLER, external_id=f"bad-{normalize_text(bad['title'])}",
            ))
        original = next(j for j in jobs if j.status == JobStatus.OPEN)
        duplicate = Job(**original.model_dump(exclude={"id", "created_at", "updated_at"}))
        duplicate.posted_at = now
        db.add(duplicate)
        await db.flush()
        for js in (await db.exec(select(JobSkill).where(JobSkill.job_id == original.id))).all():
            db.add(JobSkill(job_id=duplicate.id, skill_id=js.skill_id, is_required=js.is_required))
        await db.commit()

        open_jobs = [j for j in jobs if j.status == JobStatus.OPEN]
        for school in schools:
            linked = (await db.exec(select(SchoolCompanyLink.company_id).where(
                SchoolCompanyLink.school_id == school.id))).all()
            for job in [j for j in open_jobs if j.company_id in linked][:5]:
                db.add(SchoolFeedPost(school_id=school.id, job_id=job.id,
                                      note="Doanh nghiệp đối tác của trường đang tuyển"))

        # ---- Ứng viên ----
        profiles: list[CandidateProfile] = []
        profile_template: dict[int, int] = {}
        for i in range(N_CANDIDATES + 1):
            is_demo = i == 0
            name = "Nguyễn Minh An" if is_demo else _person_name()
            email = "ungvien@careerbridge.vn" if is_demo else f"{_email_slug(name, i)}@example.com"
            user = User(email=email, password_hash=password_hash, full_name=name,
                        role=UserRole.CANDIDATE)
            db.add(user)
            await db.flush()

            t_idx = 0 if is_demo else rng.randrange(len(JOB_TEMPLATES))
            base_title, required, optional, _ = JOB_TEMPLATES[t_idx]
            have_req = rng.sample(required, k=max(1, round(len(required) * rng.uniform(0.5, 1))))
            have_opt = rng.sample(optional, k=rng.randint(0, len(optional)))
            extras = rng.sample(SOFT_SKILLS, k=rng.randint(1, 3))
            # Nhiễu: thỉnh thoảng có kỹ năng của ngành khác
            noise = [rng.choice(SKILLS)[0]] if rng.random() < 0.3 else []
            skills = list(dict.fromkeys(have_req + have_opt + extras + noise))
            school = rng.choice(schools)
            major = rng.choice(MAJORS)
            years = rng.choice([0, 0, 0, 0.5, 1, 1, 2, 3])
            target = TARGET_POSITIONS[base_title]
            city = rng.choice(["Hà Nội", "Hồ Chí Minh", "Hồ Chí Minh", "Đà Nẵng"])
            profile = CandidateProfile(
                user_id=user.id, school_id=school.id, major=major,
                study_year=rng.randint(3, 5), location=city,
                work_types=rng.sample([WorkType.FULL_TIME.value, WorkType.INTERNSHIP.value,
                                       WorkType.HYBRID.value, WorkType.REMOTE.value], k=2),
                availability=rng.choice(["Toàn thời gian", "Các buổi chiều trong tuần",
                                         "Thứ 2 - Thứ 6", "Cuối tuần"]),
                target_position=target, years_experience=years,
                education=[{"school": school.name, "degree": "Cử nhân", "start_year": 2021,
                            "end_year": 2025, "gpa": None}],
                cv_text=_cv_text(name, school.name, major, target, skills, years, base_title),
                is_discoverable=is_demo or rng.random() < 0.6,
            )
            db.add(profile)
            await db.flush()
            profiles.append(profile)
            profile_template[profile.id] = t_idx
            for skill_name in skills:
                db.add(CandidateSkill(
                    candidate_id=profile.id, skill_id=skill_ids[skill_name],
                    source=rng.choice([SkillSource.AI_EXTRACTED, SkillSource.MANUAL]),
                    is_confirmed=True, level=rng.randint(2, 5),
                ))
            grants = {
                ConsentPurpose.CV_ANALYSIS: is_demo or rng.random() < 0.95,
                ConsentPurpose.JOB_RECOMMENDATION: is_demo or rng.random() < 0.95,
                ConsentPurpose.EMPLOYER_DISCOVERY: profile.is_discoverable,
                ConsentPurpose.SCHOOL_SHARING: is_demo or rng.random() < 0.7,
                ConsentPurpose.MODEL_IMPROVEMENT: is_demo or rng.random() < 0.8,
            }
            for purpose, granted in grants.items():
                db.add(Consent(candidate_id=profile.id, purpose=purpose, is_granted=granted,
                               granted_at=now if granted else None))

        # ---- Ứng tuyển với lịch sử trạng thái (dữ liệu cho phễu chuyển đổi) ----
        jobs_by_template: dict[int, list[Job]] = {}
        for job in jobs:
            jobs_by_template.setdefault(job_template[job.id], []).append(job)
        for profile in profiles[1:]:
            t_idx = profile_template[profile.id]
            chosen: set[int] = set()
            for _ in range(rng.randint(1, 5)):
                same = rng.random() < 0.7 and jobs_by_template.get(t_idx)
                job = rng.choice(jobs_by_template[t_idx] if same else jobs)
                if job.id in chosen:
                    continue
                chosen.add(job.id)
                fit = job_template[job.id] == t_idx
                at = job.posted_at + timedelta(days=rng.randint(1, 20))
                history = [{"status": ApplicationStatus.SUBMITTED.value, "at": at.isoformat()}]
                status = ApplicationStatus.SUBMITTED
                path = [
                    (ApplicationStatus.VIEWED, 0.8),
                    (ApplicationStatus.INTERVIEW, 0.45 if fit else 0.12),
                    (ApplicationStatus.HIRED, 0.35 if fit else 0.1),
                ]
                for next_status, prob in path:
                    at += timedelta(days=rng.randint(1, 7))
                    if rng.random() < prob:
                        status = next_status
                    else:
                        if status != ApplicationStatus.SUBMITTED or rng.random() < 0.5:
                            status = ApplicationStatus.REJECTED
                        break
                    history.append({"status": status.value, "at": at.isoformat()})
                if status == ApplicationStatus.REJECTED:
                    history.append({"status": status.value, "at": at.isoformat()})
                db.add(Application(
                    job_id=job.id, candidate_id=profile.id, status=status,
                    match_score=None, status_history=history, created_at=job.posted_at,
                ))
                revoked = status == ApplicationStatus.REJECTED or job.status != JobStatus.OPEN
                db.add(ProfileAccessGrant(
                    company_id=job.company_id, candidate_id=profile.id, job_id=job.id,
                    source=AccessSource.APPLICATION,
                    revoked_at=at if revoked else None,
                    revoke_reason=(
                        None if not revoked
                        else RevokeReason.CANDIDATE_REJECTED if status == ApplicationStatus.REJECTED
                        else RevokeReason.JOB_CLOSED
                    ),
                ))
        await db.commit()

        # ---- Phản hồi "gợi ý có phù hợp không" ----
        # Nhãn mô phỏng đánh giá của người dùng: phù hợp khi tin cùng nhóm nghề, có 10% nhiễu
        job_features = await build_job_features(db, open_jobs)
        for profile in profiles[1:]:
            skills = set((await db.exec(select(CandidateSkill.skill_id).where(
                CandidateSkill.candidate_id == profile.id))).all())
            candidate = CandidateFeatures(
                candidate_id=profile.id, skill_ids=skills, text=profile.cv_text or "",
                years_experience=profile.years_experience, location=profile.location,
                work_types=profile.work_types, target_position=profile.target_position,
            )
            ranked = rank_jobs_for_candidate(candidate, job_features)
            shown = ranked[:FEEDBACK_PER_CANDIDATE // 2] + rng.sample(
                ranked[FEEDBACK_PER_CANDIDATE // 2:], k=FEEDBACK_PER_CANDIDATE // 2
            )
            for result in shown:
                relevant = job_template[result.job_id] == profile_template[profile.id]
                if rng.random() < 0.1:
                    relevant = not relevant
                db.add(RecommendationFeedback(
                    job_id=result.job_id, candidate_id=profile.id, is_relevant=relevant,
                    features=result.features,
                ))

        # ---- Lịch sử chỉ số chất lượng dữ liệu ----
        for d in range(N_HISTORY_SNAPSHOTS, 0, -1):
            db.add(DataQualitySnapshot(
                taken_at=now - timedelta(days=d), total_jobs=N_JOBS - d,
                completeness=round(rng.uniform(0.93, 0.97), 4),
                accuracy=round(rng.uniform(0.9, 0.96), 4),
                freshness=round(rng.uniform(0.4, 0.5), 4),
                uniqueness=round(rng.uniform(0.98, 1.0), 4),
            ))
        await db.commit()

        scan = await quality_service.scan_all_jobs(db)
        snapshot = await quality_service.take_snapshot(db)

    print("Đã tạo dữ liệu mẫu:")
    print(f"  {len(SKILLS)} kỹ năng, {len(COURSES)} khóa học, {len(SCHOOLS)} trường, "
          f"{len(COMPANIES)} doanh nghiệp")
    print(f"  {N_JOBS + len(BAD_JOBS) + 1} tin tuyển dụng ({len(open_jobs)} đang mở), "
          f"{N_CANDIDATES + 1} ứng viên")
    print(f"  {scan.message}; {snapshot.message}")
    print(f"\nTài khoản demo (mật khẩu: {PASSWORD}):")
    print("  Ứng viên:       ungvien@careerbridge.vn")
    print("  Nhà tuyển dụng: ntd1@careerbridge.vn ... ntd12@careerbridge.vn")
    print("  Nhà trường:     truong1@careerbridge.vn ... truong5@careerbridge.vn")
    print("  Quản trị:       admin@careerbridge.vn")


if __name__ == "__main__":
    asyncio.run(seed())
