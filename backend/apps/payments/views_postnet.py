import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.db import transaction

from apps.reservations.models import Payment
from .adapters.postnet import PostnetAdapter

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def settle_postnet_payment(request, payment_id):
    """
    Endpoint para confirmar o rechazar un pago POSTNET pendiente.
    """
    try:
        payment = get_object_or_404(Payment, id=payment_id, method='pos')
        
        if payment.status != 'pending_settlement':
            return Response(
                {"detail": "El pago no está en estado pendiente de liquidación."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        action = request.data.get('action')  # 'approve' o 'reject'
        notes = request.data.get('notes', '')
        
        if action not in ['approve', 'reject']:
            return Response(
                {"detail": "La acción debe ser 'approve' o 'reject'."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Usar el adapter para procesar el settlement
            adapter = PostnetAdapter({})
            result = adapter.settle_payment(str(payment_id), {
                'action': action,
                'notes': notes
            })
            
            if result['success']:
                # Actualizar el pago
                payment.status = result['new_status']
                if notes:
                    payment.notes = notes
                payment.save()
                
                logger.info(f"POSTNET payment {payment_id} settled as {result['new_status']}")
                
                return Response({
                    "success": True,
                    "payment_id": payment_id,
                    "new_status": result['new_status'],
                    "action": action
                })
            else:
                return Response(
                    {"detail": result['error']}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
    except Exception as e:
        logger.error(f"Error settling POSTNET payment {payment_id}: {e}", exc_info=True)
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
