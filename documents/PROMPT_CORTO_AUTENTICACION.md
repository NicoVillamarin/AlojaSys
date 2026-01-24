# PROMPT CORTO: Autenticación BFF → AlojaSys

Necesito implementar autenticación JWT en mi BFF (Python FastAPI) para consumir APIs de AlojaSys (Django + DRF + SimpleJWT).

**Problema**: AlojaSys requiere `Authorization: Bearer <token>` en todas las llamadas, y necesito que mi BFF obtenga/renueve tokens automáticamente.

**Endpoints de AlojaSys**:
- Login: `POST /api/token/` con `{"username": "...", "password": "..."}` → devuelve `{"access": "...", "refresh": "..."}`
- Refresh: `POST /api/token/refresh/` con `{"refresh": "..."}` → devuelve nuevo `{"access": "..."}`
- Base URL: configurable vía env var `ALOJASYS_API_URL`

**Requerimientos**:
1. Crear clase `AlojaSysClient` que maneje autenticación automática
2. Cachear tokens en memoria y renovarlos antes de expirar
3. Si recibe 401, intentar refresh; si falla, reloguear
4. Exponer métodos tipo `get_hotels()`, `get_rooms()`, `search_availability(...)`, etc.
5. Usar variables de entorno para credenciales (`.env`)

**Stack**: Python FastAPI, `httpx` (async) o `requests` (sync)

Generá el código completo del cliente con manejo robusto de errores y renovación automática de tokens.
