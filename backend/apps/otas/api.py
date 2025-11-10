"""
API REST para el módulo OTA.

Endpoints personalizados para gestión de OTAs, sincronización y mapeos.
"""
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from django.http import StreamingHttpResponse
import json, time, os
import redis

from .models import (
    OtaConfig,
    OtaRoomMapping,
    OtaSyncLog,
    OtaProvider,
    OtaSyncJob,
)
from .serializers import (
    OtaConfigSerializer,
    OtaRoomMappingSerializer,
    OtaSyncLogSerializer,
)
from .services.ical_sync_service import ICALSyncService
from django.conf import settings

# Import opcional para Google Calendar
try:
    from .services.google_sync_service import import_events_for_mapping as google_import_events
    from .services.google_sync_service import enable_webhook_watch
    GOOGLE_AVAILABLE = True
except Exception:
    GOOGLE_AVAILABLE = False
    google_import_events = None
    enable_webhook_watch = None


@api_view(["GET"])
def list_ota_configs(request: Request) -> Response:
    """
    Lista canales OTA configurados con filtros.
    
    GET /api/otas/
    
    Query params:
    - provider: Filtrar por proveedor (ej: ?provider=booking)
    - is_active: Filtrar por estado activo (ej: ?is_active=true)
    - hotel: Filtrar por hotel (ej: ?hotel=1)
    """
    queryset = OtaConfig.objects.select_related("hotel").all()
    
    # Aplicar filtros
    provider = request.query_params.get("provider")
    if provider:
        queryset = queryset.filter(provider=provider)
    
    is_active = request.query_params.get("is_active")
    if is_active is not None:
        is_active_bool = is_active.lower() in ("true", "1", "yes")
        queryset = queryset.filter(is_active=is_active_bool)
    
    hotel_id = request.query_params.get("hotel")
    if hotel_id:
        queryset = queryset.filter(hotel_id=hotel_id)
    
    # Ordenar por fecha de creación descendente
    queryset = queryset.order_by("-created_at")
    
    serializer = OtaConfigSerializer(queryset, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
def sync_otas(request: Request) -> Response:
    """
    Endpoint para ejecutar sincronización manual de OTAs.
    
    POST /api/otas/sync/
    
    Body opcional:
    {
        "provider": "booking",  // Sincronizar solo un proveedor
        "hotel_id": 1,          // Sincronizar solo un hotel
    }
    
    Si no se especifica, sincroniza todos los mapeos activos.
    
    Retorna:
    {
        "status": "ok" | "running" | "error",
        "message": "...",
        "job_id": 123,
        "logs": [...]  // Logs recientes
    }
    """
    provider = request.data.get("provider")
    hotel_id = request.data.get("hotel_id")
    
    try:
        # Si se especifica provider o hotel_id, sincronizar específico
        if provider or hotel_id:
            # Filtrar mapeos según criterios
            mappings = OtaRoomMapping.objects.filter(is_active=True)
            if provider:
                mappings = mappings.filter(provider=provider)
            if hotel_id:
                mappings = mappings.filter(hotel_id=hotel_id)
            
            # Ejecutar sync para cada mapeo encontrado
            stats = {
                "total_mappings": 0,
                "import_success": 0,
                "import_errors": 0,
                "export_success": 0,
                "export_errors": 0,
            }
            
            for mapping in mappings:
                stats["total_mappings"] += 1
                # Import si corresponde (iCal o Google)
                if mapping.sync_direction in [
                    OtaRoomMapping.SyncDirection.IMPORT,
                    OtaRoomMapping.SyncDirection.BOTH,
                ]:
                    try:
                        from .models import OtaSyncJob
                        job = OtaSyncJob.objects.create(
                            hotel=mapping.hotel,
                            provider=mapping.provider,
                            job_type=OtaSyncJob.JobType.IMPORT_ICS,
                            status=OtaSyncJob.JobStatus.RUNNING,
                            stats={"mapping_id": mapping.id},
                        )
                        if mapping.provider == OtaProvider.GOOGLE and GOOGLE_AVAILABLE:
                            result = google_import_events(mapping, job=job)
                        elif mapping.ical_in_url:
                            result = ICALSyncService.import_reservations(mapping, job=job)
                        else:
                            result = {"errors": 1, "reason": "no_import_source"}
                        job.status = OtaSyncJob.JobStatus.SUCCESS if result.get("errors", 0) == 0 else OtaSyncJob.JobStatus.FAILED
                        job.save()
                        if result.get("errors", 0) == 0:
                            stats["import_success"] += 1
                        else:
                            stats["import_errors"] += 1
                    except Exception:
                        stats["import_errors"] += 1
                
                # Export si corresponde
                if mapping.sync_direction in [
                    OtaRoomMapping.SyncDirection.EXPORT,
                    OtaRoomMapping.SyncDirection.BOTH,
                ]:
                    try:
                        from .models import OtaSyncJob
                        from django.utils import timezone
                        job = OtaSyncJob.objects.create(
                            hotel=mapping.hotel,
                            provider=mapping.provider,
                            job_type=OtaSyncJob.JobType.EXPORT_ICS,
                            status=OtaSyncJob.JobStatus.RUNNING,
                            stats={"mapping_id": mapping.id},
                        )
                        result = ICALSyncService.export_reservations(mapping, job=job)
                        job.status = OtaSyncJob.JobStatus.SUCCESS
                        job.save()
                        stats["export_success"] += 1
                    except Exception:
                        stats["export_errors"] += 1
            
            response_status = "ok" if (stats["import_errors"] == 0 and stats["export_errors"] == 0) else "error"
            
        else:
            # Sincronización completa de todos los mapeos activos usando el servicio
            stats = ICALSyncService.schedule_sync()
            response_status = "ok" if (stats.get("import_errors", 0) == 0 and stats.get("export_errors", 0) == 0) else "error"
            
        # Obtener logs recientes
        recent_logs = OtaSyncLog.objects.select_related("job").order_by("-created_at")[:10]
        
        return Response({
            "status": response_status,
            "message": "Sincronización ejecutada correctamente" if response_status == "ok" else "Sincronización en progreso",
            "stats": stats,
            "logs": OtaSyncLogSerializer(recent_logs, many=True).data,
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        return Response({
            "status": "error",
            "message": str(e),
            "logs": [],
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def google_enable_watch(request: Request) -> Response:
    """Activa el webhook (watch channel) para un mapeo de Google.

    Body: { "mapping_id": 1, "callback_base_url": "https://tu-dominio" }
    """
    if not GOOGLE_AVAILABLE:
        return Response({"status": "error", "message": "Google API no disponible"}, status=status.HTTP_400_BAD_REQUEST)

    mapping_id = request.data.get("mapping_id")
    hotel_id = request.data.get("hotel_id")
    base_url = request.data.get("callback_base_url")
    if not base_url:
        base_url = settings.EXTERNAL_BASE_URL or f"{request.scheme}://{request.get_host()}"

    # Caso 1: mapping_id específico
    if mapping_id:
        try:
            mapping = OtaRoomMapping.objects.get(id=mapping_id, provider=OtaProvider.GOOGLE)
        except OtaRoomMapping.DoesNotExist:
            return Response({"status": "error", "message": "mapping no encontrado o no es Google"}, status=status.HTTP_404_NOT_FOUND)
        result = enable_webhook_watch(mapping, base_url)
        http_status = status.HTTP_200_OK if result.get("status") == "ok" else status.HTTP_400_BAD_REQUEST
        return Response(result, status=http_status)

    # Caso 2: por hotel - activar para todos los mapeos Google activos
    if hotel_id:
        mappings = OtaRoomMapping.objects.filter(provider=OtaProvider.GOOGLE, hotel_id=hotel_id, is_active=True)
        if not mappings.exists():
            return Response({"status": "error", "message": "No hay mapeos Google activos para este hotel"}, status=status.HTTP_404_NOT_FOUND)
        ok = 0
        errors = []
        details = []
        for m in mappings:
            try:
                r = enable_webhook_watch(m, base_url)
                if r.get("status") == "ok":
                    ok += 1
                    details.append({"mapping_id": m.id, "channel_id": r.get("channel_id")})
                else:
                    errors.append({"mapping_id": m.id, "reason": r})
            except Exception as e:
                errors.append({"mapping_id": m.id, "error": str(e)})
        return Response({"status": "ok" if ok > 0 else "error", "enabled": ok, "errors": errors, "details": details}, status=status.HTTP_200_OK if ok > 0 else status.HTTP_400_BAD_REQUEST)

    return Response({"status": "error", "message": "Debe enviar mapping_id o hotel_id"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def google_webhook_notify(request: Request) -> Response:
    """Webhook receptor de Google Calendar.

    Google envía headers con:
    - X-Goog-Channel-ID, X-Goog-Channel-Token, X-Goog-Resource-ID, X-Goog-Resource-State
    """
    chan_id = request.headers.get("X-Goog-Channel-ID")
    token = request.headers.get("X-Goog-Channel-Token")
    resource_id = request.headers.get("X-Goog-Resource-ID")
    state = request.headers.get("X-Goog-Resource-State")

    if not (chan_id and token and resource_id):
        return Response({"status": "ignored"}, status=status.HTTP_200_OK)

    mapping = (
        OtaRoomMapping.objects.filter(
            provider=OtaProvider.GOOGLE,
            google_watch_channel_id=chan_id,
            google_webhook_token=token,
            google_resource_id=resource_id,
        ).first()
    )
    if not mapping:
        return Response({"status": "ignored"}, status=status.HTTP_200_OK)

    # Encolar import inmediato para este mapping
    try:
        from .tasks import import_google_for_mapping_task
        import_google_for_mapping_task.delay(mapping.id)
    except Exception:
        pass

    return Response({"status": "ok", "state": state}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def events_stream(request: Request):
    """SSE: emite eventos de OTAs (reservations_updated) para refrescar UI sin F5.

    Opcional: ?hotel=<id> para filtrar por hotel.
    """
    hotel_id = request.GET.get("hotel")
    redis_host = os.environ.get("REDIS_HOST", "redis")
    r = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
    p = r.pubsub()
    channels = ["otas:events"]
    if hotel_id:
        channels.append(f"otas:events:{hotel_id}")
    p.subscribe(*channels)

    def event_stream():
        # Enviar cabecera inicial
        yield "event: ping\ndata: {}\n\n"
        last_heartbeat = time.time()
        try:
            while True:
                message = p.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("type") == "message":
                    data = message.get("data")
                    yield f"event: update\ndata: {data}\n\n"
                # Heartbeat cada 15s
                if time.time() - last_heartbeat > 15:
                    yield "event: ping\ndata: {}\n\n"
                    last_heartbeat = time.time()
        finally:
            try:
                p.close()
            except Exception:
                pass

    resp = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    resp['Cache-Control'] = 'no-cache'
    resp['X-Accel-Buffering'] = 'no'
    return resp
