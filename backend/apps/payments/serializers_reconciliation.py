"""
Serializers para Conciliación Bancaria
"""
from rest_framework import serializers
from decimal import Decimal
from .models import (
    BankReconciliation, BankTransaction, ReconciliationMatch, BankReconciliationLog,
    BankReconciliationConfig, ReconciliationStatus, MatchType, ReconciliationEventType
)
from apps.core.models import Hotel


class BankReconciliationConfigSerializer(serializers.ModelSerializer):
    """Serializer para configuración de conciliación bancaria"""
    
    class Meta:
        model = BankReconciliationConfig
        fields = [
            'id', 'hotel', 'exact_match_date_tolerance', 'fuzzy_match_amount_tolerance_percent',
            'fuzzy_match_date_tolerance', 'partial_match_amount_tolerance_percent',
            'partial_match_date_tolerance', 'auto_confirm_threshold', 'pending_review_threshold',
            'default_currency', 'currency_rate', 'currency_rate_date', 'email_notifications',
            'notification_threshold_percent', 'notification_emails', 'csv_encoding',
            'csv_separator', 'csv_columns', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BankTransactionSerializer(serializers.ModelSerializer):
    """Serializer para transacciones bancarias"""
    
    class Meta:
        model = BankTransaction
        fields = [
            'id', 'reconciliation', 'transaction_date', 'description', 'amount',
            'currency', 'reference', 'is_matched', 'is_reversal', 'match_confidence',
            'match_type', 'matched_payment_id', 'matched_payment_type',
            'matched_reservation_id', 'amount_difference', 'date_difference_days',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReconciliationMatchSerializer(serializers.ModelSerializer):
    """Serializer para matches de conciliación"""
    
    class Meta:
        model = ReconciliationMatch
        fields = [
            'id', 'reconciliation', 'bank_transaction', 'payment_id', 'payment_type',
            'reservation_id', 'match_type', 'confidence_score', 'amount_difference',
            'date_difference_days', 'is_confirmed', 'is_manual', 'manual_approved_by',
            'manual_approved_at', 'manual_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BankReconciliationLogSerializer(serializers.ModelSerializer):
    """Serializer para logs de auditoría de conciliación"""
    
    class Meta:
        model = BankReconciliationLog
        fields = [
            'id', 'reconciliation', 'event_type', 'event_description',
            'bank_transaction_id', 'payment_id', 'payment_type', 'reservation_id',
            'details', 'confidence_score', 'created_by', 'created_at', 'csv_filename'
        ]
        read_only_fields = ['id', 'created_at']


class BankReconciliationSerializer(serializers.ModelSerializer):
    """Serializer para conciliaciones bancarias"""
    
    match_percentage = serializers.ReadOnlyField()
    needs_manual_review = serializers.ReadOnlyField()
    transactions = BankTransactionSerializer(many=True, read_only=True)
    matches = ReconciliationMatchSerializer(many=True, read_only=True)
    audit_logs = BankReconciliationLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = BankReconciliation
        fields = [
            'id', 'hotel', 'reconciliation_date', 'csv_file', 'csv_filename',
            'csv_file_size', 'total_transactions', 'matched_transactions',
            'unmatched_transactions', 'pending_review_transactions', 'error_transactions',
            'status', 'processing_started_at', 'processing_completed_at',
            'created_by', 'created_at', 'updated_at', 'processing_notes',
            'error_details', 'match_percentage', 'needs_manual_review',
            'transactions', 'matches', 'audit_logs'
        ]
        read_only_fields = [
            'id', 'csv_file_size', 'total_transactions', 'matched_transactions',
            'unmatched_transactions', 'pending_review_transactions', 'error_transactions',
            'processing_started_at', 'processing_completed_at', 'created_at', 'updated_at',
            'match_percentage', 'needs_manual_review'
        ]


class BankReconciliationCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear conciliaciones bancarias"""
    
    class Meta:
        model = BankReconciliation
        fields = ['hotel', 'reconciliation_date', 'csv_file']
    
    def validate_csv_file(self, value):
        """Validar archivo CSV"""
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("El archivo debe ser un CSV")
        
        if value.size > 10 * 1024 * 1024:  # 10MB
            raise serializers.ValidationError("El archivo es demasiado grande (máximo 10MB)")
        
        return value
    
    def validate_reconciliation_date(self, value):
        """Validar fecha de conciliación"""
        from django.utils import timezone
        if value > timezone.now().date():
            raise serializers.ValidationError("La fecha de conciliación no puede ser futura")
        return value


class BankReconciliationUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar conciliaciones bancarias"""
    
    class Meta:
        model = BankReconciliation
        fields = ['processing_notes']
    
    def validate(self, data):
        """Validar que solo se puedan actualizar las notas"""
        if self.instance.status not in ['pending', 'processing']:
            raise serializers.ValidationError("Solo se pueden actualizar conciliaciones pendientes o en procesamiento")
        return data


class ReconciliationMatchUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar matches de conciliación"""
    
    class Meta:
        model = ReconciliationMatch
        fields = ['is_confirmed', 'is_manual', 'manual_notes']
    
    def validate(self, data):
        """Validar actualización de match"""
        if self.instance.is_confirmed and not data.get('is_confirmed', True):
            raise serializers.ValidationError("No se puede desconfirmar un match ya confirmado")
        
        if data.get('is_manual') and not data.get('manual_notes'):
            raise serializers.ValidationError("Se requieren notas para matches manuales")
        
        return data


class BankReconciliationStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas de conciliación"""
    
    total_reconciliations = serializers.IntegerField()
    pending_reconciliations = serializers.IntegerField()
    completed_reconciliations = serializers.IntegerField()
    failed_reconciliations = serializers.IntegerField()
    total_transactions = serializers.IntegerField()
    matched_transactions = serializers.IntegerField()
    unmatched_transactions = serializers.IntegerField()
    pending_review_transactions = serializers.IntegerField()
    average_match_percentage = serializers.FloatField()
    reconciliations_this_month = serializers.IntegerField()
    reconciliations_last_month = serializers.IntegerField()


class BankReconciliationSummarySerializer(serializers.Serializer):
    """Serializer para resumen de conciliación"""
    
    reconciliation_id = serializers.IntegerField()
    hotel_name = serializers.CharField()
    reconciliation_date = serializers.DateField()
    status = serializers.CharField()
    total_transactions = serializers.IntegerField()
    matched_transactions = serializers.IntegerField()
    unmatched_transactions = serializers.IntegerField()
    pending_review_transactions = serializers.IntegerField()
    match_percentage = serializers.FloatField()
    needs_manual_review = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    processing_completed_at = serializers.DateTimeField(allow_null=True)

