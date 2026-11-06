"""Trích kỹ năng từ văn bản dựa trên từ điển kỹ năng (tên chuẩn + từ đồng nghĩa/viết tắt)."""

import re
import unicodedata
from dataclasses import dataclass, field

from ai.text_utils import normalize_text

# Ký tự được coi là một phần của "từ" khi xác định ranh giới (để 'c++' không khớp trong 'c++11')
_WORD_CHARS = r"a-z0-9+#"
MIN_ALIAS_LENGTH = 2

# Cụm từ trông giống alias kỹ năng nhưng mang nghĩa khác, phải loại trước khi bỏ dấu:
# 'khoa học máy tính' không phải 'học máy'; 'học sau đại học' không phải 'học sâu'.
_FALSE_FRIENDS_RE = re.compile(r"học máy tính|hoc may tinh|học sau")


def _remove_false_friends(text: str) -> str:
    return _FALSE_FRIENDS_RE.sub(" ", unicodedata.normalize("NFC", text).lower())


@dataclass(frozen=True)
class SkillEntry:
    skill_id: int
    name: str
    category: str = "Khác"
    aliases: tuple[str, ...] = ()


@dataclass
class ExtractedSkill:
    skill_id: int
    name: str
    category: str
    mentions: int
    matched_terms: list[str] = field(default_factory=list)


class SkillDictionary:
    """Biên dịch từ điển thành các regex có ranh giới từ, ưu tiên cụm dài trước."""

    def __init__(self, entries: list[SkillEntry]) -> None:
        self.entries: dict[int, SkillEntry] = {entry.skill_id: entry for entry in entries}
        self._patterns: list[tuple[re.Pattern[str], int, str]] = []
        self._term_to_skill: dict[str, int] = {}
        for entry in entries:
            for term in (entry.name, *entry.aliases):
                normalized = normalize_text(term)
                if len(normalized) < MIN_ALIAS_LENGTH or normalized in self._term_to_skill:
                    continue
                self._term_to_skill[normalized] = entry.skill_id
        for term in sorted(self._term_to_skill, key=len, reverse=True):
            pattern = re.compile(rf"(?<![{_WORD_CHARS}.]){re.escape(term)}(?![{_WORD_CHARS}])")
            self._patterns.append((pattern, self._term_to_skill[term], term))

    def lookup(self, term: str) -> SkillEntry | None:
        skill_id = self._term_to_skill.get(normalize_text(term))
        return self.entries.get(skill_id) if skill_id is not None else None

    def extract(self, text: str | None) -> list[ExtractedSkill]:
        if not text:
            return []
        normalized = normalize_text(_remove_false_friends(text))
        if not normalized:
            return []
        found: dict[int, ExtractedSkill] = {}
        # Che phần đã khớp để 'react native' không bị đếm thêm lần nữa thành 'react'
        masked = normalized
        for pattern, skill_id, term in self._patterns:
            matches = list(pattern.finditer(masked))
            if not matches:
                continue
            entry = self.entries[skill_id]
            item = found.setdefault(
                skill_id, ExtractedSkill(skill_id, entry.name, entry.category, 0)
            )
            item.mentions += len(matches)
            item.matched_terms.append(term)
            masked = pattern.sub(lambda m: " " * len(m.group(0)), masked)
        return sorted(found.values(), key=lambda s: (-s.mentions, s.name))

    def extract_ids(self, text: str | None) -> set[int]:
        return {skill.skill_id for skill in self.extract(text)}
