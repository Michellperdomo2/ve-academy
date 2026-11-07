"""Categorías, lecturas, actividades e intentos."""

from fastapi import APIRouter, Query, status

from app.api.deps import AdminUser, CurrentStudent, CurrentUser, DbSession
from app.models.enums import ActivityType, ComprehensionLevel, ReadingLength, RoleCode, Skill
from app.repositories.learning_repository import AttemptRepository, ReadingSessionRepository
from app.schemas.common import Page
from app.schemas.content import (
    ActivityAdminDetail,
    ActivityDetail,
    ActivitySummary,
    ActivityWrite,
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    ReadingCompletionResult,
    ReadingDetail,
    ReadingSessionRead,
    ReadingSummary,
    ReadingWrite,
)
from app.schemas.learning import AnswerFeedback, AnswerSubmit, AttemptResult, AttemptStart
from app.services.content_service import ActivityService, CategoryService, ReadingService
from app.services.learning_service import LearningService

categories = APIRouter(prefix="/categories", tags=["Categorías"])
readings = APIRouter(prefix="/readings", tags=["Lecturas"])
activities = APIRouter(prefix="/activities", tags=["Actividades"])
attempts = APIRouter(prefix="/attempts", tags=["Intentos y evaluación"])


def _published_only(user, include_unpublished: bool) -> bool:
    return not (include_unpublished and user.role_code == RoleCode.ADMIN)


# ---------------- Categorías ----------------
@categories.get("", response_model=list[CategoryRead])
def list_categories(_: CurrentUser, db: DbSession) -> list[CategoryRead]:
    return [CategoryRead.model_validate(c) for c in CategoryService(db).list()]


@categories.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, _: AdminUser, db: DbSession) -> CategoryRead:
    return CategoryRead.model_validate(CategoryService(db).create(data))


@categories.patch("/{category_id}", response_model=CategoryRead)
def update_category(category_id: int, data: CategoryUpdate, _: AdminUser, db: DbSession) -> CategoryRead:
    return CategoryRead.model_validate(CategoryService(db).update(category_id, data))


@categories.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, _: AdminUser, db: DbSession) -> None:
    CategoryService(db).delete(category_id)


# ---------------- Lecturas ----------------
@readings.get("", response_model=Page[ReadingSummary], summary="Catálogo de lecturas con filtros")
def list_readings(
    user: CurrentUser, db: DbSession,
    category_id: int | None = None, difficulty: int | None = Query(None, ge=1, le=3),
    age: int | None = Query(None, ge=4, le=12), length: ReadingLength | None = None,
    comprehension: ComprehensionLevel | None = None, q: str | None = Query(None, max_length=60),
    include_unpublished: bool = False, page: int = Query(1, ge=1), size: int = Query(24, ge=1, le=100),
) -> Page[ReadingSummary]:
    completed = None
    if user.student_profile:
        completed = ReadingSessionRepository(db).completed_reading_ids(user.student_profile.id)
    return ReadingService(db).search(
        published_only=_published_only(user, include_unpublished), page=page, size=size, completed=completed,
        category_id=category_id, difficulty=difficulty, age=age, length=length, comprehension=comprehension, q=q,
    )


@readings.get("/{reading_id}", response_model=ReadingDetail)
def get_reading(reading_id: int, user: CurrentUser, db: DbSession) -> ReadingDetail:
    published_only = user.role_code != RoleCode.ADMIN
    svc = ReadingService(db)
    completed = ReadingSessionRepository(db).completed_reading_ids(user.student_profile.id) if user.student_profile else None
    return svc.to_detail(svc.get(reading_id, published_only), completed, published_only)


@readings.post("", response_model=ReadingDetail, status_code=status.HTTP_201_CREATED)
def create_reading(data: ReadingWrite, admin: AdminUser, db: DbSession) -> ReadingDetail:
    svc = ReadingService(db)
    return svc.to_detail(svc.create(admin, data), None, False)


@readings.put("/{reading_id}", response_model=ReadingDetail)
def update_reading(reading_id: int, data: ReadingWrite, _: AdminUser, db: DbSession) -> ReadingDetail:
    svc = ReadingService(db)
    return svc.to_detail(svc.update(reading_id, data), None, False)


