from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from forestal_bot.models import DailySummaryDelivery, DailySummaryRun


@override_settings(OPENCLAW_INGEST_TOKEN="test-openclaw-token")
class DailySummaryAPITests(APITestCase):
    def setUp(self):
        self.url = reverse("forestal_bot:daily-summary-list")
        self.headers = {"HTTP_AUTHORIZATION": "Bearer test-openclaw-token"}
        self.payload = {
            "idempotency_key": "2026-07-13:consolidated",
            "operational_date": "2026-07-13",
            "generated_at": "2026-07-13T21:00:00-03:00",
            "status": "generated",
            "consolidated_text": "Resumen consolidado",
            "spoken_script": "Guion hablado",
            "total_groups": 2,
            "total_messages": 7,
            "generator_version": "daily-operational-v1",
            "source": "openclaw",
            "groups": [
                {
                    "group_key": "mantenimiento",
                    "group_name": "Mantenimiento",
                    "message_count": 7,
                    "summary_text": "Una novedad operativa.",
                    "no_updates": False,
                    "position": 0,
                },
                {
                    "group_key": "full-tree-arauco",
                    "group_name": "Full Tree ARAUCO",
                    "message_count": 0,
                    "summary_text": "Sin novedades registradas.",
                    "no_updates": True,
                    "position": 1,
                },
            ],
            "deliveries": [
                {
                    "channel": "whatsapp",
                    "recipient_name": "jose",
                    "status": "pending",
                }
            ],
        }

    def test_requires_bearer_token(self):
        self.assertEqual(
            self.client.get(self.url).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.post(self.url, self.payload, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_create_and_get_detail(self):
        response = self.client.post(
            self.url, self.payload, format="json", **self.headers
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["created"])
        summary = response.data["summary"]
        self.assertEqual(len(summary["groups"]), 2)
        self.assertEqual(summary["groups"][1]["group_key"], "full-tree-arauco")
        self.assertEqual(summary["deliveries"][0]["recipient_name"], "jose")

        detail = self.client.get(
            reverse("forestal_bot:daily-summary-detail", args=[summary["id"]]),
            **self.headers,
        )
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data["consolidated_text"], "Resumen consolidado")

    def test_repeated_post_updates_without_duplicates(self):
        first = self.client.post(
            self.url, self.payload, format="json", **self.headers
        )
        update = {**self.payload, "status": "sent"}
        update["deliveries"] = [
            {
                "channel": "whatsapp",
                "recipient_name": "jose",
                "status": "sent",
                "attempted_at": "2026-07-13T21:05:00-03:00",
                "delivered_at": "2026-07-13T21:05:01-03:00",
            }
        ]

        second = self.client.post(
            self.url, update, format="json", **self.headers
        )

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertFalse(second.data["created"])
        self.assertEqual(DailySummaryRun.objects.count(), 1)
        self.assertEqual(DailySummaryDelivery.objects.count(), 1)
        self.assertEqual(second.data["summary"]["status"], "sent")
        self.assertEqual(
            second.data["summary"]["deliveries"][0]["status"], "sent"
        )

    def test_filters_by_date_group_status_and_channel(self):
        self.client.post(self.url, self.payload, format="json", **self.headers)

        response = self.client.get(
            self.url,
            {
                "date_from": "2026-07-13",
                "date_to": "2026-07-13",
                "group_key": "mantenimiento",
                "status": "generated",
                "channel": "whatsapp",
            },
            **self.headers,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        empty = self.client.get(
            self.url, {"group_key": "inexistente"}, **self.headers
        )
        self.assertEqual(empty.status_code, status.HTTP_200_OK)
        self.assertEqual(empty.data, [])

    def test_rejects_duplicate_groups_and_sensitive_error(self):
        duplicate = {**self.payload}
        duplicate["groups"] = [self.payload["groups"][0]] * 2
        response = self.client.post(
            self.url, duplicate, format="json", **self.headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("groups", response.data)

        unsafe = {**self.payload}
        unsafe["deliveries"] = [
            {
                "channel": "email",
                "recipient_name": "oscar",
                "status": "failed",
                "error": "Traceback (most recent call last): secret_key exposed",
            }
        ]
        response = self.client.post(
            self.url, unsafe, format="json", **self.headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("deliveries", response.data)

    def test_rejects_invalid_limit_and_oversized_summary(self):
        response = self.client.get(self.url, {"limit": "0"}, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        oversized = {**self.payload, "consolidated_text": "x" * 50001}
        response = self.client.post(
            self.url, oversized, format="json", **self.headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("consolidated_text", response.data)

    def test_rejects_inconsistent_totals(self):
        inconsistent = {**self.payload, "total_messages": 99}

        response = self.client.post(
            self.url, inconsistent, format="json", **self.headers
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("total_messages", response.data)
