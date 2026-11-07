#!/bin/sh
# Aplica migraciones y carga los datos iniciales (idempotente) antes de iniciar la API.
set -e
echo "[entrypoint] Aplicando migraciones de base de datos..."
alembic upgrade head
echo "[entrypoint] Cargando datos iniciales..."
python -m app.seed.run
echo "[entrypoint] Iniciando: $*"
exec "$@"
