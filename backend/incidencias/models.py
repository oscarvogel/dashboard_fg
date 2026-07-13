from django.core.exceptions import ValidationError
from django.db import models


class IncidenciaEquipo(models.Model):
    class Estado(models.TextChoices):
        PARADO = "parado", "Parado"
        OPERATIVO = "operativo", "Operativo"
        INTERMITENTE = "intermitente", "Intermitente"
        DESCONOCIDO = "desconocido", "Desconocido"

    equipo = models.ForeignKey("produccion.Equipo", on_delete=models.PROTECT, related_name="incidencias")
    tipo = models.CharField(max_length=80, db_index=True)
    descripcion = models.TextField()
    ubicacion = models.CharField(max_length=150, blank=True)
    estado_actual = models.CharField(max_length=20, choices=Estado.choices, default=Estado.DESCONOCIDO, db_index=True)
    inicio = models.DateTimeField(db_index=True)
    finalizacion = models.DateTimeField(null=True, blank=True, db_index=True)
    abierta = models.BooleanField(default=True, db_index=True)
    mensaje_origen = models.TextField()
    observaciones = models.TextField(blank=True)
    diagnostico = models.TextField(blank=True)
    solucion = models.TextField(blank=True)
    responsable = models.CharField(max_length=150, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "incidencia_equipo"
        ordering = ["-inicio", "-id"]
        indexes = [models.Index(fields=["equipo", "inicio"], name="inc_eq_equipo_inicio_idx")]


class EventoEstadoEquipo(models.Model):
    incidencia = models.ForeignKey(IncidenciaEquipo, on_delete=models.PROTECT, related_name="eventos")
    equipo = models.ForeignKey("produccion.Equipo", on_delete=models.PROTECT, related_name="eventos_estado")
    estado_anterior = models.CharField(max_length=20, choices=IncidenciaEquipo.Estado.choices)
    estado_nuevo = models.CharField(max_length=20, choices=IncidenciaEquipo.Estado.choices)
    fecha_hora = models.DateTimeField(db_index=True)
    fuente = models.CharField(max_length=80)
    source_message_id = models.CharField(max_length=191, unique=True)
    descripcion = models.TextField(blank=True)
    confirmado = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "incidencia_equipo_evento"
        ordering = ["fecha_hora", "id"]
        indexes = [models.Index(fields=["equipo", "fecha_hora"], name="inc_ev_equipo_fecha_idx")]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Los eventos de estado son inmutables.")
        if self.incidencia_id and self.equipo_id != self.incidencia.equipo_id:
            raise ValidationError("El equipo del evento debe coincidir con el de la incidencia.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Los eventos de estado son inmutables.")


class IncidenciaPersonal(models.Model):
    class Tipo(models.TextChoices):
        FALTA = "falta", "Falta"
        MEDICO = "medico", "Medico"
        RETIRO_ANTICIPADO = "retiro_anticipado", "Retiro anticipado"
        LLEGADA_TARDE = "llegada_tarde", "Llegada tarde"
        LICENCIA = "licencia", "Licencia"
        OTROS = "otros", "Otros"

    class Justificacion(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        JUSTIFICADA = "justificada", "Justificada"
        NO_JUSTIFICADA = "no_justificada", "No justificada"
        NO_APLICA = "no_aplica", "No aplica"

    persona = models.ForeignKey("produccion.Empleado", on_delete=models.PROTECT, related_name="incidencias")
    tipo = models.CharField(max_length=25, choices=Tipo.choices, db_index=True)
    fecha = models.DateField(db_index=True)
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fin = models.TimeField(null=True, blank=True)
    duracion_minutos = models.PositiveIntegerField(null=True, blank=True)
    jornada_afectada = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    motivo = models.TextField()
    estado_justificacion = models.CharField(max_length=20, choices=Justificacion.choices, default=Justificacion.PENDIENTE, db_index=True)
    mensaje_origen = models.TextField()
    source_message_id = models.CharField(max_length=191, unique=True)
    observaciones = models.TextField(blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "incidencia_personal"
        ordering = ["-fecha", "-id"]
        indexes = [models.Index(fields=["persona", "fecha"], name="inc_per_persona_fecha_idx")]
