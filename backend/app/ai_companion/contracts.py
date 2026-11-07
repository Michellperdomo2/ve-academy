"""V&E AI Companion — contratos de integración (PROPUESTA FUTURA).

Este módulo NO hace parte de los requerimientos originales del documento V&E Academy.
Define las interfaces para que, más adelante, se conecte un proveedor de IA sin tocar
el resto del sistema (principio de inversión de dependencias).

En la versión actual NO hay ningún proveedor real conectado: `DisabledCompanionProvider`
rechaza toda solicitud y el endpoint de estado lo informa explícitamente.
"""

from enum import Enum
from typing import Protocol

from pydantic import BaseModel, Field

from app.models.enums import Skill


class CompanionIntent(str, Enum):
    EXPLAIN_WORD = "explain_word"  # explicar una palabra desconocida
    GIVE_HINT = "give_hint"  # pista sin revelar la respuesta
    ASK_QUESTION = "ask_question"  # formular una pregunta sencilla sobre la lectura
    ENCOURAGE = "encourage"  # motivar / felicitar
    EXPLAIN_MISTAKE = "explain_mistake"  # explicar un error en tono positivo


class CompanionContext(BaseModel):
    """Contexto MINIMIZADO que se enviaría al proveedor: sin nombre, edad exacta ni identificadores."""

    reading_title: str | None = None
    paragraph_text: str | None = Field(default=None, max_length=2000)
    question_prompt: str | None = None
    target_word: str | None = Field(default=None, max_length=40)
    reading_level: int = Field(ge=1, le=3, description="Dificultad 1-3, no la edad del niño")
    skills_to_reinforce: list[Skill] = []


class CompanionRequest(BaseModel):
    intent: CompanionIntent
    child_message: str | None = Field(default=None, max_length=200)
    context: CompanionContext


class CompanionReply(BaseModel):
    text: str = Field(max_length=400)
    suggested_activity_ids: list[int] = []
    flagged: bool = False  # True si el filtro de seguridad intervino


class CompanionProvider(Protocol):
    """Contrato que debe implementar cualquier proveedor (OpenAI, Anthropic, Gemini, modelo local...)."""

    name: str

    def is_available(self) -> bool: ...

    def reply(self, request: CompanionRequest) -> CompanionReply: ...
