# Guía: Crear Nueva Instancia de Cliente en Railway (Plan Hobby)

## Contexto
Tienes un proyecto en Railway llamado `splendid-elegance` con la demo funcionando. Ahora necesitas crear una nueva instancia para tu primer cliente real, reutilizando la misma infraestructura pero con datos/configuración separada.

## Opción Recomendada: Nuevo Entorno en el Mismo Proyecto

### Ventajas
- ✅ Reutiliza la misma infraestructura (más económico en plan Hobby)
- ✅ Misma configuración de servicios
- ✅ Variables de entorno separadas por cliente
- ✅ Base de datos independiente
- ✅ Dominio independiente

### Pasos para Crear la Nueva Instancia

#### 1. Crear Nuevo Entorno en Railway

1. Ve a tu proyecto `splendid-elegance` en Railway
2. En la parte superior, verás el selector de entorno (actualmente dice "production")
3. Haz clic en el selector y selecciona **"+ New Environment"** o **"Create Environment"**
4. Nombre el nuevo entorno: `cliente-[nombre-cliente]` (ej: `cliente-hotel-plaza`)

#### 2. Duplicar los Servicios al Nuevo Entorno

Una vez creado el nuevo entorno, necesitas crear los mismos servicios que tienes en `production`:

**Servicios a crear:**
- `alojasys-db` (PostgreSQL)
- `alojasys-backend` (Backend Django)
- `alojasys` (Frontend React)
- `Redis` (Redis Cache)

**Para cada servicio:**

1. En la vista Architecture del nuevo entorno, haz clic en **"+ Create"** o el botón **"+"** del panel lateral
2. Selecciona el tipo de servicio:
   - **PostgreSQL** para la base de datos
   - **GitHub Repo** para backend y frontend
   - **Redis** para cache

3. **Para PostgreSQL:**
   - Nombre: `alojasys-db-cliente-[nombre]`
   - Railway creará automáticamente las variables `DATABASE_URL`, `PGHOST`, `PGPORT`, etc.

4. **Para Backend (GitHub):**
   - Conecta el mismo repositorio
   - Selecciona la rama (probablemente `main` o `production`)
   - Nombre: `alojasys-backend-cliente-[nombre]`
   - **Variables de entorno importantes:**
     ```
     DATABASE_URL=<se conecta automáticamente al PostgreSQL del entorno>
     REDIS_URL=<se conecta automáticamente al Redis del entorno>
     SECRET_KEY=<genera uno nuevo y único>
     DEBUG=False
     ALLOWED_HOSTS=<dominio-del-cliente>
     FRONTEND_URL=https://<dominio-del-cliente>
     EXTERNAL_BASE_URL=https://<url-backend-cliente>
     ```

5. **Para Frontend (GitHub):**
   - Conecta el mismo repositorio
   - Selecciona la rama
   - Nombre: `alojasys-cliente-[nombre]`
   - **Variables de entorno:**
     ```
     VITE_API_URL=https://<url-backend-cliente>
     ```

6. **Para Redis:**
   - Nombre: `redis-cliente-[nombre]`
   - Railway creará automáticamente `REDIS_URL`

#### 3. Configurar Variables de Entorno Específicas del Cliente

En cada servicio, configura las variables específicas del cliente:

