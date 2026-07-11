from datetime import date
from decimal import Decimal
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import connection, models
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Empleado,
    Equipo,
    Origen,
    ProduccionMensual,
    RegistroProduccion,
    UnidadNegocio,
)
from .serializers import RegistroProduccionSerializer


class OperatorModelContractTests(SimpleTestCase):
    def test_cod_operador_es_fk_de_estado_sin_constraint_fisica(self):
        field = RegistroProduccion._meta.get_field("cod_operador")

        self.assertIsInstance(field, models.ForeignKey)
        self.assertIs(field.related_model, Empleado)
        self.assertEqual(field.db_column, "cod_operador")
        self.assertFalse(field.null)
        self.assertFalse(field.blank)
        self.assertFalse(field.db_constraint)
        self.assertEqual(field.default, 1)
        self.assertIs(field.remote_field.on_delete, models.DO_NOTHING)

    def test_operador_texto_legado_se_conserva(self):
        field = RegistroProduccion._meta.get_field("operador")

        self.assertIsInstance(field, models.CharField)
        self.assertEqual(field.max_length, 50)

    def test_migracion_0011_es_exclusivamente_de_estado(self):
        import importlib

        module = importlib.import_module(
            "produccion.migrations.0011_registroproduccion_cod_operador_state"
        )
        operation = module.Migration.operations[0]

        self.assertEqual(operation.database_operations, [])
        self.assertEqual(len(operation.state_operations), 1)


