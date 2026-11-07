"""Usuarios, roles, perfiles de estudiante y relaciones docente/acudiente."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin
from app.models.enums import RoleCode, str_enum


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[RoleCode] = mapped_column(str_enum(RoleCode, "role_code"), unique=True)
    name: Mapped[str] = mapped_column(String(60))
    description: Mapped[str | None] = mapped_column(String(255))


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    # Opcional: los estudiantes (menores) no necesitan correo.
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    role: Mapped[Role] = relationship(lazy="joined")
    student_profile: Mapped["StudentProfile | None"] = relationship(
        back_populates="user", uselist=False, foreign_keys="StudentProfile.user_id"
    )

    @property
    def role_code(self) -> RoleCode:
        return self.role.code


class RevokedToken(Base):
    """Lista de revocación de JWT (cierre de sesión)."""

    __tablename__ = "revoked_tokens"

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Classroom(TimestampMixin, Base):
    """Grupo/aula de un docente. Asocia docentes con estudiantes."""

    __tablename__ = "classrooms"
    __table_args__ = (UniqueConstraint("teacher_id", "name", "school_year", name="uq_classroom_teacher_name_year"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    grade: Mapped[str] = mapped_column(String(20), default="Primero", server_default="Primero")
    school_year: Mapped[int] = mapped_column(SmallInteger)
    institution: Mapped[str | None] = mapped_column(String(150))
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)

    teacher: Mapped[User] = relationship()
    students: Mapped[list["StudentProfile"]] = relationship(back_populates="classroom")


class StudentProfile(TimestampMixin, Base):
    """Datos pedagógicos mínimos del estudiante (minimización de datos de menores)."""

    __tablename__ = "student_profiles"
    __table_args__ = (CheckConstraint("age IS NULL OR (age BETWEEN 4 AND 12)", name="age_range"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    display_name: Mapped[str] = mapped_column(String(40))
    avatar: Mapped[str] = mapped_column(String(40), default="owl", server_default="owl")
    age: Mapped[int | None] = mapped_column(SmallInteger)
    classroom_id: Mapped[int | None] = mapped_column(
        ForeignKey("classrooms.id", ondelete="SET NULL"), index=True
    )
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    user: Mapped[User] = relationship(back_populates="student_profile", foreign_keys=[user_id], lazy="joined")
    classroom: Mapped[Classroom | None] = relationship(back_populates="students")
    guardians: Mapped[list["GuardianStudent"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )


class GuardianStudent(Base):
    """Relación N:M entre acudientes y estudiantes."""

    __tablename__ = "guardian_students"

    guardian_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("student_profiles.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    relationship_label: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    guardian: Mapped[User] = relationship()
    student: Mapped[StudentProfile] = relationship(back_populates="guardians")


class StudentLinkCode(Base):
    """Código de un solo uso que un docente entrega al acudiente para vincularse."""

    __tablename__ = "student_link_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True)
    code_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
