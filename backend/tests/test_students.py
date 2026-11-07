"""Aulas, cuentas de estudiantes, vinculación de acudientes y gestión de usuarios."""

from .conftest import API, login


def test_classroom_crud(client, teacher):
    _, headers = teacher
    res = client.post(f"{API}/classrooms", headers=headers, json={"name": "Primero B", "school_year": 2026})
    assert res.status_code == 201
    cid = res.json()["id"]
    assert client.patch(f"{API}/classrooms/{cid}", headers=headers, json={"name": "Primero C"}).json()["name"] == "Primero C"
    assert [c["name"] for c in client.get(f"{API}/classrooms", headers=headers).json()] == ["Primero C"]
    assert client.delete(f"{API}/classrooms/{cid}", headers=headers).status_code == 204
    assert client.get(f"{API}/classrooms/{cid}", headers=headers).status_code == 404


def test_classroom_with_students_cannot_be_deleted(client, teacher, student):
    _, headers = teacher
    data, _ = student
    assert client.delete(f"{API}/classrooms/{data['classroom_id']}", headers=headers).status_code == 409


def test_teacher_creates_student_and_student_logs_in(client, teacher, student):
    data, s_headers = student
    assert data["display_name"] == "Sofía" and data["total_points"] == 0 and data["level_number"] == 1
    me = client.get(f"{API}/auth/me", headers=s_headers).json()
    assert me["role"] == "student" and me["email"] is None  # minimización de datos
    _, t_headers = teacher
    assert len(client.get(f"{API}/students", headers=t_headers).json()) == 1


def test_teacher_must_choose_own_classroom(client, teacher):
    _, headers = teacher
    res = client.post(f"{API}/students", headers=headers, json={"display_name": "Juan", "username": "juan.x", "password": "lectura1"})
    assert res.status_code == 409


def test_guardian_creates_child(client, guardian):
    _, headers = guardian
    res = client.post(f"{API}/students", headers=headers, json={
        "display_name": "Mateo", "username": "mateo.g", "password": "lectura1", "relationship_label": "Padre"})
    assert res.status_code == 201
    assert res.json()["classroom_id"] is None and len(res.json()["guardian_names"]) == 1
    assert len(client.get(f"{API}/students", headers=headers).json()) == 1


def test_link_code_flow(client, teacher, student, guardian):
    data, _ = student
    _, t_headers = teacher
    _, g_headers = guardian
    code = client.post(f"{API}/students/{data['id']}/link-code", headers=t_headers).json()["code"]
    res = client.post(f"{API}/students/link", headers=g_headers, json={"code": code.lower(), "relationship_label": "Madre"})
    assert res.status_code == 200 and res.json()["id"] == data["id"]
    assert client.get(f"{API}/students/{data['id']}/progress", headers=g_headers).status_code == 200
    # Un solo uso
    assert client.post(f"{API}/students/link", headers=g_headers, json={"code": code}).status_code == 404


def test_reset_student_password_and_update(client, teacher, student):
    data, _ = student
    _, headers = teacher
    assert client.post(f"{API}/students/{data['id']}/reset-password", headers=headers, json={"new_password": "nueva1"}).status_code == 200
    login(client, data["username"], "nueva1")
    res = client.patch(f"{API}/students/{data['id']}", headers=headers, json={"display_name": "Sofi", "age": 7})
    assert res.json()["display_name"] == "Sofi" and res.json()["age"] == 7


def test_avatar_must_be_unlocked(client, student):
    _, headers = student
    assert client.patch(f"{API}/me/avatar", headers=headers, json={"avatar": "dragon"}).status_code == 403
    assert client.patch(f"{API}/me/avatar", headers=headers, json={"avatar": "cat"}).json()["avatar"] == "cat"
    rewards = client.get(f"{API}/me/rewards", headers=headers).json()
    assert any(r["code"] == "cat" and r["unlocked"] for r in rewards)
    assert any(r["code"] == "dragon" and not r["unlocked"] for r in rewards)


def test_admin_user_management(client, admin_headers):
    res = client.post(f"{API}/users", headers=admin_headers, json={
        "full_name": "Docente Nuevo", "username": "doc.nuevo", "email": "doc@n.co", "password": "Clave12345", "role": "teacher"})
    assert res.status_code == 201
    uid = res.json()["id"]
    page = client.get(f"{API}/users", headers=admin_headers, params={"role": "teacher", "q": "nuevo"}).json()
    assert page["total"] == 1
    assert client.patch(f"{API}/users/{uid}", headers=admin_headers, json={"full_name": "Docente Editado"}).json()["full_name"] == "Docente Editado"
    assert client.post(f"{API}/users/{uid}/reset-password", headers=admin_headers, json={"new_password": "Otra12345"}).status_code == 200
    login(client, "doc.nuevo", "Otra12345")
