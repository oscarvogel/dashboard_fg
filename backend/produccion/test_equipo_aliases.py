from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from .equipo_aliases import normalize_alias


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