@readings.delete("/{reading_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reading(reading_id: int, _: AdminUser, db: DbSession) -> None:
    ReadingService(db).delete(reading_id)


@readings.post("/{reading_id}/sessions", response_model=ReadingSessionRead, status_code=status.HTTP_201_CREATED,
               summary="Estudiante: empezar a leer")
def start_reading(reading_id: int, student: CurrentStudent, db: DbSession) -> ReadingSessionRead:
    return ReadingSessionRead.model_validate(LearningService(db).start_reading(student, reading_id))


@readings.post("/sessions/{session_id}/complete", response_model=ReadingCompletionResult,
               summary="Estudiante: terminar la lectura (otorga puntos)")
def complete_reading(session_id: int, student: CurrentStudent, db: DbSession) -> ReadingCompletionResult:
    return LearningService(db).complete_reading(student, session_id)


# ---------------- Actividades ----------------
@activities.get("", response_model=Page[ActivitySummary])
def list_activities(
    user: CurrentUser, db: DbSession,
    activity_type: ActivityType | None = None, skill: Skill | None = None,
    difficulty: int | None = Query(None, ge=1, le=3), reading_id: int | None = None,
    include_unpublished: bool = False, page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=100),
) -> Page[ActivitySummary]:
    best = AttemptRepository(db).best_scores(user.student_profile.id) if user.student_profile else None
    return ActivityService(db).search(
        published_only=_published_only(user, include_unpublished), page=page, size=size, best=best,
        activity_type=activity_type, skill=skill, difficulty=difficulty, reading_id=reading_id,
    )


@activities.get("/{activity_id}", response_model=ActivityDetail,
                summary="Detalle para resolver (no revela respuestas correctas)")
def get_activity(activity_id: int, user: CurrentUser, db: DbSession) -> ActivityDetail:
    svc = ActivityService(db)
    best = AttemptRepository(db).best_scores(user.student_profile.id) if user.student_profile else None
    return svc.to_public(svc.get(activity_id, user.role_code != RoleCode.ADMIN), best)


@activities.get("/{activity_id}/admin", response_model=ActivityAdminDetail, summary="Detalle completo (administrador)")
def get_activity_admin(activity_id: int, _: AdminUser, db: DbSession) -> ActivityAdminDetail:
    svc = ActivityService(db)
    return svc.to_admin(svc.get(activity_id, published_only=False))


@activities.post("", response_model=ActivityAdminDetail, status_code=status.HTTP_201_CREATED)
def create_activity(data: ActivityWrite, admin: AdminUser, db: DbSession) -> ActivityAdminDetail:
    svc = ActivityService(db)
    return svc.to_admin(svc.create(admin, data))


@activities.put("/{activity_id}", response_model=ActivityAdminDetail)
def update_activity(activity_id: int, data: ActivityWrite, _: AdminUser, db: DbSession) -> ActivityAdminDetail:
    svc = ActivityService(db)
    return svc.to_admin(svc.update(activity_id, data))


@activities.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(activity_id: int, _: AdminUser, db: DbSession) -> None:
    ActivityService(db).delete(activity_id)


@activities.post("/{activity_id}/attempts", response_model=AttemptStart, status_code=status.HTTP_201_CREATED,
                 summary="Estudiante: iniciar un intento")
def start_attempt(activity_id: int, student: CurrentStudent, db: DbSession) -> AttemptStart:
    return LearningService(db).start_attempt(student, activity_id)


# ---------------- Intentos ----------------
@attempts.post("/{attempt_id}/answers", response_model=AnswerFeedback,
               summary="Responder una pregunta (retroalimentación inmediata)")
def answer(attempt_id: int, data: AnswerSubmit, student: CurrentStudent, db: DbSession) -> AnswerFeedback:
    return LearningService(db).answer(student, attempt_id, data)


@attempts.post("/{attempt_id}/finish", response_model=AttemptResult, summary="Terminar intento y calificar")
def finish(attempt_id: int, student: CurrentStudent, db: DbSession) -> AttemptResult:
    return LearningService(db).finish(student, attempt_id)
