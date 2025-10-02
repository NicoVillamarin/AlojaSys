FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
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