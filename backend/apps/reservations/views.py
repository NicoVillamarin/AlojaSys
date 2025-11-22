from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, permissions, filters, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone as django_timezone
from apps.rooms.models import Room, RoomStatus
from apps.rooms.serializers import RoomSerializer
from .models import Reservation, ReservationStatus, ReservationChannel, RoomBlock, ReservationNight
from .serializers import (
    ReservationSerializer,
    PaymentSerializer,
    ChannelCommissionSerializer,
    ReservationChargeSerializer,
    MultiRoomReservationCreateSerializer,
)
from rest_framework.decorators import action, api_view
from decimal import Decimal
from django.db import models, transaction
from django.db.models import Sum
from .services.pricing import compute_nightly_rate, recalc_reservation_totals, generate_nights_for_reservation
from apps.rates.models import RatePlan, DiscountType, PromoRule
from apps.rates.services.engine import get_applicable_rule, compute_rate_for_date
import uuid
import logging

logger = logging.getLogger(__name__)


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Reservation.objects.select_related("hotel", "room")
        hotel_id = self.request.query_params.get("hotel")
        room_id = self.request.query_params.get("room")
        status_param = self.request.query_params.get("status")
        group_code = self.request.query_params.get("group_code")
        ordering = self.request.query_params.get("ordering", "-check_in")  # Por defecto ordenar por check-in descendente
        
        if hotel_id and hotel_id.isdigit():
            qs = qs.filter(hotel_id=hotel_id)
        if room_id and room_id.isdigit():
            qs = qs.filter(room_id=room_id)
        if status_param:
            qs = qs.filter(status=status_param)
        if group_code:
            qs = qs.filter(group_code=group_code)
        
        # Validar que el campo de ordenamiento sea válido
        valid_orderings = ['created_at', '-created_at', 'check_in', '-check_in', 'check_out', '-check_out', 'id', '-id']
        if ordering in valid_orderings:
            # Si se ordena por ID, mantener ordenamiento secundario por check_in descendente
            # para asegurar que las reservas futuras estén visibles
            if ordering in ['id', '-id']:
                qs = qs.order_by(ordering, '-check_in')
            else:
                qs = qs.order_by(ordering)
        else:
            qs = qs.order_by("-check_in")  # Fallback a check-in descendente
        
        return qs

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            # Recalcular noches/totales inmediatamente para reflejar impuestos/promos en la respuesta
            if instance.check_in and instance.check_out and instance.room_id:
                generate_nights_for_reservation(instance)
                recalc_reservation_totals(instance)
                try:
                    instance.refresh_from_db(fields=["total_price"])  # asegurar valor actualizado
                except Exception:
                    pass
            output = self.get_serializer(instance)
            headers = self.get_success_headers(output.data)
            return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)
        except ValidationError as e:
            # Convertir ValidationError a formato JSON
            if hasattr(e, 'message_dict'):
                # Error de validación de campo específico
                return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)
            elif hasattr(e, 'messages'):
                # Error de validación general
                return Response({'__all__': list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Error simple
                return Response({'__all__': [str(e)]}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            if instance.check_in and instance.check_out and instance.room_id:
                generate_nights_for_reservation(instance)
                recalc_reservation_totals(instance)
                try:
                    instance.refresh_from_db(fields=["total_price"])  # asegurar valor actualizado
                except Exception:
                    pass
            return Response(self.get_serializer(instance).data)
        except ValidationError as e:
            # Convertir ValidationError a formato JSON
            if hasattr(e, 'message_dict'):
                # Error de validación de campo específico
                return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)
            elif hasattr(e, 'messages'):
                # Error de validación general
                return Response({'__all__': list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Error simple
                return Response({'__all__': [str(e)]}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="multi-room")
    def create_multi_room(self, request, *args, **kwargs):
        """
        Crea una reserva multi-habitación.

        A nivel de base de datos se generan varias instancias de `Reservation`,
        una por habitación, todas compartiendo:
        - hotel
        - rango de fechas (check_in / check_out)
        - canal / status / external_id (si aplica)
        - un mismo `group_code` para poder agruparlas en el frontend.

        La lógica de validación y pricing reutiliza el `ReservationSerializer`
        estándar, por lo que se respetan todas las reglas actuales:
        solapamientos, capacidad, CTA/CTD, min/max stay, políticas, etc.
        """
        serializer = MultiRoomReservationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not data.get("rooms"):
            return Response(
                {"detail": "Debe indicar al menos una habitación en 'rooms'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group_code = data.get("group_code") or str(uuid.uuid4())

        created_reservations = []
        try:
            with transaction.atomic():
                for room_payload in data["rooms"]:
                    single_payload = {
                        "hotel": data["hotel"].id if hasattr(data["hotel"], "id") else data["hotel"],
                        "room": room_payload["room"].id if hasattr(room_payload["room"], "id") else room_payload["room"],
                        "guests": room_payload["guests"],
                        "guests_data": room_payload.get("guests_data", []),
                        "check_in": data["check_in"],
                        "check_out": data["check_out"],
                        "status": data.get("status", ReservationStatus.PENDING),
                        "channel": data.get("channel", ReservationChannel.DIRECT),
                        "external_id": data.get("external_id"),
                        "notes": room_payload.get("notes") or data.get("notes"),
                        # Si la habitación tiene su propio código, usarlo; sino usar el del grupo
                        "promotion_code": room_payload.get("promotion_code") or data.get("promotion_code"),
                        "voucher_code": room_payload.get("voucher_code") or data.get("voucher_code"),
                        "group_code": group_code,
                    }
                    res_serializer = ReservationSerializer(data=single_payload)
                    res_serializer.is_valid(raise_exception=True)
                    instance = res_serializer.save()
                    created_reservations.append(instance)

                # Regenerar noches y totales para todas las reservas creadas
                for instance in created_reservations:
                    if instance.check_in and instance.check_out and instance.room_id:
                        generate_nights_for_reservation(instance)
                        recalc_reservation_totals(instance)
                        try:
                            instance.refresh_from_db(fields=["total_price"])
                        except Exception:
                            pass
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)
            elif hasattr(e, 'messages'):
                return Response({'__all__': list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'__all__': [str(e)]}, status=status.HTTP_400_BAD_REQUEST)

        output = ReservationSerializer(created_reservations, many=True)
        
        # Enviar emails consolidados para reservas multi-habitación
        # Solo si hay más de una reserva (es realmente multi-habitación)
        if len(created_reservations) > 1:
            try:
                from apps.reservations.services.email_service import ReservationEmailService
                email_results = ReservationEmailService.send_multi_room_confirmation(
                    created_reservations,
                    include_receipts=True
                )
                logger.info(f"📧 Emails consolidados enviados para grupo {group_code}: {email_results}")
            except Exception as email_error:
                # No fallar la creación de la reserva si el email falla
                logger.error(f"⚠️ Error enviando emails consolidados para grupo {group_code}: {email_error}")
        
        return Response(
            {
                "group_code": group_code,
                "reservations": output.data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def check_in(self, request, pk=None):
        reservation = self.get_object()
        today = date.today()
        if reservation.status not in [ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN]:
            return Response({"detail": "La reserva debe estar confirmada para hacer check-in."}, status=status.HTTP_400_BAD_REQUEST)
        if not (reservation.check_in <= today < reservation.check_out):
            return Response({"detail": "El check-in solo puede realizarse dentro del rango de la reserva."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si hay saldo pendiente según la política de pago
        from apps.payments.services.payment_calculator import calculate_balance_due
        balance_info = calculate_balance_due(reservation)
        
        # Si hay saldo pendiente y la política indica que se debe cobrar en check-in
        if (balance_info['has_balance'] and 
            balance_info.get('policy') and 
            balance_info['policy'].balance_due == 'check_in'):
            return Response({
                "detail": "Check-in requiere pago del saldo pendiente.",
                "requires_payment": True,
                "balance_due": float(balance_info['balance_due']),
                "total_paid": float(balance_info['total_paid']),
                "total_reservation": float(balance_info['total_reservation']),
                "payment_required_at": "check_in"
            }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        reservation.status = ReservationStatus.CHECK_IN
        reservation.room.status = RoomStatus.OCCUPIED
        reservation.room.save(update_fields=["status"])
        reservation.save(update_fields=["status"]) 
        # log explícito con autor
        from apps.reservations.models import ReservationChangeLog, ReservationChangeEvent
        ReservationChangeLog.objects.create(
            reservation=reservation,
            event_type=ReservationChangeEvent.CHECK_IN,
            changed_by=request.user if request.user.is_authenticated else None,
        )
        return Response({"detail": "Check-in realizado."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def check_out(self, request, pk=None):
        reservation = self.get_object()
        if reservation.status != ReservationStatus.CHECK_IN:
            return Response({"detail": "La reserva debe estar en check-in para hacer check-out."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si hay saldo pendiente según la política de pago
        from apps.payments.services.payment_calculator import calculate_balance_due
        balance_info = calculate_balance_due(reservation)
        
        # Si hay saldo pendiente y la política indica que se debe cobrar en check-out
        if (balance_info['has_balance'] and 
            balance_info.get('policy') and 
            balance_info['policy'].balance_due == 'check_out'):
            return Response({
                "detail": "Check-out requiere pago del saldo pendiente.",
                "requires_payment": True,
                "balance_due": float(balance_info['balance_due']),
                "total_paid": float(balance_info['total_paid']),
                "total_reservation": float(balance_info['total_reservation']),
                "payment_required_at": "check_out"
            }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        reservation.status = ReservationStatus.CHECK_OUT
        # Verificar si hay otra reserva activa hoy para la misma room
        today = date.today()
        overlapping_active = Reservation.objects.filter(
            room=reservation.room,
            status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN],
            check_in__lt=today,
            check_out__gt=today,
        ).exclude(pk=reservation.pk).exists()
        if not overlapping_active:
            reservation.room.status = RoomStatus.AVAILABLE
            reservation.room.save(update_fields=["status"])
        reservation.save(update_fields=["status"]) 
        # Crear tarea de limpieza de salida y marcar habitación como sucia
        try:
            from datetime import date as _date
            from apps.housekeeping.models import HousekeepingTask, TaskType, TaskStatus
            from apps.rooms.models import CleaningStatus
            today_date = _date.today()
            exists = HousekeepingTask.objects.filter(
                hotel=reservation.hotel,
                room=reservation.room,
                task_type=TaskType.CHECKOUT,
                created_at__date=today_date,
            ).exclude(status=TaskStatus.CANCELLED).exists()
            if not exists:
                HousekeepingTask.objects.create(
                    hotel=reservation.hotel,
                    room=reservation.room,
                    task_type=TaskType.CHECKOUT,
                    status=TaskStatus.PENDING,
                    zone=None,
                    created_by=request.user if request.user.is_authenticated else None,
                )
            # Marcar estado de limpieza como sucia
            if hasattr(reservation.room, "cleaning_status"):
                reservation.room.cleaning_status = CleaningStatus.DIRTY
                reservation.room.save(update_fields=["cleaning_status"])
        except Exception:
            # Evitar romper el flujo de checkout por errores de housekeeping
            pass
        from apps.reservations.models import ReservationChangeLog, ReservationChangeEvent
        ReservationChangeLog.objects.create(
            reservation=reservation,
            event_type=ReservationChangeEvent.CHECK_OUT,
            changed_by=request.user if request.user.is_authenticated else None,
        )
        return Response({"detail": "Check-out realizado."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def balance_info(self, request, pk=None):
        """Obtiene información del saldo pendiente de una reserva"""
        reservation = self.get_object()
        from apps.payments.services.payment_calculator import calculate_balance_due
        balance_info = calculate_balance_due(reservation)
        
        return Response({
            "has_balance": balance_info['has_balance'],
            "balance_due": float(balance_info['balance_due']),
            "total_paid": float(balance_info['total_paid']),
            "total_reservation": float(balance_info['total_reservation']),
            "policy": {
                "balance_due": balance_info.get('policy').balance_due if balance_info.get('policy') else None,
                "deposit_type": balance_info.get('policy').deposit_type if balance_info.get('policy') else None,
                "deposit_value": float(balance_info.get('policy').deposit_value) if balance_info.get('policy') else None,
            } if balance_info.get('policy') else None
        })

    @action(detail=True, methods=["get"])
    def test_cancellation(self, request, pk=None):
        """Endpoint de prueba para verificar que las acciones funcionan"""
        return Response({
            "message": "Endpoint de prueba funcionando",
            "reservation_id": pk,
            "timestamp": "2024-01-01T00:00:00Z"
        })

    @action(detail=True, methods=["get"])
    def cancellation_rules(self, request, pk=None):
        """Obtiene las reglas de cancelación y devolución para una reserva"""
        try:
            reservation = self.get_object()
            
            # Usar la política de cancelación aplicada a la reserva (histórica)
            if not reservation.applied_cancellation_policy:
                return Response({
                    "error": "No hay política de cancelación aplicada a esta reserva"
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Obtener política de devolución del hotel
            from apps.payments.models import RefundPolicy
            refund_policy = RefundPolicy.resolve_for_hotel(reservation.hotel)
            
            if not refund_policy:
                return Response({
                    "error": "No hay política de devolución configurada para este hotel"
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Calcular tiempo hasta el check-in
            from datetime import datetime
            check_in_date = reservation.check_in
            now = datetime.now().date()
            time_until_checkin = (check_in_date - now).total_seconds()
            
            # Obtener reglas de cancelación usando la política histórica
            cancellation_rules = reservation.applied_cancellation_policy.get_cancellation_rules(check_in_date)
            
            # Obtener reglas de devolución
            refund_rules = refund_policy.get_refund_rules(check_in_date)
            
            return Response({
                "cancellation_rules": cancellation_rules,
                "refund_rules": refund_rules,
                "applied_cancellation_policy": {
                    "id": reservation.applied_cancellation_policy.id,
                    "name": reservation.applied_cancellation_policy.name,
                    "applied_at": reservation.created_at.isoformat()
                },
                "reservation": {
                    "id": reservation.id,
                    "total_price": float(reservation.total_price),
                    "check_in": reservation.check_in.isoformat(),
                    "check_out": reservation.check_out.isoformat(),
                    "status": reservation.status
                }
            })
        except Exception as e:
            return Response({
                "error": f"Error interno del servidor: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """
        Cancela una reserva con opción de solo calcular o confirmar cancelación
        
        Parámetros:
        - confirm: true/false - Si es true, cancela la reserva. Si es false, solo calcula.
        """
        reservation = self.get_object()
        
        # Obtener parámetro confirm (por defecto true para mantener compatibilidad)
        confirm = request.data.get('confirm', True)
        if isinstance(confirm, str):
            confirm = confirm.lower() in ['true', '1', 'yes']
        
        # Obtener motivo de cancelación (obligatorio cuando se confirma)
        cancellation_reason = request.data.get('cancellation_reason', '').strip()
        if confirm and not cancellation_reason:
            return Response({
                "detail": "El motivo de cancelación es obligatorio",
                "field": "cancellation_reason"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener método de reembolso (opcional, por defecto 'money')
        refund_method = request.data.get('refund_method', 'money')
        if refund_method not in ['money', 'voucher']:
            refund_method = 'money'  # Fallback seguro
        
        # Debug temporal para ver el estado real de la reserva
        print(f"DEBUG: Reserva {reservation.id} - Estado actual: '{reservation.status}' (tipo: {type(reservation.status)})")
        print(f"DEBUG: Estados permitidos: {[ReservationStatus.PENDING, ReservationStatus.CONFIRMED]}")
        print(f"DEBUG: PENDING valor: '{ReservationStatus.PENDING}' (tipo: {type(ReservationStatus.PENDING)})")
        print(f"DEBUG: CONFIRMED valor: '{ReservationStatus.CONFIRMED}' (tipo: {type(ReservationStatus.CONFIRMED)})")
        print(f"DEBUG: ¿Es PENDING? {reservation.status == ReservationStatus.PENDING}")
        print(f"DEBUG: ¿Es CONFIRMED? {reservation.status == ReservationStatus.CONFIRMED}")
        print(f"DEBUG: ¿Está en la lista? {reservation.status in [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]}")
        
        if reservation.status not in [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]:
            return Response({
                "detail": "Solo se pueden cancelar reservas pendientes o confirmadas.",
                "debug": {
                    "current_status": reservation.status,
                    "allowed_statuses": [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Usar la política de cancelación aplicada a la reserva (histórica)
        if not reservation.applied_cancellation_policy:
            return Response({
                "detail": "No hay política de cancelación aplicada a esta reserva"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener política de devolución del hotel
        from apps.payments.models import RefundPolicy
        refund_policy = RefundPolicy.resolve_for_hotel(reservation.hotel)
        
        if not refund_policy:
            return Response({
                "detail": "No hay política de devolución configurada para este hotel"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calcular reglas de cancelación y devolución
        # Usar snapshot si está disponible, sino usar política actual
        from apps.reservations.services.snapshot_cancellation_calculator import SnapshotCancellationCalculator
        
        if SnapshotCancellationCalculator.should_use_snapshot(reservation):
            cancellation_rules = SnapshotCancellationCalculator.get_cancellation_rules_from_snapshot(reservation)
            if not cancellation_rules:
                # Fallback a política actual si no se puede calcular desde snapshot
                cancellation_rules = reservation.applied_cancellation_policy.get_cancellation_rules(reservation.check_in)
        else:
            cancellation_rules = reservation.applied_cancellation_policy.get_cancellation_rules(reservation.check_in)
        
        refund_rules = refund_policy.get_refund_rules(reservation.check_in)
        
        # Calcular información financiera
        from apps.payments.services.refund_processor import RefundProcessor
        from apps.payments.services.refund_processor_v2 import RefundProcessorV2
        from decimal import Decimal
        
        # Calcular monto total pagado
        total_paid = RefundProcessor._calculate_total_paid(reservation)
        
        # Calcular penalidad
        penalty_amount = RefundProcessor._calculate_penalty(reservation, cancellation_rules, total_paid)
        
        # Calcular monto de devolución
        refund_amount = RefundProcessor._calculate_refund_amount(total_paid, penalty_amount, refund_rules)
        
        # Preparar respuesta base
        response_data = {
            "cancellation_rules": cancellation_rules,
            "refund_rules": refund_rules,
            "financial_summary": {
                "total_paid": float(total_paid),
                "penalty_amount": float(penalty_amount),
                "refund_amount": float(refund_amount),
                "net_refund": float(refund_amount - penalty_amount)
            },
            "reservation": {
                "id": reservation.id,
                "status": reservation.status,
                "check_in": reservation.check_in.isoformat(),
                "check_out": reservation.check_out.isoformat(),
                "total_price": float(reservation.total_price)
            }
        }
        
        # Si solo es cálculo, devolver la información
        if not confirm:
            return Response({
                "detail": "Cálculo de cancelación completado",
                "action": "calculation",
                **response_data
            })
        
        # Si es confirmación, proceder con la cancelación
        refund_result = RefundProcessor.process_refund(reservation, cancellation_reason=cancellation_reason, refund_method=refund_method)
        
        if not refund_result or not refund_result.get('success', False):
            error_msg = refund_result.get('error', 'Error desconocido') if refund_result else 'Error procesando devolución'
            return Response({
                "detail": f"Error procesando devolución: {error_msg}",
                "action": "calculation",
                **response_data
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Marcar el refund como completado si se creó exitosamente
        if refund_result.get('refund_result') and refund_result['refund_result'].get('refund'):
            refund = refund_result['refund_result']['refund']
            # Marcar como completado con referencia externa simulada
            external_ref = f"REF-{refund.id}-{int(django_timezone.now().timestamp())}"
            refund.mark_as_completed(external_reference=external_ref, user=request.user)
        
        # Actualizar estado de la reserva principal
        reservation.status = ReservationStatus.CANCELLED
        reservation.save(update_fields=["status"])
        
        # Actualizar estado de la habitación a disponible (reserva principal)
        if reservation.room:
            from apps.rooms.models import RoomStatus
            reservation.room.status = RoomStatus.AVAILABLE
            reservation.room.save(update_fields=["status"])
        
        # Registrar log de cancelación con motivo
        from apps.reservations.models import ReservationChangeLog, ReservationChangeEvent
        ReservationChangeLog.objects.create(
            reservation=reservation,
            event_type=ReservationChangeEvent.CANCEL,
            changed_by=request.user,
            message=f"Reserva cancelada manualmente. Motivo: {cancellation_reason}",
            fields_changed={
                'cancellation_reason': cancellation_reason,
                'refund_amount': refund_result.get('refund_amount', 0) if refund_result else 0,
                'penalty_amount': refund_result.get('penalty_amount', 0) if refund_result else 0,
                'total_paid': refund_result.get('total_paid', 0) if refund_result else 0,
                'manual_cancellation': True
            }
        )

        # Si la reserva forma parte de un grupo multi-habitación, cancelar también
        # las demás reservas del mismo group_code (solo estados pendientes/confirmados)
        if reservation.group_code:
            from apps.rooms.models import RoomStatus
            from .models import Reservation as ReservationModel
            from apps.reservations.models import ReservationChangeLog as GroupChangeLog, ReservationChangeEvent as GroupChangeEvent

            sibling_reservations = (
                ReservationModel.objects
                .filter(group_code=reservation.group_code)
                .exclude(pk=reservation.pk)
            )

            for sibling in sibling_reservations:
                if sibling.status not in [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]:
                    continue

                # Marcar reserva del grupo como cancelada
                sibling.status = ReservationStatus.CANCELLED
                sibling.save(update_fields=["status"])

                # Liberar habitación asociada
                if sibling.room:
                    sibling.room.status = RoomStatus.AVAILABLE
                    sibling.room.save(update_fields=["status"])

                # Registrar log de cancelación para la reserva del grupo
                GroupChangeLog.objects.create(
                    reservation=sibling,
                    event_type=GroupChangeEvent.CANCEL,
                    changed_by=request.user,
                    message=f"Reserva cancelada como parte de un grupo multi-habitación (grupo {reservation.group_code}). Motivo: {cancellation_reason}",
                    fields_changed={
                        'cancellation_reason': cancellation_reason,
                        'manual_cancellation': True,
                        'group_code': reservation.group_code,
                        'cancelled_with_reservation_id': reservation.id,
                    }
                )
        
        # Crear notificación de cancelación manual
        try:
            from apps.notifications.services import NotificationService
            NotificationService.create_manual_cancel_notification(
                reservation_code=f"RES-{reservation.id}",
                hotel_name=reservation.hotel.name,
                reason=cancellation_reason,
                hotel_id=reservation.hotel.id,
                reservation_id=reservation.id,
                user_id=request.user.id  # Notificar al usuario que canceló (staff)
            )
        except Exception as e:
            print(f"⚠️ Error creando notificación de cancelación manual para reserva {reservation.id}: {e}")
        
        # Enviar email al huésped informando cancelación (con o sin devolución)
        try:
            from apps.reservations.services.email_service import ReservationEmailService
            ReservationEmailService.send_cancellation_email(
                reservation,
                cancellation_reason=cancellation_reason,
                total_paid=float(refund_result.get('total_paid', 0)) if refund_result else 0.0,
                penalty_amount=float(refund_result.get('penalty_amount', 0)) if refund_result else 0.0,
                refund_amount=float(refund_result.get('refund_amount', 0)) if refund_result else 0.0,
            )
        except Exception as e:
            print(f"⚠️ Error enviando email de cancelación para reserva {reservation.id}: {e}")
        
        # Obtener información detallada del reembolso
        refund_details = None
        if refund_result and refund_result.get('refund_result'):
            refund_obj = refund_result['refund_result'].get('refund')
            if refund_obj:
                refund_details = {
                    "id": refund_obj.id,
                    "amount": float(refund_obj.amount),
                    "status": refund_obj.status,
                    "method": refund_obj.refund_method,
                    "external_reference": refund_obj.external_reference,
                    "processing_days": refund_obj.processing_days,
                    "processed_at": refund_obj.processed_at.isoformat() if refund_obj.processed_at else None,
                    "notes": refund_obj.notes,
                    "created_at": refund_obj.created_at.isoformat(),
                    "requires_manual_processing": refund_result['refund_result'].get('requires_manual_processing', False)
                }
        
        # Obtener método de devolución de forma segura
        refund_method = 'N/A'
        if refund_result and refund_result.get('refund_result'):
            refund_method = refund_result['refund_result'].get('method', 'N/A')
        
        # Información de cancelación detallada
        cancellation_details = {
            "reason": cancellation_reason,
            "policy_applied": reservation.applied_cancellation_policy.name if reservation.applied_cancellation_policy else "N/A",
            "cancellation_type": cancellation_rules.get('cancellation_type', 'unknown') if cancellation_rules else 'unknown',
            "cancelled_by": {
                "id": request.user.id if request.user.is_authenticated else None,
                "username": request.user.username if request.user.is_authenticated else "Sistema",
                "full_name": request.user.get_full_name() if request.user.is_authenticated else "Sistema"
            },
            "cancelled_at": django_timezone.now().isoformat()
        }
        
        return Response({
            "detail": "Reserva cancelada exitosamente.",
            "action": "cancelled",
            "refund": refund_details,
            "refund_info": {
                "total_paid": refund_result.get('total_paid', 0) if refund_result else 0,
                "penalty_amount": refund_result.get('penalty_amount', 0) if refund_result else 0,
                "refund_amount": refund_result.get('refund_amount', 0) if refund_result else 0,
                "refund_processed": refund_result.get('refund_processed', False) if refund_result else False,
                "refund_method": refund_method
            },
            "cancellation_details": cancellation_details,
            **response_data
        })

    @action(detail=True, methods=["get"])
    def debug_status(self, request, pk=None):
        """Endpoint temporal para debug del estado de la reserva"""
        reservation = self.get_object()
        return Response({
            "reservation_id": reservation.id,
            "current_status": reservation.status,
            "status_type": type(reservation.status).__name__,
            "pending_value": ReservationStatus.PENDING,
            "confirmed_value": ReservationStatus.CONFIRMED,
            "is_pending": reservation.status == ReservationStatus.PENDING,
            "is_confirmed": reservation.status == ReservationStatus.CONFIRMED,
            "in_allowed_list": reservation.status in [ReservationStatus.PENDING, ReservationStatus.CONFIRMED],
            "all_status_choices": [choice[0] for choice in ReservationStatus.choices]
        })

    @action(detail=True, methods=["get"])
    def refund_history(self, request, pk=None):
        """Obtiene el historial de devoluciones de una reserva"""
        reservation = self.get_object()
        
        # Obtener pagos de devolución (montos negativos)
        refund_payments = reservation.payments.filter(
            amount__lt=0
        ).order_by('-date')
        
        # Obtener logs de cancelación con información de devolución
        from apps.reservations.models import ReservationChangeLog, ReservationChangeEvent
        cancellation_logs = reservation.change_logs.filter(
            event_type=ReservationChangeEvent.CANCEL
        ).order_by('-changed_at')
        
        refund_data = []
        
        # Procesar pagos de devolución
        for payment in refund_payments:
            refund_data.append({
                'type': 'payment_refund',
                'date': payment.date.isoformat(),
                'amount': float(abs(payment.amount)),
                'method': payment.method,
                'status': 'completed',
                'notes': None  # El modelo Payment no tiene campo notes
            })
        
        # Procesar logs de cancelación
        for log in cancellation_logs:
            if log.fields_changed and 'refund_amount' in log.fields_changed:
                refund_data.append({
                    'type': 'cancellation_refund',
                    'date': log.changed_at.isoformat(),
                    'amount': log.fields_changed.get('refund_amount', 0),
                    'method': log.fields_changed.get('refund_result', {}).get('method', 'N/A'),
                    'status': 'processed' if log.fields_changed.get('refund_processed', False) else 'pending',
                    'notes': f"Devolución por cancelación - Penalidad: ${log.fields_changed.get('penalty_amount', 0)}"
                })
        
        return Response({
            'reservation_id': reservation.id,
            'total_refunds': len(refund_data),
            'refunds': sorted(refund_data, key=lambda x: x['date'], reverse=True)
        })

    @action(detail=False, methods=['post'])
    def auto_cancel_expired(self, request):
        """Ejecuta manualmente la auto-cancelación de reservas vencidas"""
        from apps.reservations.tasks import auto_cancel_expired_reservations
        
        try:
            # Ejecutar la tarea de auto-cancelación
            result = auto_cancel_expired_reservations.delay()
            
            return Response({
                'success': True,
                'message': 'Tarea de auto-cancelación iniciada',
                'task_id': result.id
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error iniciando auto-cancelación: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def pending_expiration_stats(self, request):
        """Obtiene estadísticas de reservas pendientes y sus fechas de vencimiento"""
        from apps.payments.services.payment_calculator import calculate_balance_due
        from apps.payments.models import PaymentPolicy
        
        try:
            # Obtener reservas pendientes
            pending_reservations = Reservation.objects.select_related("hotel", "room").filter(
                status=ReservationStatus.PENDING
            )
            
            stats = {
                'total_pending': pending_reservations.count(),
                'expired_today': 0,
                'expires_tomorrow': 0,
                'expires_this_week': 0,
                'expires_next_week': 0,
                'expires_later': 0,
                'no_policy': 0,
                'reservations': []
            }
            
            from datetime import date, timedelta
            today = date.today()
            tomorrow = today + timedelta(days=1)
            next_week = today + timedelta(days=7)
            week_after = today + timedelta(days=14)
            
            for reservation in pending_reservations:
                # Obtener política de pago del hotel
                payment_policy = PaymentPolicy.resolve_for_hotel(reservation.hotel)
                
                if not payment_policy:
                    stats['no_policy'] += 1
                    continue
                
                # Calcular información de pago
                balance_info = calculate_balance_due(reservation)
                deposit_due_date = balance_info.get('deposit_due_date')
                
                if not deposit_due_date:
                    continue
                
                # Categorizar por fecha de vencimiento
                if deposit_due_date < today:
                    stats['expired_today'] += 1
                elif deposit_due_date == today:
                    stats['expires_tomorrow'] += 1
                elif deposit_due_date <= next_week:
                    stats['expires_this_week'] += 1
                elif deposit_due_date <= week_after:
                    stats['expires_next_week'] += 1
                else:
                    stats['expires_later'] += 1
                
                # Agregar detalles de la reserva
                stats['reservations'].append({
                    'id': reservation.id,
                    'hotel_name': reservation.hotel.name,
                    'room_name': reservation.room.name if reservation.room else 'N/A',
                    'guest_name': reservation.guest_name,
                    'check_in': reservation.check_in.isoformat(),
                    'check_out': reservation.check_out.isoformat(),
                    'total_price': float(reservation.total_price),
                    'deposit_due_date': deposit_due_date.isoformat(),
                    'days_until_expiry': (deposit_due_date - today).days,
                    'is_expired': deposit_due_date < today,
                    'payment_policy_name': payment_policy.name
                })
            
            # Ordenar reservas por fecha de vencimiento
            stats['reservations'].sort(key=lambda x: x['deposit_due_date'])
            
            return Response(stats)
            
        except Exception as e:
            return Response({
                'error': f'Error obteniendo estadísticas: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AvailabilityView(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RoomSerializer
    queryset = Room.objects.all()  #

    def get(self, request):
        hotel_id = request.query_params.get("hotel")
        start_str = request.query_params.get("start")
        end_str = request.query_params.get("end")
        channel = request.query_params.get("channel")
        calendar = request.query_params.get("calendar")  # "1"/"true" para incluir detalles por día
        if not (hotel_id and start_str and end_str):
            return Response({"detail": "Parámetros requeridos: hotel, start, end"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start = date.fromisoformat(start_str)
            end = date.fromisoformat(end_str)
        except ValueError:
            return Response({"detail": "Fechas inválidas (YYYY-MM-DD)"}, status=status.HTTP_400_BAD_REQUEST)
        if start > end:
            return Response({"detail": "la fecha de check-in debe ser anterior a la fecha de check-out"}, status=status.HTTP_400_BAD_REQUEST)

        active_status = [
            ReservationStatus.PENDING,
            ReservationStatus.CONFIRMED,
            ReservationStatus.CHECK_IN,
        ]

        rooms = (
            Room.objects.select_related("hotel")
            .filter(hotel_id=hotel_id)
            .exclude(status=RoomStatus.OUT_OF_SERVICE)
            .exclude(
                reservations__status__in=active_status,
                reservations__check_in__lt=end,
                reservations__check_out__gt=start,
            )
            .exclude(
                room_blocks__is_active=True,
                room_blocks__start_date__lt=end,
                room_blocks__end_date__gt=start,
            )
            .distinct()
        )

        page = self.paginate_queryset(rooms)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Si se solicita calendario detallado, devolver por habitación el estado por día
        if calendar in ("1", "true", "True"):
            def get_applicable_rule(room, on_date, channel_value):
                plans = RatePlan.objects.filter(hotel=room.hotel, is_active=True).order_by("-priority", "id").prefetch_related("rules")
                for plan in plans:
                    rules = sorted(plan.rules.all(), key=lambda r: r.priority, reverse=True)
                    for rule in rules:
                        if not (rule.start_date <= on_date <= rule.end_date):
                            continue
                        dow = on_date.weekday()
                        if not [rule.apply_mon, rule.apply_tue, rule.apply_wed, rule.apply_thu, rule.apply_fri, rule.apply_sat, rule.apply_sun][dow]:
                            continue
                        if rule.target_room_id and rule.target_room_id != room.id:
                            continue
                        if rule.target_room_type and rule.target_room_type != room.room_type:
                            continue
                        if rule.channel and channel_value and rule.channel != channel_value:
                            continue
                        if rule.channel and not channel_value:
                            continue
                        return rule
                return None

            results = []
            for room in rooms:
                days = []
                current = start
                while current <= end:
                    rule = get_applicable_rule(room, current, channel)
                    day_info = {
                        "date": current,
                        "available": True,
                        "closed": False,
                        "closed_to_arrival": False,
                        "closed_to_departure": False,
                        "min_stay": None,
                        "max_stay": None,
                    }
                    if rule:
                        if rule.closed:
                            day_info["available"] = False
                            day_info["closed"] = True
                        if rule.closed_to_arrival:
                            day_info["closed_to_arrival"] = True
                        if rule.closed_to_departure:
                            day_info["closed_to_departure"] = True
                        if rule.min_stay:
                            day_info["min_stay"] = rule.min_stay
                        if rule.max_stay:
                            day_info["max_stay"] = rule.max_stay
                    days.append(day_info)
                    current += timedelta(days=1)
                results.append({
                    "room": self.get_serializer(room).data,
                    "days": days,
                })
            return Response({
                "hotel": int(hotel_id),
                "start": start,
                "end": end,
                "channel": channel,
                "results": results,
            }, status=status.HTTP_200_OK)

        serializer = self.get_serializer(rooms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def pricing_quote(request):
    room_id = int(request.query_params.get("room_id"))
    guests = int(request.query_params.get("guests", 1))
    check_in = date.fromisoformat(request.query_params.get("check_in"))
    check_out = date.fromisoformat(request.query_params.get("check_out"))

    room = Room.objects.get(id=room_id)
    nights = []
    total = Decimal('0.00')

    current = check_in

    while current < check_out:
        parts = compute_nightly_rate(room, guests, current)
        nights.append({
            'date': current,
            'base_rate': parts['base_rate'],
            'extra_guest_fee': parts['extra_guest_fee'],
            'discount': parts['discount'],
            'tax': parts['tax'],
            'total_night': parts['total_night'],
        })
        total += parts['total_night']
        current += timedelta(days=1)

    return Response({
        'room_id': room_id,
        'guests': guests,
        'check_in': check_in,
        'check_out': check_out,
        'nights': nights,
        'total': total,
    })


@api_view(['GET'])
def can_book(request):
    """Valida si se puede reservar una habitación en el rango dado respetando CTA/CTD y min/max stay.
    Parámetros: room_id, check_in (YYYY-MM-DD), check_out (YYYY-MM-DD), guests (opcional), channel (opcional)
    """
    try:
        room_id = int(request.query_params.get("room_id"))
        check_in = date.fromisoformat(request.query_params.get("check_in"))
        check_out = date.fromisoformat(request.query_params.get("check_out"))
    except Exception:
        return Response({"detail": "Parámetros inválidos."}, status=status.HTTP_400_BAD_REQUEST)

    channel = request.query_params.get("channel")
    if check_in >= check_out:
        return Response({"detail": "check_in debe ser anterior a check_out."}, status=status.HTTP_400_BAD_REQUEST)
    room = get_object_or_404(Room.objects.select_related("hotel"), pk=room_id)

    # CTA/CTD
    start_rule = get_applicable_rule(room, check_in, channel, include_closed=True)
    if start_rule and start_rule.closed_to_arrival:
        return Response({"ok": False, "reason": "closed_to_arrival"}, status=status.HTTP_200_OK)
    end_rule = get_applicable_rule(room, check_out, channel, include_closed=True)
    if end_rule and end_rule.closed_to_departure:
        return Response({"ok": False, "reason": "closed_to_departure"}, status=status.HTTP_200_OK)

    # min/max stay
    nights = (check_out - check_in).days
    if start_rule and start_rule.min_stay and nights < start_rule.min_stay:
        return Response({"ok": False, "reason": "min_stay", "value": start_rule.min_stay}, status=status.HTTP_200_OK)
    if start_rule and start_rule.max_stay and nights > start_rule.max_stay:
        return Response({"ok": False, "reason": "max_stay", "value": start_rule.max_stay}, status=status.HTTP_200_OK)

    # Días cerrados
    current = check_in
    while current < check_out:
        rule = get_applicable_rule(room, current, channel, include_closed=True)
        if rule and rule.closed:
            return Response({"ok": False, "reason": "closed", "date": current}, status=status.HTTP_200_OK)
        current += timedelta(days=1)

    return Response({"ok": True}, status=status.HTTP_200_OK)


@api_view(['GET'])
def quote_range(request):
    """Valida CTA/CTD y min/max stay y, si es válido, devuelve el detalle por noche y totales.
    Parámetros: room_id, check_in, check_out, guests (opcional, default 1), channel (opcional)
    """
    try:
        room_id = int(request.query_params.get("room_id"))
        check_in = date.fromisoformat(request.query_params.get("check_in"))
        check_out = date.fromisoformat(request.query_params.get("check_out"))
        guests = int(request.query_params.get("guests", 1))
    except Exception:
        return Response({"detail": "Parámetros inválidos."}, status=status.HTTP_400_BAD_REQUEST)

    channel = request.query_params.get("channel")
    promo_code = request.query_params.get("promotion_code")
    if check_in >= check_out:
        return Response({"detail": "check_in debe ser anterior a check_out."}, status=status.HTTP_400_BAD_REQUEST)
    room = get_object_or_404(Room.objects.select_related("hotel"), pk=room_id)

    # Validaciones CTA/CTD / min-max / closed
    start_rule = get_applicable_rule(room, check_in, channel, include_closed=True)
    if start_rule and start_rule.closed_to_arrival:
        return Response({"ok": False, "reason": "closed_to_arrival"}, status=status.HTTP_200_OK)
    end_rule = get_applicable_rule(room, check_out, channel, include_closed=True)
    if end_rule and end_rule.closed_to_departure:
        return Response({"ok": False, "reason": "closed_to_departure"}, status=status.HTTP_200_OK)

    nights = (check_out - check_in).days
    if start_rule and start_rule.min_stay and nights < start_rule.min_stay:
        return Response({"ok": False, "reason": "min_stay", "value": start_rule.min_stay}, status=status.HTTP_200_OK)
    if start_rule and start_rule.max_stay and nights > start_rule.max_stay:
        return Response({"ok": False, "reason": "max_stay", "value": start_rule.max_stay}, status=status.HTTP_200_OK)

    current = check_in
    raw_days = []
    while current < check_out:
        rule = get_applicable_rule(room, current, channel, include_closed=True)
        if rule and rule.closed:
            return Response({"ok": False, "reason": "closed", "date": current}, status=status.HTTP_200_OK)
        pricing = compute_rate_for_date(room, guests, current, channel, promo_code)
        applied_rule = None
        if rule:
            applied_rule = {
                "id": rule.id,
                "plan_id": rule.plan_id,
                "name": rule.name,
                "priority": rule.priority,
                "channel": rule.channel,
                "price_mode": rule.price_mode,
            }
        raw_days.append({
            "date": current,
            "pricing": pricing,
            "rule": applied_rule,
        })
        current += timedelta(days=1)

    # Prorrateo de promos por reserva
    bases = []
    for d in raw_days:
        p = d["pricing"]
        bases.append(p["base_rate"] + p["extra_guest_fee"] - p["discount"])  # base neta sin impuestos
    total_base = sum(bases) if bases else Decimal('0.00')

    per_res_promos = PromoRule.objects.none()
    if promo_code:
        per_res_promos = PromoRule.objects.filter(
            hotel=room.hotel,
            is_active=True,
            scope=PromoRule.PromoScope.PER_RESERVATION,
        )
        if channel:
            per_res_promos = per_res_promos.filter(models.Q(channel__isnull=True) | models.Q(channel=channel))
        else:
            per_res_promos = per_res_promos.filter(channel__isnull=True)
        per_res_promos = per_res_promos.filter(models.Q(code__iexact=str(promo_code)))

    total_res_discount = Decimal('0.00')
    applied_any = False
    applied_per_res_promo = None
    for promo in per_res_promos.order_by('-priority'):
        applicable = False
        for d in raw_days:
            dd = d['date']
            if not (promo.start_date <= dd <= promo.end_date):
                continue
            if not [promo.apply_mon, promo.apply_tue, promo.apply_wed, promo.apply_thu, promo.apply_fri, promo.apply_sat, promo.apply_sun][dd.weekday()]:
                continue
            applicable = True
            break
        if not applicable:
            continue
        if total_base <= 0:
            break
        if promo.discount_type == DiscountType.PERCENT:
            total_res_discount = (Decimal(total_base) * (promo.discount_value / Decimal('100'))).quantize(Decimal('0.01'))
        else:
            total_res_discount = Decimal(promo.discount_value).quantize(Decimal('0.01'))
        applied_any = total_res_discount > 0
        if applied_any and not applied_per_res_promo:
            applied_per_res_promo = promo
        if applied_any and not promo.combinable:
            break

    days = []
    total = Decimal('0.00')
    if applied_any and total_base > 0:
        for idx, d in enumerate(raw_days):
            p = d['pricing']
            proportion = (bases[idx] / total_base) if total_base > 0 else Decimal('0.00')
            extra_discount = (total_res_discount * proportion).quantize(Decimal('0.01'))
            discount = p['discount'] + extra_discount
            taxable = (p['base_rate'] + p['extra_guest_fee'] - discount)
            if taxable < 0:
                taxable = Decimal('0.00')
            total_night = (taxable + p['tax']).quantize(Decimal('0.01'))
            # Merge promo details
            details = list(p.get('applied_promos_detail') or [])
            if applied_per_res_promo:
                details.append({
                    'id': applied_per_res_promo.id,
                    'name': applied_per_res_promo.name,
                    'code': applied_per_res_promo.code,
                    'scope': 'per_reservation',
                    'amount': float(extra_discount),
                })
            adj = { **p, 'discount': discount, 'total_night': total_night, 'applied_promos_detail': details }
            days.append({ "date": d['date'], "pricing": adj, "rule": d.get('rule') })
            total += total_night
    else:
        for d in raw_days:
            days.append(d)
            total += d['pricing']['total_night']

    adr = (total / Decimal(nights)).quantize(Decimal('0.01')) if nights else Decimal('0.00')
    return Response({
        "ok": True,
        "room_id": room.id,
        "hotel_id": room.hotel_id,
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
        "channel": channel,
        "nights": nights,
        "days": days,
        "total": total,
        "adr": adr,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def quote(request):
    """Endpoint POST para cotizar una estadía completa con validaciones y detalle por noche.
    Body JSON esperado: {
      "room_id": int,
      "check_in": "YYYY-MM-DD",
      "check_out": "YYYY-MM-DD",
      "guests": int (opcional, default 1),
      "channel": str (opcional)
    }
    """
    body = request.data or {}
    try:
        room_id = int(body.get("room_id"))
        check_in = date.fromisoformat(body.get("check_in"))
        check_out = date.fromisoformat(body.get("check_out"))
        guests = int(body.get("guests", 1))
    except Exception:
        return Response({"detail": "Parámetros inválidos."}, status=status.HTTP_400_BAD_REQUEST)

    channel = body.get("channel")
    promo_code = body.get("promotion_code")
    if guests < 1:
        return Response({"detail": "guests debe ser >= 1"}, status=status.HTTP_400_BAD_REQUEST)
    if check_in >= check_out:
        return Response({"detail": "check_in debe ser anterior a check_out."}, status=status.HTTP_400_BAD_REQUEST)

    room = get_object_or_404(Room.objects.select_related("hotel"), pk=room_id)

    # Validar capacidad
    if guests > (room.max_capacity or 1):
        return Response({"ok": False, "reason": "capacity_exceeded", "max_capacity": room.max_capacity}, status=status.HTTP_200_OK)

    # Validar solapamiento de reservas activas
    active_status = [
        ReservationStatus.PENDING,
        ReservationStatus.CONFIRMED,
        ReservationStatus.CHECK_IN,
    ]
    overlap = Reservation.objects.filter(
        room=room,
        status__in=active_status,
        check_in__lt=check_out,
        check_out__gt=check_in,
    ).exists()
    if overlap:
        return Response({"ok": False, "reason": "overlap"}, status=status.HTTP_200_OK)

    # Validar bloqueos de habitación
    blocked = RoomBlock.objects.filter(
        room=room,
        is_active=True,
        start_date__lt=check_out,
        end_date__gt=check_in,
    ).exists()
    if blocked:
        return Response({"ok": False, "reason": "room_block"}, status=status.HTTP_200_OK)

    # CTA/CTD y min/max stay
    start_rule = get_applicable_rule(room, check_in, channel, include_closed=True)
    if start_rule and start_rule.closed_to_arrival:
        return Response({"ok": False, "reason": "closed_to_arrival"}, status=status.HTTP_200_OK)
    end_rule = get_applicable_rule(room, check_out, channel, include_closed=True)
    if end_rule and end_rule.closed_to_departure:
        return Response({"ok": False, "reason": "closed_to_departure"}, status=status.HTTP_200_OK)

    nights = (check_out - check_in).days
    if start_rule and start_rule.min_stay and nights < start_rule.min_stay:
        return Response({"ok": False, "reason": "min_stay", "value": start_rule.min_stay}, status=status.HTTP_200_OK)
    if start_rule and start_rule.max_stay and nights > start_rule.max_stay:
        return Response({"ok": False, "reason": "max_stay", "value": start_rule.max_stay}, status=status.HTTP_200_OK)

    # Días cerrados y pricing
    current = check_in
    days = []
    total = Decimal('0.00')
    while current < check_out:
        rule = get_applicable_rule(room, current, channel, include_closed=True)
        if rule and rule.closed:
            return Response({"ok": False, "reason": "closed", "date": current}, status=status.HTTP_200_OK)
        pricing = compute_rate_for_date(room, guests, current, channel, promo_code)
        applied_rule = None
        if rule:
            applied_rule = {
                "id": rule.id,
                "plan_id": rule.plan_id,
                "name": rule.name,
                "priority": rule.priority,
                "channel": rule.channel,
                "price_mode": rule.price_mode,
            }
        days.append({
            "date": current,
            "pricing": pricing,
            "rule": applied_rule,
        })
        total += pricing["total_night"]
        current += timedelta(days=1)

    adr = (total / Decimal(nights)).quantize(Decimal('0.01')) if nights else Decimal('0.00')
    return Response({
        "ok": True,
        "room_id": room.id,
        "hotel_id": room.hotel_id,
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
        "channel": channel,
        "nights": nights,
        "days": days,
        "total": total,
        "adr": adr,
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
def pricing_daily_summary(request):
    hotel_id_str = request.query_params.get("hotel_id")
    start_date_str = request.query_params.get("start_date")
    end_date_str = request.query_params.get("end_date")
    mode = request.query_params.get("mode", "check_in")
    metric = request.query_params.get("metric", "gross")
    
    # Validación básica de parámetros
    if not hotel_id_str or not start_date_str or not end_date_str:
        return Response(
            {"detail": "Parámetros requeridos: hotel_id, start_date, end_date"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        hotel_id = int(hotel_id_str)
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
    except (ValueError, TypeError):
        return Response(
            {"detail": "Parámetros inválidos. Formatos: hotel_id=int, fechas=YYYY-MM-DD"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if mode == "check_in":
        qs = Reservation.objects.filter(
            hotel_id=hotel_id,
            check_in__range=[start_date, end_date],
            status__in=[ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN, ReservationStatus.CHECK_OUT],
        )
        # Gross por día (suma de total_price en fecha de check-in)
        per = qs.values('check_in').annotate(revenue=Sum('total_price')).order_by('check_in')
        daily_map = {r['check_in']: (r['revenue'] or Decimal('0.00')) for r in per}
        total = sum(daily_map.values()) if daily_map else Decimal('0.00')

        # Net: restar comisiones imputadas al día de check-in
        if metric == "net":
            from apps.reservations.models import ChannelCommission
            comm_per = ChannelCommission.objects.filter(
                reservation__in=qs
            ).values('reservation__check_in').annotate(comm=Sum('amount'))
            for row in comm_per:
                d = row['reservation__check_in']
                comm = row['comm'] or Decimal('0.00')
                daily_map[d] = (daily_map.get(d, Decimal('0.00')) - comm)
            total = sum(daily_map.values()) if daily_map else Decimal('0.00')

        daily = [{'date': d, 'revenue': v} for d, v in sorted(daily_map.items())]
    else:
        # Modo devengo por noche usando ReservationNight
        qs = ReservationNight.objects.filter(
            hotel_id=hotel_id,
            date__range=[start_date, end_date],
        )
        total = qs.aggregate(s=Sum('total_night'))['s'] or Decimal('0.00')
        per = qs.values('date').annotate(revenue=Sum('total_night')).order_by('date')
        daily = [{'date': r['date'], 'revenue': r['revenue']} for r in per]
    
    return Response({
        'hotel_id': hotel_id,
        'period': {'start_date': start_date, 'end_date': end_date},
        'mode': mode,
        'metric': metric,
        'total': total,
        'daily': daily,
    })


@api_view(['GET'])
def reservation_pricing_summary(request, pk: int):
    try:
        reservation = Reservation.objects.get(pk=pk)
    except Reservation.DoesNotExist:
        return Response({"detail": "Reserva no encontrada"}, status=status.HTTP_404_NOT_FOUND)

    nights = reservation.nights.order_by('date').values(
        'date', 'base_rate', 'extra_guest_fee', 'discount', 'tax', 'total_night'
    )
    charges = reservation.charges.order_by('date').values('date', 'description', 'amount')
    payments = reservation.payments.order_by('date').values('date', 'method', 'amount')

    from django.db.models import Sum
    from decimal import Decimal
    totals = {
        'nights_total': reservation.nights.aggregate(s=Sum('total_night'))['s'] or Decimal('0.00'),
        'charges_total': reservation.charges.aggregate(s=Sum('amount'))['s'] or Decimal('0.00'),
        'payments_total': reservation.payments.aggregate(s=Sum('amount'))['s'] or Decimal('0.00'),
    }
    nights_count = reservation.nights.count()
    adr = (totals['nights_total'] / nights_count).quantize(Decimal('0.01')) if nights_count else Decimal('0.00')
    # Comisión por canal (si existe)
    commission = reservation.commissions.order_by('-created_at').first()
    commission_amount = commission.amount if commission else Decimal('0.00')

    net_total = (reservation.total_price or Decimal('0.00')) - commission_amount
    balance = (totals['payments_total'] or Decimal('0.00')) - (reservation.total_price or Decimal('0.00'))
    data = {
        'reservation_id': reservation.id,
        'hotel_id': reservation.hotel_id,
        'room_id': reservation.room_id,
        'guest_name': reservation.guest_name,
        'check_in': reservation.check_in,
        'check_out': reservation.check_out,
        'status': reservation.status,
        'nights': list(nights),
        'charges': list(charges),
        'payments': list(payments),
        'totals': {
            **totals,
            'total_price': reservation.total_price,
            'adr': adr,
            'nights_count': nights_count,
            'commission_amount': commission_amount,
            'net_total': net_total,
            'balance': balance,
        }
    }
    return Response(data)


# ----- Charges / Payments / Commission -----

@api_view(['GET', 'POST'])
def reservation_charges(request, pk: int):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'GET':
        ser = ReservationChargeSerializer(reservation.charges.order_by('-date'), many=True)
        return Response(ser.data)
    # POST
    ser = ReservationChargeSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    charge = reservation.charges.create(**ser.validated_data)
    recalc_reservation_totals(reservation)
    from apps.reservations.models import ReservationChangeLog, ReservationChangeEvent
    ReservationChangeLog.objects.create(
        reservation=reservation,
        event_type=ReservationChangeEvent.CHARGE_ADDED,
        changed_by=request.user if request.user.is_authenticated else None,
        message=f"+ {ser.validated_data.get('description', '')} ${ser.validated_data.get('amount')}"
    )
    return Response(ReservationChargeSerializer(charge).data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
def reservation_charge_delete(request, pk: int, charge_id: int):
    reservation = get_object_or_404(Reservation, pk=pk)
    charge = get_object_or_404(reservation.charges, pk=charge_id)
    charge.delete()
    recalc_reservation_totals(reservation)
    from apps.reservations.models import ReservationChangeLog, ReservationChangeEvent
    ReservationChangeLog.objects.create(
        reservation=reservation,
        event_type=ReservationChangeEvent.CHARGE_REMOVED,
        changed_by=request.user if request.user.is_authenticated else None,
        message=f"- cargo #{charge_id}"
    )
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def reservation_payments(request, pk: int):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'GET':
        ser = PaymentSerializer(reservation.payments.order_by('-date'), many=True)
        return Response(ser.data)
    # POST
    ser = PaymentSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    
    # Manejar lógica específica para POSTNET
    validated_data = ser.validated_data.copy()
    if validated_data.get('method') == 'pos':
        # Si es POSTNET, determinar el status basado en si está liquidado
        is_settled = request.data.get('is_settled', False)
        validated_data['status'] = 'approved' if is_settled else 'pending_settlement'
    
    payment = reservation.payments.create(**validated_data)
    from apps.reservations.models import ReservationChangeLog, ReservationChangeEvent
    ReservationChangeLog.objects.create(
        reservation=reservation,
        event_type=ReservationChangeEvent.PAYMENT_ADDED,
        changed_by=request.user if request.user.is_authenticated else None,
        message=f"+ pago ${ser.validated_data.get('amount')} ({ser.validated_data.get('method')})"
    )
    return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
def reservation_commission(request, pk: int):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'GET':
        comm = reservation.commissions.order_by('-created_at').first()
        if not comm:
            return Response({'detail': 'Sin comisión'}, status=status.HTTP_200_OK)
        return Response(ChannelCommissionSerializer(comm).data)

    # POST: { "channel": "booking", "rate_percent": 15.0 }
    ser = ChannelCommissionSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data
    rate = data.get('rate_percent') or Decimal('0.00')
    amount = (reservation.total_price or Decimal('0.00')) * (Decimal(rate) / Decimal('100'))
    comm, created = reservation.commissions.get_or_create(
        channel=data.get('channel', 'direct'),
        defaults={'rate_percent': rate, 'amount': amount},
    )
    if not created:
        comm.rate_percent = rate
        comm.amount = amount
        comm.save(update_fields=['rate_percent', 'amount'])
    from apps.reservations.models import ReservationChangeLog, ReservationChangeEvent
    ReservationChangeLog.objects.create(
        reservation=reservation,
        event_type=ReservationChangeEvent.COMMISSION_UPDATED,
        changed_by=request.user if request.user.is_authenticated else None,
        message=f"commission {comm.channel} {comm.rate_percent}% (${comm.amount})"
    )
    return Response(ChannelCommissionSerializer(comm).data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def reservation_history(request, pk: int):
    reservation = get_object_or_404(Reservation, pk=pk)

    status_changes_qs = reservation.status_changes.select_related("changed_by").order_by("-changed_at")
    changes_qs = reservation.change_logs.select_related("changed_by").order_by("-changed_at")

    def serialize_user(u):
        if not u:
            return None
        return {"id": u.id, "username": getattr(u, "username", None), "email": getattr(u, "email", None)}

    timeline = []
    for sc in status_changes_qs:
        timeline.append({
            "type": "status_change",
            "changed_at": sc.changed_at,
            "changed_by": serialize_user(sc.changed_by),
            "detail": {
                "from": sc.from_status,
                "to": sc.to_status,
                "notes": sc.notes,
            },
        })
    for cl in changes_qs:
        timeline.append({
            "type": "change_log",
            "changed_at": cl.changed_at,
            "changed_by": serialize_user(cl.changed_by),
            "detail": {
                "event_type": cl.event_type,
                "fields_changed": cl.fields_changed,
                "message": cl.message,
                "snapshot": cl.snapshot,  # Incluir snapshot con información detallada de penalidades, reembolsos, etc.
            },
        })
    timeline.sort(key=lambda x: x["changed_at"], reverse=True)
    return Response({"reservation_id": reservation.id, "timeline": timeline})

@api_view(['POST'])
def auto_mark_no_show(request):
    """
    Marca automáticamente las reservas confirmadas vencidas como no-show
    """
    from datetime import date
    from .models import ReservationStatusChange, ReservationStatus
    
    today = django_timezone.now().date()
    
    # Buscar reservas confirmadas con check-in pasado
    expired_reservations = Reservation.objects.filter(
        status=ReservationStatus.CONFIRMED,
        check_in__lt=today
    )
    
    updated_count = 0
    for reservation in expired_reservations:
        # Cambiar estado a no_show
        reservation.status = ReservationStatus.NO_SHOW
        reservation.save(update_fields=['status'])
        
        # Registrar el cambio de estado
        ReservationStatusChange.objects.create(
            reservation=reservation,
            from_status=ReservationStatus.CONFIRMED,
            to_status=ReservationStatus.NO_SHOW,
            changed_by=request.user if request.user.is_authenticated else None,
            notes='Auto no-show: check-in date passed'
        )
        
        updated_count += 1
    
    return Response({
        'message': f'Se marcaron {updated_count} reservas como no-show',
        'updated_count': updated_count,
        'date_checked': today.isoformat()
    })