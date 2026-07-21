import uuid

from django.db import models
from django.db.models import Q
from django.core.validators import MaxLengthValidator


UNIDENTIFIED_GROUP_NAME = "Grupo sin identificar"
TRANSCRIPTION_STATUS_CHOICES = [
    ("", "Sin estado"),
    ("pending", "Pendiente"),
    ("processing", "Procesando"),
    ("completed", "Completada"),
    ("failed", "Fallida"),
]
IMAGE_ANALYSIS_STATUS_CHOICES = TRANSCRIPTION_STATUS_CHOICES
DAILY_SUMMARY_STATUS_CHOICES = [
    ("generated", "Generado"),
    ("partial", "Entrega parcial"),
    ("sent", "Enviado"),
    ("failed", "Fallido"),
]
DAILY_SUMMARY_DELIVERY_STATUS_CHOICES = [
    ("pending", "Pendiente"),
    ("sent", "Enviado"),
    ("failed", "Fallido"),
    ("skipped_duplicate", "Duplicado omitido"),
]
WEIGHING_ORGANIZATION_KEY = "forestal-paraguay"
WEIGHING_STATUS_CHOICES = [
    ("pendiente", "Pendiente"),
    ("completo", "Completo"),
    ("observado", "Observado"),
    ("anulado", "Anulado"),
]
WEIGHING_SCALE_CHOICES = [
    ("felber", "Felber"),
    ("forestal_paraguay", "Forestal Paraguay"),
    ("otro", "Otro"),
]
WEIGHING_KIND_CHOICES = [("tara", "Tara"), ("bruto", "Bruto")]
WEIGHING_SOURCE_CHOICES = [
    ("foto_balanza", "Foto de balanza"),
    ("remision", "Remisión"),
    ("planilla", "Planilla"),
    ("mensaje", "Mensaje"),
    ("correccion_manual", "Corrección manual"),
]
WEIGHING_UNIT_CATALOG = {
    "logistica-felber": {
        "display_name": "Logística Felber",
        "usual_official_scale": "felber",
    },
    "cosecha-paraguari": {
        "display_name": "Cosecha Paraguari",
        "usual_official_scale": "forestal_paraguay",
    },
}
FUEL_ORGANIZATION_KEY = "forestal-paraguay"
FUEL_ORIGIN_GROUP_KEY = "choferes-fgpy"
FUEL_STATUS_CHOICES = [
    ("received", "Recibida"),
    ("requires_review", "Requiere revisión"),
    ("confirmed", "Confirmada"),
    ("corrected", "Corregida"),
    ("rejected", "Rechazada"),
]
FUEL_SOURCE_ROLE_CHOICES = [
    ("initial", "Inicial"),
    ("receipt", "Comprobante"),
    ("dashboard", "Tablero"),
    ("clarification", "Aclaración"),
    ("correction", "Corrección"),
    ("confirmation", "Confirmación"),
]
FUEL_EVIDENCE_TYPE_CHOICES = [
    ("receipt", "Comprobante"),
    ("dashboard", "Tablero"),
    ("combined", "Combinada"),
    ("other", "Otra"),
]
FGPY_CATALOG_STATUS_CHOICES = [
    ("pending", "Pendiente"),
    ("confirmed", "Confirmado"),
    ("inactive", "Inactivo"),
]
FGPY_CATALOG_CREATED_VIA_CHOICES = [("bot", "Bot"), ("user", "Usuario")]


class WhatsAppGroup(models.Model):
    account_id = models.CharField(max_length=255)
    jid = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "jid"]
        indexes = [
            models.Index(fields=["jid"], name="forestal_wag_jid_idx"),
            models.Index(
                fields=["account_id", "active"],
                name="forestal_wag_acct_active_idx",
            ),
            models.Index(fields=["name"], name="forestal_wag_name_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["account_id", "jid"],
                name="forestal_bot_whatsapp_group_identity_uniq",
            )
        ]

    def __str__(self):
        return self.name


