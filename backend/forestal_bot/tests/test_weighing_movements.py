from django.contrib import admin
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from forestal_bot.models import (
    WEIGHING_UNIT_CATALOG,
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

    def create_unit_summary_fixture(self):
        paraguari = self.create_movement(
            "paraguari-complete",
            operational_date="2026-07-19",
            origin_group_key="cosecha-paraguari",
            plate_original="AA XO 380",
            driver_name="Juan Pintos",
            declared_quantity_kg=None,
            official_scale="forestal_paraguay",
            observations="Remisión 0002421",
            evidence=[{"type": "remision", "id": "0002421"}],
            source_message_ids=[],
        ).data["movement"]
        self.add_measurement(
            paraguari["id"],
            "paraguari-tare",
            "forestal_paraguay",
            "tara",
            16810,
        )
        self.add_measurement(
            paraguari["id"],
            "paraguari-gross",
            "forestal_paraguay",
            "bruto",
            48650,
        )

        felber_complete = self.create_movement(
            "felber-complete",
            operational_date="2026-07-19",
            origin_group_key="logistica-felber",
            plate_original="ABC 123",
            declared_quantity_kg=None,
            official_scale="felber",
        ).data["movement"]
        self.add_measurement(
            felber_complete["id"],
            "felber-unit-tare",
            "felber",
            "tara",
            15000,
        )
        self.add_measurement(
            felber_complete["id"],
            "felber-unit-gross",
            "felber",
            "bruto",
            35000,
        )

        pending = self.create_movement(
            "felber-pending",
            operational_date="2026-07-19",
            origin_group_key="logistica-felber",
            official_scale=None,
            declared_quantity_kg=None,
        ).data["movement"]
        observed = self.create_movement(
            "paraguari-observed",
            operational_date="2026-07-19",
            origin_group_key="cosecha-paraguari",
            status="observado",
            official_scale=None,
            declared_quantity_kg=None,
        ).data["movement"]
        cancelled = self.create_movement(
            "felber-cancelled",
            operational_date="2026-07-19",
            origin_group_key="logistica-felber",
            status="anulado",
            official_scale=None,
            declared_quantity_kg=None,
        ).data["movement"]
        other_date = self.create_movement(
            "paraguari-other-date",
            operational_date="2026-07-10",
            origin_group_key="cosecha-paraguari",
            official_scale=None,
            declared_quantity_kg=None,
        ).data["movement"]
        WeighingMovement.objects.create(
            idempotency_key="other-organization",
            organization_key="forestal-garuhape",
            origin_group_key="logistica-felber",
            operational_date="2026-07-19",
            status="pendiente",
        )
        return {
            "paraguari": paraguari,
            "felber_complete": felber_complete,
            "pending": pending,
            "observed": observed,
            "cancelled": cancelled,
            "other_date": other_date,
        }

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

    def test_summary_filters_each_known_unit_and_unknown_is_empty(self):
        self.create_unit_summary_fixture()
        url = reverse("forestal_bot:weighing-summary")
        common = {
            "period": "daily",
            "date_from": "2026-07-19",
            "date_to": "2026-07-19",
        }
        paraguari = self.client.get(
            url,
            {**common, "origin_group_key": "cosecha-paraguari"},
            **self.headers,
        )
        felber = self.client.get(
            url,
            {**common, "origin_group_key": "logistica-felber"},
            **self.headers,
        )
        unknown = self.client.get(
            url,
            {**common, "origin_group_key": "unidad-desconocida"},
            **self.headers,
        )
        self.assertEqual(paraguari.status_code, status.HTTP_200_OK)
        self.assertEqual(paraguari.data["results"][0]["effective_net_kg"], 31840)
        self.assertEqual(paraguari.data["results"][0]["complete_count"], 1)
        self.assertEqual(paraguari.data["results"][0]["observed_count"], 1)
        self.assertEqual(felber.data["results"][0]["effective_net_kg"], 20000)
        self.assertEqual(felber.data["results"][0]["pending_count"], 1)
        self.assertEqual(felber.data["results"][0]["cancelled_count"], 1)
        self.assertEqual(unknown.data, {"period": "daily", "results": []})

    def test_grouped_summary_contains_units_and_exact_general_totals(self):
        fixture = self.create_unit_summary_fixture()
        response = self.client.get(
            reverse("forestal_bot:weighing-summary"),
            {
                "period": "daily",
                "date_from": "2026-07-19",
                "date_to": "2026-07-19",
                "group_by": "origin_group_key",
            },
            **self.headers,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["organization_key"], "forestal-paraguay")
        self.assertEqual(str(response.data["date_from"]), "2026-07-19")
        self.assertEqual(str(response.data["date_to"]), "2026-07-19")
        units = {
            unit["origin_group_key"]: unit for unit in response.data["units"]
        }
        self.assertEqual(set(units), set(WEIGHING_UNIT_CATALOG))
        self.assertEqual(
            units["cosecha-paraguari"]["display_name"],
            WEIGHING_UNIT_CATALOG["cosecha-paraguari"]["display_name"],
        )
        self.assertEqual(
            units["logistica-felber"]["display_name"],
            WEIGHING_UNIT_CATALOG["logistica-felber"]["display_name"],
        )
        self.assertEqual(
            units["cosecha-paraguari"]["effective_net_tonnes"], "31.840"
        )
        self.assertEqual(
            units["logistica-felber"]["effective_net_tonnes"], "20.000"
        )
        totals = response.data["totals"]
        for field in (
            "complete_count",
            "pending_count",
            "observed_count",
            "cancelled_count",
            "effective_net_kg",
        ):
            self.assertEqual(
                totals[field], sum(unit[field] for unit in units.values())
            )
        self.assertEqual(totals["effective_net_kg"], 51840)
        self.assertEqual(totals["effective_net_tonnes"], "51.840")
        self.assertEqual(
            totals["scale_totals_kg"],
            {"felber": 20000, "forestal_paraguay": 31840},
        )
        self.assertEqual(
            totals["differences_kg"],
            {
                "felber_minus_forestal_paraguay": {
                    "tara": 0,
                    "bruto": 0,
                    "neto": 0,
                }
            },
        )
        included = [
            movement_id
            for unit in units.values()
            for movement_id in unit["included_movements"]
        ]
        self.assertEqual(len(included), len(set(included)))
        self.assertEqual(
            set(included),
            {
                fixture["paraguari"]["id"],
                fixture["felber_complete"]["id"],
            },
        )
        excluded = [
            movement_id
            for unit in units.values()
            for movement_id in unit["excluded_movements"]
        ]
        self.assertNotIn(str(fixture["other_date"]["id"]), excluded)
        self.assertEqual(len(excluded), 3)
        self.assertEqual(len(excluded), len(set(excluded)))

    def test_grouped_summary_can_filter_one_unit(self):
        self.create_unit_summary_fixture()
        response = self.client.get(
            reverse("forestal_bot:weighing-summary"),
            {
                "period": "daily",
                "date_from": "2026-07-19",
                "date_to": "2026-07-19",
                "group_by": "origin_group_key",
                "origin_group_key": "cosecha-paraguari",
            },
            **self.headers,
        )
        self.assertEqual(len(response.data["units"]), 1)
        self.assertEqual(
            response.data["units"][0]["origin_group_key"],
            "cosecha-paraguari",
        )
        self.assertEqual(response.data["totals"]["effective_net_kg"], 31840)

    def test_grouped_summary_supports_all_periods_and_date_filters(self):
        self.create_unit_summary_fixture()
        expected_starts = {
            "daily": "2026-07-19",
            "weekly": "2026-07-13",
            "monthly": "2026-07-01",
        }
        for period, expected_start in expected_starts.items():
            response = self.client.get(
                reverse("forestal_bot:weighing-summary"),
                {
                    "period": period,
                    "date_from": "2026-07-19",
                    "date_to": "2026-07-19",
                    "group_by": "origin_group_key",
                },
                **self.headers,
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            for unit in response.data["units"]:
                self.assertEqual(
                    str(unit["buckets"][0]["period_start"]), expected_start
                )
            self.assertEqual(response.data["totals"]["pending_count"], 1)

    def test_legacy_summary_contract_is_unchanged_without_group_by(self):
        self.create_unit_summary_fixture()
        response = self.client.get(
            reverse("forestal_bot:weighing-summary"),
            {
                "period": "daily",
                "date_from": "2026-07-19",
                "date_to": "2026-07-19",
            },
            **self.headers,
        )
        self.assertEqual(set(response.data), {"period", "results"})
        self.assertEqual(
            set(response.data["results"][0]),
            {
                "period_start",
                "complete_count",
                "pending_count",
                "observed_count",
                "cancelled_count",
                "effective_net_kg",
                "effective_net_tonnes",
                "scale_totals_kg",
                "differences_kg",
                "included_movements",
                "excluded_movements",
            },
        )
        self.assertEqual(response.data["results"][0]["effective_net_kg"], 51840)

    def test_invalid_group_by_is_rejected_and_summary_requires_bearer(self):
        url = reverse("forestal_bot:weighing-summary")
        invalid = self.client.get(
            url, {"group_by": "scale"}, **self.headers
        )
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("group_by", invalid.data)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_grouped_summary_unknown_unit_and_other_organization_are_isolated(self):
        self.create_unit_summary_fixture()
        response = self.client.get(
            reverse("forestal_bot:weighing-summary"),
            {
                "period": "daily",
                "date_from": "2026-07-19",
                "date_to": "2026-07-19",
                "group_by": "origin_group_key",
                "origin_group_key": "unidad-desconocida",
            },
            **self.headers,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["units"], [])
        self.assertEqual(response.data["totals"], {
            "complete_count": 0,
            "pending_count": 0,
            "observed_count": 0,
            "cancelled_count": 0,
            "effective_net_kg": 0,
            "effective_net_tonnes": "0.000",
            "scale_totals_kg": {},
            "differences_kg": {
                "felber_minus_forestal_paraguay": {
                    "tara": 0,
                    "bruto": 0,
                    "neto": 0,
                }
            },
            "included_movements": [],
            "excluded_movements": [],
        })

    def test_same_remission_number_never_links_movements_across_units(self):
        shared_evidence = [{"type": "remision", "id": "0002421"}]
        felber = self.create_movement(
            "shared-remission-felber",
            operational_date="2026-07-19",
            origin_group_key="logistica-felber",
            plate_original="ACB 190",
            official_scale=None,
            declared_quantity_kg=None,
            evidence=shared_evidence,
            observations="Remisión 0002421",
        ).data["movement"]
        paraguari = self.create_movement(
            "shared-remission-paraguari",
            operational_date="2026-07-19",
            origin_group_key="cosecha-paraguari",
            plate_original="AA XO 380",
            official_scale=None,
            declared_quantity_kg=None,
            evidence=shared_evidence,
            observations="Remisión 0002421",
        ).data["movement"]

        response = self.client.get(
            reverse("forestal_bot:weighing-summary"),
            {
                "period": "daily",
                "date_from": "2026-07-19",
                "date_to": "2026-07-19",
                "group_by": "origin_group_key",
            },
            **self.headers,
        )
        units = {
            unit["origin_group_key"]: unit for unit in response.data["units"]
        }
        self.assertEqual(
            units["logistica-felber"]["excluded_movements"], [felber["id"]]
        )
        self.assertEqual(
            units["cosecha-paraguari"]["excluded_movements"],
            [paraguari["id"]],
        )
        self.assertNotEqual(felber["id"], paraguari["id"])
        self.assertEqual(response.data["totals"]["pending_count"], 2)
        self.assertEqual(
            set(response.data["totals"]["excluded_movements"]),
            {felber["id"], paraguari["id"]},
        )
