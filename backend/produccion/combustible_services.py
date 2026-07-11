from decimal import Decimal, ROUND_HALF_UP

from dateutil.relativedelta import relativedelta
from django.db.models import Case, Count, DecimalField, F, Sum, Value, When
from rest_framework import serializers

from .models import CargaCombustible, Equipo, RegistroProduccion


MAX_RANGE_DAYS = 366
DEFAULT_MESES_ATRAS = 6
SEMAFORO_VERDE_MAX_PCT = Decimal("5")
SEMAFORO_AMARILLO_MAX_PCT = Decimal("15")
ZERO = Decimal("0")


class ConsultaCombustibleParamsSerializer(serializers.Serializer):
    inicio = serializers.DateField(required=True, input_formats=["%Y-%m-%d"])
    fin = serializers.DateField(required=True, input_formats=["%Y-%m-%d"])
    un_id = serializers.IntegerField(required=False, min_value=1)
    movil_id = serializers.IntegerField(required=False, min_value=1)
    meses_atras = serializers.IntegerField(
        required=False, min_value=1, max_value=60, default=DEFAULT_MESES_ATRAS
    )

    def validate(self, attrs):
        if attrs["fin"] < attrs["inicio"]:
            raise serializers.ValidationError({"fin": "Debe ser igual o posterior a inicio."})
        if (attrs["fin"] - attrs["inicio"]).days + 1 > MAX_RANGE_DAYS:
            raise serializers.ValidationError(
                {"fin": f"El rango máximo permitido es de {MAX_RANGE_DAYS} días."}
            )
        return attrs


def parse_consulta_params(query_params, include_history=False):
    serializer = ConsultaCombustibleParamsSerializer(data=query_params)
    serializer.is_valid(raise_exception=True)
    data = dict(serializer.validated_data)
    if not include_history:
        data.pop("meses_atras", None)
    return data


def _decimal(value):
    return value if isinstance(value, Decimal) else Decimal(str(value or 0))


def _number(value, places="0.01"):
    if value is None:
        return None
    return float(_decimal(value).quantize(Decimal(places), rounding=ROUND_HALF_UP))


def _base_querysets(inicio, fin, un_id=None, movil_id=None):
    fuel = CargaCombustible.objects.filter(
        fecha__range=(inicio, fin), tipo_mov="E"
    )
    production = RegistroProduccion.objects.filter(fecha__range=(inicio, fin))
    if un_id:
        fuel = fuel.filter(unidad_negocio_id=un_id)
        production = production.filter(cod_un_id=un_id)
    if movil_id:
        fuel = fuel.filter(equipo_id=movil_id)
        production = production.filter(cod_equipo_id=movil_id)
    return fuel, production


