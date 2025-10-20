#!/usr/bin/env bash
set -e

host="${DATABASE_HOST:-db}"
port="${DATABASE_PORT:-5432}"

echo "🔄 Esperando a la base de datos en $host:$port..."

# Esperar a que la BD esté disponible
max_attempts=30
attempt=0

while ! nc -z "$host" "$port"; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo "❌ Error: No se pudo conectar a la base de datos después de $max_attempts intentos"
        exit 1
    fi
    echo "Intento $attempt/$max_attempts - Esperando..."
    sleep 2
done

echo "✅ Base de datos disponible"

# Verificar permisos del archivo de log (ya debe existir por el Dockerfile)
if [ ! -w /app/logs/django.log ]; then
    echo "⚠️  Advertencia: No se puede escribir en /app/logs/django.log"
fi

# Ejecutar migraciones
echo "🔄 Ejecutando migraciones..."
if python manage.py migrate --noinput; then
    echo "✅ Migraciones completadas"
else
    echo "❌ Error al ejecutar migraciones"
    exit 1
fi

# Recolectar archivos estáticos
echo "🔄 Recolectando archivos estáticos..."
if python manage.py collectstatic --noinput --clear; then
    echo "✅ Archivos estáticos recolectados"
else
    echo "⚠️  Advertencia: Error al recolectar archivos estáticos (puede ser normal si no hay archivos)"
fi

echo "🚀 Iniciando aplicación..."
exec "$@"
