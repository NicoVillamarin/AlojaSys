from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chatbot.services import WhatsappChatbotService


class WhatsappWebhookView(APIView):
    """
    Endpoint genérico para recibir los webhooks de WhatsApp (Twilio, Meta, etc.).
    En producción, normalmente se configurará una URL pública (via EXTERNAL_BASE_URL).
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        """
        Permite a algunos proveedores validar el endpoint con un simple GET.
        """
        return Response({"detail": "Webhook WhatsApp operativo"}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        service = WhatsappChatbotService()
        result = service.handle_incoming_message(request.data)
        http_status = status.HTTP_200_OK if result.get("ok", True) else status.HTTP_400_BAD_REQUEST
        return Response(result, status=http_status)

