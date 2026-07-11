from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase

from .facturacion_services import FacturacionParamsSerializer, _calculate_row


class FacturacionParamsTests(SimpleTestCase):
    def test_rejects_inverted_and_excessive_ranges(self):
        inverted = FacturacionParamsSerializer(data={
            "start_date": "2026-07-02", "end_date": "2026-07-01", "movil_id": 1
        })
        self.assertFalse(inverted.is_valid())
        excessive = FacturacionParamsSerializer(data={
            "start_date": "2025-01-01", "end_date": "2026-07-01", "movil_id": 1
        })
        self.assertFalse(excessive.is_valid())

    def test_quote_is_always_simulation(self):
        serializer = FacturacionParamsSerializer(data={
            "start_date": "2026-07-01", "end_date": "2026-07-02", "movil_id": 1,
            "cotizacion": "1325.000000",
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["moneda"], "ARS")


class FacturacionCalculationTests(SimpleTestCase):
    row = {
        "id": 7, "fecha": date(2026, 7, 1), "cod_equipo_id": 8, "cod_un_id": 9,
        "operacion": "PROCESO", "produccion": Decimal("1250.50"),
        "unidad_produccion": "TN", "origen_camion__precio": None,
    }

    def test_calculated_uses_decimal_formula(self):
        monthly = {
            "coeficiente": Decimal("1.10"), "cotizacion": Decimal("1"),
            "tarifa": Decimal("8.50"), "unidad_tarifa": "TN",
        }
        result = _calculate_row(self.row, monthly, Decimal("0"))
        self.assertEqual(result["estado_calculo"], "calculado")
        self.assertEqual(result["facturacion_total"], "11692.18")
        self.assertIsNone(result["facturacion_simulada"])

    def test_historical_quote_is_required_not_assumed(self):
        monthly = {
            "coeficiente": Decimal("1.10"), "cotizacion": Decimal("1420"),
            "tarifa": Decimal("8.50"), "unidad_tarifa": "TN",
        }
        result = _calculate_row(self.row, monthly, Decimal("0"))
        self.assertEqual(result["estado_calculo"], "requiere_cotizacion")
        self.assertIsNone(result["facturacion_total"])

    def test_explicit_quote_creates_separate_simulation(self):
        monthly = {
            "coeficiente": Decimal("1.10"), "cotizacion": Decimal("1420"),
            "tarifa": Decimal("8.50"), "unidad_tarifa": "TN",
        }
        result = _calculate_row(
            self.row, monthly, Decimal("0"), Decimal("1325"), "ARS"
        )
        self.assertEqual(result["estado_calculo"], "simulacion")
        self.assertIsNone(result["facturacion_total"])
        self.assertEqual(result["facturacion_simulada"], "15492131.88")

    def test_missing_tariff_is_explicit(self):
        result = _calculate_row(self.row, None, Decimal("0"))
        self.assertEqual(result["estado_calculo"], "sin_tarifa")
        self.assertIn("tarifa_base", result["faltantes"])
