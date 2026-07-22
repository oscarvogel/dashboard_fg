from django.db import migrations


def convert_whatsapp_messages_to_utf8mb4(apps, schema_editor):
    """Allow the complete Unicode range in WhatsApp message metadata and text."""
    if schema_editor.connection.vendor != "mysql":
        return

    Message = apps.get_model("forestal_bot", "WhatsAppMessage")
    table_name = schema_editor.quote_name(Message._meta.db_table)
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            f"ALTER TABLE {table_name} "
            "CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("forestal_bot", "0010_mysql_compatible_fgpy_uniqueness"),
    ]

    operations = [
        migrations.RunPython(
            convert_whatsapp_messages_to_utf8mb4,
            migrations.RunPython.noop,
        ),
    ]
