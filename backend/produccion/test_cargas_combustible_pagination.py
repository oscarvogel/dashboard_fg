from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CargaCombustible, Equipo, LugarCarga, UnidadNegocio


class CargasCombustiblePaginationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="fuel-pages", password="test-pass")
        cls.un_1 = UnidadNegocio.objects.create(nombre="FULL TREE")
        cls.un_2 = UnidadNegocio.objects.create(nombre="BIOMASA")
        cls.equipo_1 = Equipo.objects.create(
            patente="AA 123 BB", detalle="Equipo uno", unidad_negocio=cls.un_1
        )
        cls.equipo_2 = Equipo.objects.create(
            patente="CC 456 DD", detalle="Equipo dos", unidad_negocio=cls.un_2
        )
        cls.lugar_1 = LugarCarga.objects.create(detalle="Tanque principal")
        cls.lugar_2 = LugarCarga.objects.create(detalle="Tanque secundario")

        cls.cargas = []
        for index in range(7):
            equipo = cls.equipo_1 if index % 2 == 0 else cls.equipo_2
            lugar = cls.lugar_1 if index < 4 else cls.lugar_2
            cls.cargas.append(
                CargaCombustible.objects.create(
                    equipo=equipo,
                    fecha=date(2026, 7, 1) if index < 5 else date(2026, 7, 2),
                    litros=Decimal(str((index + 1) * 10)),
                    tipo_mov="I" if index in (0, 5) else "E",
                    unidad_negocio=equipo.unidad_negocio,
                    lugar_carga=lugar,
                )
            )

    def setUp(self):
        self.client = APIClient()
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.url = reverse("cargas-combustible")

    def params(self, **extra):
        return {
            "start_date": "2026-07-01",
            "end_date": "2026-07-02",
            **extra,
        }

    def ids(self, response):
        return [row["id"] for row in response.json()["results"]]

    def test_requiere_autenticacion(self):
        self.client.credentials()
        response = self.client.get(self.url, self.params())
        self.assertIn(response.status_code, (401, 403))

    def test_valida_fechas_y_rango_invertido(self):
        for params in (
            {"start_date": "2026/07/01", "end_date": "2026-07-02"},
            {"start_date": "2026-07-01", "end_date": "invalida"},
            {"start_date": "2026-07-02", "end_date": "2026-07-01"},
        ):
            with self.subTest(params=params):
                self.assertEqual(self.client.get(self.url, params).status_code, 400)

    def test_valida_pagina_tamano_e_identificadores_enteros_positivos(self):
        for field, value in (
            ("page", "abc"),
            ("page", "0"),
            ("page_size", "abc"),
            ("page_size", "0"),
            ("un_id", "abc"),
            ("movil_id", "AA 123 BB"),
            ("lugar_id", "-1"),
        ):
            with self.subTest(field=field, value=value):
                response = self.client.get(self.url, self.params(**{field: value}))
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.json())

    def test_paginas_son_distintas_exhaustivas_y_sin_duplicados(self):
        page_1 = self.client.get(self.url, self.params(page=1, page_size=3))
        page_2 = self.client.get(self.url, self.params(page=2, page_size=3))
        self.assertNotEqual(self.ids(page_1), self.ids(page_2))

        seen = []
        for page in range(1, page_1.json()["total_pages"] + 1):
            response = self.client.get(self.url, self.params(page=page, page_size=3))
            page_ids = self.ids(response)
            self.assertTrue(set(seen).isdisjoint(page_ids))
            seen.extend(page_ids)

        expected = list(
            CargaCombustible.objects.filter(
                fecha__range=(date(2026, 7, 1), date(2026, 7, 2))
            ).values_list("id", flat=True)
        )
        self.assertEqual(len(seen), page_1.json()["count"])
        self.assertEqual(set(seen), set(expected))

    def test_respeta_page_size_y_lo_limita_a_200(self):
        response = self.client.get(self.url, self.params(page_size=2))
        self.assertEqual(len(response.json()["results"]), 2)
        self.assertEqual(response.json()["page_size"], 2)

        capped = self.client.get(self.url, self.params(page_size=999))
        self.assertEqual(capped.status_code, 200)
        self.assertEqual(capped.json()["page_size"], 200)

    def test_pagina_fuera_de_rango_es_vacia_y_conserva_metadatos(self):
        response = self.client.get(self.url, self.params(page=99, page_size=3))
        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["results"], [])
        self.assertEqual(payload["count"], 7)
        self.assertEqual(payload["total_pages"], 3)
        self.assertEqual(payload["current_page"], 99)
        self.assertEqual(payload["page_size"], 3)
        self.assertEqual(set(payload["totales"]), {"Ingreso", "Egreso"})

    def test_totales_son_globales_y_estables_en_todas_las_paginas(self):
        totals = []
        for page in (1, 2, 3, 99):
            response = self.client.get(self.url, self.params(page=page, page_size=3))
            totals.append(response.json()["totales"])
        self.assertTrue(all(total == totals[0] for total in totals))
        self.assertEqual(totals[0], {"Ingreso": 70.0, "Egreso": 210.0})

    def test_aplica_filtros_por_un_movil_patente_y_lugar(self):
        cases = (
            ({"un_id": self.un_1.id}, {row.id for row in self.cargas if row.unidad_negocio_id == self.un_1.id}),
            ({"movil_id": self.equipo_2.id}, {row.id for row in self.cargas if row.equipo_id == self.equipo_2.id}),
            ({"patente": "  aa 123 bb  "}, {row.id for row in self.cargas if row.equipo_id == self.equipo_1.id}),
            ({"lugar_id": self.lugar_2.id}, {row.id for row in self.cargas if row.lugar_carga_id == self.lugar_2.id}),
        )
        for filters, expected in cases:
            with self.subTest(filters=filters):
                response = self.client.get(self.url, self.params(page_size=200, **filters))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(set(self.ids(response)), expected)

    def test_patente_inexistente_y_no_parcial_devuelve_vacio(self):
        for patente in ("NO EXISTE", "AA 123"):
            with self.subTest(patente=patente):
                response = self.client.get(self.url, self.params(patente=patente))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["count"], 0)
                self.assertEqual(response.json()["results"], [])

    def test_orden_estable_por_fecha_e_id(self):
        response = self.client.get(self.url, self.params(page_size=200))
        expected = list(
            CargaCombustible.objects.order_by("fecha", "id").values_list("id", flat=True)
        )
        self.assertEqual(self.ids(response), expected)

    def test_compatibilidad_y_select_related_sin_n_mas_uno(self):
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(self.url, self.params(page_size=200))
        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertIn("results", payload)
        self.assertIn("totales", payload)
        self.assertIn("movil_detalle", payload["results"][0])
        self.assertIn("lugar_carga_detalle", payload["results"][0])
        self.assertLessEqual(len(captured), 6)
