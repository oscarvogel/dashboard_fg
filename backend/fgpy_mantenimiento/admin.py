from django.contrib import admin

from fgpy_mantenimiento.models import (
    FgpyEquipmentAlias,
    FgpyMaintenanceEvent,
    FgpyMaintenanceEvidence,
    FgpyMaintenanceIncident,
)


@admin.register(FgpyMaintenanceIncident)
class FgpyMaintenanceIncidentAdmin(admin.ModelAdmin):
    list_display = (
        "opened_at",
        "status",
        "operational_status",
        "management_status",
        "fgpy_equipment_display",
        "proposal_key",
    )
    search_fields = (
        "proposal_key",
        "fgpy_equipment_external_id",
        "fgpy_equipment_display",
        "summary",
    )
    list_filter = ("status", "operational_status", "management_status")


admin.site.register(FgpyMaintenanceEvent)
admin.site.register(FgpyMaintenanceEvidence)
admin.site.register(FgpyEquipmentAlias)
