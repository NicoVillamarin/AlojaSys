from django.urls import path

from apps.chatbot.views import WhatsappWebhookView

urlpatterns = [
    path("whatsapp/webhook/", WhatsappWebhookView.as_view(), name="chatbot-whatsapp-webhook"),
]

