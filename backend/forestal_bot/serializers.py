from datetime import datetime

from rest_framework import serializers

from forestal_bot.models import (
    DailySummaryDelivery,
    DailySummaryGroup,
    DailySummaryRun,
    WhatsAppGroup,
    WhatsAppMessage,
)


FORBIDDEN_ERROR_MARKERS = (
    "traceback (most recent call last)",
    "authorization: bearer",
    "openclaw_ingest_token",
    "secret_key",
    "database_url",
)


def validate_sanitized_error(value):
    if any(marker in value.lower() for marker in FORBIDDEN_ERROR_MARKERS):
        raise serializers.ValidationError(
            "Provide a short technical description without traces or secrets."
        )
    return value


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

    def validate(self, attrs):
        if attrs.get("transcription_status") == "completed" and not attrs.get(
            "transcription", ""
        ).strip():
            raise serializers.ValidationError(
                {"transcription": ["A completed transcription requires text."]}
            )
        if attrs.get("image_analysis_status") == "completed" and not attrs.get(
            "image_description", ""
        ).strip():
            raise serializers.ValidationError(
                {"image_description": ["A completed image analysis requires a description."]}
            )
        return attrs

    def validate_transcription_error(self, value):
        return validate_sanitized_error(value)

    def validate_image_analysis_error(self, value):
        return validate_sanitized_error(value)

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
            "transcribed_at",
            "image_analyzed_at",
        )
        validators = []
        extra_kwargs = {
            "account_id": {"required": True},
            "group_jid": {"required": True},
            "message_id": {"required": True},
            "timestamp": {"required": True},
        }


class WhatsAppOwnerMessageSerializer(WhatsAppMessageSerializer):
    class Meta:
        model = WhatsAppMessage
        fields = (
            "id",
            "group",
            "group_display_name",
            "sender_name",
            "sender_id",
            "timestamp",
            "body",
            "message_type",
            "media_type",
            "transcription",
            "transcription_status",
            "transcription_error",
            "transcribed_at",
            "image_description",
            "image_analysis_status",
            "image_analysis_error",
            "image_analyzed_at",
        )
        read_only_fields = fields


class DailySummaryGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailySummaryGroup
        fields = (
            "group_key",
            "group_name",
            "message_count",
            "summary_text",
            "no_updates",
            "position",
        )


class DailySummaryDeliverySerializer(serializers.ModelSerializer):
    def validate_error(self, value):
        return validate_sanitized_error(value)

    class Meta:
        model = DailySummaryDelivery
        fields = (
            "channel",
            "recipient_name",
            "status",
            "attempted_at",
            "delivered_at",
            "error",
            "external_id",
        )


class DailySummaryRunSerializer(serializers.ModelSerializer):
    idempotency_key = serializers.CharField(max_length=128, validators=[])
    groups = DailySummaryGroupSerializer(many=True)
    deliveries = DailySummaryDeliverySerializer(many=True, required=False)

    class Meta:
        model = DailySummaryRun
        fields = (
            "id",
            "idempotency_key",
            "operational_date",
            "generated_at",
            "status",
            "consolidated_text",
            "spoken_script",
            "total_groups",
            "total_messages",
            "generator_version",
            "source",
            "groups",
            "deliveries",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_groups(self, value):
        keys = [item["group_key"] for item in value]
        if not keys:
            raise serializers.ValidationError("At least one group is required.")
        if len(keys) != len(set(keys)):
            raise serializers.ValidationError("group_key values must be unique.")
        return value

    def validate(self, attrs):
        groups = attrs.get("groups", [])
        if attrs.get("total_groups") != len(groups):
            raise serializers.ValidationError(
                {"total_groups": ["Must match the number of groups."]}
            )
        message_total = sum(group["message_count"] for group in groups)
        if attrs.get("total_messages") != message_total:
            raise serializers.ValidationError(
                {"total_messages": ["Must match the sum of group message counts."]}
            )
        return attrs

    def validate_deliveries(self, value):
        identities = [(item["channel"], item["recipient_name"]) for item in value]
        if len(identities) != len(set(identities)):
            raise serializers.ValidationError(
                "channel and recipient_name pairs must be unique."
            )
        return value
