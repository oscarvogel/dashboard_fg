from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from forestal_bot.models import WhatsAppMessage


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

    def test_message_identity_is_unique(self):
        WhatsAppMessage.objects.create(**self.message_data())

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WhatsAppMessage.objects.create(**self.message_data())
