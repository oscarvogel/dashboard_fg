from rest_framework import serializers
from .models import CargaCombustible, Empleado, RegistroProduccion

# class RegistroProduccionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = RegistroProduccion
#         fields = '__all__'
        
class EmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empleado
        fields = '__all__'

class LoginSerializer(serializers.Serializer):
    dni = serializers.CharField(max_length=8)
    password = serializers.CharField(max_length=255)        


class RegistroProduccionDiarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroProduccion
        fields = [
            'fecha',
            'equipo',
            'm3',
            'produccion',
            'hr_inicio',
            'hr_fin',
            'combustible',
            'aceite_cadena',
            'UN',
            'operacion',
            'stock_abc',
        ]

    # Opcional: puedes formatear los campos si lo necesitas
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Formatear valores numéricos como string con comas o puntos si es necesario
        return {
            **data,
            "m3": int(data["m3"]),
            "produccion": float(data["produccion"]),
            "hr_inicio": float(data["hr_inicio"]),
            "hr_fin": float(data["hr_fin"]),
            "combustible": float(data["combustible"]),
            "aceite_cadena": float(data["aceite_cadena"]),
            "stock_abc": float(data["stock_abc"]),
        }    

class RegistroProduccionSerializer(serializers.ModelSerializer):
    equipo_patente = serializers.CharField(source='cod_equipo.patente', read_only=True)
    equipo_detalle = serializers.CharField(source='cod_equipo.detalle', read_only=True)

    class Meta:
        model = RegistroProduccion
        fields = [
            'id',
            'UN',
            'operacion',
            'operador',
            'fecha',
            'equipo',
            'hr_inicio',
            'hr_fin',
            'm3',
            'tn_despachadas',
            'produccion',
            'unidad_produccion',
            'hrs_no_operativas',
            'plantas',
            'combustible',
            'aceite_cadena',
            'predio',
            'equipo_patente',
            'equipo_detalle',
            'stock_abc',
        ]        
        
class CargaCombustibleSerializer(serializers.ModelSerializer):
    movil_detalle = serializers.CharField(source='equipo.detalle', read_only=True)
    movil_patente = serializers.CharField(source='equipo.patente', read_only=True)
    unidad_negocio_nombre = serializers.CharField(source='unidad_negocio.nombre', read_only=True)
    lugar_carga_detalle = serializers.CharField(source='lugar_carga.detalle', read_only=True, allow_null=True)
    paniol_nombre = serializers.CharField(source='paniol.nombre', read_only=True, allow_null=True)
    # personal_nombre = serializers.CharField(source='personal.nombre', read_only=True, allow_null=True)
    # Nuevo campo: devuelve 'Ingreso' o 'Egreso' en lugar de 'I' o 'E'
    tipo_mov_display = serializers.SerializerMethodField()

    class Meta:
        model = CargaCombustible
        fields = [
            'id', 'fecha', 'movil_detalle', 'movil_patente',
            'unidad_negocio_nombre', 'litros', 'km',
            'lugar_carga_detalle', 'paniol_nombre', 'tipo_mov', 'tipo_mov_display'
        ]

    def get_tipo_mov_display(self, obj):
        return dict(CargaCombustible.tipo_mov.field.choices).get(obj.tipo_mov, obj.tipo_mov)