class WhatsAppMessage(models.Model):
    source = models.CharField(max_length=255, blank=True)
    provider = models.CharField(max_length=255, blank=True)
    account_id = models.CharField(max_length=255)
    group_jid = models.CharField(max_length=255)
    message_id = models.CharField(max_length=255)
    group_name = models.CharField(max_length=255, blank=True)
    group = models.ForeignKey(
        WhatsAppGroup,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="messages",
    )
    sender_id = models.CharField(max_length=255, blank=True)
    sender_e164 = models.CharField(max_length=255, blank=True)
    sender_name = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField()
    body = models.TextField(blank=True, default="")
    message_type = models.CharField(max_length=255, blank=True)
    media_type = models.CharField(max_length=255, blank=True)
    media_path = models.TextField(blank=True, default="")
    transcription = models.TextField(
        blank=True,
        default="",
        validators=[MaxLengthValidator(20000)],
    )
    transcription_status = models.CharField(
        max_length=32,
        blank=True,
        default="",
        choices=TRANSCRIPTION_STATUS_CHOICES,
    )
    transcription_error = models.TextField(
        blank=True,
        default="",
        validators=[MaxLengthValidator(1000)],
    )
    transcribed_at = models.DateTimeField(null=True, blank=True)
    image_description = models.TextField(
        blank=True,
        default="",
        validators=[MaxLengthValidator(10000)],
    )
    image_analysis_status = models.CharField(
        max_length=32,
        blank=True,
        default="",
        choices=IMAGE_ANALYSIS_STATUS_CHOICES,
    )
    image_analysis_error = models.TextField(
        blank=True,
        default="",
        validators=[MaxLengthValidator(500)],
    )
    image_analyzed_at = models.DateTimeField(null=True, blank=True)
    gated_out = models.BooleanField(default=False)
    would_process_agent = models.BooleanField(default=False)
    skip_reason = models.CharField(max_length=255, blank=True)
    raw_json = models.JSONField(default=dict)
    synced_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp", "-created_at"]
        indexes = [
            models.Index(
                fields=["timestamp", "created_at"],
                name="forestal_wa_ts_created_idx",
            ),
            models.Index(
                fields=["group_jid", "timestamp", "created_at"],
                name="forestal_wa_group_ts_cr_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["account_id", "group_jid", "message_id"],
                name="forestal_bot_whatsapp_message_identity_uniq",
            )
        ]


class DailySummaryRun(models.Model):
    idempotency_key = models.CharField(max_length=128, unique=True)
    operational_date = models.DateField(db_index=True)
    generated_at = models.DateTimeField()
    status = models.CharField(max_length=16, choices=DAILY_SUMMARY_STATUS_CHOICES)
    consolidated_text = models.TextField(validators=[MaxLengthValidator(50000)])
    spoken_script = models.TextField(
        blank=True,
        default="",
        validators=[MaxLengthValidator(50000)],
    )
    total_groups = models.PositiveIntegerField(default=0)
    total_messages = models.PositiveIntegerField(default=0)
    generator_version = models.CharField(max_length=100, blank=True, default="")
    source = models.CharField(max_length=100, default="openclaw")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-operational_date", "-generated_at"]


class DailySummaryGroup(models.Model):
    run = models.ForeignKey(
        DailySummaryRun,
        on_delete=models.CASCADE,
        related_name="groups",
    )
    group_key = models.CharField(max_length=100)
    group_name = models.CharField(max_length=255)
    message_count = models.PositiveIntegerField(default=0)
    summary_text = models.TextField(validators=[MaxLengthValidator(30000)])
    no_updates = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["run", "group_key"],
                name="forestal_bot_daily_summary_group_uniq",
            )
        ]


class DailySummaryDelivery(models.Model):
    run = models.ForeignKey(
        DailySummaryRun,
        on_delete=models.CASCADE,
        related_name="deliveries",
    )
    channel = models.CharField(max_length=32)
    recipient_name = models.CharField(max_length=100)
    status = models.CharField(
        max_length=32,
        choices=DAILY_SUMMARY_DELIVERY_STATUS_CHOICES,
    )
    attempted_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(
        blank=True,
        default="",
        validators=[MaxLengthValidator(1000)],
    )
    external_id = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["channel", "recipient_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["run", "channel", "recipient_name"],
                name="forestal_bot_daily_summary_delivery_uniq",
            )
        ]


class WeighingMovement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    idempotency_key = models.CharField(max_length=128, unique=True)
    organization_key = models.CharField(
        max_length=64, default=WEIGHING_ORGANIZATION_KEY, db_index=True
    )
    origin_group_key = models.CharField(
        max_length=100, default="logistica-felber", db_index=True
    )
    operational_date = models.DateField(db_index=True)
    plate_normalized = models.CharField(max_length=32, blank=True, default="", db_index=True)
    plate_original = models.CharField(max_length=64, blank=True, default="")
    driver_name = models.CharField(max_length=255, blank=True, default="", db_index=True)
    status = models.CharField(
        max_length=16, choices=WEIGHING_STATUS_CHOICES, default="pendiente", db_index=True
    )
    declared_quantity_kg = models.PositiveIntegerField(null=True, blank=True)
    official_scale = models.CharField(
        max_length=32, choices=WEIGHING_SCALE_CHOICES, null=True, blank=True
    )
    observations = models.TextField(blank=True, default="")
    evidence = models.JSONField(default=list, blank=True)
    source_message_ids = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-operational_date", "-created_at"]
        indexes = [
            models.Index(
                fields=["organization_key", "operational_date"],
                name="forestal_weigh_org_date_idx",
            )
        ]


