from collections import defaultdict
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Case, Count, DecimalField, F, Sum, Value, When
from rest_framework import serializers

from .facturacion_services import (
    FacturacionParamsSerializer,
    calcular_facturacion_movil,
)
from .models import CargaCombustible, RegistroProduccion


ZERO = Decimal("0")


class MovilOperativoParamsSerializer(FacturacionParamsSerializer):
    compare = serializers.ChoiceField(
        required=False, choices=("none", "previous_period"), default="none"
    )


def parse_movil_operativo_params(query_params):
    serializer = MovilOperativoParamsSerializer(data=query_params)
    serializer.is_valid(raise_exception=True)
    return dict(serializer.validated_data)


def _d(value):
    if value is None:
        return ZERO
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _text(value, places="0.01"):
    if value is None:
        return None
    return format(_d(value).quantize(Decimal(places), rounding=ROUND_HALF_UP), "f")


def _ratio(numerator, denominator):
    if numerator is None:
        return None, "numerador_no_disponible"
    if denominator is None or _d(denominator) <= ZERO:
        return None, "denominador_no_disponible_o_no_positivo"
    return _d(numerator) / _d(denominator), None


def _production_and_fuel(start_date, end_date, movil_id, un_id=None):
    production = RegistroProduccion.objects.filter(
        fecha__range=(start_date, end_date), cod_equipo_id=movil_id
    )
    fuel = CargaCombustible.objects.filter(
        fecha__range=(start_date, end_date), equipo_id=movil_id, tipo_mov="E"
    )
    if un_id:
        production = production.filter(cod_un_id=un_id)
        fuel = fuel.filter(unidad_negocio_id=un_id)

    production_rows = list(
        production.values("unidad_produccion")
        .annotate(cantidad=Sum("produccion"), registros=Count("id"))
        .order_by("unidad_produccion")
    )
    valid_hours = Case(
        When(hr_fin__gt=F("hr_inicio"), then=F("hr_fin") - F("hr_inicio")),
        default=Value(ZERO),
        output_field=DecimalField(max_digits=20, decimal_places=2),
    )
    hours = production.aggregate(
        horas=Sum(valid_hours), registros=Count("id")
    )
    invalid_hours = production.filter(hr_fin__lte=F("hr_inicio")).count()
    fuel_data = fuel.aggregate(
        litros=Sum("litros"), cargas=Count("id"), dias=Count("fecha", distinct=True)
    )
    units = [
        {
            "unidad": (row["unidad_produccion"] or "").strip() or "DESCONOCIDA",
            "cantidad": _text(row["cantidad"]),
            "registros": row["registros"],
        }
        for row in production_rows
    ]
    return {
        "produccion": {
            "cantidades_por_unidad": units,
            "horas_validas": _text(hours["horas"]),
            "registros": hours["registros"],
            "intervalos_horas_invalidos": invalid_hours,
        },
        "combustible": {
            "litros_egreso": _text(fuel_data["litros"]),
            "cantidad_cargas": fuel_data["cargas"],
            "dias_con_consumo": fuel_data["dias"],
        },
    }


def _single_total(items):
    if len(items) != 1:
        return None, None
    return _d(items[0]["total"]), items[0]["moneda"]


