from rest_framework import serializers

from forestal_bot.models import WhatsAppMessage


class WhatsAppMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsAppMessage
        fields = "__all__"
        read_only_fields = ("id", "raw_json", "synced_at", "created_at")
        validators = []
        extra_kwargs = {
            "account_id": {"required": True},
            "group_jid": {"required": True},
            "message_id": {"required": True},
            "timestamp": {"required": True},
        }
