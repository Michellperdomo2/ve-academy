from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, DbSession, TokenPayload
from app.schemas.common import Message
from app.schemas.user import (
    ChangePasswordRequest,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    ProfileUpdate,
    RegisterRequest,
    TokenResponse,
    UserRead,
)
from app.services.auth_service import AuthService, user_to_read
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse, summary="Iniciar sesión (JSON)")
def login(data: LoginRequest, db: DbSession) -> TokenResponse:
    return AuthService(db).login(data.username, data.password)


@router.post("/token", response_model=TokenResponse, summary="Iniciar sesión (formulario OAuth2, usado por Swagger)")
def login_form(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession) -> TokenResponse:
    return AuthService(db).login(form.username, form.password)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED,
             summary="Registro público de docentes y acudientes")
def register(data: RegisterRequest, db: DbSession) -> UserRead:
    return user_to_read(AuthService(db).register(data))


@router.post("/logout", response_model=Message, summary="Cerrar sesión (revoca el token actual)")
def logout(payload: TokenPayload, db: DbSession) -> Message:
    AuthService(db).logout(payload)
    return Message(message="Sesión cerrada.")


@router.get("/me", response_model=UserRead, summary="Usuario autenticado")
def me(user: CurrentUser) -> UserRead:
    return user_to_read(user)


@router.patch("/me", response_model=UserRead, summary="Actualizar mi perfil")
def update_me(data: ProfileUpdate, user: CurrentUser, db: DbSession) -> UserRead:
    return user_to_read(UserService(db).update_profile(user, data))


@router.post("/change-password", response_model=Message)
def change_password(data: ChangePasswordRequest, user: CurrentUser, db: DbSession) -> Message:
    AuthService(db).change_password(user, data.current_password, data.new_password)
    return Message(message="Contraseña actualizada.")


@router.post("/password-reset/request", response_model=Message,
             summary="Solicitar enlace de recuperación (requiere SMTP configurado)")
def password_reset_request(data: PasswordResetRequest, db: DbSession) -> Message:
    enabled = AuthService(db).request_password_reset(data.email)
    if not enabled:
        return Message(message="La recuperación por correo no está habilitada en este servidor. "
                               "Pide al administrador que restablezca tu contraseña.")
    return Message(message="Si el correo está registrado, recibirás un enlace para restablecer tu contraseña.")


@router.post("/password-reset/confirm", response_model=Message)
def password_reset_confirm(data: PasswordResetConfirm, db: DbSession) -> Message:
    AuthService(db).confirm_password_reset(data.token, data.new_password)
    return Message(message="Contraseña restablecida. Ya puedes iniciar sesión.")