class OperatorMigrationTests(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        with connection.schema_editor() as editor:
            editor.create_model(Origen)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        with connection.schema_editor() as editor:
            editor.delete_model(Origen)

    @override_settings(
        MIGRATION_MODULES={
            "produccion": "produccion.migrations",
            "mantenimiento": None,
        }
    )
    def test_sqlmigrate_0011_no_emite_ddl(self):
        output = StringIO()

        call_command("sqlmigrate", "produccion", "0011", stdout=output)

        sql = output.getvalue().lower()
        self.assertIn("no-op", sql)
        self.assertNotIn("alter table", sql)
        self.assertNotIn("add constraint", sql)


class OperatorIdentityAPITests(TestCase):
    @classmethod
    def setUpClass(cls):
        with connection.schema_editor() as editor:
            editor.create_model(Origen)
            editor.create_model(ProduccionMensual)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        with connection.schema_editor() as editor:
            editor.delete_model(ProduccionMensual)
            editor.delete_model(Origen)

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="operator-reader", password="test-pass")
        cls.un = UnidadNegocio.objects.create(nombre="FULL TREE")
        cls.equipo = Equipo.objects.create(
            patente="PROCE-Nº3", detalle="Procesadora Nº3", unidad_negocio=cls.un
        )
        cls.anzuate = Empleado.objects.create(
            nombre="ANZUATE ANGEL JONATAN", dni="12345678", password="unused"
        )
        cls.otro = Empleado.objects.create(
            nombre="OTRO OPERADOR", dni="87654321", password="unused"
        )
        cls.registro_legacy_corto = cls._crear_registro(
            empleado=cls.anzuate, legacy="ANZUATE JONATAN", day=1
        )
        cls.registro_legacy_largo = cls._crear_registro(
            empleado=cls.anzuate, legacy="ANZUATE ANGEL JONATAN", day=2
        )
        cls._crear_registro(empleado=cls.otro, legacy="ANZUATE JONATAN", day=3)

    @classmethod
    def _crear_registro(cls, empleado, legacy, day):
        return RegistroProduccion.objects.create(
            UN=cls.un.nombre,
            operacion="PROCESADO",
            operador=legacy,
            fecha=date(2026, 7, day),
            equipo=cls.equipo.detalle,
            cod_equipo=cls.equipo,
            cod_operador=empleado,
            cod_un=cls.un,
            hr_inicio=Decimal("10"),
            hr_fin=Decimal("18"),
            produccion=Decimal("100"),
        )

    def setUp(self):
        self.client = APIClient()
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_serializer_conserva_legado_y_agrega_identidad_canonica(self):
        data = RegistroProduccionSerializer(self.registro_legacy_corto).data

        self.assertEqual(data["operador"], "ANZUATE JONATAN")
        self.assertEqual(data["operador_texto_legacy"], "ANZUATE JONATAN")
        self.assertEqual(data["operador_id"], self.anzuate.id)
        self.assertEqual(data["operador_nombre"], "ANZUATE ANGEL JONATAN")

    def test_serializer_tolera_operador_sin_relacion(self):
        registro = RegistroProduccion(
            operador="TEXTO SIN RELACION", cod_operador_id=None
        )

        data = RegistroProduccionSerializer(registro).data

        self.assertIsNone(data["operador_id"])
        self.assertIsNone(data["operador_nombre"])
        self.assertEqual(data["operador_texto_legacy"], "TEXTO SIN RELACION")

    def test_serializer_con_select_related_no_hace_n_mas_uno(self):
        for day in range(4, 10):
            self._crear_registro(
                empleado=self.anzuate,
                legacy=f"VARIANTE LEGADA {day}",
                day=day,
            )
        queryset = RegistroProduccion.objects.select_related(
            "cod_operador", "cod_equipo", "cod_un", "origen_camion"
        ).order_by("id")

        with CaptureQueriesContext(connection) as captured:
            data = RegistroProduccionSerializer(queryset, many=True).data

        self.assertEqual(len(data), 9)
        self.assertEqual(len(captured), 1)

    def test_prefetch_preserva_registro_con_operador_huerfano_sin_n_mas_uno(self):
        registro = self._crear_registro(
            empleado=self.anzuate,
            legacy="OPERADOR ELIMINADO",
            day=10,
        )
        connection.disable_constraint_checking()
        try:
            RegistroProduccion.objects.filter(pk=registro.pk).update(cod_operador_id=999999)
            queryset = RegistroProduccion.objects.select_related(
                "cod_equipo", "cod_un", "origen_camion"
            ).prefetch_related("cod_operador").filter(pk=registro.pk)
            with CaptureQueriesContext(connection) as captured:
                data = RegistroProduccionSerializer(queryset, many=True).data
        finally:
            RegistroProduccion.objects.filter(pk=registro.pk).delete()
            connection.enable_constraint_checking()

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["operador_id"], 999999)
        self.assertIsNone(data[0]["operador_nombre"])
        self.assertLessEqual(len(captured), 2)

    def test_dashboard_no_descarta_registro_con_operador_huerfano(self):
        registro = self._crear_registro(
            empleado=self.anzuate,
            legacy="OPERADOR ELIMINADO",
            day=10,
        )
        connection.disable_constraint_checking()
        try:
            RegistroProduccion.objects.filter(pk=registro.pk).update(cod_operador_id=999999)
            response = self.client.get(
                reverse("produccion-list"),
                {
                    "start_date": "2026-07-10",
                    "end_date": "2026-07-10",
                    "page_size": 100,
                },
            )
        finally:
            RegistroProduccion.objects.filter(pk=registro.pk).delete()
            connection.enable_constraint_checking()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(response.json()["results"][0]["operador_id"], 999999)
        self.assertIsNone(response.json()["results"][0]["operador_nombre"])

    def test_filtros_colapsan_aliases_por_id_y_usan_nombre_personal(self):
        response = self.client.get(
            reverse("filtros-dinamicos"),
            {"start_date": "2026-07-01", "end_date": "2026-07-03"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["operadores"],
            [
                {"id": self.anzuate.id, "nombre": "ANZUATE ANGEL JONATAN"},
                {"id": self.otro.id, "nombre": "OTRO OPERADOR"},
            ],
        )

    def test_dashboard_filtra_por_operador_id_y_mantiene_campos_existentes(self):
        response = self.client.get(
            reverse("produccion-list"),
            {
                "start_date": "2026-07-01",
                "end_date": "2026-07-03",
                "operador": self.anzuate.id,
                "page_size": 100,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["filtros"]["operadores"], [
            {"id": self.anzuate.id, "nombre": "ANZUATE ANGEL JONATAN"}
        ])
        for row in payload["results"]:
            self.assertIn("operador", row)
            self.assertEqual(row["operador_id"], self.anzuate.id)
            self.assertEqual(row["operador_nombre"], "ANZUATE ANGEL JONATAN")

    def test_dashboard_mantiene_cantidad_constante_de_queries_con_volumen(self):
        params = {
            "start_date": "2026-07-01",
            "end_date": "2026-07-20",
            "page_size": 100,
        }
        with CaptureQueriesContext(connection) as baseline:
            response = self.client.get(reverse("produccion-list"), params)
        self.assertEqual(response.status_code, 200)

        for day in range(11, 18):
            self._crear_registro(
                empleado=self.anzuate,
                legacy=f"LEGACY {day}",
                day=day,
            )
        with CaptureQueriesContext(connection) as with_volume:
            response = self.client.get(reverse("produccion-list"), params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(with_volume), len(baseline))

    def test_produccion_operador_usa_id_y_nombre_canonico(self):
        response = self.client.get(
            reverse("produccion_operador"),
            {
                "operador_id": self.anzuate.id,
                "fecha_inicio": "2026-07-01",
                "fecha_fin": "2026-07-03",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["operador_id"], self.anzuate.id)
        self.assertEqual(response.json()["operador"], "ANZUATE ANGEL JONATAN")

    def test_maquinas_por_frente_deduplica_por_operador_id(self):
        response = self.client.get(
            reverse("maquinas_frente_operador"),
            {"fecha_inicio": "2026-07-01", "fecha_fin": "2026-07-02"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["data"]), 1)
        row = response.json()["data"][0]
        self.assertEqual(row["operador_id"], self.anzuate.id)
        self.assertEqual(row["operador"], "ANZUATE ANGEL JONATAN")

    def test_maquinas_por_frente_preserva_operador_huerfano(self):
        registro = self._crear_registro(
            empleado=self.anzuate,
            legacy="OPERADOR ELIMINADO",
            day=10,
        )
        connection.disable_constraint_checking()
        try:
            RegistroProduccion.objects.filter(pk=registro.pk).update(cod_operador_id=999999)
            response = self.client.get(
                reverse("maquinas_frente_operador"),
                {"fecha_inicio": "2026-07-10", "fecha_fin": "2026-07-10"},
            )
        finally:
            RegistroProduccion.objects.filter(pk=registro.pk).delete()
            connection.enable_constraint_checking()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["data"]), 1)
        self.assertEqual(response.json()["data"][0]["operador_id"], 999999)
        self.assertIsNone(response.json()["data"][0]["operador"])

    def test_maquinas_por_frente_mantiene_queries_constantes_con_volumen(self):
        params = {"fecha_inicio": "2026-07-01", "fecha_fin": "2026-07-20"}
        with CaptureQueriesContext(connection) as baseline:
            response = self.client.get(reverse("maquinas_frente_operador"), params)
        self.assertEqual(response.status_code, 200)

        for day in range(11, 18):
            self._crear_registro(
                empleado=self.anzuate,
                legacy=f"LEGACY {day}",
                day=day,
            )
        with CaptureQueriesContext(connection) as with_volume:
            response = self.client.get(reverse("maquinas_frente_operador"), params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(with_volume), len(baseline))
