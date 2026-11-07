"""Consultas de aprendizaje y agregados de progreso (todo calculado en PostgreSQL)."""

from datetime import datetime

from sqlalchemy import case, distinct, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Activity,
    Attempt,
    AttemptAnswer,
    Badge,
    Challenge,
    Level,
    PointTransaction,
    Question,
    ReadingSession,
    Reward,
    StudentBadge,
    StudentChallenge,
)
from app.models.enums import AttemptStatus, Skill
from app.repositories.base import BaseRepository


class ReadingSessionRepository(BaseRepository[ReadingSession]):
    model = ReadingSession

    def completed_reading_ids(self, student_id: int) -> set[int]:
        stmt = select(distinct(ReadingSession.reading_id)).where(
            ReadingSession.student_id == student_id, ReadingSession.completed_at.is_not(None)
        )
        return set(self.db.scalars(stmt))

    def completed_count(self, student_id: int, since: datetime | None = None) -> int:
        stmt = select(func.count(distinct(ReadingSession.reading_id))).where(
            ReadingSession.student_id == student_id, ReadingSession.completed_at.is_not(None)
        )
        if since:
            stmt = stmt.where(ReadingSession.completed_at >= since)
        return self.db.scalar(stmt) or 0

    def has_completed(self, student_id: int, reading_id: int) -> bool:
        return reading_id in self.completed_reading_ids(student_id)

    def history(self, student_id: int, limit: int = 50) -> list[ReadingSession]:
        stmt = (
            select(ReadingSession)
            .options(selectinload(ReadingSession.reading))
            .where(ReadingSession.student_id == student_id, ReadingSession.completed_at.is_not(None))
            .order_by(ReadingSession.completed_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def total_completed(self) -> int:
        return self.db.scalar(select(func.count(ReadingSession.id)).where(ReadingSession.completed_at.is_not(None))) or 0


class AttemptRepository(BaseRepository[Attempt]):
    model = Attempt

    def get_with_answers(self, attempt_id: int) -> Attempt | None:
        return self.db.scalar(
            select(Attempt)
            .where(Attempt.id == attempt_id)
            .options(selectinload(Attempt.answers), selectinload(Attempt.activity))
        )

    def next_attempt_number(self, student_id: int, activity_id: int) -> int:
        current = self.db.scalar(
            select(func.max(Attempt.attempt_number)).where(
                Attempt.student_id == student_id, Attempt.activity_id == activity_id
            )
        )
        return (current or 0) + 1

    def best_points_before(self, student_id: int, activity_id: int, exclude_attempt_id: int) -> int:
        """Puntos ya obtenidos en esta actividad (para premiar solo la mejora)."""
        return (
            self.db.scalar(
                select(func.coalesce(func.sum(Attempt.points_awarded), 0)).where(
                    Attempt.student_id == student_id,
                    Attempt.activity_id == activity_id,
                    Attempt.id != exclude_attempt_id,
                )
            )
            or 0
        )

    def best_scores(self, student_id: int) -> dict[int, float]:
        rows = self.db.execute(
            select(Attempt.activity_id, func.max(Attempt.score))
            .where(Attempt.student_id == student_id, Attempt.status == AttemptStatus.COMPLETED)
            .group_by(Attempt.activity_id)
        ).all()
        return {aid: float(score) for aid, score in rows if score is not None}

    def completed_activity_count(self, student_id: int, since: datetime | None = None) -> int:
        stmt = select(func.count(distinct(Attempt.activity_id))).where(
            Attempt.student_id == student_id, Attempt.status == AttemptStatus.COMPLETED
        )
        if since:
            stmt = stmt.where(Attempt.completed_at >= since)
        return self.db.scalar(stmt) or 0

    def perfect_count(self, student_id: int, since: datetime | None = None) -> int:
        stmt = select(func.count(distinct(Attempt.activity_id))).where(
            Attempt.student_id == student_id, Attempt.status == AttemptStatus.COMPLETED, Attempt.score == 100
        )
        if since:
            stmt = stmt.where(Attempt.completed_at >= since)
        return self.db.scalar(stmt) or 0

    def completed_attempts(self, student_id: int) -> int:
        return (
            self.db.scalar(
                select(func.count(Attempt.id)).where(
                    Attempt.student_id == student_id, Attempt.status == AttemptStatus.COMPLETED
                )
            )
            or 0
        )

    def average_score(self, student_ids: list[int] | None = None) -> float | None:
        stmt = select(func.avg(Attempt.score)).where(Attempt.status == AttemptStatus.COMPLETED)
        if student_ids is not None:
            if not student_ids:
                return None
            stmt = stmt.where(Attempt.student_id.in_(student_ids))
        value = self.db.scalar(stmt)
        return round(float(value), 1) if value is not None else None

    def history(self, student_id: int, limit: int = 50) -> list[tuple[Attempt, int]]:
        tries = (
            select(AttemptAnswer.attempt_id, func.count(AttemptAnswer.id).label("tries"))
            .group_by(AttemptAnswer.attempt_id)
            .subquery()
        )
        stmt = (
            select(Attempt, func.coalesce(tries.c.tries, 0))
            .options(selectinload(Attempt.activity))
            .outerjoin(tries, tries.c.attempt_id == Attempt.id)
            .where(Attempt.student_id == student_id)
            .order_by(Attempt.started_at.desc())
            .limit(limit)
        )
        return [(a, int(t)) for a, t in self.db.execute(stmt).all()]

    def answer_totals(self, student_id: int) -> tuple[int, int]:
        row = self.db.execute(
            select(
                func.count(AttemptAnswer.id),
                func.coalesce(func.sum(case((AttemptAnswer.is_correct, 1), else_=0)), 0),
            )
            .join(Attempt, Attempt.id == AttemptAnswer.attempt_id)
            .where(Attempt.student_id == student_id)
        ).one()
        return int(row[0]), int(row[1])

    def skill_stats(self, student_ids: list[int] | None) -> dict[Skill, tuple[int, int]]:
        """Por habilidad: (preguntas respondidas al primer intento, correctas al primer intento)."""
        stmt = (
            select(
                Question.skill,
                func.count(AttemptAnswer.id),
                func.coalesce(func.sum(case((AttemptAnswer.is_correct, 1), else_=0)), 0),
            )
            .join(Question, Question.id == AttemptAnswer.question_id)
            .join(Attempt, Attempt.id == AttemptAnswer.attempt_id)
            .where(AttemptAnswer.try_number == 1)
            .group_by(Question.skill)
        )
        if student_ids is not None:
            if not student_ids:
                return {}
            stmt = stmt.where(Attempt.student_id.in_(student_ids))
        return {skill: (int(total), int(correct)) for skill, total, correct in self.db.execute(stmt).all()}

    def skill_correct_count(self, student_id: int, skill: Skill, since: datetime | None = None) -> int:
        stmt = (
            select(func.count(AttemptAnswer.id))
            .join(Question, Question.id == AttemptAnswer.question_id)
            .join(Attempt, Attempt.id == AttemptAnswer.attempt_id)
            .where(Attempt.student_id == student_id, Question.skill == skill, AttemptAnswer.is_correct.is_(True))
        )
        if since:
            stmt = stmt.where(AttemptAnswer.answered_at >= since)
        return self.db.scalar(stmt) or 0

    def last_activity_at(self, student_id: int) -> datetime | None:
        a = self.db.scalar(select(func.max(Attempt.started_at)).where(Attempt.student_id == student_id))
        r = self.db.scalar(select(func.max(ReadingSession.started_at)).where(ReadingSession.student_id == student_id))
        values = [v for v in (a, r) if v is not None]
        return max(values) if values else None

    def active_students_since(self, since: datetime) -> int:
        a = select(Attempt.student_id).where(Attempt.started_at >= since)
        r = select(ReadingSession.student_id).where(ReadingSession.started_at >= since)
        return self.db.scalar(select(func.count()).select_from(a.union(r).subquery())) or 0

    def total_completed(self) -> int:
        return self.db.scalar(select(func.count(Attempt.id)).where(Attempt.status == AttemptStatus.COMPLETED)) or 0


class GamificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Puntos ---
    def total_points(self, student_id: int) -> int:
        return self.db.scalar(
            select(func.coalesce(func.sum(PointTransaction.amount), 0)).where(PointTransaction.student_id == student_id)
        ) or 0

    def add_points(self, tx: PointTransaction) -> None:
        self.db.add(tx)
        self.db.flush()

    def daily_points(self, student_id: int, since: datetime) -> dict[str, int]:
        day = func.date(PointTransaction.created_at)
        rows = self.db.execute(
            select(day, func.sum(PointTransaction.amount))
            .where(PointTransaction.student_id == student_id, PointTransaction.created_at >= since)
            .group_by(day)
        ).all()
        return {str(d): int(p) for d, p in rows}

    def recent_transactions(self, student_id: int, limit: int = 20) -> list[PointTransaction]:
        return list(
            self.db.scalars(
                select(PointTransaction)
                .where(PointTransaction.student_id == student_id)
                .order_by(PointTransaction.created_at.desc(), PointTransaction.id.desc())
                .limit(limit)
            )
        )

    # --- Niveles ---
    def levels(self) -> list[Level]:
        return list(self.db.scalars(select(Level).order_by(Level.min_points)))

    # --- Insignias ---
    def active_badges(self) -> list[Badge]:
        return list(self.db.scalars(select(Badge).where(Badge.is_active.is_(True)).order_by(Badge.criteria_value)))

    def all_badges(self) -> list[Badge]:
        return list(self.db.scalars(select(Badge).order_by(Badge.id)))

    def student_badges(self, student_id: int) -> list[StudentBadge]:
        return list(
            self.db.scalars(
                select(StudentBadge).where(StudentBadge.student_id == student_id).order_by(StudentBadge.awarded_at.desc())
            )
        )

    def award_badge(self, student_id: int, badge_id: int) -> None:
        self.db.add(StudentBadge(student_id=student_id, badge_id=badge_id))
        self.db.flush()

    # --- Retos ---
    def active_challenges(self) -> list[Challenge]:
        return list(self.db.scalars(select(Challenge).where(Challenge.is_active.is_(True)).order_by(Challenge.id)))

    def all_challenges(self) -> list[Challenge]:
        return list(self.db.scalars(select(Challenge).order_by(Challenge.id)))

    def completed_challenges(self, student_id: int) -> dict[int, StudentChallenge]:
        rows = self.db.scalars(select(StudentChallenge).where(StudentChallenge.student_id == student_id))
        return {r.challenge_id: r for r in rows}

    def complete_challenge(self, student_id: int, challenge_id: int) -> None:
        self.db.add(StudentChallenge(student_id=student_id, challenge_id=challenge_id))
        self.db.flush()

    # --- Recompensas ---
    def rewards(self) -> list[Reward]:
        return list(self.db.scalars(select(Reward).order_by(Reward.required_level, Reward.id)))

    def reward_by_code(self, code: str) -> Reward | None:
        return self.db.scalar(select(Reward).where(Reward.code == code))


__all__ = ["Activity", "AttemptRepository", "GamificationRepository", "ReadingSessionRepository"]
