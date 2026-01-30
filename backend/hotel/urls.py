from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.core.views import CurrencyViewSet, HotelViewSet, StatusSummaryView, GlobalSummaryView
from apps.rooms.views import RoomViewSet
from apps.reservations.views import ReservationViewSet
from apps.locations.views import CountryViewSet, StateViewSet, CityViewSet
from apps.users.views import me_view
from apps.dashboard.views import DashboardMetricsListCreateView, DashboardMetricsDetailView

router = DefaultRouter()
router.register(r"hotels", HotelViewSet, basename="hotel")
router.register(r"currencies", CurrencyViewSet, basename="currency")
router.register(r"rooms", RoomViewSet, basename="room")
router.register(r"reservations", ReservationViewSet, basename="reservation")
router.register(r"countries", CountryViewSet, basename="country")
router.register(r"states", StateViewSet, basename="state")
router.register(r"cities", CityViewSet, basename="city")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", lambda request: JsonResponse({"status": "ok"})),
    # Endpoints específicos de reservas (can-book, quote-range, etc.)
    path("api/", include("apps.reservations.urls")),
    # Resto de endpoints
    path("api/", include(router.urls)),  # router principal
    path("api/", include("apps.enterprises.urls")),
    path("api/", include("apps.users.urls")),
    path("api/rates/", include("apps.rates.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
    path("api/status/summary/", StatusSummaryView.as_view(), name="status-summary"),
    path("api/status/global-summary/", GlobalSummaryView.as_view(), name="global-summary"),
    path("api/auth/", include("rest_framework.urls")),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/me/", me_view, name="me"),
    path("api/payments/", include("apps.payments.urls")),
    path("api/calendar/", include("apps.calendar.urls")),
    path("api/", include("apps.notifications.urls")),
    path("api/invoicing/", include("apps.invoicing.urls")),
    path("api/otas/", include("apps.otas.urls")),
    path("api/", include("apps.housekeeping.urls")),
    path("api/chatbot/", include("apps.chatbot.urls")),
]

# Servir archivos media
# En desarrollo usa static(), en producción usa serve() para archivos locales
if not getattr(settings, 'USE_CLOUDINARY', False):
    if settings.DEBUG:
        # Desarrollo: usar static() helper
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    else:
        # Producción: usar serve() para servir archivos media
        urlpatterns += [
            path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
        ]