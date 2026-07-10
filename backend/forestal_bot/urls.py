from django.urls import path

from forestal_bot.views import WhatsAppMessageCreateView

app_name = "forestal_bot"

urlpatterns = [
    path(
        "whatsapp/messages/",
        WhatsAppMessageCreateView.as_view(),
        name="whatsapp-message-list",
    ),
]
