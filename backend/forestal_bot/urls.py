from django.urls import path

from forestal_bot.views import WhatsAppMessageCreateView, WhatsAppMessageRecentView

app_name = "forestal_bot"

urlpatterns = [
    path(
        "whatsapp/messages/recent/",
        WhatsAppMessageRecentView.as_view(),
        name="whatsapp-message-recent",
    ),
    path(
        "whatsapp/messages/",
        WhatsAppMessageCreateView.as_view(),
        name="whatsapp-message-list",
    ),
]
