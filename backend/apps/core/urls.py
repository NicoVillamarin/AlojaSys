from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HotelViewSet, StatusSummaryView

router = DefaultRouter()
router.register(r"hotels", HotelViewSet, basename="hotel")

urlpatterns = [
    path("", include(router.urls)),
    path("status/summary/", StatusSummaryView.as_view(), name="status-summary"),
]