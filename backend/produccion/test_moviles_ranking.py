from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .ranking_services import RankingParamsSerializer


class RankingParamsTests(APITestCase):
    def test_financial_metric_requires_currency(self):
        serializer = RankingParamsSerializer(data={
            "start_date": "2026-07-01", "end_date": "2026-07-07",
            "metric": "facturacion_total",
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("moneda", serializer.errors)

    def test_production_metric_requires_unit(self):
        serializer = RankingParamsSerializer(data={
            "start_date": "2026-07-01", "end_date": "2026-07-07",
            "metric": "produccion_por_litro",
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("unidad", serializer.errors)

    def test_page_size_and_metric_are_allowlisted(self):
        for data, field in (
            ({"metric": "drop_table", "page_size": 10}, "metric"),
            ({"metric": "litros_combustible", "page_size": 101}, "page_size"),
        ):
            serializer = RankingParamsSerializer(data={
                "start_date": "2026-07-01", "end_date": "2026-07-07", **data,
            })
            self.assertFalse(serializer.is_valid())
            self.assertIn(field, serializer.errors)


class RankingAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="ranking-reader", password="test-pass")

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("moviles-ranking")
        self.params = {
            "start_date": "2026-07-01", "end_date": "2026-07-07",
            "metric": "litros_combustible",
        }

    def authenticate(self):
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_requires_authentication(self):
        self.assertEqual(self.client.get(self.url, self.params).status_code, 401)

    def test_rejects_writes(self):
        self.authenticate()
        for method in ("post", "put", "patch", "delete"):
            self.assertEqual(getattr(self.client, method)(self.url, {}).status_code, 405)

    @patch("produccion.views.calcular_ranking_moviles")
    def test_valid_request_delegates_to_bulk_service(self, calculate):
        self.authenticate()
        calculate.return_value = {"results": [], "datos_insuficientes": [], "paginacion": {}}
        response = self.client.get(self.url, self.params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(calculate.call_args.kwargs["metric"], "litros_combustible")
