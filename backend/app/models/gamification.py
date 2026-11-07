"""Gamificación: puntos, niveles, insignias, logros, retos y recompensas."""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin
from app.models.enums import (
    BadgeCriteria,
    ChallengeType,
    PointReason,
    RewardKind,
    Skill,
    str_enum,
)


class PointTransaction(Base):
    """Libro de puntos. El total del estudiante es la suma de sus transacciones."""

    __tablename__ = "point_transactions"
    __table_args__ = (CheckConstraint("amount > 0", name="amount_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    reason: Mapped[PointReason] = mapped_column(str_enum(PointReason, "point_reason"))
    description: Mapped[str] = mapped_column(String(200))
    attempt_id: Mapped[int | None] = mapped_column(ForeignKey("attempts.id", ondelete="SET NULL"))
    reading_session_id: Mapped[int | None] = mapped_column(ForeignKey("reading_sessions.id", ondelete="SET NULL"))
    badge_id: Mapped[int | None] = mapped_column(ForeignKey("badges.id", ondelete="SET NULL"))
    challenge_id: Mapped[int | None] = mapped_column(ForeignKey("challenges.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class Level(Base):
    __tablename__ = "levels"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column(SmallInteger, unique=True)
    name: Mapped[str] = mapped_column(String(60))
    min_points: Mapped[int] = mapped_column(Integer, unique=True)
    icon: Mapped[str] = mapped_column(String(16))


class Badge(TimestampMixin, Base):
    __tablename__ = "badges"
    __table_args__ = (CheckConstraint("criteria_value > 0", name="criteria_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(String(255))
    icon: Mapped[str] = mapped_column(String(16))
    criteria_type: Mapped[BadgeCriteria] = mapped_column(str_enum(BadgeCriteria, "badge_criteria"))
    criteria_value: Mapped[int] = mapped_column(Integer)
    criteria_skill: Mapped[Skill | None] = mapped_column(str_enum(Skill, "skill"))
    points_bonus: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class StudentBadge(Base):
    """Logros: insignias obtenidas por un estudiante."""

    __tablename__ = "student_badges"

    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id", ondelete="CASCADE"), primary_key=True)
    badge_id: Mapped[int] = mapped_column(ForeignKey("badges.id", ondelete="CASCADE"), primary_key=True)
    awarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    badge: Mapped[Badge] = relationship(lazy="joined")


class Challenge(TimestampMixin, Base):
    """Reto educativo (p. ej. "Lee 3 cuentos esta semana")."""

    __tablename__ = "challenges"
    __table_args__ = (CheckConstraint("target > 0", name="target_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255))
    icon: Mapped[str] = mapped_column(String(16))
    challenge_type: Mapped[ChallengeType] = mapped_column(str_enum(ChallengeType, "challenge_type"))
    target: Mapped[int] = mapped_column(Integer)
    skill: Mapped[Skill | None] = mapped_column(str_enum(Skill, "skill"))
    points_reward: Mapped[int] = mapped_column(Integer, default=10)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class StudentChallenge(Base):
    __tablename__ = "student_challenges"

    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id", ondelete="CASCADE"), primary_key=True)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Reward(Base):
    """Recompensas desbloqueables por nivel (avatares y stickers)."""

    __tablename__ = "rewards"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(60))
    kind: Mapped[RewardKind] = mapped_column(str_enum(RewardKind, "reward_kind"))
    icon: Mapped[str] = mapped_column(String(16))
    required_level: Mapped[int] = mapped_column(SmallInteger, default=1)
