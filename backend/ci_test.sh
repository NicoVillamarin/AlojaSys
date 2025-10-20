#!/bin/bash
# Script de CI para tests de integración de cancelación y refund

set -e  # Exit on any error

echo "🚀 Iniciando tests de integración de cancelación y refund..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con color
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    print_error "No se encontró manage.py. Ejecutar desde el directorio backend/"
    exit 1
fi

# Verificar que Python está disponible
if ! command -v python &> /dev/null; then
    print_error "Python no está instalado o no está en el PATH"
    exit 1
fi

# Verificar que pip está disponible
if ! command -v pip &> /dev/null; then
    print_error "pip no está instalado o no está en el PATH"
    exit 1
fi

print_status "Instalando dependencias de test..."

# Instalar dependencias de test
if [ -f "requirements-test.txt" ]; then
    pip install -r requirements-test.txt
else
    print_warning "No se encontró requirements-test.txt, instalando dependencias básicas..."
    pip install pytest pytest-django factory-boy
fi

# Instalar dependencias del proyecto
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

print_status "Configurando base de datos de test..."

# Configurar variables de entorno para tests
export DJANGO_SETTINGS_MODULE=hotel.settings
export DATABASE_URL=sqlite:///test_db.sqlite3
export CELERY_TASK_ALWAYS_EAGER=True
export CELERY_TASK_EAGER_PROPAGATES=True
export EMAIL_BACKEND=django.core.mail.backends.locmem.EmailBackend

# Crear base de datos de test
python manage.py migrate --run-syncdb

print_status "Ejecutando tests de integración..."

# Ejecutar tests con pytest
if command -v pytest &> /dev/null; then
    # Usar pytest si está disponible
    pytest tests/test_cancel_refund_integration.py -v --tb=short --disable-warnings
    PYTEST_EXIT_CODE=$?
else
    # Usar Django test runner como fallback
    python run_tests.py
    PYTEST_EXIT_CODE=$?
fi

# Verificar resultado de los tests
if [ $PYTEST_EXIT_CODE -eq 0 ]; then
    print_status "✅ Todos los tests pasaron exitosamente!"
    
    # Ejecutar tests de coverage si está disponible
    if command -v pytest &> /dev/null && pip list | grep -q pytest-cov; then
        print_status "Generando reporte de cobertura..."
        pytest tests/test_cancel_refund_integration.py --cov=apps.payments --cov=apps.reservations --cov-report=term-missing --cov-report=html
    fi
    
    # Limpiar base de datos de test
    print_status "Limpiando base de datos de test..."
    rm -f test_db.sqlite3
    
    print_status "🎉 Tests completados exitosamente!"
    exit 0
else
    print_error "❌ Algunos tests fallaron!"
    
    # Mostrar logs de error si están disponibles
    if [ -f "test_logs.txt" ]; then
        print_error "Logs de error:"
        cat test_logs.txt
    fi
    
    exit 1
fi

