from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase

from .equipo_aliases import normalize_alias
from .models import Equipo, EquipoAlias


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
