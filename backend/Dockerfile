FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    libcairo2 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu \
    libharfbuzz0b \
    libfribidi0 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxcb1 \
    libxau6 \
    libxdmcp6 \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Recopilar estáticos para producción
RUN python manage.py collectstatic --noinput || true

# Exponer puerto
EXPOSE 8000

# Comando por defecto
# Ejecutar migraciones y servir con gunicorn (Render usa $PORT)
CMD ["bash", "-lc", "python manage.py migrate --noinput && gunicorn hotel.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3"]