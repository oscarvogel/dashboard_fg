from rest_framework import serializers

from fgpy_mantenimiento.models import (
    EVIDENCE_TYPE_CHOICES,
    EVENT_TYPE_CHOICES,
    FGPY_ORGANIZATION_KEY,
    INCIDENT_STATUS_CHOICES,
    MANAGEMENT_STATUS_CHOICES,
    OPERATIONAL_STATUS_CHOICES,
    FgpyEquipmentAlias,
    FgpyMaintenanceEvent,
    FgpyMaintenanceEvidence,
    FgpyMaintenanceIncident,
)


class FgpyMaintenanceEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FgpyMaintenanceEvidence
        fields = (
            "id",
            "incident",
            "event",
            "evidence_type",
            "description",
            "external_reference",
            "mime_type",
            "size",
            "sha256",
            "source_message_id",
            "source_group_key",
            "source_group_name",
            "captured_at",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class FgpyMaintenanceEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = FgpyMaintenanceEvent
        fields = (
            "id",
            "incident",
            "event_type",
            "description",
            "operational_status",
            "management_status",
            "occurred_at",
            "source_message_id",
            "source_group_key",
            "source_group_name",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class FgpyMaintenanceIncidentSerializer(serializers.ModelSerializer):
    events = FgpyMaintenanceEventSerializer(many=True, read_only=True)
    evidence = FgpyMaintenanceEvidenceSerializer(many=True, read_only=True)

    class Meta:
        model = FgpyMaintenanceIncident
        fields = (
            "id",
            "organization_key",
            "fgpy_equipment_external_id",
            "fgpy_equipment_display",
            "fgpy_equipment_code",
            "status",
            "operational_status",
            "management_status",
            "incident_type",
            "summary",
            "location",
            "diagnosis",
            "pending",
            "responsible",
            "source_system",
            "proposal_key",
            "opened_at",
            "closed_at",
            "events",
            "evidence",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "events", "evidence")
        extra_kwargs = {"proposal_key": {"validators": []}}

    def validate_organization_key(self, value):
        if value != FGPY_ORGANIZATION_KEY:
            raise serializers.ValidationError("Use forestal-paraguay.")
        return value

    def validate(self, attrs):
        attrs["organization_key"] = FGPY_ORGANIZATION_KEY
        return attrs


class FgpyEquipmentAliasSerializer(serializers.ModelSerializer):
    class Meta:
        model = FgpyEquipmentAlias
        fields = (
            "id",
            "organization_key",
            "fgpy_equipment_external_id",
            "alias",
            "normalized_alias",
            "confirmed",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "organization_key", "normalized_alias", "created_at", "updated_at")


# ---------------------------------------------------------------------------
# Bot payload serializer
# ---------------------------------------------------------------------------

MAX_EVIDENCE_METADATA_ENTRIES = 10
MAX_EVIDENCE_REFERENCE_LENGTH = 512
EVIDENCE_METADATA_FIELDS = {
    "evidence_type",
    "description",
    "external_reference",
    "mime_type",
    "size",
    "sha256",
    "source_message_id",
    "source_group_key",
    "source_group_name",
    "captured_at",
}


def _validate_evidence_metadata(value):
    """Allow only metadata, never file payloads.

    The bot endpoint never accepts raw files; this is a defensive filter
    so a misconfigured caller cannot inject binary content via a metadata
    field.
    """
    if not isinstance(value, dict):
        raise serializers.ValidationError("Each evidence entry must be an object.")
    unknown = set(value) - EVIDENCE_METADATA_FIELDS
    if unknown:
        raise serializers.ValidationError(
            f"Unsupported evidence fields: {sorted(unknown)}."
        )
    evidence_type = value.get("evidence_type", "other")
    valid_types = {choice[0] for choice in EVIDENCE_TYPE_CHOICES}
    if evidence_type not in valid_types:
        raise serializers.ValidationError(
            f"evidence_type must be one of {sorted(valid_types)}."
        )
    external_reference = str(value.get("external_reference", "") or "")
    if len(external_reference) > MAX_EVIDENCE_REFERENCE_LENGTH:
        raise serializers.ValidationError(
            "external_reference is too long."
        )
    if "size" in value and value["size"] is not None:
        try:
            size = int(value["size"])
        except (TypeError, ValueError) as exc:
            raise serializers.ValidationError("size must be an integer.") from exc
        if size < 0:
            raise serializers.ValidationError("size must be non-negative.")
    sha256 = str(value.get("sha256", "") or "")
    if sha256 and (len(sha256) != 64 or any(c not in "0123456789abcdef" for c in sha256.lower())):
        raise serializers.ValidationError("sha256 must be a 64-character hex string.")
    if "captured_at" in value and value["captured_at"] not in (None, ""):
        try:
            value["captured_at"] = serializers.DateTimeField().run_validation(
                value["captured_at"]
            )
        except serializers.ValidationError as exc:
            raise serializers.ValidationError(
                {"captured_at": exc.detail}
            ) from exc
    return value


class FgpyBotMaintenanceIncidentInputSerializer(serializers.Serializer):
    """Input contract for the OpenClaw/WhatsApp bot endpoint.

    The bot may post the minimum it has; missing fields are normalized to
    safe defaults. organization_key is forced to "forestal-paraguay" and
    the cross-organization validation is enforced here.
    """

    organization_key = serializers.CharField(max_length=64, required=False, default="")
    proposal_key = serializers.CharField(max_length=128)
    source_system = serializers.CharField(max_length=100, required=False, allow_blank=True, default="openclaw")
    source_message_id = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    source_group_key = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    source_group_name = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    opened_at = serializers.DateTimeField(required=False, allow_null=True)
    occurred_at = serializers.DateTimeField(required=False, allow_null=True)
    equipment_text = serializers.CharField(required=False, allow_blank=True, default="")
    fgpy_equipment_external_id = serializers.CharField(
        max_length=64, required=False, allow_blank=True, allow_null=True, default=None
    )
    fgpy_equipment_display = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    fgpy_equipment_code = serializers.CharField(
        max_length=100, required=False, allow_blank=True, allow_null=True, default=None
    )
    incident_type = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    summary = serializers.CharField(required=False, allow_blank=True, default="")
    location = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    diagnosis = serializers.CharField(required=False, allow_blank=True, default="")
    pending = serializers.CharField(required=False, allow_blank=True, default="")
    responsible = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    operational_status = serializers.ChoiceField(
        choices=OPERATIONAL_STATUS_CHOICES, required=False, default="unknown"
    )
    management_status = serializers.ChoiceField(
        choices=MANAGEMENT_STATUS_CHOICES, required=False, default="unknown"
    )
    status = serializers.ChoiceField(
        choices=INCIDENT_STATUS_CHOICES, required=False, default="open"
    )
    event_type = serializers.ChoiceField(
        choices=EVENT_TYPE_CHOICES, required=False, default="opened"
    )
    event_description = serializers.CharField(required=False, allow_blank=True, default="")
    evidence = serializers.ListField(
        child=serializers.DictField(), required=False, default=list
    )

    def validate_organization_key(self, value):
        if value and value != FGPY_ORGANIZATION_KEY:
            raise serializers.ValidationError(
                f"Only {FGPY_ORGANIZATION_KEY} is accepted."
            )
        return FGPY_ORGANIZATION_KEY

    def validate_evidence(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("evidence must be a list.")
        if len(value) > MAX_EVIDENCE_METADATA_ENTRIES:
            raise serializers.ValidationError(
                f"Too many evidence entries (max {MAX_EVIDENCE_METADATA_ENTRIES})."
            )
        return [_validate_evidence_metadata(entry) for entry in value]

    def validate(self, attrs):
        if not attrs.get("opened_at"):
            if attrs.get("occurred_at"):
                attrs["opened_at"] = attrs["occurred_at"]
            else:
                raise serializers.ValidationError(
                    {"opened_at": ["opened_at or occurred_at is required."]}
                )
        attrs["organization_key"] = FGPY_ORGANIZATION_KEY
        return attrs
