from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .equipo_aliases import confirm_equipo_alias
from .models import Equipo, UnidadNegocio


class ResolucionMovilIndicadoresIntegrationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username="bot-resolver", email="resolver@example.invalid", password="test-pass"
        )
        cls.un = UnidadNegocio.objects.create(nombre="BIOMASA")
        cls.equipment = Equipo.objects.create(
            patente="CHI-003", codigo_fg="CHI-3", detalle="Chipeadora tres",
            unidad_negocio=cls.un,
        )
        confirm_equipo_alias(
            equipo=cls.equipment, alias="Chipeadora azul",
            confirmado_por=cls.user, origen="manual",
        )

    def setUp(self):
        self.client = APIClient()
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    @patch("produccion.views.calcular_movil_operativo")
    def test_human_alias_resolves_before_indicator_query(self, calculate):
        search = self.client.get(reverse("equipos-search"), {"q": "chipeadora-azul"})
        self.assertEqual(search.status_code, 200)
        self.assertFalse(search.data["requires_confirmation"])
        self.assertEqual(search.data["results"][0]["id"], self.equipment.id)
        calculate.return_value = {
            "movil": {"id": self.equipment.id}, "periodo": {}, "facturacion": {},
            "produccion": {}, "combustible": {}, "indicadores": {},
            "comparacion_periodo_anterior": None, "calidad_datos": {},
        }
        indicator = self.client.get(reverse("movil-operativo"), {
            "start_date": "2026-07-01", "end_date": "2026-07-07",
            "movil_id": search.data["results"][0]["id"],
        })
        self.assertEqual(indicator.status_code, 200)
        self.assertEqual(calculate.call_args.kwargs["movil_id"], self.equipment.id)

    def test_ambiguous_reference_requires_confirmation(self):
        Equipo.objects.create(
            patente="CHI-004", codigo_fg="CHI-4", detalle="Chipeadora cuatro",
            unidad_negocio=self.un,
        )
        search = self.client.get(reverse("equipos-search"), {"q": "chipeadora"})
        self.assertEqual(search.status_code, 200)
        self.assertTrue(search.data["requires_confirmation"])
        self.assertGreaterEqual(search.data["total"], 2)
