from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CargaCombustible, Equipo, Origen, RegistroProduccion, UnidadNegocio


class CombustibleConsultasAPITests(TestCase):
    inicio = "2026-07-01"
    fin = "2026-07-07"

    @classmethod
    def setUpClass(cls):
        # Origen is an unmanaged legacy table, but SQLite still enforces the
        # nullable FK declared by RegistroProduccion during isolated tests.
        with connection.schema_editor() as editor:
            editor.create_model(Origen)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        with connection.schema_editor() as editor:
            editor.delete_model(Origen)

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="fuel-reader", password="test-pass")
        cls.un = UnidadNegocio.objects.create(nombre="FULL TREE")
        cls.otra_un = UnidadNegocio.objects.create(nombre="BIOMASA")
        cls.equipo = Equipo.objects.create(
            patente="EQ-123", detalle="Tigercat 875", unidad_negocio=cls.un
        )
        cls.otro_equipo = Equipo.objects.create(
            patente="EQ-456", detalle="Ponsse Buffalo", unidad_negocio=cls.otra_un
        )
        cls.solo_produccion = Equipo.objects.create(
            patente="EQ-789", detalle="John Deere 1910", unidad_negocio=cls.un
        )

    def setUp(self):
        self.client = APIClient()
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def carga(self, equipo, fecha, litros, tipo_mov="E", unidad=None):
        return CargaCombustible.objects.create(
            equipo=equipo,
            fecha=fecha,
            litros=Decimal(litros),
            tipo_mov=tipo_mov,
            unidad_negocio=unidad or equipo.unidad_negocio,
        )

    def produccion(self, equipo, fecha, inicio, fin, unidad=None):
        return RegistroProduccion.objects.create(
            UN=(unidad or equipo.unidad_negocio).nombre,
            operacion="COSECHA",
            operador="Operador",
            fecha=fecha,
            equipo=equipo.detalle,
            cod_equipo=equipo,
            cod_un=unidad or equipo.unidad_negocio,
            hr_inicio=Decimal(inicio),
            hr_fin=Decimal(fin),
        )

    def params(self, **extra):
        return {"inicio": self.inicio, "fin": self.fin, **extra}

    def test_todos_los_endpoints_requieren_autenticacion(self):
        self.client.credentials()
        for name in (
            "combustible-equipo-lh",
            "combustible-equipo-vs-historico",
            "combustible-sin-produccion",
        ):
            with self.subTest(name=name):
                response = self.client.get(reverse(name), self.params())
                self.assertEqual(response.status_code, 401)

    def test_parametros_requeridos_invalidos_invertidos_y_rango_maximo(self):
        url = reverse("combustible-equipo-lh")
        cases = (
            ({}, "inicio"),
            ({"inicio": "01-07-2026", "fin": self.fin}, "inicio"),
            ({"inicio": self.fin, "fin": self.inicio}, "fin"),
            ({"inicio": "2025-01-01", "fin": "2026-07-07"}, "fin"),
            (self.params(un_id="abc"), "un_id"),
            (self.params(movil_id="0"), "movil_id"),
        )
        for params, field in cases:
            with self.subTest(params=params):
                response = self.client.get(url, params)
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.json())

        history_url = reverse("combustible-equipo-vs-historico")
        for value in ("abc", "0", "61"):
            with self.subTest(meses_atras=value):
                response = self.client.get(history_url, self.params(meses_atras=value))
                self.assertEqual(response.status_code, 400)
                self.assertIn("meses_atras", response.json())

    def test_lh_agrega_por_fk_excluye_ingresos_y_no_duplica_cargas(self):
        self.carga(self.equipo, date(2026, 7, 1), "300")
        self.carga(self.equipo, date(2026, 7, 1), "200")
        self.carga(self.equipo, date(2026, 7, 2), "350")
        self.carga(self.equipo, date(2026, 7, 2), "999", tipo_mov="I")
        self.produccion(self.equipo, date(2026, 7, 1), "100", "120")
        self.produccion(self.equipo, date(2026, 7, 2), "200", "222.5")

        response = self.client.get(reverse("combustible-equipo-lh"), self.params())

        self.assertEqual(response.status_code, 200)
        result = response.json()["results"][0]
        self.assertEqual(result["equipo_id"], self.equipo.id)
        self.assertEqual(result["equipo"], "Tigercat 875")
        self.assertEqual(result["unidad_negocio"], "FULL TREE")
        self.assertEqual(result["litros_egreso"], 850.0)
        self.assertEqual(result["horas_operativas"], 42.5)
        self.assertEqual(result["litros_por_hora"], 20.0)
        self.assertEqual(result["cantidad_cargas"], 3)
        self.assertEqual(result["registros_produccion"], 2)
        self.assertEqual(result["warnings"], [])
        self.assertEqual(response.json()["totales"]["litros_egreso"], 850.0)

    def test_lh_incluye_equipo_solo_produccion_y_advierte_horas_invalidas(self):
        self.produccion(self.solo_produccion, date(2026, 7, 1), "10", "10")
        self.produccion(self.solo_produccion, date(2026, 7, 2), "20", "19")

        response = self.client.get(reverse("combustible-equipo-lh"), self.params())

        self.assertEqual(response.status_code, 200)
        result = response.json()["results"][0]
        self.assertEqual(result["litros_egreso"], 0.0)
        self.assertEqual(result["horas_operativas"], 0.0)
        self.assertIsNone(result["litros_por_hora"])
        self.assertIn("sin_horas_operativas_validas", result["warnings"])
        self.assertEqual(response.json()["data_quality"]["intervalos_horas_invalidos"], 2)

    def test_lh_filtra_por_equipo_y_unidad(self):
        self.carga(self.equipo, date(2026, 7, 1), "100")
        self.carga(self.otro_equipo, date(2026, 7, 1), "200")
        self.produccion(self.equipo, date(2026, 7, 1), "0", "10")
        self.produccion(self.otro_equipo, date(2026, 7, 1), "0", "10")

        response = self.client.get(
            reverse("combustible-equipo-lh"),
            self.params(un_id=self.un.id, movil_id=self.equipo.id),
        )

        self.assertEqual([row["equipo_id"] for row in response.json()["results"]], [self.equipo.id])

    def test_historico_compara_periodo_equivalente_y_semaforos(self):
        self.carga(self.equipo, date(2026, 7, 1), "120")
        self.produccion(self.equipo, date(2026, 7, 1), "0", "10")
        self.carga(self.equipo, date(2026, 1, 1), "100")
        self.produccion(self.equipo, date(2026, 1, 1), "0", "10")

        response = self.client.get(
            reverse("combustible-equipo-vs-historico"), self.params(meses_atras=6)
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["periodo_historico"], {"inicio": "2026-01-01", "fin": "2026-01-07"})
        result = payload["results"][0]
        self.assertEqual(result["litros_por_hora_actual"], 12.0)
        self.assertEqual(result["litros_por_hora_historico"], 10.0)
        self.assertEqual(result["diferencia_absoluta"], 2.0)
        self.assertEqual(result["variacion_porcentual"], 20.0)
        self.assertEqual(result["semaforo"], "rojo")

    def test_historico_sin_datos_y_base_cero_no_calcula_porcentaje(self):
        self.carga(self.equipo, date(2026, 7, 1), "100")
        self.produccion(self.equipo, date(2026, 7, 1), "0", "10")
        self.produccion(self.equipo, date(2026, 1, 1), "0", "10")

        response = self.client.get(reverse("combustible-equipo-vs-historico"), self.params())

        result = response.json()["results"][0]
        self.assertEqual(result["litros_por_hora_historico"], 0.0)
        self.assertIsNone(result["variacion_porcentual"])
        self.assertEqual(result["semaforo"], "sin_datos")
        self.assertIn("base_historica_nula_o_cero", result["warnings"])

    def test_historico_inexistente_devuelve_sin_datos(self):
        self.carga(self.equipo, date(2026, 7, 1), "100")
        self.produccion(self.equipo, date(2026, 7, 1), "0", "10")

        response = self.client.get(reverse("combustible-equipo-vs-historico"), self.params())

        result = response.json()["results"][0]
        self.assertIsNone(result["litros_por_hora_historico"])
        self.assertIsNone(result["diferencia_absoluta"])
        self.assertIsNone(result["variacion_porcentual"])
        self.assertEqual(result["semaforo"], "sin_datos")
        self.assertIn("muestra_historica_insuficiente", result["warnings"])

    def test_historico_incluye_equipo_solo_presente_en_periodo_historico(self):
        self.carga(self.equipo, date(2026, 1, 1), "100")
        self.produccion(self.equipo, date(2026, 1, 1), "0", "10")

        response = self.client.get(reverse("combustible-equipo-vs-historico"), self.params())

        result = response.json()["results"][0]
        self.assertIsNone(result["litros_por_hora_actual"])
        self.assertEqual(result["litros_por_hora_historico"], 10.0)
        self.assertEqual(result["semaforo"], "sin_datos")
        self.assertIn("muestra_actual_insuficiente", result["warnings"])

    def test_historico_aplica_filtros_por_unidad_y_equipo(self):
        for target, liters in ((self.equipo, "100"), (self.otro_equipo, "200")):
            self.carga(target, date(2026, 7, 1), liters)
            self.produccion(target, date(2026, 7, 1), "0", "10")
            self.carga(target, date(2026, 1, 1), liters)
            self.produccion(target, date(2026, 1, 1), "0", "10")

        response = self.client.get(
            reverse("combustible-equipo-vs-historico"),
            self.params(un_id=self.un.id, movil_id=self.equipo.id),
        )

        self.assertEqual([row["equipo_id"] for row in response.json()["results"]], [self.equipo.id])

    def test_semaforos_usann_umbrales_iniciales_configurables(self):
        from .combustible_services import (
            SEMAFORO_AMARILLO_MAX_PCT,
            SEMAFORO_VERDE_MAX_PCT,
        )

        self.assertEqual(SEMAFORO_VERDE_MAX_PCT, Decimal("5"))
        self.assertEqual(SEMAFORO_AMARILLO_MAX_PCT, Decimal("15"))
        self.carga(self.equipo, date(2026, 1, 1), "100")
        self.produccion(self.equipo, date(2026, 1, 1), "0", "10")
        for liters, expected in (("105", "verde"), ("115", "amarillo"), ("116", "rojo")):
            CargaCombustible.objects.filter(fecha=date(2026, 7, 1)).delete()
            self.carga(self.equipo, date(2026, 7, 1), liters)
            if not RegistroProduccion.objects.filter(fecha=date(2026, 7, 1)).exists():
                self.produccion(self.equipo, date(2026, 7, 1), "0", "10")
            with self.subTest(liters=liters):
                response = self.client.get(
                    reverse("combustible-equipo-vs-historico"), self.params()
                )
                self.assertEqual(response.json()["results"][0]["semaforo"], expected)

    def test_sin_produccion_agrupa_misma_fecha_y_no_acusa_fraude(self):
        self.carga(self.equipo, date(2026, 7, 1), "100")
        self.carga(self.equipo, date(2026, 7, 1), "50")
        self.carga(self.equipo, date(2026, 7, 2), "25")
        self.produccion(self.equipo, date(2026, 7, 2), "0", "8")

        response = self.client.get(reverse("combustible-sin-produccion"), self.params())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 1)
        result = response.json()["results"][0]
        self.assertEqual(result["fecha"], "2026-07-01")
        self.assertEqual(result["litros_egreso"], 150.0)
        self.assertEqual(result["cantidad_cargas"], 2)
        self.assertIn("revisión", result["motivo"])
        self.assertNotIn("fraude", result["motivo"].lower())

    def test_sin_produccion_respeta_fecha_local_datefield_y_filtros(self):
        self.carga(self.equipo, date(2026, 7, 1), "100")
        self.produccion(self.equipo, date(2026, 7, 2), "0", "8")
        self.carga(self.otro_equipo, date(2026, 7, 1), "200")

        response = self.client.get(
            reverse("combustible-sin-produccion"),
            self.params(un_id=self.un.id, movil_id=self.equipo.id),
        )

        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(response.json()["results"][0]["equipo_id"], self.equipo.id)

    def test_sin_produccion_reporta_fk_huerfana_separada_de_id_nulo(self):
        carga = self.carga(self.equipo, date(2026, 7, 1), "100")
        connection.disable_constraint_checking()
        try:
            CargaCombustible.objects.filter(pk=carga.pk).update(equipo_id=999999)
            response = self.client.get(reverse("combustible-sin-produccion"), self.params())
        finally:
            CargaCombustible.objects.filter(pk=carga.pk).delete()
            connection.enable_constraint_checking()

        quality = response.json()["data_quality"]
        self.assertEqual(quality["cargas_con_equipo_id_huerfano"], 1)
        self.assertEqual(quality["cargas_sin_equipo_identificado"], 0)

    def test_endpoints_tienen_limite_razonable_de_queries(self):
        self.carga(self.equipo, date(2026, 7, 1), "100")
        self.produccion(self.equipo, date(2026, 7, 1), "0", "10")
        for index in range(5):
            equipment = Equipo.objects.create(
                patente=f"NQ-{index}", detalle=f"Equipo query {index}", unidad_negocio=self.un
            )
            self.carga(equipment, date(2026, 7, 1), "10")
            self.produccion(equipment, date(2026, 7, 1), "0", "1")
        for name, maximum in (
            ("combustible-equipo-lh", 10),
            ("combustible-equipo-vs-historico", 18),
            ("combustible-sin-produccion", 10),
        ):
            with self.subTest(name=name), CaptureQueriesContext(connection) as captured:
                response = self.client.get(reverse(name), self.params())
            self.assertEqual(response.status_code, 200)
            self.assertLessEqual(len(captured), maximum)
