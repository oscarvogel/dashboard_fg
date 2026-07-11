from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .indicadores_services import _build_indicators


class IndicatorCalculationTests(APITestCase):
    def test_missing_historical_total_returns_null_with_reason(self):
        billing = {"totales_por_moneda": [], "totales_simulados_por_moneda": []}
        operational = {
            "combustible": {"litros_egreso": "100.00"},
            "produccion": {"horas_validas": "20.00", "cantidades_por_unidad": []},
        }
        result = _build_indicators(billing, operational)
        self.assertIsNone(result["facturacion_por_litro"]["valor"])
        self.assertEqual(
            result["razones_no_disponibles"]["facturacion_por_litro"],
            "numerador_no_disponible",
        )

    def test_compatible_operational_and_simulated_ratios_are_separate(self):
        billing = {
            "totales_por_moneda": [{"moneda": "ARS", "total": "1000.00"}],
            "totales_simulados_por_moneda": [{"moneda": "ARS", "total": "2000.00"}],
        }
        operational = {
            "combustible": {"litros_egreso": "100.00"},
            "produccion": {
                "horas_validas": "20.00",
                "cantidades_por_unidad": [{"unidad": "TN", "cantidad": "50.00"}],
            },
        }
        result = _build_indicators(billing, operational)
        self.assertEqual(result["facturacion_por_litro"]["valor"], "10.000")
        self.assertEqual(result["facturacion_simulada_por_litro"]["valor"], "20.000")
        self.assertEqual(result["produccion_por_unidad"][0]["produccion_por_litro"], "0.500")


class MovilOperativoAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="indicator-reader", password="test-pass")

    def setUp(self):
        self.client = APIClient()
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.url = reverse("movil-operativo")
        self.params = {
            "start_date": "2026-07-01", "end_date": "2026-07-07", "movil_id": 208
        }

    def test_requires_auth_and_rejects_writes(self):
        self.client.credentials()
        self.assertEqual(self.client.get(self.url, self.params).status_code, 401)
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        for method in ("post", "put", "patch", "delete"):
            self.assertEqual(getattr(self.client, method)(self.url, {}).status_code, 405)

    @patch("produccion.views.calcular_movil_operativo")
    def test_previous_period_parameter_is_forwarded(self, calculate):
        calculate.return_value = {
            "movil": {"id": 208}, "periodo": {}, "facturacion": {}, "produccion": {},
            "combustible": {}, "indicadores": {}, "comparacion_periodo_anterior": {},
            "calidad_datos": {},
        }
        response = self.client.get(self.url, {**self.params, "compare": "previous_period"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(calculate.call_args.kwargs["compare"], "previous_period")

    def test_invalid_compare_returns_400(self):
        response = self.client.get(self.url, {**self.params, "compare": "last_month"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("compare", response.data)