def _aggregate_period(inicio, fin, un_id=None, movil_id=None):
    fuel, production = _base_querysets(inicio, fin, un_id, movil_id)
    fuel_rows = list(
        fuel.values("equipo_id")
        .annotate(litros=Sum("litros"), cantidad_cargas=Count("id"))
        .order_by()
    )

    valid_hours = Case(
        When(hr_fin__gt=F("hr_inicio"), then=F("hr_fin") - F("hr_inicio")),
        default=Value(ZERO),
        output_field=DecimalField(max_digits=18, decimal_places=2),
    )
    production_rows = list(
        production.values("cod_equipo_id")
        .annotate(
            horas=Sum(valid_hours),
            registros=Count("id"),
        )
        .order_by()
    )

    # Count with a comparison filter is not portable through F expressions in
    # every supported Django/MySQL combination, so compute this aggregate once.
    invalid_by_equipment = {
        row["cod_equipo_id"]: row["total"]
        for row in production.filter(hr_fin__lte=F("hr_inicio"))
        .values("cod_equipo_id")
        .annotate(total=Count("id"))
        .order_by()
    }

    combined = {}
    for row in fuel_rows:
        combined[row["equipo_id"]] = {
            "litros": _decimal(row["litros"]),
            "cargas": row["cantidad_cargas"],
            "horas": ZERO,
            "registros": 0,
            "invalidos": 0,
        }
    for row in production_rows:
        item = combined.setdefault(
            row["cod_equipo_id"],
            {"litros": ZERO, "cargas": 0, "horas": ZERO, "registros": 0, "invalidos": 0},
        )
        item["horas"] = _decimal(row["horas"])
        item["registros"] = row["registros"]
        item["invalidos"] = invalid_by_equipment.get(row["cod_equipo_id"], 0)

    equipment = {
        item.id: item
        for item in Equipo.objects.filter(id__in=combined).select_related("unidad_negocio")
    }
    results = []
    for equipment_id, values in combined.items():
        obj = equipment.get(equipment_id)
        if obj is None:
            continue
        hours = values["horas"]
        liters = values["litros"]
        warnings = []
        if hours <= ZERO:
            lph = None
            warnings.append("sin_horas_operativas_validas")
        else:
            lph = liters / hours
        if values["invalidos"]:
            warnings.append("intervalos_horas_cero_o_negativos_excluidos")
        results.append(
            {
                "equipo_id": equipment_id,
                "equipo": obj.detalle or obj.patente or str(equipment_id),
                "unidad_negocio": obj.unidad_negocio.nombre if obj.unidad_negocio else None,
                "litros_egreso": _number(liters),
                "horas_operativas": _number(hours),
                "litros_por_hora": _number(lph, "0.001"),
                "cantidad_cargas": values["cargas"],
                "registros_produccion": values["registros"],
                "warnings": warnings,
            }
        )
    results.sort(key=lambda row: (row["equipo"] or "", row["equipo_id"]))
    return results, sum(invalid_by_equipment.values())


def combustible_equipo_lh(inicio, fin, un_id=None, movil_id=None):
    results, invalid_intervals = _aggregate_period(inicio, fin, un_id, movil_id)
    total_liters = sum((_decimal(row["litros_egreso"]) for row in results), ZERO)
    total_hours = sum((_decimal(row["horas_operativas"]) for row in results), ZERO)
    total_lph = total_liters / total_hours if total_hours > ZERO else None
    return {
        "inicio": inicio.isoformat(),
        "fin": fin.isoformat(),
        "results": results,
        "totales": {
            "litros_egreso": _number(total_liters),
            "horas_operativas": _number(total_hours),
            "litros_por_hora": _number(total_lph, "0.001"),
            "cantidad_cargas": sum(row["cantidad_cargas"] for row in results),
            "registros_produccion": sum(row["registros_produccion"] for row in results),
        },
        "data_quality": {
            "intervalos_horas_invalidos": invalid_intervals,
            "formula_horas": "suma(hr_fin - hr_inicio) por registro cuando hr_fin > hr_inicio",
        },
    }


