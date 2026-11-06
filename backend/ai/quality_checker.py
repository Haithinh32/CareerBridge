"""Phát hiện tin kém chất lượng: trùng, hết hạn, 'fresher' đòi nhiều năm kinh nghiệm, lừa đảo, thiếu thông tin."""

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ai.text_utils import normalize_text, tokenize
from constants import (
    DUPLICATE_SIMILARITY_THRESHOLD,
    FRESHER_MAX_YEARS,
    MIN_DESCRIPTION_LENGTH,
    SCAM_SCORE_THRESHOLD,
    UNREALISTIC_JUNIOR_SALARY_VND,
)
from enums.job import FlagType, JobLevel

_FRESHER_TEXT_RE = re.compile(
    r"\b(fresher|intern|thuc tap|moi tot nghiep|sinh vien|chua co kinh nghiem|entry level)\b"
)

# (mẫu, điểm rủi ro, mô tả) - cộng dồn, gắn cờ khi tổng >= SCAM_SCORE_THRESHOLD
SCAM_RULES: list[tuple[str, float, str]] = [
    (r"dat coc|nop tien|dong tien|phi ho so|phi dao tao|phi dong phuc|le phi", 0.5,
     "yêu cầu ứng viên nộp tiền/đặt cọc"),
    (r"viec nhe luong cao|thu nhap khung|kiem tien nhanh|lam giau", 0.4,
     "hứa hẹn thu nhập phi thực tế"),
    (r"chuyen khoan|so tai khoan|ngan hang.*truoc", 0.3, "đề cập chuyển khoản"),
    (r"like ?share|danh gia san pham|nhan hang tai nha|cong tac vien online|chot don", 0.3,
     "hình thức việc làm thường gặp trong lừa đảo"),
    (r"chi lien he (qua )?(zalo|telegram)|lien he (zalo|telegram) ngay|inbox ngay", 0.2,
     "chỉ liên hệ qua kênh chat cá nhân"),
    (r"khong can kinh nghiem.{0,40}(\d{2,3}) ?(trieu|tr)", 0.2,
     "không cần kinh nghiệm nhưng lương rất cao"),
]


@dataclass
class JobSnapshot:
    job_id: int
    title: str
    description: str
    company_name: str
    level: str | None = None
    min_years_experience: float = 0.0
    salary_max: int | None = None
    deadline: date | None = None
    skill_count: int = 0
    has_verified_company: bool = False


@dataclass
class FlagResult:
    flag_type: FlagType
    score: float
    detail: str
    related_job_id: int | None = None


def check_expired(job: JobSnapshot, today: date) -> FlagResult | None:
    if job.deadline and job.deadline < today:
        return FlagResult(FlagType.EXPIRED, 1.0, f"Đã quá hạn nộp ({job.deadline.isoformat()})")
    return None


def check_fresher_requires_experience(job: JobSnapshot) -> FlagResult | None:
    is_entry = job.level in (JobLevel.INTERN.value, JobLevel.FRESHER.value) or bool(
        _FRESHER_TEXT_RE.search(normalize_text(job.title))
    )
    if is_entry and job.min_years_experience > FRESHER_MAX_YEARS:
        return FlagResult(
            FlagType.FRESHER_REQUIRES_EXPERIENCE,
            min(1.0, job.min_years_experience / 3),
            f"Tin dành cho fresher/thực tập nhưng yêu cầu {job.min_years_experience:g} năm "
            "kinh nghiệm",
        )
    return None


def scam_score(job: JobSnapshot) -> tuple[float, list[str]]:
    text = normalize_text(f"{job.title} {job.description}")
    score, reasons = 0.0, []
    for pattern, weight, reason in SCAM_RULES:
        if re.search(pattern, text):
            score += weight
            reasons.append(reason)
    is_entry = job.level in (JobLevel.INTERN.value, JobLevel.FRESHER.value)
    if is_entry and job.salary_max and job.salary_max > UNREALISTIC_JUNIOR_SALARY_VND:
        score += 0.3
        reasons.append("lương thực tập/fresher cao bất thường")
    if not job.has_verified_company and reasons:
        score += 0.1
        reasons.append("doanh nghiệp chưa xác minh")
    return min(score, 1.0), reasons


def check_scam(job: JobSnapshot) -> FlagResult | None:
    score, reasons = scam_score(job)
    if score >= SCAM_SCORE_THRESHOLD:
        return FlagResult(FlagType.SCAM, round(score, 2), "Dấu hiệu lừa đảo: " + "; ".join(reasons))
    return None


def check_incomplete(job: JobSnapshot) -> FlagResult | None:
    missing = []
    if len(job.description.strip()) < MIN_DESCRIPTION_LENGTH:
        missing.append("mô tả quá ngắn")
    if job.skill_count == 0:
        missing.append("không có kỹ năng yêu cầu")
    if missing:
        return FlagResult(FlagType.INCOMPLETE, 0.5, "Thiếu thông tin: " + ", ".join(missing))
    return None


def check_job(job: JobSnapshot, today: date) -> list[FlagResult]:
    checks = (
        check_expired(job, today),
        check_fresher_requires_experience(job),
        check_scam(job),
        check_incomplete(job),
    )
    return [flag for flag in checks if flag is not None]


def find_duplicates(
    jobs: list[JobSnapshot], threshold: float = DUPLICATE_SIMILARITY_THRESHOLD
) -> list[tuple[int, int, float]]:
    """Trả về các cặp (id mới hơn, id cũ hơn, độ tương đồng) bị coi là trùng.

    Hai tin trùng khi nội dung gần giống nhau VÀ cùng doanh nghiệp hoặc cùng tiêu đề.
    """
    if len(jobs) < 2:
        return []
    # Chặn theo khối (blocking): chỉ so các tin cùng doanh nghiệp hoặc cùng tiêu đề,
    # tránh ma trận n x n khi số tin lớn.
    blocks: dict[str, list[int]] = defaultdict(list)
    for i, job in enumerate(jobs):
        blocks["c:" + normalize_text(job.company_name)].append(i)
        blocks["t:" + normalize_text(job.title)].append(i)
    candidate_pairs = {
        (members[x], members[y])
        for members in blocks.values() if len(members) > 1
        for x in range(len(members)) for y in range(x + 1, len(members))
    }
    if not candidate_pairs:
        return []

    docs = [normalize_text(f"{j.title} {j.company_name} {j.description}") for j in jobs]
    vectorizer = TfidfVectorizer(tokenizer=tokenize, token_pattern=None, lowercase=False)
    matrix = vectorizer.fit_transform(docs)
    pairs: list[tuple[int, int, float]] = []
    for i, k in sorted(candidate_pairs):
        sim = float(cosine_similarity(matrix[i], matrix[k])[0, 0])
        if sim < threshold:
            continue
        a, b = jobs[i], jobs[k]
        newer, older = (a, b) if a.job_id > b.job_id else (b, a)
        pairs.append((newer.job_id, older.job_id, round(sim, 3)))
    return pairs
