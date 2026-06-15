import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'produccion_api.settings')
django.setup()

from produccion.models import RegistroProduccion, ProduccionMensual
from django.db.models import Count
from datetime import datetime

# Verificar registros de ACARREO
print("=== Registros con ACARREO ===")
acarreo = RegistroProduccion.objects.filter(
    operacion__icontains='ACARREO'
).values('operacion', 'cod_un__nombre').annotate(count=Count('id')).order_by('-count')

for r in acarreo[:10]:
    print(f"{r['operacion']} - {r['cod_un__nombre']}: {r['count']} registros")

# Verificar en ProduccionMensual
print("\n=== ProduccionMensual con ACARREO para 202602 ===")
pm_acarreo = ProduccionMensual.objects.filter(
    periodo='202602',
    tipo_operacion__icontains='ACARREO'
)

for pm in pm_acarreo:
    un_name = pm.unidad_negocio.nombre if pm.unidad_negocio else 'Sin UN'
    print(f"UN: {un_name}")
    print(f"  Tipo: {pm.tipo_operacion}")
    print(f"  Producción: {pm.produccion}")
    print(f"  Tarifa: {pm.tarifa}")
    print(f"  Cantidad equipos: {pm.cantidad_equipo}")
    print()
