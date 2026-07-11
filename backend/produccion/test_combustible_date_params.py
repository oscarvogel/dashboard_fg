from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


class CombustibleDateParamsCompatibilityTests(TestCase):
    endpoint_names = (
        "combustible-equipo-lh",
        "combustible-equipo-vs-historico",
        "combustible-sin-produccion",
    )
    inicio = "2026-07-01"
    fin = "2026-07-07"

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="fuel-date-reader",
            password="test-pass",
        )

    def setUp(self):
        self.client = APIClient()
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def assert_status_for_all(self, params, expected_status):
        for name in self.endpoint_names:
            with self.subTest(endpoint=name, params=params):
                response = self.client.get(reverse(name), params)
                self.assertEqual(response.status_code, expected_status)

    def test_endpoints_accept_start_date_and_end_date(self):
        self.assert_status_for_all(
            {"start_date": self.inicio, "end_date": self.fin},
            200,
        )

    def test_endpoints_keep_inicio_and_fin_as_legacy_aliases(self):
        self.assert_status_for_all(
            {"inicio": self.inicio, "fin": self.fin},
            200,
        )

    def test_endpoints_accept_both_equal_date_pairs(self):
        self.assert_status_for_all(
            {
                "start_date": self.inicio,
                "end_date": self.fin,
                "inicio": self.inicio,
                "fin": self.fin,
            },
            200,
        )

    def test_endpoints_reject_incomplete_or_mixed_date_pairs(self):
        invalid_cases = (
            {"start_date": self.inicio},
            {"end_date": self.fin},
            {"inicio": self.inicio},
            {"fin": self.fin},
            {"start_date": self.inicio, "fin": self.fin},
            {"inicio": self.inicio, "end_date": self.fin},
            {
                "start_date": self.inicio,
                "end_date": self.fin,
                "inicio": self.inicio,
            },
            {
                "start_date": self.inicio,
                "inicio": self.inicio,
                "fin": self.fin,
            },
        )
        for params in invalid_cases:
            for name in self.endpoint_names:
                with self.subTest(endpoint=name, params=params):
                    response = self.client.get(reverse(name), params)
                    self.assertEqual(response.status_code, 400)
                    self.assertIn("date_range", response.json())

    def test_endpoints_reject_conflicting_date_pairs(self):
        params = {
            "start_date": self.inicio,
            "end_date": self.fin,
            "inicio": self.inicio,
            "fin": "2026-07-08",
        }
        for name in self.endpoint_names:
            with self.subTest(endpoint=name):
                response = self.client.get(reverse(name), params)
                self.assertEqual(response.status_code, 400)
                self.assertIn("date_range", response.json())
                self.assertIn("mismo rango", response.json()["date_range"][0])

    def test_canonical_params_keep_existing_date_validations(self):
        invalid_cases = (
            {"start_date": "01-07-2026", "end_date": self.fin},
            {"start_date": self.fin, "end_date": self.inicio},
            {"start_date": "2025-01-01", "end_date": "2026-07-07"},
        )
        for params in invalid_cases:
            for name in self.endpoint_names:
                with self.subTest(endpoint=name, params=params):
                    response = self.client.get(reverse(name), params)
                    self.assertEqual(response.status_code, 400)
