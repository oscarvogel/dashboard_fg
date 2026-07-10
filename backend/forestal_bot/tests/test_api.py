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
