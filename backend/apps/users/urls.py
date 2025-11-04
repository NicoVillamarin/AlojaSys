from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserProfileViewSet,
    PermissionViewSet,
    GroupViewSet,
    UserPermissionsViewSet
)

router = DefaultRouter()
router.register(r"users", UserProfileViewSet, basename="user-profile")
router.register(r"permissions", PermissionViewSet, basename="permission")
router.register(r"groups", GroupViewSet, basename="group")
router.register(r"user-permissions", UserPermissionsViewSet, basename="user-permissions")

urlpatterns = [
    path("", include(router.urls)),
]

