"""
API REST para el módulo OTA.

Endpoints personalizados para gestión de OTAs, sincronización y mapeos.
"""
from rest_framework import permissions, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.request import Request

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
                # Import si corresponde
                if mapping.sync_direction in [
                    OtaRoomMapping.SyncDirection.IMPORT,
                    OtaRoomMapping.SyncDirection.BOTH,
                ] and mapping.ical_in_url:
                    try:
                        from .models import OtaSyncJob
                        job = OtaSyncJob.objects.create(
                            hotel=mapping.hotel,
                            provider=mapping.provider,
                            job_type=OtaSyncJob.JobType.IMPORT_ICS,
                            status=OtaSyncJob.JobStatus.RUNNING,
                            stats={"mapping_id": mapping.id},
                        )
                        result = ICALSyncService.import_reservations(mapping, job=job)
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

