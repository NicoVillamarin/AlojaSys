from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AfipConfigViewSet,
    InvoiceViewSet,
    InvoiceItemViewSet,
    GenerateInvoiceFromPaymentView,
    InvoicesByReservationView,
    CreateInvoiceFromReservationView,
    get_afip_status,
    TestCertificateValidationView,
    TestAfipConnectionView,
    TestInvoiceGenerationView,
    TestAfipStatusView,
    ListCertificatesView,
    TestPDFGenerationView,
)

router = DefaultRouter()
router.register(r'afip-configs', AfipConfigViewSet, basename='afip-config')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'invoice-items', InvoiceItemViewSet, basename='invoice-item')

# IMPORTANTE: las rutas específicas deben ir ANTES del router
urlpatterns = [
    # Nuevos endpoints de facturación (específicos)
    path('invoices/generate-from-payment/<int:payment_id>/', GenerateInvoiceFromPaymentView.as_view(), name='generate-invoice-from-payment'),
    path('invoices/by-reservation/<int:reservation_id>/', InvoicesByReservationView.as_view(), name='invoices-by-reservation'),

    # Acciones específicas de facturas (las acciones del ViewSet ya exponen rutas REST:
    # /invoices/<id>/send_to_afip, /pdf, /retry, /cancel, /summary, etc.)
    path('invoices/create-from-reservation/', CreateInvoiceFromReservationView.as_view(), name='create-invoice-from-reservation'),

    # Estado de AFIP
    path('afip/status/', get_afip_status, name='afip-status'),

    # Endpoints de prueba para certificados AFIP
    path('test/certificates/validate/', TestCertificateValidationView.as_view(), name='test-certificates-validate'),
    path('test/afip/connection/', TestAfipConnectionView.as_view(), name='test-afip-connection'),
    path('test/invoices/generate/', TestInvoiceGenerationView.as_view(), name='test-invoices-generate'),
    path('test/afip/status/', TestAfipStatusView.as_view(), name='test-afip-status'),
    path('certificates/list/', ListCertificatesView.as_view(), name='list-certificates'),
    path('test/pdf/generate/', TestPDFGenerationView.as_view(), name='test-pdf-generate'),

    # Incluir todas las rutas del router (al final para evitar colisiones)
    path('', include(router.urls)),
]