**Backend:**
- `SECRET_KEY`: Genera uno nuevo (puedes usar: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- `CLOUDINARY_CLOUD_NAME`: (si usas Cloudinary, puede ser el mismo o diferente)
- `CLOUDINARY_API_KEY`: (si aplica)
- `CLOUDINARY_API_SECRET`: (si aplica)
- `RESEND_API_KEY`: (si usas Resend para emails)
- `AFIP_CERTIFICATE_PATH`: (ruta a certificados AFIP del cliente)
- `AFIP_PRIVATE_KEY_PATH`: (ruta a clave privada AFIP del cliente)
- Cualquier otra variable específica del cliente

**Frontend:**
- `VITE_API_URL`: URL del backend del cliente

#### 4. Configurar Dominios

1. En cada servicio (backend y frontend), ve a la pestaña **"Settings"**
2. En la sección **"Networking"**, haz clic en **"Generate Domain"** o **"Custom Domain"**
3. Configura:
   - Backend: `api.cliente-[nombre].alojasys.com` (o el dominio que prefieras)
   - Frontend: `cliente-[nombre].alojasys.com` (o el dominio del cliente)

#### 5. Conectar Servicios (Dependencies)

Asegúrate de que los servicios estén conectados:
- Backend → PostgreSQL (Railway lo hace automáticamente si están en el mismo entorno)
- Backend → Redis (Railway lo hace automáticamente)
- Frontend → Backend (configurado vía `VITE_API_URL`)

#### 6. Ejecutar Migraciones

Una vez que el backend esté desplegado:

1. Ve al servicio del backend
2. En la pestaña **"Deployments"** o **"Logs"**, puedes ejecutar comandos
3. O usa la terminal de Railway (si está disponible) para ejecutar:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

#### 7. Inicializar Datos del Cliente

Después de las migraciones, necesitas:
- Crear el hotel del cliente
- Configurar usuarios iniciales
- Configurar datos básicos (países, ciudades, etc.)

Puedes hacerlo desde el admin de Django o crear un script de inicialización.

---

## Alternativa: Crear Nuevo Proyecto (No Recomendado en Plan Hobby)

Si prefieres crear un proyecto completamente separado:

1. Ve a la página principal de Railway
2. Haz clic en **"+ New"**
3. Conecta el mismo repositorio
4. Crea los mismos servicios

**Desventajas:**
- ❌ Puede tener límites en el plan Hobby
- ❌ Más costoso (cada proyecto cuenta por separado)
- ❌ Más difícil de gestionar

---

## Checklist de Creación de Instancia

- [ ] Nuevo entorno creado en Railway
- [ ] Servicio PostgreSQL creado y funcionando
- [ ] Servicio Redis creado y funcionando
- [ ] Servicio Backend creado, conectado a GitHub, y desplegado
- [ ] Servicio Frontend creado, conectado a GitHub, y desplegado
- [ ] Variables de entorno configuradas (especialmente `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`)
- [ ] Dominios configurados para backend y frontend
- [ ] Migraciones ejecutadas en la base de datos
- [ ] Superusuario creado
- [ ] Datos iniciales del cliente configurados
- [ ] Verificación de que todo funciona correctamente

---

## Notas Importantes

1. **Base de Datos Separada**: Cada entorno tiene su propia base de datos, así que los datos están completamente aislados.

2. **Variables de Entorno**: Railway automáticamente crea variables como `DATABASE_URL` y `REDIS_URL` cuando conectas servicios. Solo necesitas configurar las variables específicas de tu aplicación.

3. **Costos**: En el plan Hobby, cada servicio activo consume recursos. Asegúrate de monitorear el uso.

4. **Backups**: Considera configurar backups automáticos para las bases de datos de producción.

5. **Monitoreo**: Usa la pestaña "Observability" en Railway para monitorear logs y métricas de cada servicio.

---

## Comandos Útiles

### Generar SECRET_KEY nuevo:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Verificar conexión a base de datos (desde Railway terminal):
```bash
python manage.py dbshell
```

### Verificar variables de entorno:
```bash
python manage.py shell
>>> import os
>>> from decouple import config
>>> print(config('DATABASE_URL'))
>>> print(config('REDIS_URL'))
```

---

## Solución de Problemas

### Error de CORS: "Access to fetch... has been blocked by CORS policy"

**Síntomas:**
- El frontend intenta conectarse al backend pero recibe error de CORS
- El error menciona que el origen del frontend no está permitido
- El frontend puede estar intentando conectarse al backend de producción en lugar del suyo

**Causas comunes:**
1. ❌ `VITE_API_URL` no está configurada en el servicio frontend del nuevo cliente
2. ❌ `FRONTEND_URL` no está configurada en el servicio backend del nuevo cliente
3. ❌ El frontend está usando un valor por defecto que apunta al backend de producción

**Solución paso a paso:**

1. **Verificar y configurar `VITE_API_URL` en el Frontend:**
   - Ve al servicio del frontend del nuevo cliente en Railway
   - Ve a la pestaña **"Variables"**
   - Asegúrate de que existe `VITE_API_URL` con el valor correcto:
     ```
     VITE_API_URL=https://alojasys-backend-cliente-[nombre].up.railway.app
     ```
   - O si tienes un dominio personalizado:
     ```
     VITE_API_URL=https://api.hotelkansas.alojasys.com
     ```
   - **IMPORTANTE:** Si cambias esta variable, necesitas **redesplegar** el frontend para que tome efecto (Vite compila las variables en tiempo de build)

2. **Verificar y configurar `FRONTEND_URL` en el Backend:**
   - Ve al servicio del backend del nuevo cliente en Railway
   - Ve a la pestaña **"Variables"**
   - Asegúrate de que existe `FRONTEND_URL` con el dominio del frontend:
     ```
     FRONTEND_URL=https://hotelkansas.alojasys.com
     ```
   - Esta variable permite que el backend acepte peticiones CORS desde ese dominio

3. **Verificar `ALLOWED_HOSTS` en el Backend:**
   - En el mismo servicio backend, verifica que `ALLOWED_HOSTS` incluya el dominio del backend:
     ```
     ALLOWED_HOSTS=hotelkansas.alojasys.com,api.hotelkansas.alojasys.com,alojasys-backend-cliente-[nombre].up.railway.app
     ```

4. **Redesplegar los servicios:**
   - Después de cambiar las variables, **redesplega** ambos servicios (frontend y backend)
   - En Railway, ve a la pestaña **"Deployments"** y haz clic en **"Redeploy"**

5. **Verificar que los dominios sean correctos:**
   - Frontend debe apuntar a: `https://hotelkansas.alojasys.com` (o el dominio que configuraste)
   - Backend debe estar en: `https://api.hotelkansas.alojasys.com` (o el dominio que configuraste)
   - `VITE_API_URL` debe ser exactamente la URL del backend (con `https://`)

**Nota importante sobre Vite:**
Las variables que empiezan con `VITE_` se compilan en tiempo de build. Si cambias `VITE_API_URL` después de desplegar, necesitas:
- Hacer un nuevo deploy (Railway lo hará automáticamente si está conectado a GitHub)
- O forzar un redeploy manual

**Verificación rápida:**
1. Abre la consola del navegador en `https://hotelkansas.alojasys.com`
2. Ejecuta: `console.log(import.meta.env.VITE_API_URL)`
3. Debe mostrar la URL de tu backend, no la de producción

---

## Próximos Pasos

Una vez que tengas la instancia funcionando:
1. Configurar certificados AFIP del cliente (si aplica)
2. Configurar integraciones (OTAs, pagos, etc.)
3. Configurar dominios personalizados del cliente
4. Configurar backups automáticos
5. Documentar credenciales y configuraciones del cliente