class WeighingMeasurement(models.Model):
    movement = models.ForeignKey(
        WeighingMovement, on_delete=models.CASCADE, related_name="measurements"
    )
    idempotency_key = models.CharField(max_length=128, unique=True)
    scale = models.CharField(max_length=32, choices=WEIGHING_SCALE_CHOICES)
    kind = models.CharField(max_length=16, choices=WEIGHING_KIND_CHOICES)
    weight_kg = models.PositiveIntegerField()
    source = models.CharField(max_length=32, choices=WEIGHING_SOURCE_CHOICES)
    evidence_id = models.CharField(max_length=255, blank=True, default="")
    message_id = models.CharField(max_length=255, blank=True, default="")
    measured_at = models.DateTimeField()
    correction_reason = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scale", "kind"]
        constraints = [
            models.UniqueConstraint(
                fields=["movement", "scale", "kind"],
                name="forestal_weigh_measurement_identity_uniq",
            )
        ]


class WeighingMeasurementRevision(models.Model):
    measurement = models.ForeignKey(
        WeighingMeasurement, on_delete=models.CASCADE, related_name="revisions"
    )
    revision = models.PositiveIntegerField()
    idempotency_key = models.CharField(max_length=128, unique=True)
    weight_kg = models.PositiveIntegerField()
    source = models.CharField(max_length=32, choices=WEIGHING_SOURCE_CHOICES)
    evidence_id = models.CharField(max_length=255, blank=True, default="")
    message_id = models.CharField(max_length=255, blank=True, default="")
    measured_at = models.DateTimeField()
    correction_reason = models.CharField(max_length=500, blank=True, default="")
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["revision"]
        constraints = [
            models.UniqueConstraint(
                fields=["measurement", "revision"],
                name="forestal_weigh_revision_identity_uniq",
            )
        ]


