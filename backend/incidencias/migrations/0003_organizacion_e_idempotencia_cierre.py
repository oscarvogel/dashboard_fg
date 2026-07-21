from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("incidencias", "0002_grupo_origen_y_cierre_personal")]

    operations = [
        migrations.AddField(
            model_name="incidenciaequipo",
            name="organization_key",
            field=models.CharField(db_index=True, default="forestal-paraguay", max_length=64),
        ),
        migrations.AddField(
            model_name="incidenciapersonal",
            name="organization_key",
            field=models.CharField(db_index=True, default="forestal-paraguay", max_length=64),
        ),
        migrations.AddField(
            model_name="incidenciapersonal",
            name="cierre_source_message_id",
            field=models.CharField(blank=True, max_length=191, null=True, unique=True),
        ),
    ]
