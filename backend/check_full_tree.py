import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'produccion_api.settings')
django.setup()

from produccion.models import RegistroProduccion
from django.db.models import Count

# Check for FULL TREE records
result = RegistroProduccion.objects.filter(
    operacion__in=['PROCESO', 'CARGA'], 
    cod_un__nombre__icontains='FULL'
).values('cod_un__nombre').annotate(count=Count('id'))

print("=== Registros de COSECHA FULL TREE ===")
for r in result:
    print(f"{r['cod_un__nombre']}: {r['count']} registros")

# Check for CTL records
result_ctl = RegistroProduccion.objects.filter(
    operacion__in=['PROCESO', 'CARGA'], 
    cod_un__nombre__icontains='CTL'
).values('cod_un__nombre').annotate(count=Count('id'))

print("\n=== Registros de COSECHA CTL ===")
for r in result_ctl:
    print(f"{r['cod_un__nombre']}: {r['count']} registros")
