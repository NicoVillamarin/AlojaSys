from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.core.views import HotelViewSet, StatusSummaryView, GlobalSummaryView
from apps.rooms.views import RoomViewSet
from apps.reservations.views import ReservationViewSet, AvailabilityView
from apps.locations.views import CountryViewSet, StateViewSet, CityViewSet
from apps.users.views import me_view
from apps.dashboard.views import DashboardMetricsListCreateView, DashboardMetricsDetailView
router = DefaultRouter()
router.register(r"hotels", HotelViewSet, basename="hotel")
router.register(r"rooms", RoomViewSet, basename="room")
router.register(r"reservations", ReservationViewSet, basename="reservation")
router.register(r"countries", CountryViewSet, basename="country")
router.register(r"states", StateViewSet, basename="state")
router.register(r"cities", CityViewSet, basename="city")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", lambda request: JsonResponse({"status": "ok"})),
    path("api/", include(router.urls)),  # <- ÚNICO include de router
    path("api/", include("apps.enterprises.urls")),
    path("api/", include("apps.reservations.urls")),
    path("api/", include("apps.users.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
    path("api/status/summary/", StatusSummaryView.as_view(), name="status-summary"),
    path("api/status/global-summary/", GlobalSummaryView.as_view(), name="global-summary"),
    path("api/reservations/availability/", AvailabilityView.as_view(), name="reservations-availability"),
    path("api/auth/", include("rest_framework.urls")),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/me/", me_view, name="me"),
]