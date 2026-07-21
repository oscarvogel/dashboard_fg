import json

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from fgpy_mantenimiento.models import (
    FGPY_ORGANIZATION_KEY,
    FgpyEquipmentAlias,
    FgpyMaintenanceEvent,
    FgpyMaintenanceEvidence,
    FgpyMaintenanceIncident,
)
from fgpy_mantenimiento.serializers import (
    FgpyBotMaintenanceIncidentInputSerializer,
    FgpyEquipmentAliasSerializer,
    FgpyMaintenanceEventSerializer,
    FgpyMaintenanceEvidenceSerializer,
    FgpyMaintenanceIncidentSerializer,
)
from fgpy_mantenimiento.services import (
    EQUIPMENT_RESOLVE_NEEDS_REVIEW,
    EQUIPMENT_RESOLVE_OK,
    EQUIPMENT_RESOLVE_UNRESOLVED,
    EQUIPMENT_RESOLVE_EXTERNAL_UNAVAILABLE,
    list_active_equipment,
    resolve_equipment,
    search_equipment,
)
from forestal_bot.permissions import OpenClawBearerPermission


def _sanitize_evidence_metadata(entry):
    """Return a dict limited to known, JSON-safe fields. Drops unknown keys.

    ``captured_at`` is preserved as a ``datetime`` when the serializer
    already normalized it, so the model can store the original evidence
    timestamp instead of dropping it.
    """
    allowed = {
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
    cleaned = {}
    for field, value in entry.items():
        if field not in allowed:
            continue
        if field == "evidence_type":
            cleaned[field] = str(value or "other") or "other"
        elif field == "size" and value is not None:
            try:
                cleaned[field] = int(value)
            except (TypeError, ValueError):
                continue
        elif field == "captured_at":
            if value in (None, ""):
                continue
            # Keep datetime objects; coerce ISO strings to datetime so the
            # model field receives a value it can persist.
            if hasattr(value, "isoformat"):
                cleaned[field] = value
            else:
                from django.utils.dateparse import parse_datetime

                parsed = parse_datetime(str(value))
                if parsed is None:
                    continue
                cleaned[field] = parsed
        else:
            if value is None:
                continue
            cleaned[field] = str(value)
    return cleaned


def _serialize_candidate_summary(candidates):
    """Return a small, JSON-safe list of candidate hints for audit logs."""
    summary = []
    for entry in candidates or []:
        summary.append(
            {
                "external_id": str(entry.get("external_id", "")),
                "display": str(entry.get("display", "")),
                "code": str(entry.get("code", "")),
                "active": bool(entry.get("active", True)),
            }
        )
    return summary


class FgpyEquipmentCatalogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "")
        limit = request.query_params.get("limit", 25 if query else 100)
        result = (
            search_equipment(query=query, limit=limit)
            if query
            else list_active_equipment(limit=limit)
        )
        http_status = status.HTTP_200_OK if result.available else status.HTTP_503_SERVICE_UNAVAILABLE
        if not result.configured:
            http_status = status.HTTP_200_OK
        return Response(result.as_dict(), status=http_status)


