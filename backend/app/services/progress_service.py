"""Seguimiento del progreso, habilidades y recomendaciones de refuerzo."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Attempt, ReadingSession, StudentProfile
from app.models.enums import AttemptStatus, Skill
from app.repositories.content_repository import ActivityRepository, ReadingRepository
from app.repositories.learning_repository import AttemptRepository, ReadingSessionRepository
from app.schemas.gamification import LevelRead
from app.schemas.learning import (
    AttemptHistoryItem,
    DailyActivity,
    ProgressSummary,
    ReadingHistoryItem,
    Recommendation,
    SkillProgress,
)
from app.services.gamification_service import GamificationService
from app.services.utils import SKILL_LABELS

STRONG_THRESHOLD = 80.0
SUPPORT_THRESHOLD = 60.0
MIN_ANSWERS_FOR_STATUS = 3


def skill_rows(stats: dict[Skill, tuple[int, int]]) -> list[SkillProgress]:
    rows = []
    for skill in Skill:
        answered, correct = stats.get(skill, (0, 0))
        accuracy = round(correct * 100 / answered, 1) if answered else None
        if not answered:
            status = "not_started"
        elif answered >= MIN_ANSWERS_FOR_STATUS and accuracy is not None and accuracy >= STRONG_THRESHOLD:
            status = "strong"
        elif answered >= MIN_ANSWERS_FOR_STATUS and accuracy is not None and accuracy < SUPPORT_THRESHOLD:
            status = "needs_support"
        else:
            status = "developing"
        rows.append(SkillProgress(skill=skill, label=SKILL_LABELS[skill], answered=answered,
                                  correct_first_try=correct, accuracy=accuracy, status=status))
    return rows


class ProgressService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.attempts = AttemptRepository(db)
        self.sessions = ReadingSessionRepository(db)
        self.activities = ActivityRepository(db)
        self.readings = ReadingRepository(db)
        self.gamification = GamificationService(db)

    def recommendations(self, student_id: int, skills: list[SkillProgress], exclude_activity_id: int | None = None,
                        limit: int = 3) -> list[Recommendation]:
        """Prioriza habilidades con necesidad de refuerzo; luego las que están en desarrollo."""
        best = self.attempts.best_scores(student_id)
        ordered = [s for s in skills if s.status == "needs_support"] + [s for s in skills if s.status == "developing"]
        recs: list[Recommendation] = []
        seen: set[int] = set()
        for sp in ordered:
            for act in self.activities.published_by_skill([sp.skill]):
                if act.id in seen or act.id == exclude_activity_id or best.get(act.id, 0) >= STRONG_THRESHOLD:
                    continue
                reason = ("Para reforzar: " if sp.status == "needs_support" else "Para seguir practicando: ") + sp.label.lower()
                recs.append(Recommendation(activity_id=act.id, title=act.title, icon=act.icon, skill=sp.skill, reason=reason))
                seen.add(act.id)
                break
            if len(recs) >= limit:
                return recs
        if len(recs) < limit:  # Nada pendiente de refuerzo: proponer lo siguiente no realizado, variando el tipo.
            candidates = sorted(
                self.db.scalars(self.activities.search_stmt(published_only=True)).unique(),
                key=lambda a: (a.reading_id is not None, a.difficulty, a.id),
            )
            seen_types = {a.activity_type for a in candidates if a.id in seen}
            for act in candidates:
                if act.activity_type in seen_types:
                    continue
                if act.id not in best and act.id not in seen and act.id != exclude_activity_id:
                    seen_types.add(act.activity_type)
                    recs.append(Recommendation(activity_id=act.id, title=act.title, icon=act.icon, skill=act.skill,
                                               reason="¡Una nueva aventura para ti!"))
                    seen.add(act.id)
                if len(recs) >= limit:
                    break
        return recs

    def weekly(self, student_id: int) -> list[DailyActivity]:
        today = datetime.now(UTC).date()
        since = datetime.combine(today - timedelta(days=6), datetime.min.time(), tzinfo=UTC)
        r_day = func.date(ReadingSession.completed_at)
        a_day = func.date(Attempt.completed_at)
        readings = dict(self.db.execute(
            select(r_day, func.count()).where(ReadingSession.student_id == student_id, ReadingSession.completed_at >= since).group_by(r_day)
        ).all())
        acts = dict(self.db.execute(
            select(a_day, func.count()).where(Attempt.student_id == student_id, Attempt.status == AttemptStatus.COMPLETED,
                                              Attempt.completed_at >= since).group_by(a_day)
        ).all())
        points = self.gamification.repo.daily_points(student_id, since)
        days = []
        for i in range(7):
            d = today - timedelta(days=6 - i)
            days.append(DailyActivity(date=d.isoformat(), readings=int(readings.get(d, 0)),
                                      activities=int(acts.get(d, 0)), points=points.get(d.isoformat(), 0)))
        return days

    def summary(self, student: StudentProfile) -> ProgressSummary:
        sid = student.id
        points = self.gamification.total_points(sid)
        level, nxt = self.gamification.level_for(points)
        readings_done = self.sessions.completed_count(sid)
        readings_total = self.readings.count_published()
        acts_done = self.attempts.completed_activity_count(sid)
        acts_total = self.activities.count_published()
        total_items = readings_total + acts_total
        progress = round((readings_done + acts_done) * 100 / total_items, 1) if total_items else 0.0
        answers, correct = self.attempts.answer_totals(sid)
        skills = skill_rows(self.attempts.skill_stats([sid]))
        return ProgressSummary(
            student_id=sid, display_name=student.display_name, avatar=student.avatar,
            total_points=points, level=LevelRead.model_validate(level),
            next_level=LevelRead.model_validate(nxt) if nxt else None,
            points_to_next_level=(nxt.min_points - points) if nxt else None,
            readings_completed=readings_done, readings_total=readings_total,
            activities_completed=acts_done, activities_total=acts_total, progress_percent=min(progress, 100.0),
            total_attempts=self.attempts.completed_attempts(sid), total_answers=answers,
            correct_answers=correct, incorrect_answers=answers - correct,
            average_score=self.attempts.average_score([sid]),
            badges_earned=len(self.gamification.repo.student_badges(sid)),
            skills=skills,
            strengths=[s.label for s in skills if s.status == "strong"],
            needs_support=[s.label for s in skills if s.status == "needs_support"],
            recommendations=self.recommendations(sid, skills),
            weekly_activity=self.weekly(sid),
        )

    def attempt_history(self, student_id: int) -> list[AttemptHistoryItem]:
        return [
            AttemptHistoryItem(
                attempt_id=a.id, activity_id=a.activity_id, activity_title=a.activity.title,
                activity_type=a.activity.activity_type, skill=a.activity.skill, attempt_number=a.attempt_number,
                status=a.status, score=float(a.score) if a.score is not None else None,
                correct_first_try=a.correct_first_try, total_questions=a.total_questions, total_tries=tries,
                points_awarded=a.points_awarded, started_at=a.started_at, completed_at=a.completed_at,
            )
            for a, tries in self.attempts.history(student_id)
        ]

    def reading_history(self, student_id: int) -> list[ReadingHistoryItem]:
        return [
            ReadingHistoryItem(
                session_id=s.id, reading_id=s.reading_id, reading_title=s.reading.title,
                cover_emoji=s.reading.cover_emoji, completed_at=s.completed_at, points_awarded=s.points_awarded,
            )
            for s in self.sessions.history(student_id)
            if s.completed_at is not None
        ]
