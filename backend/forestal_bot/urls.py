from django.urls import path

from forestal_bot.views import (
    WhatsAppGroupDetailView,
    WhatsAppGroupListCreateView,
    WhatsAppMessageCreateView,
    WhatsAppMessageRecentView,
)

app_name = "forestal_bot"

urlpatterns = [
    path(
        "whatsapp/groups/",
        WhatsAppGroupListCreateView.as_view(),
        name="whatsapp-group-list",
    ),
    path(
        "whatsapp/groups/<int:pk>/",
        WhatsAppGroupDetailView.as_view(),
        name="whatsapp-group-detail",
    ),
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
