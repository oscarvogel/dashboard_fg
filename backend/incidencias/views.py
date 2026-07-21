from collections import defaultdict
import re
import unicodedata

from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from forestal_bot.permissions import OpenClawBearerPermission
from produccion.models import Empleado, Equipo

from .models import EventoEstadoEquipo, IncidenciaEquipo, IncidenciaPersonal
from .serializers import (
    CierreIncidenciaPersonalSerializer, CierreIncidenciaSerializer, EventoEstadoEquipoSerializer,
    IncidenciaEquipoSerializer, IncidenciaPersonalSerializer, PeriodoSerializer,
)
from .services import agregar_evento, cerrar_incidencia, limites_mes, resumen_horas_paradas


class BotAPIView(APIView):
    authentication_classes = []
    permission_classes = [OpenClawBearerPermission]


ORGANIZATION_KEY = "forestal-paraguay"


def _validate_organization(request):
    supplied = request.query_params.get("organization_key") or request.data.get("organization_key")
    if supplied and supplied != ORGANIZATION_KEY:
        raise serializers.ValidationError({"organization_key": "Organizacion no permitida."})
    return ORGANIZATION_KEY


def _normalized(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.casefold()).split())


def _resolution_response(results, query):
    query_key = _normalized(query)
    results.sort(key=lambda item: (query_key not in item["search_keys"], item["nombre"].casefold(), item["id"]))
    public = [{key: value for key, value in item.items() if key != "search_keys"} for item in results[:20]]
    if not public:
        return {"estado": "sin_coincidencias", "resultados": []}
    if len(public) == 1:
        return {"estado": "coincidencia_unica", "resultado": public[0], "resultados": public}
    return {"estado": "requiere_confirmacion", "resultados": public}


class IncidenciaEquipoListCreateView(BotAPIView):
    def get(self, request):
        _validate_organization(request)
        qs = IncidenciaEquipo.objects.filter(organization_key=ORGANIZATION_KEY).select_related("equipo").prefetch_related("eventos")
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
        _validate_organization(request)
        source_id = str(request.data.get("source_message_id") or "").strip()
        existing = IncidenciaEquipo.objects.filter(
            organization_key=ORGANIZATION_KEY, eventos__source_message_id=source_id
        ).first() if source_id else None
        if existing:
            return Response(IncidenciaEquipoSerializer(existing).data)
        serializer = IncidenciaEquipoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EventoEstadoEquipoCreateView(BotAPIView):
    def post(self, request, pk):
        _validate_organization(request)
        incidencia = get_object_or_404(IncidenciaEquipo, pk=pk, organization_key=ORGANIZATION_KEY)
        source_id = str(request.data.get("source_message_id") or "").strip()
        existing = EventoEstadoEquipo.objects.filter(incidencia=incidencia, source_message_id=source_id).first() if source_id else None
        if existing:
            return Response(EventoEstadoEquipoSerializer(existing).data)
        serializer = EventoEstadoEquipoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ultimo = incidencia.eventos.order_by("-fecha_hora", "-id").first()
        if ultimo and serializer.validated_data["fecha_hora"] < ultimo.fecha_hora:
            raise serializers.ValidationError({"fecha_hora": "No puede ser anterior al ultimo evento registrado."})
        evento = agregar_evento(incidencia, dict(serializer.validated_data))
        return Response(EventoEstadoEquipoSerializer(evento).data, status=status.HTTP_201_CREATED)


class CerrarIncidenciaEquipoView(BotAPIView):
    def post(self, request, pk):
        _validate_organization(request)
        source_id = str(request.data.get("source_message_id") or "").strip()
        replay = EventoEstadoEquipo.objects.filter(
            incidencia_id=pk, incidencia__organization_key=ORGANIZATION_KEY, source_message_id=source_id
        ).first() if source_id else None
        if replay:
            return Response(IncidenciaEquipoSerializer(replay.incidencia).data)
        incidencia = get_object_or_404(IncidenciaEquipo, pk=pk, abierta=True, organization_key=ORGANIZATION_KEY)
        serializer = CierreIncidenciaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ultimo = incidencia.eventos.order_by("-fecha_hora", "-id").first()
        if ultimo and serializer.validated_data["fecha_hora"] < ultimo.fecha_hora:
            raise serializers.ValidationError({"fecha_hora": "No puede ser anterior al ultimo evento registrado."})
        _, incidencia = cerrar_incidencia(incidencia, dict(serializer.validated_data))
        return Response(IncidenciaEquipoSerializer(incidencia).data)


