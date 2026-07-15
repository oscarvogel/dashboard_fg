from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Case, Count, DecimalField, F, Sum, Value, When
from rest_framework import serializers

from .facturacion_services import (
    MAX_RANGE_DAYS, ONE, ZERO, _assemble_result, _calculate_row, _period,
    _select_monthly,
)
from .models import CargaCombustible, Equipo, ProduccionMensual, RegistroProduccion


FINANCIAL_METRICS = {
    "facturacion_total", "facturacion_por_litro", "facturacion_por_hora"
}
PRODUCTION_METRICS = {
    "produccion", "produccion_por_litro", "litros_por_unidad_producida"
}
ALLOWED_METRICS = FINANCIAL_METRICS | PRODUCTION_METRICS | {
    "litros_combustible", "horas_trabajadas", "cobertura"
}


class RankingParamsSerializer(serializers.Serializer):
    start_date = serializers.DateField(input_formats=["%Y-%m-%d"])
    end_date = serializers.DateField(input_formats=["%Y-%m-%d"])
    un_id = serializers.IntegerField(required=False, min_value=1)
    tipo_movil = serializers.IntegerField(required=False, min_value=1)
    metric = serializers.ChoiceField(choices=sorted(ALLOWED_METRICS))
    order = serializers.ChoiceField(required=False, choices=("asc", "desc"), default="desc")
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)
    moneda = serializers.ChoiceField(required=False, choices=("ARS", "USD"))
    unidad = serializers.CharField(required=False, max_length=50)

    def validate(self, attrs):
        if attrs["end_date"] < attrs["start_date"]:
            raise serializers.ValidationError({"end_date": "Rango invertido."})
        if (attrs["end_date"] - attrs["start_date"]).days + 1 > MAX_RANGE_DAYS:
            raise serializers.ValidationError(
                {"end_date": f"El rango máximo permitido es de {MAX_RANGE_DAYS} días."}
            )
        if attrs["metric"] in FINANCIAL_METRICS and not attrs.get("moneda"):
            raise serializers.ValidationError(
                {"moneda": "Es obligatoria para rankings financieros."}
            )
        if attrs["metric"] in PRODUCTION_METRICS and not attrs.get("unidad"):
            raise serializers.ValidationError(
                {"unidad": "Es obligatoria para no mezclar unidades productivas."}
            )
        if attrs.get("unidad"):
            attrs["unidad"] = attrs["unidad"].strip().upper()
        return attrs


def parse_ranking_params(query_params):
    serializer = RankingParamsSerializer(data=query_params)
    serializer.is_valid(raise_exception=True)
    return dict(serializer.validated_data)


def _d(value):
    if value is None:
        return ZERO
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _text(value, places="0.001"):
    if value is None:
        return None
    return format(_d(value).quantize(Decimal(places), rounding=ROUND_HALF_UP), "f")


def _bulk_billings(start_date, end_date, equipment_ids, un_id=None):
    activity = RegistroProduccion.objects.filter(
        fecha__range=(start_date, end_date), cod_equipo_id__in=equipment_ids
    )
    if un_id:
        activity = activity.filter(cod_un_id=un_id)
    rows = list(
        activity.values(
            "id", "fecha", "cod_equipo_id", "cod_un_id", "operacion", "produccion",
            "unidad_produccion", "origen_camion__precio",
        ).order_by("cod_equipo_id", "fecha", "id")
    )
    if not rows:
        return {}
    periods = {_period(row["fecha"]) for row in rows}
    un_ids = {row["cod_un_id"] for row in rows if row["cod_un_id"]}
    operations = {row["operacion"] for row in rows}
    monthly = list(
        ProduccionMensual.objects.filter(
            periodo__in=periods, unidad_negocio_id__in=un_ids,
            tipo_operacion__in=operations,
        ).values(
            "periodo", "unidad_negocio_id", "tipo_operacion", "equipo_id", "tarifa",
            "coeficiente", "cotizacion", "unidad_produccion", "unidad_tarifa",
        ).order_by("periodo", "unidad_negocio_id", "tipo_operacion", "equipo_id")
    )
    unit_rows = RegistroProduccion.objects.filter(
        fecha__range=(start_date, end_date), cod_un_id__in=un_ids, operacion__in=operations
    )
    unit_sums = {
        (item["cod_un_id"], item["operacion"]): _d(item["total"])
        for item in unit_rows.values("cod_un_id", "operacion").annotate(total=Sum("unitario"))
    }
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["cod_equipo_id"]].append(
            _calculate_row(
                row, _select_monthly(monthly, row),
                unit_sums.get((row["cod_un_id"], row["operacion"]), ZERO),
            )
        )
    return grouped


