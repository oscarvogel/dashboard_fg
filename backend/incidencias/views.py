from collections import defaultdict

from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from forestal_bot.permissions import OpenClawBearerPermission
from produccion.models import Empleado, Equipo

from .models import IncidenciaEquipo, IncidenciaPersonal
from .serializers import (
    CierreIncidenciaPersonalSerializer, CierreIncidenciaSerializer, EventoEstadoEquipoSerializer,
    IncidenciaEquipoSerializer, IncidenciaPersonalSerializer, PeriodoSerializer,
)
from .services import agregar_evento, cerrar_incidencia, limites_mes, resumen_horas_paradas


class BotAPIView(APIView):
    authentication_classes = []
    permission_classes = [OpenClawBearerPermission]


class IncidenciaEquipoListCreateView(BotAPIView):
    def get(self, request):
        qs = IncidenciaEquipo.objects.select_related("equipo").prefetch_related("eventos")
        for param, field in (("equipo_id", "equipo_id"), ("tipo", "tipo"), ("estado", "estado_actual"), ("abierta", "abierta"), ("grupo_origen_key", "grupo_origen_key")):
            value = request.query_params.get(param)
            if value is not None:
                if param == "abierta":
                    value = serializers.BooleanField().run_validation(value)
                qs = qs.filter(**{field: value})
        if request.query_params.get("inicio"):
            qs = qs.filter(Q(finalizacion__isnull=True) | Q(finalizacion__gte=request.query_params["inicio"]))
        if request.query_params.get("fin"):
            qs = qs.filter(inicio__lt=request.query_params["fin"])
        return Response(IncidenciaEquipoSerializer(qs, many=True).data)

    def post(self, request):
        serializer = IncidenciaEquipoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EventoEstadoEquipoCreateView(BotAPIView):
    def post(self, request, pk):
        incidencia = get_object_or_404(IncidenciaEquipo, pk=pk)
        serializer = EventoEstadoEquipoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ultimo = incidencia.eventos.order_by("-fecha_hora", "-id").first()
        if ultimo and serializer.validated_data["fecha_hora"] < ultimo.fecha_hora:
            raise serializers.ValidationError({"fecha_hora": "No puede ser anterior al ultimo evento registrado."})
        evento = agregar_evento(incidencia, dict(serializer.validated_data))
        return Response(EventoEstadoEquipoSerializer(evento).data, status=status.HTTP_201_CREATED)


class CerrarIncidenciaEquipoView(BotAPIView):
    def post(self, request, pk):
        incidencia = get_object_or_404(IncidenciaEquipo, pk=pk, abierta=True)
        serializer = CierreIncidenciaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ultimo = incidencia.eventos.order_by("-fecha_hora", "-id").first()
        if ultimo and serializer.validated_data["fecha_hora"] < ultimo.fecha_hora:
            raise serializers.ValidationError({"fecha_hora": "No puede ser anterior al ultimo evento registrado."})
        _, incidencia = cerrar_incidencia(incidencia, dict(serializer.validated_data))
        return Response(IncidenciaEquipoSerializer(incidencia).data)


class IncidenciaPersonalListCreateView(BotAPIView):
    def get(self, request):
        qs = IncidenciaPersonal.objects.select_related("persona")
        for param, field in (("persona_id", "persona_id"), ("tipo", "tipo"), ("estado", "estado_justificacion"), ("grupo_origen_key", "grupo_origen_key")):
            if request.query_params.get(param):
                qs = qs.filter(**{field: request.query_params[param]})
        if request.query_params.get("abierta") is not None:
            qs = qs.filter(abierta=serializers.BooleanField().run_validation(request.query_params["abierta"]))
        if request.query_params.get("inicio"):
            qs = qs.filter(fecha__gte=request.query_params["inicio"])
        if request.query_params.get("fin"):
            qs = qs.filter(fecha__lte=request.query_params["fin"])
        return Response(IncidenciaPersonalSerializer(qs, many=True).data)

    def post(self, request):
        serializer = IncidenciaPersonalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CerrarIncidenciaPersonalView(BotAPIView):
    def post(self, request, pk):
        incidencia = get_object_or_404(IncidenciaPersonal, pk=pk, abierta=True)
        serializer = CierreIncidenciaPersonalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        incidencia.abierta = False
        incidencia.finalizacion = serializer.validated_data["fecha_hora"]
        cierre = serializer.validated_data["mensaje"].strip()
        extra = serializer.validated_data.get("observaciones", "").strip()
        incidencia.observaciones = " | ".join(x for x in (incidencia.observaciones, cierre, extra) if x)
        incidencia.save(update_fields=["abierta", "finalizacion", "observaciones", "actualizada_en"])
        return Response(IncidenciaPersonalSerializer(incidencia).data)


class DashboardIncidenciasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        equipos = IncidenciaEquipo.objects.select_related("equipo").prefetch_related("eventos")
        personas = IncidenciaPersonal.objects.select_related("persona")
        grupo = request.query_params.get("grupo_origen_key")
        abierta = request.query_params.get("abierta")
        if grupo:
            equipos = equipos.filter(grupo_origen_key=grupo)
            personas = personas.filter(grupo_origen_key=grupo)
        if abierta is not None:
            value = serializers.BooleanField().run_validation(abierta)
            equipos = equipos.filter(abierta=value)
            personas = personas.filter(abierta=value)
        return Response({"equipos": IncidenciaEquipoSerializer(equipos, many=True).data, "personas": IncidenciaPersonalSerializer(personas, many=True).data})


class HorasParadasView(BotAPIView):
    def get(self, request):
        params = PeriodoSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        equipo_id = request.query_params.get("equipo_id")
        datos = resumen_horas_paradas(params.validated_data["inicio"], params.validated_data["fin"], int(equipo_id) if equipo_id else None)
        nombres = {e.id: {"equipo_nombre": e.detalle, "equipo_referencia": e.patente} for e in Equipo.objects.filter(id__in=[d["equipo_id"] for d in datos])}
        for dato in datos:
            dato.update(nombres.get(dato["equipo_id"], {}))
        return Response(datos)


class IncidenciasPorPersonaView(BotAPIView):
    def get(self, request):
        qs = IncidenciaPersonal.objects.select_related("persona")
        if request.query_params.get("inicio"):
            qs = qs.filter(fecha__gte=request.query_params["inicio"])
        if request.query_params.get("fin"):
            qs = qs.filter(fecha__lte=request.query_params["fin"])
        if request.query_params.get("persona_id"):
            qs = qs.filter(persona_id=request.query_params["persona_id"])
        grupos = qs.values("persona_id", "persona__nombre", "tipo").annotate(cantidad=Count("id"), duracion_minutos=Sum("duracion_minutos"), jornadas_afectadas=Sum("jornada_afectada")).order_by("persona__nombre", "tipo")
        return Response(list(grupos))


class ResumenMensualView(BotAPIView):
    def get(self, request):
        periodo = request.query_params.get("periodo")
        if not periodo:
            raise serializers.ValidationError({"periodo": "Use el formato YYYY-MM."})
        try:
            inicio, fin = limites_mes(periodo)
        except ValueError as exc:
            raise serializers.ValidationError({"periodo": "Use el formato YYYY-MM."}) from exc
        horas = resumen_horas_paradas(inicio, fin)
        equipos = {e.id: e.detalle or e.patente for e in Equipo.objects.filter(id__in=[x["equipo_id"] for x in horas])}
        for item in horas:
            item["equipo_nombre"] = equipos.get(item["equipo_id"])
        personales = IncidenciaPersonal.objects.filter(fecha__gte=inicio.date(), fecha__lt=fin.date()).values("persona_id", "persona__nombre", "tipo").annotate(cantidad=Count("id"), duracion_minutos=Sum("duracion_minutos"), jornadas_afectadas=Sum("jornada_afectada")).order_by("persona__nombre", "tipo")
        por_tipo = defaultdict(int)
        for item in personales:
            por_tipo[item["tipo"]] += item["cantidad"]
        abiertas = IncidenciaEquipo.objects.filter(inicio__lt=fin).filter(Q(finalizacion__isnull=True) | Q(finalizacion__gte=fin)).count()
        return Response({
            "periodo": periodo,
            "equipos_horas_paradas": horas,
            "incidencias_equipos_abiertas_al_cierre": abiertas,
            "personas_por_tipo": list(personales),
            "totales_personal_por_tipo": dict(por_tipo),
            "personas_que_faltaron": por_tipo[IncidenciaPersonal.Tipo.FALTA],
            "personas_que_fueron_al_medico": por_tipo[IncidenciaPersonal.Tipo.MEDICO],
            "llegadas_tarde": por_tipo[IncidenciaPersonal.Tipo.LLEGADA_TARDE],
            "retiros_anticipados": por_tipo[IncidenciaPersonal.Tipo.RETIRO_ANTICIPADO],
        })


class ResolverReferenciaView(BotAPIView):
    def get(self, request):
        q = request.query_params.get("q", "").strip()
        tipo = request.query_params.get("tipo")
        if not q or tipo not in {"equipo", "persona"}:
            raise serializers.ValidationError({"detail": "Informe q y tipo=equipo|persona."})
        if tipo == "equipo":
            qs = Equipo.objects.filter(Q(patente__icontains=q) | Q(detalle__icontains=q) | Q(codigo_fg__icontains=q)).order_by("detalle")[:20]
            return Response([{"id": x.id, "nombre": x.detalle, "referencia": x.patente, "codigo_fg": x.codigo_fg, "aliases": x.aliases} for x in qs])
        qs = Empleado.objects.filter(Q(nombre__icontains=q) | Q(dni__icontains=q)).order_by("nombre")[:20]
        return Response([{"id": x.id, "nombre": x.nombre, "referencia": x.dni} for x in qs])
