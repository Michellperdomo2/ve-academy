"""Esquemas de autenticación, usuarios, aulas y estudiantes."""

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import RoleCode
from app.schemas.common import ORMModel

USERNAME_RE = re.compile(r"^[a-z0-9._-]{3,40}$")


def _validate_username(value: str) -> str:
    value = value.strip().lower()
    if not USERNAME_RE.match(value):
        raise ValueError("Usa de 3 a 40 caracteres: letras minúsculas, números, punto, guion o guion bajo.")
    return value


def _validate_strong_password(value: str) -> str:
    if len(value) < 8 or not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        raise ValueError("La contraseña debe tener al menos 8 caracteres, con letras y números.")
    return value


# ---------- Autenticación ----------
class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=255, description="Usuario o correo")
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: "UserRead"


class RegisterRequest(BaseModel):
    """Registro público solo para adultos. Las cuentas de niños las crea un adulto."""

    full_name: str = Field(min_length=3, max_length=120)
    email: EmailStr
    username: str
    password: str = Field(max_length=128)
    role: Literal["teacher", "guardian"]
    accept_terms: bool = Field(description="Acepta el tratamiento de datos (Ley 1581 de 2012)")

    _u = field_validator("username")(_validate_username)
    _p = field_validator("password")(_validate_strong_password)

    @field_validator("accept_terms")
    @classmethod
    def _must_accept(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Debes aceptar la política de tratamiento de datos.")
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(max_length=128)

    _p = field_validator("new_password")(_validate_strong_password)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    new_password: str = Field(max_length=128)

    _p = field_validator("new_password")(_validate_strong_password)


# ---------- Usuarios ----------
class UserRead(ORMModel):
    id: int
    username: str
    email: str | None
    full_name: str
    role: RoleCode
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None
    student_profile_id: int | None = None


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=3, max_length=120)
    email: EmailStr | None = None


class AdminUserCreate(BaseModel):
    full_name: str = Field(min_length=3, max_length=120)
    email: EmailStr | None = None
    username: str
    password: str = Field(max_length=128)
    role: RoleCode

    _u = field_validator("username")(_validate_username)
    _p = field_validator("password")(_validate_strong_password)


class AdminUserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=3, max_length=120)
    email: EmailStr | None = None
    is_active: bool | None = None


class AdminPasswordReset(BaseModel):
    new_password: str = Field(max_length=128)

    _p = field_validator("new_password")(_validate_strong_password)


# ---------- Aulas ----------
class ClassroomCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    grade: str = Field(default="Primero", max_length=20)
    school_year: int = Field(ge=2020, le=2100)
    institution: str | None = Field(default=None, max_length=150)


class ClassroomUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    grade: str | None = Field(default=None, max_length=20)
    school_year: int | None = Field(default=None, ge=2020, le=2100)
    institution: str | None = Field(default=None, max_length=150)


class ClassroomRead(ORMModel):
    id: int
    name: str
    grade: str
    school_year: int
    institution: str | None
    teacher_id: int
    teacher_name: str
    student_count: int


# ---------- Estudiantes ----------
class StudentCreate(BaseModel):
    """Datos mínimos de un menor: nombre visible, usuario y contraseña sencilla."""

    display_name: str = Field(min_length=2, max_length=40)
    username: str
    password: str = Field(min_length=6, max_length=64, description="Contraseña sencilla para el niño (mín. 6)")
    age: int | None = Field(default=None, ge=4, le=12)
    classroom_id: int | None = None
    relationship_label: str | None = Field(default=None, max_length=40)

    _u = field_validator("username")(_validate_username)


class StudentUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=40)
    age: int | None = Field(default=None, ge=4, le=12)
    classroom_id: int | None = None
    is_active: bool | None = None


class StudentPasswordReset(BaseModel):
    new_password: str = Field(min_length=6, max_length=64)


class StudentRead(BaseModel):
    id: int
    user_id: int
    username: str
    display_name: str
    avatar: str
    age: int | None
    is_active: bool
    classroom_id: int | None
    classroom_name: str | None
    guardian_names: list[str]
    total_points: int
    level_number: int
    created_at: datetime


class LinkCodeResponse(BaseModel):
    code: str
    expires_at: datetime


class LinkStudentRequest(BaseModel):
    code: str = Field(min_length=6, max_length=12)
    relationship_label: str | None = Field(default=None, max_length=40)


class AvatarUpdate(BaseModel):
    avatar: str = Field(min_length=2, max_length=40)


TokenResponse.model_rebuild()
