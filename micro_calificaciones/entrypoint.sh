#!/usr/bin/env bash
set -e

host="${CALIFICACIONES_DB_HOST:-db_calificaciones}"
port="${CALIFICACIONES_DB_PORT:-5432}"

echo "⏳ Esperando a la base de datos en $host:$port..."

until nc -z "$host" "$port"; do
  echo "❌ Base de datos no disponible aún..."
  sleep 2
done

echo "✅ Base de datos lista!"

# Aplicar migraciones
echo "🚀 Aplicando migraciones..."
python manage.py migrate --noinput

# Iniciar servidor
echo "🏁 Iniciando microservicio Calificaciones..."
python manage.py runserver 0.0.0.0:8001
