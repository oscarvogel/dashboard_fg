from django.test import override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from forestal_bot.models import WhatsAppGroup, WhatsAppMessage


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
        self.assertEqual(message.group.name, "Operaciones Forestales")

    def test_post_links_existing_group(self):
        group = WhatsAppGroup.objects.create(
            account_id="account-1",
            jid=self.payload["group_jid"],
            name="Nombre administrado",
        )

        response = self.client.post(
            self.url,
            {**self.payload, "group_name": "Nombre entrante"},
            format="json",
            HTTP_AUTHORIZATION="Bearer test-openclaw-token",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(WhatsAppMessage.objects.get().group, group)
        group.refresh_from_db()
        self.assertEqual(group.name, "Nombre administrado")

    def test_incoming_name_replaces_only_provisional_name(self):
        group = WhatsAppGroup.objects.create(
            account_id="account-1",
            jid=self.payload["group_jid"],
            name="Grupo sin identificar",
        )

        self.client.post(
            self.url,
            self.payload,
            format="json",
            HTTP_AUTHORIZATION="Bearer test-openclaw-token",
        )

        group.refresh_from_db()
        self.assertEqual(group.name, "Operaciones Forestales")

    def test_payload_without_group_name_creates_provisional_group(self):
        payload = dict(self.payload)
        payload.pop("group_name")

        response = self.client.post(
            self.url,
            payload,
            format="json",
            HTTP_AUTHORIZATION="Bearer test-openclaw-token",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        group = WhatsAppGroup.objects.get()
        self.assertEqual(group.name, "Grupo sin identificar")
        self.assertEqual(WhatsAppMessage.objects.get().group, group)

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

    def test_audio_pending_then_completed_updates_only_transcription_fields(self):
        headers = {"HTTP_AUTHORIZATION": "Bearer test-openclaw-token"}
        pending_payload = {
            **self.payload,
            "body": "",
            "message_type": "audio/ogg",
            "media_type": "audio/ogg",
            "media_path": "/local/audio.ogg",
            "transcription_status": "pending",
        }
        first_response = self.client.post(self.url, pending_payload, format="json", **headers)
        original = WhatsAppMessage.objects.get()
        original_raw_json = original.raw_json
        original_timestamp = original.timestamp

        completed_response = self.client.post(
            self.url,
            {
                **pending_payload,
                "body": "contenido que no debe reemplazarse",
                "transcription": "Texto transcripto localmente por Whisper.",
                "transcription_status": "completed",
                "transcription_error": "error anterior",
            },
            format="json",
            **headers,
        )

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(completed_response.status_code, status.HTTP_200_OK)
        self.assertFalse(completed_response.data["created"])
        self.assertEqual(WhatsAppMessage.objects.count(), 1)
        message = WhatsAppMessage.objects.get()
        self.assertEqual(message.transcription, "Texto transcripto localmente por Whisper.")
        self.assertEqual(message.transcription_status, "completed")
        self.assertEqual(message.transcription_error, "")
        self.assertIsNotNone(message.transcribed_at)
        self.assertEqual(message.body, "")
        self.assertEqual(message.raw_json, original_raw_json)
        self.assertEqual(message.timestamp, original_timestamp)

    def test_failed_update_is_bounded_and_does_not_replace_completed_transcription(self):
        headers = {"HTTP_AUTHORIZATION": "Bearer test-openclaw-token"}
        completed = {
            **self.payload,
            "transcription": "Transcripción definitiva",
            "transcription_status": "completed",
        }
        self.client.post(self.url, completed, format="json", **headers)
        response = self.client.post(
            self.url,
            {
                **self.payload,
                "transcription_status": "failed",
                "transcription_error": "Fallo técnico acotado",
            },
            format="json",
            **headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        message = WhatsAppMessage.objects.get()
        self.assertEqual(message.transcription, "Transcripción definitiva")
        self.assertEqual(message.transcription_status, "completed")
        self.assertEqual(message.transcription_error, "")

    def test_failed_update_stores_error_before_completion(self):
        headers = {"HTTP_AUTHORIZATION": "Bearer test-openclaw-token"}
        self.client.post(
            self.url,
            {**self.payload, "transcription_status": "pending"},
            format="json",
            **headers,
        )
        response = self.client.post(
            self.url,
            {
                **self.payload,
                "transcription_status": "failed",
                "transcription_error": "Formato no soportado",
            },
            format="json",
            **headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        message = WhatsAppMessage.objects.get()
        self.assertEqual(message.transcription_status, "failed")
        self.assertEqual(message.transcription_error, "Formato no soportado")
        self.assertIsNone(message.transcribed_at)

    def test_second_completed_does_not_replace_existing_transcription(self):
        headers = {"HTTP_AUTHORIZATION": "Bearer test-openclaw-token"}
        self.client.post(
            self.url,
            {
                **self.payload,
                "transcription": "Primera transcripción",
                "transcription_status": "completed",
            },
            format="json",
            **headers,
        )
        self.client.post(
            self.url,
            {
                **self.payload,
                "transcription": "Intento de reemplazo",
                "transcription_status": "completed",
            },
            format="json",
            **headers,
        )

        self.assertEqual(WhatsAppMessage.objects.get().transcription, "Primera transcripción")

    def test_invalid_status_and_oversized_fields_return_400(self):
        headers = {"HTTP_AUTHORIZATION": "Bearer test-openclaw-token"}
        invalid_status = self.client.post(
            self.url,
            {**self.payload, "transcription_status": "unknown"},
            format="json",
            **headers,
        )
        oversized_transcription = self.client.post(
            self.url,
            {**self.payload, "message_id": "message-2", "transcription": "x" * 20001},
            format="json",
            **headers,
        )
        oversized_error = self.client.post(
            self.url,
            {**self.payload, "message_id": "message-3", "transcription_error": "x" * 1001},
            format="json",
            **headers,
        )

        self.assertEqual(invalid_status.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(oversized_transcription.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(oversized_error.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transcription_error_rejects_tracebacks_and_secret_markers(self):
        headers = {"HTTP_AUTHORIZATION": "Bearer test-openclaw-token"}
        traceback_response = self.client.post(
            self.url,
            {
                **self.payload,
                "transcription_status": "failed",
                "transcription_error": "Traceback (most recent call last): decoder failed",
            },
            format="json",
            **headers,
        )
        secret_response = self.client.post(
            self.url,
            {
                **self.payload,
                "message_id": "message-secret",
                "transcription_status": "failed",
                "transcription_error": "OPENCLAW_INGEST_TOKEN was rejected",
            },
            format="json",
            **headers,
        )

        self.assertEqual(traceback_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(secret_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_old_payload_returns_new_transcription_fields(self):
        response = self.client.post(
            self.url,
            self.payload,
            format="json",
            HTTP_AUTHORIZATION="Bearer test-openclaw-token",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for field in (
            "transcription",
            "transcription_status",
            "transcription_error",
            "transcribed_at",
        ):
            self.assertIn(field, response.data["message"])

    def test_image_pending_then_completed_updates_only_image_analysis_fields(self):
        headers = {"HTTP_AUTHORIZATION": "Bearer test-openclaw-token"}
        pending_payload = {
            **self.payload,
            "body": "",
            "message_type": "image/jpeg",
            "media_type": "image/jpeg",
            "media_path": "/local/private/image.jpg",
            "image_analysis_status": "pending",
        }
        pending_response = self.client.post(self.url, pending_payload, format="json", **headers)
        original = WhatsAppMessage.objects.get()
        original_raw_json = original.raw_json
        original_timestamp = original.timestamp

        completed_response = self.client.post(
            self.url,
            {
                **pending_payload,
                "body": "NO DEBE REEMPLAZAR",
                "image_description": "Se observa una manguera con una fisura longitudinal.",
                "image_analysis_status": "completed",
                "image_analysis_error": "error anterior",
            },
            format="json",
            **headers,
        )

        self.assertEqual(pending_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(completed_response.status_code, status.HTTP_200_OK)
        self.assertFalse(completed_response.data["created"])
        self.assertEqual(WhatsAppMessage.objects.count(), 1)
        message = WhatsAppMessage.objects.get()
        self.assertEqual(
            message.image_description,
            "Se observa una manguera con una fisura longitudinal.",
        )
        self.assertEqual(message.image_analysis_status, "completed")
        self.assertEqual(message.image_analysis_error, "")
        self.assertIsNotNone(message.image_analyzed_at)
        self.assertEqual(message.body, "")
        self.assertEqual(message.raw_json, original_raw_json)
        self.assertEqual(message.timestamp, original_timestamp)

    def test_failed_image_analysis_stores_bounded_error_before_completion(self):
        headers = {"HTTP_AUTHORIZATION": "Bearer test-openclaw-token"}
        self.client.post(
            self.url,
            {**self.payload, "image_analysis_status": "pending"},
            format="json",
            **headers,
        )
        response = self.client.post(
            self.url,
            {
                **self.payload,
                "image_analysis_status": "failed",
                "image_analysis_error": "Formato de imagen no soportado",
            },
            format="json",
            **headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        message = WhatsAppMessage.objects.get()
        self.assertEqual(message.image_analysis_status, "failed")
        self.assertEqual(message.image_analysis_error, "Formato de imagen no soportado")
        self.assertIsNone(message.image_analyzed_at)

    def test_completed_image_description_cannot_be_replaced_or_failed(self):
        headers = {"HTTP_AUTHORIZATION": "Bearer test-openclaw-token"}
        completed = {
            **self.payload,
            "image_description": "Descripción inicial",
            "image_analysis_status": "completed",
        }
        self.client.post(self.url, completed, format="json", **headers)
        self.client.post(
            self.url,
            {
                **self.payload,
                "image_description": "Intento de reemplazo",
                "image_analysis_status": "completed",
            },
            format="json",
            **headers,
        )
        response = self.client.post(
            self.url,
            {
                **self.payload,
                "image_analysis_status": "failed",
                "image_analysis_error": "Error posterior",
            },
            format="json",
            **headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        message = WhatsAppMessage.objects.get()
        self.assertEqual(message.image_description, "Descripción inicial")
        self.assertEqual(message.image_analysis_status, "completed")
        self.assertEqual(message.image_analysis_error, "")

    def test_invalid_or_oversized_image_analysis_fields_return_400(self):
        headers = {"HTTP_AUTHORIZATION": "Bearer test-openclaw-token"}
        responses = [
            self.client.post(
                self.url,
                {**self.payload, "image_analysis_status": "unknown"},
                format="json",
                **headers,
            ),
            self.client.post(
                self.url,
                {**self.payload, "message_id": "image-2", "image_description": "x" * 10001},
                format="json",
                **headers,
            ),
            self.client.post(
                self.url,
                {**self.payload, "message_id": "image-3", "image_analysis_error": "x" * 501},
                format="json",
                **headers,
            ),
            self.client.post(
                self.url,
                {
                    **self.payload,
                    "message_id": "image-4",
                    "image_analysis_status": "failed",
                    "image_analysis_error": "Traceback (most recent call last): decoder failed",
                },
                format="json",
                **headers,
            ),
        ]

        self.assertTrue(
            all(response.status_code == status.HTTP_400_BAD_REQUEST for response in responses)
        )

    def test_old_payload_returns_new_image_analysis_fields(self):
        response = self.client.post(
            self.url,
            self.payload,
            format="json",
            HTTP_AUTHORIZATION="Bearer test-openclaw-token",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for field in (
            "image_description",
            "image_analysis_status",
            "image_analysis_error",
            "image_analyzed_at",
        ):
            self.assertIn(field, response.data["message"])

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
        self.assertEqual(WhatsAppGroup.objects.count(), 1)
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

    def test_get_recent_returns_group_and_display_name(self):
        group = WhatsAppGroup.objects.create(
            account_id="account-1",
            jid="group-a@g.us",
            name="Grupo de prueba",
        )
        message = self.create_message("message-1", "2026-07-10T11:00:00-03:00")
        message.group = group
        message.group_name = "Nombre histórico"
        message.save(update_fields=["group", "group_name"])

        response = self.client.get(self.url, **self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data[0]["group"],
            {"id": group.id, "jid": group.jid, "name": group.name},
        )
        self.assertEqual(response.data[0]["group_display_name"], "Grupo de prueba")
        for field in (
            "image_description",
            "image_analysis_status",
            "image_analysis_error",
            "image_analyzed_at",
        ):
            self.assertIn(field, response.data[0])


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


@override_settings(OPENCLAW_INGEST_TOKEN="test-openclaw-token")
class WhatsAppGroupAPITests(APITestCase):
    def setUp(self):
        self.url = reverse("forestal_bot:whatsapp-group-list")
        self.headers = {"HTTP_AUTHORIZATION": "Bearer test-openclaw-token"}

    def test_endpoints_without_token_are_forbidden(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            self.client.post(self.url, {}, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_authenticated_create_list_filter_and_patch(self):
        create_response = self.client.post(
            self.url,
            {"account_id": "account-1", "jid": "group-a@g.us", "name": "Grupo A"},
            format="json",
            **self.headers,
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        group_id = create_response.data["id"]
        WhatsAppGroup.objects.create(
            account_id="account-2", jid="group-b@g.us", name="Grupo B", active=False
        )

        list_response = self.client.get(
            self.url, {"account_id": "account-1", "active": "true"}, **self.headers
        )
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in list_response.data], [group_id])

        patch_response = self.client.patch(
            reverse("forestal_bot:whatsapp-group-detail", args=[group_id]),
            {"name": "Grupo renombrado"},
            format="json",
            **self.headers,
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data["name"], "Grupo renombrado")

    def test_duplicate_account_and_jid_returns_400(self):
        payload = {"account_id": "account-1", "jid": "group-a@g.us", "name": "Grupo A"}
        self.client.post(self.url, payload, format="json", **self.headers)

        response = self.client.post(self.url, payload, format="json", **self.headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class WhatsAppOwnerMessageAPITests(APITestCase):
    def setUp(self):
        self.url = reverse("forestal_bot:whatsapp-owner-message-list")
        self.user = get_user_model().objects.create_user(
            username="owner-test",
            password="not-used",
        )
        self.group = WhatsAppGroup.objects.create(
            account_id="default",
            jid="group-a@g.us",
            name="Grupo de prueba",
        )
        self.message = WhatsAppMessage.objects.create(
            account_id="default",
            group_jid=self.group.jid,
            group=self.group,
            message_id="audio-1",
            timestamp="2026-07-10T20:00:00Z",
            sender_name="Operador Uno",
            message_type="audio/ogg",
            media_type="audio/ogg",
            media_path="/private/mac/audio.ogg",
            transcription="Audio transcripto",
            transcription_status="completed",
        )

    def test_owner_messages_requires_jwt_authentication(self):
        response = self.client.get(self.url)

        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_owner_messages_returns_friendly_fields_without_media_path(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        row = response.data[0]
        self.assertEqual(row["group_display_name"], "Grupo de prueba")
        self.assertEqual(row["sender_name"], "Operador Uno")
        self.assertEqual(row["transcription_status"], "completed")
        self.assertNotIn("media_path", row)
        self.assertNotIn("group_jid", row)
        for field in (
            "image_description",
            "image_analysis_status",
            "image_analysis_error",
            "image_analyzed_at",
        ):
            self.assertIn(field, row)
