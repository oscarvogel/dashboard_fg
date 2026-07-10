from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from forestal_bot.models import WhatsAppGroup, WhatsAppMessage


class WhatsAppGroupTests(TestCase):
    def test_group_creation_and_indexes(self):
        group = WhatsAppGroup.objects.create(
            account_id="account-1",
            jid="group-a@g.us",
            name="Operaciones Forestales",
        )

        self.assertTrue(group.active)
        indexes = {index.name: list(index.fields) for index in group._meta.indexes}
        self.assertEqual(indexes["forestal_wag_jid_idx"], ["jid"])
        self.assertEqual(
            indexes["forestal_wag_acct_active_idx"],
            ["account_id", "active"],
        )
        self.assertEqual(indexes["forestal_wag_name_idx"], ["name"])

    def test_account_and_jid_are_unique_together(self):
        WhatsAppGroup.objects.create(
            account_id="account-1",
            jid="group-a@g.us",
            name="Grupo A",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WhatsAppGroup.objects.create(
                    account_id="account-1",
                    jid="group-a@g.us",
                    name="Duplicado",
                )


class WhatsAppMessageTests(TestCase):
    def message_data(self, **overrides):
        data = {
            "account_id": "account-1",
            "group_jid": "120363000000000000@g.us",
            "message_id": "message-1",
            "timestamp": timezone.now(),
        }
        data.update(overrides)
        return data

    def test_media_message_allows_blank_body(self):
        message = WhatsAppMessage.objects.create(
            **self.message_data(
                message_type="image",
                media_type="image/jpeg",
                media_path="media/incoming/photo.jpg",
            )
        )

        self.assertEqual(message.body, "")
        self.assertEqual(message.media_path, "media/incoming/photo.jpg")

    def test_transcription_fields_have_compatible_defaults_and_status_choices(self):
        message = WhatsAppMessage.objects.create(**self.message_data())

        self.assertEqual(message.transcription, "")
        self.assertEqual(message.transcription_status, "")
        self.assertEqual(message.transcription_error, "")
        self.assertIsNone(message.transcribed_at)
        status_field = WhatsAppMessage._meta.get_field("transcription_status")
        self.assertEqual(
            {value for value, _label in status_field.choices},
            {"", "pending", "processing", "completed", "failed"},
        )

    def test_message_identity_is_unique(self):
        WhatsAppMessage.objects.create(**self.message_data())

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WhatsAppMessage.objects.create(**self.message_data())

    def test_recent_message_queries_have_global_and_group_indexes(self):
        indexes = {
            index.name: list(index.fields)
            for index in WhatsAppMessage._meta.indexes
        }

        self.assertEqual(
            indexes["forestal_wa_ts_created_idx"],
            ["timestamp", "created_at"],
        )
        self.assertEqual(
            indexes["forestal_wa_group_ts_cr_idx"],
            ["group_jid", "timestamp", "created_at"],
        )
