import os
import sys
import django
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'produccion_api.settings')
django.setup()

from produccion.models import RegistroProduccion, ProduccionMensual, UnidadNegocio
from django.db.models import Sum

start = datetime(2026,2,1).date()
end = datetime(2026,2,28).date()
print(f"Buscando registros de ACARREO DE TROZAS entre {start} y {end}\n")
qs = RegistroProduccion.objects.filter(operacion__iexact='ACARREO DE TROZAS', fecha__gte=start, fecha__lte=end).select_related('cod_un','cod_equipo')
print(f"Total registros encontrados: {qs.count()}\n")

by_un = {}
for r in qs:
    un = r.cod_un.nombre if r.cod_un else 'Sin UN'
    if un not in by_un:
        by_un[un] = {'produccion':0.0, 'registros':0, 'equipos':set(), 'rows':[]}
    by_un[un]['produccion'] += float(r.produccion or 0.0)
    by_un[un]['registros'] += 1
    if r.cod_equipo:
        by_un[un]['equipos'].add(r.cod_equipo.id)
    by_un[un]['rows'].append(r)

for un_name, data in by_un.items():
    print(f"UN: {un_name}")
    print(f"  Registros: {data['registros']}")
    print(f"  Produccion total mes: {data['produccion']:,.2f}")
    print(f"  Equipos distintos: {len(data['equipos'])}")
    # Mostrar tarifa en ProduccionMensual para esta UN
    un_obj = UnidadNegocio.objects.filter(nombre__iexact=un_name).first()
    if un_obj:
        pm = ProduccionMensual.objects.filter(periodo='202602', unidad_negocio=un_obj).filter(tipo_operacion__icontains='ACARREO').first()
        if pm:
            print(f"  ProduccionMensual: tipo='{pm.tipo_operacion}', produccion={pm.produccion}, tarifa={pm.tarifa}, cantidad_equipo={pm.cantidad_equipo}")
        else:
            # intentar buscar cualquier PM con ACARREO por unidad
            pm_all = ProduccionMensual.objects.filter(periodo='202602', unidad_negocio=un_obj)
            print(f"  ProduccionMensual entries for UN: {pm_all.count()}")
            for p in pm_all:
                print(f"    tipo='{p.tipo_operacion}', produccion={p.produccion}, tarifa={p.tarifa}, cantidad_equipo={p.cantidad_equipo}")
    else:
        print("  Unidad no encontrada en UnidadNegocio")
    print('\n')

# Print sample rows
print('Detalles (primeros 10 registros):')
for r in qs[:10]:
    print(f"{r.fecha} | {r.operacion} | UN={r.cod_un.nombre if r.cod_un else 'N/A'} | Equipo={r.cod_equipo.detalle if r.cod_equipo else 'N/A'} | prod={r.produccion} | tarifa={r.tarifa}")
