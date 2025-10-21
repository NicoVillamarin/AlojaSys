"""
Serializers para el módulo de Cobros
"""
from rest_framework import serializers
from decimal import Decimal


class PaymentCollectionSerializer(serializers.Serializer):
    """Serializer para el módulo de Cobros - Historial unificado"""
    
    id = serializers.CharField()
    type = serializers.CharField()
    reservation_id = serializers.IntegerField()
    hotel_id = serializers.IntegerField()
    hotel_name = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    method = serializers.CharField()
    status = serializers.CharField()
    date = serializers.DateField()
    created_at = serializers.DateTimeField()
    description = serializers.CharField()
    reference = serializers.CharField(allow_null=True)
    currency = serializers.CharField()
    guest_name = serializers.CharField()
    room_name = serializers.CharField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    cbu_iban = serializers.CharField(allow_null=True, required=False)
    bank_name = serializers.CharField(allow_null=True, required=False)
    
    def to_representation(self, instance):
        """Convierte el diccionario a formato de respuesta"""
        data = super().to_representation(instance)
        
        # Formatear monto
        data['amount_formatted'] = f"${instance['amount']:,.2f}"
        
        # Formatear fechas
        data['date_formatted'] = instance['date'].strftime('%d/%m/%Y')
        data['created_at_formatted'] = instance['created_at'].strftime('%d/%m/%Y %H:%M')
        
        # Formatear estado
        status_map = {
            'approved': 'Aprobado',
            'pending': 'Pendiente',
            'rejected': 'Rechazado',
            'cancelled': 'Cancelado',
        }
        data['status_display'] = status_map.get(instance['status'], instance['status'])
        
        # Formatear método
        method_map = {
            'cash': 'Efectivo',
            'card': 'Tarjeta',
            'bank_transfer': 'Transferencia Bancaria',
            'mercado_pago': 'Mercado Pago',
            'pos': 'POS',
        }
        data['method_display'] = method_map.get(instance['method'], instance['method'])
        
        # Formatear tipo
        type_map = {
            'manual': 'Manual',
            'online': 'Online',
            'bank_transfer': 'Transferencia',
        }
        data['type_display'] = type_map.get(instance['type'], instance['type'])
        
        return data


class PaymentStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas de cobros"""
    
    summary = serializers.DictField()
    by_type = serializers.DictField()
    by_method = serializers.DictField()
    by_month = serializers.DictField()
