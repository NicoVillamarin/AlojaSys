from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal
import os
import mercadopago
from uuid import uuid4
from rest_framework import serializers

from apps.reservations.models import Reservation, ReservationStatus, Payment
from .models import PaymentGatewayConfig, PaymentIntent, PaymentIntentStatus


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

        # Confirmar reserva si corresponde
        try:
            reservation = reservation or intent.reservation
            if reservation and status_detail == "approved" and reservation.status == ReservationStatus.PENDING:
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

    # Confirmar reserva si aprobado
    if status_detail == "approved" and reservation.status == ReservationStatus.PENDING:
        reservation.status = ReservationStatus.CONFIRMED
        reservation.save(update_fields=["status", "updated_at"])

    return Response({
        "payment_id": payment.get("id"),
        "status": status_detail,
        "status_detail": payment.get("status_detail"),
    }, status=200)