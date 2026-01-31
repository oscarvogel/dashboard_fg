import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'produccion_api.settings')
django.setup()

from produccion.models import RegistroProduccion

op = 77592
start = date(2025, 12, 30)
end = date(2026, 1, 30)

qs = RegistroProduccion.objects.filter(cod_operador=op, fecha__range=[start, end]).order_by('fecha')
print('COUNT:', qs.count())
for r in qs:
    equipo = getattr(r, 'equipo', None)
    print(f"{r.fecha} | {equipo} | {r.operador} | {r.hr_inicio} -> {r.hr_fin}")
