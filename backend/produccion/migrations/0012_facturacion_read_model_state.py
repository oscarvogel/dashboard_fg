from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("produccion", "0011_registroproduccion_cod_operador_state")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterModelOptions(
                    name="registroproduccion",
                    options={"managed": False},
                ),
                migrations.AddField(
                    model_name="registroproduccion",
                    name="unitario",
                    field=models.DecimalField(
                        decimal_places=2, default=0.0, max_digits=12
                    ),
                ),
                migrations.AddField(
                    model_name="produccionmensual",
                    name="unidad_tarifa",
                    field=models.CharField(blank=True, max_length=50, null=True),
                ),
                migrations.AddField(
                    model_name="produccionmensual",
                    name="coeficiente",
                    field=models.DecimalField(
                        blank=True, decimal_places=6, max_digits=20, null=True
                    ),
                ),
                migrations.AddField(
                    model_name="produccionmensual",
                    name="cotizacion",
                    field=models.DecimalField(
                        blank=True, decimal_places=6, max_digits=20, null=True
                    ),
                ),
                migrations.AlterModelTable(name="moneda", table="monedas"),
                migrations.AlterModelOptions(name="moneda", options={"managed": False}),
            ],
        )
    ]
