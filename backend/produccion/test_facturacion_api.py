from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Equipo


class FacturacionMovilAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="billing-reader", password="test-pass")

    def setUp(self):
        self.client = APIClient()
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.url = reverse("facturacion-movil")
        self.params = {
            "start_date": "2026-07-01",
            "end_date": "2026-07-07",
            "movil_id": "208",
        }

    def test_requires_authentication(self):
        self.client.credentials()
        self.assertEqual(self.client.get(self.url, self.params).status_code, 401)

    @patch("produccion.views.calcular_facturacion_movil")
    def test_valid_request_returns_service_contract(self, calculate):
        calculate.return_value = {
            "movil": {"id": 208},
            "estado_calculo": "requiere_cotizacion",
            "totales_por_moneda": [],
            "desglose": [],
        }
        response = self.client.get(self.url, self.params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado_calculo"], "requiere_cotizacion")
        calculate.assert_called_once()
        self.assertEqual(calculate.call_args.kwargs["movil_id"], 208)

    @patch("produccion.views.calcular_facturacion_movil")
    def test_unknown_equipment_returns_404(self, calculate):
        calculate.side_effect = Equipo.DoesNotExist
        response = self.client.get(self.url, self.params)
        self.assertEqual(response.status_code, 404)
        self.assertIn("movil_id", response.data)

    def test_invalid_parameters_return_structured_400(self):
        cases = (
            ({}, "start_date"),
            ({**self.params, "start_date": "01-07-2026"}, "start_date"),
            ({**self.params, "start_date": "2026-07-08"}, "end_date"),
            ({**self.params, "movil_id": "0"}, "movil_id"),
            ({**self.params, "moneda": "USD"}, "moneda"),
        )
        for params, field in cases:
            with self.subTest(params=params):
                response = self.client.get(self.url, params)
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data)

    def test_write_methods_are_not_allowed(self):
        for method in ("post", "put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.url, self.params, format="json")
                self.assertEqual(response.status_code, 405)
