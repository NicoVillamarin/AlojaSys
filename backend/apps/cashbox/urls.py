from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CashSessionViewSet, CashMovementViewSet


router = DefaultRouter()
router.register(r"sessions", CashSessionViewSet, basename="cash-session")
router.register(r"movements", CashMovementViewSet, basename="cash-movement")


urlpatterns = [
    path("", include(router.urls)),
]