def _build_indicators(facturacion, operational):
    liters = _d(operational["combustible"]["litros_egreso"])
    hours = _d(operational["produccion"]["horas_validas"])
    historical, currency = _single_total(facturacion["totales_por_moneda"])
    simulated, simulated_currency = _single_total(
        facturacion["totales_simulados_por_moneda"]
    )
    values = {}
    reasons = {}

    for name, numerator, denominator in (
        ("facturacion_por_litro", historical, liters),
        ("facturacion_por_hora", historical, hours),
        ("litros_por_hora", liters, hours),
    ):
        value, reason = _ratio(numerator, denominator)
        values[name] = {"valor": _text(value, "0.001"), "moneda": currency if name.startswith("facturacion") else None}
        if reason:
            reasons[name] = reason

    production_ratios = []
    for item in operational["produccion"]["cantidades_por_unidad"]:
        quantity = _d(item["cantidad"])
        production_per_liter, r1 = _ratio(quantity, liters)
        liters_per_unit, r2 = _ratio(liters, quantity)
        billing_per_unit, r3 = _ratio(historical, quantity)
        simulated_per_unit, r4 = _ratio(simulated, quantity)
        production_ratios.append(
            {
                "unidad": item["unidad"],
                "produccion_por_litro": _text(production_per_liter, "0.001"),
                "litros_por_unidad_producida": _text(liters_per_unit, "0.001"),
                "facturacion_por_unidad": _text(billing_per_unit, "0.001"),
                "moneda_facturacion": currency,
                "facturacion_simulada_por_unidad": _text(simulated_per_unit, "0.001"),
                "moneda_simulacion": simulated_currency,
                "razones_no_disponibles": [r for r in (r1, r2, r3, r4) if r],
            }
        )
    simulated_liter, sr1 = _ratio(simulated, liters)
    simulated_hour, sr2 = _ratio(simulated, hours)
    values["facturacion_simulada_por_litro"] = {
        "valor": _text(simulated_liter, "0.001"), "moneda": simulated_currency
    }
    values["facturacion_simulada_por_hora"] = {
        "valor": _text(simulated_hour, "0.001"), "moneda": simulated_currency
    }
    if sr1:
        reasons["facturacion_simulada_por_litro"] = sr1
    if sr2:
        reasons["facturacion_simulada_por_hora"] = sr2
    values["produccion_por_unidad"] = production_ratios
    values["razones_no_disponibles"] = reasons
    return values


def _comparison(current, previous):
    result = {"periodo_anterior": previous["periodo"], "metricas": {}}
    pairs = {
        "litros": (
            current["combustible"]["litros_egreso"], previous["combustible"]["litros_egreso"]
        ),
        "horas": (
            current["produccion"]["horas_validas"], previous["produccion"]["horas_validas"]
        ),
    }
    for name, (now, old) in pairs.items():
        absolute = _d(now) - _d(old)
        percentage, reason = _ratio(absolute * Decimal("100"), _d(old))
        result["metricas"][name] = {
            "actual": now,
            "anterior": old,
            "variacion_absoluta": _text(absolute),
            "variacion_porcentual": _text(percentage),
            "razon_no_disponible": reason,
        }
    return result


def calcular_movil_operativo(
    *, start_date, end_date, movil_id, un_id=None, cotizacion=None, moneda=None,
    compare="none"
):
    billing = calcular_facturacion_movil(
        start_date=start_date, end_date=end_date, movil_id=movil_id, un_id=un_id,
        cotizacion=cotizacion, moneda=moneda,
    )
    operational = _production_and_fuel(start_date, end_date, movil_id, un_id)
    result = {
        "movil": billing["movil"],
        "periodo": billing["periodo"],
        "facturacion": billing,
        "produccion": operational["produccion"],
        "combustible": operational["combustible"],
        "indicadores": _build_indicators(billing, operational),
        "comparacion_periodo_anterior": None,
        "calidad_datos": {
            "cobertura_facturacion": billing["cobertura"],
            "cross_un": (
                "un_id filtra independientemente cod_un de producción y UnidadNegocio "
                "de combustible; sin un_id ambas fuentes se cruzan por movil_id y fecha."
            ),
        },
    }
    if compare == "previous_period":
        days = (end_date - start_date).days + 1
        previous_end = start_date - timedelta(days=1)
        previous_start = previous_end - timedelta(days=days - 1)
        previous_billing = calcular_facturacion_movil(
            start_date=previous_start, end_date=previous_end, movil_id=movil_id,
            un_id=un_id, cotizacion=cotizacion, moneda=moneda,
        )
        previous_operational = _production_and_fuel(
            previous_start, previous_end, movil_id, un_id
        )
        previous_operational["periodo"] = {
            "start_date": previous_start.isoformat(), "end_date": previous_end.isoformat()
        }
        result["comparacion_periodo_anterior"] = _comparison(
            {**operational, "periodo": billing["periodo"]}, previous_operational
        )
        result["comparacion_periodo_anterior"]["facturacion"] = {
            "actual": billing["totales_por_moneda"],
            "anterior": previous_billing["totales_por_moneda"],
            "nota": "Las variaciones financieras sólo son comparables por la misma moneda.",
        }
    return result
