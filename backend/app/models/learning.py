"""Registro del aprendizaje: sesiones de lectura, intentos y respuestas."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.content import Activity, Question, Reading
from app.models.enums import AttemptStatus, str_enum


class ReadingSession(Base):
    """Cada vez que un estudiante abre y termina una lectura."""

    __tablename__ = "reading_sessions"
    __table_args__ = (Index("ix_reading_sessions_student_reading", "student_id", "reading_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id", ondelete="CASCADE"))
    reading_id: Mapped[int] = mapped_column(ForeignKey("readings.id", ondelete="CASCADE"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    points_awarded: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    reading: Mapped[Reading] = relationship()


class Attempt(Base):
    """Intento de un estudiante sobre una actividad (resultado agregado)."""

    __tablename__ = "attempts"
    __table_args__ = (
        Index("ix_attempts_student_activity", "student_id", "activity_id"),
        CheckConstraint("score IS NULL OR (score BETWEEN 0 AND 100)", name="score_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id", ondelete="CASCADE"))
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id", ondelete="CASCADE"))
    attempt_number: Mapped[int] = mapped_column(SmallInteger)
    status: Mapped[AttemptStatus] = mapped_column(
        str_enum(AttemptStatus, "attempt_status"), default=AttemptStatus.IN_PROGRESS
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_questions: Mapped[int] = mapped_column(SmallInteger)
    correct_first_try: Mapped[int | None] = mapped_column(SmallInteger)
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    points_awarded: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    activity: Mapped[Activity] = relationship()
    answers: Mapped[list["AttemptAnswer"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan", order_by="AttemptAnswer.id"
    )


class AttemptAnswer(Base):
    """Cada respuesta enviada (incluye reintentos de la misma pregunta)."""

    __tablename__ = "attempt_answers"
    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", "try_number", name="uq_answer_try"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    try_number: Mapped[int] = mapped_column(SmallInteger)
    selected_option_id: Mapped[int | None] = mapped_column(ForeignKey("answer_options.id", ondelete="SET NULL"))
    ordered_option_ids: Mapped[list[int] | None] = mapped_column(ARRAY(Integer))
    is_correct: Mapped[bool] = mapped_column(Boolean)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    attempt: Mapped[Attempt] = relationship(back_populates="answers")
    question: Mapped[Question] = relationship()
