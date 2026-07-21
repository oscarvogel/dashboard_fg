import uuid

from django.db import models
from django.db.models import Q


FGPY_ORGANIZATION_KEY = "forestal-paraguay"

INCIDENT_STATUS_CHOICES = [
    ("open", "Abierta"),
    ("resolved", "Resuelta"),
    ("cancelled", "Cancelada"),
    ("requires_review", "Requiere revision"),
]
OPERATIONAL_STATUS_CHOICES = [
    ("stopped", "Parada"),
    ("operating", "Operando"),
    ("intermittent", "Intermitente"),
    ("unknown", "Desconocido"),
]
MANAGEMENT_STATUS_CHOICES = [
    ("waiting_part", "Esperando repuesto"),
    ("waiting_pickup", "Esperando retiro"),
    ("in_repair", "En reparacion"),
    ("resolved", "Resuelto"),
    ("pending_review", "Revision pendiente"),
    ("unknown", "Desconocido"),
]
EVENT_TYPE_CHOICES = [
    ("opened", "Apertura"),
    ("update", "Actualizacion"),
    ("diagnosis", "Diagnostico"),
    ("status_change", "Cambio de estado"),
    ("resolved", "Resolucion"),
    ("cancelled", "Cancelacion"),
    ("evidence", "Evidencia"),
]
EVIDENCE_TYPE_CHOICES = [
    ("image", "Imagen"),
    ("audio", "Audio"),
    ("document", "Documento"),
    ("message", "Mensaje"),
    ("other", "Otra"),
]


class FgpyMaintenanceIncident(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_key = models.CharField(
        max_length=64, default=FGPY_ORGANIZATION_KEY, db_index=True
    )
    fgpy_equipment_external_id = models.CharField(
        max_length=64, null=True, blank=True, db_index=True
    )
    fgpy_equipment_display = models.CharField(max_length=255, blank=True, default="")
    fgpy_equipment_code = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(
        max_length=24, choices=INCIDENT_STATUS_CHOICES, default="open", db_index=True
    )
    operational_status = models.CharField(
        max_length=24, choices=OPERATIONAL_STATUS_CHOICES, default="unknown"
    )
    management_status = models.CharField(
        max_length=24, choices=MANAGEMENT_STATUS_CHOICES, default="unknown"
    )
    incident_type = models.CharField(max_length=100, blank=True, default="")
    summary = models.TextField(blank=True, default="")
    location = models.CharField(max_length=255, blank=True, default="")
    diagnosis = models.TextField(blank=True, default="")
    pending = models.TextField(blank=True, default="")
    responsible = models.CharField(max_length=255, blank=True, default="")
    source_system = models.CharField(max_length=100, blank=True, default="")
    proposal_key = models.CharField(max_length=128, unique=True)
    opened_at = models.DateTimeField(db_index=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-opened_at", "-created_at"]
        indexes = [
            models.Index(
                fields=["organization_key", "status"],
                name="fgpy_maint_inc_org_status_idx",
            ),
            models.Index(
                fields=["organization_key", "fgpy_equipment_external_id"],
                name="fgpy_maint_inc_org_equip_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(organization_key=FGPY_ORGANIZATION_KEY),
                name="fgpy_maint_incident_org_check",
            )
        ]

    def save(self, *args, **kwargs):
        self.organization_key = FGPY_ORGANIZATION_KEY
        super().save(*args, **kwargs)

    def __str__(self):
        return self.summary or self.proposal_key


class FgpyMaintenanceEvent(models.Model):
    incident = models.ForeignKey(
        FgpyMaintenanceIncident, on_delete=models.CASCADE, related_name="events"
    )
    event_type = models.CharField(
        max_length=32, choices=EVENT_TYPE_CHOICES, default="update", db_index=True
    )
    description = models.TextField(blank=True, default="")
    operational_status = models.CharField(
        max_length=24, choices=OPERATIONAL_STATUS_CHOICES, null=True, blank=True
    )
    management_status = models.CharField(
        max_length=24, choices=MANAGEMENT_STATUS_CHOICES, null=True, blank=True
    )
    occurred_at = models.DateTimeField(db_index=True)
    source_message_id = models.CharField(max_length=255, blank=True, default="")
    source_group_key = models.CharField(max_length=100, blank=True, default="")
    source_group_name = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["occurred_at", "id"]
        indexes = [
            models.Index(
                fields=["source_group_key", "occurred_at"],
                name="fgpy_maint_evt_group_time_idx",
            )
        ]


class FgpyMaintenanceEvidence(models.Model):
    incident = models.ForeignKey(
        FgpyMaintenanceIncident, on_delete=models.CASCADE, related_name="evidence"
    )
    event = models.ForeignKey(
        FgpyMaintenanceEvent,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="evidence",
    )
    evidence_type = models.CharField(
        max_length=32, choices=EVIDENCE_TYPE_CHOICES, default="other"
    )
    description = models.TextField(blank=True, default="")
    external_reference = models.TextField(blank=True, default="")
    mime_type = models.CharField(max_length=100, blank=True, default="")
    size = models.PositiveBigIntegerField(null=True, blank=True)
    sha256 = models.CharField(max_length=64, blank=True, default="")
    source_message_id = models.CharField(max_length=255, blank=True, default="")
    source_group_key = models.CharField(max_length=100, blank=True, default="")
    source_group_name = models.CharField(max_length=255, blank=True, default="")
    captured_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["sha256"], name="fgpy_maint_evid_sha_idx"),
        ]


class FgpyEquipmentAlias(models.Model):
    organization_key = models.CharField(
        max_length=64, default=FGPY_ORGANIZATION_KEY, db_index=True
    )
    fgpy_equipment_external_id = models.CharField(max_length=64, db_index=True)
    alias = models.CharField(max_length=255)
    normalized_alias = models.CharField(max_length=255, db_index=True)
    confirmed = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["alias"]
        constraints = [
            models.CheckConstraint(
                check=Q(organization_key=FGPY_ORGANIZATION_KEY),
                name="fgpy_maint_alias_org_check",
            ),
            models.UniqueConstraint(
                fields=["organization_key", "fgpy_equipment_external_id", "normalized_alias"],
                name="fgpy_maint_alias_identity_uniq",
            ),
        ]

    def save(self, *args, **kwargs):
        self.organization_key = FGPY_ORGANIZATION_KEY
        self.normalized_alias = " ".join(self.alias.upper().split())
        super().save(*args, **kwargs)
