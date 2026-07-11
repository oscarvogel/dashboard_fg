from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase

from .equipo_aliases import (
    AliasConflict,
    confirm_equipo_alias,
    deactivate_equipo_alias,
    normalize_alias,
)
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
