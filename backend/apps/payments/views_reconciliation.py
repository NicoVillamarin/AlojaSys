"""
Vistas para Conciliación Bancaria
"""
import logging
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction, models
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import (
    BankReconciliation, BankTransaction, ReconciliationMatch, BankReconciliationLog,
    BankReconciliationConfig, ReconciliationStatus, MatchType
)
from .serializers_reconciliation import (
    BankReconciliationSerializer, BankReconciliationCreateSerializer,
    BankReconciliationUpdateSerializer, ReconciliationMatchSerializer,
    ReconciliationMatchUpdateSerializer, BankReconciliationConfigSerializer,
    BankReconciliationStatsSerializer, BankReconciliationSummarySerializer
)
from .services.bank_reconciliation import BankReconciliationService
from .tasks import process_bank_reconciliation, send_reconciliation_notifications

logger = logging.getLogger(__name__)


class BankReconciliationConfigViewSet(viewsets.ModelViewSet):
    """ViewSet para configuración de conciliación bancaria"""
    
    serializer_class = BankReconciliationConfigSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar por hotel del usuario"""
        hotel_id = self.request.query_params.get('hotel_id')
        if hotel_id:
            return BankReconciliationConfig.objects.filter(hotel_id=hotel_id)
        return BankReconciliationConfig.objects.all()
    
    @action(detail=False, methods=['get'])
    def by_hotel(self, request):
        """Obtener configuración por hotel"""
        hotel_id = request.query_params.get('hotel_id')
        if not hotel_id:
            return Response({'error': 'hotel_id requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        config = get_object_or_404(BankReconciliationConfig, hotel_id=hotel_id)
        serializer = self.get_serializer(config)
        return Response(serializer.data)


class BankReconciliationViewSet(viewsets.ModelViewSet):
    """ViewSet para conciliaciones bancarias"""
    
    serializer_class = BankReconciliationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar por hotel del usuario"""
        hotel_id = self.request.query_params.get('hotel_id')
        if hotel_id:
            return BankReconciliation.objects.filter(hotel_id=hotel_id)
        return BankReconciliation.objects.all()
    
    def get_serializer_class(self):
        """Usar serializer apropiado según la acción"""
        if self.action == 'create':
            return BankReconciliationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BankReconciliationUpdateSerializer
        return BankReconciliationSerializer
    
    def create(self, request, *args, **kwargs):
        """Crear nueva conciliación bancaria"""
        try:
            # Obtener hotel
            hotel_id = request.data.get('hotel')
            if not hotel_id:
                return Response({'error': 'hotel requerido'}, status=status.HTTP_400_BAD_REQUEST)
            
            from apps.core.models import Hotel
            hotel = get_object_or_404(Hotel, id=hotel_id)
            
            # Obtener datos del CSV
            csv_file_base64 = request.data.get('csv_file_base64')
            csv_filename = request.data.get('csv_filename')
            reconciliation_date = request.data.get('reconciliation_date')
            
            if not csv_file_base64:
                return Response({'error': 'csv_file_base64 requerido'}, status=status.HTTP_400_BAD_REQUEST)
            
            if not reconciliation_date:
                return Response({'error': 'reconciliation_date requerido'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Crear conciliación usando el servicio
            service = BankReconciliationService(hotel)
            reconciliation = service.create_reconciliation_from_base64(
                csv_file_base64=csv_file_base64,
                csv_filename=csv_filename,
                reconciliation_date=reconciliation_date,
                created_by=request.user
            )
            
            # Procesar conciliación en background
            process_bank_reconciliation.delay(reconciliation.id)
            
            # Retornar datos de la conciliación creada
            response_serializer = BankReconciliationSerializer(reconciliation)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creando conciliación: {str(e)}")
            return Response({'error': 'Error interno del servidor'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Procesar conciliación manualmente"""
        reconciliation = self.get_object()
        
        if reconciliation.status != ReconciliationStatus.PENDING:
            return Response(
                {'error': 'Solo se pueden procesar conciliaciones pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Procesar en background
            task = process_bank_reconciliation.delay(reconciliation.id)
            
            return Response({
                'message': 'Conciliación en procesamiento',
                'task_id': task.id
            })
            
        except Exception as e:
            logger.error(f"Error procesando conciliación {pk}: {str(e)}")
            return Response({'error': 'Error procesando conciliación'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Obtener transacciones de una conciliación"""
        reconciliation = self.get_object()
        transactions = reconciliation.transactions.all()
        
        # Aplicar filtros
        is_matched = request.query_params.get('is_matched')
        if is_matched is not None:
            transactions = transactions.filter(is_matched=is_matched.lower() == 'true')
        
        is_reversal = request.query_params.get('is_reversal')
        if is_reversal is not None:
            transactions = transactions.filter(is_reversal=is_reversal.lower() == 'true')
        
        # Paginación
        page = self.paginate_queryset(transactions)
        if page is not None:
            from .serializers_reconciliation import BankTransactionSerializer
            serializer = BankTransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        from .serializers_reconciliation import BankTransactionSerializer
        serializer = BankTransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def matches(self, request, pk=None):
        """Obtener matches de una conciliación"""
        reconciliation = self.get_object()
        matches = reconciliation.matches.all()
        
        # Aplicar filtros
        is_confirmed = request.query_params.get('is_confirmed')
        if is_confirmed is not None:
            matches = matches.filter(is_confirmed=is_confirmed.lower() == 'true')
        
        is_manual = request.query_params.get('is_manual')
        if is_manual is not None:
            matches = matches.filter(is_manual=is_manual.lower() == 'true')
        
        # Paginación
        page = self.paginate_queryset(matches)
        if page is not None:
            serializer = ReconciliationMatchSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ReconciliationMatchSerializer(matches, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def audit_logs(self, request, pk=None):
        """Obtener logs de auditoría de una conciliación"""
        reconciliation = self.get_object()
        logs = reconciliation.audit_logs.all()
        
        # Paginación
        page = self.paginate_queryset(logs)
        if page is not None:
            from .serializers_reconciliation import BankReconciliationLogSerializer
            serializer = BankReconciliationLogSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        from .serializers_reconciliation import BankReconciliationLogSerializer
        serializer = BankReconciliationLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Obtener estadísticas de conciliaciones"""
        hotel_id = request.query_params.get('hotel_id')
        if not hotel_id:
            return Response({'error': 'hotel_id requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        reconciliations = BankReconciliation.objects.filter(hotel_id=hotel_id)
        
        stats = {
            'total_reconciliations': reconciliations.count(),
            'pending_reconciliations': reconciliations.filter(status=ReconciliationStatus.PENDING).count(),
            'completed_reconciliations': reconciliations.filter(status=ReconciliationStatus.COMPLETED).count(),
            'failed_reconciliations': reconciliations.filter(status=ReconciliationStatus.FAILED).count(),
            'total_transactions': reconciliations.aggregate(
                total=models.Sum('total_transactions')
            )['total'] or 0,
            'matched_transactions': reconciliations.aggregate(
                total=models.Sum('matched_transactions')
            )['total'] or 0,
            'unmatched_transactions': reconciliations.aggregate(
                total=models.Sum('unmatched_transactions')
            )['total'] or 0,
            'pending_review_transactions': reconciliations.aggregate(
                total=models.Sum('pending_review_transactions')
            )['total'] or 0,
        }
        
        # Calcular porcentaje promedio de match
        completed_reconciliations = reconciliations.filter(status=ReconciliationStatus.COMPLETED)
        if completed_reconciliations.exists():
            total_percentage = sum(r.match_percentage for r in completed_reconciliations)
            stats['average_match_percentage'] = total_percentage / completed_reconciliations.count()
        else:
            stats['average_match_percentage'] = 0.0
        
        # Estadísticas por mes
        from datetime import datetime, timedelta
        now = timezone.now()
        this_month = now.replace(day=1)
        last_month = (this_month - timedelta(days=1)).replace(day=1)
        
        stats['reconciliations_this_month'] = reconciliations.filter(
            created_at__gte=this_month
        ).count()
        
        stats['reconciliations_last_month'] = reconciliations.filter(
            created_at__gte=last_month,
            created_at__lt=this_month
        ).count()
        
        serializer = BankReconciliationStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Obtener resumen de conciliaciones"""
        hotel_id = request.query_params.get('hotel_id')
        if not hotel_id:
            return Response({'error': 'hotel_id requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        reconciliations = BankReconciliation.objects.filter(hotel_id=hotel_id).select_related('hotel')
        
        # Aplicar filtros
        status_filter = request.query_params.get('status')
        if status_filter:
            reconciliations = reconciliations.filter(status=status_filter)
        
        # Ordenar por fecha de creación descendente
        reconciliations = reconciliations.order_by('-created_at')
        
        # Paginación
        page = self.paginate_queryset(reconciliations)
        if page is not None:
            serializer = BankReconciliationSummarySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = BankReconciliationSummarySerializer(reconciliations, many=True)
        return Response(serializer.data)


class ReconciliationMatchViewSet(viewsets.ModelViewSet):
    """ViewSet para matches de conciliación"""
    
    serializer_class = ReconciliationMatchSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar por conciliación"""
        reconciliation_id = self.request.query_params.get('reconciliation_id')
        if reconciliation_id:
            return ReconciliationMatch.objects.filter(reconciliation_id=reconciliation_id)
        return ReconciliationMatch.objects.all()
    
    def get_serializer_class(self):
        """Usar serializer apropiado según la acción"""
        if self.action in ['update', 'partial_update']:
            return ReconciliationMatchUpdateSerializer
        return ReconciliationMatchSerializer
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Aprobar un match manualmente"""
        match = self.get_object()
        
        if match.is_confirmed:
            return Response(
                {'error': 'El match ya está confirmado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Actualizar match
                match.is_confirmed = True
                match.is_manual = True
                match.manual_approved_by = request.user
                match.manual_approved_at = timezone.now()
                match.manual_notes = request.data.get('notes', '')
                match.save()
                
                # Actualizar transacción bancaria
                bank_transaction = match.bank_transaction
                bank_transaction.is_matched = True
                bank_transaction.match_confidence = match.confidence_score
                bank_transaction.match_type = MatchType.MANUAL
                bank_transaction.matched_payment_id = match.payment_id
                bank_transaction.matched_payment_type = match.payment_type
                bank_transaction.matched_reservation_id = match.reservation_id
                bank_transaction.save()
                
                # Confirmar el pago
                service = BankReconciliationService(match.reconciliation.hotel)
                service._confirm_payment(match.payment_id, match.payment_type)
                
                # Actualizar estadísticas de la conciliación
                reconciliation = match.reconciliation
                reconciliation.matched_transactions += 1
                reconciliation.pending_review_transactions -= 1
                reconciliation.save()
                
                # Log del evento
                service._log_event(
                    reconciliation,
                    'manual_matched',
                    f"Match aprobado manualmente: {bank_transaction.amount}",
                    created_by=request.user,
                    bank_transaction_id=bank_transaction.id,
                    payment_id=match.payment_id,
                    payment_type=match.payment_type,
                    reservation_id=match.reservation_id
                )
            
            return Response({'message': 'Match aprobado exitosamente'})
            
        except Exception as e:
            logger.error(f"Error aprobando match {pk}: {str(e)}")
            return Response({'error': 'Error aprobando match'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Rechazar un match"""
        match = self.get_object()
        
        if match.is_confirmed:
            return Response(
                {'error': 'No se puede rechazar un match confirmado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Eliminar match
                match.delete()
                
                # Actualizar transacción bancaria
                bank_transaction = match.bank_transaction
                bank_transaction.is_matched = False
                bank_transaction.match_confidence = None
                bank_transaction.match_type = None
                bank_transaction.matched_payment_id = None
                bank_transaction.matched_payment_type = None
                bank_transaction.matched_reservation_id = None
                bank_transaction.save()
                
                # Actualizar estadísticas de la conciliación
                reconciliation = match.reconciliation
                reconciliation.pending_review_transactions -= 1
                reconciliation.unmatched_transactions += 1
                reconciliation.save()
                
                # Log del evento
                service = BankReconciliationService(reconciliation.hotel)
                service._log_event(
                    reconciliation,
                    'unmatched',
                    f"Match rechazado: {bank_transaction.amount}",
                    created_by=request.user,
                    bank_transaction_id=bank_transaction.id
                )
            
            return Response({'message': 'Match rechazado exitosamente'})
            
        except Exception as e:
            logger.error(f"Error rechazando match {pk}: {str(e)}")
            return Response({'error': 'Error rechazando match'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
