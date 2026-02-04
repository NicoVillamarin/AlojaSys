from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from decimal import Decimal
import os
import mercadopago
from uuid import uuid4
from rest_framework import serializers
from django.utils import timezone
import logging
import re

logger = logging.getLogger(__name__)

from apps.reservations.models import Reservation, ReservationStatus, Payment
from .models import PaymentGatewayConfig, PaymentIntent, PaymentIntentStatus, PaymentMethod, PaymentPolicy, CancellationPolicy, RefundPolicy, Refund, RefundStatus, RefundReason, RefundLog, RefundVoucher, RefundVoucherStatus, BankTransferPayment, BankTransferStatus
from .serializers import PaymentMethodSerializer, PaymentPolicySerializer, CancellationPolicySerializer, CancellationPolicyCreateSerializer, RefundPolicySerializer, RefundPolicyCreateSerializer, RefundSerializer, RefundCreateSerializer, RefundStatusUpdateSerializer, RefundVoucherSerializer, RefundVoucherCreateSerializer, RefundVoucherUseSerializer, PaymentGatewayConfigSerializer, BankTransferPaymentSerializer, BankTransferPaymentCreateSerializer, BankTransferPaymentUpdateSerializer, BankTransferPaymentListSerializer, CreateDepositSerializer, DepositResponseSerializer, GenerateInvoiceFromPaymentSerializer
from apps.core.models import Hotel


class PaymentIntentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentIntent
        fields = [
            'id', 'amount', 'currency', 'description', 'status', 
            'mp_preference_id', 'mp_payment_id', 'external_reference',
            'created_at', 'updated_at'
        ]

class PaymentSerializer(serializers.ModelSerializer):
    reservation_id = serializers.IntegerField(source='reservation.id', read_only=True)
    reservation_display_name = serializers.CharField(source='reservation.display_name', read_only=True)
    guest_name = serializers.CharField(source='reservation.guest_name', read_only=True)
    hotel_name = serializers.CharField(source='reservation.hotel.name', read_only=True)
    receipt_pdf_url = serializers.URLField(read_only=True, allow_null=True)
    receipt_number = serializers.CharField(read_only=True, allow_null=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'date', 'method', 'amount', 'currency', 'status', 'is_deposit', 
            'created_at', 'reservation_id', 'reservation_display_name', 
            'guest_name', 'hotel_name', 'receipt_pdf_url', 'receipt_number', 'notes'
        ]


def _resolve_gateway_for_hotel(hotel):
    cfg = PaymentGatewayConfig.resolve_for_hotel(hotel)
    if cfg:
        return cfg
    # Fallback a variables de entorno (útil en desarrollo)
    class EnvCfg:
        provider = "mercado_pago"
        public_key = os.environ.get("MP_PUBLIC_KEY", "")
        access_token = os.environ.get("MP_ACCESS_TOKEN", "")
        integrator_id = os.environ.get("MP_INTEGRATOR_ID", "")
        is_test = True
        country_code = (hotel.country.code2 if getattr(hotel, "country", None) else "") or "AR"
        currency_code = (hotel.country.currency_code if getattr(hotel, "country", None) else "") or "ARS"
        webhook_secret = os.environ.get("MP_WEBHOOK_SECRET", "")
    env_cfg = EnvCfg()
    if not env_cfg.access_token:
        return None
    return env_cfg


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ping(request):
    return Response({"payments": "ok"}, status=200)


class PaymentMethodViewSet(viewsets.ModelViewSet):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]


class PaymentPolicyViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentPolicySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = PaymentPolicy.objects.all().select_related("hotel").prefetch_related("methods")
        hotel_id = self.request.query_params.get("hotel_id")
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
        return qs.order_by("-is_default", "name")


class CancellationPolicyViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar políticas de cancelación"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CancellationPolicyCreateSerializer
        return CancellationPolicySerializer
    
    def get_queryset(self):
        qs = CancellationPolicy.objects.all().select_related("hotel", "created_by")
        hotel_id = self.request.query_params.get("hotel_id")
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
        return qs.order_by("-is_default", "-is_active", "name")
    
    @action(detail=False, methods=['get'])
    def for_hotel(self, request):
        """Obtiene la política de cancelación activa para un hotel específico"""
        hotel_id = request.query_params.get('hotel_id')
        if not hotel_id:
            return Response(
                {"detail": "hotel_id es requerido"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            hotel = Hotel.objects.get(id=hotel_id)
            policy = CancellationPolicy.resolve_for_hotel(hotel)
            
            if not policy:
                return Response(
                    {"detail": "No hay política de cancelación configurada para este hotel"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = self.get_serializer(policy)
            return Response(serializer.data)
            
        except Hotel.DoesNotExist:
            return Response(
                {"detail": "Hotel no encontrado"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def calculate_cancellation(self, request, pk=None):
        """Calcula las reglas de cancelación para una reserva específica"""
        policy = self.get_object()
        check_in_date = request.data.get('check_in_date')
        room_type = request.data.get('room_type')
        channel = request.data.get('channel')
        
        if not check_in_date:
            return Response(
                {"detail": "check_in_date es requerido"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from datetime import datetime
            check_in = datetime.strptime(check_in_date, '%Y-%m-%d').date()
            rules = policy.get_cancellation_rules(check_in, room_type, channel)
            
            return Response({
                'policy_id': policy.id,
                'policy_name': policy.name,
                'check_in_date': check_in_date,
                'rules': rules
            })
            
        except ValueError:
            return Response(
                {"detail": "Formato de fecha inválido. Use YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def set_default(self, request):
        """Establece una política como predeterminada para un hotel"""
        policy_id = request.data.get('policy_id')
        hotel_id = request.data.get('hotel_id')
        
        if not policy_id or not hotel_id:
            return Response(
                {"detail": "policy_id y hotel_id son requeridos"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            policy = CancellationPolicy.objects.get(id=policy_id, hotel_id=hotel_id)
            
            # Quitar default de otras políticas del mismo hotel
            CancellationPolicy.objects.filter(
                hotel_id=hotel_id, 
                is_default=True
            ).update(is_default=False)
            
            # Establecer esta como default
            policy.is_default = True
            policy.save(update_fields=['is_default'])
            
            return Response({
                'success': True,
                'message': f'Política "{policy.name}" establecida como predeterminada'
            })
            
        except CancellationPolicy.DoesNotExist:
            return Response(
                {"detail": "Política no encontrada"}, 
                status=status.HTTP_404_NOT_FOUND
            )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_reservation_payments(request, reservation_id):
    """Obtener todos los pagos de una reserva específica (PaymentIntent + Payment manuales)"""
    try:
        reservation = get_object_or_404(Reservation, pk=reservation_id)
        
        # Verificar que el usuario tenga acceso a esta reserva
        # (esto debería implementarse según tu lógica de permisos)
        
        # Obtener PaymentIntent (pagos online)
        payment_intents = PaymentIntent.objects.filter(reservation=reservation).order_by('-created_at')
        payment_intents_data = PaymentIntentSerializer(payment_intents, many=True).data
        
        # Obtener Payment (pagos manuales)
        manual_payments = Payment.objects.filter(reservation=reservation).order_by('-created_at')
        manual_payments_data = PaymentSerializer(manual_payments, many=True).data
        
        # Combinar y normalizar ambos tipos de pagos
        all_payments = []
        
        # Agregar PaymentIntent con tipo 'online'
        for pi in payment_intents_data:
            all_payments.append({
                'id': f"pi_{pi['id']}",
                'type': 'online',
                'amount': pi['amount'],
                'method': 'mercado_pago',
                'status': pi['status'],
                'created_at': pi['created_at'],
                'description': pi['description'],
                'reference': pi['mp_payment_id'],
                'currency': pi['currency']
            })
        
        # Agregar Payment con tipo 'manual'
        for mp in manual_payments_data:
            all_payments.append({
                'id': f"p_{mp['id']}",
                'type': 'manual',
                'amount': mp['amount'],
                'method': mp['method'],
                'status': 'approved',  # Los pagos manuales se consideran aprobados
                'created_at': mp['created_at'],
                'description': f"Pago {mp['method']}",
                'reference': None,
                'currency': 'ARS'  # Por defecto
            })
        
        # Ordenar por fecha de creación (más reciente primero)
        all_payments.sort(key=lambda x: x['created_at'], reverse=True)
        
        return Response({
            "results": all_payments,
            "count": len(all_payments),
            "reservation_id": reservation_id,
            "reservation_total": str(reservation.total_price),
            "payment_intents_count": payment_intents.count(),
            "manual_payments_count": manual_payments.count()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"detail": f"Error obteniendo pagos: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_checkout_preference(request):
    reservation_id = request.data.get("reservation_id")
    if not reservation_id:
        return Response({"detail": "reservation_id es requerido"}, status=status.HTTP_400_BAD_REQUEST)

    reservation = get_object_or_404(Reservation, pk=reservation_id)
    hotel = reservation.hotel
    gateway = _resolve_gateway_for_hotel(hotel)
    if not gateway:
        return Response({"detail": "Configuración de pasarela no disponible"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        amount_raw = request.data.get("amount")
        amount = Decimal(str(amount_raw)) if amount_raw is not None else reservation.total_price
    except Exception:
        return Response({"detail": "amount inválido"}, status=status.HTTP_400_BAD_REQUEST)

    currency = getattr(gateway, "currency_code", None) or (hotel.country.currency_code if getattr(hotel, "country", None) else None) or "ARS"
    title = f"Reserva {reservation.id}"
    if getattr(reservation, "room", None):
        title = f"Reserva {reservation.id} - {reservation.room.name}"

    external_reference = f"reservation:{reservation.id}|hotel:{hotel.id}"
    notification_url = os.environ.get("MP_WEBHOOK_URL")  # opcional; si tenés un dominio/ngrok

    sdk = mercadopago.SDK(gateway.access_token)
    # Email de respaldo para sandbox si la reserva no lo tiene
    payer_email = getattr(reservation, "guest_email", "") or "test_user@example.com"

    preference_data = {
        "items": [
            {
                "title": title,
                "quantity": 1,
                "unit_price": float(amount),
                "currency_id": currency,
            }
        ],
        "payer": {"email": payer_email},
        "external_reference": external_reference,
        # Forzar respuesta binaria en sandbox y facilitar pruebas
        "binary_mode": True,
        # Sugerir tarjeta por defecto (sin excluir account_money para evitar errores)
        "payment_methods": {
            "installments": 1,
            "default_payment_method_id": "visa"
        },
        # Metadata útil para rastrear
        "metadata": {
            "reservation_id": str(reservation.id),
            "hotel_id": str(hotel.id),
        },
    }

    # Añadir back_urls/auto_return solo si FRONTEND_URL válido (evita invalid_auto_return en local http)
    frontend_url = os.environ.get("FRONTEND_URL")
    if isinstance(frontend_url, str) and frontend_url.startswith("http"):
        preference_data["back_urls"] = {
            "success": frontend_url.rstrip("/") + "/payment/success",
            "failure": frontend_url.rstrip("/") + "/payment/failure",
            "pending": frontend_url.rstrip("/") + "/payment/pending",
        }
        preference_data["auto_return"] = "approved"
    if notification_url:
        preference_data["notification_url"] = notification_url

    pref_response = sdk.preference().create(preference_data)
    if pref_response.get("status") not in (201, 200):
        return Response({"detail": "Error creando preferencia", "mp": pref_response.get("response")}, status=status.HTTP_502_BAD_GATEWAY)

    pref = pref_response.get("response", {})

    with transaction.atomic():
        PaymentIntent.objects.create(
            reservation=reservation,
            hotel=hotel,
            enterprise=hotel.enterprise if getattr(hotel, "enterprise", None) else None,
            amount=amount,
            currency=currency,
            description=title,
            mp_preference_id=pref.get("id", ""),
            external_reference=external_reference,
            status=PaymentIntentStatus.CREATED,
        )

    return Response(
        {
            "preference_id": pref.get("id"),
            "init_point": pref.get("init_point"),
            "sandbox_init_point": pref.get("sandbox_init_point"),
            "currency": currency,
            "amount": str(amount),
        },
        status=status.HTTP_201_CREATED,
    )


def _extract_primary_guest_phone(reservation: Reservation) -> str:
    """
    Intenta extraer el teléfono del huésped principal desde guests_data.
    Se espera (ideal) formato E.164, pero no lo exigimos estrictamente acá.
    """
    primary = None
    try:
        primary = reservation.get_primary_guest() or None
    except Exception:
        primary = None
    if not isinstance(primary, dict):
        return ""
    for k in ("phone", "phone_number", "guest_phone", "whatsapp", "whatsapp_phone", "telefono", "tel"):
        v = primary.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_payment_link_whatsapp(request):
    """
    Crea un link de pago (Checkout Pro / init_point) y lo envía por WhatsApp
    al huésped principal de la reserva.

    Requiere que el hotel tenga configuración de WhatsApp (Meta/Twilio) y que
    el teléfono esté cargado en guests_data del huésped principal.
    """
    body = request.data or {}
    reservation_id = body.get("reservation_id")
    amount_raw = body.get("amount")
    custom_message = body.get("message")

    if not reservation_id:
        return Response({"detail": "reservation_id es requerido"}, status=400)

    reservation = get_object_or_404(Reservation, pk=reservation_id)
    hotel = reservation.hotel
    gateway = _resolve_gateway_for_hotel(hotel)
    if not gateway:
        return Response({"detail": "Configuración de pasarela no disponible"}, status=400)

    try:
        amount = Decimal(str(amount_raw)) if amount_raw is not None else reservation.total_price
    except Exception:
        return Response({"detail": "amount inválido"}, status=400)

    currency = getattr(gateway, "currency_code", None) or (hotel.country.currency_code if getattr(hotel, "country", None) else None) or "ARS"
    title = f"Reserva {reservation.id}"
    if getattr(reservation, "room", None):
        title = f"Reserva {reservation.id} - {reservation.room.name}"
    external_reference = f"reservation:{reservation.id}|hotel:{hotel.id}"
    notification_url = os.environ.get("MP_WEBHOOK_URL")

    sdk = mercadopago.SDK(gateway.access_token)
    payer_email = getattr(reservation, "guest_email", "") or "test_user@example.com"
    preference_data = {
        "items": [
            {
                "title": title,
                "quantity": 1,
                "unit_price": float(amount),
                "currency_id": currency,
            }
        ],
        "payer": {"email": payer_email},
        "external_reference": external_reference,
        "binary_mode": True,
        "metadata": {
            "reservation_id": str(reservation.id),
            "hotel_id": str(hotel.id),
            "sent_via": "whatsapp",
        },
    }
    frontend_url = os.environ.get("FRONTEND_URL")
    if isinstance(frontend_url, str) and frontend_url.startswith("http"):
        preference_data["back_urls"] = {
            "success": frontend_url.rstrip("/") + "/payment/success",
            "failure": frontend_url.rstrip("/") + "/payment/failure",
            "pending": frontend_url.rstrip("/") + "/payment/pending",
        }
        preference_data["auto_return"] = "approved"
    if notification_url:
        preference_data["notification_url"] = notification_url

    pref_response = sdk.preference().create(preference_data)
    if pref_response.get("status") not in (201, 200):
        return Response({"detail": "Error creando preferencia", "mp": pref_response.get("response")}, status=status.HTTP_502_BAD_GATEWAY)

    pref = pref_response.get("response", {}) or {}
    # Preferir init_point (prod) por sobre sandbox_init_point
    init_point = pref.get("init_point") or pref.get("sandbox_init_point")
    if not init_point:
        return Response({"detail": "No se obtuvo init_point"}, status=502)

    with transaction.atomic():
        PaymentIntent.objects.create(
            reservation=reservation,
            hotel=hotel,
            enterprise=hotel.enterprise if getattr(hotel, "enterprise", None) else None,
            amount=amount,
            currency=currency,
            description=title,
            mp_preference_id=pref.get("id", ""),
            external_reference=external_reference,
            status=PaymentIntentStatus.CREATED,
        )

    to_phone = _extract_primary_guest_phone(reservation)
    if not to_phone:
        return Response(
            {"detail": "La reserva no tiene teléfono del huésped principal cargado (guests_data)."},
            status=400,
        )

    # Construir mensaje
    guest_name = reservation.guest_name or "Hola"
    default_message = (
        f"{guest_name}, te compartimos el link de Mercado Pago para abonar la reserva RES-{reservation.id} "
        f"por {currency} {amount}: {init_point}"
    )
    message = custom_message.strip() if isinstance(custom_message, str) and custom_message.strip() else default_message

    # Enviar por proveedor WhatsApp del hotel (si existe)
    try:
        from apps.chatbot.services import WhatsappChatbotService
        from apps.chatbot.providers.registry import get_adapter_for_config

        service = WhatsappChatbotService()
        cfg = service._build_provider_config(hotel)
        if not cfg:
            return Response({"detail": "El hotel no tiene proveedor WhatsApp configurado."}, status=400)
        adapter = get_adapter_for_config(cfg)
        if not adapter:
            return Response({"detail": "No se pudo resolver el adaptador de WhatsApp."}, status=400)

        adapter.send_message(to_phone, message)
    except Exception as e:
        logger.exception("Error enviando link de pago por WhatsApp")
        return Response({"detail": "No se pudo enviar el mensaje por WhatsApp."}, status=502)

    return Response(
        {
            "success": True,
            "sent_to": re.sub(r"\D", "", to_phone or ""),
            "init_point": init_point,
            "preference_id": pref.get("id"),
        },
        status=200,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_brick_intent(request):
    # Queda como placeholder. Se implementará con Payment Brick.
    return Response({"note": "Próximamente: Payment Brick"}, status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def webhook(request):
    """
    Webhook mejorado con verificación HMAC, idempotencia y actualizaciones atómicas
    """
    # Healthcheck / validación de URL (algunos paneles validan con GET)
    if request.method == "GET":
        return Response({"ok": True, "webhook": "mercadopago"}, status=200)

    from apps.payments.services.webhook_security import WebhookSecurityService
    from apps.payments.services.payment_processor import PaymentProcessorService
    
    # Extraer datos del webhook de forma segura
    webhook_data = WebhookSecurityService.extract_webhook_data(request)
    topic = webhook_data.get('topic')
    payment_id = webhook_data.get('payment_id')
    notification_id = webhook_data.get('notification_id')
    external_reference = webhook_data.get('external_reference')
    
    # Verificar que es un evento de pago
    if topic != "payment" or not payment_id:
        return Response({"received": True, "note": "evento no procesado"}, status=200)
    
    # Obtener configuración de la pasarela para verificación HMAC
    webhook_secret = None
    try:
        # Intentar obtener webhook_secret desde configuración del hotel
        if external_reference:
            from apps.payments.services.payment_processor import PaymentProcessorService
            reservation_id = PaymentProcessorService._extract_reservation_id(external_reference)
            if reservation_id:
                from apps.reservations.models import Reservation
                reservation = Reservation.objects.get(id=reservation_id)
                gateway_config = PaymentGatewayConfig.resolve_for_hotel(reservation.hotel)
                if gateway_config:
                    webhook_secret = gateway_config.webhook_secret
    except Exception as e:
        logger.warning(f"Error obteniendo webhook_secret: {e}")
    
    # Fallback a variable de entorno si no se encontró en configuración
    if not webhook_secret:
        webhook_secret = os.environ.get("MP_WEBHOOK_SECRET", "")
    
    # Verificar firma HMAC si está configurada
    if webhook_secret:
        if not WebhookSecurityService.verify_webhook_signature(request, webhook_secret):
            WebhookSecurityService.log_webhook_security_event(
                'hmac_failed',
                notification_id=notification_id,
                external_reference=external_reference,
                details={'payment_id': payment_id}
            )
            return Response({
                "success": False,
                "error": "Firma HMAC inválida",
                "code": "HMAC_VERIFICATION_FAILED"
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            WebhookSecurityService.log_webhook_security_event(
                'hmac_verified',
                notification_id=notification_id,
                external_reference=external_reference,
                details={'payment_id': payment_id}
            )
    
    # Verificar idempotencia
    if WebhookSecurityService.is_notification_processed(notification_id, external_reference):
        WebhookSecurityService.log_webhook_security_event(
            'duplicate_detected',
            notification_id=notification_id,
            external_reference=external_reference,
            details={'payment_id': payment_id}
        )
        return Response({
            "success": True,
            "processed": False,
            "message": "Notificación ya procesada",
            "code": "DUPLICATE_NOTIFICATION"
        }, status=200)
    
    # Obtener datos del pago desde Mercado Pago
    access_token = os.environ.get("MP_ACCESS_TOKEN", "")
    if not access_token:
        return Response({
            "success": False,
            "error": "ACCESS_TOKEN no configurado",
            "code": "MISSING_ACCESS_TOKEN"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        sdk = mercadopago.SDK(access_token)
        pay_resp = sdk.payment().get(payment_id)
        if pay_resp.get("status") != 200:
            logger.warning(
                "Mercado Pago payment().get() falló | payment_id=%s mp_status=%s mp_response=%s",
                payment_id,
                pay_resp.get("status"),
                pay_resp.get("response"),
            )
            return Response({
                "success": False,
                "error": "No se pudo consultar el pago",
                "code": "MP_API_ERROR",
                "payment_id": payment_id,
                "mp_status": pay_resp.get("status"),
                "mp_response": pay_resp.get("response")
            }, status=status.HTTP_502_BAD_GATEWAY)
        
        payment_data = pay_resp.get("response", {})
        
    except Exception as e:
        logger.exception("Error consultando pago en Mercado Pago")
        return Response({
            "success": False,
            "error": "Error consultando pago",
            "code": "MP_CONNECTION_ERROR"
        }, status=status.HTTP_502_BAD_GATEWAY)
    
    # Procesar pago de forma atómica
    result = PaymentProcessorService.process_webhook_payment(
        payment_data=payment_data,
        webhook_secret=webhook_secret,
        notification_id=notification_id
    )
    
    if result.get('success'):
        # Encolar tarea de post-procesamiento si el pago fue procesado
        if result.get('processed', False):
            from .tasks import process_webhook_post_processing
            
            # Encolar tarea de post-procesamiento de forma asíncrona
            process_webhook_post_processing.delay(
                payment_intent_id=result.get('payment_intent_id'),
                webhook_data=payment_data,
                notification_id=notification_id,
                external_reference=external_reference
            )
            
            logger.info(f"Tarea de post-procesamiento encolada para PaymentIntent {result.get('payment_intent_id')}")
        
        return Response({
            "success": True,
            "processed": result.get('processed', False),
            "payment_intent_id": result.get('payment_intent_id'),
            "status": result.get('status'),
            "message": result.get('message'),
            "post_processing_queued": result.get('processed', False)
        }, status=200)
    else:
        logger.error(f"Error procesando webhook: {result.get('error')}")
        return Response({
            "success": False,
            "error": result.get('error'),
            "code": "PAYMENT_PROCESSING_ERROR"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def process_card_payment(request):
    body = request.data or {}
    reservation_id = body.get("reservation_id")
    token = body.get("token")
    payment_method_id = body.get("payment_method_id")
    installments = int(body.get("installments", 1))
    amount_raw = body.get("amount")
    issuer_id = body.get("issuer_id")
    payer_email = body.get("payer_email")
    doc_type = body.get("doc_type") or body.get("docType")
    doc_number = body.get("doc_number") or body.get("docNumber")

    if not reservation_id or not token or not payment_method_id:
        return Response({"detail": "reservation_id, token y payment_method_id son requeridos"}, status=400)

    reservation = get_object_or_404(Reservation, pk=reservation_id)
    hotel = reservation.hotel
    gateway = _resolve_gateway_for_hotel(hotel)
    if not gateway:
        return Response({"detail": "Configuración de pasarela no disponible"}, status=400)

    try:
        amount = Decimal(str(amount_raw)) if amount_raw is not None else reservation.total_price
    except Exception:
        return Response({"detail": "amount inválido"}, status=400)

    currency = (getattr(gateway, "currency_code", None)
                or (hotel.country.currency_code if getattr(hotel, "country", None) else None)
                or "ARS")
    title = f"Reserva {reservation.id}" + (f" - {reservation.room.name}" if getattr(reservation, "room", None) else "")
    external_reference = f"reservation:{reservation.id}|hotel:{hotel.id}"

    sdk = mercadopago.SDK(gateway.access_token)
    headers = {"X-Idempotency-Key": f"res-{reservation.id}-{uuid4()}"}

    # Débito no acepta cuotas > 1
    try:
        if isinstance(payment_method_id, str) and payment_method_id.lower().startswith("deb"):
            installments = 1
    except Exception:
        pass

    payer = {"email": payer_email or reservation.guest_email or "test_user@example.com"}
    if doc_number:
        payer["identification"] = {"type": doc_type or "DNI", "number": str(doc_number)}

    payment_data = {
        "token": token,
        "transaction_amount": float(amount),
        "installments": installments,
        "payment_method_id": payment_method_id,
        "description": title,
        "external_reference": external_reference,
        "payer": payer,
    }
    if issuer_id:
        payment_data["issuer_id"] = issuer_id

    # El SDK oficial (v2) acepta headers como segundo argumento en algunas versiones.
    # Si no está soportado, usamos la API HTTP directa.
    try:
        mp_resp = sdk.payment().create(payment_data, headers=headers)
    except TypeError:
        import requests
        mp_url = "https://api.mercadopago.com/v1/payments"
        http_resp = requests.post(
            mp_url,
            json=payment_data,
            headers={
                "Authorization": f"Bearer {gateway.access_token}",
                "Content-Type": "application/json",
                **headers,
            },
            timeout=20,
        )
        try:
            body = http_resp.json()
        except Exception:
            body = {"raw": http_resp.text}
        mp_resp = {"status": http_resp.status_code, "response": body}
    if mp_resp.get("status") not in (200, 201):
        return Response({"detail": "Error creando pago", "mp": mp_resp.get("response")}, status=502)

    payment = mp_resp.get("response", {})
    status_detail = payment.get("status")  # approved / rejected / in_process
    status_detail_code = payment.get("status_detail")  # accredited, cc_rejected_*, etc.

    # Registrar/actualizar intent
    intent = PaymentIntent.objects.filter(external_reference=external_reference).order_by("-created_at").first()
    if not intent:
        intent = PaymentIntent.objects.create(
            reservation=reservation,
            hotel=hotel,
            enterprise=hotel.enterprise if getattr(hotel, "enterprise", None) else None,
            amount=amount,
            currency=currency,
            description=title,
            mp_payment_id=str(payment.get("id") or ""),
            external_reference=external_reference,
            status=PaymentIntentStatus.CREATED,
        )
    intent.mp_payment_id = str(payment.get("id") or "")
    intent.status = (
        PaymentIntentStatus.APPROVED if status_detail == "approved"
        else PaymentIntentStatus.REJECTED if status_detail == "rejected"
        else PaymentIntentStatus.CREATED
    )
    intent.save(update_fields=["mp_payment_id", "status", "updated_at"])

    # Confirmar reserva si aprobado y crear registro de pago
    if status_detail == "approved":
        # Crear registro de pago en la tabla Payment
        from apps.reservations.models import Payment
        # Considerar seña si el monto es menor al total de la reserva
        is_deposit_flag = False
        try:
            is_deposit_flag = float(amount) + 0.01 < float(reservation.total_price)
        except Exception:
            is_deposit_flag = False

        Payment.objects.create(
            reservation=reservation,
            date=timezone.now().date(),
            method="card",
            amount=amount,
            is_deposit=is_deposit_flag
        )
        
        # Confirmar reserva si está pendiente
        if reservation.status == ReservationStatus.PENDING:
            reservation.status = ReservationStatus.CONFIRMED
            reservation.save(update_fields=["status", "updated_at"])

    return Response({
        "payment_id": payment.get("id"),
        "status": status_detail,
        "status_detail": status_detail_code,
    }, status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def process_deposit_payment(request):
    """
    Procesa un pago de depósito para una reserva
    """
    try:
        data = request.data
        reservation_id = data.get('reservation')
        amount = data.get('amount')
        method = data.get('method')
        notes = data.get('notes', '')
        
        if not reservation_id or not amount or not method:
            return Response({
                'error': 'Faltan campos requeridos: reservation, amount, method'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener la reserva
        reservation = get_object_or_404(Reservation, id=reservation_id)
        
        # Obtener la política de pago del hotel
        policy = PaymentPolicy.resolve_for_hotel(reservation.hotel)
        if not policy:
            return Response({
                'error': 'No hay política de pago configurada para este hotel'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calcular el depósito requerido
        from .services.payment_calculator import calculate_deposit
        deposit_info = calculate_deposit(policy, reservation.total_price)
        
        if not deposit_info['required']:
            return Response({
                'error': 'No se requiere depósito para esta reserva'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar que el monto sea correcto
        expected_amount = deposit_info['amount']
        if abs(float(amount) - float(expected_amount)) > 0.01:  # Tolerancia de 1 centavo
            return Response({
                'error': f'El monto debe ser ${expected_amount}, se recibió ${amount}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear el pago
        with transaction.atomic():
            # Marcar como seña
            payment = Payment.objects.create(
                reservation=reservation,
                date=timezone.now().date(),
                method=method,
                amount=Decimal(str(amount)),
                is_deposit=True
            )
            
            # Si el depósito se cobra al confirmar, confirmar la reserva
            if policy.deposit_due == PaymentPolicy.DepositDue.CONFIRMATION:
                reservation.status = ReservationStatus.CONFIRMED
                reservation.save(update_fields=['status', 'updated_at'])
                
                # Log del cambio
                from apps.reservations.models import ReservationChangeLog, ReservationChangeEvent
                ReservationChangeLog.objects.create(
                    reservation=reservation,
                    event_type=ReservationChangeEvent.PAYMENT_ADDED,
                    changed_by=request.user,
                    message=f"Depósito de ${amount} pagado con {method}. Reserva confirmada."
                )
        
        return Response({
            'success': True,
            'payment_id': payment.id,
            'reservation_status': reservation.status,
            'message': 'Depósito procesado correctamente'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Error procesando el pago: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def process_full_payment(request):
    """
    Procesa un pago completo para una reserva (efectivo, transferencia, POS)
    """
    try:
        data = request.data
        reservation_id = data.get('reservation')
        amount = data.get('amount')
        method = data.get('method')
        notes = data.get('notes', '')
        
        if not reservation_id or not amount or not method:
            return Response({
                'error': 'Faltan campos requeridos: reservation, amount, method'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar método de pago
        valid_methods = ['cash', 'transfer', 'pos']
        if method not in valid_methods:
            return Response({
                'error': f'Método de pago inválido. Debe ser uno de: {", ".join(valid_methods)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener la reserva
        reservation = get_object_or_404(Reservation, id=reservation_id)
        
        # Validar que el monto sea correcto (debe ser el total de la reserva)
        expected_amount = reservation.total_price
        if abs(float(amount) - float(expected_amount)) > 0.01:  # Tolerancia de 1 centavo
            return Response({
                'error': f'El monto debe ser ${expected_amount}, se recibió ${amount}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear el pago
        with transaction.atomic():
            # Pago total (no es seña)
            payment = Payment.objects.create(
                reservation=reservation,
                date=timezone.now().date(),
                method=method,
                amount=Decimal(str(amount)),
                notes=notes
            )
            
            # Confirmar la reserva si está pendiente
            if reservation.status == ReservationStatus.PENDING:
                reservation.status = ReservationStatus.CONFIRMED
                reservation.save(update_fields=['status', 'updated_at'])
                
                # Log del cambio
                from apps.reservations.models import ReservationChangeLog, ReservationChangeEvent
                ReservationChangeLog.objects.create(
                    reservation=reservation,
                    event_type=ReservationChangeEvent.PAYMENT_ADDED,
                    changed_by=request.user,
                    message=f"Pago completo de ${amount} pagado con {method}. Reserva confirmada."
                )
        
        return Response({
            'success': True,
            'payment_id': payment.id,
            'reservation_status': reservation.status,
            'message': 'Pago completo procesado correctamente'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Error procesando el pago: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RefundPolicyViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar políticas de devolución"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RefundPolicyCreateSerializer
        return RefundPolicySerializer
    
    def get_queryset(self):
        qs = RefundPolicy.objects.all().select_related("hotel", "created_by")
        hotel_id = self.request.query_params.get("hotel_id")
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
        return qs.order_by("-is_default", "-is_active", "name")
    
    @action(detail=False, methods=['get'])
    def for_hotel(self, request):
        """Obtiene la política de devolución activa para un hotel específico"""
        hotel_id = request.query_params.get('hotel_id')
        if not hotel_id:
            return Response(
                {"detail": "hotel_id es requerido"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            hotel = Hotel.objects.get(id=hotel_id)
            policy = RefundPolicy.resolve_for_hotel(hotel)
            
            if not policy:
                return Response(
                    {"detail": "No hay política de devolución configurada para este hotel"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = self.get_serializer(policy)
            return Response(serializer.data)
            
        except Hotel.DoesNotExist:
            return Response(
                {"detail": "Hotel no encontrado"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def calculate_refund(self, request, pk=None):
        """Calcula las reglas de devolución para una reserva específica"""
        policy = self.get_object()
        check_in_date = request.data.get('check_in_date')
        room_type = request.data.get('room_type')
        channel = request.data.get('channel')
        
        if not check_in_date:
            return Response(
                {"detail": "check_in_date es requerido"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from datetime import datetime
            check_in = datetime.strptime(check_in_date, '%Y-%m-%d').date()
            rules = policy.get_refund_rules(check_in, room_type, channel)
            
            return Response({
                'policy_id': policy.id,
                'policy_name': policy.name,
                'check_in_date': check_in_date,
                'rules': rules
            })
            
        except ValueError:
            return Response(
                {"detail": "Formato de fecha inválido. Use YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def set_default(self, request):
        """Establece una política como predeterminada para un hotel"""
        policy_id = request.data.get('policy_id')
        hotel_id = request.data.get('hotel_id')
        
        if not policy_id or not hotel_id:
            return Response(
                {"detail": "policy_id y hotel_id son requeridos"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            policy = RefundPolicy.objects.get(id=policy_id, hotel_id=hotel_id)
            
            # Quitar default de otras políticas del mismo hotel
            RefundPolicy.objects.filter(
                hotel_id=hotel_id, 
                is_default=True
            ).update(is_default=False)
            
            # Establecer esta como default
            policy.is_default = True
            policy.save(update_fields=['is_default'])
            
            return Response({
                'success': True,
                'message': f'Política "{policy.name}" establecida como predeterminada'
            })
            
        except RefundPolicy.DoesNotExist:
            return Response(
                {"detail": "Política no encontrada"}, 
                status=status.HTTP_404_NOT_FOUND
            )


class RefundViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar reembolsos"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RefundCreateSerializer
        elif self.action in ['update_status', 'partial_update']:
            return RefundStatusUpdateSerializer
        return RefundSerializer
    
    def get_queryset(self):
        qs = Refund.objects.all().select_related("reservation", "payment", "created_by")
        
        # Filtro por reserva
        reservation_id = self.request.query_params.get("reservation_id")
        if reservation_id:
            qs = qs.filter(reservation_id=reservation_id)
        
        # Filtro por status (soporta múltiples valores separados por coma)
        status_param = self.request.query_params.get("status")
        if status_param:
            # Dividir por coma y limpiar espacios
            status_list = [s.strip() for s in status_param.split(',') if s.strip()]
            if status_list:
                qs = qs.filter(status__in=status_list)
        
        # Filtro por método de reembolso
        refund_method = self.request.query_params.get("refund_method")
        if refund_method:
            qs = qs.filter(refund_method=refund_method)
        
        # Filtro por búsqueda general
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(reservation_id__icontains=search) |
                Q(amount__icontains=search) |
                Q(reason__icontains=search) |
                Q(external_reference__icontains=search)
            )
        
        return qs.order_by("-created_at")
    
    def create(self, request, *args, **kwargs):
        """Crear un nuevo reembolso y enviar notificación"""
        response = super().create(request, *args, **kwargs)
        
        if response.status_code == 201:  # Si se creó exitosamente
            refund = Refund.objects.get(id=response.data['id'])
            
            # Crear notificación de reembolso creado
            try:
                from apps.notifications.services import NotificationService
                from apps.notifications.models import NotificationType
                NotificationService.create(
                    notification_type=NotificationType.REFUND_AUTO,
                    title="Nuevo reembolso creado",
                    message=f"Se ha creado un reembolso de ${refund.amount} para la reserva #RES-{refund.reservation.id} en {refund.reservation.hotel.name}. Estado: {refund.get_status_display()}",
                    user_id=request.user.id,
                    hotel_id=refund.reservation.hotel.id,
                    reservation_id=refund.reservation.id,
                    metadata={
                        'reservation_code': f"RES-{refund.reservation.id}",
                        'hotel_name': refund.reservation.hotel.name,
                        'amount': str(refund.amount),
                        'status': 'created',
                        'refund_id': refund.id
                    }
                )
            except Exception as e:
                print(f"⚠️ Error creando notificación de reembolso creado para refund {refund.id}: {e}")
        
        return response

    def partial_update(self, request, *args, **kwargs):
        print(f"DEBUG ViewSet: partial_update llamado para reembolso {kwargs.get('pk')}")
        print(f"DEBUG ViewSet: Datos recibidos: {request.data}")
        
        # Obtener el refund antes de actualizar
        refund = self.get_object()
        old_status = refund.status
        
        # Hacer la actualización normal
        response = super().partial_update(request, *args, **kwargs)
        
        # Si se cambió el estado a COMPLETED, llamar a mark_as_completed para generar PDF
        if response.status_code in [200, 201] and old_status != RefundStatus.COMPLETED:
            # Recargar el refund para obtener el nuevo estado
            refund.refresh_from_db()
            if refund.status == RefundStatus.COMPLETED:
                try:
                    # Llamar al método que genera el PDF automáticamente
                    refund.mark_as_completed(user=request.user)
                    # No hacer save() porque mark_as_completed ya lo hace
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error en mark_as_completed para refund {refund.id}: {e}")
        
        return response
    
    @action(detail=False, methods=['get'])
    def for_reservation(self, request):
        """Obtiene todos los reembolsos de una reserva específica"""
        reservation_id = request.query_params.get('reservation_id')
        if not reservation_id:
            return Response(
                {"detail": "reservation_id es requerido"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            refunds = Refund.objects.filter(
                reservation_id=reservation_id
            ).select_related("payment", "created_by").order_by("-created_at")
            
            serializer = self.get_serializer(refunds, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {"detail": f"Error obteniendo reembolsos: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Actualiza el estado de un reembolso"""
        refund = self.get_object()
        serializer = self.get_serializer(refund, data=request.data, partial=True)
        
        if serializer.is_valid():
            # Usar los métodos del modelo para actualizar el estado
            new_status = serializer.validated_data.get('status')
            external_reference = serializer.validated_data.get('external_reference')
            notes = serializer.validated_data.get('notes')
            
            if new_status == RefundStatus.PROCESSING:
                refund.mark_as_processing()
            elif new_status == RefundStatus.COMPLETED:
                refund.mark_as_completed(external_reference)
            elif new_status == RefundStatus.FAILED:
                refund.mark_as_failed(notes)
            elif new_status == RefundStatus.CANCELLED:
                refund.cancel(notes)
            
            # Actualizar otros campos si se proporcionan
            if external_reference and new_status != RefundStatus.COMPLETED:
                refund.external_reference = external_reference
            if notes and new_status not in [RefundStatus.FAILED, RefundStatus.CANCELLED]:
                refund.notes = notes
            
            refund.save()
            
            # Crear notificación de cambio de estado del reembolso
            try:
                from apps.notifications.services import NotificationService
                from apps.notifications.models import NotificationType
                if new_status == RefundStatus.PROCESSING:
                    NotificationService.create(
                        notification_type=NotificationType.REFUND_AUTO,
                        title="Reembolso en procesamiento",
                        message=f"El reembolso de ${refund.amount} para la reserva #RES-{refund.reservation.id} en {refund.reservation.hotel.name} está siendo procesado.",
                        user_id=request.user.id,
                        hotel_id=refund.reservation.hotel.id,
                        reservation_id=refund.reservation.id,
                        metadata={
                            'reservation_code': f"RES-{refund.reservation.id}",
                            'hotel_name': refund.reservation.hotel.name,
                            'amount': str(refund.amount),
                            'status': 'processing'
                        }
                    )
                elif new_status == RefundStatus.COMPLETED:
                    NotificationService.create_refund_auto_notification(
                        reservation_code=f"RES-{refund.reservation.id}",
                        hotel_name=refund.reservation.hotel.name,
                        amount=str(refund.amount),
                        status="success",
                        hotel_id=refund.reservation.hotel.id,
                        reservation_id=refund.reservation.id,
                        user_id=request.user.id
                    )
                elif new_status == RefundStatus.FAILED:
                    NotificationService.create_refund_auto_notification(
                        reservation_code=f"RES-{refund.reservation.id}",
                        hotel_name=refund.reservation.hotel.name,
                        amount=str(refund.amount),
                        status="failed",
                        hotel_id=refund.reservation.hotel.id,
                        reservation_id=refund.reservation.id,
                        user_id=request.user.id
                    )
            except Exception as e:
                print(f"⚠️ Error creando notificación de reembolso para refund {refund.id}: {e}")
            
            return Response({
                'success': True,
                'message': f'Estado del reembolso actualizado a {refund.get_status_display()}',
                'refund': RefundSerializer(refund).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Obtiene estadísticas de reembolsos"""
        from django.db.models import Count, Sum
        from django.db.models.functions import TruncMonth
        
        # Estadísticas por estado
        status_stats = Refund.objects.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('status')
        
        # Estadísticas por mes
        monthly_stats = Refund.objects.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('month')
        
        # Estadísticas por razón
        reason_stats = Refund.objects.values('reason').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('reason')
        
        return Response({
            'status_stats': list(status_stats),
            'monthly_stats': list(monthly_stats),
            'reason_stats': list(reason_stats)
        })
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Obtiene el historial completo de un reembolso"""
        refund = self.get_object()
        
        try:
            from .services.refund_audit_service import RefundAuditService
            
            # Obtener información básica del reembolso
            refund_info = {
                'id': refund.id,
                'amount': str(refund.amount),
                'reason': refund.get_reason_display() if refund.reason else 'No especificado',
                'status': refund.get_status_display(),
                'refund_method': refund.get_refund_method_display() if hasattr(refund, 'get_refund_method_display') else refund.refund_method,
                'created_at': refund.created_at.isoformat(),
                'processed_at': refund.processed_at.isoformat() if refund.processed_at else None,
                'external_reference': refund.external_reference,
                'notes': refund.notes,
                'processing_days': refund.processing_days,
                'reservation': {
                    'id': refund.reservation.id,
                    'display_name': getattr(refund.reservation, 'display_name', f'Reserva #{refund.reservation.id}'),
                    'hotel_name': refund.reservation.hotel.name,
                    'guest_name': getattr(refund.reservation, 'guest_name', 'N/A'),
                    'check_in': refund.reservation.check_in.isoformat() if refund.reservation.check_in else None,
                    'check_out': refund.reservation.check_out.isoformat() if refund.reservation.check_out else None,
                },
                'created_by': {
                    'id': refund.created_by.id,
                    'username': refund.created_by.username,
                    'email': getattr(refund.created_by, 'email', None)
                } if refund.created_by else None,
                'processed_by': {
                    'id': refund.processed_by.id,
                    'username': refund.processed_by.username,
                    'email': getattr(refund.processed_by, 'email', None)
                } if refund.processed_by else None,
            }
            
            # Obtener voucher generado si existe
            voucher_info = None
            if refund.generated_voucher:
                voucher = refund.generated_voucher
                voucher_info = {
                    'id': voucher.id,
                    'code': voucher.code,
                    'amount': str(voucher.amount),
                    'remaining_amount': str(voucher.remaining_amount),
                    'status': voucher.get_status_display(),
                    'expiry_date': voucher.expiry_date.isoformat(),
                    'used_at': voucher.used_at.isoformat() if voucher.used_at else None,
                    'used_in_reservation': voucher.used_in_reservation.id if voucher.used_in_reservation else None,
                }
            
            # Obtener historial de cambios de estado
            status_changes = []
            try:
                logs = RefundAuditService.get_refund_audit_trail(refund)
                for log in logs:
                    if log.event_type in ['status_changed', 'created', 'processing_started', 'processing_completed', 'processing_failed', 'cancelled']:
                        status_changes.append({
                            'event_type': log.event_type,
                            'status': log.status,
                            'timestamp': log.timestamp.isoformat(),
                            'user': {
                                'id': log.user.id,
                                'username': log.user.username,
                                'email': getattr(log.user, 'email', None)
                            } if log.user else None,
                            'message': log.message,
                            'details': log.details,
                            'external_reference': log.external_reference,
                            'error_message': log.error_message
                        })
            except Exception as e:
                # Si hay error obteniendo logs, continuar sin historial
                pass
            
            return Response({
                'refund': refund_info,
                'voucher': voucher_info,
                'status_changes': status_changes,
                'summary': {
                    'total_changes': len(status_changes),
                    'current_status': refund.get_status_display(),
                    'days_since_created': (timezone.now() - refund.created_at).days,
                    'is_overdue': refund.status == 'pending' and (timezone.now() - refund.created_at).days > refund.processing_days
                }
            })
            
        except Exception as e:
            return Response(
                {"detail": f"Error obteniendo historial: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def audit_trail(self, request, pk=None):
        """Obtiene el trail completo de auditoría de un reembolso"""
        refund = self.get_object()
        
        try:
            from .services.refund_audit_service import RefundAuditService
            audit_trail = RefundAuditService.get_refund_audit_trail(refund)
            
            # Serializar los logs
            logs_data = []
            for log in audit_trail:
                logs_data.append({
                    'id': log.id,
                    'event_type': log.event_type,
                    'status': log.status,
                    'timestamp': log.timestamp,
                    'user': {
                        'id': log.user.id,
                        'username': log.user.username,
                        'email': getattr(log.user, 'email', None)
                    } if log.user else None,
                    'action': log.action,
                    'details': log.details,
                    'external_reference': log.external_reference,
                    'error_message': log.error_message,
                    'message': log.message
                })
            
            return Response({
                'refund_id': refund.id,
                'audit_trail': logs_data
            })
            
        except Exception as e:
            return Response(
                {"detail": f"Error obteniendo trail de auditoría: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RefundVoucherViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar vouchers de reembolso"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RefundVoucherCreateSerializer
        elif self.action == 'use_voucher':
            return RefundVoucherUseSerializer
        return RefundVoucherSerializer
    
    def get_queryset(self):
        qs = RefundVoucher.objects.all().select_related("hotel", "created_by", "used_by", "original_refund", "used_in_reservation")
        
        # Filtro por hotel
        hotel_id = self.request.query_params.get("hotel_id")
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
        
        # Filtro por estado
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        
        # Filtro por código
        code = self.request.query_params.get("code")
        if code:
            qs = qs.filter(code__icontains=code)
        
        # Filtro por búsqueda general
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(code__icontains=search) |
                Q(notes__icontains=search)
            )
        
        return qs.order_by("-created_at")
    
    def create(self, request, *args, **kwargs):
        """Crear un nuevo voucher de reembolso"""
        response = super().create(request, *args, **kwargs)
        
        if response.status_code == 201:  # Si se creó exitosamente
            try:
                # Obtener el ID del voucher de la respuesta
                voucher_id = response.data.get('id')
                if not voucher_id:
                    print("⚠️ No se pudo obtener el ID del voucher de la respuesta")
                    return response
                
                voucher = RefundVoucher.objects.get(id=voucher_id)
                
                # Crear notificación de voucher creado
                try:
                    from apps.notifications.services import NotificationService
                    from apps.notifications.models import NotificationType
                    NotificationService.create(
                        notification_type=NotificationType.REFUND_AUTO,
                        title="Nuevo voucher de reembolso creado",
                        message=f"Se ha creado un voucher de ${voucher.amount} (código: {voucher.code}) para {voucher.hotel.name}. Válido hasta {voucher.expiry_date.strftime('%d/%m/%Y')}",
                        user_id=request.user.id,
                        hotel_id=voucher.hotel.id,
                        metadata={
                            'voucher_code': voucher.code,
                            'hotel_name': voucher.hotel.name,
                            'amount': str(voucher.amount),
                            'expiry_date': voucher.expiry_date.isoformat(),
                            'voucher_id': voucher.id
                        }
                    )
                except Exception as e:
                    print(f"⚠️ Error creando notificación de voucher creado para voucher {voucher.id}: {e}")
                    
            except RefundVoucher.DoesNotExist:
                print(f"⚠️ Voucher con ID {voucher_id} no encontrado después de crear")
            except Exception as e:
                print(f"⚠️ Error procesando voucher creado: {e}")
        
        return response
    
    @action(detail=False, methods=['post'])
    def use_voucher(self, request):
        """Usar un voucher en una reserva"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                voucher_code = serializer.validated_data['voucher_code']
                amount = serializer.validated_data['amount']
                reservation_id = serializer.validated_data['reservation_id']
                
                # Obtener voucher y reserva
                voucher = RefundVoucher.objects.get(code=voucher_code)
                reservation = Reservation.objects.get(id=reservation_id)
                
                # Usar el voucher
                voucher.use_voucher(amount, reservation, request.user)
                
                # Crear notificación de voucher usado
                try:
                    from apps.notifications.services import NotificationService
                    from apps.notifications.models import NotificationType
                    NotificationService.create(
                        notification_type=NotificationType.REFUND_AUTO,
                        title="Voucher de reembolso usado",
                        message=f"El voucher {voucher.code} por ${amount} ha sido usado en la reserva #{reservation.id} en {reservation.hotel.name}",
                        user_id=request.user.id,
                        hotel_id=reservation.hotel.id,
                        reservation_id=reservation.id,
                        metadata={
                            'voucher_code': voucher.code,
                            'amount_used': str(amount),
                            'reservation_id': reservation.id,
                            'hotel_name': reservation.hotel.name,
                            'voucher_id': voucher.id
                        }
                    )
                except Exception as e:
                    print(f"⚠️ Error creando notificación de voucher usado para voucher {voucher.id}: {e}")
                
                return Response({
                    'success': True,
                    'message': f'Voucher {voucher.code} usado exitosamente por ${amount}',
                    'voucher': RefundVoucherSerializer(voucher).data,
                    'remaining_amount': str(voucher.remaining_amount)
                })
                
            except RefundVoucher.DoesNotExist:
                return Response(
                    {"detail": "Voucher no encontrado"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            except Reservation.DoesNotExist:
                return Response(
                    {"detail": "Reserva no encontrada"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            except ValueError as e:
                return Response(
                    {"detail": str(e)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancel_voucher(self, request, pk=None):
        """Cancelar un voucher"""
        voucher = self.get_object()
        reason = request.data.get('reason', '')
        
        try:
            voucher.cancel_voucher(request.user, reason)
            
            # Crear notificación de voucher cancelado
            try:
                from apps.notifications.services import NotificationService
                from apps.notifications.models import NotificationType
                NotificationService.create(
                    notification_type=NotificationType.REFUND_AUTO,
                    title="Voucher de reembolso cancelado",
                    message=f"El voucher {voucher.code} por ${voucher.amount} ha sido cancelado en {voucher.hotel.name}",
                    user_id=request.user.id,
                    hotel_id=voucher.hotel.id,
                    metadata={
                        'voucher_code': voucher.code,
                        'amount': str(voucher.amount),
                        'hotel_name': voucher.hotel.name,
                        'voucher_id': voucher.id,
                        'reason': reason
                    }
                )
            except Exception as e:
                print(f"⚠️ Error creando notificación de voucher cancelado para voucher {voucher.id}: {e}")
            
            return Response({
                'success': True,
                'message': f'Voucher {voucher.code} cancelado exitosamente',
                'voucher': RefundVoucherSerializer(voucher).data
            })
            
        except ValueError as e:
            return Response(
                {"detail": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def validate_voucher(self, request):
        """Validar un voucher por código"""
        voucher_code = request.query_params.get('code')
        if not voucher_code:
            return Response(
                {"detail": "Código de voucher requerido"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            voucher = RefundVoucher.objects.get(code=voucher_code)
            return Response({
                'valid': voucher.can_be_used(),
                'voucher': RefundVoucherSerializer(voucher).data
            })
        except RefundVoucher.DoesNotExist:
            return Response({
                'valid': False,
                'message': 'Voucher no encontrado'
            })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Obtiene estadísticas de vouchers"""
        from django.db.models import Count, Sum
        from django.db.models.functions import TruncMonth
        
        # Estadísticas por estado
        status_stats = RefundVoucher.objects.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('status')
        
        # Estadísticas por mes
        monthly_stats = RefundVoucher.objects.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('month')
        
        # Estadísticas por hotel
        hotel_stats = RefundVoucher.objects.values('hotel__name').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('hotel__name')
        
        return Response({
            'status_stats': list(status_stats),
            'monthly_stats': list(monthly_stats),
            'hotel_stats': list(hotel_stats)
        })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def rotate_payment_tokens(request):
    """
    Endpoint para rotar access_token y public_key de una configuración de pago
    """
    try:
        config_id = request.data.get('config_id')
        new_access_token = request.data.get('new_access_token')
        new_public_key = request.data.get('new_public_key')
        
        if not config_id:
            return Response({
                'success': False,
                'error': 'config_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not new_access_token or not new_public_key:
            return Response({
                'success': False,
                'error': 'new_access_token y new_public_key son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener la configuración
        try:
            config = PaymentGatewayConfig.objects.get(id=config_id)
        except PaymentGatewayConfig.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Configuración de pago no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validar que el usuario tenga permisos para modificar esta configuración
        # (aquí podrías agregar lógica de permisos específica)
        
        # Guardar los tokens anteriores para logging
        old_access_token = config.access_token
        old_public_key = config.public_key
        
        # Actualizar los tokens
        config.access_token = new_access_token
        config.public_key = new_public_key
        
        # Validar la configuración actualizada
        try:
            config.clean()
            config.save()
            
            # Log de la rotación
            logger.info(f"Tokens rotados para PaymentGatewayConfig {config_id}. Usuario: {request.user}")
            
            return Response({
                'success': True,
                'message': 'Tokens rotados exitosamente',
                'config_id': config_id,
                'rotated_at': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as validation_error:
            # Revertir cambios si la validación falla
            config.access_token = old_access_token
            config.public_key = old_public_key
            config.save()
            
            return Response({
                'success': False,
                'error': f'Error de validación: {str(validation_error)}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error rotando tokens: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BankTransferPaymentViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar transferencias bancarias"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BankTransferPaymentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BankTransferPaymentUpdateSerializer
        elif self.action == 'list':
            return BankTransferPaymentListSerializer
        return BankTransferPaymentSerializer
    
    def get_queryset(self):
        qs = BankTransferPayment.objects.all().select_related("reservation", "hotel", "created_by", "reviewed_by")
        
        # Filtro por reserva
        reservation_id = self.request.query_params.get("reservation_id")
        if reservation_id:
            qs = qs.filter(reservation_id=reservation_id)
        
        # Filtro por hotel
        hotel_id = self.request.query_params.get("hotel_id")
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
        
        # Filtro por estado
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        
        # Filtro por necesidades de revisión
        needs_review = self.request.query_params.get("needs_review")
        if needs_review and needs_review.lower() == 'true':
            qs = qs.filter(status=BankTransferStatus.PENDING_REVIEW)
        
        # Filtro por búsqueda general
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(reservation_id__icontains=search) |
                Q(cbu_iban__icontains=search) |
                Q(bank_name__icontains=search) |
                Q(external_reference__icontains=search)
            )
        
        return qs.order_by("-created_at")
    
    def create(self, request, *args, **kwargs):
        """Crear una nueva transferencia bancaria"""
        logger.info(f"Creando transferencia bancaria. Usuario: {request.user.id}")
        logger.info(f"Datos recibidos: {list(request.data.keys())}")
        
        response = super().create(request, *args, **kwargs)
        
        logger.info(f"Respuesta del serializer: {response.status_code}")
        if hasattr(response, 'data'):
            logger.info(f"Datos de respuesta: {list(response.data.keys()) if isinstance(response.data, dict) else 'No es dict'}")
        
        if response.status_code == 201:
            logger.info(f"Transferencia creada y confirmada automáticamente: {response.data.get('id')}")
        
        return response
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirmar una transferencia bancaria"""
        transfer = self.get_object()
        
        if transfer.status == BankTransferStatus.CONFIRMED:
            return Response({
                'error': 'La transferencia ya está confirmada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        notes = request.data.get('notes', '')
        transfer.mark_as_confirmed(user=request.user, notes=notes)
        
        return Response({
            'success': True,
            'message': 'Transferencia confirmada exitosamente',
            'transfer': BankTransferPaymentSerializer(transfer, context={'request': request}).data
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Rechazar una transferencia bancaria"""
        transfer = self.get_object()
        
        if transfer.status == BankTransferStatus.REJECTED:
            return Response({
                'error': 'La transferencia ya está rechazada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        notes = request.data.get('notes', '')
        if not notes:
            return Response({
                'error': 'Las notas son requeridas para rechazar una transferencia'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        transfer.mark_as_rejected(user=request.user, notes=notes)
        
        return Response({
            'success': True,
            'message': 'Transferencia rechazada exitosamente',
            'transfer': BankTransferPaymentSerializer(transfer, context={'request': request}).data
        })
    
    @action(detail=True, methods=['post'])
    def mark_pending_review(self, request, pk=None):
        """Marcar transferencia como pendiente de revisión"""
        transfer = self.get_object()
        
        if transfer.status in [BankTransferStatus.CONFIRMED, BankTransferStatus.REJECTED]:
            return Response({
                'error': 'No se puede marcar como pendiente una transferencia ya procesada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        transfer.mark_as_pending_review(user=request.user)
        
        return Response({
            'success': True,
            'message': 'Transferencia marcada como pendiente de revisión',
            'transfer': BankTransferPaymentSerializer(transfer, context={'request': request}).data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Obtiene estadísticas de transferencias bancarias"""
        from django.db.models import Count, Sum
        from django.db.models.functions import TruncMonth
        
        # Estadísticas por estado
        status_stats = BankTransferPayment.objects.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('status')
        
        # Estadísticas por mes
        monthly_stats = BankTransferPayment.objects.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('month')
        
        # Estadísticas por hotel
        hotel_stats = BankTransferPayment.objects.values('hotel__name').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('hotel__name')
        
        # Transferencias que necesitan revisión
        pending_review_count = BankTransferPayment.objects.filter(
            status=BankTransferStatus.PENDING_REVIEW
        ).count()
        
        return Response({
            'status_stats': list(status_stats),
            'monthly_stats': list(monthly_stats),
            'hotel_stats': list(hotel_stats),
            'pending_review_count': pending_review_count
        })
    
    @action(detail=False, methods=['get'])
    def pending_review(self, request):
        """Obtiene transferencias pendientes de revisión"""
        transfers = BankTransferPayment.objects.filter(
            status=BankTransferStatus.PENDING_REVIEW
        ).select_related("reservation", "hotel", "created_by").order_by("-created_at")
        
        serializer = self.get_serializer(transfers, many=True)
        return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_bank_transfer_receipt(request):
    """
    Endpoint específico para subir comprobante de transferencia bancaria
    """
    try:
        logger.info(f"Iniciando subida de comprobante de transferencia. Usuario: {request.user.id}")
        logger.info(f"Datos recibidos: {list(request.data.keys())}")
        logger.info(f"Archivos recibidos: {list(request.FILES.keys())}")
        
        # Validar que se envíe un archivo
        if 'receipt_file' not in request.FILES:
            logger.warning("No se recibió archivo de comprobante")
            return Response({
                'error': 'El archivo de comprobante es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar datos requeridos
        required_fields = ['reservation', 'amount', 'transfer_date', 'cbu_iban']
        missing_fields = []
        for field in required_fields:
            if field not in request.data:
                missing_fields.append(field)
        
        if missing_fields:
            logger.warning(f"Campos requeridos faltantes: {missing_fields}")
            return Response({
                'error': f'Los campos {", ".join(missing_fields)} son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info("Validando datos con serializer...")
        
        # Crear la transferencia
        serializer = BankTransferPaymentCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            logger.info("Serializer válido, creando transferencia...")
            transfer = serializer.save()
            logger.info(f"Transferencia creada exitosamente: {transfer.id}")
            
            # Encolar tarea de procesamiento OCR
            try:
                from .tasks import process_bank_transfer_ocr
                process_bank_transfer_ocr.delay(transfer.id)
                logger.info(f"Tarea OCR encolada para transferencia {transfer.id}")
            except Exception as e:
                logger.warning(f"Error encolando tarea OCR para transferencia {transfer.id}: {e}")
            
            return Response({
                'success': True,
                'message': 'Comprobante subido exitosamente',
                'transfer': BankTransferPaymentSerializer(transfer, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        else:
            logger.error(f"Serializer inválido: {serializer.errors}")
            return Response({
                'error': 'Datos inválidos',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error subiendo comprobante de transferencia: {str(e)}", exc_info=True)
        return Response({
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===== VISTAS PARA SEÑAS (PAGOS PARCIALES) =====

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_deposit(request):
    """
    Crear una seña/depósito para una reserva
    
    POST /api/payments/create-deposit/
    {
        "reservation_id": 123,
        "amount": 1000.00,
        "method": "cash",
        "send_to_afip": false,
        "notes": "Seña del 50%"
    }
    """
    try:
        serializer = CreateDepositSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'error': 'Datos inválidos',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener datos validados
        reservation_id = serializer.validated_data['reservation_id']
        amount = serializer.validated_data['amount']
        method = serializer.validated_data['method']
        send_to_afip = serializer.validated_data['send_to_afip']
        notes = serializer.validated_data.get('notes', '')
        
        # Obtener reserva
        reservation = get_object_or_404(Reservation, id=reservation_id)
        
        # Obtener política de pago del hotel
        policy = PaymentPolicy.resolve_for_hotel(reservation.hotel)
        if not policy:
            return Response({
                'error': 'El hotel no tiene política de pago configurada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calcular depósito según política
        from .services.payment_calculator import calculate_deposit
        deposit_info = calculate_deposit(policy, reservation.total_price)
        
        if not deposit_info['required']:
            return Response({
                'error': 'La política de pago no requiere depósito'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar que el monto de la seña no exceda el depósito requerido
        if amount > deposit_info['amount']:
            return Response({
                'error': f'El monto de la seña no puede exceder ${deposit_info["amount"]} (según política)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Crear pago como seña
            payment = Payment.objects.create(
                reservation=reservation,
                date=timezone.now().date(),
                method=method,
                amount=amount,
                is_deposit=True,
                metadata={
                    'deposit_info': deposit_info,
                    'policy_id': policy.id,
                    'notes': notes
                },
                notes=notes
            )
            
            # Generar recibo PDF
            from .tasks import generate_payment_receipt_pdf
            generate_payment_receipt_pdf.delay(payment.id, 'payment')
            
            # Si se debe enviar a AFIP, generar factura
            receipt_pdf_url = None
            if send_to_afip:
                try:
                    # Verificar configuración AFIP
                    afip_config = reservation.hotel.afip_config
                    if not afip_config:
                        return Response({
                            'error': 'El hotel no tiene configuración AFIP para facturación'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Generar factura para la seña
                    from apps.invoicing.views import GenerateInvoiceFromPaymentView
                    invoice_view = GenerateInvoiceFromPaymentView()
                    
                    # Simular request para generar factura
                    invoice_data = {
                        'customer_name': reservation.guest_name or 'Cliente',
                        'customer_document_type': 'DNI',
                        'customer_document_number': '00000000',
                        'send_to_afip': True
                    }
                    
                    # Crear factura usando el servicio existente
                    from apps.invoicing.services.invoice_generator import InvoiceGeneratorService
                    invoice_service = InvoiceGeneratorService()
                    invoice_result = invoice_service.create_invoice_from_payment(
                        payment, 
                        invoice_data,
                        send_to_afip=True
                    )
                    
                    if invoice_result['success']:
                        receipt_pdf_url = invoice_result.get('pdf_url')
                    else:
                        logger.warning(f"Error generando factura para seña {payment.id}: {invoice_result.get('error')}")
                        
                except Exception as e:
                    logger.error(f"Error generando factura para seña {payment.id}: {str(e)}")
                    # No fallar la creación del pago si hay error en la factura
            
            # Preparar respuesta
            response_data = DepositResponseSerializer(payment).data
            response_data['receipt_pdf_url'] = receipt_pdf_url
            response_data['deposit_info'] = deposit_info
            
            return Response({
                'message': 'Seña creada exitosamente',
                'payment': response_data
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        logger.error(f"Error creando seña: {str(e)}", exc_info=True)
        return Response({
            'error': 'Error interno del servidor',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_invoice_from_payment_extended(request, payment_id):
    """
    Generar factura desde pago con soporte para múltiples pagos (señas + pago final)
    
    POST /api/payments/generate-invoice-from-payment/{payment_id}/
    {
        "send_to_afip": true,
        "reference_payments": [123, 124, 125],
        "customer_name": "Juan Pérez",
        "customer_document_type": "DNI",
        "customer_document_number": "12345678"
    }
    """
    try:
        # Obtener pago principal
        payment = get_object_or_404(Payment, id=payment_id)
        
        serializer = GenerateInvoiceFromPaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'error': 'Datos inválidos',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener pagos de referencia si se proporcionan
        reference_payments = serializer.validated_data.get('reference_payments', [payment_id])
        if payment_id not in reference_payments:
            reference_payments.append(payment_id)
        
        # Obtener todos los pagos
        payments = Payment.objects.filter(id__in=reference_payments)
        if not payments.exists():
            return Response({
                'error': 'No se encontraron pagos válidos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar que todos los pagos pertenezcan a la misma reserva
        reservation_ids = set(p.id for p in payments for p in [p.reservation])
        if len(reservation_ids) > 1:
            return Response({
                'error': 'Todos los pagos deben pertenecer a la misma reserva'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        reservation = payment.reservation
        
        # Verificar configuración AFIP
        afip_config = reservation.hotel.afip_config
        if not afip_config:
            return Response({
                'error': 'El hotel no tiene configuración AFIP'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Calcular total de todos los pagos
            total_amount = sum(p.amount for p in payments)
            
            # Generar número de factura
            next_number = afip_config.get_next_invoice_number()
            formatted_number = afip_config.format_invoice_number(next_number)
            
            # Obtener datos del cliente
            customer_data = {
                'customer_name': serializer.validated_data.get('customer_name', reservation.guest_name or 'Cliente'),
                'customer_document_type': serializer.validated_data.get('customer_document_type', 'DNI'),
                'customer_document_number': serializer.validated_data.get('customer_document_number', '00000000'),
                'customer_address': serializer.validated_data.get('customer_address', ''),
                'customer_city': serializer.validated_data.get('customer_city', ''),
                'customer_postal_code': serializer.validated_data.get('customer_postal_code', ''),
                'customer_country': serializer.validated_data.get('customer_country', 'Argentina'),
            }
            
            # Crear factura
            from apps.invoicing.models import Invoice
            invoice_data = {
                'reservation': reservation,
                'payment': payment,  # Pago principal para compatibilidad
                'payments_data': reference_payments,  # Lista de IDs de pagos
                'hotel': reservation.hotel,
                'type': 'B',  # Factura B por defecto
                'number': formatted_number,
                'issue_date': serializer.validated_data.get('issue_date', timezone.now().date()),
                'total': total_amount,
                'net_amount': total_amount * Decimal('0.83'),  # Aproximado sin IVA
                'vat_amount': total_amount * Decimal('0.17'),  # Aproximado con IVA
                'currency': 'ARS',
                'status': 'draft',
                'created_by': request.user,
                **customer_data
            }
            
            invoice = Invoice.objects.create(**invoice_data)
            
            # Crear items de la factura
            from apps.invoicing.models import InvoiceItem
            item_data = {
                'invoice': invoice,
                'description': f'Hospedaje - {reservation.room.name} (Incluye señas y pago final)',
                'quantity': (reservation.check_out - reservation.check_in).days,
                'unit_price': reservation.room.base_price,
                'vat_rate': Decimal('21.00'),
                'afip_code': '1'  # Servicios
            }
            InvoiceItem.objects.create(**item_data)
            
            # Actualizar número en configuración
            afip_config.update_invoice_number(next_number)
            
            # Si se debe enviar a AFIP
            if serializer.validated_data.get('send_to_afip', False):
                try:
                    from apps.invoicing.services.afip_service import AfipService
                    afip_service = AfipService(afip_config)
                    result = afip_service.send_invoice(invoice)
                    
                    if result['success']:
                        invoice.mark_as_approved(result['cae'], result['cae_expiration'])
                    else:
                        invoice.mark_as_error(result['error'])
                        
                except Exception as e:
                    logger.error(f"Error enviando factura {invoice.number} a AFIP: {str(e)}")
                    invoice.mark_as_error(str(e))
            
            # Generar PDF de la factura
            from apps.invoicing.tasks import generate_invoice_pdf
            generate_invoice_pdf.delay(invoice.id)
            
            return Response({
                'message': 'Factura generada exitosamente',
                'invoice': {
                    'id': invoice.id,
                    'number': invoice.number,
                    'total': float(invoice.total),
                    'status': invoice.status,
                    'cae': invoice.cae,
                    'payments_included': reference_payments
                }
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        logger.error(f"Error generando factura desde pagos: {str(e)}", exc_info=True)
        return Response({
            'error': 'Error interno del servidor',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para gestionar pagos (solo lectura para comprobantes)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        qs = Payment.objects.all().select_related("reservation", "reservation__hotel")
        
        # Filtro por hotel
        hotel_id = self.request.query_params.get("hotel")
        if hotel_id:
            qs = qs.filter(reservation__hotel_id=hotel_id)
        
        # Filtro por método de pago
        payment_method = self.request.query_params.get("payment_method")
        if payment_method:
            qs = qs.filter(method=payment_method)
        
        # Filtro por estado
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        
        # Filtro por tipo de pago (señas)
        is_deposit = self.request.query_params.get("is_deposit")
        if is_deposit is not None:
            qs = qs.filter(is_deposit=is_deposit.lower() == 'true')
        
        # Filtro por búsqueda general
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(reservation__guest_name__icontains=search) |
                Q(reservation__hotel__name__icontains=search) |
                Q(method__icontains=search) |
                Q(status__icontains=search)
            )
        
        # Filtro por rango de fechas
        date_from = self.request.query_params.get("date_from")
        if date_from:
            qs = qs.filter(date__gte=date_from)
        
        date_to = self.request.query_params.get("date_to")
        if date_to:
            qs = qs.filter(date__lte=date_to)
        
        return qs.order_by("-created_at")
    
    def get_serializer_class(self):
        return PaymentSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_receipt_from_payment(request, payment_id: int):
    """
    Genera (o regenera) el PDF de recibo para un pago parcial existente.

    Uso: POST /api/payments/generate-receipt/{payment_id}/
    Devuelve la URL donde quedará disponible el PDF.
    """
    try:
        payment = get_object_or_404(Payment, id=payment_id)

        # Generar número de comprobante si no existe
        if not payment.receipt_number:
            from .models import ReceiptNumberSequence
            
            # Determinar el tipo de comprobante según si es seña o pago total
            if payment.is_deposit:
                receipt_type = ReceiptNumberSequence.ReceiptType.DEPOSIT  # "S"
            else:
                receipt_type = ReceiptNumberSequence.ReceiptType.PAYMENT  # "P"
            
            receipt_number = ReceiptNumberSequence.generate_receipt_number(
                hotel=payment.reservation.hotel,
                receipt_type=receipt_type
            )
            payment.receipt_number = receipt_number
            payment.save(update_fields=['receipt_number'])

        # Programar/generar el PDF
        try:
            from .tasks import generate_payment_receipt_pdf
            generate_payment_receipt_pdf.delay(payment.id, 'payment')
        except Exception:
            logger.exception("Error encolando tarea de recibo de pago")

        # Construir URL del archivo destino
        from django.conf import settings
        filename = f"payment_{payment.id}.pdf"
        relative_path = f"documents/{filename}"
        base_url = getattr(settings, 'MEDIA_URL', '/media/')
        absolute_url = request.build_absolute_uri(os.path.join(base_url, relative_path))

        # Actualizar el campo receipt_pdf_url en la base de datos
        payment.receipt_pdf_url = absolute_url
        payment.save(update_fields=['receipt_pdf_url'])

        return Response({
            'message': 'Recibo en proceso de generación',
            'payment_id': payment.id,
            'receipt_pdf_url': absolute_url
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        logger.error(f"Error generando recibo para pago {payment_id}: {e}", exc_info=True)
        return Response({'error': 'Error interno del servidor'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_receipt_from_refund(request, refund_id: int):
    """
    Genera (o regenera) el PDF de comprobante para un reembolso existente.

    Uso: POST /api/payments/generate-refund-receipt/{refund_id}/
    Devuelve la URL donde quedará disponible el PDF.
    """
    try:
        refund = get_object_or_404(Refund, id=refund_id)

        # Generar número de comprobante si no existe
        if not refund.receipt_number:
            from .models import ReceiptNumberSequence
            receipt_number = ReceiptNumberSequence.generate_receipt_number(
                hotel=refund.reservation.hotel,
                receipt_type=ReceiptNumberSequence.ReceiptType.REFUND  # "D"
            )
            refund.receipt_number = receipt_number
            refund.save(update_fields=['receipt_number'])

        # Programar/generar el PDF
        try:
            from .tasks import generate_payment_receipt_pdf
            generate_payment_receipt_pdf.delay(refund.id, 'refund')
        except Exception:
            logger.exception("Error encolando tarea de comprobante de reembolso")

        # Construir URL del archivo destino
        from django.conf import settings
        filename = f"refund_{refund.id}.pdf"
        relative_path = f"documents/{filename}"
        base_url = getattr(settings, 'MEDIA_URL', '/media/')
        absolute_url = request.build_absolute_uri(os.path.join(base_url, relative_path))

        # Actualizar el campo receipt_pdf_url en la base de datos
        refund.receipt_pdf_url = absolute_url
        refund.save(update_fields=['receipt_pdf_url'])

        return Response({
            'message': 'Comprobante de reembolso en proceso de generación',
            'refund_id': refund.id,
            'receipt_pdf_url': absolute_url
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        logger.error(f"Error generando comprobante para reembolso {refund_id}: {e}", exc_info=True)
        return Response({'error': 'Error interno del servidor'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)