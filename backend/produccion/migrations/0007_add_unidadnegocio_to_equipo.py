import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0006_lugarcarga_moneda_tipomovil_unidadnegocio_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name='equipo',
                    name='unidad_negocio',
                    field=models.ForeignKey(
                        blank=True,
                        db_column='idUnidadNegocio',
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to='produccion.unidadnegocio',
                    ),
                ),
            ],
        ),
    ]
