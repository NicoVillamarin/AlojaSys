from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RoomViewSet, RoomTypeViewSet

router = DefaultRouter()
router.register(r'rooms', RoomViewSet, basename="room")
router.register(r'room-types', RoomTypeViewSet, basename="room-type")

urlpatterns = [
    path('', include(router.urls)),
]