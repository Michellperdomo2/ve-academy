#!/bin/sh
# Se ejecuta solo la primera vez que se crea el volumen de PostgreSQL.
# Crea una base de datos separada para las pruebas automatizadas (pytest).
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-SQL
  CREATE DATABASE ${POSTGRES_DB}_test OWNER ${POSTGRES_USER};
SQL