def calcular_ranking_moviles(
    *, start_date, end_date, metric, order="desc", page=1, page_size=20,
    un_id=None, tipo_movil=None, moneda=None, unidad=None
):
    production = RegistroProduccion.objects.filter(fecha__range=(start_date, end_date))
    fuel = CargaCombustible.objects.filter(fecha__range=(start_date, end_date), tipo_mov="E")
    if un_id:
        production = production.filter(cod_un_id=un_id)
        fuel = fuel.filter(unidad_negocio_id=un_id)
    candidate_ids = set(production.values_list("cod_equipo_id", flat=True).distinct())
    candidate_ids.update(fuel.values_list("equipo_id", flat=True).distinct())
    candidate_ids.discard(None)
    equipment_qs = Equipo.objects.filter(id__in=candidate_ids).select_related(
        "unidad_negocio", "tipo_movil"
    )
    if tipo_movil:
        equipment_qs = equipment_qs.filter(tipo_movil_id=tipo_movil)
    equipment = {obj.id: obj for obj in equipment_qs}
    ids = set(equipment)

    fuel_map = {
        row["equipo_id"]: _d(row["litros"])
        for row in fuel.filter(equipo_id__in=ids).values("equipo_id").annotate(litros=Sum("litros"))
    }
    valid_hours = Case(
        When(hr_fin__gt=F("hr_inicio"), then=F("hr_fin") - F("hr_inicio")),
        default=Value(ZERO), output_field=DecimalField(max_digits=20, decimal_places=2),
    )
    operational = {
        row["cod_equipo_id"]: {"horas": _d(row["horas"]), "registros": row["registros"]}
        for row in production.filter(cod_equipo_id__in=ids).values("cod_equipo_id").annotate(
            horas=Sum(valid_hours), registros=Count("id")
        )
    }
    production_map = {
        row["cod_equipo_id"]: _d(row["cantidad"])
        for row in production.filter(
            cod_equipo_id__in=ids, unidad_produccion__iexact=unidad or ""
        ).values("cod_equipo_id").annotate(cantidad=Sum("produccion"))
    } if unidad else {}
    billings = _bulk_billings(start_date, end_date, ids, un_id)

    valid = []
    insufficient = []
    for equipment_id in sorted(ids):
        obj = equipment[equipment_id]
        liters = fuel_map.get(equipment_id, ZERO)
        hours = operational.get(equipment_id, {}).get("horas", ZERO)
        produced = production_map.get(equipment_id, ZERO)
        detail = billings.get(equipment_id, [])
        historical = sum(
            (_d(item["facturacion_total"]) for item in detail if item["moneda"] == moneda), ZERO
        )
        calculated_rows = sum(
            item["facturacion_total"] is not None and item["moneda"] == moneda for item in detail
        )
        coverage = (
            Decimal(calculated_rows) / Decimal(len(detail)) * Decimal("100") if detail else ZERO
        )
        metric_value = {
            "facturacion_total": historical if calculated_rows else None,
            "litros_combustible": liters,
            "horas_trabajadas": hours,
            "produccion": produced if equipment_id in production_map else None,
            "facturacion_por_litro": historical / liters if calculated_rows and liters > ZERO else None,
            "facturacion_por_hora": historical / hours if calculated_rows and hours > ZERO else None,
            "produccion_por_litro": produced / liters if equipment_id in production_map and liters > ZERO else None,
            "litros_por_unidad_producida": liters / produced if produced > ZERO else None,
            "cobertura": coverage,
        }[metric]
        row = {
            "movil": {
                "id": equipment_id, "codigo": obj.codigo_fg or None,
                "patente": obj.patente or None, "descripcion": obj.detalle or None,
            },
            "unidad_negocio": obj.unidad_negocio.nombre if obj.unidad_negocio else None,
            "facturacion_por_moneda": (
                [{"moneda": moneda, "total": _text(historical, "0.01")}] if calculated_rows else []
            ),
            "produccion": {"unidad": unidad, "cantidad": _text(produced)},
            "litros": _text(liters), "horas": _text(hours),
            "metrica": metric, "valor_metrica": _text(metric_value),
            "cobertura_porcentual": _text(coverage, "0.01"),
        }
        if metric_value is None:
            row["motivo"] = "datos_insuficientes_o_incompatibles"
            insufficient.append(row)
        else:
            valid.append(row)
    reverse = order == "desc"
    valid.sort(
        key=lambda row: (_d(row["valor_metrica"]), -row["movil"]["id"] if reverse else row["movil"]["id"]),
        reverse=reverse,
    )
    for position, row in enumerate(valid, 1):
        row["posicion"] = position
    total = len(valid)
    start = (page - 1) * page_size
    return {
        "periodo": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        "metrica": metric, "orden": order, "moneda": moneda, "unidad": unidad,
        "paginacion": {
            "page": page, "page_size": page_size, "total_resultados": total,
            "total_paginas": (total + page_size - 1) // page_size,
        },
        "results": valid[start:start + page_size],
        "datos_insuficientes": insufficient,
    }
