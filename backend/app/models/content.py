"""Contenido educativo: categorías, lecturas, actividades, preguntas y opciones."""

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin
from app.models.enums import (
    ActivityType,
    ComprehensionLevel,
    QuestionType,
    ReadingLength,
    Skill,
    str_enum,
)


class Category(TimestampMixin, Base):
    """Temática de las lecturas (animales, familia, naturaleza...)."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True)
    description: Mapped[str | None] = mapped_column(String(255))
    icon: Mapped[str | None] = mapped_column(String(16))


class Reading(TimestampMixin, Base):
    __tablename__ = "readings"
    __table_args__ = (
        CheckConstraint("difficulty BETWEEN 1 AND 3", name="difficulty_range"),
        CheckConstraint("min_age <= max_age", name="age_order"),
        CheckConstraint("min_age BETWEEN 4 AND 12 AND max_age BETWEEN 4 AND 12", name="age_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(140), unique=True)
    summary: Mapped[str] = mapped_column(String(300))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), index=True)
    difficulty: Mapped[int] = mapped_column(SmallInteger)
    min_age: Mapped[int] = mapped_column(SmallInteger, default=6)
    max_age: Mapped[int] = mapped_column(SmallInteger, default=7)
    length: Mapped[ReadingLength] = mapped_column(str_enum(ReadingLength, "reading_length"))
    comprehension_focus: Mapped[ComprehensionLevel] = mapped_column(
        str_enum(ComprehensionLevel, "comprehension_level")
    )
    cover_emoji: Mapped[str] = mapped_column(String(16), default="📖")
    cover_color: Mapped[str] = mapped_column(String(9), default="#FFD166")
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", index=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    category: Mapped[Category] = relationship(lazy="joined")
    paragraphs: Mapped[list["ReadingParagraph"]] = relationship(
        back_populates="reading", cascade="all, delete-orphan", order_by="ReadingParagraph.position"
    )
    activities: Mapped[list["Activity"]] = relationship(back_populates="reading")

    @property
    def word_count(self) -> int:
        return sum(len(p.text.split()) for p in self.paragraphs)


class ReadingParagraph(Base):
    __tablename__ = "reading_paragraphs"
    __table_args__ = (UniqueConstraint("reading_id", "position", name="uq_paragraph_position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    reading_id: Mapped[int] = mapped_column(ForeignKey("readings.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(SmallInteger)
    text: Mapped[str] = mapped_column(Text)
    illustration: Mapped[str | None] = mapped_column(String(32))  # emoji o clave de ilustración
    image_url: Mapped[str | None] = mapped_column(String(500))

    reading: Mapped[Reading] = relationship(back_populates="paragraphs")


class Activity(TimestampMixin, Base):
    __tablename__ = "activities"
    __table_args__ = (
        CheckConstraint("difficulty BETWEEN 1 AND 3", name="difficulty_range"),
        CheckConstraint("points_reward BETWEEN 1 AND 100", name="points_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(140), unique=True)
    activity_type: Mapped[ActivityType] = mapped_column(str_enum(ActivityType, "activity_type"), index=True)
    skill: Mapped[Skill] = mapped_column(str_enum(Skill, "skill"), index=True)
    difficulty: Mapped[int] = mapped_column(SmallInteger)
    instructions: Mapped[str] = mapped_column(String(400))
    icon: Mapped[str] = mapped_column(String(16), default="⭐")
    points_reward: Mapped[int] = mapped_column(Integer, default=10)
    reading_id: Mapped[int | None] = mapped_column(ForeignKey("readings.id", ondelete="SET NULL"), index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", index=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    reading: Mapped[Reading | None] = relationship(back_populates="activities")
    questions: Mapped[list["Question"]] = relationship(
        back_populates="activity", cascade="all, delete-orphan", order_by="Question.position"
    )


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (UniqueConstraint("activity_id", "position", name="uq_question_position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(SmallInteger)
    prompt: Mapped[str] = mapped_column(String(400))
    prompt_illustration: Mapped[str | None] = mapped_column(String(32))
    question_type: Mapped[QuestionType] = mapped_column(str_enum(QuestionType, "question_type"))
    skill: Mapped[Skill] = mapped_column(str_enum(Skill, "skill"), index=True)
    hint: Mapped[str | None] = mapped_column(String(300))
    explanation: Mapped[str] = mapped_column(String(400))

    activity: Mapped[Activity] = relationship(back_populates="questions")
    options: Mapped[list["AnswerOption"]] = relationship(
        back_populates="question", cascade="all, delete-orphan", order_by="AnswerOption.position"
    )


class AnswerOption(Base):
    __tablename__ = "answer_options"
    __table_args__ = (
        UniqueConstraint("question_id", "position", name="uq_option_position"),
        CheckConstraint("correct_position IS NULL OR correct_position >= 1", name="correct_position_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(SmallInteger)
    text: Mapped[str] = mapped_column(String(200))
    illustration: Mapped[str | None] = mapped_column(String(32))
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    # Solo para preguntas de ordenamiento: posición correcta (1..n).
    correct_position: Mapped[int | None] = mapped_column(SmallInteger)

    question: Mapped[Question] = relationship(back_populates="options")
