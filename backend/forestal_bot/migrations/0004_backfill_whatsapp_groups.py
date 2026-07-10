from django.db import migrations


UNIDENTIFIED_GROUP_NAME = "Grupo sin identificar"


def backfill_whatsapp_groups(apps, schema_editor):
    WhatsAppGroup = apps.get_model("forestal_bot", "WhatsAppGroup")
    WhatsAppMessage = apps.get_model("forestal_bot", "WhatsAppMessage")
    identities = (
        WhatsAppMessage.objects.exclude(account_id="")
        .exclude(group_jid="")
        .values_list("account_id", "group_jid")
        .distinct()
    )

    for account_id, group_jid in identities.iterator():
        existing_name = (
            WhatsAppMessage.objects.filter(
                account_id=account_id,
                group_jid=group_jid,
            )
            .exclude(group_name="")
            .values_list("group_name", flat=True)
            .first()
        )
        group, _ = WhatsAppGroup.objects.get_or_create(
            account_id=account_id,
            jid=group_jid,
            defaults={"name": existing_name or UNIDENTIFIED_GROUP_NAME},
        )
        WhatsAppMessage.objects.filter(
            account_id=account_id,
            group_jid=group_jid,
            group__isnull=True,
        ).update(group=group)


class Migration(migrations.Migration):
    dependencies = [
        ("forestal_bot", "0003_whatsappgroup_whatsappmessage_group"),
    ]

    operations = [
        migrations.RunPython(backfill_whatsapp_groups, migrations.RunPython.noop),
    ]
