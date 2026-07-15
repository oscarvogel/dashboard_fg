from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase

from .equipo_aliases import confirm_equipo_alias
from .models import Equipo, EquipoAlias


class SyncEquipoAliasesCommandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="system-importer")

    def create_equipo(self, **overrides):
        values = {
            "patente": "ALIAS-DRY-RUN",
            "detalle": "Procesador JCB JS220F - Nº 1",
            "codigo_fg": "JCB-01",
            "modelo_normalizado": "JCB JS220F",
            "aliases": ["Legacy JCB"],
        }
        values.update(overrides)
        return Equipo.objects.create(**values)

    def run_command(self, *args, **options):
        output = StringIO()
        call_command("sync_equipo_aliases", *args, stdout=output, **options)
        return output.getvalue()

    def test_default_dry_run_for_one_equipment_does_not_write(self):
        equipo = self.create_equipo()
        before_aliases = list(equipo.aliases)

        output = self.run_command(equipo_id=equipo.id)

        self.assertIn("MODO: DRY-RUN", output)
        self.assertIn("Legacy JCB", output)
        self.assertEqual(EquipoAlias.objects.count(), 0)
        equipo.refresh_from_db()
        self.assertEqual(equipo.aliases, before_aliases)

    def test_explicit_dry_run_does_not_write(self):
        self.create_equipo()

        output = self.run_command(dry_run=True)

        self.assertIn("CREAR", output)
        self.assertEqual(EquipoAlias.objects.count(), 0)

    def test_apply_requires_existing_confirmer(self):
        self.create_equipo()

        with self.assertRaisesMessage(CommandError, "--confirmed-by-user-id"):
            self.run_command(apply=True)
        with self.assertRaisesMessage(CommandError, "Usuario confirmador inexistente"):
            self.run_command(apply=True, confirmed_by_user_id=999999)

    def test_dry_run_and_apply_are_mutually_exclusive(self):
        self.create_equipo()

        with self.assertRaisesMessage(CommandError, "mutuamente excluyentes"):
            self.run_command(dry_run=True, apply=True)

    def test_missing_equipment_filter_fails_without_writes(self):
        with self.assertRaisesMessage(CommandError, "Equipo inexistente"):
            self.run_command(equipo_id=999999)

        self.assertEqual(EquipoAlias.objects.count(), 0)

    def test_conflicts_are_reported_and_not_applied(self):
        first = self.create_equipo(
            patente="SAFE-1",
            detalle="Equipo A",
            codigo_fg="SAME",
            modelo_normalizado="",
            aliases=[],
        )
        second = self.create_equipo(
            patente="SAFE-2",
            detalle="Equipo B",
            codigo_fg="SAME",
            modelo_normalizado="",
            aliases=[],
        )

        output = self.run_command(
            apply=True,
            confirmed_by_user_id=self.user.id,
        )

        self.assertIn("CONFLICTO", output)
        self.assertIn("APLICADO", output)
        self.assertLess(output.index("CONFLICTO"), output.index("APLICADO"))
        self.assertFalse(
            EquipoAlias.objects.filter(
                alias_normalizado="same",
                equipo_id__in=(first.id, second.id),
            ).exists()
        )

    def test_apply_creates_all_sources_and_is_idempotent(self):
        equipo = self.create_equipo()

        first = self.run_command(
            apply=True,
            equipo_id=equipo.id,
            confirmed_by_user_id=self.user.id,
        )
        count_after_first = EquipoAlias.objects.count()
        second = self.run_command(
            apply=True,
            equipo_id=equipo.id,
            confirmed_by_user_id=self.user.id,
        )

        self.assertIn("APLICADO", first)
        self.assertGreaterEqual(count_after_first, 5)
        self.assertEqual(EquipoAlias.objects.count(), count_after_first)
        self.assertIn("EXISTENTE", second)
        origins = set(EquipoAlias.objects.values_list("origen", flat=True))
        self.assertEqual(
            origins,
            {EquipoAlias.Origen.IMPORTACION, EquipoAlias.Origen.SISTEMA},
        )

    def test_apply_does_not_overwrite_manual_alias_audit(self):
        equipo = self.create_equipo(aliases=["JCB"])
        manual_user = get_user_model().objects.create_user(username="manual-user")
        record = confirm_equipo_alias(
            equipo=equipo,
            alias="JCB",
            origen=EquipoAlias.Origen.MANUAL,
            confirmado_por=manual_user,
            metadata={"kept": True},
        ).alias

        self.run_command(
            apply=True,
            equipo_id=equipo.id,
            confirmed_by_user_id=self.user.id,
        )

        record.refresh_from_db()
        self.assertEqual(record.origen, EquipoAlias.Origen.MANUAL)
        self.assertEqual(record.confirmado_por, manual_user)
        self.assertEqual(record.metadata, {"kept": True})
        self.assertTrue(record.activo)
