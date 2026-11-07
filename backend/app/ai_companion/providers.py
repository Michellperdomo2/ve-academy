"""Fábrica de proveedores del AI Companion (PROPUESTA FUTURA).

Hoy solo existe `DisabledCompanionProvider`. Para integrar un proveedor real se crea una
clase que cumpla `CompanionProvider` y se registra en `_REGISTRY` (ver docs/05-ai-companion.md).
"""

from app.ai_companion.contracts import CompanionProvider, CompanionReply, CompanionRequest
from app.core.config import get_settings
from app.core.exceptions import ServiceUnavailableError


class DisabledCompanionProvider:
    name = "none"

    def is_available(self) -> bool:
        return False

    def reply(self, request: CompanionRequest) -> CompanionReply:  # noqa: ARG002
        raise ServiceUnavailableError(
            "El acompañante V&E AI Companion es una propuesta futura y no está conectado a ningún servicio de IA."
        )


_REGISTRY: dict[str, type] = {"none": DisabledCompanionProvider}


def get_companion_provider() -> CompanionProvider:
    settings = get_settings()
    if not settings.AI_COMPANION_ENABLED:
        return DisabledCompanionProvider()
    provider_cls = _REGISTRY.get(settings.AI_PROVIDER, DisabledCompanionProvider)
    return provider_cls()
