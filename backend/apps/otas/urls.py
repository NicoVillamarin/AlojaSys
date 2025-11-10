from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from . import api

# Router para endpoints estándar
router = DefaultRouter()
router.register(r"configs", views.OtaConfigViewSet, basename="ota-configs")
router.register(r"mappings", views.OtaRoomMappingViewSet, basename="ota-mappings")
router.register(r"jobs", views.OtaSyncJobViewSet, basename="ota-jobs")
router.register(r"logs", views.OtaSyncLogViewSet, basename="ota-logs")
router.register(r"room-type-mappings", views.OtaRoomTypeMappingViewSet, basename="ota-room-type-mappings")
router.register(r"rate-plan-mappings", views.OtaRatePlanMappingViewSet, basename="ota-rate-plan-mappings")

urlpatterns = [
    # Endpoints personalizados (tienen prioridad)
    path("", api.list_ota_configs, name="otas-list"),  # GET /api/otas/
    path("sync/", api.sync_otas, name="otas-sync"),  # POST /api/otas/sync/
    # Webhooks OTAs
    path("webhooks/booking/", views.booking_webhook, name="otas-webhook-booking"),
    path("webhooks/airbnb/", views.airbnb_webhook, name="otas-webhook-airbnb"),
    # Google Calendar webhooks
    path("google/webhooks/notify/", api.google_webhook_notify, name="otas-google-webhook"),
    path("google/webhooks/enable/", api.google_enable_watch, name="otas-google-enable"),
    
    # Endpoints iCal y ARI
    path("ical/hotel/<int:hotel_id>.ics", views.ical_export_hotel, name="otas-ical-hotel"),
    path("ical/room/<int:room_id>.ics", views.ical_export_room, name="otas-ical-room"),
    path("ari/push/", views.push_ari, name="otas-ari-push"),
    # SSE events stream
    path("events/stream/", api.events_stream, name="otas-events-stream"),
    
    # Endpoints estándar (ViewSets)
    path("", include(router.urls)),
]