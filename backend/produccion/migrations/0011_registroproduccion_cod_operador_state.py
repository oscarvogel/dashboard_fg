import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("produccion", "0010_reconcile_legacy_state"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="registroproduccion",
                    name="cod_operador",
                    field=models.ForeignKey(
                        db_column="cod_operador",
                        db_constraint=False,
                        default=1,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="produccion.empleado",
                    ),
                ),
            ],
        ),
    ]
