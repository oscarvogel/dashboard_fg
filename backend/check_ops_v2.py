
import os
import sys
import django

# Add 'backend' to sys.path so 'produccion_api' can be found
sys.path.append(os.path.join(os.getcwd(), 'backend'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'produccion_api.settings')
django.setup()

from produccion.models import RegistroProduccion

ops = RegistroProduccion.objects.filter(operacion__iexact='PROCESO').values('m3', 'produccion', 'unidad_produccion')[:5]
print("Ejemplo PROCESO:", list(ops))
ops_chip = RegistroProduccion.objects.filter(operacion__icontains='CHIPEADO').values('m3', 'produccion', 'unidad_produccion')[:5]
print("Ejemplo CHIPEADO:", list(ops_chip))
