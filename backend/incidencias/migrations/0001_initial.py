import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    # __first__ also supports the isolated SQLite test settings, where the
    # legacy produccion app is synchronized without running its MySQL migrations.
    dependencies = [("produccion", "__first__")]
    operations = [
        migrations.CreateModel(
            name="IncidenciaEquipo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(db_index=True, max_length=80)),
                ("descripcion", models.TextField()),
                ("ubicacion", models.CharField(blank=True, max_length=150)),
                ("estado_actual", models.CharField(choices=[("parado", "Parado"), ("operativo", "Operativo"), ("intermitente", "Intermitente"), ("desconocido", "Desconocido")], db_index=True, default="desconocido", max_length=20)),
                ("inicio", models.DateTimeField(db_index=True)),
                ("finalizacion", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("abierta", models.BooleanField(db_index=True, default=True)),
                ("mensaje_origen", models.TextField()),
                ("observaciones", models.TextField(blank=True)),
                ("diagnostico", models.TextField(blank=True)),
                ("solucion", models.TextField(blank=True)),
                ("responsable", models.CharField(blank=True, max_length=150)),
                ("creada_en", models.DateTimeField(auto_now_add=True)),
                ("actualizada_en", models.DateTimeField(auto_now=True)),
                ("equipo", models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.PROTECT, related_name="incidencias", to="produccion.equipo")),
            ],
            options={"db_table": "incidencia_equipo", "ordering": ["-inicio", "-id"]},
        ),
        migrations.CreateModel(
            name="IncidenciaPersonal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(choices=[("falta", "Falta"), ("medico", "Medico"), ("retiro_anticipado", "Retiro anticipado"), ("llegada_tarde", "Llegada tarde"), ("licencia", "Licencia"), ("otros", "Otros")], db_index=True, max_length=25)),
                ("fecha", models.DateField(db_index=True)),
                ("hora_inicio", models.TimeField(blank=True, null=True)),
                ("hora_fin", models.TimeField(blank=True, null=True)),
                ("duracion_minutos", models.PositiveIntegerField(blank=True, null=True)),
                ("jornada_afectada", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ("motivo", models.TextField()),
                ("estado_justificacion", models.CharField(choices=[("pendiente", "Pendiente"), ("justificada", "Justificada"), ("no_justificada", "No justificada"), ("no_aplica", "No aplica")], db_index=True, default="pendiente", max_length=20)),
                ("mensaje_origen", models.TextField()),
                ("source_message_id", models.CharField(max_length=191, unique=True)),
                ("observaciones", models.TextField(blank=True)),
                ("creada_en", models.DateTimeField(auto_now_add=True)),
                ("actualizada_en", models.DateTimeField(auto_now=True)),
                ("persona", models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.PROTECT, related_name="incidencias", to="produccion.empleado")),
            ],
            options={"db_table": "incidencia_personal", "ordering": ["-fecha", "-id"]},
        ),
        migrations.CreateModel(
            name="EventoEstadoEquipo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("estado_anterior", models.CharField(choices=[("parado", "Parado"), ("operativo", "Operativo"), ("intermitente", "Intermitente"), ("desconocido", "Desconocido")], max_length=20)),
                ("estado_nuevo", models.CharField(choices=[("parado", "Parado"), ("operativo", "Operativo"), ("intermitente", "Intermitente"), ("desconocido", "Desconocido")], max_length=20)),
                ("fecha_hora", models.DateTimeField(db_index=True)),
                ("fuente", models.CharField(max_length=80)),
                ("source_message_id", models.CharField(max_length=191, unique=True)),
                ("descripcion", models.TextField(blank=True)),
                ("confirmado", models.BooleanField(default=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("equipo", models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.PROTECT, related_name="eventos_estado", to="produccion.equipo")),
                ("incidencia", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="eventos", to="incidencias.incidenciaequipo")),
            ],
            options={"db_table": "incidencia_equipo_evento", "ordering": ["fecha_hora", "id"]},
        ),
        migrations.AddIndex(model_name="incidenciaequipo", index=models.Index(fields=["equipo", "inicio"], name="inc_eq_equipo_inicio_idx")),
        migrations.AddIndex(model_name="incidenciapersonal", index=models.Index(fields=["persona", "fecha"], name="inc_per_persona_fecha_idx")),
        migrations.AddIndex(model_name="eventoestadoequipo", index=models.Index(fields=["equipo", "fecha_hora"], name="inc_ev_equipo_fecha_idx")),
    ]
