"""Healthcheck, errores homogéneos y la propuesta futura V&E AI Companion (desactivada)."""

import pytest

from app.ai_companion.contracts import CompanionContext, CompanionIntent, CompanionRequest
from app.ai_companion.providers import get_companion_provider
from app.ai_companion.safety import is_off_topic_or_unsafe, redact_personal_data
from app.core.exceptions import ServiceUnavailableError

from .conftest import API


def test_health(client):
    assert client.get(f"{API}/health").json() == {"status": "ok", "database": "ok", "version": "1.0.0"}


def test_openapi_and_swagger_available(client):
    assert client.get("/docs").status_code == 200
    spec = client.get(f"{API}/openapi.json").json()
    assert "/api/v1/auth/login" in spec["paths"] and "/api/v1/attempts/{attempt_id}/answers" in spec["paths"]


def test_error_format(client):
    body = client.get(f"{API}/auth/me").json()
    assert set(body["error"]) == {"code", "message", "details"}


def test_security_headers(client):
    res = client.get(f"{API}/health")
    assert res.headers["x-content-type-options"] == "nosniff" and res.headers["x-frame-options"] == "DENY"


def test_ai_companion_reports_not_connected(client, student):
    _, headers = student
    status = client.get(f"{API}/ai-companion/status", headers=headers).json()
    assert status == {"enabled": False, "provider": "none", "available": False, "message": status["message"]}
    assert "Propuesta futura" in status["message"]


def test_disabled_provider_never_fakes_answers():
    provider = get_companion_provider()
    request = CompanionRequest(intent=CompanionIntent.EXPLAIN_WORD, context=CompanionContext(reading_level=1, target_word="caparazón"))
    with pytest.raises(ServiceUnavailableError):
        provider.reply(request)


def test_safety_filters():
    text, found = redact_personal_data("Mi correo es nino@mail.com y vivo en la calle 10, mi número 3001234567")
    assert set(found) == {"email", "phone", "address"}
    assert "nino@mail.com" not in text and "3001234567" not in text
    assert is_off_topic_or_unsafe("¿dónde vives?") and not is_off_topic_or_unsafe("¿qué significa caparazón?")
