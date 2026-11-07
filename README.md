# V&E Academy

Aplicación educativa para fortalecer la **comprensión lectora** (literal, inferencial y crítica) en niños de **primer grado** (6-7 años). Combina lecturas cortas graduadas, juegos de sílabas, rimas y palabras, y retroalimentación inmediata. La gamificación se basa en el progreso individual, sin comparaciones entre niños. Docentes y acudientes cuentan con reportes de progreso.

Basada en el proyecto integrador *"Prototipo de aplicación educativa para el fortalecimiento de la comprensión lectora en estudiantes de primer grado de una institución educativa urbana"* (Valery Michell Sossa Perdomo y Emanuel Velázquez Pineda, Universidad de Cundinamarca, 2025).

| | |
|---|---|
| Frontend | Angular 19 · TypeScript · componentes standalone · formularios reactivos · guards · interceptores |
| Backend | Python 3.12 · FastAPI · SQLAlchemy 2.0 · Pydantic v2 · Alembic · JWT · Argon2 |
| Base de datos | PostgreSQL 16 |
| Infraestructura | Docker · Docker Compose · nginx |
| Pruebas | pytest (contra PostgreSQL real) · Karma/Jasmine · Playwright (E2E) |

## Contenido

1. [Objetivos](#objetivos)
2. [Funcionalidades](#funcionalidades)
3. [Arquitectura](#arquitectura)
4. [Requisitos previos](#requisitos-previos)
5. [Instalación y ejecución con Docker](#instalación-y-ejecución-con-docker)
6. [Variables de entorno](#variables-de-entorno)
7. [Acceso a la aplicación](#acceso-a-la-aplicación)
8. [Desarrollo local sin Docker](#desarrollo-local-sin-docker)
9. [Migraciones](#migraciones)
10. [Pruebas](#pruebas)
11. [Estructura de carpetas](#estructura-de-carpetas)
12. [Solución de errores frecuentes](#solución-de-errores-frecuentes)
13. [Propuesta futura: V&E AI Companion](#propuesta-futura-ve-ai-companion)
14. [Estado de la verificación](#estado-de-la-verificación)

Documentación detallada en [`docs/`](docs):
[análisis de requerimientos](docs/01-analisis-requerimientos.md) ·
[arquitectura](docs/02-arquitectura.md) ·
[modelo de datos](docs/03-modelo-datos.md) ·
[API](docs/04-api.md) ·
[AI Companion](docs/05-ai-companion.md)

## Objetivos

**General** (del documento): diseñar un software educativo que fortalezca la comprensión lectora en niños de primer grado mediante una interfaz interactiva y atractiva.

**Específicos de esta versión:**

- Ofrecer lecturas graduadas y actividades de conciencia fonológica, reconocimiento de palabras y comprensión en sus tres niveles.
- Dar retroalimentación inmediata como andamiaje (zona de desarrollo próximo de Vygotsky): pista, luego explicación y nunca castigo.
- Motivar con puntos, niveles, insignias, retos y avatares, sin rankings.
- Entregar a docentes y acudientes información útil y comprensible del progreso.
- Proteger los datos de los menores.

## Funcionalidades

**Estudiante**
- Inicio personalizado con la mascota Lumi, su nivel, retos y sugerencias.
- Biblioteca con filtros por nivel y temática. Lector sobre **cuaderno doble línea**: cada palabra se puede tocar para escucharla y cada párrafo tiene botón de audio.
- 8 tipos de actividad: sílabas (directas e inversas), reconocer palabras, imagen y palabra, completar palabras, formar oraciones, ordenar secuencias, rimas y comprensión de textos.
- Retroalimentación inmediata: pista tras el 1.er error; respuesta y explicación tras el 2.º.
- Resultado con estrellas, puntos, nuevas insignias, subida de nivel y actividades de refuerzo.
- Mis logros: insignias con progreso, retos, avatares y stickers desbloqueables, y "Mi avance".

**Docente**: aulas, alta de estudiantes, reporte por estudiante (habilidades, actividad semanal, historial de intentos y lecturas, insignias), estadísticas por aula, código de vinculación para acudientes y restablecimiento de contraseñas.

**Acudiente**: crear la cuenta de su niño o vincularse con el código del docente, y ver el mismo reporte de progreso.

**Administrador**: estadísticas generales, gestión de usuarios (alta, activación, contraseñas), CRUD de lecturas (con párrafos), actividades (con preguntas y opciones), categorías, insignias y retos, y estado del AI Companion.

Las lecturas incluidas son **8 cuentos originales** escritos para el proyecto, entre ellos uno ambientado en el río Magdalena. También hay **17 actividades**.

## Arquitectura

```
Navegador ──► frontend (nginx: SPA + proxy /api) ──► backend (FastAPI) ──► db (PostgreSQL)
                                                          └─ ai_companion (interfaz; sin proveedor conectado)
```

El backend está organizado por capas: `routers → services → repositories → models`, con `schemas` (Pydantic) y `core` (configuración, seguridad y errores). El frontend está organizado por funcionalidad: `core`, `shared` y `features/{auth,student,adult,admin}`, con carga diferida. El detalle está en [docs/02-arquitectura.md](docs/02-arquitectura.md).

## Requisitos previos

- **Docker Desktop** (Windows/macOS) o Docker Engine con el plugin **Compose v2** (`docker compose version`).
- Puertos libres: `4200` (frontend), `8000` (API) y `5432` (PostgreSQL, solo local).
- Para desarrollo sin Docker: Python 3.12+, Node.js 20.19+ o 22, y PostgreSQL 15+.

## Instalación y ejecución con Docker

```bash
git clone <url-del-repositorio> ve-academy && cd ve-academy
cp .env.example .env
# Edita .env: cambia POSTGRES_PASSWORD, JWT_SECRET_KEY y ADMIN_PASSWORD.
# Para generar una clave segura:
python -c "import secrets; print(secrets.token_urlsafe(48))"

docker compose up --build
```

Al iniciar, el backend **aplica las migraciones** (`alembic upgrade head`) y **carga los datos iniciales** de forma idempotente. El frontend arranca cuando el backend está saludable (healthcheck).

| Acción | Comando |
|--------|---------|
| Iniciar en segundo plano | `docker compose up -d --build` |
| Ver estado y salud | `docker compose ps` |
| Ver logs (todos / uno) | `docker compose logs -f` · `docker compose logs -f backend` |
| Detener | `docker compose stop` |
| Reiniciar un servicio | `docker compose restart backend` |
| Detener y eliminar contenedores | `docker compose down` |
| Borrar también la base de datos | `docker compose down -v` ⚠️ elimina todos los datos |
| Consola de PostgreSQL | `docker compose exec db psql -U ve_user -d ve_academy` |
| pgAdmin (opcional) | `docker compose --profile tools up -d pgadmin` → <http://localhost:5050> (host `db`, puerto `5432`) |

## Variables de entorno

Todas están documentadas en [`.env.example`](.env.example). Las más importantes:

| Variable | Descripción |
|----------|-------------|
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Credenciales de la base de datos (la contraseña es obligatoria) |
| `JWT_SECRET_KEY` | Clave para firmar los tokens (obligatoria, mínimo 32 caracteres; se rechaza el valor de ejemplo) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duración de la sesión (120 por defecto) |
| `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Administrador inicial (se crea si no existe) |
| `SEED_CONTENT` | Carga lecturas y actividades iniciales |
| `SEED_DEMO_USERS` | Crea usuarios de demostración. **Solo para desarrollo** |
| `SMTP_*` | Correo para recuperar contraseñas (opcional) |
| `CORS_ORIGINS` | Orígenes permitidos si el frontend se sirve desde otro dominio |
| `BACKEND_INSTALL_DEV` | Incluye pytest en la imagen del backend |

## Acceso a la aplicación

| Servicio | URL |
|----------|-----|
| Aplicación (Angular) | <http://localhost:4200> |
| API | <http://localhost:8000/api/v1> |
| Swagger UI | <http://localhost:8000/docs> |
| ReDoc | <http://localhost:8000/redoc> |
| Healthcheck | <http://localhost:8000/api/v1/health> |
| PostgreSQL | `localhost:5432` (solo desde este equipo) |

Con `SEED_DEMO_USERS=true` se crean estas cuentas (sin progreso inventado; el progreso solo se genera usando la app):

| Rol | Usuario | Contraseña |
|-----|---------|-----------|
| Administrador | `admin` (o tu `ADMIN_USERNAME`) | tu `ADMIN_PASSWORD` |
| Docente | `docente.demo` | `Docente123` |
| Acudiente | `acudiente.demo` | `Acudiente123` |
| Estudiante (aula "Primero A", vinculada al acudiente) | `sofia.demo` | `lectura1` |
| Estudiante | `mateo.demo` | `lectura1` |

En Swagger, pulsa **Authorize** e ingresa usuario y contraseña (flujo OAuth2 *password*).

## Desarrollo local sin Docker

```bash
# Base de datos (ejemplo con un PostgreSQL local)
createuser ve_user -P && createdb ve_academy -O ve_user && createdb ve_academy_test -O ve_user

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp ../.env.example .env   # y ajusta DATABASE_URL=postgresql+psycopg://ve_user:<clave>@localhost:5432/ve_academy
alembic upgrade head && python -m app.seed.run
uvicorn app.main:app --reload --port 8000

# Frontend (otra terminal). proxy.conf.json envía /api a localhost:8000
cd frontend && npm install && npm start      # http://localhost:4200
```

## Migraciones

```bash
# Dentro de Docker
docker compose exec backend alembic current
docker compose exec backend alembic upgrade head
docker compose exec backend alembic downgrade -1

# Crear una migración tras cambiar app/models (desarrollo local)
cd backend && alembic revision --autogenerate -m "describe el cambio"
alembic check        # verifica que modelos y migraciones estén sincronizados
```

El DDL SQL generado a partir de las migraciones está en [`database/schema.sql`](database/schema.sql).

## Pruebas

| Suite | Qué cubre | Comando |
|-------|-----------|---------|
| Backend (47 pruebas) | Registro, login, bloqueo, logout con revocación, recuperación de contraseña; autorización por rol y aislamiento de menores; CRUD de usuarios, aulas, estudiantes, categorías, lecturas y actividades; validaciones; evaluación (selección y ordenamiento); reintentos y retroalimentación; puntos, insignias y retos; progreso y reportes; persistencia en PostgreSQL; migraciones; AI Companion desactivado y filtros | `docker compose exec backend pytest` |
| Frontend (13 pruebas) | Servicio de autenticación, guards, interceptores (token, 401, 403), mensajes de error, componentes compartidos | `cd frontend && npm run test:ci` (requiere Chrome/Chromium; usa `CHROME_BIN` si no está en el PATH) |
| E2E (6 recorridos) | Navegador real → Angular → API → PostgreSQL: el docente crea un estudiante, el niño lee y juega, el docente ve el progreso; aislamiento del acudiente; el administrador crea contenido; vista móvil sin desbordes | `pip install pytest playwright && playwright install chromium` y luego `E2E_BASE_URL=http://localhost:4200 E2E_ADMIN_PASSWORD=<clave> pytest e2e` (con `SEED_DEMO_USERS=true`) |

Las pruebas del backend usan una base de datos **separada** (`ve_academy_test`, creada por `database/init/`) y reconstruyen el esquema ejecutando las migraciones de Alembic.

## Estructura de carpetas

```
ve-academy/
├── backend/
│   ├── app/
│   │   ├── api/            dependencias (usuario actual, roles) y router principal
│   │   ├── core/           config, database, security, exceptions
│   │   ├── models/         entidades SQLAlchemy
│   │   ├── schemas/        modelos Pydantic (entrada/salida)
│   │   ├── repositories/   acceso a datos
│   │   ├── services/       lógica de negocio
│   │   ├── routers/        endpoints
│   │   ├── seed/           datos iniciales (lecturas y actividades originales)
│   │   ├── ai_companion/   contratos y filtros (propuesta futura)
│   │   └── main.py
│   ├── alembic/  tests/  Dockerfile  docker-entrypoint.sh  requirements.txt  requirements-dev.txt
├── frontend/
│   ├── src/app/{core,shared,features}/   src/styles.scss (sistema visual)
│   ├── public/  angular.json  package.json  karma.conf.js  proxy.conf.json  nginx.conf  Dockerfile
├── database/   init/ (base de pruebas) · schema.sql
├── e2e/        test_e2e.py
├── docs/       análisis · arquitectura · modelo de datos (+ modelo-er.svg) · API · AI Companion
├── docker-compose.yml  .env.example  .gitignore  README.md
```

## Solución de errores frecuentes

| Síntoma | Causa y solución |
|---------|------------------|
| `required variable POSTGRES_PASSWORD is missing` | Falta `.env`. Ejecuta `cp .env.example .env` y define los valores |
| El backend se reinicia con `JWT_SECRET_KEY usa el valor de ejemplo` | Genera una clave real (ver Instalación) |
| `port is already allocated` | Cambia `FRONTEND_PORT`, `BACKEND_PORT` o `POSTGRES_PORT` en `.env`, o detén el servicio que ocupa el puerto |
| `password authentication failed for user "ve_user"` | Cambiaste `POSTGRES_PASSWORD` después de crear el volumen. PostgreSQL solo la toma la primera vez: vuelve a la clave anterior o recrea el volumen con `docker compose down -v` (borra los datos) |
| Las pruebas fallan con `database "ve_academy_test" does not exist` | El volumen se creó antes de existir `database/init`. Ejecuta `docker compose exec db createdb -U ve_user ve_academy_test` |
| El frontend muestra "No hay conexión con el servidor" | Revisa `docker compose ps` (backend `healthy`) y `docker compose logs backend` |
| El usuario administrador no existe | `ADMIN_PASSWORD` estaba vacío en el primer arranque. Defínelo y ejecuta `docker compose restart backend` |
| "Demasiados intentos fallidos" | Bloqueo de 10 minutos tras 5 errores. Un adulto o el administrador puede restablecer la contraseña |
| No se escucha el audio | La síntesis de voz depende del navegador y del sistema operativo; instala una voz en español (Windows: Configuración → Hora e idioma → Voz) |
| Recuperar contraseña dice "no está habilitada" | Configura las variables `SMTP_*` o pide al administrador que la restablezca |

## Propuesta futura: V&E AI Companion

> **No hace parte de los requerimientos originales** y **no hay IA conectada** en esta versión.

*Mi compañero de aprendizaje* sería un acompañante (Lumi) que explica palabras, da pistas sin revelar las respuestas, felicita y recomienda refuerzos, siempre bajo la supervisión de docentes y acudientes. Lo que ya está en el código:

- Contratos de integración (`CompanionProvider`).
- Un proveedor desactivado que **no simula respuestas**.
- Filtros deterministas de datos personales y temas no permitidos, con pruebas.
- El endpoint `GET /api/v1/ai-companion/status`.

Endpoints futuros, modelo de datos, flujo, consideraciones de seguridad para menores (consentimiento, minimización, supervisión, sin diagnósticos) y proveedores posibles: **[docs/05-ai-companion.md](docs/05-ai-companion.md)**.

## Estado de la verificación

Verificado en el entorno de desarrollo:

- ✅ 47 pruebas de backend contra PostgreSQL 16 real, con el esquema creado por las migraciones; `alembic check` sin diferencias.
- ✅ 13 pruebas unitarias de Angular en Chrome sin interfaz; compilación de producción sin errores.
- ✅ 6 recorridos E2E con Playwright contra el servidor de desarrollo **y** contra la compilación de producción servida con el mismo `nginx.conf` del contenedor (proxy `/api`, rutas profundas de la SPA, encabezados de seguridad).
- ✅ `docker-entrypoint.sh` (migraciones, datos iniciales y arranque) ejecutado sobre una base vacía.
- ✅ `docker compose config` válido.
- ⚠️ El comando completo `docker compose up --build` **no se pudo ejecutar** en el entorno donde se construyó el proyecto, porque ese entorno no tiene acceso a Docker Hub para descargar las imágenes base (`python:3.12-slim`, `node:22-alpine`, `nginx:1.27-alpine`, `postgres:16-alpine`). Cada pieza que ejecutan los contenedores se probó por separado (ver arriba). Se recomienda ejecutarlo una vez en tu equipo como verificación final.

---

Proyecto académico, Universidad de Cundinamarca. El contenido educativo (lecturas, actividades e ilustraciones de la mascota) es original.
