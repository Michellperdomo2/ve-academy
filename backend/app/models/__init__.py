"""Importa todos los modelos para que Alembic y SQLAlchemy los registren."""

from app.models.content import Activity, AnswerOption, Category, Question, Reading, ReadingParagraph
from app.models.gamification import (
    Badge,
    Challenge,
    Level,
    PointTransaction,
    Reward,
    StudentBadge,
    StudentChallenge,
)
from app.models.learning import Attempt, AttemptAnswer, ReadingSession
from app.models.user import (
    Classroom,
    GuardianStudent,
    PasswordResetToken,
    RevokedToken,
    Role,
    StudentLinkCode,
    StudentProfile,
    User,
)

__all__ = [
    "Activity",
    "AnswerOption",
    "Attempt",
    "AttemptAnswer",
    "Badge",
    "Category",
    "Challenge",
    "Classroom",
    "GuardianStudent",
    "Level",
    "PasswordResetToken",
    "PointTransaction",
    "Question",
    "Reading",
    "ReadingParagraph",
    "ReadingSession",
    "RevokedToken",
    "Reward",
    "Role",
    "StudentBadge",
    "StudentChallenge",
    "StudentLinkCode",
    "StudentProfile",
    "User",
]
