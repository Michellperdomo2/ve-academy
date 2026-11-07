"""Autenticación: login con bloqueo por intentos, registro, cierre de sesión y contraseñas."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, ConflictError, TooManyRequestsError
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_password,
    sha256,
    verify_password,
)
from app.models import PasswordResetToken, User
from app.models.enums import RoleCode
from app.repositories.user_repository import RoleRepository, TokenRepository, UserRepository
from app.schemas.user import RegisterRequest, TokenResponse, UserRead
from app.services.email_service import EmailService

INVALID_CREDENTIALS = "Usuario o contraseña incorrectos."
_DUMMY_HASH = hash_password("ve-academy-dummy-password")


def user_to_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role.code,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        student_profile_id=user.student_profile.id if user.student_profile else None,
    )


class AuthService:
    def __init__(self, db: Session, email_service: EmailService | None = None) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)
        self.tokens = TokenRepository(db)
        self.email = email_service or EmailService()
        self.settings = get_settings()

    # ---------- Login / logout ----------
    def login(self, login: str, password: str) -> TokenResponse:
        user = self.users.by_login(login)
        now = datetime.now(UTC)
        if user is None:
            verify_password(password, _DUMMY_HASH)  # mismo costo que un usuario real (evita enumeración)
            raise AuthenticationError(INVALID_CREDENTIALS)
        if user.locked_until and user.locked_until > now:
            raise TooManyRequestsError("Demasiados intentos fallidos. Espera unos minutos e inténtalo de nuevo.")
        if not verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= self.settings.LOGIN_MAX_FAILED_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=self.settings.LOGIN_LOCK_MINUTES)
                user.failed_login_attempts = 0
            self.db.commit()
            raise AuthenticationError(INVALID_CREDENTIALS)
        if not user.is_active:
            raise AuthenticationError("La cuenta está desactivada. Contacta a tu docente o al administrador.")

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = now
        self.db.commit()
        token, expires = create_access_token(user.id, user.role.code.value)
        return TokenResponse(access_token=token, expires_at=expires, user=user_to_read(user))

    def logout(self, payload: dict) -> None:
        expires = datetime.fromtimestamp(payload["exp"], tz=UTC)
        self.tokens.revoke(payload["jti"], int(payload["sub"]), expires)
        self.db.commit()

    # ---------- Registro ----------
    def register(self, data: RegisterRequest) -> User:
        self._ensure_unique(data.username, data.email)
        role = self.roles.by_code(RoleCode(data.role))
        assert role is not None, "Roles no inicializados"
        user = User(
            username=data.username,
            email=data.email.lower(),
            full_name=data.full_name.strip(),
            password_hash=hash_password(data.password),
            role=role,
        )
        self.users.add(user)
        self.db.commit()
        return user

    def _ensure_unique(self, username: str, email: str | None) -> None:
        if self.users.by_username(username):
            raise ConflictError("Ese nombre de usuario ya está en uso.")
        if email and self.users.by_email(email):
            raise ConflictError("Ese correo ya está registrado.")

    # ---------- Contraseñas ----------
    def change_password(self, user: User, current: str, new: str) -> None:
        if not verify_password(current, user.password_hash):
            raise AuthenticationError("La contraseña actual no es correcta.")
        user.password_hash = hash_password(new)
        self.db.commit()

    def request_password_reset(self, email: str) -> bool:
        """Siempre responde igual para no revelar si el correo existe."""
        user = self.users.by_email(email)
        if not user or not user.is_active or not self.email.enabled:
            return self.email.enabled
        token = generate_opaque_token()
        self.tokens.add_reset_token(
            PasswordResetToken(
                user_id=user.id,
                token_hash=sha256(token),
                expires_at=datetime.now(UTC) + timedelta(minutes=self.settings.PASSWORD_RESET_EXPIRE_MINUTES),
            )
        )
        self.db.commit()
        self.email.send_password_reset(user.email or "", user.full_name, token)
        return True

    def confirm_password_reset(self, token: str, new_password: str) -> None:
        record = self.tokens.reset_token_by_hash(sha256(token))
        now = datetime.now(UTC)
        if not record or record.used_at or record.expires_at < now:
            raise AuthenticationError("El enlace no es válido o ya expiró.")
        user = self.users.get(record.user_id)
        if not user:
            raise AuthenticationError("El enlace no es válido o ya expiró.")
        user.password_hash = hash_password(new_password)
        user.failed_login_attempts = 0
        user.locked_until = None
        record.used_at = now
        self.db.commit()
