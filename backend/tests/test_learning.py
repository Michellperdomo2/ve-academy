"""Evaluación de respuestas, registro de resultados, gamificación y progreso."""

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.models import Attempt, AttemptAnswer, PointTransaction

from .conftest import API

ADMIN_ACTIVITY = {
    "title": "Orden y rima", "activity_type": "sentence_building", "skill": "sentence_building", "difficulty": 1,
    "instructions": "Resuelve.", "points_reward": 20,
    "questions": [
        {"prompt": "¿Qué rima con SOL?", "skill": "phonological_awareness", "hint": "Termina en -ol",
         "explanation": "SOL y COL.", "options": [{"text": "Mar"}, {"text": "Col", "is_correct": True}]},
        {"prompt": "Ordena", "question_type": "ordering", "skill": "sentence_building", "explanation": "Yo leo mucho.",
         "options": [{"text": "mucho", "correct_position": 3}, {"text": "Yo", "correct_position": 1},
                     {"text": "leo", "correct_position": 2}]},
    ],
}


def _admin_activity(client, admin_headers):
    return client.post(f"{API}/activities", headers=admin_headers, json=ADMIN_ACTIVITY).json()


def _ids(activity):
    q1, q2 = activity["questions"]
    correct = next(o["id"] for o in q1["options"] if o["is_correct"])
    wrong = next(o["id"] for o in q1["options"] if not o["is_correct"])
    order = [o["id"] for o in sorted(q2["options"], key=lambda o: o["correct_position"])]
    return q1["id"], correct, wrong, q2["id"], order


def test_perfect_attempt_awards_points_badges_and_records(client, admin_headers, student):
    _, headers = student
    act = _admin_activity(client, admin_headers)
    q1, correct, _, q2, order = _ids(act)
    attempt = client.post(f"{API}/activities/{act['id']}/attempts", headers=headers).json()
    aid = attempt["attempt_id"]
    assert attempt["attempt_number"] == 1 and attempt["total_questions"] == 2

    fb = client.post(f"{API}/attempts/{aid}/answers", headers=headers, json={"question_id": q1, "selected_option_id": correct}).json()
    assert fb["is_correct"] and fb["explanation"] == "SOL y COL." and not fb["can_retry"]
    fb = client.post(f"{API}/attempts/{aid}/answers", headers=headers, json={"question_id": q2, "ordered_option_ids": order}).json()
    assert fb["is_correct"]

    result = client.post(f"{API}/attempts/{aid}/finish", headers=headers).json()
    assert result["score"] == 100 and result["stars"] == 3 and result["points_awarded"] == 20
    assert "estrella_perfecta" in {b["code"] for b in result["new_badges"]}
    # Puntos = actividad (20) + bono de insignia (5)
    assert client.get(f"{API}/me/profile", headers=headers).json()["total_points"] == 25

    with SessionLocal() as db:  # persistencia real en PostgreSQL
        assert db.scalar(select(func.count(AttemptAnswer.id)).where(AttemptAnswer.attempt_id == aid)) == 2
        assert db.get(Attempt, aid).status.value == "completed"

    # Repetir la actividad no vuelve a dar los mismos puntos (solo se premia la mejora)
    aid2 = client.post(f"{API}/activities/{act['id']}/attempts", headers=headers).json()["attempt_id"]
    client.post(f"{API}/attempts/{aid2}/answers", headers=headers, json={"question_id": q1, "selected_option_id": correct})
    client.post(f"{API}/attempts/{aid2}/answers", headers=headers, json={"question_id": q2, "ordered_option_ids": order})
    assert client.post(f"{API}/attempts/{aid2}/finish", headers=headers).json()["points_awarded"] == 0


