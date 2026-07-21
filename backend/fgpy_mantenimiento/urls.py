from django.urls import path
from rest_framework.routers import DefaultRouter

from fgpy_mantenimiento import views


app_name = "fgpy_mantenimiento"

router = DefaultRouter()
router.register("incidents", views.FgpyMaintenanceIncidentViewSet, basename="incident")
router.register("events", views.FgpyMaintenanceEventViewSet, basename="event")
router.register("evidence", views.FgpyMaintenanceEvidenceViewSet, basename="evidence")
router.register("equipment-aliases", views.FgpyEquipmentAliasViewSet, basename="equipment-alias")

urlpatterns = [
    path("catalog/equipment/", views.FgpyEquipmentCatalogView.as_view(), name="equipment-catalog"),
    *router.urls,
]
