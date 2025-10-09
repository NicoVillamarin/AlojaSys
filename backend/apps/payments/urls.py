from django.urls import path
from .views import ping, create_checkout_preference, create_brick_intent, process_card_payment, webhook

urlpatterns = [
    path("ping/", ping, name="payments-ping"),
    path("checkout-preference/", create_checkout_preference, name="payments-checkout-preference"),
    path("brick-intent/", create_brick_intent, name="payments-brick-intent"),
    path("webhook/", webhook, name="payments-webhook"),
    path("process-card/", process_card_payment, name="payments-process-card"),
]