def test_feedback_hint_then_reveal(client, admin_headers, student):
    _, headers = student
    act = _admin_activity(client, admin_headers)
    q1, correct, wrong, q2, order = _ids(act)
    aid = client.post(f"{API}/activities/{act['id']}/attempts", headers=headers).json()["attempt_id"]

    fb1 = client.post(f"{API}/attempts/{aid}/answers", headers=headers, json={"question_id": q1, "selected_option_id": wrong}).json()
    assert not fb1["is_correct"] and fb1["can_retry"] and fb1["hint"] == "Termina en -ol" and fb1["correct_option_ids"] is None
    fb2 = client.post(f"{API}/attempts/{aid}/answers", headers=headers, json={"question_id": q1, "selected_option_id": wrong}).json()
    assert not fb2["can_retry"] and fb2["correct_option_ids"] == [correct] and fb2["explanation"]
    assert client.post(f"{API}/attempts/{aid}/answers", headers=headers,
                       json={"question_id": q1, "selected_option_id": correct}).status_code == 409

    # Faltan preguntas: no se puede terminar
    res = client.post(f"{API}/attempts/{aid}/finish", headers=headers)
    assert res.status_code == 409 and res.json()["error"]["details"]["missing_positions"] == [2]

    client.post(f"{API}/attempts/{aid}/answers", headers=headers, json={"question_id": q2, "ordered_option_ids": order})
    result = client.post(f"{API}/attempts/{aid}/finish", headers=headers).json()
    assert result["score"] == 50 and result["points_awarded"] == 10 and result["stars"] == 1
    assert result["recommendations"], "Debe recomendar refuerzo cuando el puntaje es bajo"

    history = client.get(f"{API}/me/attempts", headers=headers).json()
    assert history[0]["total_tries"] == 3 and history[0]["correct_first_try"] == 1


def test_ordering_and_invalid_answers(client, admin_headers, student):
    _, headers = student
    act = _admin_activity(client, admin_headers)
    q1, _, _, q2, order = _ids(act)
    aid = client.post(f"{API}/activities/{act['id']}/attempts", headers=headers).json()["attempt_id"]
    # Orden incompleto u opción ajena -> 400
    assert client.post(f"{API}/attempts/{aid}/answers", headers=headers, json={"question_id": q2, "ordered_option_ids": order[:2]}).status_code == 400
    assert client.post(f"{API}/attempts/{aid}/answers", headers=headers, json={"question_id": q1, "selected_option_id": order[0]}).status_code == 400
    # Ni las dos ni ninguna respuesta -> 422
    assert client.post(f"{API}/attempts/{aid}/answers", headers=headers, json={"question_id": q1}).status_code == 422
    wrong_order = list(reversed(order))
    fb = client.post(f"{API}/attempts/{aid}/answers", headers=headers, json={"question_id": q2, "ordered_option_ids": wrong_order}).json()
    assert fb["is_correct"] is False and fb["can_retry"]


def test_attempt_belongs_to_student(client, admin_headers, student, teacher, classroom):
    _, headers = student
    act = _admin_activity(client, admin_headers)
    aid = client.post(f"{API}/activities/{act['id']}/attempts", headers=headers).json()["attempt_id"]
    _, t_headers = teacher
    res = client.post(f"{API}/students", headers=t_headers, json={
        "display_name": "Otro", "username": "otro.nino", "password": "lectura1", "classroom_id": classroom["id"]})
    other = client.post(f"{API}/auth/login", json={"username": "otro.nino", "password": "lectura1"}).json()["access_token"]
    assert res.status_code == 201
    assert client.post(f"{API}/attempts/{aid}/finish", headers={"Authorization": f"Bearer {other}"}).status_code == 404


