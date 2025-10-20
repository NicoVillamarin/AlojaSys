@echo off
REM Script de Windows para ejecutar tests de integración de cancelación y refund

echo 🚀 Iniciando tests de integración de cancelación y refund...

REM Verificar que estamos en el directorio correcto
if not exist "manage.py" (
    echo ❌ No se encontró manage.py. Ejecutar desde el directorio backend/
    exit /b 1
)

REM Verificar que Python está disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no está instalado o no está en el PATH
    exit /b 1
)

REM Verificar que pip está disponible
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip no está instalado o no está en el PATH
    exit /b 1
)

echo ✅ Instalando dependencias de test...

REM Instalar dependencias de test
if exist "requirements-test.txt" (
    pip install -r requirements-test.txt
) else (
    echo ⚠️ No se encontró requirements-test.txt, instalando dependencias básicas...
    pip install pytest pytest-django factory-boy
)

REM Instalar dependencias del proyecto
if exist "requirements.txt" (
    pip install -r requirements.txt
)

echo ✅ Configurando base de datos de test...

REM Configurar variables de entorno para tests
set DJANGO_SETTINGS_MODULE=hotel.settings
set DATABASE_URL=sqlite:///test_db.sqlite3
set CELERY_TASK_ALWAYS_EAGER=True
set CELERY_TASK_EAGER_PROPAGATES=True
set EMAIL_BACKEND=django.core.mail.backends.locmem.EmailBackend

REM Crear base de datos de test
python manage.py migrate --run-syncdb

echo ✅ Ejecutando tests de integración...

REM Ejecutar tests con pytest
pytest tests/test_cancel_refund_integration.py -v --tb=short --disable-warnings
if errorlevel 1 (
    echo ❌ Algunos tests fallaron!
    exit /b 1
)

echo ✅ Todos los tests pasaron exitosamente!

REM Ejecutar tests de coverage si está disponible
pytest --version >nul 2>&1
if not errorlevel 1 (
    pip list | findstr pytest-cov >nul 2>&1
    if not errorlevel 1 (
        echo ✅ Generando reporte de cobertura...
        pytest tests/test_cancel_refund_integration.py --cov=apps.payments --cov=apps.reservations --cov-report=term-missing --cov-report=html
    )
)

REM Limpiar base de datos de test
echo ✅ Limpiando base de datos de test...
if exist "test_db.sqlite3" del test_db.sqlite3

echo 🎉 Tests completados exitosamente!
pause

