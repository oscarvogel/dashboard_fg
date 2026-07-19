from django.contrib import admin
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from forestal_bot.models import (
    WeighingMeasurement,
    WeighingMeasurementRevision,
    WeighingMovement,
)


@override_settings(OPENCLAW_INGEST_TOKEN="test-openclaw-token")
class WeighingMovementAPITests(APITestCase):
    def setUp(self):
        self.headers = {"HTTP_AUTHORIZATION": "Bearer test-openclaw-token"}
        self.list_url = reverse("forestal_bot:weighing-movement-list")

    def create_movement(self, key="movement-1", **overrides):
        payload = {
            "idempotency_key": key,
            "organization_key": "forestal-paraguay",
            "origin_group_key": "logistica-felber",
            "operational_date": "2026-07-18",
            "plate_original": "ACB 190",
            "driver_name": "David Coronel",
            "status": "pendiente",
            "declared_quantity_kg": 42330,
            "official_scale": "felber",
            "evidence": [{"type": "remision", "id": "rem-1"}],
            "source_message_ids": ["msg-remision-1"],
        }
        payload.update(overrides)
        return self.client.post(
            self.list_url, payload, format="json", **self.headers
        )

    def add_measurement(
        self,
        movement_id,
        key,
        scale,
        kind,
        weight,
        **overrides,
    ):
        payload = {
            "idempotency_key": key,
            "scale": scale,
            "kind": kind,
            "weight_kg": weight,
            "source": "foto_balanza",
            "evidence_id": f"photo-{key}",
            "message_id": f"msg-{key}",
            "measured_at": "2026-07-18T10:00:00-03:00",
        }
        payload.update(overrides)
        return self.client.post(
            reverse(
                "forestal_bot:weighing-measurement-upsert",
                args=[movement_id],
            ),
            payload,
            format="json",
            **self.headers,
        )

    def test_requires_bearer_authentication(self):
        self.assertEqual(self.client.get(self.list_url).status_code, 403)
        self.assertEqual(
            self.client.post(self.list_url, {}, format="json").status_code,
            403,
        )

    def test_pending_with_tare_then_gross_completes_and_is_idempotent(self):
        movement_response = self.create_movement()
        movement = movement_response.data["movement"]
        self.assertEqual(movement_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(movement["plate_normalized"], "ACB190")

        tare = self.add_measurement(
            movement["id"], "felber-tare-1", "felber", "tara", 16020
        )
        self.assertEqual(tare.status_code, status.HTTP_201_CREATED)
        self.assertEqual(tare.data["movement"]["status"], "pendiente")

        replay = self.add_measurement(
            movement["id"], "felber-tare-1", "felber", "tara", 16020
        )
        self.assertEqual(replay.status_code, status.HTTP_200_OK)
        self.assertTrue(replay.data["replayed"])
        self.assertEqual(WeighingMeasurement.objects.count(), 1)
        self.assertEqual(WeighingMeasurementRevision.objects.count(), 1)

        gross = self.add_measurement(
            movement["id"],
            "felber-gross-1",
            "felber",
            "bruto",
            58340,
            net_kg=42320,
        )
        self.assertEqual(gross.status_code, status.HTTP_201_CREATED)
        self.assertEqual(gross.data["movement"]["status"], "completo")
        self.assertEqual(
            gross.data["movement"]["calculated_nets_kg"]["felber"], 42320
        )
        self.assertEqual(
            gross.data["movement"]["declared_vs_official_net_kg"], 10
        )

        repeated_movement = self.create_movement()
        self.assertEqual(repeated_movement.status_code, status.HTTP_200_OK)
        self.assertFalse(repeated_movement.data["created"])
        self.assertEqual(repeated_movement.data["movement"]["status"], "completo")
        self.assertEqual(WeighingMovement.objects.count(), 1)

    def test_real_acb_190_second_scale_and_independent_declared_quantity(self):
        movement = self.create_movement().data["movement"]
        measurements = (
            ("f-t", "felber", "tara", 16020),
            ("f-b", "felber", "bruto", 58340),
            ("p-t", "forestal_paraguay", "tara", 15910),
            ("p-b", "forestal_paraguay", "bruto", 57380),
        )
        latest = None
        for values in measurements:
            latest = self.add_measurement(movement["id"], *values)
            self.assertIn(latest.status_code, (200, 201))
        detail = self.client.get(
            reverse(
                "forestal_bot:weighing-movement-detail",
                args=[movement["id"]],
            ),
            **self.headers,
        )
        self.assertEqual(detail.data["calculated_nets_kg"]["felber"], 42320)
        self.assertEqual(
            detail.data["calculated_nets_kg"]["forestal_paraguay"], 41470
        )
        differences = detail.data["comparisons_kg"][
            "felber_minus_forestal_paraguay"
        ]
        self.assertEqual(differences["tara"], 110)
        self.assertEqual(differences["bruto"], 960)
        self.assertEqual(differences["neto"], 850)
        self.assertEqual(detail.data["declared_quantity_kg"], 42330)
        self.assertEqual(detail.data["declared_vs_official_net_kg"], 10)

    def test_correction_keeps_audit_history(self):
        movement = self.create_movement().data["movement"]
        self.add_measurement(
            movement["id"], "tare-original", "felber", "tara", 16020
        )
        corrected = self.add_measurement(
            movement["id"],
            "tare-correction",
            "felber",
            "tara",
            16010,
            source="correccion_manual",
            correction_reason="Lectura verificada",
        )
        self.assertEqual(corrected.status_code, status.HTTP_200_OK)
        self.assertFalse(corrected.data["created"])
        revisions = corrected.data["measurement"]["revisions"]
        self.assertEqual([item["weight_kg"] for item in revisions], [16020, 16010])
        self.assertEqual(revisions[-1]["correction_reason"], "Lectura verificada")

    def test_rejects_invalid_weights_and_inconsistent_net(self):
        movement = self.create_movement().data["movement"]
        invalid = self.add_measurement(
            movement["id"], "bad-weight", "felber", "tara", 0
        )
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self.add_measurement(
            movement["id"], "valid-tare", "felber", "tara", 16020
        )
        mismatch = self.add_measurement(
            movement["id"],
            "bad-net",
            "felber",
            "bruto",
            58340,
            net_kg=999,
        )
        self.assertEqual(mismatch.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            WeighingMeasurement.objects.filter(idempotency_key="bad-net").exists()
        )

    def test_completion_rejects_zero_or_negative_net(self):
        movement = self.create_movement().data["movement"]
        self.add_measurement(
            movement["id"], "tare-high", "felber", "tara", 16020
        )
        self.add_measurement(
            movement["id"], "gross-low", "felber", "bruto", 16000
        )
        response = self.client.post(
            reverse(
                "forestal_bot:weighing-movement-complete",
                args=[movement["id"]],
            ),
            {},
            format="json",
            **self.headers,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_correction_cannot_leave_complete_movement_with_invalid_net(self):
        movement = self.create_movement().data["movement"]
        self.add_measurement(
            movement["id"], "complete-tare", "felber", "tara", 16020
        )
        self.add_measurement(
            movement["id"], "complete-gross", "felber", "bruto", 58340
        )
        invalid = self.add_measurement(
            movement["id"],
            "invalid-correction",
            "felber",
            "bruto",
            15000,
            source="correccion_manual",
            correction_reason="Dato inválido de prueba",
        )
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        measurement = WeighingMeasurement.objects.get(
            movement_id=movement["id"], scale="felber", kind="bruto"
        )
        self.assertEqual(measurement.weight_kg, 58340)

    def test_prevents_organization_mix(self):
        response = self.create_movement(organization_key="forestal-garuhape")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(WeighingMovement.objects.count(), 0)

    def test_filters_list(self):
        self.create_movement("match")
        self.create_movement(
            "other",
            operational_date="2026-07-10",
            plate_original="XYZ 999",
            driver_name="Otro Chofer",
            origin_group_key="segunda-balanza",
        )
        response = self.client.get(
            self.list_url,
            {
                "date_from": "2026-07-18",
                "date_to": "2026-07-18",
                "plate": "acb 190",
                "driver": "David",
                "status": "pendiente",
                "origin_group_key": "logistica-felber",
                "organization_key": "forestal-paraguay",
            },
            **self.headers,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_daily_weekly_monthly_summaries_and_exclusions(self):
        complete = self.create_movement("complete").data["movement"]
        self.add_measurement(
            complete["id"], "summary-tare", "felber", "tara", 16020
        )
        self.add_measurement(
            complete["id"], "summary-gross", "felber", "bruto", 58340
        )
        self.create_movement("pending", official_scale=None)
        self.create_movement("observed", status="observado", official_scale=None)
        self.create_movement("cancelled", status="anulado", official_scale=None)

        for period, expected_start in (
            ("daily", "2026-07-18"),
            ("weekly", "2026-07-13"),
            ("monthly", "2026-07-01"),
        ):
            response = self.client.get(
                reverse("forestal_bot:weighing-summary"),
                {
                    "period": period,
                    "date_from": "2026-07-01",
                    "date_to": "2026-07-31",
                },
                **self.headers,
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            result = response.data["results"][0]
            self.assertEqual(str(result["period_start"]), expected_start)
            self.assertEqual(result["complete_count"], 1)
            self.assertEqual(result["pending_count"], 1)
            self.assertEqual(result["observed_count"], 1)
            self.assertEqual(result["cancelled_count"], 1)
            self.assertEqual(result["effective_net_kg"], 42320)
            self.assertEqual(result["effective_net_tonnes"], "42.320")
            self.assertEqual(len(result["included_movements"]), 1)
            self.assertEqual(len(result["excluded_movements"]), 3)

    def test_models_are_registered_in_admin(self):
        self.assertIn(WeighingMovement, admin.site._registry)
        self.assertIn(WeighingMeasurement, admin.site._registry)
        self.assertIn(WeighingMeasurementRevision, admin.site._registry)
