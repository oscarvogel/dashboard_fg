from produccion.models import ProduccionMensual, UnidadNegocio, RegistroProduccion
from datetime import date, timedelta
import calendar

# Parámetros
month, year, cod_un_id = 5, 2026, 1
periodo = f"{year:04d}{month:02d}"
start_date = date(year, month, 1)
month_end = date(year, month, calendar.monthrange(year, month)[1])

print("=" * 80)
print(f"Verificando cálculo de producción esperada para {periodo}, Unidad {cod_un_id}")
print("=" * 80)

# Datos de ProduccionMensual
queryset = ProduccionMensual.objects.filter(periodo=periodo, unidad_negocio_id=cod_un_id)
print(f"\nProduccionMensual registros: {queryset.count()}")
if queryset.exists():
    total_meta = sum(pm.produccion for pm in queryset)
    print(f"Meta total: {total_meta}")
else:
    print("SIN REGISTROS EN ProduccionMensual")
    total_meta = 0

# Días hábiles
dias_del_mes = sum(1 for d in range(1, calendar.monthrange(year, month)[1] + 1) if date(year, month, d).weekday() < 5)
print(f"Días hábiles en el mes: {dias_del_mes}")

# Último día con actividad
from django.db.models import Max
last_activity = RegistroProduccion.objects.filter(
    fecha__range=[start_date, month_end],
    cod_un_id=cod_un_id,
).aggregate(max_fecha=Max('fecha')).get('max_fecha', month_end)

if last_activity is None:
    last_activity = month_end

print(f"Último día con actividad: {last_activity}")

# Calcular proporción
dias_habiles_rango = sum(
    1 for d in range((last_activity - start_date).days + 1)
    if (start_date + timedelta(days=d)).weekday() < 5
)

proporcion = dias_habiles_rango / dias_del_mes if dias_del_mes > 0 else 0
esperada = round(total_meta * proporcion, 2)

print(f"\nDías hábiles en rango ({start_date} a {last_activity}): {dias_habiles_rango}")
print(f"Proporción: {proporcion:.6f}")
print(f"Producción esperada acumulada: {esperada}")

# Verificar RegistroProduccion
print(f"\nRegistroProduccion registros en período: {RegistroProduccion.objects.filter(fecha__range=[start_date, month_end], cod_un_id=cod_un_id).count()}")