class IncidenciaPersonalListCreateView(BotAPIView):
    def get(self, request):
        _validate_organization(request)
        qs = IncidenciaPersonal.objects.filter(organization_key=ORGANIZATION_KEY).select_related("persona")
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
        _validate_organization(request)
        source_id = str(request.data.get("source_message_id") or "").strip()
        existing = IncidenciaPersonal.objects.filter(
            organization_key=ORGANIZATION_KEY, source_message_id=source_id
        ).first() if source_id else None
        if existing:
            return Response(IncidenciaPersonalSerializer(existing).data)
        serializer = IncidenciaPersonalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CerrarIncidenciaPersonalView(BotAPIView):
    def post(self, request, pk):
        _validate_organization(request)
        source_id = str(request.data.get("source_message_id") or "").strip()
        replay = IncidenciaPersonal.objects.filter(
            pk=pk, organization_key=ORGANIZATION_KEY, cierre_source_message_id=source_id
        ).first() if source_id else None
        if replay:
            return Response(IncidenciaPersonalSerializer(replay).data)
        incidencia = get_object_or_404(IncidenciaPersonal, pk=pk, abierta=True, organization_key=ORGANIZATION_KEY)
        serializer = CierreIncidenciaPersonalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        incidencia.abierta = False
        incidencia.finalizacion = serializer.validated_data["fecha_hora"]
        incidencia.cierre_source_message_id = serializer.validated_data["source_message_id"]
        cierre = serializer.validated_data["mensaje"].strip()
        extra = serializer.validated_data.get("observaciones", "").strip()
        incidencia.observaciones = " | ".join(x for x in (incidencia.observaciones, cierre, extra) if x)
        incidencia.save(update_fields=["abierta", "finalizacion", "cierre_source_message_id", "observaciones", "actualizada_en"])
        return Response(IncidenciaPersonalSerializer(incidencia).data)


class DashboardIncidenciasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        equipos = IncidenciaEquipo.objects.filter(organization_key=ORGANIZATION_KEY).select_related("equipo").prefetch_related("eventos")
        personas = IncidenciaPersonal.objects.filter(organization_key=ORGANIZATION_KEY).select_related("persona")
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
        _validate_organization(request)
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
        _validate_organization(request)
        qs = IncidenciaPersonal.objects.filter(organization_key=ORGANIZATION_KEY).select_related("persona")
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
        _validate_organization(request)
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
        personales = IncidenciaPersonal.objects.filter(organization_key=ORGANIZATION_KEY, fecha__gte=inicio.date(), fecha__lt=fin.date()).values("persona_id", "persona__nombre", "tipo").annotate(cantidad=Count("id"), duracion_minutos=Sum("duracion_minutos"), jornadas_afectadas=Sum("jornada_afectada")).order_by("persona__nombre", "tipo")
        por_tipo = defaultdict(int)
        for item in personales:
            por_tipo[item["tipo"]] += item["cantidad"]
        abiertas = IncidenciaEquipo.objects.filter(organization_key=ORGANIZATION_KEY, inicio__lt=fin).filter(Q(finalizacion__isnull=True) | Q(finalizacion__gte=fin)).count()
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
        _validate_organization(request)
        q = request.query_params.get("q", "").strip()
        tipo = request.query_params.get("tipo")
        if not q or tipo not in {"equipo", "persona"}:
            raise serializers.ValidationError({"detail": "Informe q y tipo=equipo|persona."})
        query_key = _normalized(q)
        if tipo == "equipo":
            results = []
            for item in Equipo.objects.filter(baja=False).order_by("detalle", "id"):
                keys = [_normalized(item.patente), _normalized(item.detalle), _normalized(item.codigo_fg)]
                keys.extend(_normalized(alias) for alias in (item.aliases or []))
                if any(query_key in key for key in keys if key):
                    results.append({"id": item.id, "nombre": item.detalle or item.patente, "referencia": item.patente, "search_keys": keys})
            return Response(_resolution_response(results, q))
        results = []
        for item in Empleado.objects.order_by("nombre", "id"):
            keys = [_normalized(item.nombre), _normalized(item.dni)]
            if any(query_key in key for key in keys if key):
                results.append({"id": item.id, "nombre": item.nombre, "referencia": item.dni, "search_keys": keys})
        return Response(_resolution_response(results, q))
