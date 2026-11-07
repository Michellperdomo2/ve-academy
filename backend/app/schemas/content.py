"""Esquemas de categorías, lecturas, actividades y preguntas."""

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.enums import ActivityType, ComprehensionLevel, QuestionType, ReadingLength, Skill
from app.schemas.common import ORMModel


# ---------- Categorías ----------
class CategoryBase(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    description: str | None = Field(default=None, max_length=255)
    icon: str | None = Field(default=None, max_length=16)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=60)
    description: str | None = Field(default=None, max_length=255)
    icon: str | None = Field(default=None, max_length=16)


class CategoryRead(ORMModel):
    id: int
    name: str
    slug: str
    description: str | None
    icon: str | None


# ---------- Lecturas ----------
class ParagraphIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    illustration: str | None = Field(default=None, max_length=32)
    image_url: str | None = Field(default=None, max_length=500)


class ParagraphRead(ORMModel):
    id: int
    position: int
    text: str
    illustration: str | None
    image_url: str | None


class ReadingWrite(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    summary: str = Field(min_length=2, max_length=300)
    category_id: int
    difficulty: int = Field(ge=1, le=3)
    min_age: int = Field(default=6, ge=4, le=12)
    max_age: int = Field(default=7, ge=4, le=12)
    comprehension_focus: ComprehensionLevel
    cover_emoji: str = Field(default="📖", max_length=16)
    cover_color: str = Field(default="#FFD166", pattern=r"^#[0-9A-Fa-f]{6}$")
    is_published: bool = True
    paragraphs: list[ParagraphIn] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def _ages(self) -> "ReadingWrite":
        if self.min_age > self.max_age:
            raise ValueError("La edad mínima no puede ser mayor que la máxima.")
        return self


class ReadingSummary(ORMModel):
    id: int
    title: str
    slug: str
    summary: str
    category: CategoryRead
    difficulty: int
    min_age: int
    max_age: int
    length: ReadingLength
    comprehension_focus: ComprehensionLevel
    cover_emoji: str
    cover_color: str
    is_published: bool
    word_count: int
    completed_by_me: bool | None = None


class ReadingDetail(ReadingSummary):
    paragraphs: list[ParagraphRead]
    activity_ids: list[int]
    created_at: datetime
    updated_at: datetime


class ReadingSessionRead(ORMModel):
    id: int
    reading_id: int
    started_at: datetime
    completed_at: datetime | None
    points_awarded: int


class ReadingCompletionResult(BaseModel):
    session: ReadingSessionRead
    points_awarded: int
    first_time: bool
    new_badges: list["BadgeBrief"]
    completed_challenges: list["ChallengeBrief"]
    next_activity_id: int | None


# ---------- Actividades ----------
class OptionWrite(BaseModel):
    text: str = Field(min_length=1, max_length=200)
    illustration: str | None = Field(default=None, max_length=32)
    is_correct: bool = False
    correct_position: int | None = Field(default=None, ge=1)


class QuestionWrite(BaseModel):
    prompt: str = Field(min_length=1, max_length=400)
    prompt_illustration: str | None = Field(default=None, max_length=32)
    question_type: QuestionType = QuestionType.SINGLE_CHOICE
    skill: Skill
    hint: str | None = Field(default=None, max_length=300)
    explanation: str = Field(min_length=1, max_length=400)
    options: list[OptionWrite] = Field(min_length=2, max_length=8)

    @model_validator(mode="after")
    def _validate_options(self) -> "QuestionWrite":
        if self.question_type == QuestionType.SINGLE_CHOICE:
            if sum(o.is_correct for o in self.options) != 1:
                raise ValueError("Una pregunta de selección debe tener exactamente una opción correcta.")
        else:
            positions = sorted(o.correct_position or 0 for o in self.options)
            if positions != list(range(1, len(self.options) + 1)):
                raise ValueError("En ordenamiento, cada opción necesita una posición correcta única de 1 a n.")
        return self


class ActivityWrite(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    activity_type: ActivityType
    skill: Skill
    difficulty: int = Field(ge=1, le=3)
    instructions: str = Field(min_length=2, max_length=400)
    icon: str = Field(default="⭐", max_length=16)
    points_reward: int = Field(default=10, ge=1, le=100)
    reading_id: int | None = None
    is_published: bool = True
    questions: list[QuestionWrite] = Field(min_length=1, max_length=20)


class ActivitySummary(ORMModel):
    id: int
    title: str
    slug: str
    activity_type: ActivityType
    skill: Skill
    difficulty: int
    instructions: str
    icon: str
    points_reward: int
    reading_id: int | None
    is_published: bool
    question_count: int
    best_score: float | None = None


class OptionPublic(BaseModel):
    """Opción sin revelar la respuesta correcta (vista del estudiante)."""

    id: int
    text: str
    illustration: str | None


class OptionAdmin(OptionPublic):
    is_correct: bool
    correct_position: int | None


class QuestionPublic(BaseModel):
    id: int
    position: int
    prompt: str
    prompt_illustration: str | None
    question_type: QuestionType
    skill: Skill
    has_hint: bool
    options: list[OptionPublic]


class QuestionAdmin(BaseModel):
    id: int
    position: int
    prompt: str
    prompt_illustration: str | None
    question_type: QuestionType
    skill: Skill
    hint: str | None
    explanation: str
    options: list[OptionAdmin]


class ActivityDetail(ActivitySummary):
    reading_title: str | None
    questions: list[QuestionPublic]


class ActivityAdminDetail(ActivitySummary):
    reading_title: str | None
    attempt_count: int = 0
    questions: list[QuestionAdmin]


from app.schemas.gamification import BadgeBrief, ChallengeBrief  # noqa: E402

ReadingCompletionResult.model_rebuild()
