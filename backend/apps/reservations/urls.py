from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReservationViewSet, AvailabilityView

router = DefaultRouter()
router.register(r"reservations", ReservationViewSet, basename="reservation")
urlpatterns = [
    path("reservations/availability/", AvailabilityView.as_view(), name="reservations-availability"),
    path("", include(router.urls)),
]