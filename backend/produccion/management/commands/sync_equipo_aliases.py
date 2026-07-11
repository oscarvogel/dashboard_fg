from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from produccion.equipo_aliases import AliasConflict, confirm_equipo_alias, normalize_alias
from produccion.models import Equipo, EquipoAlias


@dataclass(frozen=True)
class Candidate:
    equipo: Equipo
    display: str
    normalized: str
    origen: str
    field: str


class Command(BaseCommand):
    help = "Inventaría o importa aliases de equipos sin crear equipos ni borrar aliases."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--equipo-id", type=int)
        parser.add_argument("--confirmed-by-user-id", type=int)

    def handle(self, *args, **options):
        if options["dry_run"] and options["apply"]:
            raise CommandError("--dry-run y --apply son mutuamente excluyentes")

        apply_changes = options["apply"]
        confirmer = self._get_confirmer(options, apply_changes)
        equipos = Equipo.objects.all().order_by("id")
        if options["equipo_id"] is not None:
            equipos = equipos.filter(pk=options["equipo_id"])
            if not equipos.exists():
                raise CommandError(f"Equipo inexistente: {options['equipo_id']}")
        equipos = list(equipos)
        candidates = self._build_candidates(equipos)
        conflicts = self._conflicting_keys(candidates)

        self.stdout.write(f"MODO: {'APPLY' if apply_changes else 'DRY-RUN'}")
        self.stdout.write(
            f"EQUIPOS: {len(equipos)} | CANDIDATOS: {len(candidates)}"
        )
        counters = {
            "created": 0,
            "existing": 0,
            "conflicts": 0,
            "invalid": 0,
        }
        for candidate in candidates:
            if candidate.normalized not in conflicts:
                continue
            counters["conflicts"] += 1
            owners = ",".join(
                map(str, sorted(conflicts[candidate.normalized]))
            )
            self.stdout.write(
                "CONFLICTO "
                f"equipo={candidate.equipo.id} patente={candidate.equipo.patente} "
                f"alias={candidate.display!r} origen={candidate.origen} "
                f"campo={candidate.field} equipos={owners}"
            )

        for candidate in candidates:
            prefix = (
                f"equipo={candidate.equipo.id} patente={candidate.equipo.patente} "
                f"alias={candidate.display!r} origen={candidate.origen} campo={candidate.field}"
            )
            if candidate.normalized in conflicts:
                continue

            existing = EquipoAlias.objects.filter(
                equipo=candidate.equipo,
                alias_normalizado=candidate.normalized,
            ).first()
            if existing and existing.origen == EquipoAlias.Origen.MANUAL:
                counters["existing"] += 1
                self.stdout.write(f"EXISTENTE-MANUAL {prefix}")
                continue
            if existing and existing.activo:
                counters["existing"] += 1
                self.stdout.write(f"EXISTENTE {prefix}")
                continue

            if not apply_changes:
                self.stdout.write(
                    f"{'REACTIVAR' if existing else 'CREAR'} {prefix}"
                )
                continue

            try:
                result = confirm_equipo_alias(
                    equipo=candidate.equipo,
                    alias=candidate.display,
                    origen=candidate.origen,
                    confirmado_por=confirmer,
                    metadata={
                        "source": "sync_equipo_aliases",
                        "field": candidate.field,
                    },
                )
            except AliasConflict as conflict:
                counters["conflicts"] += 1
                self.stdout.write(
                    f"CONFLICTO {prefix} candidatos={conflict.candidates}"
                )
                continue
            counters["created"] += int(result.created)
            counters["existing"] += int(not result.created)
            self.stdout.write(f"APLICADO {prefix}")

        self.stdout.write(
            "RESUMEN "
            f"creados={counters['created']} existentes={counters['existing']} "
            f"conflictos={counters['conflicts']} invalidos={counters['invalid']}"
        )

    def _get_confirmer(self, options, apply_changes):
        user_id = options["confirmed_by_user_id"]
        if not apply_changes:
            return None
        if user_id is None:
            raise CommandError("--apply exige --confirmed-by-user-id")
        try:
            return get_user_model().objects.get(pk=user_id)
        except get_user_model().DoesNotExist as error:
            raise CommandError("Usuario confirmador inexistente") from error

    def _build_candidates(self, equipos):
        candidates = []
        for equipo in equipos:
            raw_candidates = []
            for alias in equipo.aliases or []:
                raw_candidates.append(
                    (alias, EquipoAlias.Origen.IMPORTACION, "aliases")
                )
            raw_candidates.extend(
                (
                    (equipo.patente, EquipoAlias.Origen.SISTEMA, "patente"),
                    (equipo.detalle, EquipoAlias.Origen.SISTEMA, "detalle"),
                    (equipo.codigo_fg, EquipoAlias.Origen.SISTEMA, "codigo_fg"),
                    (
                        equipo.modelo_normalizado,
                        EquipoAlias.Origen.SISTEMA,
                        "modelo_normalizado",
                    ),
                )
            )
            seen = set()
            for value, origen, field in raw_candidates:
                if not isinstance(value, str) or not value.strip():
                    continue
                try:
                    normalized = normalize_alias(value)
                except ValidationError as error:
                    self.stdout.write(
                        f"INVALIDO equipo={equipo.id} campo={field} error={error.messages}"
                    )
                    continue
                if normalized.normalized in seen:
                    continue
                seen.add(normalized.normalized)
                candidates.append(
                    Candidate(
                        equipo=equipo,
                        display=normalized.display,
                        normalized=normalized.normalized,
                        origen=origen,
                        field=field,
                    )
                )
        return candidates

    def _conflicting_keys(self, candidates):
        owners = {}
        for candidate in candidates:
            owners.setdefault(candidate.normalized, set()).add(candidate.equipo.id)
        for normalized, equipo_id in EquipoAlias.objects.filter(
            activo=True
        ).values_list("alias_normalizado", "equipo_id"):
            owners.setdefault(normalized, set()).add(equipo_id)
        return {
            normalized: equipo_ids
            for normalized, equipo_ids in owners.items()
            if len(equipo_ids) > 1
        }
