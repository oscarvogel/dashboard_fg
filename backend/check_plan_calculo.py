import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'produccion_api.settings')
django.setup()

from produccion.models import ProduccionMensual, RegistroProduccion
from datetime import datetime

periodo = '202602'
target_date = datetime(2026, 2, 9).date()

print("=== ProduccionMensual para CTL ===")
ctl_pm = ProduccionMensual.objects.filter(
    periodo=periodo,
    unidad_negocio__nombre__icontains='CTL'
)
for pm in ctl_pm:
    print(f"UN: {pm.unidad_negocio.nombre}")
    print(f"  Tipo: {pm.tipo_operacion}")
    print(f"  Producción plan: {pm.produccion}")
    print(f"  Tarifa: {pm.tarifa}")
    print(f"  Cantidad equipos: {pm.cantidad_equipo}")
    print(f"  Plan total: {float(pm.produccion) * float(pm.tarifa):,.2f}")
    print()

print("\n=== ProduccionMensual para FULL TREE ===")
ft_pm = ProduccionMensual.objects.filter(
    periodo=periodo,
    unidad_negocio__nombre__icontains='FULL'
)
for pm in ft_pm:
    print(f"UN: {pm.unidad_negocio.nombre}")
    print(f"  Tipo: {pm.tipo_operacion}")
    print(f"  Producción plan: {pm.produccion}")
    print(f"  Tarifa: {pm.tarifa}")
    print(f"  Cantidad equipos: {pm.cantidad_equipo}")
    print(f"  Plan total: {float(pm.produccion) * float(pm.tarifa):,.2f}")
    print()

print("\n=== Equipos únicos que operaron en febrero ===")
# CTL
ctl_equipos = RegistroProduccion.objects.filter(
    fecha__month=2,
    fecha__year=2026,
    operacion__in=['PROCESO', 'CARGA'],
    cod_un__nombre__icontains='CTL'
).values_list('cod_equipo_id', flat=True).distinct()
print(f"CTL: {len(ctl_equipos)} equipos únicos")

# FT
ft_equipos = RegistroProduccion.objects.filter(
    fecha__month=2,
    fecha__year=2026,
    operacion__in=['PROCESO', 'CARGA'],
    cod_un__nombre__icontains='FULL'
).values_list('cod_equipo_id', flat=True).distinct()
print(f"FULL TREE: {len(ft_equipos)} equipos únicos")
