import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'produccion_api.settings')
django.setup()

from produccion.models import ProduccionMensual, Equipo

# Verificar tarifas en ProduccionMensual para febrero 2026
periodo = '202602'

print(f"=== Tarifas en ProduccionMensual para {periodo} ===\n")

# Ver algunos equipos CTL
ctl_plans = ProduccionMensual.objects.filter(
    periodo=periodo,
    tipo_operacion__in=['PROCESO', 'CARGA'],
    unidad_negocio__nombre__icontains='CTL'
)[:5]

print("CTL:")
for pm in ctl_plans:
    eq_name = pm.equipo.detalle if pm.equipo else 'Sin equipo'
    print(f"  Equipo ID: {pm.equipo_id}, {eq_name}")
    print(f"    Tarifa: ${pm.tarifa}, Producción plan: {pm.produccion}, Tipo: {pm.tipo_operacion}")

# Ver algunos equipos FT
ft_plans = ProduccionMensual.objects.filter(
    periodo=periodo,
    tipo_operacion__in=['PROCESO', 'CARGA'],
    unidad_negocio__nombre__icontains='FULL'
)[:5]

print("\nFULL TREE:")
for pm in ft_plans:
    eq_name = pm.equipo.detalle if pm.equipo else 'Sin equipo'
    print(f"  Equipo ID: {pm.equipo_id}, {eq_name}")
    print(f"    Tarifa: ${pm.tarifa}, Producción plan: {pm.produccion}, Tipo: {pm.tipo_operacion}")

# Ver algunos equipos BIOMASA
bio_plans = ProduccionMensual.objects.filter(
    periodo=periodo,
    tipo_operacion__icontains='CHIPEADO',
    unidad_negocio__nombre__icontains='BIOMASA'
)[:5]

print("\nBIOMASA CHIPEADO:")
for pm in bio_plans:
    eq_name = pm.equipo.detalle if pm.equipo else 'Sin equipo'
    print(f"  Equipo ID: {pm.equipo_id}, {eq_name}")
    print(f"    Tarifa: ${pm.tarifa}, Producción plan: {pm.produccion}, Tipo: {pm.tipo_operacion}")

# Verificar un equipo específico del registro
print("\n=== Verificando equipos del día 09-02 ===")
eq_ids = [205, 204, 201, 190]  # IDs de ejemplo de los equipos que vimos antes
for eq_id in eq_ids:
    eq = Equipo.objects.filter(id=eq_id).first()
    if eq:
        pm = ProduccionMensual.objects.filter(periodo=periodo, equipo_id=eq_id).first()
        if pm:
            print(f"\nEquipo {eq_id}: {eq.detalle}")
            print(f"  UN: {pm.unidad_negocio.nombre if pm.unidad_negocio else 'N/A'}")
            print(f"  Tarifa en PM: ${pm.tarifa}")
