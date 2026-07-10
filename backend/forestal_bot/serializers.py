from datetime import datetime

from rest_framework import serializers

from forestal_bot.models import WhatsAppMessage


class ExplicitTimezoneDateTimeField(serializers.DateTimeField):
    default_error_messages = {
        **serializers.DateTimeField.default_error_messages,
        "timezone_required": "An explicit timezone offset is required.",
    }

    def to_internal_value(self, value):
        parsed_value = super().to_internal_value(value)
        try:
            source_value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (AttributeError, TypeError, ValueError):
            return parsed_value

        if source_value.tzinfo is None or source_value.utcoffset() is None:
            self.fail("timezone_required")
        return parsed_value


class WhatsAppMessageSerializer(serializers.ModelSerializer):
    timestamp = ExplicitTimezoneDateTimeField(required=True)

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
