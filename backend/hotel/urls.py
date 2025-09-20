from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.core.views import HotelViewSet, StatusSummaryView
from apps.rooms.views import RoomViewSet
from apps.reservations.views import ReservationViewSet, AvailabilityView
from apps.locations.views import CountryViewSet, StateViewSet, CityViewSet

router = DefaultRouter()
router.register(r"hotels", HotelViewSet, basename="hotel")
router.register(r"rooms", RoomViewSet, basename="room")
router.register(r"reservations", ReservationViewSet, basename="reservation")
router.register(r"countries", CountryViewSet, basename="country")
router.register(r"states", StateViewSet, basename="state")
router.register(r"cities", CityViewSet, basename="city")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),  # <- ÚNICO include de router
    path("api/status/summary/", StatusSummaryView.as_view(), name="status-summary"),
    path("api/reservations/availability/", AvailabilityView.as_view(), name="reservations-availability"),
    path("api/auth/", include("rest_framework.urls")),
]