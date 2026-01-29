# serializers.py
from produccion.models import Empleado
from rest_framework import serializers
from .models import OrdenServicioDetalle, Sector

class SectorEfectividadSerializer(serializers.Serializer):
    sector = serializers.CharField()
    horas_practicas = serializers.FloatField()
    downtime = serializers.FloatField()
    horas_extras = serializers.FloatField()
    efectividad = serializers.FloatField()

class EmpleadoEfectividadSerializer(serializers.Serializer):
    empleado_id = serializers.IntegerField()
    empleado = serializers.CharField()
    sector = serializers.CharField()
    horas_practicas = serializers.FloatField()
    downtime = serializers.FloatField()
    horas_extras = serializers.FloatField()
    efectividad = serializers.FloatField()

class EmpleadoConMovimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empleado
        fields = ['id', 'nombre']