def test_reading_completion_points_and_challenge(client, student):
    _, headers = student
    for reading_id in (1, 2, 3):
        sid = client.post(f"{API}/readings/{reading_id}/sessions", headers=headers).json()["id"]
        result = client.post(f"{API}/readings/sessions/{sid}/complete", headers=headers).json()
        assert result["first_time"] and result["points_awarded"] == 10 and result["next_activity_id"]
    assert "Tres cuentos" in {c["title"] for c in result["completed_challenges"]}
    sid = client.post(f"{API}/readings/1/sessions", headers=headers).json()["id"]
    reread = client.post(f"{API}/readings/sessions/{sid}/complete", headers=headers).json()
    assert reread["points_awarded"] == 2 and not reread["first_time"]
    assert client.post(f"{API}/readings/sessions/{sid}/complete", headers=headers).status_code == 409

    challenges = client.get(f"{API}/me/challenges", headers=headers).json()
    assert next(c for c in challenges if c["challenge"]["title"] == "Tres cuentos")["completed"]
    history = client.get(f"{API}/me/readings", headers=headers).json()
    assert len(history) == 4
    with SessionLocal() as db:
        total = db.scalar(select(func.sum(PointTransaction.amount)))
    # 3 lecturas (30) + relectura (2) + insignia primer cuento (5) + reto tres cuentos (15)
    assert total == 52
    assert client.get(f"{API}/me/readings", headers=headers).json()[0]["reading_title"] == "El gato Tito"


def test_progress_updates_and_reports(client, admin_headers, student, teacher, classroom):
    data, headers = student
    act = _admin_activity(client, admin_headers)
    q1, _, wrong, q2, order = _ids(act)
    aid = client.post(f"{API}/activities/{act['id']}/attempts", headers=headers).json()["attempt_id"]
    client.post(f"{API}/attempts/{aid}/answers", headers=headers, json={"question_id": q1, "selected_option_id": wrong})
    client.post(f"{API}/attempts/{aid}/answers", headers=headers, json={"question_id": q1, "selected_option_id": wrong})
    client.post(f"{API}/attempts/{aid}/answers", headers=headers, json={"question_id": q2, "ordered_option_ids": order})
    client.post(f"{API}/attempts/{aid}/finish", headers=headers)
    sid = client.post(f"{API}/readings/1/sessions", headers=headers).json()["id"]
    client.post(f"{API}/readings/sessions/{sid}/complete", headers=headers)

    progress = client.get(f"{API}/me/progress", headers=headers).json()
    assert progress["readings_completed"] == 1 and progress["activities_completed"] == 1
    assert progress["total_answers"] == 3 and progress["correct_answers"] == 1 and progress["incorrect_answers"] == 2
    assert progress["average_score"] == 50.0 and 0 < progress["progress_percent"] < 100
    skills = {s["skill"]: s for s in progress["skills"]}
    assert skills["phonological_awareness"]["accuracy"] == 0 and skills["sentence_building"]["accuracy"] == 100
    assert sum(d["readings"] for d in progress["weekly_activity"]) == 1

    _, t_headers = teacher
    report = client.get(f"{API}/students/{data['id']}/progress", headers=t_headers).json()
    assert report["total_points"] == progress["total_points"]
    stats = client.get(f"{API}/classrooms/{classroom['id']}/stats", headers=t_headers).json()
    assert stats["student_count"] == 1 and stats["students"][0]["activities_completed"] == 1
    assert client.get(f"{API}/students/{data['id']}/attempts", headers=t_headers).json()[0]["score"] == 50.0

    dashboard = client.get(f"{API}/me/dashboard", headers=headers).json()
    assert dashboard["greeting"].endswith("Sofía!") and dashboard["progress"]["total_points"] == progress["total_points"]

    overview = client.get(f"{API}/stats/overview", headers=admin_headers).json()
    assert overview["attempts_completed"] == 1 and overview["ai_companion_enabled"] is False


def test_seeded_comprehension_activity_has_three_levels(client, student):
    _, headers = student
    detail = client.get(f"{API}/readings/1", headers=headers).json()
    activity = client.get(f"{API}/activities/{detail['activity_ids'][0]}", headers=headers).json()
    assert {q["skill"] for q in activity["questions"]} == {"literal", "inferential", "critical"}
