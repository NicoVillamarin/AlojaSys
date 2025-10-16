from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ping, create_checkout_preference, create_brick_intent, process_card_payment, webhook, get_reservation_payments,
    PaymentMethodViewSet, PaymentPolicyViewSet, CancellationPolicyViewSet, RefundPolicyViewSet, RefundViewSet, process_deposit_payment,
)

router = DefaultRouter()
router.register(r"methods", PaymentMethodViewSet, basename="payment-method")
router.register(r"policies", PaymentPolicyViewSet, basename="payment-policy")
router.register(r"cancellation-policies", CancellationPolicyViewSet, basename="cancellation-policy")
router.register(r"refund-policies", RefundPolicyViewSet, basename="refund-policy")
router.register(r"refunds", RefundViewSet, basename="refund")

urlpatterns = [
    path("ping/", ping, name="payments-ping"),
    path("checkout-preference/", create_checkout_preference, name="payments-checkout-preference"),
    path("brick-intent/", create_brick_intent, name="payments-brick-intent"),
    path("webhook/", webhook, name="payments-webhook"),
    path("process-card/", process_card_payment, name="payments-process-card"),
    path("process-deposit/", process_deposit_payment, name="payments-process-deposit"),
    path("reservation/<int:reservation_id>/payments/", get_reservation_payments, name="payments-reservation-payments"),
    path("", include(router.urls)),
]