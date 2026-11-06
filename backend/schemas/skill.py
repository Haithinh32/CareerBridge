from pydantic import BaseModel, Field


class SkillAliasResponse(BaseModel):
    id: int
    alias: str


class SkillResponse(BaseModel):
    id: int
    name: str
    category: str
    aliases: list[SkillAliasResponse] = []


class SkillListResponse(BaseModel):
    items: list[SkillResponse]
    total: int


class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(default="Khác", max_length=120)
    aliases: list[str] = []


class SkillUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    category: str | None = Field(default=None, max_length=120)


class SkillAliasCreate(BaseModel):
    alias: str = Field(min_length=1, max_length=120)


class SkillRef(BaseModel):
    skill_id: int
    name: str


class CourseResponse(BaseModel):
    id: int
    skill_id: int
    title: str
    provider: str
    url: str
    duration_hours: int | None
    is_free: bool
