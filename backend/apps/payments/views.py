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

from apps.reservations.models import Reservation, ReservationStatus, Payment
from .models import PaymentGatewayConfig, PaymentIntent, PaymentIntentStatus, PaymentMethod, PaymentPolicy, CancellationPolicy, RefundPolicy, Refund, RefundStatus, RefundReason, RefundLog, RefundVoucher, RefundVoucherStatus
from .serializers import PaymentMethodSerializer, PaymentPolicySerializer, CancellationPolicySerializer, CancellationPolicyCreateSerializer, RefundPolicySerializer, RefundPolicyCreateSerializer, RefundSerializer, RefundCreateSerializer, RefundStatusUpdateSerializer, RefundVoucherSerializer, RefundVoucherCreateSerializer, RefundVoucherUseSerializer
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
    class Meta:
        model = Payment
        fields = [
            'id', 'date', 'method', 'amount', 'created_at'
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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_brick_intent(request):
    # Queda como placeholder. Se implementará con Payment Brick.
    return Response({"note": "Próximamente: Payment Brick"}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def webhook(request):
    # Soportar varios formatos de webhook (query o body)
    topic = request.query_params.get("type") or request.query_params.get("topic") or request.data.get("type")
    payment_id = (
        request.query_params.get("data.id")
        or request.query_params.get("id")
        or (request.data.get("data", {}) if isinstance(request.data, dict) else {}).get("id")
        or request.data.get("id")
    )

    # Acceso básico con token de entorno (desarrollo). En escenarios multi‑tenant, se resuelve por hotel.
    access_token = os.environ.get("MP_ACCESS_TOKEN", "")
    if not access_token:
        return Response({"detail": "ACCESS_TOKEN no configurado"}, status=status.HTTP_400_BAD_REQUEST)

    if topic != "payment" or not payment_id:
        return Response({"received": True, "note": "evento no procesado"}, status=200)

    sdk = mercadopago.SDK(access_token)
    pay_resp = sdk.payment().get(payment_id)
    if pay_resp.get("status") != 200:
        return Response({"detail": "No se pudo consultar el pago", "mp": pay_resp.get("response")}, status=status.HTTP_502_BAD_GATEWAY)

    payment = pay_resp.get("response", {})
    status_detail = payment.get("status")
    external_reference = payment.get("external_reference") or ""

    # Intento de localizar el intent/reserva
    intent = None
    if external_reference:
        intent = PaymentIntent.objects.filter(external_reference=external_reference).order_by("-created_at").first()

    # Parsear external_reference para obtener reserva/hotel si no hay intent
    reservation = None
    if not intent and external_reference:
        try:
            parts = {kv.split(":", 1)[0]: kv.split(":", 1)[1] for kv in external_reference.split("|") if ":" in kv}
            res_id_str = parts.get("reservation")
            if res_id_str:
                reservation = Reservation.objects.filter(pk=int(res_id_str)).first()
        except Exception:
            reservation = None

    # Actualizar/crear intent mínimo
    if intent is None and reservation is not None:
        try:
            amount = Decimal(str(payment.get("transaction_amount", "0") or "0"))
        except Exception:
            amount = Decimal("0")
        currency = payment.get("currency_id") or (reservation.hotel.country.currency_code if getattr(reservation.hotel, "country", None) else "ARS")
        intent = PaymentIntent.objects.create(
            reservation=reservation,
            hotel=reservation.hotel,
            enterprise=reservation.hotel.enterprise if getattr(reservation.hotel, "enterprise", None) else None,
            amount=amount,
            currency=currency,
            description=f"Reserva {reservation.id}",
            mp_preference_id=payment.get("order", {}).get("id", "") if isinstance(payment.get("order"), dict) else "",
            mp_payment_id=str(payment.get("id")),
            external_reference=external_reference,
            status=PaymentIntentStatus.APPROVED if status_detail == "approved" else (
                PaymentIntentStatus.REJECTED if status_detail == "rejected" else PaymentIntentStatus.CREATED
            ),
        )

    # Si existe intent, sincronizar estado
    if intent:
        intent.mp_payment_id = str(payment.get("id"))
        if status_detail == "approved":
            intent.status = PaymentIntentStatus.APPROVED
        elif status_detail == "rejected":
            intent.status = PaymentIntentStatus.REJECTED
        else:
            intent.status = PaymentIntentStatus.CREATED
        intent.save(update_fields=["mp_payment_id", "status", "updated_at"])

        # Confirmar reserva si corresponde y crear registro de pago
        try:
            reservation = reservation or intent.reservation
            if reservation and status_detail == "approved":
                # Crear registro de pago en la tabla Payment si no existe
                from apps.reservations.models import Payment
                existing_payment = Payment.objects.filter(
                    reservation=reservation,
                    amount=intent.amount,
                    method="card"
                ).first()
                
                if not existing_payment:
                    Payment.objects.create(
                        reservation=reservation,
                        date=timezone.now().date(),
                        method="card",
                        amount=intent.amount
                    )
                
                # Confirmar reserva si está pendiente
                if reservation.status == ReservationStatus.PENDING:
                    reservation.status = ReservationStatus.CONFIRMED
                    reservation.save(update_fields=["status", "updated_at"])
        except Exception:
            pass

    return Response({"processed": True}, status=200)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def process_card_payment(request):
    body = request.data or {}
    reservation_id = body.get("reservation_id")
    token = body.get("token")
    payment_method_id = body.get("payment_method_id")
    installments = int(body.get("installments", 1))
    amount_raw = body.get("amount")

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
    payment_data = {
        "token": token,
        "transaction_amount": float(amount),
        "installments": installments,
        "payment_method_id": payment_method_id,
        "description": title,
        "external_reference": external_reference,
        "payer": {"email": reservation.guest_email or "test_user@example.com"},
    }

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
        Payment.objects.create(
            reservation=reservation,
            date=timezone.now().date(),
            method="card",
            amount=amount
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
            payment = Payment.objects.create(
                reservation=reservation,
                date=timezone.now().date(),
                method=method,
                amount=Decimal(str(amount))
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
        return super().partial_update(request, *args, **kwargs)
    
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
            timeline = RefundAuditService.get_refund_timeline(refund)
            
            return Response({
                'refund_id': refund.id,
                'timeline': timeline
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