class FgpyVehicle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_key = models.CharField(
        max_length=64, default=FUEL_ORGANIZATION_KEY, db_index=True
    )
    original_plate = models.CharField(max_length=64, blank=True, default="")
    normalized_plate = models.CharField(max_length=32, blank=True, default="", db_index=True)
    internal_code = models.CharField(max_length=64, blank=True, default="")
    proposal_key = models.CharField(max_length=128, blank=True, null=True, default=None)
    description = models.CharField(max_length=255, blank=True, default="")
    make = models.CharField(max_length=100, blank=True, default="")
    model = models.CharField(max_length=100, blank=True, default="")
    confirmed_plate_key = models.CharField(
        max_length=32, blank=True, null=True, default=None, editable=False
    )
    confirmed_aliases = models.JSONField(default=list, blank=True)
    active = models.BooleanField(default=True)
    status = models.CharField(
        max_length=16, choices=FGPY_CATALOG_STATUS_CHOICES, default="pending", db_index=True
    )
    initial_source_message = models.ForeignKey(
        WhatsAppMessage, null=True, blank=True, on_delete=models.PROTECT,
        related_name="proposed_fgpy_vehicles",
    )
    created_via = models.CharField(
        max_length=8, choices=FGPY_CATALOG_CREATED_VIA_CHOICES
    )
    created_by = models.ForeignKey(
        "auth.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="created_fgpy_vehicles",
    )
    confirmed_by = models.ForeignKey(
        "auth.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="confirmed_fgpy_vehicles",
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "forestal_bot_fgpy_vehicle"
        ordering = ["description", "original_plate", "created_at"]
        constraints = [
            models.CheckConstraint(
                check=Q(organization_key=FUEL_ORGANIZATION_KEY),
                name="forestal_fgpy_vehicle_org_check",
            ),
            models.UniqueConstraint(
                fields=["organization_key", "confirmed_plate_key"],
                name="forestal_fgpy_vehicle_plate_confirmed_uniq",
            ),
            models.UniqueConstraint(
                fields=["organization_key", "proposal_key"],
                name="forestal_fgpy_vehicle_proposal_uniq",
            ),
        ]

    def save(self, *args, **kwargs):
        self.proposal_key = self.proposal_key or None
        self.confirmed_plate_key = (
            self.normalized_plate
            if self.status == "confirmed" and self.normalized_plate
            else None
        )
        super().save(*args, **kwargs)


class FgpyDriver(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_key = models.CharField(
        max_length=64, default=FUEL_ORGANIZATION_KEY, db_index=True
    )
    reported_name = models.CharField(max_length=255)
    normalized_name = models.CharField(max_length=255, blank=True, default="", db_index=True)
    external_identifier = models.CharField(max_length=128, blank=True, default="")
    proposal_key = models.CharField(max_length=128, blank=True, null=True, default=None)
    whatsapp_sender_identifier_hash = models.CharField(
        max_length=64, blank=True, default=""
    )
    confirmed_aliases = models.JSONField(default=list, blank=True)
    active = models.BooleanField(default=True)
    status = models.CharField(
        max_length=16, choices=FGPY_CATALOG_STATUS_CHOICES, default="pending", db_index=True
    )
    initial_source_message = models.ForeignKey(
        WhatsAppMessage, null=True, blank=True, on_delete=models.PROTECT,
        related_name="proposed_fgpy_drivers",
    )
    created_via = models.CharField(
        max_length=8, choices=FGPY_CATALOG_CREATED_VIA_CHOICES
    )
    created_by = models.ForeignKey(
        "auth.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="created_fgpy_drivers",
    )
    confirmed_by = models.ForeignKey(
        "auth.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="confirmed_fgpy_drivers",
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "forestal_bot_fgpy_driver"
        ordering = ["reported_name", "created_at"]
        constraints = [
            models.CheckConstraint(
                check=Q(organization_key=FUEL_ORGANIZATION_KEY),
                name="forestal_fgpy_driver_org_check",
            ),
            models.UniqueConstraint(
                fields=["organization_key", "proposal_key"],
                name="forestal_fgpy_driver_proposal_uniq",
            ),
        ]

    def save(self, *args, **kwargs):
        self.proposal_key = self.proposal_key or None
        super().save(*args, **kwargs)


class FuelReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_key = models.CharField(max_length=64, db_index=True)
    origin_group_key = models.CharField(max_length=100, db_index=True)
    idempotency_key = models.CharField(max_length=128)
    event_at = models.DateTimeField(null=True, blank=True, db_index=True)
    vehicle = models.ForeignKey(
        FgpyVehicle,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="forestal_bot_fuel_reports",
    )
    driver = models.ForeignKey(
        FgpyDriver,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="forestal_bot_fuel_reports",
    )
    liters = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    odometer_total = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    odometer_partial = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    station = models.CharField(max_length=255, blank=True, default="")
    receipt_number = models.CharField(max_length=100, blank=True, default="")
    fuel_type = models.CharField(max_length=100, blank=True, default="")
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, blank=True, default="")
    unit_price = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True
    )
    status = models.CharField(
        max_length=24, choices=FUEL_STATUS_CHOICES, default="received", db_index=True
    )
    overall_confidence = models.DecimalField(
        max_digits=5, decimal_places=4, null=True, blank=True
    )
    field_confidence = models.JSONField(default=dict, blank=True)
    original_extraction = models.JSONField(default=dict, blank=True)
    inconsistencies = models.JSONField(default=list, blank=True)
    review_notes = models.TextField(blank=True, default="")
    reviewed_by = models.ForeignKey(
        "auth.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_forestal_bot_fuel_reports",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "forestal_bot_fuel_report"
        ordering = ["-event_at", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization_key", "origin_group_key", "idempotency_key"],
                name="forestal_bot_fuel_report_idem_uniq",
            )
        ]
        indexes = [
            models.Index(
                fields=["organization_key", "origin_group_key", "status"],
                name="forestal_fuel_scope_status_idx",
            )
        ]


class FuelReportSourceMessage(models.Model):
    report = models.ForeignKey(
        FuelReport, on_delete=models.CASCADE, related_name="source_links"
    )
    message = models.ForeignKey(
        WhatsAppMessage, on_delete=models.PROTECT, related_name="fuel_report_links"
    )
    role = models.CharField(max_length=24, choices=FUEL_SOURCE_ROLE_CHOICES)
    position = models.PositiveIntegerField(default=0)
    linked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "forestal_bot_fuel_report_source_message"
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["report", "message"],
                name="forestal_bot_fuel_source_message_uniq",
            )
        ]


class FuelReportEvidence(models.Model):
    report = models.ForeignKey(
        FuelReport, on_delete=models.CASCADE, related_name="evidence_files"
    )
    source_message = models.ForeignKey(
        WhatsAppMessage,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="fuel_evidence_files",
    )
    evidence_type = models.CharField(max_length=16, choices=FUEL_EVIDENCE_TYPE_CHOICES)
    file = models.FileField(upload_to="forestal_bot/fuel/%Y/%m/")
    mime_type = models.CharField(max_length=100)
    size = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64)
    position = models.PositiveIntegerField(default=0)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "forestal_bot_fuel_report_evidence"
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["report", "sha256"],
                name="forestal_bot_fuel_evidence_sha_uniq",
            )
        ]


class FuelReportRevision(models.Model):
    report = models.ForeignKey(
        FuelReport, on_delete=models.CASCADE, related_name="revisions"
    )
    field_name = models.CharField(max_length=64)
    previous_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    reason = models.TextField(blank=True, default="")
    user = models.ForeignKey(
        "auth.User", null=True, blank=True, on_delete=models.SET_NULL
    )
    correction_source = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "forestal_bot_fuel_report_revision"
        ordering = ["created_at", "id"]
