"""Aulas y estudiantes (docentes, acudientes y administradores)."""

from fastapi import APIRouter, status

from app.api.deps import AdultUser, DbSession, GuardianUser, StaffUser
from app.schemas.common import Message
from app.schemas.learning import AttemptHistoryItem, ClassroomStats, ProgressSummary, ReadingHistoryItem
from app.schemas.gamification import StudentBadgeRead
from app.schemas.user import (
    ClassroomCreate,
    ClassroomRead,
    ClassroomUpdate,
    LinkCodeResponse,
    LinkStudentRequest,
    StudentCreate,
    StudentPasswordReset,
    StudentRead,
    StudentUpdate,
)
from app.services.gamification_service import GamificationService
from app.services.progress_service import ProgressService
from app.services.stats_service import StatsService
from app.services.student_service import ClassroomService, StudentService

classrooms = APIRouter(prefix="/classrooms", tags=["Aulas"])
students = APIRouter(prefix="/students", tags=["Estudiantes"])


# ---------------- Aulas ----------------
@classrooms.get("", response_model=list[ClassroomRead])
def list_classrooms(user: StaffUser, db: DbSession) -> list[ClassroomRead]:
    return ClassroomService(db).list(user)


@classrooms.post("", response_model=ClassroomRead, status_code=status.HTTP_201_CREATED)
def create_classroom(data: ClassroomCreate, user: StaffUser, db: DbSession) -> ClassroomRead:
    return ClassroomService.to_read(ClassroomService(db).create(user, data))


@classrooms.get("/{classroom_id}", response_model=ClassroomRead)
def get_classroom(classroom_id: int, user: StaffUser, db: DbSession) -> ClassroomRead:
    return ClassroomService.to_read(ClassroomService(db).get_owned(user, classroom_id))


@classrooms.patch("/{classroom_id}", response_model=ClassroomRead)
def update_classroom(classroom_id: int, data: ClassroomUpdate, user: StaffUser, db: DbSession) -> ClassroomRead:
    return ClassroomService.to_read(ClassroomService(db).update(user, classroom_id, data))


@classrooms.delete("/{classroom_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_classroom(classroom_id: int, user: StaffUser, db: DbSession) -> None:
    ClassroomService(db).delete(user, classroom_id)


@classrooms.get("/{classroom_id}/students", response_model=list[StudentRead])
def classroom_students(classroom_id: int, user: StaffUser, db: DbSession) -> list[StudentRead]:
    return StudentService(db).list(user, classroom_id)


@classrooms.get("/{classroom_id}/stats", response_model=ClassroomStats, summary="Estadísticas del aula")
def classroom_stats(classroom_id: int, user: StaffUser, db: DbSession) -> ClassroomStats:
    return StatsService(db).classroom(user, classroom_id)


# ---------------- Estudiantes ----------------
@students.get("", response_model=list[StudentRead], summary="Estudiantes asociados al usuario")
def list_students(user: AdultUser, db: DbSession) -> list[StudentRead]:
    return StudentService(db).list(user)


@students.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED,
               summary="Crear cuenta de estudiante (la crea un adulto responsable)")
def create_student(data: StudentCreate, user: AdultUser, db: DbSession) -> StudentRead:
    svc = StudentService(db)
    return svc.to_read(svc.create(user, data))


@students.post("/link", response_model=StudentRead, summary="Acudiente: vincularse con un código")
def link_student(data: LinkStudentRequest, user: GuardianUser, db: DbSession) -> StudentRead:
    svc = StudentService(db)
    return svc.to_read(svc.redeem_link_code(user, data.code, data.relationship_label))


@students.get("/{student_id}", response_model=StudentRead)
def get_student(student_id: int, user: AdultUser, db: DbSession) -> StudentRead:
    svc = StudentService(db)
    return svc.to_read(svc.get_visible(user, student_id))


@students.patch("/{student_id}", response_model=StudentRead)
def update_student(student_id: int, data: StudentUpdate, user: AdultUser, db: DbSession) -> StudentRead:
    svc = StudentService(db)
    return svc.to_read(svc.update(user, student_id, data))


@students.post("/{student_id}/reset-password", response_model=Message)
def reset_student_password(student_id: int, data: StudentPasswordReset, user: AdultUser, db: DbSession) -> Message:
    StudentService(db).reset_password(user, student_id, data.new_password)
    return Message(message="Contraseña del estudiante actualizada.")


@students.post("/{student_id}/link-code", response_model=LinkCodeResponse,
               summary="Generar código de vinculación para el acudiente (válido 7 días, un solo uso)")
def create_link_code(student_id: int, user: StaffUser, db: DbSession) -> LinkCodeResponse:
    return StudentService(db).create_link_code(user, student_id)


@students.get("/{student_id}/progress", response_model=ProgressSummary, summary="Reporte de progreso")
def student_progress(student_id: int, user: AdultUser, db: DbSession) -> ProgressSummary:
    student = StudentService(db).get_visible(user, student_id)
    return ProgressService(db).summary(student)


@students.get("/{student_id}/attempts", response_model=list[AttemptHistoryItem], summary="Historial de actividades")
def student_attempts(student_id: int, user: AdultUser, db: DbSession) -> list[AttemptHistoryItem]:
    student = StudentService(db).get_visible(user, student_id)
    return ProgressService(db).attempt_history(student.id)


@students.get("/{student_id}/readings", response_model=list[ReadingHistoryItem], summary="Historial de lecturas")
def student_readings(student_id: int, user: AdultUser, db: DbSession) -> list[ReadingHistoryItem]:
    student = StudentService(db).get_visible(user, student_id)
    return ProgressService(db).reading_history(student.id)


@students.get("/{student_id}/badges", response_model=list[StudentBadgeRead])
def student_badges(student_id: int, user: AdultUser, db: DbSession) -> list[StudentBadgeRead]:
    student = StudentService(db).get_visible(user, student_id)
    return GamificationService(db).badges_for(student.id)
