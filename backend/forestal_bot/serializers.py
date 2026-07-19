from datetime import datetime

from rest_framework import serializers

from forestal_bot.models import (
    DailySummaryDelivery,
    DailySummaryGroup,
    DailySummaryRun,
    WEIGHING_ORGANIZATION_KEY,
    WeighingMeasurement,
    WeighingMeasurementRevision,
    WeighingMovement,
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


def normalize_plate(value):
    return "".join(character for character in value.upper() if character.isalnum())


class WeighingMeasurementRevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeighingMeasurementRevision
        fields = (
            "revision",
            "idempotency_key",
            "weight_kg",
            "source",
            "evidence_id",
            "message_id",
            "measured_at",
            "correction_reason",
            "recorded_at",
        )
        read_only_fields = fields


class WeighingMeasurementSerializer(serializers.ModelSerializer):
    idempotency_key = serializers.CharField(max_length=128, validators=[])
    net_kg = serializers.IntegerField(required=False, write_only=True)
    revisions = WeighingMeasurementRevisionSerializer(many=True, read_only=True)

    class Meta:
        model = WeighingMeasurement
        fields = (
            "id",
            "idempotency_key",
            "scale",
            "kind",
            "weight_kg",
            "source",
            "evidence_id",
            "message_id",
            "measured_at",
            "correction_reason",
            "net_kg",
            "revisions",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "revisions", "created_at", "updated_at")

    def validate_weight_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError("El peso debe ser mayor que cero.")
        return value


class WeighingMovementSerializer(serializers.ModelSerializer):
    idempotency_key = serializers.CharField(max_length=128, validators=[])
    measurements = WeighingMeasurementSerializer(many=True, read_only=True)
    calculated_nets_kg = serializers.SerializerMethodField()
    comparisons_kg = serializers.SerializerMethodField()
    declared_vs_official_net_kg = serializers.SerializerMethodField()
    net_kg = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = WeighingMovement
        fields = (
            "id",
            "idempotency_key",
            "organization_key",
            "origin_group_key",
            "operational_date",
            "plate_normalized",
            "plate_original",
            "driver_name",
            "status",
            "declared_quantity_kg",
            "official_scale",
            "observations",
            "evidence",
            "source_message_ids",
            "measurements",
            "calculated_nets_kg",
            "comparisons_kg",
            "declared_vs_official_net_kg",
            "net_kg",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "plate_normalized",
            "measurements",
            "calculated_nets_kg",
            "comparisons_kg",
            "declared_vs_official_net_kg",
            "created_at",
            "updated_at",
        )

    def validate_organization_key(self, value):
        if value != WEIGHING_ORGANIZATION_KEY:
            raise serializers.ValidationError(
                f"organization_key debe ser {WEIGHING_ORGANIZATION_KEY}."
            )
        return value

    def validate_declared_quantity_kg(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "La cantidad declarada debe ser mayor que cero."
            )
        return value

    def validate(self, attrs):
        if attrs.get("status") == "completo" and not attrs.get("official_scale"):
            raise serializers.ValidationError(
                {"official_scale": ["Es obligatoria para completar el movimiento."]}
            )
        return attrs

    @staticmethod
    def nets_for(obj):
        weights = {}
        for measurement in obj.measurements.all():
            weights.setdefault(measurement.scale, {})[measurement.kind] = (
                measurement.weight_kg
            )
        return {
            scale: values["bruto"] - values["tara"]
            for scale, values in weights.items()
            if "tara" in values and "bruto" in values
        }

    def get_calculated_nets_kg(self, obj):
        return self.nets_for(obj)

    def get_comparisons_kg(self, obj):
        weights = {
            (measurement.scale, measurement.kind): measurement.weight_kg
            for measurement in obj.measurements.all()
        }
        felber_net = self.nets_for(obj).get("felber")
        paraguay_net = self.nets_for(obj).get("forestal_paraguay")

        def difference(kind):
            first = weights.get(("felber", kind))
            second = weights.get(("forestal_paraguay", kind))
            return None if first is None or second is None else first - second

        return {
            "felber_minus_forestal_paraguay": {
                "tara": difference("tara"),
                "bruto": difference("bruto"),
                "neto": (
                    None
                    if felber_net is None or paraguay_net is None
                    else felber_net - paraguay_net
                ),
            }
        }

    def get_declared_vs_official_net_kg(self, obj):
        if obj.declared_quantity_kg is None or not obj.official_scale:
            return None
        official_net = self.nets_for(obj).get(obj.official_scale)
        if official_net is None:
            return None
        return obj.declared_quantity_kg - official_net
