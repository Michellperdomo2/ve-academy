"""Fixtures de pruebas.

Las pruebas corren contra PostgreSQL REAL (no SQLite), en una base dedicada definida por
TEST_DATABASE_URL. El esquema se crea ejecutando las migraciones de Alembic, así que las
migraciones también quedan probadas.
"""

import os
import uuid

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://ve_user:ve_pass_local@127.0.0.1:5432/ve_academy_test"
)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-0123456789abcdef0123456789")
os.environ["ENVIRONMENT"] = "test"
os.environ["SMTP_HOST"] = ""
os.environ["SEED_DEMO_USERS"] = "false"
os.environ["ADMIN_PASSWORD"] = ""

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.database import SessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Role, User  # noqa: E402
from app.models.enums import RoleCode  # noqa: E402
from app.seed.run import seed_catalog, seed_content  # noqa: E402

BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
API = "/api/v1"

PER_TEST_TABLES = [
    "revoked_tokens", "password_reset_tokens", "point_transactions", "student_badges", "student_challenges",
    "attempt_answers", "attempts", "reading_sessions", "student_link_codes", "guardian_students",
    "student_profiles", "classrooms",
]


@pytest.fixture(scope="session", autouse=True)
def database():
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    command.upgrade(cfg, "head")
    with SessionLocal() as db:
        seed_catalog(db)
        seed_content(db)
    yield


@pytest.fixture(autouse=True)
def clean_tables():
    with engine.begin() as conn:
        for table in PER_TEST_TABLES:
            conn.execute(text(f"DELETE FROM {table}"))
        conn.execute(text("UPDATE readings SET created_by_id = NULL; UPDATE activities SET created_by_id = NULL;"))
        conn.execute(text("DELETE FROM users"))
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def make_user(role: RoleCode, password: str = "Clave12345", username: str | None = None) -> User:
    username = username or f"{role.value}_{uuid.uuid4().hex[:8]}"
    with SessionLocal() as db:
        role_obj = db.query(Role).filter(Role.code == role).one()
        user = User(username=username, email=f"{username}@example.com", full_name=f"Usuario {username}",
                    password_hash=hash_password(password), role_id=role_obj.id)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


def login(client: TestClient, username: str, password: str = "Clave12345") -> dict:
    res = client.post(f"{API}/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
def admin_headers(client) -> dict:
    user = make_user(RoleCode.ADMIN)
    return login(client, user.username)


@pytest.fixture
def teacher(client) -> tuple[User, dict]:
    user = make_user(RoleCode.TEACHER)
    return user, login(client, user.username)


@pytest.fixture
def guardian(client) -> tuple[User, dict]:
    user = make_user(RoleCode.GUARDIAN)
    return user, login(client, user.username)


@pytest.fixture
def classroom(client, teacher) -> dict:
    _, headers = teacher
    res = client.post(f"{API}/classrooms", json={"name": "Primero A", "school_year": 2026}, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


@pytest.fixture
def student(client, teacher, classroom) -> tuple[dict, dict]:
    """Estudiante creado por el docente en su aula. Devuelve (datos, headers del estudiante)."""
    _, headers = teacher
    username = f"nino_{uuid.uuid4().hex[:6]}"
    res = client.post(f"{API}/students", headers=headers, json={
        "display_name": "Sofía", "username": username, "password": "lectura1", "age": 6, "classroom_id": classroom["id"],
    })
    assert res.status_code == 201, res.text
    return res.json(), login(client, username, "lectura1")
