from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CurrencyViewSet, HotelViewSet, StatusSummaryView, GlobalSummaryView, validate_reservation_action, validate_reservation_dates, get_hotel_business_config

router = DefaultRouter()
router.register(r"hotels", HotelViewSet, basename="hotel")
router.register(r"currencies", CurrencyViewSet, basename="currency")

urlpatterns = [
    path("", include(router.urls)),
    path("status/summary/", StatusSummaryView.as_view(), name="status-summary"),
    path("business-rules/validate-reservation-action/", validate_reservation_action, name="validate-reservation-action"),
    path("business-rules/validate-reservation-dates/", validate_reservation_dates, name="validate-reservation-dates"),
    path("business-rules/hotel-config/<int:hotel_id>/", get_hotel_business_config, name="hotel-business-config"),
]