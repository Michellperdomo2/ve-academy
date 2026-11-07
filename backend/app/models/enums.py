"""Enumeraciones del dominio.

Se guardan como VARCHAR + CHECK (no ENUM nativo de PostgreSQL) para que agregar un
valor nuevo sea una migración simple.
"""

import enum

from sqlalchemy import Enum as SAEnum


def str_enum(enum_cls: type[enum.Enum], name: str) -> SAEnum:
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=40,
        values_callable=lambda e: [m.value for m in e],
        validate_strings=True,
    )


class RoleCode(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    GUARDIAN = "guardian"
    STUDENT = "student"


class ReadingLength(str, enum.Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class ComprehensionLevel(str, enum.Enum):
    LITERAL = "literal"
    INFERENTIAL = "inferential"
    CRITICAL = "critical"


class Skill(str, enum.Enum):
    """Habilidades lectoras que se miden en cada pregunta."""

    PHONOLOGICAL_AWARENESS = "phonological_awareness"  # sílabas, rimas
    WORD_RECOGNITION = "word_recognition"  # reconocimiento de palabras / fluidez
    VOCABULARY = "vocabulary"  # asociación imagen-palabra
    SENTENCE_BUILDING = "sentence_building"  # formación de oraciones
    SEQUENCING = "sequencing"  # ordenar secuencias
    LITERAL = "literal"  # comprensión literal
    INFERENTIAL = "inferential"  # comprensión inferencial
    CRITICAL = "critical"  # comprensión crítica


class ActivityType(str, enum.Enum):
    SYLLABLES = "syllables"
    WORD_RECOGNITION = "word_recognition"
    SENTENCE_BUILDING = "sentence_building"
    IMAGE_WORD = "image_word"
    COMPLETE_WORD = "complete_word"
    SEQUENCE_ORDER = "sequence_order"
    RHYMES = "rhymes"
    READING_COMPREHENSION = "reading_comprehension"


class QuestionType(str, enum.Enum):
    SINGLE_CHOICE = "single_choice"
    ORDERING = "ordering"


class AttemptStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class PointReason(str, enum.Enum):
    READING_COMPLETED = "reading_completed"
    ACTIVITY_COMPLETED = "activity_completed"
    BADGE_EARNED = "badge_earned"
    CHALLENGE_COMPLETED = "challenge_completed"


class BadgeCriteria(str, enum.Enum):
    READINGS_COMPLETED = "readings_completed"
    ACTIVITIES_COMPLETED = "activities_completed"
    PERFECT_SCORES = "perfect_scores"
    TOTAL_POINTS = "total_points"
    SKILL_CORRECT_ANSWERS = "skill_correct_answers"


class ChallengeType(str, enum.Enum):
    COMPLETE_READINGS = "complete_readings"
    COMPLETE_ACTIVITIES = "complete_activities"
    PERFECT_SCORES = "perfect_scores"
    SKILL_PRACTICE = "skill_practice"


class RewardKind(str, enum.Enum):
    AVATAR = "avatar"
    STICKER = "sticker"
