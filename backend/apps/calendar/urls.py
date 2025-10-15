from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'events', views.CalendarEventViewSet, basename='calendar-events')
router.register(r'maintenance', views.RoomMaintenanceViewSet, basename='room-maintenance')
router.register(r'views', views.CalendarViewViewSet, basename='calendar-views')

urlpatterns = [
    path('', include(router.urls)),
    path('availability-matrix/', views.availability_matrix, name='availability-matrix'),
]
