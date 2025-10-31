from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"configs", views.OtaConfigViewSet, basename="ota-configs")
router.register(r"mappings", views.OtaRoomMappingViewSet, basename="ota-mappings")
router.register(r"jobs", views.OtaSyncJobViewSet, basename="ota-jobs")
router.register(r"logs", views.OtaSyncLogViewSet, basename="ota-logs")
router.register(r"room-type-mappings", views.OtaRoomTypeMappingViewSet, basename="ota-room-type-mappings")
router.register(r"rate-plan-mappings", views.OtaRatePlanMappingViewSet, basename="ota-rate-plan-mappings")

urlpatterns = [
    path("ical/hotel/<int:hotel_id>.ics", views.ical_export_hotel, name="otas-ical-hotel"),
    path("ical/room/<int:room_id>.ics", views.ical_export_room, name="otas-ical-room"),
    path("ari/push/", views.push_ari, name="otas-ari-push"),
    path("", include(router.urls)),
]