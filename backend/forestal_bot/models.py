from django.db import models


class WhatsAppMessage(models.Model):
    source = models.CharField(max_length=255, blank=True)
    provider = models.CharField(max_length=255, blank=True)
    account_id = models.CharField(max_length=255)
    group_jid = models.CharField(max_length=255)
    message_id = models.CharField(max_length=255)
    group_name = models.CharField(max_length=255, blank=True)
    sender_id = models.CharField(max_length=255, blank=True)
    sender_e164 = models.CharField(max_length=255, blank=True)
    sender_name = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField()
    body = models.TextField(blank=True, default="")
    message_type = models.CharField(max_length=255, blank=True)
    media_type = models.CharField(max_length=255, blank=True)
    media_path = models.TextField(blank=True, default="")
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
