"""Chuẩn hóa văn bản tiếng Việt/tiếng Anh dùng chung cho trích xuất và so khớp."""

import re
import unicodedata

_WHITESPACE_RE = re.compile(r"\s+")
_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+#.]*[a-z0-9+#]|[a-z0-9]")

STOPWORDS: frozenset[str] = frozenset(
    {
        "va", "cua", "cho", "cac", "nhung", "voi", "trong", "duoc", "la", "co", "khong",
        "mot", "nguoi", "tai", "ve", "tu", "den", "nay", "the", "and", "or", "of", "to",
        "in", "for", "with", "on", "at", "a", "an", "is", "are", "be", "as", "by",
        "cong", "viec", "lam", "ung", "vien", "tuyen", "dung",
    }
)


def strip_accents(text: str) -> str:
    """Bỏ dấu tiếng Việt: 'Hồ Chí Minh' -> 'Ho Chi Minh'."""
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def normalize_text(text: str | None) -> str:
    """Viết thường, bỏ dấu, gộp khoảng trắng."""
    if not text:
        return ""
    return _WHITESPACE_RE.sub(" ", strip_accents(text).lower()).strip()


def tokenize(text: str | None, *, drop_stopwords: bool = True) -> list[str]:
    tokens = _TOKEN_RE.findall(normalize_text(text))
    if drop_stopwords:
        return [tok for tok in tokens if tok not in STOPWORDS]
    return tokens


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)
