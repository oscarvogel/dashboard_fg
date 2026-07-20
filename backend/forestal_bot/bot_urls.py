from django.urls import path

from forestal_bot.views import (
    FgpyDriverDetailView,
    FgpyDriverListCreateView,
    FgpyVehicleDetailView,
    FgpyVehicleListCreateView,
    FuelReportDetailView,
    FuelReportEvidenceDownloadView,
    FuelReportListCreateView,
)


app_name = "forestal_bot_api"

urlpatterns = [
    path("fgpy-vehicles/", FgpyVehicleListCreateView.as_view(), name="fgpy-vehicle-list"),
    path("fgpy-vehicles/<uuid:pk>/", FgpyVehicleDetailView.as_view(), name="fgpy-vehicle-detail"),
    path("fgpy-drivers/", FgpyDriverListCreateView.as_view(), name="fgpy-driver-list"),
    path("fgpy-drivers/<uuid:pk>/", FgpyDriverDetailView.as_view(), name="fgpy-driver-detail"),
    path("fuel-reports/", FuelReportListCreateView.as_view(), name="fuel-report-list"),
    path(
        "fuel-reports/<uuid:pk>/",
        FuelReportDetailView.as_view(),
        name="fuel-report-detail",
    ),
    path(
        "fuel-reports/<uuid:pk>/evidence/<int:evidence_id>/",
        FuelReportEvidenceDownloadView.as_view(),
        name="fuel-report-evidence",
    ),
]
