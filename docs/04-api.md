# API REST (`/api/v1`)

La documentación interactiva se genera automáticamente:

- Swagger UI: <http://localhost:8000/docs> (botón **Authorize**: usuario y contraseña).
- ReDoc: <http://localhost:8000/redoc>
- OpenAPI: <http://localhost:8000/api/v1/openapi.json>

Formato de error único:

```json
{ "error": { "code": "validation_error", "message": "Los datos enviados no son válidos.", "details": [{ "field": "username", "message": "..." }] } }
```

Códigos: `400` regla de negocio, `401` sin sesión, `403` rol sin permiso, `404` no existe o no es visible, `409` conflicto, `422` validación, `429` bloqueo por intentos, `503` servicio no disponible.

| Grupo | Método y ruta | Roles |
|-------|---------------|-------|
| Sistema | `GET /health` · `GET /ai-companion/status` | público · autenticado |
| Auth | `POST /auth/login` · `POST /auth/token` · `POST /auth/register` · `POST /auth/logout` · `GET/PATCH /auth/me` · `POST /auth/change-password` · `POST /auth/password-reset/request` · `POST /auth/password-reset/confirm` | — |
| Usuarios | `GET/POST /users` · `GET/PATCH/DELETE /users/{id}` · `POST /users/{id}/reset-password` | admin |
| Aulas | `GET/POST /classrooms` · `GET/PATCH/DELETE /classrooms/{id}` · `GET /classrooms/{id}/students` · `GET /classrooms/{id}/stats` | admin, docente (las suyas) |
| Estudiantes | `GET/POST /students` · `GET/PATCH /students/{id}` · `POST /students/{id}/reset-password` · `GET /students/{id}/progress\|attempts\|readings\|badges` | admin, docente, acudiente (solo los asociados) |
| Vinculación | `POST /students/{id}/link-code` (admin, docente) · `POST /students/link` (acudiente) | — |
| Estudiante | `GET /me/dashboard\|profile\|progress\|attempts\|readings\|badges\|challenges\|rewards\|points` · `PATCH /me/avatar` | estudiante |
| Categorías | `GET` (todos) · `POST/PATCH/DELETE` | admin |
| Lecturas | `GET /readings?difficulty&age&category_id&length&comprehension&q` · `GET /readings/{id}` · `POST/PUT/DELETE` (admin) · `POST /readings/{id}/sessions` · `POST /readings/sessions/{id}/complete` (estudiante) | — |
| Actividades | `GET /activities?activity_type&skill&difficulty&reading_id` · `GET /activities/{id}` · `GET /activities/{id}/admin` · `POST/PUT/DELETE` (admin) · `POST /activities/{id}/attempts` (estudiante) | — |
| Evaluación | `POST /attempts/{id}/answers` · `POST /attempts/{id}/finish` | estudiante (dueño del intento) |
| Gamificación | `GET /levels` · `GET/POST /badges` · `PUT /badges/{id}` · `GET/POST /challenges` · `PUT /challenges/{id}` | admin (niveles: todos) |
| Estadísticas | `GET /stats/overview` | admin |

En total son 73 operaciones. Ejemplo de flujo completo con `curl`:

```bash
TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' \
  -d '{"username":"sofia.demo","password":"lectura1"}' | jq -r .access_token)
A=$(curl -s -X POST localhost:8000/api/v1/activities/1/attempts -H "Authorization: Bearer $TOKEN" | jq .attempt_id)
curl -s -X POST localhost:8000/api/v1/attempts/$A/answers -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"question_id":1,"selected_option_id":2}'
```
