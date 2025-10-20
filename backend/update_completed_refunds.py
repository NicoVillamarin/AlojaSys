#!/usr/bin/env python
"""
Script para actualizar refunds completados que no tienen processed_at
"""
import os
import sys
import django
from django.utils import timezone

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

from apps.payments.models import Refund, RefundStatus

def update_completed_refunds():
    """Actualiza refunds completados que no tienen processed_at"""
    # Buscar refunds completados sin processed_at
    completed_refunds = Refund.objects.filter(
        status=RefundStatus.COMPLETED,
        processed_at__isnull=True
    )
    
    print(f"Encontrados {completed_refunds.count()} refunds completados sin processed_at")
    
    updated_count = 0
    for refund in completed_refunds:
        # Usar updated_at como processed_at si no hay mejor opción
        refund.processed_at = refund.updated_at
        refund.save(update_fields=['processed_at'])
        updated_count += 1
        print(f"Actualizado refund {refund.id} - processed_at: {refund.processed_at}")
    
    print(f"Se actualizaron {updated_count} refunds")
    
    # Mostrar estadísticas
    stats = Refund.objects.values('status').annotate(
        count=django.db.models.Count('id'),
        with_processed_at=django.db.models.Count('id', filter=django.db.models.Q(processed_at__isnull=False))
    ).order_by('status')
    
    print("\nEstadísticas por estado:")
    for stat in stats:
        print(f"{stat['status']}: {stat['count']} total, {stat['with_processed_at']} con processed_at")

if __name__ == "__main__":
    update_completed_refunds()
