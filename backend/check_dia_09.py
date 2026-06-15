import os
import sys
import django
from datetime import datetime

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'produccion_api.settings')
django.setup()

from produccion.models import RegistroProduccion
from django.db.models import Sum, Count

target_date = datetime(2026, 2, 9).date()

print(f"=== Registros para {target_date} ===\n")

# CTL
ctl_registros = RegistroProduccion.objects.filter(
    fecha=target_date,
    operacion__in=['PROCESO', 'CARGA'],
    cod_un__nombre__icontains='CTL'
)

print(f"CTL - Total registros: {ctl_registros.count()}")
if ctl_registros.exists():
    for r in ctl_registros[:5]:
        tarifa = float(getattr(r, 'tarifa', 0.0) or 0.0)
        prod = float(r.produccion or 0.0)
        fact = prod * tarifa
        print(f"  - Equipo: {r.cod_equipo.detalle if r.cod_equipo else 'N/A'}, Prod: {prod}, Tarifa: {tarifa}, Facturación: {fact:,.2f}")

# FT
ft_registros = RegistroProduccion.objects.filter(
    fecha=target_date,
    operacion__in=['PROCESO', 'CARGA'],
    cod_un__nombre__icontains='FULL'
)

print(f"\nFULL TREE - Total registros: {ft_registros.count()}")
if ft_registros.exists():
    for r in ft_registros[:5]:
        tarifa = float(getattr(r, 'tarifa', 0.0) or 0.0)
        prod = float(r.produccion or 0.0)
        fact = prod * tarifa
        print(f"  - Equipo: {r.cod_equipo.detalle if r.cod_equipo else 'N/A'}, Prod: {prod}, Tarifa: {tarifa}, Facturación: {fact:,.2f}")

# BIOMASA CHIPEADO
chip_registros = RegistroProduccion.objects.filter(
    fecha=target_date,
    operacion__icontains='CHIPEADO',
    cod_un__nombre__icontains='BIOMASA'
)

print(f"\nBIOMASA CHIPEADO - Total registros: {chip_registros.count()}")
if chip_registros.exists():
    for r in chip_registros[:5]:
        tarifa = float(getattr(r, 'tarifa', 0.0) or 0.0)
        prod = float(r.produccion or 0.0)
        fact = prod * tarifa
        print(f"  - Equipo: {r.cod_equipo.detalle if r.cod_equipo else 'N/A'}, Prod: {prod}, Tarifa: {tarifa}, Facturación: {fact:,.2f}")

# Verificar si el campo tarifa existe
print(f"\n=== Verificando estructura de RegistroProduccion ===")
sample = RegistroProduccion.objects.first()
if sample:
    fields = [f.name for f in sample._meta.get_fields()]
    print(f"Campos disponibles: {', '.join(sorted(fields))}")
    print(f"\nTiene campo 'tarifa': {'tarifa' in fields}")
