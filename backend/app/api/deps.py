"""Dependencias de FastAPI: sesión de BD, usuario autenticado y control de acceso por rol."""

from collections.abc import Callable
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import decode_access_token
from app.models import StudentProfile, User
from app.models.enums import RoleCode
from app.repositories.user_repository import StudentRepository, TokenRepository, UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{get_settings().API_V1_PREFIX}/auth/token", auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_token_payload(token: Annotated[str | None, Depends(oauth2_scheme)], db: DbSession) -> dict:
    if not token:
        raise AuthenticationError("Debes iniciar sesión.")
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise AuthenticationError("La sesión no es válida o expiró.") from exc
    if TokenRepository(db).is_revoked(payload["jti"]):
        raise AuthenticationError("La sesión fue cerrada.")
    return payload


TokenPayload = Annotated[dict, Depends(get_token_payload)]


def get_current_user(payload: TokenPayload, db: DbSession) -> User:
    user = UserRepository(db).get(int(payload["sub"]))
    if not user or not user.is_active:
        raise AuthenticationError("La cuenta no existe o está desactivada.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: RoleCode) -> Callable[[User], User]:
    """Fábrica de dependencias: permite el acceso solo a los roles indicados."""

    def checker(user: CurrentUser) -> User:
        if user.role_code not in roles:
            raise PermissionDeniedError("No tienes permiso para realizar esta acción.")
        return user

    return checker


AdminUser = Annotated[User, Depends(require_roles(RoleCode.ADMIN))]
StaffUser = Annotated[User, Depends(require_roles(RoleCode.ADMIN, RoleCode.TEACHER))]
AdultUser = Annotated[User, Depends(require_roles(RoleCode.ADMIN, RoleCode.TEACHER, RoleCode.GUARDIAN))]
GuardianUser = Annotated[User, Depends(require_roles(RoleCode.GUARDIAN))]


def get_current_student(user: Annotated[User, Depends(require_roles(RoleCode.STUDENT))], db: DbSession) -> StudentProfile:
    student = StudentRepository(db).by_user_id(user.id)
    if not student:
        raise PermissionDeniedError("Perfil de estudiante no encontrado.")
    return student


CurrentStudent = Annotated[StudentProfile, Depends(get_current_student)]
