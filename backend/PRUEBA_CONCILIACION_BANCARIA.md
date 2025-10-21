# 🧪 Guía de Pruebas - Conciliación Bancaria

## 📋 Descripción
Esta guía te permite probar que la funcionalidad de conciliación bancaria funciona correctamente.

## 🚀 Cómo Probar

### Opción 1: Prueba Automática Completa
```bash
cd backend
python test_reconciliation_full.py
```

### Opción 2: Prueba Paso a Paso

#### Paso 1: Crear datos de prueba
```bash
cd backend
python test_reconciliation_setup.py
```

#### Paso 2: Probar el proceso de conciliación
```bash
python test_reconciliation_process.py
```

#### Paso 3: Limpiar datos de prueba
```bash
python test_reconciliation_cleanup.py
```

## 📊 ¿Qué hace cada script?

### `test_reconciliation_setup.py`
- Crea un hotel de prueba
- Crea 4 reservas con pagos pendientes
- Crea transferencias bancarias pendientes
- **Resultado:** Datos listos para conciliación

### `test_reconciliation_process.py`
- Crea una conciliación bancaria
- Simula la subida de un CSV con transferencias
- Ejecuta el proceso de matching automático
- **Resultado:** Pagos confirmados automáticamente

### `test_reconciliation_cleanup.py`
- Elimina todos los datos de prueba
- **Resultado:** Base de datos limpia

## 📁 Archivos de Prueba

### `test_reconciliation_data.csv`
```csv
fecha,descripcion,importe,moneda,referencia
2025-01-15,"Transferencia Juan Perez",25000.00,"ARS","CBU 28500109...1234"
2025-01-16,"Transferencia Maria Garcia",18000.00,"ARS","CBU 28500109...5678"
2025-01-17,"Transferencia Carlos Lopez",32000.00,"ARS","CBU 28500109...9012"
2025-01-18,"Transferencia Ana Rodriguez",15000.00,"ARS","CBU 28500109...3456"
```

## 🎯 Resultados Esperados

### Antes de la conciliación:
- 4 reservas con pagos pendientes
- 4 transferencias bancarias pendientes

### Después de la conciliación:
- 4 pagos confirmados automáticamente
- 4 matches creados
- 100% de efectividad de matching

## 🔍 Verificación Manual

### En el Frontend:
1. Ve a **Financiero → Conciliación Bancaria**
2. Haz clic en **"Subir CSV"**
3. Sube el archivo `test_reconciliation_data.csv`
4. Verifica que se crean las conciliaciones
5. Revisa que los pagos se confirman automáticamente

### En el Backend (Django Admin):
1. Ve a **Payments → Bank Reconciliations**
2. Verifica que se creó la conciliación
3. Ve a **Payments → Payments**
4. Verifica que los pagos cambiaron de "pending" a "approved"

## 🐛 Solución de Problemas

### Error: "No se encontró el hotel de prueba"
```bash
python test_reconciliation_setup.py
```

### Error: "No se encontraron pagos pendientes"
```bash
python test_reconciliation_cleanup.py
python test_reconciliation_setup.py
```

### Error: "Error en el proceso de conciliación"
- Verifica que el servicio `BankReconciliationService` esté implementado
- Revisa los logs del backend

## 📈 Métricas de Éxito

- ✅ **4 reservas creadas**
- ✅ **4 pagos pendientes creados**
- ✅ **4 transferencias bancarias creadas**
- ✅ **4 matches encontrados**
- ✅ **100% de efectividad de matching**
- ✅ **4 pagos confirmados automáticamente**

## 🎉 ¡Listo!

Si todos los pasos se ejecutan sin errores, la funcionalidad de conciliación bancaria está funcionando correctamente.
