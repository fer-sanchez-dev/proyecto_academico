# Etapa de build
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .

# Instalar dependencias del sistema para compilar
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Actualizar pip
RUN pip install --upgrade pip

# 👇 CAMBIO CRÍTICO: Quitar --no-deps para incluir todas las dependencias
RUN pip wheel --wheel-dir /wheels -r requirements.txt

# ===================================================
# Etapa final
# ===================================================
FROM python:3.11-slim

WORKDIR /app

# Crear usuario sin privilegios
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Instalar dependencias del sistema en runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    netcat-traditional \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar wheels y requirements
COPY --from=builder /wheels /wheels
COPY requirements.txt .

# Instalar desde wheels (sin hash checking)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt

# Copiar código fuente
COPY . .

# Crear directorios necesarios y asignar permisos
RUN mkdir -p /app/logs /vol/static /vol/media && \
    touch /app/logs/django.log && \
    chown -R appuser:appgroup /app /vol

# Cambiar a usuario no-root
USER appuser

EXPOSE 8000

# Entrypoint y comando
ENTRYPOINT ["bash", "entrypoint.sh"]
CMD ["gunicorn", "proyecto_academico.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]