"""Estadísticas para administradores y docentes, y panel del estudiante."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import StudentProfile, User
from app.repositories.content_repository import ActivityRepository, ReadingRepository
from app.repositories.learning_repository import AttemptRepository, ReadingSessionRepository
from app.repositories.user_repository import StudentRepository, UserRepository
from app.schemas.gamification import BadgeBrief
from app.schemas.learning import ClassroomStats, ClassroomStudentRow, OverviewStats, StudentDashboard
from app.services.gamification_service import GamificationService
from app.services.progress_service import ProgressService, skill_rows
from app.services.student_service import ClassroomService
from app.services.utils import SKILL_LABELS


class StatsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.students = StudentRepository(db)
        self.attempts = AttemptRepository(db)
        self.sessions = ReadingSessionRepository(db)
        self.readings = ReadingRepository(db)
        self.activities = ActivityRepository(db)
        self.gamification = GamificationService(db)
        self.progress = ProgressService(db)

    def overview(self) -> OverviewStats:
        return OverviewStats(
            users_by_role=self.users.count_by_role(),
            active_students_7d=self.attempts.active_students_since(datetime.now(UTC) - timedelta(days=7)),
            readings_published=self.readings.count_published(),
            activities_published=self.activities.count_published(),
            reading_sessions_completed=self.sessions.total_completed(),
            attempts_completed=self.attempts.total_completed(),
            average_score=self.attempts.average_score(None),
            skills=skill_rows(self.attempts.skill_stats(None)),
            ai_companion_enabled=get_settings().AI_COMPANION_ENABLED,
        )

    def classroom(self, actor: User, classroom_id: int) -> ClassroomStats:
        classroom = ClassroomService(self.db).get_owned(actor, classroom_id)
        students = self.students.list_for_classroom(classroom.id)
        ids = [s.id for s in students]
        rows = []
        for s in students:
            stats = skill_rows(self.attempts.skill_stats([s.id]))
            points = self.gamification.total_points(s.id)
            level, _ = self.gamification.level_for(points)
            rows.append(ClassroomStudentRow(
                student_id=s.id, display_name=s.display_name, avatar=s.avatar, total_points=points,
                level_number=level.number, readings_completed=self.sessions.completed_count(s.id),
                activities_completed=self.attempts.completed_activity_count(s.id),
                average_score=self.attempts.average_score([s.id]),
                needs_support=[x.label for x in stats if x.status == "needs_support"],
                last_activity_at=self.attempts.last_activity_at(s.id),
            ))
        return ClassroomStats(
            classroom_id=classroom.id, classroom_name=classroom.name, student_count=len(students),
            average_score=self.attempts.average_score(ids), skills=skill_rows(self.attempts.skill_stats(ids)),
            students=rows,
        )

    def student_dashboard(self, student: StudentProfile) -> StudentDashboard:
        summary = self.progress.summary(student)
        done = self.sessions.completed_reading_ids(student.id)
        stmt = self.readings.search_stmt(published_only=True)
        pending = [r for r in self.db.scalars(stmt).unique() if r.id not in done][:3]
        challenges = [c for c in self.gamification.challenges_for(student.id) if not c.completed][:3]
        recent = self.gamification.repo.student_badges(student.id)[:4]
        hour = datetime.now().hour
        greeting = "¡Buenos días" if hour < 12 else "¡Buenas tardes" if hour < 19 else "¡Buenas noches"
        return StudentDashboard(
            greeting=f"{greeting}, {student.display_name}!",
            progress=summary,
            continue_reading=[
                {"id": r.id, "title": r.title, "cover_emoji": r.cover_emoji, "cover_color": r.cover_color, "difficulty": r.difficulty}
                for r in pending
            ],
            suggested_activities=[
                {"id": r.activity_id, "title": r.title, "icon": r.icon, "reason": r.reason, "skill_label": SKILL_LABELS[r.skill]}
                for r in summary.recommendations
            ],
            active_challenges=[
                {"id": c.challenge.id, "title": c.challenge.title, "icon": c.challenge.icon,
                 "progress": c.progress, "target": c.challenge.target, "points_reward": c.challenge.points_reward}
                for c in challenges
            ],
            recent_badges=[BadgeBrief.model_validate(sb.badge) for sb in recent],
        )
