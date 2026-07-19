import uuid

from django.db import models
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
