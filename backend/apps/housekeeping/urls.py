from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CleaningStaffViewSet, HousekeepingTaskViewSet, HousekeepingConfigViewSet,
    CleaningZoneViewSet, TaskTemplateViewSet, ChecklistViewSet,
    ChecklistItemViewSet, TaskChecklistCompletionViewSet
)

router = DefaultRouter()
router.register(r"housekeeping/staff", CleaningStaffViewSet, basename="housekeeping-staff")
router.register(r"housekeeping/tasks", HousekeepingTaskViewSet, basename="housekeeping-task")
router.register(r"housekeeping/config", HousekeepingConfigViewSet, basename="housekeeping-config")
router.register(r"housekeeping/zones", CleaningZoneViewSet, basename="housekeeping-zone")
router.register(r"housekeeping/templates", TaskTemplateViewSet, basename="housekeeping-template")
router.register(r"housekeeping/checklists", ChecklistViewSet, basename="housekeeping-checklist")
router.register(r"housekeeping/checklist-items", ChecklistItemViewSet, basename="housekeeping-checklist-item")
router.register(r"housekeeping/task-checklist-completions", TaskChecklistCompletionViewSet, basename="housekeeping-task-checklist-completion")

urlpatterns = [
    path("", include(router.urls)),
]

