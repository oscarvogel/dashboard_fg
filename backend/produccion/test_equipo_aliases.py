from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from .equipo_aliases import (
    AliasConflict,
    confirm_equipo_alias,
    deactivate_equipo_alias,
    normalize_alias,
    CanManageEquipoAliases,
    IsEquipoAliasAdmin,
)
from .models import Equipo, EquipoAlias
from .serializers import EquipoAliasConfirmSerializer


class EquipoAliasNormalizationTests(SimpleTestCase):
    def test_equivalent_model_spellings_share_key(self):
        keys = {
            normalize_alias(value).normalized
            for value in ("JS 220 F", "js220f", "JS220F")
        }

        self.assertEqual(keys, {"js220f"})

    def test_preserves_distinct_ordinal_numbers(self):
        self.assertNotEqual(
            normalize_alias("JCB Nº1").normalized,
            normalize_alias("JCB Nº2").normalized,
        )

    def test_collapses_spaces_accents_and_unicode_dashes(self):
        normalized = normalize_alias("  Procesadór\u2013 JCB  ")

        self.assertEqual(normalized.display, "Procesadór- JCB")
        self.assertEqual(normalized.normalized, "procesadorjcb")

    def test_rejects_empty_and_overlong_alias(self):
        with self.assertRaisesMessage(ValidationError, "El alias no puede estar vacío"):
            normalize_alias("   ")
        with self.assertRaisesMessage(ValidationError, "El alias no puede superar 120 caracteres"):
            normalize_alias("x" * 121)


class EquipoAliasModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="alias-admin",
            password="unused",
        )
        cls.equipo_1 = Equipo.objects.create(patente="TEST-1", detalle="Equipo 1")
        cls.equipo_2 = Equipo.objects.create(patente="TEST-2", detalle="Equipo 2")

    def create_alias(self, **overrides):
        values = {
            "equipo": self.equipo_1,
            "alias_display": "JCB",
            "alias_normalizado": "jcb",
            "alias_activo_key": "jcb",
            "activo": True,
            "origen": EquipoAlias.Origen.MANUAL,
            "confirmado_por": self.user,
            "metadata": {"source": "test"},
        }
        values.update(overrides)
        return EquipoAlias.objects.create(**values)

    def test_stores_equipment_audit_origin_and_metadata(self):
        alias = self.create_alias()

        self.assertEqual(alias.equipo, self.equipo_1)
        self.assertEqual(alias.confirmado_por, self.user)
        self.assertEqual(alias.origen, EquipoAlias.Origen.MANUAL)
        self.assertEqual(alias.metadata, {"source": "test"})
        self.assertIsNotNone(alias.confirmado_at)
        self.assertIsNotNone(alias.created_at)
        self.assertIsNotNone(alias.updated_at)

    def test_same_normalized_alias_is_unique_per_equipment(self):
        self.create_alias()

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_alias(alias_activo_key=None, activo=False)

    def test_active_alias_key_is_unique_globally(self):
        self.create_alias()

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_alias(equipo=self.equipo_2)

    def test_inactive_history_can_repeat_normalized_alias_on_other_equipment(self):
        first = self.create_alias(activo=False, alias_activo_key=None)
        second = self.create_alias(
            equipo=self.equipo_2,
            activo=False,
            alias_activo_key=None,
        )

        self.assertIsNone(first.alias_activo_key)
        self.assertIsNone(second.alias_activo_key)


class EquipoAliasServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="oscar",
            first_name="Oscar",
            last_name="Vogel",
        )
        cls.other_user = get_user_model().objects.create_user(username="operator")
        cls.equipo_1 = Equipo.objects.create(
            patente="PROCE-Nº2",
            detalle="Procesador JCB JS220F - Nº 1",
        )
        cls.equipo_2 = Equipo.objects.create(
            patente="PROCE-Nº3",
            detalle="Procesador JCB JS220F - Nº 2",
        )

    def confirm(self, equipo=None, alias="JCB", **overrides):
        values = {
            "equipo": equipo or self.equipo_1,
            "alias": alias,
            "origen": EquipoAlias.Origen.OPENCLAW,
            "confirmado_por": self.user,
            "metadata": {"source": "whatsapp"},
        }
        values.update(overrides)
        return confirm_equipo_alias(**values)

    def test_creates_alias_with_audit_and_updates_compatibility_cache(self):
        result = self.confirm(alias="  Procesadór\u2013 JCB ")

        self.assertTrue(result.created)
        self.assertEqual(result.alias.alias_display, "Procesadór- JCB")
        self.assertEqual(result.alias.alias_normalizado, "procesadorjcb")
        self.assertEqual(result.alias.alias_activo_key, "procesadorjcb")
        self.assertEqual(result.alias.confirmado_por, self.user)
        self.assertEqual(result.alias.metadata, {"source": "whatsapp"})
        self.equipo_1.refresh_from_db()
        self.assertEqual(self.equipo_1.aliases, ["Procesadór- JCB"])

    def test_same_equipment_confirmation_is_idempotent(self):
        first = self.confirm()
        second = self.confirm(alias=" j c b ")

        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(second.alias.pk, first.alias.pk)
        self.assertEqual(EquipoAlias.objects.count(), 1)
        self.equipo_1.refresh_from_db()
        self.assertEqual(self.equipo_1.aliases, ["JCB"])

    def test_reactivates_inactive_alias_and_refreshes_audit(self):
        first = self.confirm()
        deactivate_equipo_alias(alias_record=first.alias)

        result = self.confirm(
            confirmado_por=self.other_user,
            metadata={"source": "manual"},
        )

        self.assertFalse(result.created)
        self.assertTrue(result.alias.activo)
        self.assertEqual(result.alias.alias_activo_key, "jcb")
        self.assertEqual(result.alias.confirmado_por, self.other_user)
        self.assertEqual(result.alias.metadata, {"source": "manual"})

    def test_conflict_on_other_equipment_changes_nothing(self):
        self.confirm(equipo=self.equipo_1)

        with self.assertRaises(AliasConflict) as context:
            self.confirm(equipo=self.equipo_2)

        self.assertEqual(
            context.exception.candidates,
            [
                {
                    "equipo_id": self.equipo_1.id,
                    "patente": "PROCE-Nº2",
                    "detalle": "Procesador JCB JS220F - Nº 1",
                }
            ],
        )
        self.assertEqual(EquipoAlias.objects.count(), 1)
        self.equipo_2.refresh_from_db()
        self.assertEqual(self.equipo_2.aliases, [])

    def test_rejects_invalid_origin_and_metadata(self):
        with self.assertRaisesMessage(ValidationError, "Origen de alias inválido"):
            self.confirm(origen="robot")
        with self.assertRaisesMessage(ValidationError, "metadata debe ser un objeto"):
            self.confirm(metadata=["invalid"])

    def test_empty_and_overlong_aliases_are_rejected(self):
        with self.assertRaises(ValidationError):
            self.confirm(alias=" ")
        with self.assertRaises(ValidationError):
            self.confirm(alias="x" * 121)

    def test_deactivation_is_logical_idempotent_and_updates_cache(self):
        result = self.confirm()

        first = deactivate_equipo_alias(alias_record=result.alias)
        second = deactivate_equipo_alias(alias_record=result.alias)

        self.assertTrue(first.changed)
        self.assertFalse(second.changed)
        result.alias.refresh_from_db()
        self.assertFalse(result.alias.activo)
        self.assertIsNone(result.alias.alias_activo_key)
        self.equipo_1.refresh_from_db()
        self.assertEqual(self.equipo_1.aliases, [])


class EquipoAliasPermissionTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = type("AliasView", (), {})()

    def request_for(self, user):
        request = self.factory.post("/api/equipos/aliases/confirm/", {})
        force_authenticate(request, user=user)
        request.user = user
        return request

    def test_manage_permission_accepts_staff_superuser_or_explicit_permission(self):
        regular = get_user_model().objects.create_user(username="regular")
        staff = get_user_model().objects.create_user(username="staff", is_staff=True)
        superuser = get_user_model().objects.create_superuser(
            username="root",
            email="root@example.test",
            password="unused",
        )
        permitted = get_user_model().objects.create_user(username="permitted")
        permission = Permission.objects.get(
            content_type=ContentType.objects.get_for_model(EquipoAlias),
            codename="change_equipoalias",
        )
        permitted.user_permissions.add(permission)

        checker = CanManageEquipoAliases()
        self.assertFalse(checker.has_permission(self.request_for(regular), self.view))
        self.assertTrue(checker.has_permission(self.request_for(staff), self.view))
        self.assertTrue(checker.has_permission(self.request_for(superuser), self.view))
        self.assertTrue(checker.has_permission(self.request_for(permitted), self.view))

    def test_admin_permission_only_accepts_staff_or_superuser(self):
        regular = get_user_model().objects.create_user(username="regular")
        staff = get_user_model().objects.create_user(username="staff", is_staff=True)
        checker = IsEquipoAliasAdmin()

        self.assertFalse(checker.has_permission(self.request_for(regular), self.view))
        self.assertTrue(checker.has_permission(self.request_for(staff), self.view))


