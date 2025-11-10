from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime, timedelta, timezone

# Imports opcionales - si no están instalados, las funciones fallarán con un error claro
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    service_account = None
    build = None


SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _build_service(credentials_json: Dict[str, Any]):
    """Construye el cliente de Google Calendar desde un JSON de service account.

    Espera el JSON completo de la service account compartida con el calendario.
    """
    if not GOOGLE_AVAILABLE:
        raise ImportError("Google Calendar API no está instalada. Instala: pip install google-api-python-client google-auth")
    
    creds = service_account.Credentials.from_service_account_info(credentials_json, scopes=SCOPES)
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def list_events(
    credentials_json: Dict[str, Any],
    calendar_id: str,
    time_min: Optional[datetime] = None,
    time_max: Optional[datetime] = None,
    sync_token: Optional[str] = None,
) -> Dict[str, Any]:
    service = _build_service(credentials_json)
    req = service.events().list(calendarId=calendar_id, singleEvents=True, orderBy="startTime")

    if sync_token:
        # Incremental sync: devuelve solo cambios desde el último token; incluir eliminados
        req = service.events().list(calendarId=calendar_id, syncToken=sync_token, showDeleted=True, singleEvents=True)
    else:
        now = datetime.now(timezone.utc)
        time_min = time_min or (now - timedelta(days=1))
        time_max = time_max or (now + timedelta(days=365))
        req = service.events().list(
            calendarId=calendar_id,
            singleEvents=True,
            orderBy="startTime",
            timeMin=time_min.isoformat(),
            timeMax=time_max.isoformat(),
        )

    return req.execute()


def get_calendar(credentials_json: Dict[str, Any], calendar_id: str) -> Dict[str, Any]:
    """Verifica que el calendario sea accesible y devuelve su información."""
    service = _build_service(credentials_json)
    return service.calendars().get(calendarId=calendar_id).execute()


def insert_event(credentials_json: Dict[str, Any], calendar_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    service = _build_service(credentials_json)
    return service.events().insert(calendarId=calendar_id, body=body).execute()


def update_event(credentials_json: Dict[str, Any], calendar_id: str, event_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    service = _build_service(credentials_json)
    return service.events().update(calendarId=calendar_id, eventId=event_id, body=body).execute()


def delete_event(credentials_json: Dict[str, Any], calendar_id: str, event_id: str) -> None:
    service = _build_service(credentials_json)
    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()


def watch_calendar(credentials_json: Dict[str, Any], calendar_id: str, address: str, channel_id: str, token: str) -> Dict[str, Any]:
    """Crea un canal de watch (webhook) en Google Calendar para eventos del calendario.

    address: URL pública HTTPS que recibirá notificaciones POST.
    channel_id: ID único del canal (uuid).
    token: valor opaco que Google devolverá en la cabecera X-Goog-Channel-Token.
    """
    service = _build_service(credentials_json)
    body = {
        "id": channel_id,
        "type": "web_hook",
        "address": address,
        "token": token,
    }
    return service.events().watch(calendarId=calendar_id, body=body).execute()


