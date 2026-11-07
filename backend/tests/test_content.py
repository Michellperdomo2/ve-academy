"""CRUD de categorías, lecturas y actividades; filtros del catálogo."""

from .conftest import API

NEW_READING = {
    "title": "El perro Max", "summary": "Max busca su hueso.", "category_id": 1, "difficulty": 1,
    "min_age": 6, "max_age": 7, "comprehension_focus": "literal", "cover_emoji": "🐶", "cover_color": "#FFD166",
    "paragraphs": [{"text": "Max es un perro.", "illustration": "🐶"}, {"text": "Max busca su hueso en el patio."}],
}

NEW_ACTIVITY = {
    "title": "Rimas nuevas", "activity_type": "rhymes", "skill": "phonological_awareness", "difficulty": 1,
    "instructions": "Toca la que rima.", "points_reward": 10,
    "questions": [
        {"prompt": "¿Qué rima con SOL?", "skill": "phonological_awareness", "explanation": "SOL y COL.",
         "options": [{"text": "Col", "is_correct": True}, {"text": "Mar"}]},
        {"prompt": "Ordena", "question_type": "ordering", "skill": "sentence_building", "explanation": "Yo leo.",
         "options": [{"text": "leo", "correct_position": 2}, {"text": "Yo", "correct_position": 1}]},
    ],
}


def test_seeded_catalog_is_available(client, student):
    _, headers = student
    page = client.get(f"{API}/readings", headers=headers).json()
    assert page["total"] == 8
    assert all(r["completed_by_me"] is False for r in page["items"])
    acts = client.get(f"{API}/activities", headers=headers).json()
    assert acts["total"] == 17
    types = {a["activity_type"] for a in acts["items"]}
    assert types == {"syllables", "word_recognition", "sentence_building", "image_word", "complete_word",
                     "sequence_order", "rhymes", "reading_comprehension"}


def test_reading_filters(client, student):
    _, headers = student
    get = lambda **p: client.get(f"{API}/readings", headers=headers, params=p).json()  # noqa: E731
    assert all(r["difficulty"] == 3 for r in get(difficulty=3)["items"])
    assert all(r["comprehension_focus"] == "critical" for r in get(comprehension="critical")["items"])
    assert all(r["length"] == "medium" for r in get(length="medium")["items"])
    assert get(age=8)["total"] < get(age=6)["total"]
    assert get(q="tito")["items"][0]["title"] == "El gato Tito"


def test_category_crud(client, admin_headers):
    res = client.post(f"{API}/categories", headers=admin_headers, json={"name": "Deportes", "icon": "⚽"})
    assert res.status_code == 201 and res.json()["slug"] == "deportes"
    cid = res.json()["id"]
    assert client.post(f"{API}/categories", headers=admin_headers, json={"name": "Deportes"}).status_code == 409
    assert client.patch(f"{API}/categories/{cid}", headers=admin_headers, json={"description": "Juegos"}).status_code == 200
    assert client.delete(f"{API}/categories/{cid}", headers=admin_headers).status_code == 204
    assert client.delete(f"{API}/categories/1", headers=admin_headers).status_code == 409  # tiene lecturas


def test_reading_crud_and_publication(client, admin_headers, student):
    _, s_headers = student
    res = client.post(f"{API}/readings", headers=admin_headers, json={**NEW_READING, "is_published": False})
    assert res.status_code == 201, res.text
    reading = res.json()
    assert reading["length"] == "short" and reading["word_count"] == 11 and len(reading["paragraphs"]) == 2
    # No publicada: invisible para el estudiante
    assert client.get(f"{API}/readings/{reading['id']}", headers=s_headers).status_code == 404
    res = client.put(f"{API}/readings/{reading['id']}", headers=admin_headers, json={**NEW_READING, "title": "Max y su hueso"})
    assert res.json()["title"] == "Max y su hueso" and res.json()["is_published"]
    assert client.get(f"{API}/readings/{reading['id']}", headers=s_headers).status_code == 200
    assert client.delete(f"{API}/readings/{reading['id']}", headers=admin_headers).status_code == 204
    assert client.get(f"{API}/readings/{reading['id']}", headers=admin_headers).status_code == 404


def test_reading_validation(client, admin_headers):
    bad = [{**NEW_READING, "difficulty": 5}, {**NEW_READING, "min_age": 8, "max_age": 6},
           {**NEW_READING, "paragraphs": []}, {**NEW_READING, "cover_color": "rojo"}]
    for payload in bad:
        assert client.post(f"{API}/readings", headers=admin_headers, json=payload).status_code == 422
    assert client.post(f"{API}/readings", headers=admin_headers, json={**NEW_READING, "category_id": 9999}).status_code == 404


def test_activity_crud_and_answer_secrecy(client, admin_headers, student):
    _, s_headers = student
    res = client.post(f"{API}/activities", headers=admin_headers, json=NEW_ACTIVITY)
    assert res.status_code == 201, res.text
    act = res.json()
    assert act["question_count"] == 2 and act["questions"][0]["options"][0]["is_correct"] is True
    public = client.get(f"{API}/activities/{act['id']}", headers=s_headers)
    assert "is_correct" not in public.text and "correct_position" not in public.text and "explanation" not in public.text
    res = client.put(f"{API}/activities/{act['id']}", headers=admin_headers, json={**NEW_ACTIVITY, "title": "Rimas 2"})
    assert res.json()["title"] == "Rimas 2"
    assert client.delete(f"{API}/activities/{act['id']}", headers=admin_headers).status_code == 204


def test_activity_validation(client, admin_headers):
    two_correct = {**NEW_ACTIVITY, "questions": [{**NEW_ACTIVITY["questions"][0], "options": [
        {"text": "a", "is_correct": True}, {"text": "b", "is_correct": True}]}]}
    bad_order = {**NEW_ACTIVITY, "questions": [{**NEW_ACTIVITY["questions"][1], "options": [
        {"text": "a", "correct_position": 1}, {"text": "b", "correct_position": 1}]}]}
    for payload in (two_correct, bad_order, {**NEW_ACTIVITY, "questions": []}, {**NEW_ACTIVITY, "points_reward": 0}):
        assert client.post(f"{API}/activities", headers=admin_headers, json=payload).status_code == 422


def test_activity_with_attempts_keeps_questions(client, admin_headers, student):
    _, s_headers = student
    act = client.post(f"{API}/activities", headers=admin_headers, json=NEW_ACTIVITY).json()
    client.post(f"{API}/activities/{act['id']}/attempts", headers=s_headers)
    changed = {**NEW_ACTIVITY, "questions": NEW_ACTIVITY["questions"][:1]}
    assert client.put(f"{API}/activities/{act['id']}", headers=admin_headers, json=changed).status_code == 409
    # Cambios de metadatos sí se permiten
    res = client.put(f"{API}/activities/{act['id']}", headers=admin_headers, json={**NEW_ACTIVITY, "is_published": False})
    assert res.status_code == 200 and res.json()["is_published"] is False
    assert client.delete(f"{API}/activities/{act['id']}", headers=admin_headers).status_code == 409
