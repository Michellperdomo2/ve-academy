from datetime import UTC, datetime

from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Classroom,
    GuardianStudent,
    PasswordResetToken,
    RevokedToken,
    Role,
    StudentLinkCode,
    StudentProfile,
    User,
)
from app.models.enums import RoleCode
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    model = Role

    def by_code(self, code: RoleCode) -> Role | None:
        return self.db.scalar(select(Role).where(Role.code == code))


class UserRepository(BaseRepository[User]):
    model = User

    def by_login(self, login: str) -> User | None:
        login = login.strip().lower()
        return self.db.scalar(select(User).where(or_(User.username == login, func.lower(User.email) == login)))

    def by_username(self, username: str) -> User | None:
        return self.db.scalar(select(User).where(User.username == username.lower()))

    def by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(func.lower(User.email) == email.lower()))

    def search_stmt(self, role: RoleCode | None, q: str | None, is_active: bool | None) -> Select:
        stmt = select(User).join(User.role).order_by(User.created_at.desc())
        if role:
            stmt = stmt.where(Role.code == role)
        if q:
            like = f"%{q.lower()}%"
            stmt = stmt.where(or_(func.lower(User.full_name).like(like), User.username.like(like), func.lower(User.email).like(like)))
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        return stmt

    def count_by_role(self) -> dict[str, int]:
        rows = self.db.execute(select(Role.code, func.count(User.id)).join(User, User.role_id == Role.id, isouter=True).group_by(Role.code)).all()
        return {code.value: count for code, count in rows}


class TokenRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def revoke(self, jti: str, user_id: int, expires_at: datetime) -> None:
        if not self.db.get(RevokedToken, jti):
            self.db.add(RevokedToken(jti=jti, user_id=user_id, expires_at=expires_at))
        # Limpieza oportunista de tokens ya expirados.
        self.db.execute(delete(RevokedToken).where(RevokedToken.expires_at < datetime.now(UTC)))

    def is_revoked(self, jti: str) -> bool:
        return self.db.get(RevokedToken, jti) is not None

    def add_reset_token(self, token: PasswordResetToken) -> None:
        self.db.add(token)

    def reset_token_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        return self.db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash))


class ClassroomRepository(BaseRepository[Classroom]):
    model = Classroom

    def list_for(self, teacher_id: int | None) -> list[Classroom]:
        stmt = select(Classroom).options(selectinload(Classroom.students)).order_by(Classroom.school_year.desc(), Classroom.name)
        if teacher_id is not None:
            stmt = stmt.where(Classroom.teacher_id == teacher_id)
        return list(self.db.scalars(stmt))


class StudentRepository(BaseRepository[StudentProfile]):
    model = StudentProfile

    def _base(self) -> Select:
        return (
            select(StudentProfile)
            .join(StudentProfile.user)
            .options(selectinload(StudentProfile.guardians).joinedload(GuardianStudent.guardian), selectinload(StudentProfile.classroom))
            .order_by(StudentProfile.display_name)
        )

    def list_all(self) -> list[StudentProfile]:
        return list(self.db.scalars(self._base()).unique())

    def list_for_teacher(self, teacher_id: int) -> list[StudentProfile]:
        stmt = self._base().join(Classroom, StudentProfile.classroom_id == Classroom.id).where(Classroom.teacher_id == teacher_id)
        return list(self.db.scalars(stmt).unique())

    def list_for_guardian(self, guardian_id: int) -> list[StudentProfile]:
        stmt = self._base().join(GuardianStudent, GuardianStudent.student_id == StudentProfile.id).where(GuardianStudent.guardian_id == guardian_id)
        return list(self.db.scalars(stmt).unique())

    def list_for_classroom(self, classroom_id: int) -> list[StudentProfile]:
        return list(self.db.scalars(self._base().where(StudentProfile.classroom_id == classroom_id)).unique())

    def by_user_id(self, user_id: int) -> StudentProfile | None:
        return self.db.scalar(select(StudentProfile).where(StudentProfile.user_id == user_id))

    def is_guardian_of(self, guardian_id: int, student_id: int) -> bool:
        return self.db.get(GuardianStudent, (guardian_id, student_id)) is not None

    def link_guardian(self, guardian_id: int, student_id: int, label: str | None) -> None:
        if not self.is_guardian_of(guardian_id, student_id):
            self.db.add(GuardianStudent(guardian_id=guardian_id, student_id=student_id, relationship_label=label))
            self.db.flush()

    def add_link_code(self, code: StudentLinkCode) -> None:
        self.db.add(code)
        self.db.flush()

    def link_code_by_hash(self, code_hash: str) -> StudentLinkCode | None:
        return self.db.scalar(select(StudentLinkCode).where(StudentLinkCode.code_hash == code_hash))
