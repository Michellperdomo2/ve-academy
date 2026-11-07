"""Aulas, estudiantes y control de acceso a la información de menores.

Regla central: un adulto solo ve a los niños con los que tiene relación
(docente -> estudiantes de sus aulas; acudiente -> niños vinculados).
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.core.security import generate_link_code, hash_password, sha256
from app.models import Classroom, StudentLinkCode, StudentProfile, User
from app.models.enums import RoleCode
from app.repositories.user_repository import (
    ClassroomRepository,
    RoleRepository,
    StudentRepository,
    UserRepository,
)
from app.schemas.user import (
    ClassroomCreate,
    ClassroomRead,
    ClassroomUpdate,
    LinkCodeResponse,
    StudentCreate,
    StudentRead,
    StudentUpdate,
)
from app.services.gamification_service import GamificationService

LINK_CODE_DAYS = 7


class ClassroomService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ClassroomRepository(db)

    @staticmethod
    def to_read(c: Classroom) -> ClassroomRead:
        return ClassroomRead(
            id=c.id, name=c.name, grade=c.grade, school_year=c.school_year, institution=c.institution,
            teacher_id=c.teacher_id, teacher_name=c.teacher.full_name, student_count=len(c.students),
        )

    def list(self, actor: User) -> list[ClassroomRead]:
        teacher_id = None if actor.role_code == RoleCode.ADMIN else actor.id
        return [self.to_read(c) for c in self.repo.list_for(teacher_id)]

    def get_owned(self, actor: User, classroom_id: int) -> Classroom:
        c = self.repo.get(classroom_id)
        if not c:
            raise NotFoundError("Aula no encontrada.")
        if actor.role_code != RoleCode.ADMIN and c.teacher_id != actor.id:
            raise PermissionDeniedError("Esta aula pertenece a otro docente.")
        return c

    def create(self, actor: User, data: ClassroomCreate) -> Classroom:
        c = Classroom(teacher_id=actor.id, **data.model_dump())
        self.repo.add(c)
        self.db.commit()
        self.db.refresh(c)
        return c

    def update(self, actor: User, classroom_id: int, data: ClassroomUpdate) -> Classroom:
        c = self.get_owned(actor, classroom_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(c, key, value)
        self.db.commit()
        return c

    def delete(self, actor: User, classroom_id: int) -> None:
        c = self.get_owned(actor, classroom_id)
        if c.students:
            raise ConflictError("El aula tiene estudiantes. Muévelos a otra aula antes de eliminarla.")
        self.repo.delete(c)
        self.db.commit()


class StudentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = StudentRepository(db)
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)
        self.classrooms = ClassroomService(db)
        self.gamification = GamificationService(db)

    # ---------- Control de acceso ----------
    def can_view(self, actor: User, student: StudentProfile) -> bool:
        match actor.role_code:
            case RoleCode.ADMIN:
                return True
            case RoleCode.TEACHER:
                return student.classroom is not None and student.classroom.teacher_id == actor.id
            case RoleCode.GUARDIAN:
                return self.repo.is_guardian_of(actor.id, student.id)
            case RoleCode.STUDENT:
                return student.user_id == actor.id
        return False

    def can_manage(self, actor: User, student: StudentProfile) -> bool:
        return actor.role_code != RoleCode.STUDENT and self.can_view(actor, student)

    def get_visible(self, actor: User, student_id: int) -> StudentProfile:
        student = self.repo.get(student_id)
        if not student or not self.can_view(actor, student):
            # Mismo error para "no existe" y "no autorizado": no se revela la existencia de menores.
            raise NotFoundError("Estudiante no encontrado.")
        return student

    def get_managed(self, actor: User, student_id: int) -> StudentProfile:
        student = self.get_visible(actor, student_id)
        if not self.can_manage(actor, student):
            raise PermissionDeniedError("No puedes modificar este estudiante.")
        return student

    def own_profile(self, actor: User) -> StudentProfile:
        student = self.repo.by_user_id(actor.id)
        if not student:
            raise NotFoundError("Perfil de estudiante no encontrado.")
        return student

    # ---------- Lectura ----------
    def to_read(self, s: StudentProfile) -> StudentRead:
        points = self.gamification.total_points(s.id)
        level, _ = self.gamification.level_for(points)
        return StudentRead(
            id=s.id, user_id=s.user_id, username=s.user.username, display_name=s.display_name, avatar=s.avatar,
            age=s.age, is_active=s.user.is_active, classroom_id=s.classroom_id,
            classroom_name=s.classroom.name if s.classroom else None,
            guardian_names=[g.guardian.full_name for g in s.guardians],
            total_points=points, level_number=level.number, created_at=s.created_at,
        )

    def list(self, actor: User, classroom_id: int | None = None) -> list[StudentRead]:
        if classroom_id is not None:
            if actor.role_code not in (RoleCode.ADMIN, RoleCode.TEACHER):
                raise PermissionDeniedError("Solo docentes y administradores consultan aulas.")
            self.classrooms.get_owned(actor, classroom_id)
            students = self.repo.list_for_classroom(classroom_id)
        elif actor.role_code == RoleCode.ADMIN:
            students = self.repo.list_all()
        elif actor.role_code == RoleCode.TEACHER:
            students = self.repo.list_for_teacher(actor.id)
        elif actor.role_code == RoleCode.GUARDIAN:
            students = self.repo.list_for_guardian(actor.id)
        else:
            raise PermissionDeniedError("No autorizado.")
        return [self.to_read(s) for s in students]

    # ---------- Escritura ----------
    def create(self, actor: User, data: StudentCreate) -> StudentProfile:
        classroom_id = data.classroom_id
        if actor.role_code == RoleCode.TEACHER:
            if classroom_id is None:
                raise ConflictError("Selecciona el aula del estudiante.")
            self.classrooms.get_owned(actor, classroom_id)
        elif actor.role_code == RoleCode.GUARDIAN:
            classroom_id = None  # el acudiente no asigna aulas
        elif actor.role_code == RoleCode.ADMIN and classroom_id is not None:
            self.classrooms.get_owned(actor, classroom_id)

        if self.users.by_username(data.username):
            raise ConflictError("Ese nombre de usuario ya está en uso.")
        role = self.roles.by_code(RoleCode.STUDENT)
        assert role is not None
        user = User(
            username=data.username, email=None, full_name=data.display_name.strip(),
            password_hash=hash_password(data.password), role=role,
        )
        self.users.add(user)
        student = StudentProfile(
            user_id=user.id, display_name=data.display_name.strip(), age=data.age,
            classroom_id=classroom_id, created_by_id=actor.id,
        )
        self.repo.add(student)
        if actor.role_code == RoleCode.GUARDIAN:
            self.repo.link_guardian(actor.id, student.id, data.relationship_label)
        self.db.commit()
        self.db.refresh(student)
        return student

    def update(self, actor: User, student_id: int, data: StudentUpdate) -> StudentProfile:
        student = self.get_managed(actor, student_id)
        fields = data.model_dump(exclude_unset=True)
        if "classroom_id" in fields:
            if actor.role_code == RoleCode.GUARDIAN:
                raise PermissionDeniedError("Solo un docente puede cambiar el aula.")
            if fields["classroom_id"] is not None:
                self.classrooms.get_owned(actor, fields["classroom_id"])
            student.classroom_id = fields["classroom_id"]
        if "display_name" in fields and fields["display_name"]:
            student.display_name = fields["display_name"].strip()
            student.user.full_name = student.display_name
        if "age" in fields:
            student.age = fields["age"]
        if "is_active" in fields and fields["is_active"] is not None:
            student.user.is_active = fields["is_active"]
        self.db.commit()
        self.db.refresh(student)
        return student

    def reset_password(self, actor: User, student_id: int, new_password: str) -> None:
        student = self.get_managed(actor, student_id)
        student.user.password_hash = hash_password(new_password)
        student.user.failed_login_attempts = 0
        student.user.locked_until = None
        self.db.commit()

    def set_avatar(self, actor: User, avatar: str) -> StudentProfile:
        student = self.own_profile(actor)
        if not self.gamification.is_avatar_unlocked(student, avatar):
            raise PermissionDeniedError("Ese avatar todavía está bloqueado. ¡Sigue leyendo para ganarlo!")
        student.avatar = avatar
        self.db.commit()
        return student

    # ---------- Vinculación acudiente ----------
    def create_link_code(self, actor: User, student_id: int) -> LinkCodeResponse:
        student = self.get_managed(actor, student_id)
        code = generate_link_code()
        expires = datetime.now(UTC) + timedelta(days=LINK_CODE_DAYS)
        self.repo.add_link_code(
            StudentLinkCode(student_id=student.id, code_hash=sha256(code), created_by_id=actor.id, expires_at=expires)
        )
        self.db.commit()
        return LinkCodeResponse(code=code, expires_at=expires)

    def redeem_link_code(self, actor: User, code: str, label: str | None) -> StudentProfile:
        record = self.repo.link_code_by_hash(sha256(code.strip().upper()))
        now = datetime.now(UTC)
        if not record or record.used_at or record.expires_at < now:
            raise NotFoundError("El código no es válido o ya expiró.")
        record.used_at = now
        self.repo.link_guardian(actor.id, record.student_id, label)
        self.db.commit()
        student = self.repo.get(record.student_id)
        assert student is not None
        return student
