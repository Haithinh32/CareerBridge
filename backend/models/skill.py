from sqlmodel import Field

from models.base import TimestampedModel


class Skill(TimestampedModel, table=True):
    """Kỹ năng chuẩn trong từ điển."""

    __tablename__ = "skills"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=120)
    category: str = Field(default="Khác", max_length=120, index=True)


class SkillAlias(TimestampedModel, table=True):
    """Từ đồng nghĩa / viết tắt của kỹ năng, ví dụ 'js' -> JavaScript."""

    __tablename__ = "skill_aliases"

    id: int | None = Field(default=None, primary_key=True)
    skill_id: int = Field(foreign_key="skills.id", index=True)
    alias: str = Field(unique=True, max_length=120)


class Course(TimestampedModel, table=True):
    __tablename__ = "courses"

    id: int | None = Field(default=None, primary_key=True)
    skill_id: int = Field(foreign_key="skills.id", index=True)
    title: str = Field(max_length=255)
    provider: str = Field(max_length=120)
    url: str = Field(max_length=500)
    duration_hours: int | None = Field(default=None)
    is_free: bool = Field(default=False)
