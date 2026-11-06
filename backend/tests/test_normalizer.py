import pytest

from ai.normalizer import detect_level, normalize_location, parse_salary, parse_years_required
from ai.text_utils import normalize_text, strip_accents
from enums.job import JobLevel

M = 1_000_000


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("10 - 15 triệu", (10 * M, 15 * M)),
        ("10-15tr", (10 * M, 15 * M)),
        ("15.000.000 - 20.000.000 VNĐ", (15 * M, 20 * M)),
        ("Up to 20tr", (None, 20 * M)),
        ("Từ 8 triệu", (8 * M, None)),
        ("$1000 - $1500", (25 * M, 37_500_000)),
        ("1.5k - 2k USD", (37_500_000, 50 * M)),
        ("Thỏa thuận", (None, None)),
        ("Cạnh tranh", (None, None)),
        ("", (None, None)),
        (None, (None, None)),
    ],
)
def test_parse_salary(raw: str | None, expected: tuple[int | None, int | None]) -> None:
    assert parse_salary(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("TP.HCM", "Hồ Chí Minh"),
        ("Quận 1, TP. Hồ Chí Minh", "Hồ Chí Minh"),
        ("Sài Gòn", "Hồ Chí Minh"),
        ("HN", "Hà Nội"),
        ("Cầu Giấy, Hà Nội", "Hà Nội"),
        ("Remote", "Từ xa"),
        ("Da Nang", "Đà Nẵng"),
        ("Vũng Tàu", "Vũng Tàu"),
    ],
)
def test_normalize_location(raw: str, expected: str) -> None:
    assert normalize_location(raw) == expected


def test_detect_level() -> None:
    assert detect_level("Thực tập sinh Python") == JobLevel.INTERN
    assert detect_level("Senior Java Developer") == JobLevel.SENIOR
    assert detect_level("Fresher React") == JobLevel.FRESHER
    assert detect_level("International Sales Manager") is None


def test_parse_years_required() -> None:
    assert parse_years_required("Yêu cầu ít nhất 3 năm kinh nghiệm Java") == 3
    assert parse_years_required("2-3 năm kinh nghiệm") == 2
    assert parse_years_required("3+ years of experience") == 3
    assert parse_years_required("Không yêu cầu kinh nghiệm") == 0


def test_text_normalization() -> None:
    assert strip_accents("Đà Nẵng") == "Da Nang"
    assert normalize_text("  Kỹ   Năng  ") == "ky nang"
