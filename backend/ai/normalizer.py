"""Làm sạch và chuẩn hóa dữ liệu tin tuyển dụng: lương, địa điểm, cấp bậc, kinh nghiệm."""

import re

from ai.text_utils import normalize_text
from constants import USD_TO_VND
from enums.job import JobLevel

MILLION = 1_000_000
MAX_SALARY_VND = 1_000_000_000

# Tên chuẩn (có dấu) -> các cách viết đã bỏ dấu
LOCATION_ALIASES: dict[str, tuple[str, ...]] = {
    "Hồ Chí Minh": ("ho chi minh", "tp hcm", "tp.hcm", "tphcm", "hcm", "hcmc", "sai gon", "saigon",
                    "tp. ho chi minh", "hochiminh"),
    "Hà Nội": ("ha noi", "hanoi", "hn", "tp ha noi"),
    "Đà Nẵng": ("da nang", "danang"),
    "Cần Thơ": ("can tho", "cantho"),
    "Hải Phòng": ("hai phong", "haiphong"),
    "Bình Dương": ("binh duong",),
    "Đồng Nai": ("dong nai", "bien hoa"),
    "Huế": ("hue", "thua thien hue"),
    "Từ xa": ("remote", "tu xa", "lam viec tu xa", "wfh", "work from home"),
}

_NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")
_THOUSANDS_RE = re.compile(r"(?<=\d)[.,](?=\d{3}(?:\D|$))")
_NEGOTIABLE_RE = re.compile(r"thoa thuan|negotiable|canh tranh|competitive|thuong luong")
_UPPER_ONLY_RE = re.compile(r"up ?to|toi da|len den|len toi|^den|^<|duoi")
_LOWER_ONLY_RE = re.compile(r"^tu|from|tren|^>|it nhat|toi thieu|\+$")
_YEARS_REQUIRED_RE = re.compile(
    r"(?:it nhat|toi thieu|tren|at least|minimum|min)?\s*(\d+(?:[.,]\d)?)\s*\+?\s*"
    r"(?:-\s*\d+\s*)?(?:nam|years?|yrs?)\s*(?:kinh nghiem|of experience|experience|kn)"
)
_LEVEL_PATTERNS: list[tuple[JobLevel, str]] = [
    (JobLevel.INTERN, r"\b(intern|internship|thuc tap|thuc tap sinh)\b"),
    (JobLevel.FRESHER, r"\b(fresher|moi tot nghiep|sinh vien moi ra truong|entry level)\b"),
    (JobLevel.SENIOR, r"\b(senior|sr|lead|truong nhom|principal)\b"),
    (JobLevel.MIDDLE, r"\b(middle|mid-level|mid)\b"),
    (JobLevel.JUNIOR, r"\b(junior|jr)\b"),
]


def parse_salary(raw: str | None) -> tuple[int | None, int | None]:
    """Đổi chuỗi lương bất kỳ về (min, max) VND/tháng. Không xác định -> (None, None)."""
    if not raw:
        return None, None
    text = normalize_text(raw)
    if _NEGOTIABLE_RE.search(text):
        return None, None

    is_usd = "$" in raw or "usd" in text
    compact = text
    while _THOUSANDS_RE.search(compact):
        compact = _THOUSANDS_RE.sub("", compact)
    numbers = [float(n.replace(",", ".")) for n in _NUMBER_RE.findall(compact)]
    if not numbers:
        return None, None

    if is_usd:
        unit = 1000 * USD_TO_VND if re.search(r"\d\s*k\b", compact) else USD_TO_VND
    elif re.search(r"trieu|tr\b|\d\s*m\b|million", compact) or max(numbers) < 1000:
        unit = MILLION
    else:
        unit = 1
    values = sorted(int(n * unit) for n in numbers[:2])
    if any(v <= 0 or v > MAX_SALARY_VND for v in values):
        return None, None

    if len(values) == 2:
        return values[0], values[1]
    if _UPPER_ONLY_RE.search(text):
        return None, values[0]
    if _LOWER_ONLY_RE.search(text):
        return values[0], None
    return values[0], values[0]


def normalize_location(raw: str | None) -> str | None:
    text = normalize_text(raw)
    if not text:
        return None
    for canonical, aliases in LOCATION_ALIASES.items():
        for alias in aliases:
            if re.search(rf"(?<![a-z]){re.escape(alias)}(?![a-z])", text):
                return canonical
    return raw.strip() if raw else None


def detect_level(title: str, description: str = "") -> JobLevel | None:
    text = normalize_text(f"{title} {description[:300]}")
    for level, pattern in _LEVEL_PATTERNS:
        if re.search(pattern, text):
            return level
    return None


def parse_years_required(text: str | None) -> float:
    values = [
        float(m.group(1).replace(",", "."))
        for m in _YEARS_REQUIRED_RE.finditer(normalize_text(text))
    ]
    return max(values) if values else 0.0
