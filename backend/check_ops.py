
from produccion.models import RegistroProduccion
ops = RegistroProduccion.objects.values_list('operacion', flat=True).distinct()
print("Operaciones:", list(ops))
