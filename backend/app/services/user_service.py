"""Gestión de usuarios por parte del administrador."""

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.core.security import hash_password
from app.models import StudentProfile, User
from app.models.enums import RoleCode
from app.repositories.user_repository import RoleRepository, UserRepository
from app.schemas.common import Page
from app.schemas.user import AdminUserCreate, AdminUserUpdate, ProfileUpdate, UserRead
from app.services.auth_service import user_to_read


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)

    def get(self, user_id: int) -> User:
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("Usuario no encontrado.")
        return user

    def list(self, role: RoleCode | None, q: str | None, is_active: bool | None, page: int, size: int) -> Page[UserRead]:
        items, total = self.users.paginate(self.users.search_stmt(role, q, is_active), page, size)
        return Page(items=[user_to_read(u) for u in items], total=total, page=page, size=size)

    def create(self, data: AdminUserCreate) -> User:
        if self.users.by_username(data.username):
            raise ConflictError("Ese nombre de usuario ya está en uso.")
        if data.email and self.users.by_email(data.email):
            raise ConflictError("Ese correo ya está registrado.")
        role = self.roles.by_code(data.role)
        assert role is not None
        user = User(
            username=data.username,
            email=data.email.lower() if data.email else None,
            full_name=data.full_name.strip(),
            password_hash=hash_password(data.password),
            role=role,
        )
        self.users.add(user)
        if data.role == RoleCode.STUDENT:
            self.db.add(StudentProfile(user_id=user.id, display_name=data.full_name.split()[0][:40]))
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, actor: User, user_id: int, data: AdminUserUpdate) -> User:
        user = self.get(user_id)
        if data.is_active is False and user.id == actor.id:
            raise PermissionDeniedError("No puedes desactivar tu propia cuenta.")
        self._apply_profile(user, data.full_name, data.email)
        if data.is_active is not None:
            user.is_active = data.is_active
        self.db.commit()
        return user

    def update_profile(self, user: User, data: ProfileUpdate) -> User:
        self._apply_profile(user, data.full_name, data.email)
        self.db.commit()
        return user

    def _apply_profile(self, user: User, full_name: str | None, email: str | None) -> None:
        if full_name is not None:
            user.full_name = full_name.strip()
        if email is not None:
            other = self.users.by_email(email)
            if other and other.id != user.id:
                raise ConflictError("Ese correo ya está registrado.")
            user.email = email.lower()

    def reset_password(self, user_id: int, new_password: str) -> None:
        user = self.get(user_id)
        user.password_hash = hash_password(new_password)
        user.failed_login_attempts = 0
        user.locked_until = None
        self.db.commit()
