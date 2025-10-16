from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReservationViewSet,
    AvailabilityView,
    pricing_quote,
    pricing_daily_summary,
    reservation_pricing_summary,
    reservation_charges,
    reservation_charge_delete,
    reservation_payments,
    reservation_commission,
    reservation_history,
    can_book,
    quote_range,
    quote,
    auto_mark_no_show,
)

router = DefaultRouter()
router.register(r"reservations", ReservationViewSet, basename="reservation")
urlpatterns = [
    path("reservations/availability/", AvailabilityView.as_view(), name="reservations-availability"),
    path("reservations/pricing/quote/", pricing_quote, name="pricing-quote"),
    path("reservations/can-book/", can_book, name="reservations-can-book"),
    path("reservations/quote-range/", quote_range, name="reservations-quote-range"),
    path("reservations/quote/", quote, name="reservations-quote"),
    path("reservations/pricing/daily-summary/", pricing_daily_summary, name="pricing-daily-summary"),
    path("reservations/pricing/reservation-summary/<int:pk>/", reservation_pricing_summary, name="reservation-pricing-summary"),
    path("reservations/<int:pk>/charges/", reservation_charges, name="reservation-charges"),
    path("reservations/<int:pk>/charges/<int:charge_id>/", reservation_charge_delete, name="reservation-charge-delete"),
    path("reservations/<int:pk>/payments/", reservation_payments, name="reservation-payments"),
    path("reservations/<int:pk>/commission/", reservation_commission, name="reservation-commission"),
    path("reservations/<int:pk>/history/", reservation_history, name="reservation-history"),
    path("reservations/auto-no-show/", auto_mark_no_show, name="auto-no-show"),
    path("", include(router.urls)),
]