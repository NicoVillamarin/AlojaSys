# Solución Rápida: Error de CORS en Nueva Instancia

## Tu Error Actual

```
Access to fetch at 'https://alojasys-backend-production.up.railway.app/api/token/' 
from origin 'https://hotelkansas.alojasys.com' has been blocked by CORS policy
```

**Problema:** El frontend de `hotelkansas.alojasys.com` está intentando conectarse al backend de producción en lugar de su propio backend.

---

## Solución Inmediata (5 minutos)

### Paso 1: Configurar VITE_API_URL en el Frontend

1. Ve a Railway → Tu proyecto → Entorno del cliente → Servicio **Frontend**
2. Ve a la pestaña **"Variables"**
3. Busca o crea la variable `VITE_API_URL`
4. Configúrala con la URL de tu backend del cliente:
   ```
   VITE_API_URL=https://alojasys-backend-cliente-hotelkansas.up.railway.app
   ```
   O si tienes dominio personalizado:
   ```
   VITE_API_URL=https://api.hotelkansas.alojasys.com
   ```
5. **Guarda** los cambios

### Paso 2: Configurar FRONTEND_URL en el Backend

1. Ve al servicio **Backend** del mismo entorno
2. Ve a la pestaña **"Variables"**
3. Busca o crea la variable `FRONTEND_URL`
4. Configúrala con el dominio de tu frontend:
   ```
   FRONTEND_URL=https://hotelkansas.alojasys.com
   ```
5. **Guarda** los cambios

### Paso 3: Verificar ALLOWED_HOSTS en el Backend

1. En el mismo servicio backend, verifica `ALLOWED_HOSTS`
2. Debe incluir el dominio del backend:
   ```
   ALLOWED_HOSTS=hotelkansas.alojasys.com,api.hotelkansas.alojasys.com,alojasys-backend-cliente-hotelkansas.up.railway.app
   ```
   (Ajusta según tus dominios reales)

### Paso 4: Redesplegar los Servicios

**IMPORTANTE:** Después de cambiar `VITE_API_URL`, necesitas redesplegar el frontend porque Vite compila las variables en tiempo de build.

1. Ve al servicio **Frontend**
2. Pestaña **"Deployments"**
3. Haz clic en **"Redeploy"** o **"Deploy"**
4. Espera a que termine el despliegue

El backend se reiniciará automáticamente cuando guardes las variables, pero si quieres forzarlo:
1. Ve al servicio **Backend**
2. Pestaña **"Deployments"**
3. Haz clic en **"Redeploy"**

### Paso 5: Verificar

1. Espera 2-3 minutos a que termine el despliegue
2. Abre `https://hotelkansas.alojasys.com` en el navegador
3. Abre la consola del navegador (F12)
4. Ejecuta: `console.log(import.meta.env.VITE_API_URL)`
5. Debe mostrar la URL de tu backend del cliente, NO la de producción
6. Intenta hacer login nuevamente

---

## Si el Problema Persiste

### Verificar que el Backend esté Funcionando

1. Abre directamente la URL del backend en el navegador:
   ```
   https://alojasys-backend-cliente-hotelkansas.up.railway.app/api/
   ```
   (o tu dominio personalizado)

2. Debe responder con JSON (no error 404 o 500)

### Verificar Logs

1. En Railway, ve a la pestaña **"Logs"** del servicio backend
2. Busca errores relacionados con CORS o configuración
3. Verifica que el backend esté leyendo correctamente `FRONTEND_URL`

### Verificar Variables de Entorno

En el backend, verifica que estas variables estén configuradas:
- ✅ `FRONTEND_URL=https://hotelkansas.alojasys.com`
- ✅ `ALLOWED_HOSTS` incluye el dominio del backend
- ✅ `DATABASE_URL` está configurada (Railway la crea automáticamente)
- ✅ `REDIS_URL` está configurada (Railway la crea automáticamente)

---

## Resumen de Variables Necesarias

### Frontend (Servicio Frontend)
```
VITE_API_URL=https://[url-de-tu-backend-del-cliente]
```

### Backend (Servicio Backend)
```
FRONTEND_URL=https://hotelkansas.alojasys.com
ALLOWED_HOSTS=hotelkansas.alojasys.com,api.hotelkansas.alojasys.com,[url-backend-railway]
SECRET_KEY=[tu-secret-key-unico]
DEBUG=False
```

---

## ¿Por qué pasó esto?

1. El frontend no tenía `VITE_API_URL` configurada
2. El código del frontend tiene un fallback que probablemente apunta al backend de producción
3. El backend de producción no tiene configurado CORS para permitir `hotelkansas.alojasys.com`

**Solución:** Cada instancia de cliente debe tener sus propias variables de entorno configuradas correctamente.
