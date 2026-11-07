"""Configuración central de la aplicación.

Todas las variables sensibles se leen desde el entorno (archivo `.env` en desarrollo,
variables del contenedor en Docker). Nunca se escriben credenciales en el código.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- General ---
    APP_NAME: str = "V&E Academy API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    API_V1_PREFIX: str = "/api/v1"

    # --- Base de datos ---
    DATABASE_URL: str = Field(..., description="postgresql+psycopg://user:pass@host:5432/db")

    # --- Seguridad ---
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30
    LOGIN_MAX_FAILED_ATTEMPTS: int = 5
    LOGIN_LOCK_MINUTES: int = 10

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:4200"

    # --- Datos iniciales ---
    SEED_CONTENT: bool = True
    SEED_DEMO_USERS: bool = False
    ADMIN_EMAIL: str | None = None
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str | None = None

    # --- Correo (recuperación de contraseña). Opcional ---
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None
    SMTP_USE_TLS: bool = True
    FRONTEND_URL: str = "http://localhost:4200"

    # --- Propuesta futura: V&E AI Companion (desactivado por defecto) ---
    AI_COMPANION_ENABLED: bool = False
    AI_PROVIDER: str = "none"

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def _secret_not_placeholder(cls, value: str) -> str:
        if value.lower().startswith("change-me"):
            raise ValueError("JWT_SECRET_KEY usa el valor de ejemplo; genera uno nuevo.")
        return value

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def smtp_configured(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_FROM)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
