"""
Generated migration to add UnidadNegocio FK to Equipo (moviles table).

This migration matches the `unidad_negocio` field declared in the model
and adds the corresponding DB column `unidad_negocio` to the `moviles` table.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0006_lugarcarga_moneda_tipomovil_unidadnegocio_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipo',
            name='unidad_negocio',
            field=models.ForeignKey(blank=True, db_column='unidad_negocio', null=True, on_delete=django.db.models.deletion.CASCADE, to='produccion.unidadnegocio'),
        ),
    ]
