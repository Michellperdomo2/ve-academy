"""Filtros de seguridad previos y posteriores a cualquier llamada de IA (PROPUESTA FUTURA).

Son reglas deterministas (no IA) y ya son funcionales y probadas: se aplicarán antes de
enviar texto a un proveedor (minimización de datos de menores) y sobre sus respuestas.
"""

import re

_PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "phone": re.compile(r"(?:\+?\d[\s-]?){7,}"),
    "address": re.compile(r"\b(calle|carrera|cra|cll|avenida|av\.?|diagonal|transversal|barrio)\s*\d*", re.IGNORECASE),
    "url": re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE),
}

# Temas fuera del contexto educativo que el acompañante nunca debe tratar.
_BLOCKED_TOPICS = re.compile(
    r"\b(dónde vives|donde vives|tu dirección|tu direccion|tu teléfono|tu telefono|contraseña|password|"
    r"foto tuya|secreto|no le digas)\b",
    re.IGNORECASE,
)


def redact_personal_data(text: str) -> tuple[str, list[str]]:
    """Reemplaza datos personales por marcadores y devuelve qué tipos se encontraron."""
    found: list[str] = []
    for kind, pattern in _PATTERNS.items():
        if pattern.search(text):
            found.append(kind)
            text = pattern.sub(f"[{kind} oculto]", text)
    return text, found


def is_off_topic_or_unsafe(text: str) -> bool:
    return bool(_BLOCKED_TOPICS.search(text))


SAFE_FALLBACK = "¡Hablemos de la lectura! ¿Quieres que te ayude con una palabra o con una pregunta del cuento?"
