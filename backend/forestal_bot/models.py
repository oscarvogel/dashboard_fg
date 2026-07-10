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
