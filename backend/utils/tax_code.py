"""Kiểm tra mã số thuế doanh nghiệp Việt Nam (10 số, hoặc 13 số dạng XXXXXXXXXX-YYY cho chi nhánh)."""

import re

_TAX_CODE_RE = re.compile(r"^(\d{10})(?:-?(\d{3}))?$")
_WEIGHTS = (31, 29, 23, 19, 17, 13, 7, 5, 3)
_INVALID_CHECK_DIGIT = 10


def normalize_tax_code(raw: str) -> str:
    return re.sub(r"[\s.]", "", raw)


def _check_digit(first9: list[int]) -> int:
    """Chữ số kiểm tra = 10 - (tổng có trọng số 9 chữ số đầu mod 11); bằng 10 là không hợp lệ."""
    return 10 - sum(w * d for w, d in zip(_WEIGHTS, first9, strict=True)) % 11


def is_valid_tax_code(raw: str) -> bool:
    """Kiểm tra định dạng và chữ số kiểm tra (chữ số thứ 10).

    Bước tra cứu trạng thái hoạt động trên cổng của Tổng cục Thuế cần tích hợp riêng.
    """
    match = _TAX_CODE_RE.match(normalize_tax_code(raw))
    if not match:
        return False
    digits = [int(ch) for ch in match.group(1)]
    check = _check_digit(digits[:9])
    return check != _INVALID_CHECK_DIGIT and check == digits[9]


def make_valid_tax_code(prefix9: str) -> str | None:
    """Sinh mã hợp lệ từ 9 chữ số đầu (dùng cho dữ liệu mẫu và kiểm thử)."""
    check = _check_digit([int(ch) for ch in prefix9])
    return None if check == _INVALID_CHECK_DIGIT else prefix9 + str(check)
