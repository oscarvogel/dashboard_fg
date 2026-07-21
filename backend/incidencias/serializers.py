from django.db import transaction
from rest_framework import serializers

from .models import EventoEstadoEquipo, IncidenciaEquipo, IncidenciaPersonal


class EventoEstadoEquipoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventoEstadoEquipo
        fields = ["id", "equipo", "incidencia", "estado_anterior", "estado_nuevo", "fecha_hora", "fuente", "source_message_id", "descripcion", "confirmado", "creado_en"]
        read_only_fields = ["id", "equipo", "incidencia", "estado_anterior", "creado_en"]


class IncidenciaEquipoSerializer(serializers.ModelSerializer):
    equipo_nombre = serializers.CharField(source="equipo.detalle", read_only=True)
    equipo_referencia = serializers.CharField(source="equipo.patente", read_only=True)
    duracion_minutos = serializers.SerializerMethodField()
    duracion_parcial = serializers.SerializerMethodField()
    eventos = EventoEstadoEquipoSerializer(many=True, read_only=True)
    source_message_id = serializers.CharField(write_only=True, required=True)
    fuente = serializers.CharField(write_only=True, default="whatsapp")

    class Meta:
        model = IncidenciaEquipo
        fields = ["id", "organization_key", "equipo", "equipo_nombre", "equipo_referencia", "tipo", "descripcion", "ubicacion", "estado_actual", "inicio", "finalizacion", "duracion_minutos", "duracion_parcial", "abierta", "mensaje_origen", "grupo_origen_key", "grupo_origen_nombre", "observaciones", "diagnostico", "solucion", "responsable", "source_message_id", "fuente", "eventos", "creada_en", "actualizada_en"]
        read_only_fields = ["id", "organization_key", "finalizacion", "abierta", "creada_en", "actualizada_en"]

    def validate_source_message_id(self, value):
        if EventoEstadoEquipo.objects.filter(source_message_id=value).exists():
            raise serializers.ValidationError("Ya existe un evento para este mensaje.")
        return value

    def get_duracion_minutos(self, obj):
        from .services import duracion_incidencia
        return duracion_incidencia(obj)[0]

    def get_duracion_parcial(self, obj):
        return obj.finalizacion is None

    def create(self, validated_data):
        source_message_id = validated_data.pop("source_message_id")
        fuente = validated_data.pop("fuente")
        with transaction.atomic():
            incidencia = IncidenciaEquipo.objects.create(**validated_data)
            EventoEstadoEquipo.objects.create(
                incidencia=incidencia,
                equipo=incidencia.equipo,
                estado_anterior=IncidenciaEquipo.Estado.DESCONOCIDO,
                estado_nuevo=incidencia.estado_actual,
                fecha_hora=incidencia.inicio,
                fuente=fuente,
                source_message_id=source_message_id,
                descripcion=incidencia.descripcion,
            )
        return incidencia


class IncidenciaPersonalSerializer(serializers.ModelSerializer):
    persona_nombre = serializers.CharField(source="persona.nombre", read_only=True)

    class Meta:
        model = IncidenciaPersonal
        fields = "__all__"
        read_only_fields = ["id", "organization_key", "abierta", "finalizacion", "cierre_source_message_id", "creada_en", "actualizada_en"]

    def validate(self, attrs):
        inicio = attrs.get("hora_inicio")
        fin = attrs.get("hora_fin")
        if inicio and fin and fin < inicio:
            raise serializers.ValidationError({"hora_fin": "Debe ser posterior a hora_inicio."})
        if attrs.get("duracion_minutos") is None and inicio and fin:
            attrs["duracion_minutos"] = (fin.hour * 60 + fin.minute) - (inicio.hour * 60 + inicio.minute)
        return attrs


class CierreIncidenciaSerializer(serializers.Serializer):
    fecha_hora = serializers.DateTimeField()
    source_message_id = serializers.CharField(max_length=191)
    mensaje = serializers.CharField()
    fuente = serializers.CharField(max_length=80, default="whatsapp")
    solucion = serializers.CharField(required=False, allow_blank=True)
    observaciones = serializers.CharField(required=False, allow_blank=True)
    responsable = serializers.CharField(required=False, allow_blank=True, max_length=150)

    def validate_source_message_id(self, value):
        if EventoEstadoEquipo.objects.filter(source_message_id=value).exists():
            raise serializers.ValidationError("Ya existe un evento para este mensaje.")
        return value


class CierreIncidenciaPersonalSerializer(serializers.Serializer):
    fecha_hora = serializers.DateTimeField()
    source_message_id = serializers.CharField(max_length=191)
    mensaje = serializers.CharField()
    observaciones = serializers.CharField(required=False, allow_blank=True)


class PeriodoSerializer(serializers.Serializer):
    inicio = serializers.DateTimeField()
    fin = serializers.DateTimeField()

    def validate(self, attrs):
        if attrs["fin"] <= attrs["inicio"]:
            raise serializers.ValidationError({"fin": "Debe ser posterior a inicio."})
        return attrs
