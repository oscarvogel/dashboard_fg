from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Sum
from rest_framework import serializers

from .models import Equipo, ProduccionMensual, RegistroProduccion


MAX_RANGE_DAYS = 366
ZERO = Decimal("0")
ONE = Decimal("1")


class FacturacionParamsSerializer(serializers.Serializer):
    start_date = serializers.DateField(input_formats=["%Y-%m-%d"])
    end_date = serializers.DateField(input_formats=["%Y-%m-%d"])
    movil_id = serializers.IntegerField(min_value=1)
    un_id = serializers.IntegerField(required=False, min_value=1)
    cotizacion = serializers.DecimalField(
        required=False, max_digits=20, decimal_places=6, min_value=Decimal("0.000001")
    )
    moneda = serializers.ChoiceField(required=False, choices=("ARS", "USD"))

    def validate(self, attrs):
        if attrs["end_date"] < attrs["start_date"]:
            raise serializers.ValidationError(
                {"end_date": "Debe ser igual o posterior a start_date."}
            )
        days = (attrs["end_date"] - attrs["start_date"]).days + 1
        if days > MAX_RANGE_DAYS:
            raise serializers.ValidationError(
                {"end_date": f"El rango máximo permitido es de {MAX_RANGE_DAYS} días."}
            )
        if "moneda" in attrs and "cotizacion" not in attrs:
            raise serializers.ValidationError(
                {"moneda": "Sólo se admite junto con cotizacion para una simulación."}
            )
        if "cotizacion" in attrs and "moneda" not in attrs:
            attrs["moneda"] = "ARS"
        return attrs


def parse_facturacion_params(query_params):
    serializer = FacturacionParamsSerializer(data=query_params)
    serializer.is_valid(raise_exception=True)
    return dict(serializer.validated_data)


def _d(value, default=ZERO):
    if value is None:
        return default
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _text(value, places=None):
    if value is None:
        return None
    value = _d(value)
    if places:
        value = value.quantize(Decimal(places), rounding=ROUND_HALF_UP)
    return format(value, "f")


def _period(value: date):
    return value.strftime("%Y%m")


def _select_monthly(monthly_rows, row):
    exact = None
    fallback = None
    for item in monthly_rows:
        if (
            item["periodo"] == _period(row["fecha"])
            and item["unidad_negocio_id"] == row["cod_un_id"]
            and (item["tipo_operacion"] or "").strip() == (row["operacion"] or "").strip()
        ):
            if item["equipo_id"] == row["cod_equipo_id"]:
                exact = item
                break
            if item["equipo_id"] is None and fallback is None:
                fallback = item
    return exact or fallback


def _calculate_row(row, monthly, unit_sum, simulation_rate=None, simulation_currency=None):
    production = _d(row["produccion"])
    coefficient = ONE
    tariff = _d(unit_sum)
    tariff_source = "unitario_sum" if tariff > ZERO else None
    production_unit = (row.get("unidad_produccion") or "").strip() or None
    billing_unit = None
    persisted_quote = None
    missing = []

    if monthly:
        raw_coefficient = _d(monthly.get("coeficiente"), ONE)
        coefficient = raw_coefficient if raw_coefficient > ZERO else ONE
        billing_unit = (monthly.get("unidad_tarifa") or "").strip() or None
        persisted_quote = _d(monthly.get("cotizacion"), ONE)
        if persisted_quote <= ZERO:
            persisted_quote = ONE
        if tariff <= ZERO:
            tariff = _d(monthly.get("tarifa"))
            tariff_source = "produccion_mensual" if tariff > ZERO else None

    if tariff <= ZERO:
        origin_price = _d(row.get("origen_camion__precio"))
        if origin_price > ZERO:
            tariff = origin_price
            tariff_source = "origen_precio"

    valued_quantity = production * coefficient
    requires_quote = persisted_quote is not None and persisted_quote > ONE
    historical_total = None
    simulated_total = None
    currency = "ARS" if not requires_quote else None

    if production <= ZERO:
        state = "datos_incompatibles"
        missing.append("produccion_positiva")
    elif tariff <= ZERO:
        state = "sin_tarifa"
        missing.append("tarifa_base")
    elif requires_quote:
        state = "requiere_cotizacion"
        missing.extend(("cotizacion_historica_aplicada", "moneda_confirmada"))
    else:
        historical_total = valued_quantity * tariff
        state = "calculado"

    if not production_unit:
        missing.append("unidad_produccion")
    if not billing_unit:
        missing.append("unidad_facturable")
    if state == "calculado" and missing:
        historical_total = None
        state = "parcial"

    warnings = []
    if simulation_rate is not None and tariff > ZERO and production > ZERO:
        simulated_total = valued_quantity * tariff * simulation_rate
        state = "simulacion"
        currency = simulation_currency
        warnings.extend(
            (
                "El importe fue simulado con una cotización proporcionada en la consulta.",
                "No representa necesariamente la facturación histórica efectivamente calculada.",
            )
        )

    return {
        "registro_id": row["id"],
        "fecha": row["fecha"].isoformat(),
        "estado_calculo": state,
        "moneda": currency,
        "unidad_produccion": production_unit,
        "unidad_facturable": billing_unit,
        "fuente_tarifa": tariff_source,
        "componentes": {
            "produccion": _text(production, "0.01"),
            "coeficiente": _text(coefficient, "0.000001"),
            "tarifa_base": _text(tariff, "0.0001") if tariff > ZERO else None,
            "cotizacion_persistida": _text(persisted_quote, "0.000001"),
            "cotizacion_simulacion": _text(simulation_rate, "0.000001"),
        },
        "cantidad_valorizada": _text(valued_quantity, "0.01"),
        "facturacion_total": _text(historical_total, "0.01"),
        "facturacion_simulada": _text(simulated_total, "0.01"),
        "faltantes": list(dict.fromkeys(missing)),
        "advertencias": warnings,
    }


