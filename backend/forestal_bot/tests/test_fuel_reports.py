import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, connection, transaction
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from forestal_bot.models import (
    FuelReport,
    FuelReportEvidence,
    FuelReportRevision,
    FgpyDriver,
    FgpyVehicle,
    WhatsAppMessage,
)


@override_settings(
    OPENCLAW_INGEST_TOKEN="fuel-test-token",
    FGPY_IDENTITY_HASH_KEY="fuel-test-private-hmac-key",
)
class FuelReportAPITests(APITestCase):
    def setUp(self):
        self.media_temp = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_temp.name)
        self.media_override.enable()
        self.bot_headers = {"HTTP_AUTHORIZATION": "Bearer fuel-test-token"}
        self.user = get_user_model().objects.create_user("reviewer", password="safe-test")
        self.vehicle = FgpyVehicle.objects.create(
            original_plate="AA 123 BB", normalized_plate="AA123BB",
            description="Camión 1", created_via="user", status="confirmed",
        )
        self.driver = FgpyDriver.objects.create(
            reported_name="Chofer Prueba", normalized_name="CHOFER PRUEBA",
            created_via="user", status="confirmed",
        )
        self.receipt = self.message("receipt-1", "Carga 100 litros")
        self.dashboard = self.message("dashboard-1", "Odómetro 12500")
        self.list_url = reverse("forestal_bot_api:fuel-report-list")

    def tearDown(self):
        self.media_override.disable()
        self.media_temp.cleanup()
        super().tearDown()

    def message(self, message_id, body, group_jid="120363420163225425@g.us"):
        return WhatsAppMessage.objects.create(
            account_id="fgpy",
            group_jid=group_jid,
            message_id=message_id,
            timestamp="2026-07-20T10:00:00-03:00",
            body=body,
            image_description="Lectura automática original",
            raw_json={"message": message_id},
        )

    def payload(self, key="fuel-1", **overrides):
        data = {
            "organization_key": "forestal-paraguay",
            "origin_group_key": "choferes-fgpy",
            "idempotency_key": key,
            "event_at": "2026-07-20T10:00:00-03:00",
            "vehicle": self.vehicle.pk,
            "driver": self.driver.pk,
            "liters": "100.00",
            "odometer_total": "12500.00",
            "receipt_number": "0001",
            "overall_confidence": "0.95",
            "field_confidence": {
                "vehicle": 0.95,
                "liters": 0.95,
                "odometer_total": 0.95,
            },
            "original_extraction": {"liters_raw": "100 L", "odometer_raw": "12500"},
            "source_messages": [
                {"message_id": self.receipt.pk, "role": "receipt", "position": 0},
                {"message_id": self.dashboard.pk, "role": "dashboard", "position": 1},
            ],
        }
        data.update(overrides)
        return data

    def create_report(self, **overrides):
        return self.client.post(
            self.list_url, self.payload(**overrides), format="json", **self.bot_headers
        )

    def multipart_payload(self, key, files, **overrides):
        payload = self.payload(key=key, **overrides)
        for field in (
            "source_messages", "field_confidence", "original_extraction",
            "inconsistencies", "evidence_types", "evidence_message_ids",
        ):
            if field in payload:
                payload[field] = __import__("json").dumps(payload[field])
        payload["evidence_files"] = files
        return payload

    def media_files(self):
        return [path for path in Path(self.media_temp.name).rglob("*") if path.is_file()]

    def test_authentication_is_required_and_garuhape_is_rejected(self):
        response = self.client.post(self.list_url, self.payload(), format="json")
        self.assertIn(
            response.status_code,
            {status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN},
        )
        response = self.client.post(
            self.list_url,
            self.payload(organization_key="forestal-garuhape"),
            format="json",
            **self.bot_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_two_messages_create_one_report_without_copying_source_content(self):
        response = self.create_report()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        report = FuelReport.objects.get()
        self.assertEqual(report.source_links.count(), 2)
        model_fields = {field.name for field in FuelReport._meta.fields}
        self.assertTrue(
            {"body", "media_path", "transcription", "image_description", "raw_json"}.isdisjoint(
                model_fields
            )
        )
        self.assertEqual(FuelReport._meta.db_table, "forestal_bot_fuel_report")
        self.assertEqual(
            report.source_links.model._meta.db_table,
            "forestal_bot_fuel_report_source_message",
        )
        self.assertIs(
            FuelReport._meta.get_field("vehicle").related_model, FgpyVehicle
        )
        self.assertIs(
            FuelReport._meta.get_field("driver").related_model, FgpyDriver
        )

    def test_repeat_is_idempotent_and_does_not_overwrite_human_correction(self):
        first = self.create_report()
        report = FuelReport.objects.get(pk=first.data["id"])
        report.liters = 101
        report.status = "corrected"
        report.save()
        repeated = self.create_report()
        report.refresh_from_db()
        self.assertEqual(repeated.status_code, status.HTTP_200_OK)
        self.assertEqual(FuelReport.objects.count(), 1)
        self.assertEqual(report.liters, 101)
        self.assertEqual(report.status, "corrected")
        self.assertEqual(report.source_links.count(), 2)

    def test_fuel_integrity_conflict_recovers_winner_or_returns_409(self):
        created = self.create_report(key="race-fuel")
        winner = FuelReport.objects.get(pk=created.data["id"])
        with patch("forestal_bot.views._fuel_existing_by_key", side_effect=[None, winner]), patch(
            "forestal_bot.views.FuelReport.objects.create", side_effect=IntegrityError("race")
        ):
            same = self.create_report(key="race-fuel")
        self.assertEqual(same.status_code, status.HTTP_200_OK)
        self.assertEqual(same.data["id"], str(winner.pk))

        other = self.message("other-race-message", "Otra carga")
        with patch("forestal_bot.views._fuel_existing_by_key", side_effect=[None, winner]), patch(
            "forestal_bot.views.FuelReport.objects.create", side_effect=IntegrityError("race")
        ):
            conflict = self.create_report(
                key="race-fuel",
                source_messages=[{"message_id": other.pk, "role": "initial", "position": 0}],
            )
        self.assertEqual(conflict.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(FuelReport.objects.filter(idempotency_key="race-fuel").count(), 1)

    def test_incomplete_and_low_confidence_report_requires_review(self):
        response = self.create_report(
            key="pending",
            vehicle=None,
            liters=None,
            odometer_total=None,
            field_confidence={"vehicle": 0.2, "liters": 0.2, "odometer_total": 0.2},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "requires_review")
        self.assertIn("missing_vehicle", response.data["inconsistencies"])
        self.assertIn("low_confidence_odometer", response.data["inconsistencies"])

    def test_odometer_regression_and_duplicate_receipt_are_review_flags(self):
        existing = FuelReport.objects.create(
            organization_key="forestal-paraguay",
            origin_group_key="choferes-fgpy",
            idempotency_key="old",
            event_at="2026-07-19T10:00:00-03:00",
            vehicle=self.vehicle,
            liters=50,
            odometer_total=13000,
            receipt_number="0001",
            status="confirmed",
        )
        self.assertIsNotNone(existing.pk)
        response = self.create_report()
        self.assertIn("odometer_regression", response.data["inconsistencies"])
        self.assertIn("duplicate_receipt", response.data["inconsistencies"])

    def test_human_correction_confirmation_and_rejection_are_audited(self):
        created = self.create_report(key="review")
        detail = reverse("forestal_bot_api:fuel-report-detail", args=[created.data["id"]])
        self.client.force_authenticate(self.user)
        corrected = self.client.patch(
            detail,
            {
                "action": "correct",
                "reason": "Lectura verificada",
                "changes": {"liters": "102.00"},
            },
            format="json",
        )
        self.assertEqual(corrected.status_code, status.HTTP_200_OK)
        self.assertEqual(corrected.data["status"], "corrected")
        confirmed = self.client.patch(detail, {"action": "confirm", "reason": ""}, format="json")
        self.assertEqual(confirmed.status_code, status.HTTP_200_OK)
        self.assertEqual(confirmed.data["status"], "confirmed")
        rejected = self.client.patch(
            detail, {"action": "reject", "reason": "No corresponde a una carga"}, format="json"
        )
        self.assertEqual(rejected.status_code, status.HTTP_200_OK)
        self.assertEqual(rejected.data["status"], "rejected")
        self.assertTrue(FuelReportRevision.objects.filter(field_name="liters").exists())
        self.assertGreaterEqual(FuelReportRevision.objects.filter(field_name="status").count(), 3)

    def test_listing_is_paginated_filtered_and_jwt_only_review_is_enforced(self):
        created = self.create_report()
        detail = reverse("forestal_bot_api:fuel-report-detail", args=[created.data["id"]])
        denied = self.client.patch(
            detail,
            {"action": "reject", "reason": "test"},
            format="json",
            **self.bot_headers,
        )
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.user)
        response = self.client.get(
            self.list_url,
            {"status": "received", "vehicle": self.vehicle.pk, "page_size": 1},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertEqual(len(response.data["results"]), 1)

    def test_invalid_file_is_rejected(self):
        invalid = SimpleUploadedFile("bad.jpg", b"not-an-image", content_type="image/jpeg")
        payload = self.payload(key="bad-file")
        payload["source_messages"] = __import__("json").dumps(payload["source_messages"])
        payload["field_confidence"] = __import__("json").dumps(payload["field_confidence"])
        payload["original_extraction"] = __import__("json").dumps(payload["original_extraction"])
        response = self.client.post(
            self.list_url,
            {**payload, "evidence_files": invalid},
            format="multipart",
            **self.bot_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(FuelReport.objects.count(), 0)
        self.assertEqual(FuelReportEvidence.objects.count(), 0)

    def test_valid_jpeg_png_download_headers_and_private_response(self):
        jpeg = SimpleUploadedFile("receipt.jpg", b"\xff\xd8\xffvalid-jpeg", content_type="image/jpeg")
        png = SimpleUploadedFile("dash.png", b"\x89PNG\r\n\x1a\nvalid-png", content_type="image/png")
        response = self.client.post(
            self.list_url,
            self.multipart_payload(
                "valid-images", [jpeg, png],
                evidence_types=["receipt", "dashboard"],
                evidence_message_ids=[self.receipt.pk, self.dashboard.pk],
            ),
            format="multipart", **self.bot_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual([item["mime_type"] for item in response.data["evidence"]], ["image/jpeg", "image/png"])
        serialized = __import__("json").dumps(response.data, default=str)
        self.assertNotIn(self.media_temp.name, serialized)
        self.assertNotIn("private_media", serialized)
        self.assertNotIn("file", response.data["evidence"][0])
        download_url = response.data["evidence"][0]["download_url"]
        unauthenticated = self.client.get(download_url)
        self.assertIn(unauthenticated.status_code, {status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN})
        downloaded = self.client.get(download_url, **self.bot_headers)
        self.assertEqual(downloaded.status_code, status.HTTP_200_OK)
        self.assertEqual(downloaded["Content-Type"], "image/jpeg")
        self.assertEqual(downloaded["Cache-Control"], "private, no-store")
        self.assertTrue(b"".join(downloaded.streaming_content).startswith(b"\xff\xd8\xff"))
        downloaded.close()

    def test_oversized_and_duplicate_request_files_are_rejected_without_files(self):
        with override_settings(FUEL_EVIDENCE_MAX_BYTES=8):
            oversized = SimpleUploadedFile("large.png", b"\x89PNG\r\n\x1a\nextra", content_type="image/png")
            response = self.client.post(
                self.list_url, self.multipart_payload("large", [oversized]),
                format="multipart", **self.bot_headers,
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        content = b"\xff\xd8\xffsame"
        duplicate = self.client.post(
            self.list_url,
            self.multipart_payload(
                "same-request",
                [
                    SimpleUploadedFile("a.jpg", content, content_type="image/jpeg"),
                    SimpleUploadedFile("b.jpg", content, content_type="image/jpeg"),
                ],
            ),
            format="multipart", **self.bot_headers,
        )
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.media_files(), [])

    def test_duplicate_evidence_between_reports_is_flagged_without_second_file(self):
        content = b"\xff\xd8\xffshared"
        first = self.client.post(
            self.list_url,
            self.multipart_payload("evidence-first", [SimpleUploadedFile("a.jpg", content)]),
            format="multipart", **self.bot_headers,
        )
        second_message = self.message("second-evidence-message", "Carga repetida")
        second = self.client.post(
            self.list_url,
            self.multipart_payload(
                "evidence-second", [SimpleUploadedFile("b.jpg", content)],
                source_messages=[{"message_id": second_message.pk, "role": "receipt", "position": 0}],
                receipt_number="0002",
            ),
            format="multipart", **self.bot_headers,
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertIn("duplicate_evidence", second.data["inconsistencies"])
        self.assertEqual(FuelReportEvidence.objects.count(), 1)
        self.assertEqual(len(self.media_files()), 1)

    def test_database_failure_after_storage_removes_physical_file(self):
        self.client.raise_request_exception = False
        with patch(
            "forestal_bot.views.FuelReportEvidence.objects.create",
            side_effect=IntegrityError("evidence insert failed"),
        ):
            response = self.client.post(
                self.list_url,
                self.multipart_payload(
                    "storage-rollback",
                    [SimpleUploadedFile("rollback.jpg", b"\xff\xd8\xffrollback")],
                ),
                format="multipart", **self.bot_headers,
            )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(FuelReport.objects.filter(idempotency_key="storage-rollback").exists())
        self.assertEqual(self.media_files(), [])

    def test_idempotency_conflict_with_upload_leaves_no_orphan_file(self):
        winner_response = self.create_report(key="upload-race")
        winner = FuelReport.objects.get(pk=winner_response.data["id"])
        with patch("forestal_bot.views._fuel_existing_by_key", side_effect=[None, winner]), patch(
            "forestal_bot.views.FuelReport.objects.create", side_effect=IntegrityError("race")
        ):
            response = self.client.post(
                self.list_url,
                self.multipart_payload(
                    "upload-race", [SimpleUploadedFile("race.jpg", b"\xff\xd8\xffrace")]
                ),
                format="multipart", **self.bot_headers,
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.media_files(), [])

    def test_flow_does_not_query_legacy_vehicle_driver_or_fuel_tables(self):
        with CaptureQueriesContext(connection) as captured:
            response = self.create_report(key="no-legacy")
            self.client.force_authenticate(self.user)
            self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        sql = " ".join(query["sql"].lower() for query in captured.captured_queries)
        self.assertNotIn("moviles", sql)
        self.assertNotIn("personal", sql)
        self.assertNotIn("cargacomb", sql)

    def test_general_and_repair_messages_do_not_create_specialized_records(self):
        self.message("general", "Coordinamos la entrega")
        self.message("repair", "Cambio de diafragma del pulmón de freno")
        self.assertEqual(FuelReport.objects.count(), 0)


@override_settings(
    OPENCLAW_INGEST_TOKEN="fuel-test-token",
    FGPY_IDENTITY_HASH_KEY="catalog-test-private-hmac-key",
)
class FgpyCatalogAPITests(APITestCase):
    def setUp(self):
        self.bot_headers = {"HTTP_AUTHORIZATION": "Bearer fuel-test-token"}
        self.user = get_user_model().objects.create_user("catalog-reviewer")
        self.message = WhatsAppMessage.objects.create(
            account_id="fgpy", group_jid="120363420163225425@g.us",
            message_id="catalog-source", timestamp="2026-07-20T10:00:00-03:00",
            raw_json={},
        )
        self.vehicle_url = reverse("forestal_bot_api:fgpy-vehicle-list")
        self.driver_url = reverse("forestal_bot_api:fgpy-driver-list")

    def test_bot_proposals_are_idempotent_pending_and_do_not_learn_aliases(self):
        vehicle_payload = {
            "organization_key": "forestal-paraguay", "proposal_key": "vehicle-1",
            "original_plate": "AA 123 BB", "description": "Camión informado",
            "confirmed_aliases": ["NO DEBE APRENDERSE"],
            "initial_source_message": self.message.pk,
        }
        first = self.client.post(self.vehicle_url, vehicle_payload, format="json", **self.bot_headers)
        repeated = self.client.post(self.vehicle_url, vehicle_payload, format="json", **self.bot_headers)
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(repeated.status_code, status.HTTP_200_OK)
        self.assertEqual(FgpyVehicle.objects.count(), 1)
        vehicle = FgpyVehicle.objects.get()
        self.assertEqual(vehicle.status, "pending")
        self.assertEqual(vehicle.confirmed_aliases, [])
        self.assertEqual(vehicle.original_plate, "AA 123 BB")

    def test_catalog_integrity_conflict_returns_200_or_409_without_500(self):
        winner = FgpyVehicle.objects.create(
            original_plate="AA 123 BB", normalized_plate="AA123BB",
            description="Camión informado", created_via="bot",
            proposal_key="vehicle-race", initial_source_message=self.message,
        )
        payload = {
            "organization_key": "forestal-paraguay", "proposal_key": "vehicle-race",
            "original_plate": "AA 123 BB", "description": "Camión informado",
            "initial_source_message": self.message.pk,
        }
        with patch("forestal_bot.views._catalog_existing_by_key", side_effect=[None, winner]), patch(
            "forestal_bot.views.FgpyVehicle.objects.create", side_effect=IntegrityError("race")
        ):
            same = self.client.post(self.vehicle_url, payload, format="json", **self.bot_headers)
        self.assertEqual(same.status_code, status.HTTP_200_OK)
        with patch("forestal_bot.views._catalog_existing_by_key", side_effect=[None, winner]), patch(
            "forestal_bot.views.FgpyVehicle.objects.create", side_effect=IntegrityError("race")
        ):
            reused = self.client.post(
                self.vehicle_url,
                {**payload, "description": "Otro vehículo"},
                format="json", **self.bot_headers,
            )
        self.assertEqual(reused.status_code, status.HTTP_409_CONFLICT)
        other_message = WhatsAppMessage.objects.create(
            account_id="fgpy", group_jid="120363420163225425@g.us",
            message_id="other-catalog-source", timestamp="2026-07-20T11:00:00-03:00",
            raw_json={},
        )
        with patch("forestal_bot.views._catalog_existing_by_key", side_effect=[None, winner]), patch(
            "forestal_bot.views.FgpyVehicle.objects.create", side_effect=IntegrityError("race")
        ):
            reused_message = self.client.post(
                self.vehicle_url,
                {**payload, "initial_source_message": other_message.pk},
                format="json", **self.bot_headers,
            )
        self.assertEqual(reused_message.status_code, status.HTTP_409_CONFLICT)

    def test_hmac_identity_is_deterministic_private_and_key_is_required(self):
        def propose(key, sender):
            return self.client.post(
                self.driver_url,
                {
                    "organization_key": "forestal-paraguay", "proposal_key": key,
                    "reported_name": key, "whatsapp_sender_identifier": sender,
                    "initial_source_message": self.message.pk,
                },
                format="json", **self.bot_headers,
            )

        first = propose("hmac-a", "sender-a")
        second = propose("hmac-b", "sender-b")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        hashes = list(
            FgpyDriver.objects.filter(proposal_key__in=["hmac-a", "hmac-b"])
            .order_by("proposal_key")
            .values_list("whatsapp_sender_identifier_hash", flat=True)
        )
        expected = __import__("hmac").new(
            b"catalog-test-private-hmac-key", b"sender-a", __import__("hashlib").sha256
        ).hexdigest()
        self.assertEqual(hashes[0], expected)
        self.assertNotEqual(hashes[0], hashes[1])
        self.assertNotIn("sender-a", str(first.data))
        self.assertNotIn(expected, str(first.data))
        with override_settings(FGPY_IDENTITY_HASH_KEY=""):
            missing_key = propose("hmac-missing", "sender-c")
        self.assertEqual(missing_key.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(FgpyDriver.objects.filter(proposal_key="hmac-missing").exists())

    def test_pending_vehicle_and_driver_can_only_be_confirmed_by_user(self):
        vehicle = FgpyVehicle.objects.create(
            original_plate="AB 111 CD", normalized_plate="AB111CD",
            description="Unidad", created_via="bot", proposal_key="v-confirm",
        )
        driver = FgpyDriver.objects.create(
            reported_name="Juan Pérez", normalized_name="JUAN PEREZ",
            created_via="bot", proposal_key="d-confirm",
        )
        vehicle_detail = reverse("forestal_bot_api:fgpy-vehicle-detail", args=[vehicle.pk])
        denied = self.client.patch(
            vehicle_detail, {"action": "confirm"}, format="json", **self.bot_headers
        )
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.user)
        confirmed_vehicle = self.client.patch(
            vehicle_detail,
            {"action": "confirm", "confirmed_aliases": ["Camión uno"]},
            format="json",
        )
        confirmed_driver = self.client.patch(
            reverse("forestal_bot_api:fgpy-driver-detail", args=[driver.pk]),
            {"action": "confirm", "confirmed_aliases": ["Juan P."]},
            format="json",
        )
        self.assertEqual(confirmed_vehicle.data["status"], "confirmed")
        self.assertEqual(confirmed_driver.data["status"], "confirmed")
        self.assertEqual(confirmed_vehicle.data["confirmed_aliases"], ["Camión uno"])
        self.assertEqual(confirmed_driver.data["confirmed_aliases"], ["Juan P."])

    def test_similar_driver_names_are_not_automatically_merged_or_exposed(self):
        for key, name, sender in (
            ("driver-a", "Juan Perez", "private-a"),
            ("driver-b", "Juan Pérez", "private-b"),
        ):
            response = self.client.post(
                self.driver_url,
                {
                    "organization_key": "forestal-paraguay", "proposal_key": key,
                    "reported_name": name, "whatsapp_sender_identifier": sender,
                    "initial_source_message": self.message.pk,
                },
                format="json", **self.bot_headers,
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertNotIn("whatsapp_sender_identifier", response.data)
            self.assertNotIn(sender, FgpyDriver.objects.get(proposal_key=key).whatsapp_sender_identifier_hash)
        self.assertEqual(FgpyDriver.objects.count(), 2)

    def test_catalog_rejects_other_organizations(self):
        response = self.client.post(
            self.driver_url,
            {"organization_key": "forestal-garuhape", "proposal_key": "bad", "reported_name": "X"},
            format="json", **self.bot_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mysql_compatible_unique_keys_allow_blank_proposals_and_reject_duplicates(self):
        FgpyDriver.objects.create(reported_name="Uno", created_via="user")
        FgpyDriver.objects.create(reported_name="Dos", created_via="user")
        FgpyDriver.objects.create(
            reported_name="Tres", created_via="bot", proposal_key="same-proposal"
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            FgpyDriver.objects.create(
                reported_name="Cuatro", created_via="bot", proposal_key="same-proposal"
            )

        FgpyVehicle.objects.create(
            original_plate="AA 100 AA", normalized_plate="AA100AA",
            description="Uno", created_via="user", status="confirmed",
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            FgpyVehicle.objects.create(
                original_plate="AA100AA", normalized_plate="AA100AA",
                description="Dos", created_via="user", status="confirmed",
            )

    def test_dashboard_uses_only_fgpy_catalog_endpoints(self):
        source = (
            Path(__file__).resolve().parents[3]
            / "dashboard-frontend"
            / "src"
            / "views"
            / "FuelReports.vue"
        ).read_text(encoding="utf-8")
        self.assertIn("api/bot/fgpy-vehicles/", source)
        self.assertIn("api/bot/fgpy-drivers/", source)
        self.assertNotIn("api/equipos/", source)
        self.assertNotIn("api/empleados/", source)
        self.assertNotIn("api/empleado/", source)
