import json
import os
import tempfile
from contextlib import contextmanager
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from fgpy_mantenimiento.models import (
    FGPY_ORGANIZATION_KEY,
    FgpyMaintenanceEvent,
    FgpyMaintenanceEvidence,
    FgpyMaintenanceIncident,
)
from fgpy_mantenimiento.services import (
    EQUIPMENT_RESOLVE_NEEDS_REVIEW,
    EQUIPMENT_RESOLVE_OK,
    EQUIPMENT_RESOLVE_EXTERNAL_UNAVAILABLE,
    CatalogResult,
    EquipmentResolution,
)


FGPY_BOT_TOKEN = "fgpy-maint-bot-test-token"
GARUHAPE_TABLES = (
    "produccion_equipo",
    "produccion_empleado",
    "produccion_movil",
    "produccion_personal",
    "produccion_lugarcarga",
    "produccion_registroproduccion",
    "produccion_equipo_aliases",
    "produccion_unidadnegocio",
    "incidencia_equipo",
    "incidencia_personal",
    "incidencia_equipo_evento",
    "incidencias_incidenciaequipo",
    "incidencias_eventoestadoequipo",
    "incidencias_incidenciapersonal",
)


@contextmanager
def _capture_main_db_queries():
    with CaptureQueriesContext(connection) as context:
        yield context


class FgpyMaintenanceIncidentTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user("fgpy-maint")
        self.client.force_authenticate(self.user)
        self.url = reverse("fgpy_mantenimiento:incident-list")

    def payload(self, **overrides):
        data = {
            "organization_key": FGPY_ORGANIZATION_KEY,
            "fgpy_equipment_external_id": "36",
            "fgpy_equipment_display": "Skidder John Deere 548GIII-Isla Yobai",
            "fgpy_equipment_code": "jd_548",
            "status": "open",
            "operational_status": "stopped",
            "management_status": "pending_review",
            "incident_type": "mechanical",
            "summary": "No arranca",
            "location": "Isla Yobai",
            "diagnosis": "",
            "pending": "Revisar en taller",
            "responsible": "Mantenimiento FGPY",
            "source_system": "openclaw",
            "proposal_key": "maint-36-001",
            "opened_at": "2026-07-21T10:00:00-03:00",
        }
        data.update(overrides)
        return data

    def test_incident_is_saved_in_fgpy_scope_without_garuhape_foreign_keys(self):
        response = self.client.post(self.url, self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        incident = FgpyMaintenanceIncident.objects.get()
        self.assertEqual(incident.organization_key, FGPY_ORGANIZATION_KEY)
        self.assertEqual(incident.fgpy_equipment_external_id, "36")
        model_fields = {field.name for field in FgpyMaintenanceIncident._meta.fields}
        self.assertNotIn("equipo", model_fields)
        self.assertNotIn("empleado", model_fields)

    def test_rejects_other_organization_and_replay_is_idempotent(self):
        rejected = self.client.post(
            self.url,
            self.payload(organization_key="forestal-garuhape"),
            format="json",
        )
        self.assertEqual(rejected.status_code, status.HTTP_400_BAD_REQUEST)
        first = self.client.post(self.url, self.payload(), format="json")
        second = self.client.post(self.url, self.payload(summary="Texto repetido"), format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(FgpyMaintenanceIncident.objects.count(), 1)
        self.assertEqual(second.data["summary"], "No arranca")


class FgpyEquipmentCatalogTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user("fgpy-catalog")
        self.client.force_authenticate(self.user)
        self.url = reverse("fgpy_mantenimiento:equipment-catalog")

    @override_settings(FGPY_READONLY_DB_ENABLED=False)
    def test_catalog_endpoint_is_safe_when_external_database_is_disabled(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["configured"])
        self.assertEqual(response.data["results"], [])

    def test_catalog_endpoint_returns_sanitized_external_equipment_candidates(self):
        result = CatalogResult(
            configured=True,
            available=True,
            results=[
                {
                    "organization_key": FGPY_ORGANIZATION_KEY,
                    "external_id": "36",
                    "display": "Skidder John Deere 548GIII-Isla Yobai",
                    "plate": "",
                    "code": "jd_548",
                    "type": "Skidder",
                    "active": True,
                }
            ],
        )
        with patch("fgpy_mantenimiento.views.search_equipment", return_value=result):
            response = self.client.get(self.url, {"q": "jd_548"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["external_id"], "36")
        serialized = str(response.data).lower()
        self.assertNotIn("nro_chasis", serialized)
        self.assertNotIn("nro_motor", serialized)
        self.assertNotIn("empleados", serialized)


@override_settings(OPENCLAW_INGEST_TOKEN=FGPY_BOT_TOKEN)
class FgpyMaintenanceBotEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("fgpy_mantenimiento_bot:bot-incident-list")
        self.bot_headers = {"HTTP_AUTHORIZATION": f"Bearer {FGPY_BOT_TOKEN}"}

    def _payload(self, **overrides):
        data = {
            "organization_key": FGPY_ORGANIZATION_KEY,
            "proposal_key": "bot-maint-001",
            "source_system": "openclaw",
            "source_message_id": "wa-msg-1",
            "source_group_key": "choferes-fgpy",
            "source_group_name": "Choferes FGPY",
            "opened_at": "2026-07-21T10:00:00-03:00",
            "occurred_at": "2026-07-21T10:00:00-03:00",
            "equipment_text": "",
            "fgpy_equipment_external_id": "36",
            "fgpy_equipment_display": "Skidder John Deere 548GIII",
            "fgpy_equipment_code": "jd_548",
            "incident_type": "mechanical",
            "summary": "No arranca",
            "location": "Isla Yobai",
            "diagnosis": "",
            "pending": "Revisar en taller",
            "responsible": "Mantenimiento FGPY",
            "operational_status": "stopped",
            "management_status": "pending_review",
            "status": "open",
            "event_type": "opened",
            "event_description": "Mensaje inicial desde WhatsApp",
            "evidence": [],
        }
        data.update(overrides)
        return data

    def test_post_without_token_returns_401_or_403(self):
        response = self.client.post(
            self.url, self._payload(), format="json"
        )
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_post_with_wrong_token_returns_401_or_403(self):
        response = self.client.post(
            self.url,
            self._payload(),
            format="json",
            HTTP_AUTHORIZATION="Bearer nope",
        )
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    @override_settings(FGPY_READONLY_DB_ENABLED=False)
    def test_post_with_token_creates_fgpy_incident_and_initial_event(self):
        response = self.client.post(
            self.url, self._payload(), format="json", **self.bot_headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        incident = FgpyMaintenanceIncident.objects.get()
        self.assertEqual(incident.organization_key, FGPY_ORGANIZATION_KEY)
        self.assertEqual(incident.fgpy_equipment_external_id, "36")
        self.assertEqual(incident.fgpy_equipment_display, "Skidder John Deere 548GIII")
        self.assertEqual(incident.status, "open")
        events = list(incident.events.all())
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "opened")
        self.assertEqual(events[0].source_message_id, "wa-msg-1")

    def test_post_with_other_organization_returns_400(self):
        response = self.client.post(
            self.url,
            self._payload(organization_key="forestal-garuhape"),
            format="json",
            **self.bot_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(FgpyMaintenanceIncident.objects.exists())

    @override_settings(FGPY_READONLY_DB_ENABLED=False)
    def test_idempotent_replay_returns_200_and_does_not_duplicate(self):
        first = self.client.post(
            self.url, self._payload(), format="json", **self.bot_headers
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        second = self.client.post(
            self.url,
            self._payload(summary="Texto reenviado"),
            format="json",
            **self.bot_headers,
        )
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(FgpyMaintenanceIncident.objects.count(), 1)
        self.assertEqual(second.data["summary"], "No arranca")
        self.assertEqual(FgpyMaintenanceEvent.objects.count(), 1)

    @override_settings(FGPY_READONLY_DB_ENABLED=False)
    def test_idempotent_replay_with_new_message_adds_event_only_once(self):
        first = self.client.post(
            self.url, self._payload(), format="json", **self.bot_headers
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        replay = self.client.post(
            self.url,
            self._payload(
                source_message_id="wa-msg-2",
                event_type="update",
                event_description="Nueva novedad",
            ),
            format="json",
            **self.bot_headers,
        )
        self.assertEqual(replay.status_code, status.HTTP_200_OK)
        self.assertEqual(FgpyMaintenanceIncident.objects.count(), 1)
        self.assertEqual(FgpyMaintenanceEvent.objects.count(), 2)
        third = self.client.post(
            self.url,
            self._payload(
                source_message_id="wa-msg-2",
                event_type="update",
                event_description="Reintento",
            ),
            format="json",
            **self.bot_headers,
        )
        self.assertEqual(third.status_code, status.HTTP_200_OK)
        self.assertEqual(FgpyMaintenanceEvent.objects.count(), 2)

    @override_settings(FGPY_READONLY_DB_ENABLED=False)
    def test_incompatible_replay_returns_409(self):
        first = self.client.post(
            self.url, self._payload(), format="json", **self.bot_headers
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        conflict = self.client.post(
            self.url,
            self._payload(fgpy_equipment_external_id="99", opened_at="2026-07-22T11:00:00-03:00"),
            format="json",
            **self.bot_headers,
        )
        self.assertEqual(conflict.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(FgpyMaintenanceIncident.objects.count(), 1)

    @override_settings(FGPY_READONLY_DB_ENABLED=False)
    def test_equipment_text_with_unique_catalog_match_resolves_equipment(self):
        resolution = EquipmentResolution(
            status=EQUIPMENT_RESOLVE_OK,
            external_id="77",
            display="Cargador Volvo L120",
            code="volvo_l120",
            candidates=[],
        )
        with patch(
            "fgpy_mantenimiento.views.resolve_equipment", return_value=resolution
        ) as mocked:
            response = self.client.post(
                self.url,
                self._payload(
                    fgpy_equipment_external_id="",
                    fgpy_equipment_display="",
                    fgpy_equipment_code="",
                    equipment_text="volvo l120",
                ),
                format="json",
                **self.bot_headers,
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(mocked.call_count, 1)
        incident = FgpyMaintenanceIncident.objects.get()
        self.assertEqual(incident.fgpy_equipment_external_id, "77")
        self.assertEqual(incident.fgpy_equipment_display, "Cargador Volvo L120")
        self.assertEqual(incident.fgpy_equipment_code, "volvo_l120")

    @override_settings(FGPY_READONLY_DB_ENABLED=True)
    def test_equipment_text_with_multiple_candidates_marks_requires_review(self):
        resolution = EquipmentResolution(
            status=EQUIPMENT_RESOLVE_NEEDS_REVIEW,
            external_id=None,
            display="",
            code=None,
            candidates=[
                {
                    "external_id": "12",
                    "display": "Skidder A",
                    "code": "sa",
                    "active": True,
                },
                {
                    "external_id": "13",
                    "display": "Skidder B",
                    "code": "sb",
                    "active": True,
                },
            ],
            error="",
        )
        with patch(
            "fgpy_mantenimiento.views.resolve_equipment", return_value=resolution
        ):
            response = self.client.post(
                self.url,
                self._payload(
                    fgpy_equipment_external_id="",
                    fgpy_equipment_display="",
                    fgpy_equipment_code="",
                    equipment_text="skidder",
                ),
                format="json",
                **self.bot_headers,
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        incident = FgpyMaintenanceIncident.objects.get()
        self.assertEqual(incident.status, "requires_review")
        self.assertIsNone(incident.fgpy_equipment_external_id)
        evidence_qs = incident.evidence.all()
        self.assertEqual(evidence_qs.count(), 1)
        record = evidence_qs.first()
        payload = json.loads(record.external_reference)
        self.assertEqual(payload["kind"], "equipment_candidates")
        self.assertEqual({c["external_id"] for c in payload["candidates"]}, {"12", "13"})
        self.assertEqual(record.evidence_type, "other")

    @override_settings(FGPY_READONLY_DB_ENABLED=False)
    def test_equipment_text_with_no_catalog_configured_still_creates_review_incident(self):
        resolution = EquipmentResolution(
            status=EQUIPMENT_RESOLVE_EXTERNAL_UNAVAILABLE,
            external_id=None,
            display="",
            code=None,
            candidates=[],
            error="not_configured",
        )
        with patch(
            "fgpy_mantenimiento.views.resolve_equipment", return_value=resolution
        ):
            response = self.client.post(
                self.url,
                self._payload(
                    fgpy_equipment_external_id="",
                    fgpy_equipment_display="",
                    fgpy_equipment_code="",
                    equipment_text="skidder",
                ),
                format="json",
                **self.bot_headers,
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        incident = FgpyMaintenanceIncident.objects.get()
        self.assertEqual(incident.status, "requires_review")

    @override_settings(FGPY_READONLY_DB_ENABLED=False)
    def test_evidence_metadata_is_stored_without_files(self):
        response = self.client.post(
            self.url,
            self._payload(
                evidence=[
                    {
                        "evidence_type": "image",
                        "description": "Foto del skidder varado",
                        "external_reference": "https://example.invalid/img/1.jpg",
                        "mime_type": "image/jpeg",
                        "size": 1024,
                        "sha256": "0" * 64,
                        "source_message_id": "wa-msg-1",
                        "source_group_key": "choferes-fgpy",
                        "source_group_name": "Choferes FGPY",
                    }
                ]
            ),
            format="json",
            **self.bot_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        incident = FgpyMaintenanceIncident.objects.get()
        evidence = FgpyMaintenanceEvidence.objects.filter(incident=incident)
        self.assertEqual(evidence.count(), 1)
        record = evidence.get()
        self.assertEqual(record.evidence_type, "image")
        self.assertEqual(record.description, "Foto del skidder varado")
        self.assertEqual(record.size, 1024)
        self.assertEqual(record.sha256, "0" * 64)

    @override_settings(FGPY_READONLY_DB_ENABLED=False)
    def test_evidence_metadata_preserves_captured_at(self):
        from datetime import timezone as dt_timezone

        from django.utils.dateparse import parse_datetime

        original_iso = "2026-07-21T11:23:45-03:00"
        response = self.client.post(
            self.url,
            self._payload(
                evidence=[
                    {
                        "evidence_type": "image",
                        "description": "Foto con timestamp",
                        "external_reference": "https://example.invalid/img/ts.jpg",
                        "mime_type": "image/jpeg",
                        "size": 2048,
                        "sha256": "1" * 64,
                        "source_message_id": "wa-msg-1",
                        "source_group_key": "choferes-fgpy",
                        "source_group_name": "Choferes FGPY",
                        "captured_at": original_iso,
                    }
                ]
            ),
            format="json",
            **self.bot_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        record = FgpyMaintenanceEvidence.objects.get()
        self.assertIsNotNone(record.captured_at)
        # Compare the instants, not the timezone representation: Django
        # stores DateTimeField in UTC when USE_TZ is on.
        expected_utc = parse_datetime(original_iso).astimezone(dt_timezone.utc)
        self.assertEqual(record.captured_at.utcoffset(), dt_timezone.utc.utcoffset(None))
        self.assertEqual(record.captured_at, expected_utc)
        # Other fields keep working.
        self.assertEqual(record.size, 2048)
        self.assertEqual(record.sha256, "1" * 64)

    @override_settings(FGPY_READONLY_DB_ENABLED=False)
    def test_evidence_metadata_rejects_invalid_captured_at(self):
        response = self.client.post(
            self.url,
            self._payload(
                evidence=[
                    {
                        "evidence_type": "image",
                        "description": "captured_at inválido",
                        "external_reference": "x",
                        "captured_at": "ayer a la tarde",
                    }
                ]
            ),
            format="json",
            **self.bot_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(FgpyMaintenanceEvidence.objects.exists())

    @override_settings(FGPY_READONLY_DB_ENABLED=False)
    def test_evidence_rejects_unsafe_payload(self):
        response = self.client.post(
            self.url,
            self._payload(evidence=[{"evidence_type": "image", "raw_file": b"binary"}]),
            format="json",
            **self.bot_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(FGPY_READONLY_DB_ENABLED=False)
    def test_bot_endpoint_does_not_query_garuhape_tables_to_resolve_equipment(self):
        resolution = EquipmentResolution(
            status=EQUIPMENT_RESOLVE_OK,
            external_id="36",
            display="Skidder John Deere",
            code="jd_548",
            candidates=[],
        )
        with patch(
            "fgpy_mantenimiento.views.resolve_equipment", return_value=resolution
        ):
            with _capture_main_db_queries() as queries:
                response = self.client.post(
                    self.url, self._payload(), format="json", **self.bot_headers
                )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        rendered = "\n".join(query["sql"] for query in queries.captured_queries).lower()
        for table in GARUHAPE_TABLES:
            self.assertNotIn(
                table,
                rendered,
                f"Garuhape table '{table}' was queried while resolving FGPY equipment.",
            )

    @override_settings(FGPY_READONLY_DB_ENABLED=True)
    def test_resolve_equipment_does_not_touch_garuhape_models(self):
        # Even when the caller only passes equipment_text, the resolution
        # helper must never import or query Garuhape models.
        from fgpy_mantenimiento import services

        catalog = CatalogResult(
            configured=True,
            available=True,
            results=[
                {
                    "organization_key": FGPY_ORGANIZATION_KEY,
                    "external_id": "55",
                    "display": "Tractor FGPY 55",
                    "plate": "",
                    "code": "t55",
                    "type": "Tractor",
                    "active": True,
                }
            ],
        )
        with patch.object(services, "is_fgpy_readonly_configured", return_value=True), \
             patch.object(services, "search_equipment", return_value=catalog) as mocked:
            with _capture_main_db_queries() as queries:
                resolution = services.resolve_equipment(equipment_text="t55")
        self.assertEqual(resolution.status, EQUIPMENT_RESOLVE_OK)
        self.assertEqual(resolution.external_id, "55")
        self.assertEqual(mocked.call_count, 1)
        rendered = "\n".join(query["sql"] for query in queries.captured_queries).lower()
        for table in GARUHAPE_TABLES:
            self.assertNotIn(
                table,
                rendered,
                f"Garuhape table '{table}' was queried by the equipment resolver.",
            )

    def test_credentials_and_env_files_are_never_read(self):
        vault_path = os.path.join(tempfile.gettempdir(), "fgpy_db.env")
        with open(vault_path, "w", encoding="utf-8") as handle:
            handle.write("FGPY_DB_PASSWORD=should-not-appear")
        with override_settings(FGPY_READONLY_DB_ENABLED=False):
            with patch(
                "fgpy_mantenimiento.views.resolve_equipment",
                return_value=EquipmentResolution(
                    status=EQUIPMENT_RESOLVE_OK,
                    external_id="36",
                    display="",
                    code=None,
                    candidates=[],
                ),
            ):
                response = self.client.post(
                    self.url, self._payload(), format="json", **self.bot_headers
                )
        os.unlink(vault_path)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        body = json.dumps(response.data, default=str)
        self.assertNotIn("should-not-appear", body)
        self.assertNotIn("FGPY_DB_PASSWORD", body)
        self.assertNotIn(vault_path, body)
