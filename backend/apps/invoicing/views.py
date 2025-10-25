from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.http import FileResponse, Http404
from django.conf import settings
from decimal import Decimal
import requests
import logging
import os

from .models import AfipConfig, Invoice, InvoiceItem
from .serializers import (
    AfipConfigSerializer, InvoiceSerializer, InvoiceItemSerializer,
    CreateInvoiceFromReservationSerializer, SendInvoiceToAfipSerializer,
    RetryFailedInvoiceSerializer, CancelInvoiceSerializer,
    InvoiceSummarySerializer, AfipStatusSerializer,
    GenerateInvoiceFromPaymentSerializer, CreateCreditNoteSerializer
)
from .services import AfipService
from .services.invoice_pdf_service import InvoicePDFService

logger = logging.getLogger(__name__)


class AfipConfigViewSet(viewsets.ModelViewSet):
    """ViewSet para configuración AFIP"""
    queryset = AfipConfig.objects.all()
    serializer_class = AfipConfigSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        """Asignar el usuario actual al crear"""
        config = serializer.save()
        config._current_user = self.request.user
        config.save()
    
    def get_queryset(self):
        """Filtrar por hotel del usuario"""
        user = self.request.user
        
        # Si es superusuario, puede ver todas las configuraciones
        if user.is_superuser:
            return AfipConfig.objects.all()
        
        # Si tiene perfil y hoteles asociados, filtrar por sus hoteles
        if hasattr(user, 'profile') and user.profile.hotels.exists():
            return AfipConfig.objects.filter(
                hotel__in=user.profile.hotels.all()
            )
        
        # Si no tiene hoteles asociados, no mostrar nada
        return AfipConfig.objects.none()
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Probar conexión con AFIP"""
        config = self.get_object()
        try:
            afip_service = AfipService(config)
            result = afip_service.test_connection()
            return Response({
                'success': result.get('success', False),
                'message': result.get('message', 'Error de conexión'),
                'environment': result.get('environment', 'unknown'),
                'has_token': result.get('has_token', False),
                'has_sign': result.get('has_sign', False)
            })
        except Exception as e:
            logger.error(f"Error probando conexión AFIP: {e}")
            return Response({
                'success': False,
                'message': f'Error: {str(e)}',
                'environment': 'unknown',
                'has_token': False,
                'has_sign': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InvoiceViewSet(viewsets.ModelViewSet):
    """ViewSet para facturas"""
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar por hoteles asignados o por creador cuando no hay asignación"""
        user = self.request.user
        base_qs = Invoice.objects.select_related('hotel', 'reservation', 'payment').prefetch_related('items')
        # Superusuarios ven todo
        if getattr(user, 'is_superuser', False):
            return base_qs
        # Si el usuario tiene hoteles asignados, filtrar por esos hoteles
        if hasattr(user, 'profile') and user.profile.hotels.exists():
            return base_qs.filter(hotel__in=user.profile.hotels.all())
        # Si no tiene hoteles asignados, mostrar facturas creadas por él
        return base_qs.filter(created_by=user)
    
    @action(detail=True, methods=['post'])
    def send_to_afip(self, request, pk=None):
        """Enviar factura a AFIP"""
        invoice = self.get_object()
        serializer = SendInvoiceToAfipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            if not invoice.can_be_resent() and not serializer.validated_data.get('force_send'):
                return Response({
                    'error': 'La factura no puede ser reenviada',
                    'reason': 'Ya fue enviada o excedió el límite de reintentos'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obtener configuración AFIP del hotel
            try:
                afip_config = invoice.hotel.afip_config
            except Exception:
                afip_config = None
            if not afip_config:
                return Response({
                    'error': 'El hotel no tiene configuración AFIP'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Si viene force_send y la factura no está en draft, pasar a draft para cumplir validación del servicio
            # (AfipInvoiceService._validate_invoice exige estado 'draft')
            if serializer.validated_data.get('force_send') and invoice.status != 'draft':
                invoice.status = 'draft'
                invoice.save(update_fields=['status', 'updated_at'])
            
            # Enviar a AFIP
            afip_service = AfipService(afip_config)
            result = afip_service.send_invoice(invoice)
            
            if result['success']:
                invoice.mark_as_approved(result['cae'], result['cae_expiration'])
                return Response({
                    'message': 'Factura enviada exitosamente a AFIP',
                    'cae': result['cae'],
                    'cae_expiration': result['cae_expiration']
                })
            else:
                invoice.mark_as_error(result['error'])
                return Response({
                    'error': 'Error enviando factura a AFIP',
                    'details': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error enviando factura a AFIP: {e}")
            invoice.mark_as_error(str(e))
            return Response({
                'error': 'Error interno enviando factura a AFIP',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        """Obtener PDF de la factura"""
        invoice = self.get_object()
        
        try:
            # Permitir regenerar forzadamente con ?refresh=1
            refresh = request.query_params.get('refresh') in ['1', 'true', 'True']

            if refresh or (not invoice.pdf_file and not invoice.pdf_url):
                # Generar/regenerar PDF
                pdf_service = InvoicePDFService()
                pdf_path = pdf_service.generate_pdf(invoice)
                invoice.pdf_file = pdf_path
                invoice.save(update_fields=['pdf_file'])
            
            # Si hay archivo PDF, servirlo directamente
            if invoice.pdf_file:
                file_path = os.path.join(settings.MEDIA_ROOT, str(invoice.pdf_file))
                if os.path.exists(file_path):
                    response = FileResponse(
                        open(file_path, 'rb'),
                        content_type='application/pdf',
                        filename=f'factura_{invoice.number}.pdf'
                    )
                    # Permitir que se muestre en iframe
                    response['X-Frame-Options'] = 'SAMEORIGIN'
                    return response
            
            # Si hay URL externa, devolverla
            pdf_url = invoice.get_pdf_url()
            if pdf_url:
                return Response({'pdf_url': pdf_url})
            else:
                return Response({
                    'error': 'No se pudo generar el PDF de la factura'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error generando PDF: {e}")
            return Response({
                'error': 'Error generando PDF',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Reintentar factura fallida"""
        invoice = self.get_object()
        serializer = RetryFailedInvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if not invoice.can_be_resent():
            return Response({
                'error': 'La factura no puede ser reintentada',
                'reason': 'Ya fue enviada exitosamente o excedió el límite de reintentos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Resetear estado a draft para reintentar
        invoice.status = 'draft'
        invoice.last_error = serializer.validated_data.get('reason', '')
        invoice.save(update_fields=['status', 'last_error'])
        
        return Response({'message': 'Factura marcada para reintento'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancelar factura"""
        invoice = self.get_object()
        serializer = CancelInvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if invoice.status in ['approved', 'sent']:
            return Response({
                'error': 'No se puede cancelar una factura ya enviada o aprobada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        invoice.status = 'cancelled'
        invoice.last_error = serializer.validated_data['reason']
        invoice.save(update_fields=['status', 'last_error'])
        
        return Response({'message': 'Factura cancelada exitosamente'})
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Obtener resumen de la factura"""
        invoice = self.get_object()
        
        summary = {
            'id': invoice.id,
            'number': invoice.number,
            'type': invoice.type,
            'status': invoice.status,
            'total': invoice.total,
            'vat_amount': invoice.vat_amount,
            'net_amount': invoice.net_amount,
            'cae': invoice.cae,
            'cae_expiration': invoice.cae_expiration,
            'is_approved': invoice.is_approved(),
            'is_expired': invoice.is_expired(),
            'can_be_resent': invoice.can_be_resent(),
            'items_count': invoice.items.count(),
            'created_at': invoice.created_at,
            'approved_at': invoice.approved_at
        }
        
        return Response(summary)
    
    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Descargar PDF de la factura"""
        invoice = self.get_object()
        
        try:
            if not invoice.pdf_file and not invoice.pdf_url:
                # Generar PDF si no existe
                generator = InvoiceGeneratorService()
                pdf_path = generator.generate_pdf(invoice)
                invoice.pdf_file = pdf_path
                invoice.save(update_fields=['pdf_file'])
            
            # Obtener ruta del archivo
            if invoice.pdf_file:
                file_path = os.path.join(settings.MEDIA_ROOT, str(invoice.pdf_file))
                if os.path.exists(file_path):
                    response = FileResponse(
                        open(file_path, 'rb'),
                        content_type='application/pdf',
                        as_attachment=True,
                        filename=f'factura_{invoice.number}.pdf'
                    )
                    return response
            
            return Response({
                'error': 'PDF no disponible'
            }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.error(f"Error descargando PDF: {e}")
            return Response({
                'error': 'Error descargando PDF',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def create_credit_note(self, request, pk=None):
        """Crear nota de crédito vinculada a esta factura"""
        invoice = self.get_object()
        serializer = CreateCreditNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                # Verificar que la factura esté aprobada
                if invoice.status != 'approved':
                    return Response({
                        'error': 'Solo se pueden crear notas de crédito para facturas aprobadas'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Obtener configuración AFIP
                try:
                    afip_config = invoice.hotel.afip_config
                except Exception:
                    afip_config = None
                if not afip_config:
                    return Response({
                        'error': 'El hotel no tiene configuración AFIP'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Generar número de nota de crédito
                next_number = afip_config.get_next_invoice_number()
                formatted_number = afip_config.format_invoice_number(next_number)
                
                # Crear nota de crédito
                credit_note_data = {
                    'reservation': invoice.reservation,
                    'payment': invoice.payment,
                    'hotel': invoice.hotel,
                    'type': 'NC',  # Nota de Crédito
                    'number': formatted_number,
                    'issue_date': serializer.validated_data.get('issue_date', timezone.now().date()),
                    'total': serializer.validated_data['total'],
                    'net_amount': serializer.validated_data['net_amount'],
                    'vat_amount': serializer.validated_data['vat_amount'],
                    'currency': invoice.currency,
                    'customer_name': invoice.customer_name,
                    'customer_document_type': invoice.customer_document_type,
                    'customer_document_number': invoice.customer_document_number,
                    'customer_address': invoice.customer_address,
                    'customer_city': invoice.customer_city,
                    'customer_postal_code': invoice.customer_postal_code,
                    'customer_country': invoice.customer_country,
                    'status': 'draft',
                    'created_by': request.user,
                    'related_invoice': invoice  # Vincular con la factura original
                }
                
                credit_note = Invoice.objects.create(**credit_note_data)
                
                # Crear items de la nota de crédito
                items_data = serializer.validated_data.get('items', [])
                for item_data in items_data:
                    item_data['invoice'] = credit_note
                    InvoiceItem.objects.create(**item_data)
                
                # Actualizar número en configuración
                afip_config.update_invoice_number(next_number)
                
                # Serializar respuesta
                credit_note_serializer = InvoiceSerializer(credit_note)
                return Response(credit_note_serializer.data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Error creando nota de crédito: {e}")
            return Response({
                'error': 'Error interno creando nota de crédito',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InvoiceItemViewSet(viewsets.ModelViewSet):
    """ViewSet para items de factura"""
    queryset = InvoiceItem.objects.all()
    serializer_class = InvoiceItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar por facturas del usuario"""
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.hotels.exists():
            return InvoiceItem.objects.filter(
                invoice__hotel__in=user.profile.hotels.all()
            ).select_related('invoice')
        return InvoiceItem.objects.none()


# Vistas de acciones específicas

class GenerateInvoiceFromPaymentView(APIView):
    """Generar factura automáticamente desde un pago aprobado con soporte para múltiples pagos"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, payment_id):
        serializer = GenerateInvoiceFromPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                # Obtener pago principal
                from apps.reservations.models import Payment
                payment = get_object_or_404(Payment, id=payment_id)
                
                # Verificar que el pago esté aprobado
                if payment.status != 'approved':
                    return Response({
                        'error': 'Solo se pueden generar facturas para pagos aprobados'
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
                reservation_ids = set(p.reservation_id for p in payments)
                if len(reservation_ids) > 1:
                    return Response({
                        'error': 'Todos los pagos deben pertenecer a la misma reserva'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Verificar que no exista ya una factura para estos pagos
                existing_invoices = Invoice.objects.filter(
                    Q(payment__in=payments) | Q(payments_data__overlap=reference_payments)
                )
                if existing_invoices.exists():
                    return Response({
                        'error': 'Ya existe una factura para uno o más de estos pagos'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Obtener configuración AFIP
                try:
                    afip_config = payment.reservation.hotel.afip_config
                except Exception:
                    afip_config = None
                if not afip_config:
                    return Response({
                        'error': 'El hotel no tiene configuración AFIP'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Calcular total de todos los pagos
                total_amount = sum(p.amount for p in payments)
                
                # Generar número de factura
                next_number = afip_config.get_next_invoice_number()
                formatted_number = afip_config.format_invoice_number(next_number)
                
                # Determinar tipo de factura basado en el cliente
                invoice_type = self._determine_invoice_type(payment)
                
                # Obtener datos del cliente
                customer_data = {
                    'customer_name': serializer.validated_data.get('customer_name', payment.reservation.guest_name or 'Cliente'),
                    'customer_document_type': serializer.validated_data.get('customer_document_type', 'DNI'),
                    'customer_document_number': serializer.validated_data.get('customer_document_number', '00000000'),
                    'customer_address': serializer.validated_data.get('customer_address', ''),
                    'customer_city': serializer.validated_data.get('customer_city', ''),
                    'customer_postal_code': serializer.validated_data.get('customer_postal_code', ''),
                    'customer_country': serializer.validated_data.get('customer_country', 'Argentina'),
                }
                
                # Crear factura
                invoice_data = {
                    'reservation': payment.reservation,
                    'payment': payment,  # Pago principal para compatibilidad
                    'payments_data': reference_payments,  # Lista de IDs de pagos
                    'hotel': payment.reservation.hotel,
                    'type': invoice_type,
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
                
                try:
                    invoice = Invoice.objects.create(**invoice_data)
                except IntegrityError:
                    # Reintentar una vez más incrementando el número
                    next_number += 1
                    formatted_number = afip_config.format_invoice_number(next_number)
                    invoice_data['number'] = formatted_number
                    invoice = Invoice.objects.create(**invoice_data)
                
                # Crear items de la factura
                items_data = serializer.validated_data.get('items', [])
                if not items_data:
                    # Crear item por defecto basado en la reserva
                    if len(payments) > 1:
                        description = f'Hospedaje - {payment.reservation.room.name} (Incluye señas y pago final)'
                    else:
                        description = f'Hospedaje - {payment.reservation.room.name}'
                    
                    items_data = [{
                        'description': description,
                        'quantity': (payment.reservation.check_out - payment.reservation.check_in).days,
                        'unit_price': payment.reservation.room.base_price,
                        'vat_rate': Decimal('21.00'),
                        'afip_code': '1'  # Servicios
                    }]
                
                for item_data in items_data:
                    item_data['invoice'] = invoice
                    InvoiceItem.objects.create(**item_data)
                
                # Actualizar número en configuración
                afip_config.update_invoice_number(next_number)
                
                # Si se solicita envío automático a AFIP
                if serializer.validated_data.get('send_to_afip', False):
                    try:
                        afip_service = AfipService(afip_config)
                        result = afip_service.send_invoice(invoice)
                        
                        if result['success']:
                            invoice.mark_as_approved(result['cae'], result['cae_expiration'])
                        else:
                            invoice.mark_as_error(result['error'])
                    except Exception as e:
                        logger.error(f"Error enviando factura a AFIP: {e}")
                        invoice.mark_as_error(str(e))
                
                # Serializar respuesta
                invoice_serializer = InvoiceSerializer(invoice)
                response_data = invoice_serializer.data
                response_data['payments_included'] = reference_payments
                response_data['total_payments'] = len(reference_payments)
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Error generando factura desde pago: {e}")
            return Response({
                'error': 'Error interno generando factura',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _determine_invoice_type(self, payment):
        """Determina el tipo de factura basado en el pago"""
        # Lógica para determinar tipo de factura
        # Por defecto, usar Factura B para consumidores finales
        return 'B'


class InvoicesByReservationView(APIView):
    """Listar facturas por reserva"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, reservation_id):
        try:
            # Obtener reserva
            from apps.reservations.models import Reservation
            reservation = get_object_or_404(Reservation, id=reservation_id)
            
            # Verificar permisos
            user = request.user
            # Superusuarios siempre permitidos
            if not getattr(user, 'is_superuser', False):
                # Solo restringir si el usuario tiene hoteles asignados
                if hasattr(user, 'profile') and user.profile.hotels.exists():
                    if reservation.hotel not in user.profile.hotels.all():
                        return Response({
                            'error': 'No tiene permisos para ver esta reserva'
                        }, status=status.HTTP_403_FORBIDDEN)
            
            # Obtener facturas de la reserva
            invoices = Invoice.objects.filter(
                reservation=reservation
            ).select_related('hotel', 'payment').prefetch_related('items')
            
            # Aplicar filtros
            invoice_type = request.query_params.get('type')
            if invoice_type:
                invoices = invoices.filter(type=invoice_type)
            
            status_filter = request.query_params.get('status')
            if status_filter:
                invoices = invoices.filter(status=status_filter)
            
            # Serializar respuesta
            serializer = InvoiceSerializer(invoices, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error obteniendo facturas por reserva: {e}")
            return Response({
                'error': 'Error interno obteniendo facturas',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateInvoiceFromReservationView(APIView):
    """Crear factura desde una reserva"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CreateInvoiceFromReservationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Obtener reserva
                from apps.reservations.models import Reservation
                reservation = Reservation.objects.get(id=serializer.validated_data['reservation_id'])
                
                # Evitar duplicar facturas por reserva
                if Invoice.objects.filter(reservation=reservation).exists():
                    return Response({
                        'error': 'Ya existe una factura para esta reserva'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Obtener configuración AFIP
                # afip_config es una relación one-to-one, no un QuerySet
                try:
                    afip_config = reservation.hotel.afip_config
                    if not afip_config:
                        return Response({
                            'error': 'El hotel no tiene configuración AFIP'
                        }, status=status.HTTP_400_BAD_REQUEST)
                except:
                    return Response({
                        'error': 'El hotel no tiene configuración AFIP'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Generar número de factura evitando duplicados
                next_number = afip_config.get_next_invoice_number()
                formatted_number = afip_config.format_invoice_number(next_number)
                attempts = 0
                while Invoice.objects.filter(hotel=reservation.hotel, number=formatted_number).exists() and attempts < 20:
                    next_number += 1
                    formatted_number = afip_config.format_invoice_number(next_number)
                    attempts += 1
                
                # Crear factura
                invoice_data = {
                    'reservation': reservation,
                    'hotel': reservation.hotel,
                    'type': serializer.validated_data['invoice_type'],
                    'number': formatted_number,
                    'issue_date': serializer.validated_data.get('issue_date', timezone.now().date()),
                    'total': reservation.total_price,
                    'net_amount': reservation.total_price * Decimal('0.83'),  # Aproximado sin IVA
                    'vat_amount': reservation.total_price * Decimal('0.17'),  # Aproximado con IVA
                    'currency': 'ARS',
                    'client_name': serializer.validated_data['client_name'],
                    'client_document_type': serializer.validated_data['client_document_type'],
                    'client_document_number': serializer.validated_data['client_document_number'],
                    'client_tax_condition': serializer.validated_data['client_tax_condition'],
                    'client_address': serializer.validated_data.get('client_address', ''),
                    'created_by': request.user
                }
                
                invoice = Invoice.objects.create(**invoice_data)
                
                # Crear items si se proporcionaron
                items_data = serializer.validated_data.get('items', [])
                if not items_data:
                    # Crear item por defecto basado en la reserva
                    items_data = [{
                        'description': f'Hospedaje - {reservation.room.name}',
                        'quantity': (reservation.check_out - reservation.check_in).days,
                        'unit_price': reservation.room.base_price,
                        'vat_rate': Decimal('21.00'),
                        'afip_code': '1'  # Servicios
                    }]
                
                for item_data in items_data:
                    item_data['invoice'] = invoice
                    InvoiceItem.objects.create(**item_data)
                
                # Actualizar número de factura en configuración al último usado
                afip_config.update_invoice_number(next_number)
                
                # Serializar respuesta
                invoice_serializer = InvoiceSerializer(invoice)
                return Response(invoice_serializer.data, status=status.HTTP_201_CREATED)
                
        except Reservation.DoesNotExist:
            return Response({
                'error': 'La reserva no existe'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error creando factura desde reserva: {e}")
            return Response({
                'error': 'Error interno creando factura',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def send_invoice_to_afip(request, invoice_id):
    """Enviar factura específica a AFIP"""
    # Esta funcionalidad ya está implementada en el ViewSet
    pass


def get_invoice_pdf(request, invoice_id):
    """Obtener PDF de factura específica"""
    # Esta funcionalidad ya está implementada en el ViewSet
    pass


def get_invoice_status(request, invoice_id):
    """Obtener estado de factura específica"""
    # Esta funcionalidad ya está implementada en el ViewSet
    pass


def retry_failed_invoice(request, invoice_id):
    """Reintentar factura fallida específica"""
    # Esta funcionalidad ya está implementada en el ViewSet
    pass


def cancel_invoice(request, invoice_id):
    """Cancelar factura específica"""
    # Esta funcionalidad ya está implementada en el ViewSet
    pass


def get_invoice_summary(request, invoice_id):
    """Obtener resumen de factura específica"""
    # Esta funcionalidad ya está implementada en el ViewSet
    pass


def get_afip_status(request):
    """Obtener estado general de AFIP"""
    try:
        # Obtener configuración AFIP del usuario
        user = request.user
        if not hasattr(user, 'profile') or not user.profile.hotels.exists():
            return Response({
                'error': 'Usuario sin hoteles asignados'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        afip_configs = AfipConfig.objects.filter(
            hotel__in=user.profile.hotels.all(),
            is_active=True
        )
        
        if not afip_configs.exists():
            return Response({
                'error': 'No hay configuraciones AFIP activas'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Probar conexión con la primera configuración
        afip_config = afip_configs.first()
        afip_service = AfipService(afip_config)
        
        is_available = afip_service.test_connection()
        
        status_data = {
            'is_available': is_available,
            'last_connection': timezone.now(),
            'environment': afip_config.environment,
            'service_status': 'available' if is_available else 'unavailable',
            'last_error': None if is_available else 'Error de conexión'
        }
        
        serializer = AfipStatusSerializer(status_data)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error obteniendo estado AFIP: {e}")
        return Response({
            'error': 'Error interno obteniendo estado AFIP',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# VISTAS DE PRUEBA PARA CERTIFICADOS AFIP
# =============================================================================

class TestCertificateValidationView(APIView):
    """
    Endpoint para validar certificados AFIP
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Valida que los certificados estén disponibles y sean válidos"""
        try:
            # Obtener configuración AFIP del hotel
            hotel = request.user.hotel if hasattr(request.user, 'hotel') else None
            if not hotel:
                return Response({
                    'error': 'Usuario no tiene hotel asociado'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                afip_config = hotel.afip_config
            except AfipConfig.DoesNotExist:
                return Response({
                    'error': 'No hay configuración AFIP para este hotel'
                }, status=status.HTTP_404_NOT_FOUND)

            # Validar certificados
            validation_result = self.validate_certificates(afip_config)
            
            return Response({
                'hotel': hotel.name,
                'afip_config': {
                    'cuit': afip_config.cuit,
                    'point_of_sale': afip_config.point_of_sale,
                    'environment': afip_config.environment,
                    'is_active': afip_config.is_active,
                },
                'certificates': validation_result
            })

        except Exception as e:
            logger.error(f"Error validando certificados: {str(e)}")
            return Response({
                'error': f'Error validando certificados: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def validate_certificates(self, afip_config):
        """Valida que los certificados existan y sean válidos"""
        result = {
            'certificate': {
                'path': afip_config.certificate_path,
                'exists': False,
                'valid': False,
                'valid_from': None,
                'valid_to': None,
                'error': None
            },
            'private_key': {
                'path': afip_config.private_key_path,
                'exists': False,
                'valid': False,
                'error': None
            },
            'pair_match': False
        }

        # Validar certificado
        try:
            if os.path.exists(afip_config.certificate_path):
                result['certificate']['exists'] = True
                # Intentar cargar el certificado
                from cryptography import x509
                from cryptography.hazmat.primitives import serialization
                with open(afip_config.certificate_path, 'rb') as f:
                    cert_data = f.read()
                cert = x509.load_pem_x509_certificate(cert_data)
                result['certificate']['valid'] = True
                try:
                    result['certificate']['valid_from'] = cert.not_valid_before.isoformat()
                    result['certificate']['valid_to'] = cert.not_valid_after.isoformat()
                except Exception:
                    pass
            else:
                result['certificate']['error'] = 'Archivo no encontrado'
        except Exception as e:
            result['certificate']['error'] = str(e)

        # Validar clave privada
        try:
            if os.path.exists(afip_config.private_key_path):
                result['private_key']['exists'] = True
                # Intentar cargar la clave privada
                from cryptography.hazmat.primitives import serialization
                with open(afip_config.private_key_path, 'rb') as f:
                    key_data = f.read()
                private_key = serialization.load_pem_private_key(key_data, password=None)
                result['private_key']['valid'] = True
            else:
                result['private_key']['error'] = 'Archivo no encontrado'
        except Exception as e:
            result['private_key']['error'] = str(e)

        # Verificar que el par certificado/clave coinciden (mismo público)
        try:
            if result['certificate']['valid'] and result['private_key']['valid']:
                from cryptography.hazmat.primitives.asymmetric import rsa
                public_from_cert = cert.public_key()
                public_from_key = private_key.public_key()
                # Comparar parámetros públicos
                if hasattr(public_from_cert, 'public_numbers') and hasattr(public_from_key, 'public_numbers'):
                    result['pair_match'] = public_from_cert.public_numbers() == public_from_key.public_numbers()
        except Exception:
            result['pair_match'] = False

        return result


class TestAfipConnectionView(APIView):
    """
    Endpoint para probar la conexión con AFIP
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Prueba la conexión con AFIP usando los certificados"""
        try:
            # Obtener configuración AFIP del hotel
            hotel = request.user.hotel if hasattr(request.user, 'hotel') else None
            if not hotel:
                return Response({
                    'error': 'Usuario no tiene hotel asociado'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                afip_config = hotel.afip_config
            except AfipConfig.DoesNotExist:
                return Response({
                    'error': 'No hay configuración AFIP para este hotel'
                }, status=status.HTTP_404_NOT_FOUND)

            # Crear servicio de prueba
            from .services.afip_test_service import AfipTestService
            from .services.invoice_pdf_service import InvoicePDFService
            test_service = AfipTestService(afip_config)
            
            # Probar conexión
            connection_result = test_service.test_connection()
            
            return Response({
                'hotel': hotel.name,
                'afip_config': {
                    'cuit': afip_config.cuit,
                    'point_of_sale': afip_config.point_of_sale,
                    'environment': afip_config.environment,
                },
                'connection_test': connection_result
            })

        except Exception as e:
            logger.error(f"Error probando conexión AFIP: {str(e)}")
            return Response({
                'error': f'Error probando conexión: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AfipDiagnosticsView(APIView):
    """
    Diagnóstico integral de conexión AFIP (WSAA + archivos + red + firma local)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            hotel = request.user.hotel if hasattr(request.user, 'hotel') else None
            if not hotel:
                return Response({'error': 'Usuario no tiene hotel asociado'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                afip_config = hotel.afip_config
            except AfipConfig.DoesNotExist:
                return Response({'error': 'No hay configuración AFIP para este hotel'}, status=status.HTTP_404_NOT_FOUND)

            # 1) Datos de certificados
            cert_validator = TestCertificateValidationView()
            certs = cert_validator.validate_certificates(afip_config)

            # 2) WSAA URL según ambiente y chequeo WSDL
            from .services.afip_auth_service import AfipAuthService
            auth = AfipAuthService(afip_config)
            wsaa_wsdl_url = f"{auth.wsaa_url}?wsdl"
            wsdl_status = {
                'url': wsaa_wsdl_url,
                'reachable': False,
                'http_status': None,
                'error': None
            }
            try:
                r = requests.get(wsaa_wsdl_url, timeout=12)
                wsdl_status['http_status'] = r.status_code
                wsdl_status['reachable'] = r.ok and r.text.strip().startswith('<?xml')
            except Exception as e:
                wsdl_status['error'] = str(e)

            # 3) Prueba local de firma (sin red)
            sign_test = {
                'ok': False,
                'error': None
            }
            try:
                login_xml = auth._create_login_xml()
                _ = auth._sign_xml(login_xml)
                sign_test['ok'] = True
            except Exception as e:
                sign_test['error'] = str(e)

            # 4) Hora del servidor
            server_time = timezone.now().isoformat()

            return Response({
                'environment': afip_config.environment,
                'wsaa_url': auth.wsaa_url,
                'certificates': certs,
                'wsdl': wsdl_status,
                'sign_test': sign_test,
                'server_time': server_time
            })

        except Exception as e:
            logger.error(f"Error en diagnóstico AFIP: {e}")
            return Response({'error': f'Error en diagnóstico: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TestInvoiceGenerationView(APIView):
    """
    Endpoint para probar la generación de facturas de prueba
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Genera una factura de prueba"""
        try:
            # Obtener configuración AFIP del hotel
            hotel = request.user.hotel if hasattr(request.user, 'hotel') else None
            if not hotel:
                return Response({
                    'error': 'Usuario no tiene hotel asociado'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                afip_config = hotel.afip_config
            except AfipConfig.DoesNotExist:
                return Response({
                    'error': 'No hay configuración AFIP para este hotel'
                }, status=status.HTTP_404_NOT_FOUND)

            # Datos de prueba
            test_data = request.data.get('test_data', {
                'customer_name': 'Cliente de Prueba',
                'customer_document_type': 'DNI',
                'customer_document_number': '12345678',
                'customer_address': 'Av. Test 123',
                'customer_city': 'Buenos Aires',
                'items': [
                    {
                        'description': 'Servicio de Hospedaje - Habitación Test',
                        'quantity': 1,
                        'unit_price': 1000.00,
                        'vat_rate': 21.00,
                        'afip_code': '1'
                    }
                ]
            })

            # Crear servicio de prueba
            from .services.afip_test_service import AfipTestService
            from .services.invoice_pdf_service import InvoicePDFService
            test_service = AfipTestService(afip_config)
            
            # Generar factura de prueba
            invoice_result = test_service.generate_test_invoice(test_data)
            
            return Response({
                'hotel': hotel.name,
                'test_invoice': invoice_result
            })

        except Exception as e:
            logger.error(f"Error generando factura de prueba: {str(e)}")
            return Response({
                'error': f'Error generando factura de prueba: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TestAfipStatusView(APIView):
    """
    Endpoint para obtener el estado general de AFIP
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Obtiene el estado general de la configuración AFIP"""
        try:
            # Obtener configuración AFIP del hotel
            hotel = request.user.hotel if hasattr(request.user, 'hotel') else None
            if not hotel:
                return Response({
                    'error': 'Usuario no tiene hotel asociado'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                afip_config = hotel.afip_config
            except AfipConfig.DoesNotExist:
                return Response({
                    'status': 'not_configured',
                    'message': 'No hay configuración AFIP para este hotel',
                    'hotel': hotel.name
                })

            # Validar certificados
            cert_validation = self.validate_certificates(afip_config)
            
            # Determinar estado
            if not cert_validation['certificate']['exists'] or not cert_validation['private_key']['exists']:
                status_code = 'certificates_missing'
                message = 'Certificados no encontrados'
            elif not cert_validation['certificate']['valid'] or not cert_validation['private_key']['valid']:
                status_code = 'certificates_invalid'
                message = 'Certificados inválidos'
            else:
                status_code = 'ready'
                message = 'Configuración AFIP lista'

            return Response({
                'status': status_code,
                'message': message,
                'hotel': hotel.name,
                'afip_config': {
                    'cuit': afip_config.cuit,
                    'point_of_sale': afip_config.point_of_sale,
                    'environment': afip_config.environment,
                    'is_active': afip_config.is_active,
                    'last_invoice_number': afip_config.last_invoice_number,
                },
                'certificates': cert_validation
            })

        except Exception as e:
            logger.error(f"Error obteniendo estado AFIP: {str(e)}")
            return Response({
                'error': f'Error obteniendo estado: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def validate_certificates(self, afip_config):
        """Valida que los certificados existan y sean válidos"""
        result = {
            'certificate': {
                'path': afip_config.certificate_path,
                'exists': False,
                'valid': False,
                'error': None
            },
            'private_key': {
                'path': afip_config.private_key_path,
                'exists': False,
                'valid': False,
                'error': None
            }
        }

        # Validar certificado
        try:
            if os.path.exists(afip_config.certificate_path):
                result['certificate']['exists'] = True
                with open(afip_config.certificate_path, 'rb') as f:
                    cert_data = f.read()
                result['certificate']['valid'] = True
            else:
                result['certificate']['error'] = 'Archivo no encontrado'
        except Exception as e:
            result['certificate']['error'] = str(e)

        # Validar clave privada
        try:
            if os.path.exists(afip_config.private_key_path):
                result['private_key']['exists'] = True
                with open(afip_config.private_key_path, 'rb') as f:
                    key_data = f.read()
                result['private_key']['valid'] = True
            else:
                result['private_key']['error'] = 'Archivo no encontrado'
        except Exception as e:
            result['private_key']['error'] = str(e)

        return result


class ListCertificatesView(APIView):
    """Vista para listar certificados disponibles en el servidor"""
    
    def get(self, request):
        try:
            import os
            import glob
            
            # Directorio de certificados
            certs_dir = '/app/certs'
            
            if not os.path.exists(certs_dir):
                return Response({
                    'success': False,
                    'error': 'Directorio de certificados no encontrado',
                    'certificates': []
                })
            
            # Buscar archivos de certificados y claves
            cert_files = []
            key_files = []
            
            # Buscar archivos .crt y .pem (certificados)
            for pattern in ['*.crt', '*.pem']:
                cert_files.extend(glob.glob(os.path.join(certs_dir, pattern)))
            
            # Buscar archivos .key (claves privadas)
            key_files.extend(glob.glob(os.path.join(certs_dir, '*.key')))
            
            # Procesar archivos encontrados
            certificates = []
            
            for cert_file in cert_files:
                try:
                    stat = os.stat(cert_file)
                    certificates.append({
                        'path': cert_file,
                        'filename': os.path.basename(cert_file),
                        'type': 'certificate',
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'exists': True
                    })
                except Exception as e:
                    certificates.append({
                        'path': cert_file,
                        'filename': os.path.basename(cert_file),
                        'type': 'certificate',
                        'error': str(e),
                        'exists': False
                    })
            
            for key_file in key_files:
                try:
                    stat = os.stat(key_file)
                    certificates.append({
                        'path': key_file,
                        'filename': os.path.basename(key_file),
                        'type': 'private_key',
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'exists': True
                    })
                except Exception as e:
                    certificates.append({
                        'path': key_file,
                        'filename': os.path.basename(key_file),
                        'type': 'private_key',
                        'error': str(e),
                        'exists': False
                    })
            
            # Ordenar por nombre
            certificates.sort(key=lambda x: x['filename'])
            
            return Response({
                'success': True,
                'certificates': certificates,
                'total': len(certificates),
                'directory': certs_dir
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e),
                'certificates': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TestPDFGenerationView(APIView):
    """
    Vista para probar la generación de PDFs de facturas.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Genera PDF de prueba para una factura"""
        try:
            # Obtener configuración AFIP
            afip_config = AfipConfig.objects.filter(
                hotel__enterprise__users=request.user
            ).first()
            
            if not afip_config:
                return Response({
                    'success': False,
                    'error': 'No se encontró configuración AFIP'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Crear factura de prueba
            from apps.core.models import Hotel
            from apps.reservations.models import Reservation
            from decimal import Decimal
            from datetime import date
            
            hotel = afip_config.hotel
            
            # Crear factura de prueba
            test_invoice = Invoice.objects.create(
                hotel=hotel,
                type='B',
                number='0001-00000001',
                issue_date=date.today(),
                total=Decimal('1210.00'),
                vat_amount=Decimal('210.00'),
                net_amount=Decimal('1000.00'),
                currency='ARS',
                status='approved',
                cae='12345678901234',
                cae_expiration=date.today().replace(month=12, day=31),
                client_name='Cliente de Prueba',
                client_document_type='96',
                client_document_number='12345678',
                client_tax_condition='5',
                client_address='Dirección de Prueba 123',
                created_by=request.user
            )
            
            # Crear items de prueba
            InvoiceItem.objects.create(
                invoice=test_invoice,
                description='Hospedaje - 2 noches',
                quantity=Decimal('2.00'),
                unit_price=Decimal('500.00'),
                subtotal=Decimal('1000.00'),
                vat_rate=Decimal('21.00'),
                vat_amount=Decimal('210.00'),
                total=Decimal('1210.00'),
                afip_code='1'
            )
            
            # Generar PDF
            pdf_service = InvoicePDFService()
            pdf_path = pdf_service.generate_pdf(test_invoice)
            
            return Response({
                'success': True,
                'message': 'PDF generado exitosamente',
                'invoice_id': str(test_invoice.id),
                'pdf_path': pdf_path,
                'pdf_url': test_invoice.pdf_file.url if test_invoice.pdf_file else None
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error generando PDF: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
