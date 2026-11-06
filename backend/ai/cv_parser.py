"""Phân tích CV: đọc PDF/DOCX, tách mục, trích kỹ năng, học vấn, dự án, số năm kinh nghiệm."""

import io
import re
from dataclasses import dataclass, field

from ai.skill_extractor import ExtractedSkill, SkillDictionary
from ai.text_utils import normalize_text
from enums.candidate import FileFormat
from utils.time import today

MAX_REASONABLE_YEARS = 40.0
MAX_SECTION_HEADING_LENGTH = 40

SECTION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "education": ("hoc van", "education", "trinh do hoc van", "qua trinh hoc tap"),
    "experience": (
        "kinh nghiem", "kinh nghiem lam viec", "experience", "work experience",
        "employment", "qua trinh lam viec",
    ),
    "projects": ("du an", "do an", "projects", "project", "personal projects", "du an ca nhan"),
    "skills": ("ky nang", "skills", "technical skills", "ky nang chuyen mon", "cong nghe"),
    "summary": ("muc tieu", "gioi thieu", "summary", "objective", "about me", "tom tat"),
    "certificates": ("chung chi", "certifications", "certificates", "giai thuong", "awards"),
}

_SCHOOL_RE = re.compile(r"dai hoc|university|hoc vien|cao dang|college|institute|truong")
_DEGREE_PATTERNS: dict[str, str] = {
    "Thạc sĩ": r"thac si|master|msc",
    "Kỹ sư": r"ky su|engineer(?:ing)? degree",
    "Cử nhân": r"cu nhan|bachelor|bsc",
    "Cao đẳng": r"cao dang|associate",
}
_YEAR_RE = re.compile(r"\b(19[89]\d|20[0-4]\d)\b")
_GPA_RE = re.compile(r"(?:gpa|diem trung binh|dtb)\s*[:\-]?\s*(\d(?:[.,]\d{1,2})?)\s*(?:/\s*(\d+))?")
_EXPLICIT_YEARS_RE = re.compile(
    r"(\d+(?:[.,]\d)?)\s*\+?\s*(?:nam|years?|yrs?)\s*(?:kinh nghiem|of experience|experience)"
)
_DATE_RANGE_RE = re.compile(
    r"(0?[1-9]|1[0-2])\s*[/\-.]\s*(20\d{2}|19\d{2})\s*(?:-|–|den|to)\s*"
    r"(?:(0?[1-9]|1[0-2])\s*[/\-.]\s*(20\d{2}|19\d{2})|(nay|hien tai|present|now))"
)
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"(?:\+84|0)(?:[\s.]?\d){9,10}")
_BULLET_RE = re.compile(r"^\s*[-•*+●▪◦]\s*")


@dataclass
class ParsedCv:
    raw_text: str
    skills: list[ExtractedSkill]
    education: list[dict]
    projects: list[dict]
    years_experience: float
    email: str | None = None
    phone: str | None = None
    sections: dict[str, str] = field(default_factory=dict)


def extract_text(content: bytes, file_format: FileFormat) -> str:
    """Đọc văn bản thô từ file PDF hoặc DOCX."""
    if file_format == FileFormat.PDF:
        import pdfplumber

        with pdfplumber.open(io.BytesIO(content)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)

    import docx

    document = docx.Document(io.BytesIO(content))
    lines = [para.text for para in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            lines.append(" | ".join(cell.text for cell in row.cells))
    return "\n".join(lines)


def _detect_section(line: str) -> str | None:
    normalized = normalize_text(line).strip(" :.-•*#")
    if not normalized or len(normalized) > MAX_SECTION_HEADING_LENGTH:
        return None
    for section, keywords in SECTION_KEYWORDS.items():
        if normalized in keywords:
            return section
    return None


def split_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {"header": []}
    current = "header"
    for line in text.splitlines():
        section = _detect_section(line)
        if section:
            current = section
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def parse_education(section_text: str) -> list[dict]:
    entries: list[dict] = []
    for line in section_text.splitlines():
        normalized = normalize_text(line)
        if not normalized:
            continue
        if _SCHOOL_RE.search(normalized):
            degree = next(
                (label for label, pat in _DEGREE_PATTERNS.items() if re.search(pat, normalized)),
                None,
            )
            years = [int(y) for y in _YEAR_RE.findall(normalized)]
            entries.append(
                {
                    "school": _BULLET_RE.sub("", line).strip(),
                    "degree": degree,
                    "start_year": min(years) if years else None,
                    "end_year": max(years) if len(years) > 1 else None,
                    "gpa": None,
                }
            )
        gpa_match = _GPA_RE.search(normalized)
        if gpa_match and entries:
            entries[-1]["gpa"] = float(gpa_match.group(1).replace(",", "."))
    return entries


def parse_projects(section_text: str, dictionary: SkillDictionary) -> list[dict]:
    """Mỗi dòng không phải gạch đầu dòng là tên dự án; các dòng gạch đầu dòng sau đó là mô tả."""
    projects: list[dict] = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        is_bullet = bool(_BULLET_RE.match(line))
        if not is_bullet or not projects:
            projects.append({"name": _BULLET_RE.sub("", stripped), "description": ""})
        else:
            sep = " " if projects[-1]["description"] else ""
            projects[-1]["description"] += sep + _BULLET_RE.sub("", stripped)
    for project in projects:
        found = dictionary.extract(f"{project['name']} {project['description']}")
        project["skills"] = [skill.name for skill in found]
    return projects


def estimate_years_experience(text: str, experience_section: str) -> float:
    """Ưu tiên số năm ghi rõ ('2 năm kinh nghiệm'); nếu không có thì cộng các khoảng thời gian."""
    normalized = normalize_text(text)
    explicit = [
        float(m.group(1).replace(",", "."))
        for m in _EXPLICIT_YEARS_RE.finditer(normalized)
        if float(m.group(1).replace(",", ".")) <= MAX_REASONABLE_YEARS
    ]
    if explicit:
        return max(explicit)

    now = today()
    total_months = 0
    for m in _DATE_RANGE_RE.finditer(normalize_text(experience_section)):
        start = int(m.group(2)) * 12 + int(m.group(1))
        if m.group(5):
            end = now.year * 12 + now.month
        else:
            end = int(m.group(4)) * 12 + int(m.group(3))
        if end > start:
            total_months += end - start
    return round(min(total_months / 12, MAX_REASONABLE_YEARS), 1)


def parse_cv(text: str, dictionary: SkillDictionary) -> ParsedCv:
    sections = split_sections(text)
    email = _EMAIL_RE.search(text)
    phone = _PHONE_RE.search(text)
    return ParsedCv(
        raw_text=text,
        skills=dictionary.extract(text),
        education=parse_education(sections.get("education", "")),
        projects=parse_projects(sections.get("projects", ""), dictionary),
        years_experience=estimate_years_experience(text, sections.get("experience", "")),
        email=email.group(0) if email else None,
        phone=re.sub(r"[\s.]", "", phone.group(0)) if phone else None,
        sections=sections,
    )
