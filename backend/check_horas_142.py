import os
import sys
import django
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'produccion_api.settings')
django.setup()

from produccion.models import RegistroProduccion, ProduccionMensual, UnidadNegocio

start = datetime(2026,2,1).date()
end = datetime(2026,2,28).date()
print(f"Buscando registros con 'HORAS' en operacion para UN=142 entre {start} y {end}\n")
qs = RegistroProduccion.objects.filter(cod_un_id=142, operacion__icontains='HORAS', fecha__gte=start, fecha__lte=end).select_related('cod_un','cod_equipo')
print(f"Total registros encontrados: {qs.count()}\n")

total_prod = 0.0
for r in qs:
    print(f"{r.fecha} | {r.operacion} | Equipo={r.cod_equipo.detalle if r.cod_equipo else 'N/A'} | prod={r.produccion} | tarifa={r.tarifa}")
    total_prod += float(r.produccion or 0.0)

print(f"\nProduccion sumada mes: {total_prod:,.2f}\n")

# Ver ProduccionMensual para UN 142
un = UnidadNegocio.objects.filter(id=142).first()
if un:
    print(f"Unidad: {un.id} - {un.nombre}\n")
    pm_qs = ProduccionMensual.objects.filter(periodo='202602', unidad_negocio=un)
    print(f"ProduccionMensual entries: {pm_qs.count()}\n")
    for pm in pm_qs:
        print(f"tipo='{pm.tipo_operacion}', produccion={pm.produccion}, tarifa={pm.tarifa}, cantidad_equipo={pm.cantidad_equipo}")
else:
    print('UN 142 no encontrada')