def combustible_equipo_vs_historico(inicio, fin, meses_atras=6, un_id=None, movil_id=None):
    historical_start = inicio - relativedelta(months=meses_atras)
    historical_end = fin - relativedelta(months=meses_atras)
    current, current_invalid = _aggregate_period(inicio, fin, un_id, movil_id)
    historical, historical_invalid = _aggregate_period(
        historical_start, historical_end, un_id, movil_id
    )
    current_map = {row["equipo_id"]: row for row in current}
    historical_map = {row["equipo_id"]: row for row in historical}
    results = []
    equipment_ids = set(current_map) | set(historical_map)
    for equipment_id in sorted(equipment_ids):
        old = historical_map.get(equipment_id)
        row = current_map.get(equipment_id)
        identity = row or old
        if row is None:
            row = {
                "equipo_id": equipment_id,
                "equipo": identity["equipo"],
                "unidad_negocio": identity["unidad_negocio"],
                "litros_egreso": 0.0,
                "horas_operativas": 0.0,
                "litros_por_hora": None,
                "warnings": [],
            }
        current_lph = row["litros_por_hora"]
        old_lph = old["litros_por_hora"] if old else None
        warnings = list(row["warnings"])
        difference = None
        variation = None
        semaphore = "sin_datos"
        if old_lph is None:
            warnings.append("muestra_historica_insuficiente")
        elif _decimal(old_lph) <= ZERO:
            warnings.append("base_historica_nula_o_cero")
        elif current_lph is None:
            warnings.append("muestra_actual_insuficiente")
        else:
            difference = _decimal(current_lph) - _decimal(old_lph)
            variation = difference / _decimal(old_lph) * Decimal("100")
            if variation <= SEMAFORO_VERDE_MAX_PCT:
                semaphore = "verde"
            elif variation <= SEMAFORO_AMARILLO_MAX_PCT:
                semaphore = "amarillo"
            else:
                semaphore = "rojo"
        results.append(
            {
                "equipo_id": row["equipo_id"],
                "equipo": row["equipo"],
                "unidad_negocio": row["unidad_negocio"],
                "litros_por_hora_actual": current_lph,
                "litros_por_hora_historico": old_lph,
                "diferencia_absoluta": _number(difference, "0.001"),
                "variacion_porcentual": _number(variation, "0.01"),
                "semaforo": semaphore,
                "litros_actual": row["litros_egreso"],
                "horas_actual": row["horas_operativas"],
                "litros_historico": old["litros_egreso"] if old else 0.0,
                "horas_historico": old["horas_operativas"] if old else 0.0,
                "warnings": list(dict.fromkeys(warnings)),
            }
        )
    return {
        "periodo_actual": {"inicio": inicio.isoformat(), "fin": fin.isoformat()},
        "periodo_historico": {
            "inicio": historical_start.isoformat(),
            "fin": historical_end.isoformat(),
        },
        "meses_atras": meses_atras,
        "umbrales_porcentuales": {
            "verde_hasta": _number(SEMAFORO_VERDE_MAX_PCT),
            "amarillo_hasta": _number(SEMAFORO_AMARILLO_MAX_PCT),
        },
        "results": results,
        "data_quality": {
            "intervalos_horas_invalidos_actual": current_invalid,
            "intervalos_horas_invalidos_historico": historical_invalid,
        },
    }


def combustible_sin_produccion(inicio, fin, un_id=None, movil_id=None):
    fuel, production = _base_querysets(inicio, fin, un_id, movil_id)
    grouped_loads = list(
        fuel.values("fecha", "equipo_id")
        .annotate(litros=Sum("litros"), cantidad_cargas=Count("id"))
        .order_by("fecha", "equipo_id")
    )
    production_keys = set(production.values_list("fecha", "cod_equipo_id").distinct())
    equipment_ids = {row["equipo_id"] for row in grouped_loads if row["equipo_id"]}
    equipment = {
        item.id: item
        for item in Equipo.objects.filter(id__in=equipment_ids).select_related("unidad_negocio")
    }
    results = []
    unidentified = 0
    orphaned = 0
    for row in grouped_loads:
        equipment_id = row["equipo_id"]
        if not equipment_id:
            unidentified += row["cantidad_cargas"]
            continue
        if equipment_id not in equipment:
            orphaned += row["cantidad_cargas"]
            continue
        if (row["fecha"], equipment_id) in production_keys:
            continue
        obj = equipment[equipment_id]
        results.append(
            {
                "fecha": row["fecha"].isoformat(),
                "equipo_id": equipment_id,
                "equipo": obj.detalle or obj.patente or str(equipment_id),
                "unidad_negocio": obj.unidad_negocio.nombre if obj.unidad_negocio else None,
                "litros_egreso": _number(row["litros"]),
                "cantidad_cargas": row["cantidad_cargas"],
                "motivo": (
                    "Egreso sin registro de producción compatible en la misma fecha; "
                    "inconsistencia para revisión, no error definitivo."
                ),
            }
        )
    return {
        "inicio": inicio.isoformat(),
        "fin": fin.isoformat(),
        "results": results,
        "data_quality": {
            "cargas_sin_equipo_identificado": unidentified,
            "cargas_con_equipo_id_huerfano": orphaned,
            "comparacion_fecha": "DateField local America/Argentina/Buenos_Aires",
        },
    }
