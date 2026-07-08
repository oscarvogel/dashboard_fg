# feature/equipo-aliases (2026-07-08)
# Migracion limpia: solo agrega los 4 campos del feature.
# Los cambios pre-existentes no-migrados (Origen, AlterModelOptions,
# 9 AddField a RegistroProduccion, AlterField unidad_negocio con
# db_column inconsistente) quedan para otro PR.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0007_add_unidadnegocio_to_equipo'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipo',
            name='aliases',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='equipo',
            name='codigo_fg',
            field=models.CharField(blank=True, db_index=True, default='', max_length=30),
        ),
        migrations.AddField(
            model_name='equipo',
            name='modelo_normalizado',
            field=models.CharField(blank=True, default='', max_length=80),
        ),
        migrations.AddField(
            model_name='equipo',
            name='ultima_sync_filtros',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
