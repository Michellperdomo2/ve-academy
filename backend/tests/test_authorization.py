"""Control de acceso basado en roles y aislamiento de datos de menores."""

from app.models.enums import RoleCode

from .conftest import API, login, make_user

READING = {
    "title": "Prueba", "summary": "Resumen", "category_id": 1, "difficulty": 1,
    "comprehension_focus": "literal", "paragraphs": [{"text": "Hola mundo."}],
}


def test_admin_only_endpoints(client, admin_headers, teacher, guardian, student):
    _, t_headers = teacher
    _, g_headers = guardian
    _, s_headers = student
    assert client.get(f"{API}/users", headers=admin_headers).status_code == 200
    assert client.get(f"{API}/stats/overview", headers=admin_headers).status_code == 200
    for headers in (t_headers, g_headers, s_headers):
        assert client.get(f"{API}/users", headers=headers).status_code == 403
        assert client.post(f"{API}/readings", headers=headers, json=READING).status_code == 403
        assert client.get(f"{API}/stats/overview", headers=headers).status_code == 403


def test_student_cannot_use_adult_endpoints(client, student):
    data, s_headers = student
    assert client.get(f"{API}/students", headers=s_headers).status_code == 403
    assert client.get(f"{API}/students/{data['id']}/progress", headers=s_headers).status_code == 403
    assert client.get(f"{API}/classrooms", headers=s_headers).status_code == 403


def test_adults_cannot_use_student_endpoints(client, teacher):
    _, headers = teacher
    assert client.get(f"{API}/me/dashboard", headers=headers).status_code == 403
    assert client.post(f"{API}/activities/1/attempts", headers=headers).status_code == 403


def test_teacher_isolation(client, student):
    """Otro docente no puede ver (ni saber que existe) a un estudiante ajeno."""
    data, _ = student
    other = make_user(RoleCode.TEACHER)
    headers = login(client, other.username)
    assert client.get(f"{API}/students/{data['id']}", headers=headers).status_code == 404
    assert client.get(f"{API}/students/{data['id']}/progress", headers=headers).status_code == 404
    assert client.get(f"{API}/students", headers=headers).json() == []
    assert client.get(f"{API}/classrooms/{data['classroom_id']}/students", headers=headers).status_code == 403


def test_guardian_isolation(client, student, guardian):
    data, _ = student
    _, g_headers = guardian
    assert client.get(f"{API}/students/{data['id']}", headers=g_headers).status_code == 404
    assert client.patch(f"{API}/students/{data['id']}", headers=g_headers, json={"age": 7}).status_code == 404


def test_admin_cannot_deactivate_self(client):
    admin = make_user(RoleCode.ADMIN)
    headers = login(client, admin.username)
    assert client.delete(f"{API}/users/{admin.id}", headers=headers).status_code == 403


def test_deactivated_user_cannot_login(client, admin_headers):
    user = make_user(RoleCode.GUARDIAN)
    assert client.delete(f"{API}/users/{user.id}", headers=admin_headers).json()["is_active"] is False
    res = client.post(f"{API}/auth/login", json={"username": user.username, "password": "Clave12345"})
    assert res.status_code == 401
