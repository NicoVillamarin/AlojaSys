from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ping, create_checkout_preference, create_brick_intent, process_card_payment, webhook, get_reservation_payments,
    PaymentMethodViewSet, PaymentPolicyViewSet, CancellationPolicyViewSet, RefundPolicyViewSet, RefundViewSet, RefundVoucherViewSet, process_deposit_payment, process_full_payment, rotate_payment_tokens,
    BankTransferPaymentViewSet, upload_bank_transfer_receipt, create_deposit, generate_invoice_from_payment_extended, PaymentViewSet, generate_receipt_from_payment, generate_receipt_from_refund,
    send_payment_link_whatsapp,
)
from .views_collections import PaymentCollectionViewSet
from .views_reconciliation import BankReconciliationViewSet, ReconciliationMatchViewSet, BankReconciliationConfigViewSet
from .views_postnet import settle_postnet_payment

router = DefaultRouter()
router.register(r"methods", PaymentMethodViewSet, basename="payment-method")
router.register(r"policies", PaymentPolicyViewSet, basename="payment-policy")
router.register(r"cancellation-policies", CancellationPolicyViewSet, basename="cancellation-policy")
router.register(r"refund-policies", RefundPolicyViewSet, basename="refund-policy")
router.register(r"refunds", RefundViewSet, basename="refund")
router.register(r"refund-vouchers", RefundVoucherViewSet, basename="refund-voucher")
router.register(r"bank-transfers", BankTransferPaymentViewSet, basename="bank-transfer")
router.register(r"collections", PaymentCollectionViewSet, basename="payment-collection")
router.register(r"reconciliations", BankReconciliationViewSet, basename="bank-reconciliation")
router.register(r"reconciliation-matches", ReconciliationMatchViewSet, basename="reconciliation-match")
router.register(r"reconciliation-configs", BankReconciliationConfigViewSet, basename="reconciliation-config")
router.register(r"", PaymentViewSet, basename="payment")

urlpatterns = [
    path("ping/", ping, name="payments-ping"),
    path("checkout-preference/", create_checkout_preference, name="payments-checkout-preference"),
    path("brick-intent/", create_brick_intent, name="payments-brick-intent"),
    path("webhook/", webhook, name="payments-webhook"),
    path("send-payment-link-whatsapp/", send_payment_link_whatsapp, name="payments-send-payment-link-whatsapp"),
    path("process-card/", process_card_payment, name="payments-process-card"),
    path("process-deposit/", process_deposit_payment, name="payments-process-deposit"),
    path("process-full-payment/", process_full_payment, name="payments-process-full-payment"),
    path("reservation/<int:reservation_id>/payments/", get_reservation_payments, name="payments-reservation-payments"),
    path("rotate-tokens/", rotate_payment_tokens, name="payments-rotate-tokens"),
    path("upload-bank-transfer/", upload_bank_transfer_receipt, name="payments-upload-bank-transfer"),
    path("settle-postnet/<int:payment_id>/", settle_postnet_payment, name="payments-settle-postnet"),
    
    # Endpoints para señas (pagos parciales)
    path("create-deposit/", create_deposit, name="payments-create-deposit"),
    path("generate-invoice-from-payment/<int:payment_id>/", generate_invoice_from_payment_extended, name="payments-generate-invoice-extended"),
    path("generate-receipt/<int:payment_id>/", generate_receipt_from_payment, name="payments-generate-receipt"),
    path("generate-refund-receipt/<int:refund_id>/", generate_receipt_from_refund, name="payments-generate-refund-receipt"),
    
    path("", include(router.urls)),
]