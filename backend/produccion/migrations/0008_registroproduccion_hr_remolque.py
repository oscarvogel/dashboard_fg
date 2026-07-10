from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0007_add_unidadnegocio_to_equipo'),
    ]

    operations = [
        migrations.AddField(
            model_name='registroproduccion',
            name='hr_remolque',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=12),
        ),
    ]
