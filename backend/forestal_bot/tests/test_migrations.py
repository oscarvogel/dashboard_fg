from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class WhatsAppGroupDataMigrationTests(TransactionTestCase):
    available_apps = ["forestal_bot"]
    migrate_from = ("forestal_bot", "0002_whatsappmessage_forestal_wa_ts_created_idx_and_more")
    migrate_to = ("forestal_bot", "0004_backfill_whatsapp_groups")

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_from])
        old_apps = executor.loader.project_state([self.migrate_from]).apps
        Message = old_apps.get_model("forestal_bot", "WhatsAppMessage")
        common = {
            "source": "openclaw",
            "provider": "whatsapp-web",
            "sender_id": "",
            "sender_e164": "",
            "sender_name": "",
            "timestamp": "2026-07-10T13:15:30Z",
            "body": "",
            "message_type": "text",
            "media_type": "",
            "media_path": "",
            "gated_out": False,
            "would_process_agent": False,
            "skip_reason": "",
            "raw_json": {},
        }
        Message.objects.create(
            account_id="account-1",
            group_jid="named@g.us",
            group_name="Operaciones Forestales",
            message_id="message-1",
            **common,
        )
        Message.objects.create(
            account_id="account-1",
            group_jid="named@g.us",
            group_name="",
            message_id="message-2",
            **common,
        )
        Message.objects.create(
            account_id="account-1",
            group_jid="unnamed@g.us",
            group_name="",
            message_id="message-3",
            **common,
        )

        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_to])
        self.apps = executor.loader.project_state([self.migrate_to]).apps

    def test_migration_creates_groups_and_links_messages_without_rewriting_history(self):
        Group = self.apps.get_model("forestal_bot", "WhatsAppGroup")
        Message = self.apps.get_model("forestal_bot", "WhatsAppMessage")

        self.assertEqual(Group.objects.count(), 2)
        self.assertEqual(
            Group.objects.get(jid="named@g.us").name,
            "Operaciones Forestales",
        )
        self.assertEqual(
            Group.objects.get(jid="unnamed@g.us").name,
            "Grupo sin identificar",
        )
        self.assertEqual(Message.objects.filter(group__isnull=False).count(), 3)
        self.assertEqual(Message.objects.get(message_id="message-2").group_name, "")