def calcular_facturacion_movil(
    *, start_date, end_date, movil_id, un_id=None, cotizacion=None, moneda=None
):
    equipment = Equipo.objects.select_related("unidad_negocio").filter(id=movil_id).first()
    if equipment is None:
        raise Equipo.DoesNotExist

    activity = RegistroProduccion.objects.filter(
        fecha__range=(start_date, end_date), cod_equipo_id=movil_id
    )
    if un_id:
        activity = activity.filter(cod_un_id=un_id)
    rows = list(
        activity.values(
            "id", "fecha", "cod_equipo_id", "cod_un_id", "operacion", "produccion",
            "unidad_produccion", "origen_camion__precio",
        ).order_by("fecha", "id")
    )
    if not rows:
        return _empty_result(equipment, start_date, end_date)

    periods = {_period(row["fecha"]) for row in rows}
    un_ids = {row["cod_un_id"] for row in rows if row["cod_un_id"]}
    operations = {row["operacion"] for row in rows}
    monthly_rows = list(
        ProduccionMensual.objects.filter(
            periodo__in=periods,
            unidad_negocio_id__in=un_ids,
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
    simulation_rate = _d(cotizacion) if cotizacion is not None else None
    details = []
    for row in rows:
        monthly = _select_monthly(monthly_rows, row)
        details.append(
            _calculate_row(
                row,
                monthly,
                unit_sums.get((row["cod_un_id"], row["operacion"]), ZERO),
                simulation_rate,
                moneda,
            )
        )
    return _assemble_result(equipment, start_date, end_date, details)


def _empty_result(equipment, start_date, end_date):
    return {
        "movil": _equipment(equipment),
        "periodo": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        "estado_calculo": "sin_actividad",
        "totales_por_moneda": [],
        "totales_simulados_por_moneda": [],
        "cantidades_por_unidad": [],
        "desglose": [],
        "registros": {"incluidos": 0, "excluidos": 0, "sin_tarifa": 0},
        "cobertura": {"porcentaje_calculado": "0.00", "completa": False},
        "advertencias": ["El móvil no tiene actividad en el período solicitado."],
    }


def _equipment(obj):
    return {
        "id": obj.id,
        "codigo": obj.codigo_fg or None,
        "patente": obj.patente or None,
        "descripcion": obj.detalle or None,
    }


def _assemble_result(equipment, start_date, end_date, details):
    historical = defaultdict(Decimal)
    simulated = defaultdict(Decimal)
    quantities = defaultdict(Decimal)
    calculated = 0
    for item in details:
        if item["facturacion_total"] is not None:
            historical[item["moneda"]] += _d(item["facturacion_total"])
            calculated += 1
        if item["facturacion_simulada"] is not None:
            simulated[item["moneda"]] += _d(item["facturacion_simulada"])
        if item["unidad_facturable"]:
            quantities[item["unidad_facturable"]] += _d(item["cantidad_valorizada"])
    states = {item["estado_calculo"] for item in details}
    overall = next(iter(states)) if len(states) == 1 else "parcial"
    coverage = Decimal(calculated) / Decimal(len(details)) * Decimal("100")
    return {
        "movil": _equipment(equipment),
        "periodo": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        "estado_calculo": overall,
        "totales_por_moneda": [
            {"moneda": key, "total": _text(value, "0.01")}
            for key, value in sorted(historical.items())
        ],
        "totales_simulados_por_moneda": [
            {"moneda": key, "total": _text(value, "0.01")}
            for key, value in sorted(simulated.items())
        ],
        "cantidades_por_unidad": [
            {"unidad": key, "cantidad": _text(value, "0.01")}
            for key, value in sorted(quantities.items())
        ],
        "desglose": details,
        "registros": {
            "incluidos": len(details),
            "excluidos": 0,
            "sin_tarifa": sum(item["estado_calculo"] == "sin_tarifa" for item in details),
        },
        "cobertura": {
            "porcentaje_calculado": _text(coverage, "0.01"),
            "completa": calculated == len(details),
        },
        "advertencias": sorted(
            {warning for item in details for warning in item["advertencias"]}
        ),
    }
