from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("incidencias", "0001_initial")]

    operations = [
        migrations.AddField(model_name="incidenciaequipo", name="grupo_origen_key", field=models.CharField(db_index=True, default="legacy", max_length=100), preserve_default=False),
        migrations.AddField(model_name="incidenciaequipo", name="grupo_origen_nombre", field=models.CharField(default="Sin grupo identificado", max_length=150), preserve_default=False),
        migrations.AddField(model_name="incidenciapersonal", name="grupo_origen_key", field=models.CharField(db_index=True, default="legacy", max_length=100), preserve_default=False),
        migrations.AddField(model_name="incidenciapersonal", name="grupo_origen_nombre", field=models.CharField(default="Sin grupo identificado", max_length=150), preserve_default=False),
        migrations.AddField(model_name="incidenciapersonal", name="abierta", field=models.BooleanField(db_index=True, default=True)),
        migrations.AddField(model_name="incidenciapersonal", name="finalizacion", field=models.DateTimeField(blank=True, db_index=True, null=True)),
    ]
