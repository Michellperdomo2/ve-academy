import re
import unicodedata

from app.models.enums import ReadingLength, Skill

SKILL_LABELS: dict[Skill, str] = {
    Skill.PHONOLOGICAL_AWARENESS: "Conciencia fonológica (sílabas y rimas)",
    Skill.WORD_RECOGNITION: "Reconocimiento de palabras",
    Skill.VOCABULARY: "Vocabulario",
    Skill.SENTENCE_BUILDING: "Formación de oraciones",
    Skill.SEQUENCING: "Secuencias",
    Skill.LITERAL: "Comprensión literal",
    Skill.INFERENTIAL: "Comprensión inferencial",
    Skill.CRITICAL: "Comprensión crítica",
}


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or "item"


def length_for_words(word_count: int) -> ReadingLength:
    """Clasificación de extensión para lectores de 1.er grado."""
    if word_count <= 70:
        return ReadingLength.SHORT
    if word_count <= 150:
        return ReadingLength.MEDIUM
    return ReadingLength.LONG
