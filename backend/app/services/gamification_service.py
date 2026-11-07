"""Reglas de gamificación.

Reglas de puntos (documentadas en docs/02-modelo-datos.md):
- Primera lectura completa de un cuento: 10 puntos. Relecturas: 2 puntos (la relectura
  fortalece la fluidez, por eso se premia, pero menos).
- Actividad: puntos = recompensa x (% de aciertos al primer intento). En intentos
  posteriores solo se suma la *mejora* respecto al mejor resultado anterior.
- Insignias y retos otorgan un bono fijo una sola vez.

No existen rankings ni comparaciones entre niños: todo el progreso es individual.
"""

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models import Badge, Challenge, Level, PointTransaction, StudentProfile
from app.models.enums import BadgeCriteria, ChallengeType, PointReason, RewardKind
from app.repositories.learning_repository import (
    AttemptRepository,
    GamificationRepository,
    ReadingSessionRepository,
)
from app.schemas.gamification import (
    BadgeRead,
    ChallengeRead,
    RewardRead,
    StudentBadgeRead,
    StudentChallengeRead,
)


@dataclass
class EvaluationOutcome:
    new_badges: list[Badge] = field(default_factory=list)
    completed_challenges: list[Challenge] = field(default_factory=list)


class GamificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = GamificationRepository(db)
        self.attempts = AttemptRepository(db)
        self.sessions = ReadingSessionRepository(db)

    # ---------- Puntos y niveles ----------
    def total_points(self, student_id: int) -> int:
        return self.repo.total_points(student_id)

    def award_points(self, student_id: int, amount: int, reason: PointReason, description: str, **refs: int | None) -> None:
        if amount > 0:
            self.repo.add_points(
                PointTransaction(student_id=student_id, amount=amount, reason=reason, description=description, **refs)
            )

    def level_for(self, points: int) -> tuple[Level, Level | None]:
        levels = self.repo.levels()
        current = levels[0]
        nxt: Level | None = None
        for lvl in levels:
            if points >= lvl.min_points:
                current = lvl
            elif nxt is None:
                nxt = lvl
        return current, nxt

    # ---------- Evaluación de logros ----------
    def _badge_progress(self, student_id: int, badge: Badge) -> int:
        match badge.criteria_type:
            case BadgeCriteria.READINGS_COMPLETED:
                return self.sessions.completed_count(student_id)
            case BadgeCriteria.ACTIVITIES_COMPLETED:
                return self.attempts.completed_activity_count(student_id)
            case BadgeCriteria.PERFECT_SCORES:
                return self.attempts.perfect_count(student_id)
            case BadgeCriteria.TOTAL_POINTS:
                return self.repo.total_points(student_id)
            case BadgeCriteria.SKILL_CORRECT_ANSWERS:
                return self.attempts.skill_correct_count(student_id, badge.criteria_skill) if badge.criteria_skill else 0
        return 0

    def _challenge_progress(self, student_id: int, ch: Challenge) -> int:
        since = ch.created_at
        match ch.challenge_type:
            case ChallengeType.COMPLETE_READINGS:
                return self.sessions.completed_count(student_id, since)
            case ChallengeType.COMPLETE_ACTIVITIES:
                return self.attempts.completed_activity_count(student_id, since)
            case ChallengeType.PERFECT_SCORES:
                return self.attempts.perfect_count(student_id, since)
            case ChallengeType.SKILL_PRACTICE:
                return self.attempts.skill_correct_count(student_id, ch.skill, since) if ch.skill else 0
        return 0

    def evaluate(self, student_id: int) -> EvaluationOutcome:
        """Otorga retos e insignias recién alcanzados (idempotente)."""
        outcome = EvaluationOutcome()
        done = self.repo.completed_challenges(student_id)
        for ch in self.repo.active_challenges():
            if ch.id not in done and self._challenge_progress(student_id, ch) >= ch.target:
                self.repo.complete_challenge(student_id, ch.id)
                self.award_points(student_id, ch.points_reward, PointReason.CHALLENGE_COMPLETED, f"Reto: {ch.title}", challenge_id=ch.id)
                outcome.completed_challenges.append(ch)

        # Dos pasadas: el bono de una insignia puede desbloquear una insignia de puntos.
        for _ in range(2):
            owned = {sb.badge_id for sb in self.repo.student_badges(student_id)}
            for badge in self.repo.active_badges():
                if badge.id not in owned and self._badge_progress(student_id, badge) >= badge.criteria_value:
                    self.repo.award_badge(student_id, badge.id)
                    self.award_points(student_id, badge.points_bonus, PointReason.BADGE_EARNED, f"Insignia: {badge.name}", badge_id=badge.id)
                    outcome.new_badges.append(badge)
                    owned.add(badge.id)
        return outcome

    # ---------- Consultas para el estudiante ----------
    def badges_for(self, student_id: int) -> list[StudentBadgeRead]:
        owned = {sb.badge_id: sb for sb in self.repo.student_badges(student_id)}
        result = []
        for badge in self.repo.active_badges():
            sb = owned.get(badge.id)
            progress = badge.criteria_value if sb else min(self._badge_progress(student_id, badge), badge.criteria_value)
            result.append(
                StudentBadgeRead(
                    badge=BadgeRead.model_validate(badge),
                    earned=sb is not None,
                    awarded_at=sb.awarded_at if sb else None,
                    progress=progress,
                    target=badge.criteria_value,
                )
            )
        return result

    def challenges_for(self, student_id: int) -> list[StudentChallengeRead]:
        done = self.repo.completed_challenges(student_id)
        result = []
        for ch in self.repo.active_challenges():
            sc = done.get(ch.id)
            progress = ch.target if sc else min(self._challenge_progress(student_id, ch), ch.target)
            result.append(
                StudentChallengeRead(
                    challenge=ChallengeRead.model_validate(ch),
                    progress=progress,
                    completed=sc is not None,
                    completed_at=sc.completed_at if sc else None,
                )
            )
        return result

    def rewards_for(self, student: StudentProfile) -> list[RewardRead]:
        level, _ = self.level_for(self.total_points(student.id))
        return [
            RewardRead(
                id=r.id, code=r.code, name=r.name, kind=r.kind, icon=r.icon,
                required_level=r.required_level, unlocked=level.number >= r.required_level,
            )
            for r in self.repo.rewards()
        ]

    def is_avatar_unlocked(self, student: StudentProfile, code: str) -> bool:
        reward = self.repo.reward_by_code(code)
        if not reward or reward.kind != RewardKind.AVATAR:
            return False
        level, _ = self.level_for(self.total_points(student.id))
        return level.number >= reward.required_level
