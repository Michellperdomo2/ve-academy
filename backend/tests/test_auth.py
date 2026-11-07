"""Registro, inicio y cierre de sesión, bloqueo por intentos y contraseñas."""

from datetime import UTC, datetime, timedelta

from app.core.database import SessionLocal
from app.core.security import sha256
from app.models import PasswordResetToken
from app.models.enums import RoleCode

from .conftest import API, login, make_user

REGISTER = {
    "full_name": "María Pérez", "email": "maria@example.com", "username": "maria.perez",
    "password": "Segura123", "role": "guardian", "accept_terms": True,
}


def test_register_and_login(client):
    res = client.post(f"{API}/auth/register", json=REGISTER)
    assert res.status_code == 201, res.text
    assert res.json()["role"] == "guardian"
    assert "password" not in res.text and "hash" not in res.text

    res = client.post(f"{API}/auth/login", json={"username": "maria@example.com", "password": "Segura123"})
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer" and body["user"]["username"] == "maria.perez"


def test_register_duplicate_and_validation(client):
    assert client.post(f"{API}/auth/register", json=REGISTER).status_code == 201
    assert client.post(f"{API}/auth/register", json=REGISTER).json()["error"]["code"] == "conflict"
    # Un niño no puede registrarse solo, ni se aceptan contraseñas débiles o sin aceptar términos.
    for change in ({"role": "student"}, {"role": "admin"}, {"password": "abc"}, {"accept_terms": False}, {"username": "Con Espacios"}):
        res = client.post(f"{API}/auth/register", json={**REGISTER, "username": "otro.user", "email": "o@t.co", **change})
        assert res.status_code == 422, change


def test_login_wrong_password_generic_message(client):
    user = make_user(RoleCode.TEACHER)
    bad = client.post(f"{API}/auth/login", json={"username": user.username, "password": "incorrecta1"})
    missing = client.post(f"{API}/auth/login", json={"username": "no.existe", "password": "incorrecta1"})
    assert bad.status_code == missing.status_code == 401
    assert bad.json()["error"]["message"] == missing.json()["error"]["message"]


def test_account_lock_after_failed_attempts(client):
    user = make_user(RoleCode.TEACHER)
    for _ in range(5):
        client.post(f"{API}/auth/login", json={"username": user.username, "password": "mala12345"})
    res = client.post(f"{API}/auth/login", json={"username": user.username, "password": "Clave12345"})
    assert res.status_code == 429


def test_me_and_logout_revokes_token(client):
    user = make_user(RoleCode.GUARDIAN)
    headers = login(client, user.username)
    assert client.get(f"{API}/auth/me", headers=headers).json()["username"] == user.username
    assert client.post(f"{API}/auth/logout", headers=headers).status_code == 200
    res = client.get(f"{API}/auth/me", headers=headers)
    assert res.status_code == 401


def test_invalid_and_missing_token(client):
    assert client.get(f"{API}/auth/me").status_code == 401
    assert client.get(f"{API}/auth/me", headers={"Authorization": "Bearer xxx.yyy.zzz"}).status_code == 401


def test_update_profile_and_change_password(client):
    user = make_user(RoleCode.TEACHER)
    headers = login(client, user.username)
    res = client.patch(f"{API}/auth/me", headers=headers, json={"full_name": "Profe Ana"})
    assert res.json()["full_name"] == "Profe Ana"
    assert client.post(f"{API}/auth/change-password", headers=headers,
                       json={"current_password": "mala", "new_password": "Nueva12345"}).status_code == 401
    assert client.post(f"{API}/auth/change-password", headers=headers,
                       json={"current_password": "Clave12345", "new_password": "Nueva12345"}).status_code == 200
    login(client, user.username, "Nueva12345")


def test_password_reset_without_smtp_is_honest(client):
    user = make_user(RoleCode.GUARDIAN)
    res = client.post(f"{API}/auth/password-reset/request", json={"email": user.email})
    assert res.status_code == 200
    assert "no está habilitada" in res.json()["message"]


def test_password_reset_confirm_with_valid_token(client):
    user = make_user(RoleCode.GUARDIAN)
    with SessionLocal() as db:
        db.add(PasswordResetToken(user_id=user.id, token_hash=sha256("token-de-prueba-123456789"),
                                  expires_at=datetime.now(UTC) + timedelta(minutes=10)))
        db.commit()
    payload = {"token": "token-de-prueba-123456789", "new_password": "Restablecida1"}
    assert client.post(f"{API}/auth/password-reset/confirm", json=payload).status_code == 200
    login(client, user.username, "Restablecida1")
    # El token es de un solo uso.
    assert client.post(f"{API}/auth/password-reset/confirm", json=payload).status_code == 401
