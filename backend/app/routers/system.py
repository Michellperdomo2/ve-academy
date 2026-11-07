from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.ai_companion.providers import get_companion_provider
from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings

router = APIRouter(tags=["Sistema"])


class HealthResponse(BaseModel):
    status: str
    database: str
    version: str


class CompanionStatus(BaseModel):
    enabled: bool
    provider: str
    available: bool
    message: str


@router.get("/health", response_model=HealthResponse, summary="Healthcheck (API + base de datos)")
def health(db: DbSession) -> HealthResponse:
    db.execute(text("SELECT 1"))
    return HealthResponse(status="ok", database="ok", version=get_settings().APP_VERSION)


@router.get("/ai-companion/status", response_model=CompanionStatus,
            summary="Estado del V&E AI Companion (propuesta futura, desactivado)")
def companion_status(_: CurrentUser) -> CompanionStatus:
    provider = get_companion_provider()
    available = provider.is_available()
    return CompanionStatus(
        enabled=get_settings().AI_COMPANION_ENABLED, provider=provider.name, available=available,
        message="Conectado." if available else
        "Propuesta futura: no hay un proveedor de IA conectado. Ver docs/05-ai-companion.md.",
    )
