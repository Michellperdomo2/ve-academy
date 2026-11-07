"""Endpoints del estudiante autenticado (su propio progreso y gamificación)."""

from fastapi import APIRouter

from app.api.deps import CurrentStudent, CurrentUser, DbSession
from app.schemas.gamification import (
    PointTransactionRead,
    RewardRead,
    StudentBadgeRead,
    StudentChallengeRead,
)
from app.schemas.learning import AttemptHistoryItem, ProgressSummary, ReadingHistoryItem, StudentDashboard
from app.schemas.user import AvatarUpdate, StudentRead
from app.services.gamification_service import GamificationService
from app.services.progress_service import ProgressService
from app.services.stats_service import StatsService
from app.services.student_service import StudentService

router = APIRouter(prefix="/me", tags=["Estudiante"])


@router.get("/dashboard", response_model=StudentDashboard)
def dashboard(student: CurrentStudent, db: DbSession) -> StudentDashboard:
    return StatsService(db).student_dashboard(student)


@router.get("/profile", response_model=StudentRead)
def profile(student: CurrentStudent, db: DbSession) -> StudentRead:
    return StudentService(db).to_read(student)


@router.patch("/avatar", response_model=StudentRead, summary="Escoger avatar (solo avatares desbloqueados)")
def set_avatar(data: AvatarUpdate, user: CurrentUser, _: CurrentStudent, db: DbSession) -> StudentRead:
    svc = StudentService(db)
    return svc.to_read(svc.set_avatar(user, data.avatar))


@router.get("/progress", response_model=ProgressSummary)
def progress(student: CurrentStudent, db: DbSession) -> ProgressSummary:
    return ProgressService(db).summary(student)


@router.get("/attempts", response_model=list[AttemptHistoryItem])
def attempts(student: CurrentStudent, db: DbSession) -> list[AttemptHistoryItem]:
    return ProgressService(db).attempt_history(student.id)


@router.get("/readings", response_model=list[ReadingHistoryItem])
def readings(student: CurrentStudent, db: DbSession) -> list[ReadingHistoryItem]:
    return ProgressService(db).reading_history(student.id)


@router.get("/badges", response_model=list[StudentBadgeRead])
def badges(student: CurrentStudent, db: DbSession) -> list[StudentBadgeRead]:
    return GamificationService(db).badges_for(student.id)


@router.get("/challenges", response_model=list[StudentChallengeRead])
def challenges(student: CurrentStudent, db: DbSession) -> list[StudentChallengeRead]:
    return GamificationService(db).challenges_for(student.id)


@router.get("/rewards", response_model=list[RewardRead])
def rewards(student: CurrentStudent, db: DbSession) -> list[RewardRead]:
    return GamificationService(db).rewards_for(student)


@router.get("/points", response_model=list[PointTransactionRead], summary="Últimos puntos ganados")
def points(student: CurrentStudent, db: DbSession) -> list[PointTransactionRead]:
    return [PointTransactionRead.model_validate(t) for t in GamificationService(db).repo.recent_transactions(student.id)]
