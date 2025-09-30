#!/bin/bash

echo "========================================"
echo "INSTALANDO DEPENDENCIAS DE TESTING"
echo "========================================"

echo ""
echo "1. Instalando dependencias de Python..."
pip install -r requirements.txt

echo ""
echo "2. Configurando entorno..."
python setup_tests.py

echo ""
echo "3. Verificando instalación..."
python -c "import selenium, pytest; print('✓ Dependencias instaladas correctamente')"

echo ""
echo "========================================"
echo "INSTALACIÓN COMPLETADA"
echo "========================================"
echo ""
echo "Para ejecutar los tests:"
echo "  python run_tests.py"
echo ""
