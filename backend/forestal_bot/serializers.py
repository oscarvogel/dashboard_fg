from datetime import datetime

from rest_framework import serializers

from forestal_bot.models import WhatsAppGroup, WhatsAppMessage


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


class WhatsAppGroupSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsAppGroup
        fields = ("id", "jid", "name")


class WhatsAppGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsAppGroup
        fields = (
            "id",
            "account_id",
            "jid",
            "name",
            "description",
            "active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class WhatsAppMessageSerializer(serializers.ModelSerializer):
    timestamp = ExplicitTimezoneDateTimeField(required=True)
    group = WhatsAppGroupSummarySerializer(read_only=True)
    group_display_name = serializers.SerializerMethodField()

    def get_group_display_name(self, obj):
        if obj.group_id and obj.group and obj.group.name:
            return obj.group.name
        return obj.group_name or obj.group_jid

    class Meta:
        model = WhatsAppMessage
        fields = "__all__"
        read_only_fields = (
            "id",
            "group",
            "group_display_name",
            "raw_json",
            "synced_at",
            "created_at",
        )
        validators = []
        extra_kwargs = {
            "account_id": {"required": True},
            "group_jid": {"required": True},
            "message_id": {"required": True},
            "timestamp": {"required": True},
        }
