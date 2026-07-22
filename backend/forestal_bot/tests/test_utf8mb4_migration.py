from importlib import import_module
from unittest.mock import MagicMock, Mock

from django.test import SimpleTestCase


migration = import_module(
    "forestal_bot.migrations.0011_whatsapp_messages_utf8mb4"
)


class WhatsAppUtf8mb4MigrationTests(SimpleTestCase):
    def test_mysql_converts_complete_message_table(self):
        apps = Mock()
        model = Mock()
        model._meta.db_table = "forestal_bot_whatsappmessage"
        apps.get_model.return_value = model
        cursor = Mock()
        connection = MagicMock(vendor="mysql")
        connection.cursor.return_value.__enter__.return_value = cursor
        editor = Mock(connection=connection)
        editor.quote_name.return_value = "`forestal_bot_whatsappmessage`"

        migration.convert_whatsapp_messages_to_utf8mb4(apps, editor)

        cursor.execute.assert_called_once_with(
            "ALTER TABLE `forestal_bot_whatsappmessage` "
            "CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )

    def test_non_mysql_database_is_unchanged(self):
        apps = Mock()
        editor = Mock(connection=Mock(vendor="sqlite"))

        migration.convert_whatsapp_messages_to_utf8mb4(apps, editor)

        apps.get_model.assert_not_called()
