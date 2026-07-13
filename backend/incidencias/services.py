from collections import defaultdict
from datetime import datetime, time

from django.db import transaction
from django.utils import timezone

from .models import EventoEstadoEquipo, IncidenciaEquipo


def duracion_incidencia(incidencia, hasta=None):
    fin = incidencia.finalizacion or hasta or timezone.now()
    return max(0, int((fin - incidencia.inicio).total_seconds() // 60)), incidencia.finalizacion is None


def agregar_evento(incidencia, data):
    with transaction.atomic():
        bloqueada = IncidenciaEquipo.objects.select_for_update().get(pk=incidencia.pk)
        evento = EventoEstadoEquipo.objects.create(
            incidencia=bloqueada,
            equipo=bloqueada.equipo,
            estado_anterior=bloqueada.estado_actual,
            **data,
        )
        bloqueada.estado_actual = evento.estado_nuevo
        bloqueada.save(update_fields=["estado_actual", "actualizada_en"])
    return evento


def cerrar_incidencia(incidencia, data):
    with transaction.atomic():
        bloqueada = IncidenciaEquipo.objects.select_for_update().get(pk=incidencia.pk)
        evento = EventoEstadoEquipo.objects.create(
            incidencia=bloqueada,
            equipo=bloqueada.equipo,
            estado_anterior=bloqueada.estado_actual,
            estado_nuevo=IncidenciaEquipo.Estado.OPERATIVO,
            fecha_hora=data["fecha_hora"],
            fuente=data["fuente"],
            source_message_id=data["source_message_id"],
            descripcion=data["mensaje"],
        )
        bloqueada.estado_actual = IncidenciaEquipo.Estado.OPERATIVO
        bloqueada.finalizacion = data["fecha_hora"]
        bloqueada.abierta = False
        for campo in ("solucion", "observaciones", "responsable"):
            if campo in data:
                setattr(bloqueada, campo, data[campo])
        bloqueada.save()
    return evento, bloqueada


def intervalos_parada(inicio, fin, equipo_id=None):
    eventos = EventoEstadoEquipo.objects.filter(confirmado=True, fecha_hora__lt=fin).select_related("equipo")
    if equipo_id:
        eventos = eventos.filter(equipo_id=equipo_id)
    eventos = eventos.order_by("equipo_id", "fecha_hora", "id")
    estado = {}
    comienzo = {}
    intervalos = defaultdict(list)
    for evento in eventos:
        eid = evento.equipo_id
        if evento.fecha_hora < inicio:
            estado[eid] = evento.estado_nuevo
            if evento.estado_nuevo == IncidenciaEquipo.Estado.PARADO:
                comienzo[eid] = inicio
            else:
                comienzo.pop(eid, None)
            continue
        anterior = estado.get(eid, evento.estado_anterior)
        if evento.estado_nuevo == IncidenciaEquipo.Estado.PARADO and anterior != IncidenciaEquipo.Estado.PARADO:
            comienzo[eid] = max(evento.fecha_hora, inicio)
        elif evento.estado_nuevo == IncidenciaEquipo.Estado.OPERATIVO and anterior == IncidenciaEquipo.Estado.PARADO:
            desde = comienzo.pop(eid, inicio)
            if evento.fecha_hora > desde:
                intervalos[eid].append((desde, min(evento.fecha_hora, fin), False))
        estado[eid] = evento.estado_nuevo
    for eid, desde in comienzo.items():
        if desde < fin:
            intervalos[eid].append((desde, fin, True))
    return intervalos


def resumen_horas_paradas(inicio, fin, equipo_id=None):
    resultado = []
    for eid, tramos in intervalos_parada(inicio, fin, equipo_id).items():
        minutos = sum(int((hasta - desde).total_seconds() // 60) for desde, hasta, _ in tramos)
        resultado.append({"equipo_id": eid, "minutos_parado": minutos, "horas_parado": round(minutos / 60, 2), "cantidad_paradas": len(tramos), "duracion_parcial": any(p for _, _, p in tramos)})
    return sorted(resultado, key=lambda item: (-item["minutos_parado"], item["equipo_id"]))


def limites_mes(periodo):
    inicio_naive = datetime.strptime(periodo, "%Y-%m")
    if inicio_naive.month == 12:
        fin_naive = inicio_naive.replace(year=inicio_naive.year + 1, month=1)
    else:
        fin_naive = inicio_naive.replace(month=inicio_naive.month + 1)
    tz = timezone.get_current_timezone()
    return timezone.make_aware(inicio_naive, tz), timezone.make_aware(fin_naive, tz)
