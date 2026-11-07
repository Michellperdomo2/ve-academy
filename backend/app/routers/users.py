from fastapi import APIRouter, Query, status

from app.api.deps import AdminUser, DbSession
from app.models.enums import RoleCode
from app.schemas.common import Message, Page
from app.schemas.user import AdminPasswordReset, AdminUserCreate, AdminUserUpdate, UserRead
from app.services.auth_service import user_to_read
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Usuarios (administrador)"])


@router.get("", response_model=Page[UserRead])
def list_users(
    _: AdminUser, db: DbSession,
    role: RoleCode | None = None, q: str | None = Query(default=None, max_length=60),
    is_active: bool | None = None, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
) -> Page[UserRead]:
    return UserService(db).list(role, q, is_active, page, size)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(data: AdminUserCreate, _: AdminUser, db: DbSession) -> UserRead:
    return user_to_read(UserService(db).create(data))


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, _: AdminUser, db: DbSession) -> UserRead:
    return user_to_read(UserService(db).get(user_id))


@router.patch("/{user_id}", response_model=UserRead)
def update_user(user_id: int, data: AdminUserUpdate, admin: AdminUser, db: DbSession) -> UserRead:
    return user_to_read(UserService(db).update(admin, user_id, data))


@router.delete("/{user_id}", response_model=UserRead, summary="Desactivar usuario (borrado lógico)")
def deactivate_user(user_id: int, admin: AdminUser, db: DbSession) -> UserRead:
    return user_to_read(UserService(db).update(admin, user_id, AdminUserUpdate(is_active=False)))


@router.post("/{user_id}/reset-password", response_model=Message)
def reset_password(user_id: int, data: AdminPasswordReset, _: AdminUser, db: DbSession) -> Message:
    UserService(db).reset_password(user_id, data.new_password)
    return Message(message="Contraseña restablecida.")
