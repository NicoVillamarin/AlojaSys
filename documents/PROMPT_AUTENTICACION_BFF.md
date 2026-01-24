# PROMPT: Implementar autenticación BFF → AlojaSys

## Contexto
Tengo un proyecto separado llamado **`AlojasysPublicWeb`** (sitio público multi-tenant para hoteles) que necesita consumir las APIs de **AlojaSys** (backend Django con DRF + JWT).

**Problema actual**: Las APIs de AlojaSys requieren autenticación (`IsAuthenticated`), y mi BFF (backend del sitio público) no puede acceder porque no tiene credenciales.

**Stack del BFF**: Python (FastAPI o Flask) corriendo en Docker.

---

## Objetivo
Implementar en el BFF un **cliente HTTP autenticado** que:
1. Obtenga un token JWT de AlojaSys usando usuario/clave de servicio
2. Use ese token en todas las llamadas a AlojaSys (header `Authorization: Bearer <token>`)
3. Renueve el token automáticamente cuando expire (usando refresh token)
4. Maneje errores de autenticación (401) reintentando con refresh

---

## Información de AlojaSys
- **Base URL**: Configurable vía env var (ej. `http://host.docker.internal:8000` en Docker, `http://localhost:8000` local)
- **Endpoint de login**: `POST /api/token/` (SimpleJWT)
- **Endpoint de refresh**: `POST /api/token/refresh/`
- **Formato de request login**:
  ```json
  {
    "username": "publicweb_service",
    "password": "TU_PASSWORD"
  }
  ```
- **Formato de response**:
  ```json
  {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
  ```
- **Header requerido en llamadas**: `Authorization: Bearer <access_token>`

---

## Requerimientos técnicos

### 1. Variables de entorno (.env)
Crear/actualizar `.env` del BFF con:
```env
# URL base de AlojaSys
ALOJASYS_API_URL=http://host.docker.internal:8000

# Credenciales del usuario de servicio
ALOJASYS_USERNAME=publicweb_service
ALOJASYS_PASSWORD=TU_PASSWORD_AQUI

# Tiempo de expiración del token (opcional, default 50 min)
ALOJASYS_TOKEN_REFRESH_BEFORE_EXPIRY_MINUTES=10
```

### 2. Cliente HTTP con autenticación
Crear un módulo `api/alojasys_client.py` (o similar) que:
- Tenga una clase `AlojaSysClient` con métodos para llamar a AlojaSys
- Maneje autenticación automática (obtener token, renovar cuando expire)
- Cachee el token en memoria (o Redis si lo tenés)
- Exponga métodos tipo:
  - `get_hotels()`
  - `get_rooms(hotel_id=None)`
  - `search_availability(check_in, check_out, hotel_id, ...)`
  - `create_reservation(...)`
  - `get_reservation(reservation_id)`
  - etc.

### 3. Flujo de autenticación
```
1. Al iniciar el BFF (o primera llamada):
   - POST /api/token/ con username/password
   - Guardar access + refresh en memoria

2. En cada llamada a AlojaSys:
   - Usar access token en header Authorization: Bearer <token>
   - Si recibe 401:
     a) POST /api/token/refresh/ con refresh token
     b) Actualizar access token
     c) Reintentar la llamada original

3. Renovación proactiva (opcional pero recomendado):
   - Antes de que expire el access token (ej. 10 min antes)
   - Renovar usando refresh token
```

### 4. Manejo de errores
- Si el refresh token también expiró (401 en refresh): reloguear con username/password
- Si falla la conexión a AlojaSys: retornar error claro al frontend
- Loggear errores de autenticación (sin exponer passwords)

---

## Estructura sugerida del código

```python
# api/alojasys_client.py
import httpx
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

class AlojaSysClient:
    def __init__(self):
        self.base_url = os.getenv("ALOJASYS_API_URL", "http://localhost:8000")
        self.username = os.getenv("ALOJASYS_USERNAME")
        self.password = os.getenv("ALOJASYS_PASSWORD")
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
    async def _ensure_authenticated(self):
        """Asegura que tenemos un token válido"""
        # Si no hay token o está por expirar, obtener/renovar
        ...
        
    async def _get_token(self):
        """Obtiene token inicial con username/password"""
        ...
        
    async def _refresh_token(self):
        """Renueva token usando refresh token"""
        ...
        
    async def _request(self, method: str, endpoint: str, **kwargs):
        """Hace request autenticado a AlojaSys"""
        await self._ensure_authenticated()
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self._access_token}"
        ...
        
    # Métodos públicos para consumir APIs
    async def get_hotels(self):
        return await self._request("GET", "/api/hotels/")
        
    async def get_rooms(self, hotel_id: Optional[int] = None):
        url = "/api/rooms/"
        if hotel_id:
            url = f"/api/rooms/?hotel={hotel_id}"
        return await self._request("GET", url)
        
    async def search_availability(self, check_in: str, check_out: str, hotel_id: int, adults: int = 1, children: int = 0):
        return await self._request("POST", "/api/reservations/availability/", json={
            "check_in": check_in,
            "check_out": check_out,
            "hotel_id": hotel_id,
            "adults": adults,
            "children": children
        })
        
    # ... más métodos según necesites
```

---

## Entregables esperados
1. ✅ Código del cliente HTTP autenticado (`AlojaSysClient`)
2. ✅ Variables de entorno documentadas (`.env.example`)
3. ✅ Tests básicos (o al menos un script de prueba) que verifique:
   - Login exitoso
   - Llamada autenticada a `/api/hotels/`
   - Renovación automática de token
4. ✅ README o docstring explicando cómo usar el cliente

---

## Notas importantes
- **NO** hardcodear credenciales en el código
- **NO** exponer tokens en logs
- Usar `httpx` (async) o `requests` (sync) según tu stack
- Si usás FastAPI, el cliente puede ser un dependency injection
- Considerar usar un singleton para el cliente (una instancia global reutilizable)

---

## Cómo probar manualmente (antes de implementar)
Desde PowerShell en Windows:
```powershell
# 1. Obtener token
$body = @{ username="publicweb_service"; password="TU_PASSWORD" } | ConvertTo-Json
$r = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/token/" -ContentType "application/json" -Body $body
$token = $r.access

# 2. Probar endpoint autenticado
$h = @{ Authorization = "Bearer $token" }
Invoke-RestMethod -Uri "http://localhost:8000/api/hotels/" -Headers $h
```

Si eso funciona, entonces el código del cliente debe replicar ese flujo.
