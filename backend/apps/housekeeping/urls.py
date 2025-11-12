from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CleaningStaffViewSet, HousekeepingTaskViewSet, HousekeepingConfigViewSet

router = DefaultRouter()
router.register(r"housekeeping/staff", CleaningStaffViewSet, basename="housekeeping-staff")
router.register(r"housekeeping/tasks", HousekeepingTaskViewSet, basename="housekeeping-task")
router.register(r"housekeeping/config", HousekeepingConfigViewSet, basename="housekeeping-config")

urlpatterns = [
    path("", include(router.urls)),
]

