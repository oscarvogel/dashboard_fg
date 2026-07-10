from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from forestal_bot.models import WhatsAppMessage


@override_settings(OPENCLAW_INGEST_TOKEN="test-openclaw-token")
class WhatsAppMessageCreateAPITests(APITestCase):
    def setUp(self):
        self.url = reverse("forestal_bot:whatsapp-message-list")
        self.payload = {
            "source": "openclaw",
            "provider": "whatsapp-web",
            "account_id": "account-1",
            "group_jid": "120363000000000000@g.us",
            "message_id": "message-1",
            "group_name": "Operaciones Forestales",
            "sender_id": "5491112345678",
            "sender_e164": "+5491112345678",
            "sender_name": "Operador Uno",
            "timestamp": "2026-07-10T10:15:30-03:00",
            "body": "Equipo detenido por mantenimiento",
            "message_type": "text",
            "media_type": "",
            "media_path": "",
            "gated_out": False,
            "would_process_agent": True,
            "skip_reason": "",
        }

    def test_post_without_token_is_forbidden(self):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_with_invalid_bearer_token_is_forbidden(self):
        response = self.client.post(
            self.url,
            self.payload,
            format="json",
            HTTP_AUTHORIZATION="Bearer wrong-token",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_with_non_ascii_bearer_header_is_forbidden(self):
        response = self.client.post(
            self.url,
            self.payload,
            format="json",
            HTTP_AUTHORIZATION="Bearer test-openclaw-tokén",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(OPENCLAW_INGEST_TOKEN="tökén")
    def test_post_with_non_ascii_configured_token_is_forbidden(self):
        response = self.client.post(
            self.url,
            self.payload,
            format="json",
            HTTP_AUTHORIZATION="Bearer tökén",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(OPENCLAW_INGEST_TOKEN="")
    def test_post_with_missing_configured_token_is_forbidden(self):
        response = self.client.post(
            self.url,
            self.payload,
            format="json",
            HTTP_AUTHORIZATION="Bearer test-openclaw-token",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_with_valid_token_creates_message_and_preserves_raw_payload(self):
        response = self.client.post(
            self.url,
            self.payload,
            format="json",
            HTTP_AUTHORIZATION="Bearer test-openclaw-token",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["created"])
        message = WhatsAppMessage.objects.get()
        self.assertEqual(message.raw_json, self.payload)

    def test_post_rejects_timestamp_without_timezone_offset(self):
        payload = {**self.payload, "timestamp": "2026-07-10T10:15:30"}

        response = self.client.post(
            self.url,
            payload,
            format="json",
            HTTP_AUTHORIZATION="Bearer test-openclaw-token",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(set(response.data), {"timestamp"})

    def test_post_accepts_timestamp_with_z_timezone(self):
        payload = {**self.payload, "timestamp": "2026-07-10T13:15:30Z"}

        response = self.client.post(
            self.url,
            payload,
            format="json",
            HTTP_AUTHORIZATION="Bearer test-openclaw-token",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_media_without_body_persists_empty_body(self):
        payload = {
            **self.payload,
            "message_type": "image",
            "media_type": "image/jpeg",
            "media_path": "spool/image.jpg",
        }
        payload.pop("body")

        response = self.client.post(
            self.url,
            payload,
            format="json",
            HTTP_AUTHORIZATION="Bearer test-openclaw-token",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(WhatsAppMessage.objects.get().body, "")

    def test_duplicate_post_returns_existing_message_without_overwriting_it(self):
        headers = {"HTTP_AUTHORIZATION": "Bearer test-openclaw-token"}
        first_response = self.client.post(
            self.url,
            self.payload,
            format="json",
            **headers,
        )
        duplicate_payload = {**self.payload, "body": "contenido modificado"}

        duplicate_response = self.client.post(
            self.url,
            duplicate_payload,
            format="json",
            **headers,
        )

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(duplicate_response.status_code, status.HTTP_200_OK)
        self.assertFalse(duplicate_response.data["created"])
        self.assertEqual(WhatsAppMessage.objects.count(), 1)
        message = WhatsAppMessage.objects.get()
        self.assertEqual(message.body, self.payload["body"])
        self.assertEqual(message.raw_json, self.payload)

    def test_bearer_scheme_is_case_insensitive_and_allows_horizontal_whitespace(self):
        response = self.client.post(
            self.url,
            self.payload,
            format="json",
            HTTP_AUTHORIZATION="bearer   test-openclaw-token",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_malformed_bearer_header_with_extra_parts_is_forbidden(self):
        response = self.client.post(
            self.url,
            self.payload,
            format="json",
            HTTP_AUTHORIZATION="Bearer test-openclaw-token extra",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_with_empty_payload_reports_required_identity_and_timestamp(self):
        response = self.client.post(
            self.url,
            {},
            format="json",
            HTTP_AUTHORIZATION="Bearer test-openclaw-token",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            set(response.data),
            {"account_id", "group_jid", "message_id", "timestamp"},
        )

    def test_post_with_json_scalar_root_returns_stable_validation_error(self):
        response = self.client.generic(
            "POST",
            self.url,
            "42",
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer test-openclaw-token",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {"non_field_errors": ["Expected a JSON object."]},
        )

    def test_post_with_non_pair_json_array_root_returns_stable_validation_error(self):
        response = self.client.generic(
            "POST",
            self.url,
            '["not-a-pair"]',
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer test-openclaw-token",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {"non_field_errors": ["Expected a JSON object."]},
        )


@override_settings(OPENCLAW_INGEST_TOKEN="test-openclaw-token")
class WhatsAppMessageRecentAPITests(APITestCase):
    def setUp(self):
        self.url = reverse("forestal_bot:whatsapp-message-recent")
        self.headers = {
            "HTTP_AUTHORIZATION": "Bearer test-openclaw-token",
        }

    def create_message(self, message_id, timestamp, group_jid="group-a@g.us"):
        return WhatsAppMessage.objects.create(
            account_id="account-1",
            group_jid=group_jid,
            message_id=message_id,
            timestamp=timestamp,
        )

    def create_messages(self, count):
        WhatsAppMessage.objects.bulk_create(
            [
                WhatsAppMessage(
                    account_id="account-1",
                    group_jid="group-a@g.us",
                    message_id=f"message-{index}",
                    timestamp="2026-07-10T10:00:00-03:00",
                )
                for index in range(count)
            ]
        )

    def test_get_recent_without_token_is_forbidden(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_recent_returns_newest_message_first(self):
        self.create_message("oldest", "2026-07-10T10:00:00-03:00")
        self.create_message("newest", "2026-07-10T11:00:00-03:00")

        response = self.client.get(self.url, **self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [row["message_id"] for row in response.data],
            ["newest", "oldest"],
        )

    def test_get_recent_filters_by_exact_group_jid(self):
        self.create_message("selected", "2026-07-10T11:00:00-03:00")
        self.create_message(
            "other",
            "2026-07-10T12:00:00-03:00",
            group_jid="group-a@g.us.extra",
        )

        response = self.client.get(
            self.url,
            {"group_jid": "group-a@g.us"},
            **self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [row["message_id"] for row in response.data],
            ["selected"],
        )

    def test_get_recent_filters_since_iso_8601_timestamp(self):
        self.create_message("before", "2026-07-10T09:59:59-03:00")
        self.create_message("at-cutoff", "2026-07-10T10:00:00-03:00")

        response = self.client.get(
            self.url,
            {"since": "2026-07-10T10:00:00-03:00"},
            **self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [row["message_id"] for row in response.data],
            ["at-cutoff"],
        )

    def test_get_recent_applies_limit(self):
        self.create_message("oldest", "2026-07-10T10:00:00-03:00")
        self.create_message("newest", "2026-07-10T11:00:00-03:00")

        response = self.client.get(self.url, {"limit": "1"}, **self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [row["message_id"] for row in response.data],
            ["newest"],
        )

    def test_get_recent_defaults_to_100_messages(self):
        self.create_messages(101)

        response = self.client.get(self.url, **self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 100)

    def test_get_recent_caps_limit_at_500_messages(self):
        self.create_messages(501)

        response = self.client.get(self.url, {"limit": "501"}, **self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 500)

    def test_get_recent_rejects_invalid_since(self):
        response = self.client.get(
            self.url,
            {"since": "not-a-date"},
            **self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(set(response.data), {"since"})

    def test_get_recent_rejects_noninteger_limit(self):
        response = self.client.get(self.url, {"limit": "many"}, **self.headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"limit": ["A positive integer is required."]})

    def test_get_recent_rejects_zero_limit(self):
        response = self.client.get(self.url, {"limit": "0"}, **self.headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"limit": ["A positive integer is required."]})

    def test_get_recent_rejects_negative_limit(self):
        response = self.client.get(self.url, {"limit": "-1"}, **self.headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"limit": ["A positive integer is required."]})