class EquipoAliasSerializerTests(SimpleTestCase):
    def test_validates_payload_and_does_not_accept_confirmer_identity(self):
        serializer = EquipoAliasConfirmSerializer(
            data={
                "equipo_id": 208,
                "alias": " JCB ",
                "origen": "openclaw",
                "metadata": {"source": "whatsapp"},
                "confirmado_por": 999,
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["equipo_id"], 208)
        self.assertEqual(serializer.validated_data["alias"], "JCB")
        self.assertNotIn("confirmado_por", serializer.validated_data)

    def test_requires_equipment_and_alias_and_validates_origin(self):
        missing = EquipoAliasConfirmSerializer(data={})
        invalid_origin = EquipoAliasConfirmSerializer(
            data={"equipo_id": 1, "alias": "JCB", "origen": "robot"}
        )

        self.assertFalse(missing.is_valid())
        self.assertEqual(set(missing.errors), {"equipo_id", "alias"})
        self.assertFalse(invalid_origin.is_valid())
        self.assertIn("origen", invalid_origin.errors)

    def test_rejects_empty_long_alias_and_non_object_metadata(self):
        cases = (
            ({"equipo_id": 1, "alias": " "}, "alias"),
            ({"equipo_id": 1, "alias": "x" * 121}, "alias"),
            ({"equipo_id": 1, "alias": "JCB", "metadata": []}, "metadata"),
        )

        for payload, expected_field in cases:
            with self.subTest(payload=payload):
                serializer = EquipoAliasConfirmSerializer(data=payload)
                self.assertFalse(serializer.is_valid())
                self.assertIn(expected_field, serializer.errors)


class EquipoAliasApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_user(
            username="oscar",
            first_name="Oscar",
            last_name="Vogel",
            is_staff=True,
        )
        cls.regular = get_user_model().objects.create_user(username="regular")
        cls.equipo = Equipo.objects.create(
            patente="PROCE-Nº2",
            detalle="Procesador JCB JS220F - Nº 1",
        )
        cls.other_equipo = Equipo.objects.create(
            patente="PROCE-Nº3",
            detalle="Procesador JCB JS220F - Nº 2",
        )

    def setUp(self):
        self.client = APIClient()
        self.confirm_url = "/api/equipos/aliases/confirm/"

    def payload(self, **overrides):
        values = {
            "equipo_id": self.equipo.id,
            "alias": "JCB",
            "origen": "openclaw",
            "metadata": {"source": "whatsapp"},
        }
        values.update(overrides)
        return values

    def test_confirm_without_authentication_returns_401(self):
        response = self.client.post(self.confirm_url, self.payload(), format="json")

        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_without_permission_returns_403(self):
        self.client.force_authenticate(self.regular)

        response = self.client.post(self.confirm_url, self.payload(), format="json")

        self.assertEqual(response.status_code, 403)

    def test_staff_creates_then_idempotently_confirms_alias(self):
        self.client.force_authenticate(self.staff)

        created = self.client.post(self.confirm_url, self.payload(), format="json")
        repeated = self.client.post(
            self.confirm_url,
            self.payload(alias=" j c b ", confirmado_por=self.regular.id),
            format="json",
        )

        self.assertEqual(created.status_code, 201)
        self.assertTrue(created.data["created"])
        self.assertEqual(created.data["status"], "confirmed")
        self.assertEqual(created.data["equipo"]["id"], self.equipo.id)
        self.assertEqual(created.data["alias"]["normalized"], "jcb")
        self.assertEqual(
            created.data["alias"]["confirmado_por"],
            {"id": self.staff.id, "nombre": "Oscar Vogel"},
        )
        self.assertEqual(repeated.status_code, 200)
        self.assertFalse(repeated.data["created"])
        self.assertEqual(EquipoAlias.objects.count(), 1)

    def test_validation_and_missing_equipment_statuses(self):
        self.client.force_authenticate(self.staff)

        empty = self.client.post(
            self.confirm_url,
            self.payload(alias=" "),
            format="json",
        )
        long_alias = self.client.post(
            self.confirm_url,
            self.payload(alias="x" * 121),
            format="json",
        )
        missing = self.client.post(
            self.confirm_url,
            self.payload(equipo_id=999999),
            format="json",
        )

        self.assertEqual(empty.status_code, 400)
        self.assertEqual(long_alias.status_code, 400)
        self.assertEqual(missing.status_code, 404)

    def test_conflict_returns_409_candidates_and_changes_nothing(self):
        confirm_equipo_alias(
            equipo=self.other_equipo,
            alias="JCB",
            origen=EquipoAlias.Origen.MANUAL,
            confirmado_por=self.staff,
        )
        self.client.force_authenticate(self.staff)

        response = self.client.post(self.confirm_url, self.payload(), format="json")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["error"], "alias_conflict")
        self.assertEqual(
            response.data["candidates"],
            [
                {
                    "equipo_id": self.other_equipo.id,
                    "patente": "PROCE-Nº3",
                    "detalle": "Procesador JCB JS220F - Nº 2",
                }
            ],
        )
        self.assertEqual(EquipoAlias.objects.count(), 1)

    def test_history_requires_auth_and_includes_active_and_inactive(self):
        alias = confirm_equipo_alias(
            equipo=self.equipo,
            alias="JCB",
            origen=EquipoAlias.Origen.MANUAL,
            confirmado_por=self.staff,
        ).alias
        deactivate_equipo_alias(alias_record=alias)
        url = f"/api/equipos/{self.equipo.id}/aliases/"

        anonymous = self.client.get(url)
        self.client.force_authenticate(self.regular)
        authenticated = self.client.get(url)

        self.assertEqual(anonymous.status_code, 401)
        self.assertEqual(authenticated.status_code, 200)
        self.assertEqual(authenticated.data["active"], [])
        self.assertEqual(len(authenticated.data["history"]), 1)
        self.assertFalse(authenticated.data["history"][0]["activo"])

    def test_deactivate_is_admin_only_and_idempotent(self):
        alias = confirm_equipo_alias(
            equipo=self.equipo,
            alias="JCB",
            origen=EquipoAlias.Origen.MANUAL,
            confirmado_por=self.staff,
        ).alias
        url = f"/api/equipos/aliases/{alias.id}/deactivate/"
        self.client.force_authenticate(self.regular)
        forbidden = self.client.post(url, {}, format="json")
        self.client.force_authenticate(self.staff)
        first = self.client.post(url, {}, format="json")
        second = self.client.post(url, {}, format="json")

        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(first.status_code, 200)
        self.assertTrue(first.data["changed"])
        self.assertEqual(second.status_code, 200)
        self.assertFalse(second.data["changed"])


class EquipoSearchApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="reader")
        cls.staff = get_user_model().objects.create_user(username="staff", is_staff=True)
        cls.jcb_1 = Equipo.objects.create(
            patente="PROCE-Nº2",
            detalle="Procesador JCB JS220F - Nº 1",
            codigo_fg="JCB-01",
            modelo_normalizado="JCB JS220F",
        )
        cls.jcb_2 = Equipo.objects.create(
            patente="PROCE-Nº3",
            detalle="Procesador JCB JS220F - Nº 2",
            codigo_fg="JCB-02",
            modelo_normalizado="JCB JS220F",
        )
        cls.ponsse = Equipo.objects.create(
            patente="FORWA-Nº5",
            detalle="Forwarder PONSSE BUFFALO KING - Nº 1",
            modelo_normalizado="Ponsse Buffalo King",
        )
        confirm_equipo_alias(
            equipo=cls.jcb_1,
            alias="JS220",
            origen=EquipoAlias.Origen.MANUAL,
            confirmado_por=cls.staff,
        )

    def setUp(self):
        self.client = APIClient()

    def search(self, query):
        return self.client.get("/api/equipos/", {"q": query})

    def test_search_without_authentication_returns_401(self):
        self.assertEqual(self.search("JCB").status_code, 401)

    def test_searches_patent_detail_model_and_active_alias(self):
        self.client.force_authenticate(self.user)
        cases = (
            ("PROCE-Nº2", self.jcb_1.id, "patente", 1.0),
            ("BUFFALO", self.ponsse.id, "modelo_normalizado", 0.8),
            ("Ponsse Buffalo King", self.ponsse.id, "modelo_normalizado", 0.95),
            ("JS 220", self.jcb_1.id, "alias", 1.0),
        )

        for query, expected_id, match_type, score in cases:
            with self.subTest(query=query):
                response = self.search(query)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["results"][0]["id"], expected_id)
                self.assertEqual(response.data["results"][0]["match_type"], match_type)
                self.assertEqual(response.data["results"][0]["match_score"], score)

    def test_exact_matches_rank_before_partial_matches_deterministically(self):
        exact = Equipo.objects.create(
            patente="JCB",
            detalle="Camion de apoyo",
        )
        self.client.force_authenticate(self.user)

        response = self.search("JCB")

        self.assertEqual(response.data["results"][0]["id"], exact.id)
        self.assertEqual(response.data["results"][0]["match_type"], "patente")
        self.assertEqual(response.data["results"][0]["match_score"], 1.0)
        remaining = response.data["results"][1:]
        self.assertEqual(
            [(item["patente"], item["id"]) for item in remaining],
            sorted((item["patente"], item["id"]) for item in remaining),
        )

    def test_multiple_reasonable_matches_require_confirmation(self):
        self.client.force_authenticate(self.user)

        response = self.search("JCB JS220F")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 2)
        self.assertTrue(response.data["requires_confirmation"])

    def test_inactive_alias_is_not_searchable_or_returned(self):
        record = confirm_equipo_alias(
            equipo=self.ponsse,
            alias="Máquina Azul",
            origen=EquipoAlias.Origen.MANUAL,
            confirmado_por=self.staff,
        ).alias
        deactivate_equipo_alias(alias_record=record)
        self.client.force_authenticate(self.user)

        response = self.search("Máquina Azul")

        self.assertEqual(response.data["total"], 0)

    def test_query_count_does_not_grow_with_number_of_equipment(self):
        self.client.force_authenticate(self.user)

        with self.assertNumQueries(2):
            response = self.search("JCB")

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data["total"], 2)


class EquipoAliasLegacyPatchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_user(username="staff", is_staff=True)
        cls.regular = get_user_model().objects.create_user(username="regular")
        cls.permitted = get_user_model().objects.create_user(username="permitted")
        cls.permitted.user_permissions.add(
            Permission.objects.get(
                content_type=ContentType.objects.get_for_model(EquipoAlias),
                codename="change_equipoalias",
            )
        )
        cls.equipo = Equipo.objects.create(patente="LEGACY-1", detalle="Legacy 1")
        cls.other = Equipo.objects.create(patente="LEGACY-2", detalle="Legacy 2")

    def setUp(self):
        self.client = APIClient()
        self.url = f"/api/equipos/{self.equipo.patente}/aliases/"

    def test_requires_authentication_and_manage_permission(self):
        anonymous = self.client.patch(self.url, {"add": ["JCB"]}, format="json")
        self.client.force_authenticate(self.regular)
        regular = self.client.patch(self.url, {"add": ["JCB"]}, format="json")

        self.assertEqual(anonymous.status_code, 401)
        self.assertEqual(regular.status_code, 403)

    def test_add_is_audited_idempotent_and_deprecated(self):
        self.client.force_authenticate(self.permitted)

        first = self.client.patch(self.url, {"add": ["JCB", " j c b "]}, format="json")
        second = self.client.patch(self.url, {"add": ["JCB"]}, format="json")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.headers["Deprecation"], "true")
        self.assertIn("/api/equipos/aliases/confirm/", first.headers["Link"])
        record = EquipoAlias.objects.get()
        self.assertEqual(record.confirmado_por, self.permitted)
        self.assertEqual(record.origen, EquipoAlias.Origen.MANUAL)
        self.assertEqual(first.data["aliases"], ["JCB"])

    def test_conflict_rolls_back_all_additions(self):
        confirm_equipo_alias(
            equipo=self.other,
            alias="CONFLICT",
            origen=EquipoAlias.Origen.MANUAL,
            confirmado_por=self.staff,
        )
        self.client.force_authenticate(self.staff)

        response = self.client.patch(
            self.url,
            {"add": ["CREATED-FIRST", "CONFLICT"]},
            format="json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertFalse(EquipoAlias.objects.filter(equipo=self.equipo).exists())
        self.equipo.refresh_from_db()
        self.assertEqual(self.equipo.aliases, [])

    def test_replace_is_admin_only_and_logically_deactivates_omitted_alias(self):
        first = confirm_equipo_alias(
            equipo=self.equipo,
            alias="FIRST",
            origen=EquipoAlias.Origen.MANUAL,
            confirmado_por=self.staff,
        ).alias
        confirm_equipo_alias(
            equipo=self.equipo,
            alias="KEEP",
            origen=EquipoAlias.Origen.MANUAL,
            confirmado_por=self.staff,
        )
        self.client.force_authenticate(self.permitted)
        forbidden = self.client.patch(
            self.url,
            {"replace": ["KEEP"]},
            format="json",
        )
        self.client.force_authenticate(self.staff)
        replaced = self.client.patch(
            self.url,
            {"replace": ["KEEP", "NEW"]},
            format="json",
        )

        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(replaced.status_code, 200)
        first.refresh_from_db()
        self.assertFalse(first.activo)
        self.assertEqual(replaced.data["aliases"], ["KEEP", "NEW"])
        self.assertEqual(EquipoAlias.objects.filter(equipo=self.equipo).count(), 3)