class FgpyMaintenanceIncidentViewSet(viewsets.ModelViewSet):
    serializer_class = FgpyMaintenanceIncidentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = FgpyMaintenanceIncident.objects.filter(
            organization_key=FGPY_ORGANIZATION_KEY
        ).prefetch_related("events", "evidence")
        for parameter, field in (
            ("status", "status"),
            ("equipment", "fgpy_equipment_external_id"),
            ("source_system", "source_system"),
        ):
            value = self.request.query_params.get(parameter)
            if value:
                queryset = queryset.filter(**{field: value})
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        proposal_key = serializer.validated_data["proposal_key"]
        try:
            with transaction.atomic():
                incident = FgpyMaintenanceIncident.objects.create(
                    **serializer.validated_data
                )
        except IntegrityError:
            incident = self.get_queryset().filter(proposal_key=proposal_key).first()
            if incident is None:
                raise
            replay = self.get_serializer(incident)
            return Response(replay.data, status=status.HTTP_200_OK)
        headers = self.get_success_headers(serializer.data)
        return Response(
            self.get_serializer(incident).data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


class FgpyMaintenanceEventViewSet(viewsets.ModelViewSet):
    serializer_class = FgpyMaintenanceEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FgpyMaintenanceEvent.objects.filter(
            incident__organization_key=FGPY_ORGANIZATION_KEY
        ).select_related("incident")

    def perform_create(self, serializer):
        get_object_or_404(
            FgpyMaintenanceIncident,
            pk=serializer.validated_data["incident"].pk,
            organization_key=FGPY_ORGANIZATION_KEY,
        )
        serializer.save()


class FgpyMaintenanceEvidenceViewSet(viewsets.ModelViewSet):
    serializer_class = FgpyMaintenanceEvidenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FgpyMaintenanceEvidence.objects.filter(
            incident__organization_key=FGPY_ORGANIZATION_KEY
        ).select_related("incident", "event")


class FgpyEquipmentAliasViewSet(viewsets.ModelViewSet):
    serializer_class = FgpyEquipmentAliasSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FgpyEquipmentAlias.objects.filter(organization_key=FGPY_ORGANIZATION_KEY)


# ---------------------------------------------------------------------------
# Bot endpoint
# ---------------------------------------------------------------------------


REPLAY_INCOMPATIBLE_FIELDS = (
    "opened_at",
    "fgpy_equipment_external_id",
)


def _payload_is_compatible(incident, payload):
    for field in REPLAY_INCOMPATIBLE_FIELDS:
        incoming = payload.get(field)
        current = getattr(incident, field, None)
        if field == "opened_at":
            if incoming and current and incoming != current:
                return False
        elif field == "fgpy_equipment_external_id":
            current_value = str(current or "")
            incoming_value = str(incoming or "")
            if current_value != incoming_value:
                return False
        else:
            if str(incoming or "") != str(current or ""):
                return False
    return True


def _build_initial_event(incident, payload, occurred_at):
    return FgpyMaintenanceEvent(
        incident=incident,
        event_type=payload.get("event_type") or "opened",
        description=payload.get("event_description") or payload.get("summary") or "",
        operational_status=payload.get("operational_status") or "unknown",
        management_status=payload.get("management_status") or "unknown",
        occurred_at=occurred_at,
        source_message_id=payload.get("source_message_id", "") or "",
        source_group_key=payload.get("source_group_key", "") or "",
        source_group_name=payload.get("source_group_name", "") or "",
    )


def _build_candidate_evidence(incident, event, candidates, error):
    payload = {
        "kind": "equipment_candidates",
        "candidates": _serialize_candidate_summary(candidates),
    }
    if error:
        payload["error"] = str(error)
    return FgpyMaintenanceEvidence(
        incident=incident,
        event=event,
        evidence_type="other",
        description="Catalog resolution required human review.",
        external_reference=json.dumps(payload, ensure_ascii=False, sort_keys=True),
        source_message_id="",
        source_group_key="",
        source_group_name="",
        mime_type="application/json",
        size=len(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
        sha256="",
        captured_at=None,
    )


def _build_evidence_metadata_records(incident, event, entries):
    records = []
    for entry in entries or []:
        cleaned = _sanitize_evidence_metadata(entry)
        if not cleaned:
            continue
        records.append(
            FgpyMaintenanceEvidence(
                incident=incident,
                event=event,
                evidence_type=cleaned.get("evidence_type", "other") or "other",
                description=cleaned.get("description", "") or "",
                external_reference=cleaned.get("external_reference", "") or "",
                mime_type=cleaned.get("mime_type", "") or "",
                size=cleaned.get("size"),
                sha256=cleaned.get("sha256", "") or "",
                source_message_id=cleaned.get("source_message_id", "") or "",
                source_group_key=cleaned.get("source_group_key", "") or "",
                source_group_name=cleaned.get("source_group_name", "") or "",
                captured_at=cleaned.get("captured_at"),
            )
        )
    return records


class FgpyMaintenanceBotIncidentView(APIView):
    """Idempotent ingest endpoint used by the OpenClaw/WhatsApp bot.

    URL: ``/api/bot/fgpy-maintenance/incidents/``

    The endpoint:
      * requires the OpenClaw bearer token (no session, no JWT fallback).
      * enforces ``organization_key = forestal-paraguay``.
      * resolves the FGPY equipment reference either from the explicit
        ``fgpy_equipment_external_id`` (authoritative) or from the FGPY
        read-only catalog when ``equipment_text`` is provided.
      * is fully idempotent on ``proposal_key``: identical or compatible
        replays return 200, incompatible replays return 409.
      * never queries Garuhape tables to resolve equipment; never writes
        to the external FGPY database.
    """

    authentication_classes = []
    permission_classes = [OpenClawBearerPermission]

    def post(self, request):
        if not isinstance(request.data, dict):
            return Response(
                {"detail": "Expected a JSON object."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = FgpyBotMaintenanceIncidentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        opened_at = payload["opened_at"]
        occurred_at = payload.get("occurred_at") or opened_at

        resolution = resolve_equipment(
            external_id=payload.get("fgpy_equipment_external_id"),
            equipment_text=payload.get("equipment_text", ""),
        )

        proposal_key = payload["proposal_key"]
        existing = FgpyMaintenanceIncident.objects.filter(
            organization_key=FGPY_ORGANIZATION_KEY, proposal_key=proposal_key
        ).first()
        if existing is not None:
            return self._handle_replay(existing, payload, opened_at, occurred_at, resolution)

        if resolution.status == EQUIPMENT_RESOLVE_OK and resolution.external_id:
            external_id = resolution.external_id
            display = payload.get("fgpy_equipment_display") or resolution.display
            code = payload.get("fgpy_equipment_code") or resolution.code
            status_value = payload.get("status") or "open"
        else:
            external_id = payload.get("fgpy_equipment_external_id") or None
            display = payload.get("fgpy_equipment_display") or ""
            code = payload.get("fgpy_equipment_code") or None
            status_value = "requires_review"

        incident = FgpyMaintenanceIncident(
            organization_key=FGPY_ORGANIZATION_KEY,
            fgpy_equipment_external_id=external_id,
            fgpy_equipment_display=display,
            fgpy_equipment_code=code,
            status=status_value,
            operational_status=payload.get("operational_status") or "unknown",
            management_status=payload.get("management_status") or "unknown",
            incident_type=payload.get("incident_type", "") or "",
            summary=payload.get("summary", "") or "",
            location=payload.get("location", "") or "",
            diagnosis=payload.get("diagnosis", "") or "",
            pending=payload.get("pending", "") or "",
            responsible=payload.get("responsible", "") or "",
            source_system=payload.get("source_system", "") or "",
            proposal_key=proposal_key,
            opened_at=opened_at,
        )

        try:
            with transaction.atomic():
                incident.save()
                event = _build_initial_event(incident, payload, occurred_at)
                event.save()
                candidates_record = None
                if resolution.status in (
                    EQUIPMENT_RESOLVE_NEEDS_REVIEW,
                    EQUIPMENT_RESOLVE_EXTERNAL_UNAVAILABLE,
                ):
                    candidates_record = _build_candidate_evidence(
                        incident, event, resolution.candidates, resolution.error
                    )
                    candidates_record.save()
                for evidence_record in _build_evidence_metadata_records(
                    incident, event, payload.get("evidence") or []
                ):
                    evidence_record.save()
        except IntegrityError:
            existing = FgpyMaintenanceIncident.objects.filter(
                organization_key=FGPY_ORGANIZATION_KEY, proposal_key=proposal_key
            ).first()
            if existing is None:
                raise
            return self._handle_replay(existing, payload, opened_at, occurred_at, resolution)

        return Response(
            FgpyMaintenanceIncidentSerializer(incident).data,
            status=status.HTTP_201_CREATED,
        )

    def _handle_replay(self, incident, payload, opened_at, occurred_at, resolution):
        if not _payload_is_compatible(incident, payload):
            return Response(
                {
                    "detail": "The proposal_key is already associated with different data.",
                    "proposal_key": incident.proposal_key,
                },
                status=status.HTTP_409_CONFLICT,
            )

        source_message_id = payload.get("source_message_id", "") or ""
        event_type = payload.get("event_type") or "update"
        duplicate_event = FgpyMaintenanceEvent.objects.filter(
            incident=incident,
            event_type=event_type,
            source_message_id=source_message_id,
        ).first()
        if duplicate_event is None:
            with transaction.atomic():
                event = _build_initial_event(incident, payload, occurred_at)
                event.save()
                for evidence_record in _build_evidence_metadata_records(
                    incident, event, payload.get("evidence") or []
                ):
                    evidence_record.save()

        return Response(
            FgpyMaintenanceIncidentSerializer(incident).data,
            status=status.HTTP_200_OK,
        )
