import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'produccion_api.settings')
django.setup()

from produccion.models import ProduccionMensual, RegistroProduccion, UnidadNegocio
from datetime import datetime

# Ver qué es la UN 133
un = UnidadNegocio.objects.get(id=133)
print(f"=== Unidad de Negocio {un.id}: {un.nombre} ===\n")

periodo = '202602'
target_date = datetime(2026, 2, 9).date()

# Ver plan en ProduccionMensual
print("=== ProduccionMensual ===")
pm_list = ProduccionMensual.objects.filter(
    periodo=periodo,
    unidad_negocio_id=133
)
for pm in pm_list:
    print(f"Tipo operación: {pm.tipo_operacion}")
    print(f"  Producción: {pm.produccion}")
    print(f"  Tarifa: {pm.tarifa}")
    print(f"  Cantidad equipos: {pm.cantidad_equipo}")
    print(f"  Equipo ID: {pm.equipo_id}")
    plan_total = float(pm.produccion or 0) * float(pm.tarifa or 0)
    print(f"  Plan total $: {plan_total:,.2f}")
    print()

# Ver registros en tablero_produccion
print("=== Registros en febrero 2026 ===")
registros = RegistroProduccion.objects.filter(
    cod_un_id=133,
    fecha__month=2,
    fecha__year=2026
).order_by('operacion', 'fecha')

ops = {}
for r in registros:
    op = r.operacion or 'SIN_OP'
    if op not in ops:
        ops[op] = {'count': 0, 'prod': 0.0, 'equipos': set()}
    ops[op]['count'] += 1
    ops[op]['prod'] += float(r.produccion or 0)
    if r.cod_equipo:
        ops[op]['equipos'].add(r.cod_equipo.id)

for op, data in ops.items():
    print(f"{op}: {data['count']} registros, Prod total: {data['prod']:,.2f}, {len(data['equipos'])} equipos")

print("\n=== Registros del día 09-02-2026 ===")
registros_dia = RegistroProduccion.objects.filter(
    cod_un_id=133,
    fecha=target_date
)
print(f"Total registros: {registros_dia.count()}")
for r in registros_dia[:5]:
    print(f"  {r.operacion}: Equipo {r.cod_equipo.detalle if r.cod_equipo else 'N/A'}, Prod: {r.produccion}")
