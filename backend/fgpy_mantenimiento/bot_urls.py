from django.urls import path

from fgpy_mantenimiento.views import FgpyMaintenanceBotIncidentView


app_name = "fgpy_mantenimiento_bot"

urlpatterns = [
    path(
        "incidents/",
        FgpyMaintenanceBotIncidentView.as_view(),
        name="bot-incident-list",
    ),
]
